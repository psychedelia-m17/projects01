import os
import re
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def get_jwt(username, pat):
    """Authenticates with Docker Hub and returns a JWT token."""
    url = "https://hub.docker.com/v2/users/login/"
    payload = {"username": username, "password": pat}
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"[-] Authentication failed: {response.json().get('detail')}")
        exit(1)

    return response.json().get('token')


def get_tags(username, repo, token):
    """Fetches all tags for a repository, handling pagination."""
    tags = []
    url = f"https://hub.docker.com/v2/repositories/{username}/{repo}/tags/"
    headers = {"Authorization": f"JWT {token}"}

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[-] Error fetching tags: {response.status_code} - {response.text}")
            break

        data = response.json()
        tags.extend(data.get('results', []))
        url = data.get('next')  # Handle pagination

    return tags


def delete_tag(username, repo, tag_name, token):
    """Deletes a specific tag from the repository."""
    url = f"https://hub.docker.com/v2/repositories/{username}/{repo}/tags/{tag_name}/"
    headers = {"Authorization": f"JWT {token}"}
    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print(f"[+] Successfully deleted tag: {tag_name}")
    else:
        print(f"[-] Failed to delete tag {tag_name}: {response.status_code}")


def main():
    parser = argparse.ArgumentParser(description="Docker Hub Repository Manager")
    parser.add_argument("-u", "--username", required=True, help="Docker Hub username")
    parser.add_argument("-r", "--repository", required=True, help="Repository name")
    parser.add_argument("-t", "--tags", default=".*", help="Regex for tags to match (default: .*)")
    parser.add_argument("-a", "--action", choices=["list", "delete"], default="list",
                        help="Action to perform (default: list)")

    args = parser.parse_args()

    # Get PAT from environment
    pat = os.getenv("DH_PAT")
    if not pat:
        print("[-] Error: DH_PAT environment variable not set.")
        exit(1)

    print(f"[*] Authenticating as {args.username}...")
    token = get_jwt(args.username, pat)

    print(f"[*] Fetching tags for {args.username}/{args.repository}...")
    all_tags = get_tags(args.username, args.repository, token)

    # Filter tags based on regex
    regex = re.compile(args.tags)
    matched_tags = [t['name'] for t in all_tags if regex.match(t['name'])]

    if not matched_tags:
        print("[!] No tags matched the provided regex.")
        return

    if args.action == "list":
        print(f"\n[+] Matched Tags ({len(matched_tags)}):")
        for tag in matched_tags:
            print(f" - {tag}")

    elif args.action == "delete":
        confirm = input(f"\n[!] WARNING: About to delete {len(matched_tags)} tags. Proceed? (y/N): ")
        if confirm.lower() == 'y':
            for tag in matched_tags:
                delete_tag(args.username, args.repository, tag, token)
        else:
            print("[*] Operation cancelled.")


if __name__ == "__main__":
    main()

