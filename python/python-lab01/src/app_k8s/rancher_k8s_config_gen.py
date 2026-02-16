### ---------------------------------------------
# Dependencies:
# pip install requests pyyaml
# pip install requests pyyaml cryptography
# python rancher_k8s_config_gen.py \
#     --url "https://rancher.example.com" \
#     --user "admin" \
#     --password "YourSecurePassword" \
#     --cluster "mycluster1" \
#     --path "./mycluster1.yaml" \
#     --ttl 90
### ---------------------------------------------


import requests
import yaml
import argparse
import os
import shutil
from datetime import datetime, timezone

# Disable SSL warnings for self-signed certs
requests.packages.urllib3.disable_warnings()


class RancherManager:
    def __init__(self, url, username, password):
        self.url = url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = self._login(username, password)
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}

    def _login(self, username, password):
        login_url = f"{self.url}/v3-public/localProviders/local?action=login"
        resp = self.session.post(login_url, json={"username": username, "password": password}, verify=False)
        resp.raise_for_status()
        return resp.json().get('token')

    def check_kubeconfig_expiry(self, file_path):
        if not os.path.exists(file_path):
            print(f"[-] File not found: {file_path}")
            return

        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)

        # Extract token (usually in format token-xxxxx:yyyyy)
        try:
            full_token = config['users'][0]['user']['token']
            token_id = full_token.split(':')[0]

            # Query Rancher API for the token object metadata
            resp = self.session.get(f"{self.url}/v3/tokens/{token_id}", headers=self.headers, verify=False)
            if resp.status_code == 404:
                print("[-] Token not found in Rancher. It might have already expired or been deleted.")
                return

            data = resp.json()
            expiry_str = data.get('expiresAt')

            if not expiry_str:
                print("[!] This token is set to NEVER expire.")
            else:
                expiry_dt = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                diff = expiry_dt - now
                print(f"[*] Kubeconfig Expiry: {expiry_dt} (Remaining: {diff.days} days, {diff.seconds // 3600} hours)")
        except (KeyError, IndexError):
            print("[-] Could not find a valid Rancher token in the provided Kubeconfig file.")

    def create_new_kubeconfig(self, cluster_name, ttl_days, original_path):
        # 1. Get Cluster Info
        resp = self.session.get(f"{self.url}/v3/clusters?name={cluster_name}", headers=self.headers, verify=False)
        clusters = resp.json().get('data', [])
        if not clusters:
            print(f"[-] Cluster '{cluster_name}' not found.")
            return

        cluster = clusters[0]
        cluster_id = cluster['id']
        ca_cert = cluster['caCert']
        server_url = f"{self.url}/k8s/clusters/{cluster_id}"

        # 2. Create a new API Token with specific TTL
        # TTL is in milliseconds
        ttl_ms = ttl_days * 24 * 60 * 60 * 1000
        token_payload = {
            "type": "token",
            "metadata": {"name": f"kubeconfig-{cluster_name}-custom"},
            "ttl": ttl_ms,
            "description": f"Generated via script for {cluster_name}"
        }

        token_resp = self.session.post(f"{self.url}/v3/tokens", json=token_payload, headers=self.headers, verify=False)
        token_resp.raise_for_status()
        new_token_data = token_resp.json()
        new_token_value = new_token_data['token']

        # 3. Construct Kubeconfig YAML
        kubeconfig_data = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": cluster_name,
                "cluster": {"certificate-authority-data": ca_cert, "server": server_url}
            }],
            "users": [{
                "name": "user-" + cluster_id,
                "user": {"token": new_token_value}
            }],
            "contexts": [{
                "name": cluster_name,
                "context": {"cluster": cluster_name, "user": "user-" + cluster_id}
            }],
            "current-context": cluster_name
        }

        # 4. File Management
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"k8s_{cluster_name}_{timestamp}.yaml"

        # Write the new timestamped file
        with open(new_filename, 'w') as f:
            yaml.dump(kubeconfig_data, f)
        print(f"[+] New Kubeconfig saved to: {new_filename}")

        # Backup existing file
        if os.path.exists(original_path):
            backup_path = original_path + ".old"
            shutil.copy2(original_path, backup_path)
            print(f"[*] Backed up original to: {backup_path}")

        # Overwrite existing file with new content
        with open(original_path, 'w') as f:
            yaml.dump(kubeconfig_data, f)
        print(f"[+] Updated existing file: {original_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rancher Kubeconfig Management Tool")
    parser.add_argument("--url", required=True, help="Rancher Server URL")
    parser.add_argument("--user", required=True, help="Admin Username")
    parser.add_argument("--password", required=True, help="Admin Password")
    parser.add_argument("--cluster", required=True, help="Cluster Name")
    parser.add_argument("--path", required=True, help="Path to existing kubeconfig file")
    parser.add_argument("--ttl", type=int, default=30, help="TTL for new token in days")

    args = parser.parse_args()

    manager = RancherManager(args.url, args.user, args.password)

    print("--- Step 1: Checking Expiry of Existing Config ---")
    manager.check_kubeconfig_expiry(args.path)

    print("\n--- Step 2: Generating New Config ---")
    manager.create_new_kubeconfig(args.cluster, args.ttl, args.path)

