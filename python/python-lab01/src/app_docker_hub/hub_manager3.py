import os
import re
import argparse
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

"""
{
  "creator": 1495011,
  "id": 1109237100,
  "images": [
    {
      "architecture": "amd64",
      "features": "",
      "variant": null,
      "digest": "sha256:6f8f94d4a2d550e910b254c811d2df445df1903f481ca7d4e5cf0b838784ce4b",
      "os": "linux",
      "os_features": "",
      "os_version": null,
      "size": 1521559708,
      "status": "active",
      "last_pulled": "2026-03-25T11:11:09.764760756Z",
      "last_pushed": "2026-03-23T09:48:41.785816492Z"
    }
  ],
  "last_updated": "2026-03-23T09:48:42.07709Z",
  "last_updater": 1495011,
  "last_updater_username": "theco***",
  "name": "v4.4-oo***-oo***-0323-0244",
  "repository": 19134859,
  "full_size": 1521559708,
  "v2": true,
  "tag_status": "active",
  "tag_last_pulled": "2026-03-25T11:11:09.764760756Z",
  "tag_last_pushed": "2026-03-23T09:48:42.07709Z",
  "media_type": "application/vnd.docker.container.image.v1+json",
  "content_type": "image",
  "digest": "sha256:6f8f94d4a2d550e910b254c811d2df445df1903f481ca7d4e5cf0b838784ce4b"
}
"""

# Load environment variables from .env
load_dotenv()


def get_jwt(username, pat):
    """Authenticates with Docker Hub and returns a JWT token."""
    url = "https://hub.docker.com/v2/users/login/"
    payload = {"username": username, "password": pat}

    print(f"[*] Authenticating as: {username} ...")
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"[-] Authentication failed: {response.json().get('detail')}")
        exit(1)
    else:
        print(f"[*] Authentication successful for: {username}")

    return response.json().get('token')


def get_tags(username, repo, token):
    """Fetches all tags for a repository, handling pagination."""
    tags = []
    # url = f"https://hub.docker.com/v2/repositories/{username}/{repo}/tags/"
    url = f"https://hub.docker.com/v2/repositories/{username}/{repo}/tags?page_size=100"
    headers = {"Authorization": f"JWT {token}"}

    print(f"[*] Fetching tags for {username}/{repo} ...")
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

    # Parse the timestamp
    dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
    full_dt = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Calculate relative age
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
    parser.add_argument("-t", "--tags", default=".*", help="Regex for tags")
    parser.add_argument("-e", "--exclude", default=None, help="Regex for tags to EXCLUDE")
    parser.add_argument("-a", "--action", choices=["list", "delete"], default="list")

    args = parser.parse_args()

    pat = os.getenv("DH_PAT")
    if not pat:
        print("[-] Error: DH_PAT not found. Ensure it is set in your .env file.")
        exit(1)

    token = get_jwt(args.username, pat)
    all_tags = get_tags(args.username, args.repository, token)

    # Compilation of regexes
    # regex = re.compile(args.tags)
    include_re = re.compile(args.tags)
    exclude_re = re.compile(args.exclude) if args.exclude else None

    # Filtering Logic:
    # 1. Match the include regex
    # 2. Filter out anything that matches the exclude regex
    matched_tags = []
    excluded_count: int = 0
    for t in all_tags:
        name = t['name']
        if include_re.match(name):
            if exclude_re and exclude_re.match(name):
                excluded_count += 1
                continue
            matched_tags.append(t)


    if not matched_tags:
        print("[!] No tags matched your regex.")
        return
    else:
        print(100 * '=')
        print(f"[*] Tags: Total = {len(all_tags)}, Matched = {len(matched_tags)}, Excluded = {excluded_count}")
        print(100 * '=')

    # Column Width Definitions
    tag_w = 80
    date_w = 40
    size_w = 10

    if args.action == "list":
        # Header setup
        header = f"{'TAG NAME':<{tag_w}} {'PUSHED':<{date_w}} {'LAST PULLED':<{date_w}} {'SIZE (MB)':<{size_w}}"
        print(f"\n{header}")
        print("-" * (tag_w + date_w + date_w + size_w))

        for t in matched_tags:
            tag_name = t['name']
            pushed_info = format_full_dt_and_age(t.get('tag_last_pushed'))
            pulled_info = format_full_dt_and_age(t.get('tag_last_pulled'))
            full_size = t.get('full_size')/1024/1024

            print(f"{tag_name:<{tag_w}} {pushed_info:<{date_w}} {pulled_info:<{date_w}} {full_size:<{size_w}}")

    elif args.action == "delete":
        print(f"\n[!] Matching tags for deletion:")
        for t in matched_tags:
            pulled = format_full_dt_and_age(t.get('tag_last_pulled'))
            print(f" - {t['name']:<40} (Last pulled: {pulled})")

        confirm = input(f"\nConfirm deletion of {len(matched_tags)} tags? (y/N): ")
        if confirm.lower() == 'y':
            for t in matched_tags:
                delete_tag(args.username, args.repository, t['name'], token)
        else:
            print("[*] Deletion aborted.")


if __name__ == "__main__":
    main()

