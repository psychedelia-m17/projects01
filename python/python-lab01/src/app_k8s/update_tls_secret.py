import argparse
import base64
import os
from datetime import datetime, timezone
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def get_args() -> tuple[str, str, str, str, str]:
    """Parse the command line arguments."""

    # 1. Initialize the parser with a description
    parser = argparse.ArgumentParser(description="Update Kubernetes Secret for TLS certificate.")

    # 2. Add arguments with short and long switches
    # 'required=True' ensures the script won't run without these specific files
    parser.add_argument("-n", "--namespace", required=True, help="Kubernetes namespace to use.")
    parser.add_argument("-s", "--secret",   required=True, help="Name of Kubernetes secret to update.")
    parser.add_argument("-c", "--cert",     required=True, help="Path to the certificate file (.crt)")
    parser.add_argument("-k", "--key",      required=True, help="Path to the private key file (.pem)")
    parser.add_argument("-f", "--config",   required=True,
                        help="Path to the Kubernetes cluster config file (.json or .yaml)")

    # 3. Parse the arguments
    args = parser.parse_args()

    # 4. Access the paths directly via their long-form names
    print("--- Received Arguments ---")
    print(f"Namespace: {args.namespace}")
    print(f"Secret: {args.secret}")
    print(f"Certificate: {args.cert}")
    print(f"Private Key: {args.key}")
    print(f"Config File: {args.config}")
    print("---------------------------")
    return args.namespace, args.secret, args.cert, args.key, args.config

    return args.namespace, args.secret, args.cert, args.key, args.config


def get_k8s_api_client(k8s_config_file: str) -> client.CoreV1Api | None:
    """Return a Kubernetes API client."""

    if os.path.isfile(k8s_config_file):
        config.load_kube_config(k8s_config_file)
        v1 = client.CoreV1Api()
        return v1
    else:
        return None

def update_tls_secrets(api_client: client.CoreV1Api, namespaces, secret_name, cert_file_path, key_file_path):
    # 1. Load Kubernetes Configuration
    # Uses local kubeconfig (~/.kube/config). Use load_incluster_config() if running inside a Pod.
    # try:
    #     config.load_kube_config()
    #     v1 = client.CoreV1Api()
    # except Exception as e:
    #     print(f"Failed to load K8s config: {e}")
    #     return

    # 2. Read and encode Certificate and Key files
    try:
        with open(cert_file_path, "rb") as f:
            cert_data = base64.b64encode(f.read()).decode("utf-8")
        with open(key_file_path, "rb") as f:
            key_data = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError as e:
        print(f"File Error: {e}")
        return

    # 3. Define the Secret payload
    # Note: Keys must be 'tls.crt' and 'tls.key' for type 'kubernetes.io/tls'
    now_str = datetime.now(timezone.utc).isoformat()
    secret_body = {
        "metadata": {
            "annotations": {
                "dt.com.stage/updated-on": now_str,
            }
        },
        "data": {
            "tls.crt": cert_data,
            "tls.key": key_data
        }
    }

    # 4. Iterate through namespaces and update
    for ns in namespaces:
        print(f"Processing namespace: {ns}, secret: {secret_name}")
        try:
            api_client.patch_namespaced_secret(name=secret_name, namespace=ns, body=secret_body)
            print(f"Successfully updated '{secret_name}' in '{ns}'")
        except ApiException as e:
            if e.status == 404:
                print(f"Error: Secret '{secret_name}' not found in namespace '{ns}'. Skipping...")
            else:
                print(f"API Error in '{ns}': {e}")


# --- Configuration ---
if __name__ == "__main__":
    k8s_ns, k8s_secret, cert_file_path, key_file_path, cfg_file_path = get_args()

    # Paths to your new certificates
    # path_to_cert = "./certs/fullchain.pem"
    # path_to_key = "./certs/privkey.pem"

    api_client = get_k8s_api_client(cfg_file_path)

    update_tls_secrets(api_client, [k8s_ns], k8s_secret, cert_file_path, key_file_path)

