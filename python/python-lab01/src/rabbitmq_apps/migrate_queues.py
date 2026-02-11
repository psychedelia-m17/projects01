import requests
import re
import json
import sys
import urllib3

# Suppress InsecureRequestWarning if verify_ssl is False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)


def api_call(method, config, endpoint, data=None):
    """Handles HTTP/HTTPS calls with optional SSL verification."""
    protocol = config.get("protocol", "http")
    verify = config.get("verify_ssl", True)

    url = f"{protocol}://{config['host']}:{config['port']}/api/{endpoint}"
    auth = (config['user'], config['pass'])

    try:
        if method == "GET":
            resp = requests.get(url, auth=auth, verify=verify)
        elif method == "PUT":
            resp = requests.put(url, auth=auth, json=data, verify=verify)
        elif method == "POST":
            resp = requests.post(url, auth=auth, json=data, verify=verify)

        resp.raise_for_status()
        return resp.json() if method == "GET" else resp.status_code
    except requests.exceptions.SSLError:
        print(f"Error: SSL Verification failed for {url}. Set 'verify_ssl': false in config.")
        sys.exit(1)
    except Exception as e:
        print(f"Error calling {url}: {e}")
        raise


# --- Mode 1: Export ---
def export_metadata(config):
    source = config['source']
    settings = config['settings']

    print(f"[*] Exporting from {source['host']} ({source['protocol']})...")

    # 1. Fetch ALL queues
    all_queues = api_call("GET", source, "queues")
    pattern = re.compile(settings['queue_regex'])

    # Filter queues by pattern
    matched_queues = [q for q in all_queues if pattern.search(q['name'])]
    matched_names = {q['name'] for q in matched_queues}

    # 2. Fetch ALL bindings and filter for matched queues
    all_bindings = api_call("GET", source, "bindings")
    matched_bindings = [
        b for b in all_bindings
        if b['destination'] in matched_names and b['destination_type'] == 'queue' and b['source']
    ]

    payload = {
        "metadata_version": "1.1",
        "queues": matched_queues,
        "bindings": matched_bindings
    }

    with open(settings['export_file'], "w") as f:
        json.dump(payload, f, indent=4)
    print(f"[+] Successfully exported {len(matched_queues)} queues and {len(matched_bindings)} bindings.")


# --- Mode 2: Import ---
def import_metadata(config):
    target = config['target']
    settings = config['settings']

    print(f"[*] Importing to {target['host']} ({target['protocol']})...")

    with open(settings['export_file'], "r") as f:
        data = json.load(f)

    # 1. Create Queues
    for q in data['queues']:
        q_body = {
            "auto_delete": q["auto_delete"],
            "durable": q["durable"],
            "arguments": q["arguments"]
        }
        endpoint = f"queues/{target['vhost']}/{q['name']}"
        api_call("PUT", target, endpoint, q_body)
        print(f"    - Queue '{q['name']}' created/synced.")

    # 2. Create Bindings
    for b in data['bindings']:
        if not b['source']:
            print(f"Queue {b['destination']}: Skipping binding to default exchange")
            continue
        b_body = {"routing_key": b["routing_key"], "arguments": b["arguments"]}
        # Note: Exchanges must exist on the target for bindings to work
        endpoint = f"bindings/{target['vhost']}/e/{b['source']}/q/{b['destination']}"
        api_call("POST", target, endpoint, b_body)
        print(f"    - Binding '{b['source']}' -> '{b['destination']}' created.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py [export|import]")
        sys.exit(1)

    action = sys.argv[1].lower()
    config_data = load_config("config.json")

    if action == "export":
        export_metadata(config_data)
    elif action == "import":
        import_metadata(config_data)
    else:
        print("Invalid action. Use 'export' or 'import'.")
