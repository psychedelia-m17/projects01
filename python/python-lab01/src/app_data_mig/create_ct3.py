import yaml
import requests
from requests.auth import HTTPBasicAuth
from glom import glom
import json
import logging
import http.client


config_file='create_ct_cfg_main_ac.yml'

# http.client.HTTPConnection.debuglevel = 1
# logging.basicConfig()
# logging.getLogger("urllib3").setLevel(logging.DEBUG)

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_token(config):
    auth_cfg = config['auth']
    print(f"[*] Obtaining token via GET for tenant: {auth_cfg['tenantId']}...")

    headers = {
        "Accept": "application/json",
        "x-tenant-id": auth_cfg['tenantId']
    }

    response = requests.get(
        auth_cfg['token_url'],
        auth=HTTPBasicAuth(auth_cfg['username'], auth_cfg['password']),
        headers=headers
    )
    # print(f"Status Code = {response.status_code}")
    # print(f"Headers = {response.headers}")
    # print(f"Body = {response.text}")

    response.raise_for_status()
    return response.json().get('token')


def build_nested_payload(mapping_level, account_data):
    """
    Recursively builds the payload.
    Strings starting with $ are treated as YAML paths (glom).
    Other strings are treated as static values.
    """
    payload = {}
    for key, value in mapping_level.items():
        if isinstance(value, dict):
            payload[key] = build_nested_payload(value, account_data)
        elif isinstance(value, str) and value.startswith("$"):
            # Dynamic mapping: Strip the '$' and use glom
            yaml_path = value[1:]
            try:
                payload[key] = glom(account_data, yaml_path)
            except Exception:
                payload[key] = None
        else:
            # Static mapping: Use value as-is
            payload[key] = value
    return payload


def post_account_data(url, token, tenant_id, payload):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'x-tenant-id': tenant_id
    }
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print(f"  [+] Success")
    else:
        print(f"  [!] Failed: {response.status_code} - {response.text}")


def main():
    config = load_yaml(config_file)
    groups = load_yaml(config['payload_source']['data_file'])
    tenant_id = config['auth']['tenantId']

    try:
        # Get token using the new GET logic
        # token = get_token(config)
        # print(token)
        mapping = config['payload_source']['mapping']
        post_url = config['api']['post_url']

        for group in groups:
            print(f"\n>>> Processing Group: {group.get('groupName')}")
            accounts = group.get('accounts', [])

            for account in accounts:
                # Build payload with static vs dynamic logic
                payload = build_nested_payload(mapping, account)
                print(payload)
                # post_account_data(post_url, token, tenant_id, payload)

    except Exception as e:
        print(f"[X] Critical Error: {e}")


if __name__ == "__main__":
    main()
