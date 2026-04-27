import os
import re
import argparse
import requests
from datetime import datetime, timezone
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
            print(f"[-] Error fetching tags: {response.status_code}")
            break

        data = response.json()
        tags.extend(data.get('results', []))
        url = data.get('next')

    return tags


def format_full_dt_and_age(iso_date_str):
    """Returns 'YYYY-MM-DD HH:MM:SS UTC (age)'."""
    if not iso_date_str:
        return "Never"

    dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
    full_dt = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    now = datetime.now(timezone.utc)
    diff = now - dt

    if diff.days > 365:
        age = f"{diff.days // 365}y ago"
    elif diff.days > 0:
        age = f"{diff.days}d ago"
    elif diff.seconds > 3600:
        age = f"{diff.seconds // 3600}h ago"
    else:
        age = "Just now"

    return f"{full_dt} ({age})"


def delete_tag(username, repo, tag_name, token):
    """Deletes a specific tag from the repository."""
    url = f"https://hub.docker.com/v2/repositories/{username}/{repo}/tags/{tag_name}/"
    headers = {"Authorization": f"JWT {token}"}
    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print(f"[+] Successfully deleted: {tag_name}")
    else:
        print(f"[-] Failed to delete {tag_name}: {response.status_code}")


def main():
    parser = argparse.ArgumentParser(description="Docker Hub Manager")
    parser.add_argument("-u", "--username", required=True, help="Docker Hub username")
    parser.add_argument("-r", "--repository", required=True, help="Repository name")
    parser.add_argument("-t", "--tags", default=".*", help="Regex for tags to INCLUDE (default: .*)")
    parser.add_argument("-e", "--exclude", default=None, help="Regex for tags to EXCLUDE")
    parser.add_argument("-a", "--action", choices=["list", "delete"], default="list")

    args = parser.parse_args()

    pat = os.getenv("DH_PAT")
    if not pat:
        print("[-] Error: DH_PAT not found in .env or environment variables.")
        exit(1)

    token = get_jwt(args.username, pat)
    all_tags = get_tags(args.username, args.repository, token)

    # Compilation of regexes
    include_re = re.compile(args.tags)
    exclude_re = re.compile(args.exclude) if args.exclude else None

    # Filtering Logic:
    # 1. Match the include regex
    # 2. Filter out anything that matches the exclude regex
    matched_tags = []
    for t in all_tags:
        name = t['name']
        if include_re.match(name):
            if exclude_re and exclude_re.match(name):
                continue
            matched_tags.append(t)

    if not matched_tags:
        print("[!] No tags matched the specified criteria.")
        return

    # Column Widths
    tag_w = 80
    date_w = 40

    if args.action == "list":
        header = f"{'TAG NAME':<{tag_w}} {'PUSHED':<{date_w}} {'LAST PULLED':<{date_w}}"
        print(f"\n{header}")
        print("-" * (tag_w + date_w + date_w))

        for t in matched_tags:
            tag_name = t['name']
            pushed_info = format_full_dt_and_age(t.get('last_updated'))
            pulled_info = format_full_dt_and_age(t.get('last_pulled'))
            print(f"{tag_name:<{tag_w}} {pushed_info:<{date_w}} {pulled_info:<{date_w}}")

    elif args.action == "delete":
        print(f"\n[!] The following {len(matched_tags)} tags are marked for DELETION:")
        for t in matched_tags:
            pushed = format_full_dt_and_age(t.get('last_updated'))
            print(f" - {t['name']:<40} (Pushed: {pushed})")

        confirm = input(f"\nConfirm deletion of {len(matched_tags)} tags? (y/N): ")
        if confirm.lower() == 'y':
            for t in matched_tags:
                delete_tag(args.username, args.repository, t['name'], token)
        else:
            print("[*] Aborted.")


if __name__ == "__main__":
    main()

