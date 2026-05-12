import yaml
import requests
from requests.auth import HTTPBasicAuth
from glom import glom
import json

config_file='create_ct_cfg.yml'

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_token(config):
    auth_cfg = config['auth']
    print(f"[*] Authenticating for {auth_cfg['username']}...")
    headers = {
        'Accept': 'application/json',
        'x-tenant-id': auth_cfg['tenantId']
    }

    response = requests.get(auth_cfg['token_url'],
                            auth=(auth_cfg['username'], auth_cfg['password']),
                            headers=headers)

    # response = requests.post(
    #
    #     auth=HTTPBasicAuth(auth_cfg['username'], auth_cfg['password']),
    #     data={'grant_type': 'client_credentials'}
    # )

    response.raise_for_status()
    return response.json().get('access_token')


def post_account_data(url, token, payload):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    print(payload)
    # response = requests.post(url, headers=headers, json=payload)
    response = None
    if response.status_code in [200, 201]:
        print(f"  [+] Successfully posted: {payload.get('name', 'Unknown')}")
    else:
        print(f"  [!] Failed to post {payload.get('name')}: {response.status_code}")


def main():
    config = load_yaml(config_file)
    groups = load_yaml(config['payload_source']['data_file'])
    tenant_id = config['auth']['tenantId']

    try:
        token = get_token(config)
        mapping = config['payload_source']['mapping']
        post_url = config['api']['post_url']

        # 1. Iterate over each Group
        for group in groups:
            group_name = group.get('groupName', 'Unnamed Group')
            print(f"\n>>> Processing Group: {group_name}")

            # 2. Iterate over each Account in the Group
            accounts = group.get('accounts', [])
            for account in accounts:
                # 3. Build payload relative to the current 'account' object
                payload = {}
                for json_key, yaml_path in mapping.items():
                    try:
                        # We pass the 'account' dict as the data source to glom
                        payload[json_key] = glom(account, yaml_path)
                    except Exception:
                        payload[json_key] = None

                # Add group context to payload if needed
                # payload['parentGroup'] = group_name

                # 4. Make the POST request
                post_account_data(post_url, token, payload)

    except Exception as e:
        print(f"[X] Critical Error: {e}")


if __name__ == "__main__":
    main()
