import sys
import argparse
import yaml
from kubernetes import client, config


class K8sYamlManager:
    def __init__(self, config_path):
        # Load the YAML configuration
        try:
            with open(config_path, 'r') as f:
                self.full_cfg = yaml.safe_load(f)
        except Exception as e:
            print(f"Error: Could not read YAML file at {config_path}: {e}")
            sys.exit(1)

        # Setup Kubernetes Configuration
        kubeconfig_path = self.full_cfg.get("kubeconfig_path")
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            config.load_kube_config()

        self.apps_cfg = self.full_cfg.get("apps", {})
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()

    def get_resource(self, resource_type, name, namespace):
        """Fetch the specific K8s object from the cluster."""
        try:
            if resource_type == 'Deployment':
                return self.apps_v1.read_namespaced_deployment(name, namespace)
            elif resource_type == 'StatefulSet':
                return self.apps_v1.read_namespaced_stateful_set(name, namespace)
            elif resource_type == 'DaemonSet':
                return self.apps_v1.read_namespaced_daemon_set(name, namespace)
        except client.exceptions.ApiException as e:
            print(f"NotFound: {resource_type} '{name}' in namespace '{namespace}'")
        return None


    def list_resources(self):
        print(f"\n{'NAMESPACE':<15} {'TYPE':<15} {'NAME':<40} {'REPS':<6} {'IMAGE'}")
        print("=" * 100)

        for ns, resources in self.apps_cfg.items():
            for res in resources:
                rtype = res['resourceType']
                name = res['name']

                obj = self.get_resource(rtype, name, ns)
                if not obj: continue

                # DaemonSets don't have a 'replicas' field in spec
                current_reps = obj.spec.replicas if rtype != 'DaemonSet' else "N/A"
                current_image = obj.spec.template.spec.containers[0].image

                # Fetch Pods using the resource's label selector
                labels = obj.spec.selector.match_labels
                label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
                pods = self.core_v1.list_namespaced_pod(ns, label_selector=label_str)
                pod_names = [p.metadata.name for p in pods.items]

                print(f"{ns:<15} {rtype:<15} {name:<40} {current_reps:<6} {current_image}")
                if pod_names:
                    print(f"   Pods: {', '.join(pod_names)}")
                else:
                    print(f"   Pods: (None running)")
            print("-" * 100)
        print("")


    def perform_action(self, action):
        for ns, resources in self.apps_cfg.items():
            for res in resources:
                rtype = res['resourceType']
                name = res['name']
                target_reps = res.get('replicas', 1) if action == "scale-up" else 0
                target_image = res.get('image')

                obj = self.get_resource(rtype, name, ns)
                if not obj: continue

                print(f"{action.upper()}: {rtype}/{name} in {ns}...")

                # 1. Update Image (all containers in the pod template)
                if target_image:
                    for container in obj.spec.template.spec.containers:
                        container.image = target_image

                # 2. Update Replicas (Skip for DaemonSets)
                if rtype != 'DaemonSet':
                    obj.spec.replicas = target_reps

                # 3. Apply Patch
                try:
                    if rtype == 'Deployment':
                        self.apps_v1.patch_namespaced_deployment(name, ns, obj)
                    elif rtype == 'StatefulSet':
                        self.apps_v1.patch_namespaced_stateful_set(name, ns, obj)
                    elif rtype == 'DaemonSet':
                        self.apps_v1.patch_namespaced_daemon_set(name, ns, obj)
                    print(f"Success")
                except Exception as e:
                    print(f"Error patching {name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="K8s YAML-based Manager")
    parser.add_argument("--config", required=True, help="Path to the YAML config file")
    parser.add_argument("--action", choices=['scale-up', 'scale-down', 'list'], required=True,
                        help="Action to perform")

    args = parser.parse_args()
    manager = K8sYamlManager(args.config)

    if args.action == 'list':
        manager.list_resources()
    else:
        manager.perform_action(args.action)


if __name__ == "__main__":
    main()