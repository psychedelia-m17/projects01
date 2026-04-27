import sys
import argparse
import yaml
import re
from kubernetes import client, config


class K8sYamlManager:
    def __init__(self, config_path):
        try:
            with open(config_path, 'r') as f:
                self.full_cfg = yaml.safe_load(f)
        except Exception as e:
            print(f"Error: Could not read YAML file at {config_path}: {e}")
            sys.exit(1)

        # Load Kubeconfig
        kubeconfig_path = self.full_cfg.get("kubeconfig_path")
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            config.load_kube_config()

        self.apps_cfg = self.full_cfg.get("apps", {})
        # Get the regex from config, default to match nothing if not provided
        self.env_regex = self.full_cfg.get("envVarNameRegex", "$^")

        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()

    def get_resource(self, resource_type, name, namespace):
        try:
            if resource_type == 'Deployment':
                return self.apps_v1.read_namespaced_deployment(name, namespace)
            elif resource_type == 'StatefulSet':
                return self.apps_v1.read_namespaced_stateful_set(name, namespace)
            elif resource_type == 'DaemonSet':
                return self.apps_v1.read_namespaced_daemon_set(name, namespace)
        except client.exceptions.ApiException:
            print(f"  ⚠️  NotFound: {resource_type} '{name}' in '{namespace}'")
        return None

    def list_resources(self):
        print(f"\n{'NAMESPACE':<15} {'TYPE':<15} {'NAME':<40} {'REPS':<6} {'IMAGE'}")
        print("=" * 100)

        for ns, resources in self.apps_cfg.items(): #{ for1: begin
            for res in resources: #{ for2: begin
                rtype = res['resourceType']
                name = res['name']

                obj = self.get_resource(rtype, name, ns)
                if not obj: continue

                current_reps = obj.spec.replicas if rtype != 'DaemonSet' else "N/A"
                container = obj.spec.template.spec.containers[0]
                current_image = container.image

                # 1. Filter Environment Variables by Regex
                matched_envs = []
                if container.env:
                    for env_var in container.env:
                        if re.match(self.env_regex, env_var.name):
                            # Handle both direct values and valueFrom (Secrets/ConfigMaps)
                            val = env_var.value if env_var.value is not None else "[ValueFrom Reference]"
                            matched_envs.append(f"{env_var.name}={val}")

                # 2. Fetch Pod Names
                labels = obj.spec.selector.match_labels
                label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
                pods = self.core_v1.list_namespaced_pod(ns, label_selector=label_str)
                pod_names = [p.metadata.name for p in pods.items]

                # Output
                print(f"{ns:<15} {rtype:<15} {name:<40} {current_reps:<6} {current_image}")
                if matched_envs:
                    print(f"   |- Matched Env: {', '.join(matched_envs)}")
                if pod_names:
                    print(f"   |- Pods: {', '.join(pod_names)}")
                else:
                    print(f"   |- Pods: None")
                print("")
            #} for2: end
            print("-" * 100)
        #} for1: end

    def perform_action(self, action):
        for ns, resources in self.apps_cfg.items():
            for res in resources:
                skip = res['skip']
                rtype = res['resourceType']
                name = res['name']
                target_reps = res.get('replicas', 1) if action == "scale-up" else 0
                target_image = res.get('image')

                if skip:
                    print(f"Skipping {rtype}/{name}...")
                    continue

                obj = self.get_resource(rtype, name, ns)
                if not obj: continue

                print(f"*  {action.upper()}: {rtype}/{name}...")

                if target_image:
                    for container in obj.spec.template.spec.containers:
                        container.image = target_image

                if rtype != 'DaemonSet':
                    obj.spec.replicas = target_reps

                try:
                    if rtype == 'Deployment':
                        self.apps_v1.patch_namespaced_deployment(name, ns, obj)
                    elif rtype == 'StatefulSet':
                        self.apps_v1.patch_namespaced_stateful_set(name, ns, obj)
                    elif rtype == 'DaemonSet':
                        self.apps_v1.patch_namespaced_daemon_set(name, ns, obj)
                    print(f"Success")
                except Exception as e:
                    print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="K8s Manager with Regex Env Filtering")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--action", choices=['scale-up', 'scale-down', 'list'], required=True)

    args = parser.parse_args()
    manager = K8sYamlManager(args.config)

    if args.action == 'list':
        manager.list_resources()
    else:
        manager.perform_action(args.action)


if __name__ == "__main__":
    main()
