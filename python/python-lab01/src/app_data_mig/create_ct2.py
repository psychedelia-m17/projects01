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
    response = requests.post(
        auth_cfg['token_url'],
        auth=HTTPBasicAuth(auth_cfg['username'], auth_cfg['password']),
        data={'grant_type': 'client_credentials'}
    )
    response.raise_for_status()
    return response.json().get('access_token')


def build_nested_payload(mapping_level, account_data):
    """
    Recursively builds the payload.
    If a value is a dict, it recurses.
    If a value is a string, it treats it as a glom path.
    """
    payload = {}
    for key, value in mapping_level.items():
        if isinstance(value, dict):
            # Recurse into the next level of the payload
            payload[key] = build_nested_payload(value, account_data)
        else:
            # Leaf node: Value is a string representing the YAML path
            try:
                payload[key] = glom(account_data, value)
            except Exception:
                payload[key] = None
    return payload


def post_account_data(url, token, payload):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=payload)

    # Using accountName from the nested structure for logging if available
    # Adjust the path below to match your specific nested structure
    acc_name = glom(payload, "key1.key2.accountName", default="Unknown")

    if response.status_code in [200, 201]:
        print(f"  [+] Successfully posted: {acc_name}")
    else:
        print(f"  [!] Failed to post {acc_name}: {response.status_code}")


def main():
    config = load_yaml(config_file)
    groups = load_yaml(config['payload_source']['data_file'])

    try:
        token = None
        # token = get_token(config)
        mapping = config['payload_source']['mapping']
        post_url = config['api']['post_url']

        for group in groups:
            group_name = group.get('groupName', 'Unnamed Group')
            print(f"\n>>> Processing Group: {group_name}")

            accounts = group.get('accounts', [])
            for account in accounts:
                # Build the nested payload using the recursive function
                payload = build_nested_payload(mapping, account)

                # Optionally inject groupName at a specific place if not in mapping
                # payload['groupContext'] = group_name
                print(payload)
                # post_account_data(post_url, token, payload)

    except Exception as e:
        print(f"[X] Critical Error: {e}")


if __name__ == "__main__":
    main()