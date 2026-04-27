import os
import sys
import argparse
import ast
from dotenv import load_dotenv
from kubernetes import client, config

"""
K8s utility for managing Deployments and StatefulSet replica count and images.
Dependencies: 
pip install kubernetes python-dotenv
"""

class K8sManager:
    def __init__(self, env_path):
        # Load environment variables from the provided path
        if not os.path.exists(env_path):
            print(f"Error: .env file not found at {env_path}")
            sys.exit(1)

        load_dotenv(env_path)

        # Setup Kubernetes Configuration
        kubeconfig_path = os.getenv("KUBECONFIG_PATH")
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            config.load_kube_config()  # Default location ~/.kube/config

        self.apps_cfg = ast.literal_eval(os.getenv("APPS", "{}"))
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()

    def get_resource(self, resource_type, name, namespace):
        """Helper to fetch the specific K8s object API."""
        try:
            if resource_type == 'Deployment':
                return self.apps_v1.read_namespaced_deployment(name, namespace)
            elif resource_type == 'StatefulSet':
                return self.apps_v1.read_namespaced_stateful_set(name, namespace)
            elif resource_type == 'DaemonSet':
                return self.apps_v1.read_namespaced_daemon_set(name, namespace)
        except Exception as e:
            print(f"Error fetching {resource_type} {name}: {e}")
        return None

    def list_resources(self):
        print(f"{'NAMESPACE':<15} {'TYPE':<15} {'NAME':<20} {'REPLICAS':<10} {'IMAGE'}")
        print("-" * 80)

        for ns, resources in self.apps_cfg.items():
            for res in resources:
                rtype = res['resourceType']
                name = res['name']

                obj = self.get_resource(rtype, name, ns)
                if not obj:
                    continue

                # Get current stats
                # DaemonSets don't have a 'replicas' field in spec like others
                current_reps = obj.spec.replicas if rtype != 'DaemonSet' else "N/A"
                current_image = obj.spec.template.spec.containers[0].image

                # Get Pod Names
                pods = self.core_v1.list_namespaced_pod(ns, label_selector=",".join(
                    [f"{k}={v}" for k, v in obj.spec.selector.match_labels.items()]))
                pod_names = [p.metadata.name for p in pods.items]

                print(f"{ns:<15} {rtype:<15} {name:<20} {current_reps:<10} {current_image}")
                print(f"   └─ Pods: {', '.join(pod_names) if pod_names else 'None'}\n")

    def scale_and_image(self, action):
        for ns, resources in self.apps_cfg.items():
            for res in resources:
                rtype = res['resourceType']
                name = res['name']
                target_reps = res.get('replicas', 1) if action == "scale-up" else 0
                target_image = res.get('image')

                print(f"Action [{action}] on {rtype} {name} in {ns}...")

                body = self.get_resource(rtype, name, ns)
                if not body:
                    continue

                # Update Image
                for container in body.spec.template.spec.containers:
                    if target_image:
                        container.image = target_image

                # Update Replicas (DaemonSets are skipped for scaling as they depend on nodes)
                if rtype != 'DaemonSet':
                    body.spec.replicas = target_reps

                try:
                    if rtype == 'Deployment':
                        self.apps_v1.patch_namespaced_deployment(name, ns, body)
                    elif rtype == 'StatefulSet':
                        self.apps_v1.patch_namespaced_stateful_set(name, ns, body)
                    elif rtype == 'DaemonSet':
                        self.apps_v1.patch_namespaced_daemon_set(name, ns, body)
                    print(f"Successfully updated {name}")
                except Exception as e:
                    print(f"Failed to update {name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="K8s Resource Manager")
    parser.add_argument("--env", required=True, help="Path to the .env file")
    parser.add_argument("--action", choices=['scale-up', 'scale-down', 'list'], required=True,
                        help="Operation to perform: scale target replicas/image, scale to 0, or list status")

    args = parser.parse_args()
    manager = K8sManager(args.env)

    if args.action == 'list':
        manager.list_resources()
    else:
        manager.scale_and_image(args.action)


if __name__ == "__main__":
    main()
