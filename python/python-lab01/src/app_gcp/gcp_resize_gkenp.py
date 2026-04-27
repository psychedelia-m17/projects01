import argparse
import time
import yaml
import sys
import google.auth
from google.cloud import container_v1


def load_config(config_path):
    """Loads the YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_project_id():
    """Detects the Google Cloud Project ID."""
    _, project_id = google.auth.default()
    return project_id


def list_action(client, project_id, config):
    """Execution logic for the --list command."""
    cluster = config['cluster_name']
    location = config['location']
    parent = f"projects/{project_id}/locations/{location}/clusters/{cluster}"

    request = container_v1.ListNodePoolsRequest(parent=parent)
    response = client.list_node_pools(request=request)

    print(f"\n{'NAME':<25} {'MACHINE_TYPE':<20} {'NODES/ZONE':<12} {'TOTAL':<8} {'LOCATIONS'}")
    print("-" * 110)
    for pool in response.node_pools:
        zones = pool.locations
        num_zones = len(zones)
        # Fix: Use initial_node_count
        node_count_per_zone = pool.initial_node_count
        total_nodes = node_count_per_zone * num_zones

        zone_list = ", ".join(zones)
        print(f"{pool.name:<25} {pool.config.machine_type:<20} {node_count_per_zone:<12} {total_nodes:<8} {zone_list}")
    print("-" * 110 + "\n")


def resize_action(client, project_id, config, mode):
    """Execution logic for --start and --shutdown commands."""
    cluster = config['cluster_name']
    location = config['location']
    pools = config.get('node_pools', [])
    interval = config.get('polling_interval', 10)

    targets = {}
    print(f"--- Initiating {mode.upper()} for {cluster} ---")

    # 1. Dispatch Async Resize Requests
    for pool in pools:
        pool_name = pool['name']
        target_size = 0 if mode == "shutdown" else pool['target_size']
        targets[pool_name] = target_size

        # Build the full resource path
        resource_name = f"projects/{project_id}/locations/{location}/clusters/{cluster}/nodePools/{pool_name}"

        try:
            # FIX: Use the 'request' dictionary to avoid argument name conflicts
            client.set_node_pool_size(request={
                "name": resource_name,
                "node_count": target_size
            })
            print(f"-> Requested size {target_size} for pool: {pool_name}")
        except Exception as e:
            print(f"!! Error requesting resize for {pool_name}: {e}")

    # 2. Polling Loop
    print(f"\nWaiting for convergence (Polling every {interval}s)...")
    while True:
        all_ready = True
        status_line = []

        for pool_name, desired in targets.items():
            resource_name = f"projects/{project_id}/locations/{location}/clusters/{cluster}/nodePools/{pool_name}"
            pool_data = client.get_node_pool(name=resource_name)

            # GKE API: initial_node_count is the target count per zone
            current = pool_data.initial_node_count
            status = pool_data.status.name

            # A pool is "ready" if it matches the target AND isn't busy reconciling
            # Note: When scaling to 0, status often hits 'RUNNING' or 'STOPPING'
            # while count is 0.
            if current != desired or status == "RECONCILING":
                all_ready = False

            status_line.append(f"{pool_name}: {current}/{desired} ({status})")

        if all_ready:
            print("\n\nSuccess: All node pools have reached target sizes and are stable.")
            break
        else:
            # Clear the line and print update
            sys.stdout.write("\r" + " | ".join(status_line) + "   ")
            sys.stdout.flush()
            time.sleep(interval)


if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="GKE Node Pool Automation Tool")
    parser.add_argument("-c", "--config", required=True, help="Path to the config.yaml file")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--start", action="store_true", help="Resize pools to configured targets")
    group.add_argument("-d", "--shutdown", action="store_true", help="Resize all pools to zero")
    group.add_argument("-l", "--list", action="store_true", help="List current node pool status")

    args = parser.parse_args()

    # --- Initialization ---
    cfg = load_config(args.config)
    gke_client = container_v1.ClusterManagerClient()
    proj_id = get_project_id()

    print(f"GCP Project ID: {proj_id}")

    # --- Dispatcher ---
    if args.list:
        list_action(gke_client, proj_id, cfg)
    elif args.start:
        print(f"Start pools to configured targets")
        resize_action(gke_client, proj_id, cfg, mode="start")
    elif args.shutdown:
        print(f"Stop pools")
        resize_action(gke_client, proj_id, cfg, mode="shutdown")

