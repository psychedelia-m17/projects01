import argparse
import yaml
import boto3
import os
import re
import sys
from botocore.client import Config
from botocore.exceptions import ClientError


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_s3_client(config):
    """Initializes the client using the configurable S3 URL."""
    return boto3.client(
        's3',
        endpoint_url=config['s3_url'],
        aws_access_key_id=config['access_key'],
        aws_secret_access_key=config['secret'],
        config=Config(signature_version='s3v4')
    )


def list_buckets(client, config):
    """Lists all buckets available on the endpoint."""
    print(f"--- Fetching Bucket List from {config['s3_url']} ---")
    try:
        response = client.list_buckets()
        print(f"{'BUCKET NAME':<40} {'CREATION DATE'}")
        print("-" * 65)
        for bucket in response.get('Buckets', []):
            print(f"{bucket['Name']:<40} {bucket['CreationDate']}")
    except ClientError as e:
        print(f"Error listing buckets: {e}")


def create_bucket(client, config):
    name = config['bucket_name']
    print(f"--- Creating Bucket: {name} ---")
    try:
        client.create_bucket(Bucket=name)
        print(f"Successfully created: {name}")
    except ClientError as e:
        print(f"Error creating bucket: {e}")


def delete_bucket(client, config):
    name = config['bucket_name']
    print(f"--- Deleting Bucket: {name} ---")
    try:
        print("Emptying bucket contents...")
        paginator = client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=name):
            if 'Contents' in page:
                items = [{'Key': obj['Key']} for obj in page['Contents']]
                client.delete_objects(Bucket=name, Delete={'Objects': items})

        client.delete_bucket(Bucket=name)
        print(f"Successfully deleted: {name}")
    except ClientError as e:
        print(f"Error deleting bucket: {e}")


def upload_files(client, config):
    bucket = config['bucket_name']
    target_prefix = config['target_path'].strip('/')
    regex = re.compile(config['local_regex'])

    print(f"--- Uploading to {bucket} ---")
    for root, _, files in os.walk("."):
        for file in files:
            clean_path = os.path.relpath(os.path.join(root, file))
            if regex.match(clean_path):
                remote_key = f"{target_prefix}/{clean_path}" if target_prefix else clean_path
                client.upload_file(clean_path, bucket, remote_key)
                print(f"Uploaded: {clean_path}")


def download_files(client, config):
    bucket = config['bucket_name']
    remote_prefix = config['target_path'].strip('/')
    local_dir = config['download_path']

    print(f"--- Downloading from {bucket} ---")
    os.makedirs(local_dir, exist_ok=True)
    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=remote_prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                rel_path = os.path.relpath(key, remote_prefix) if remote_prefix else key
                local_path = os.path.join(local_dir, rel_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                client.download_file(bucket, key, local_path)
                print(f"Downloaded: {key}")


def main():
    parser = argparse.ArgumentParser(description="Multi-Service S3/GCS Management Tool")
    parser.add_argument("-c", "--config", required=True, help="Path to YAML config")
    parser.add_argument(
        "-o", "--operation",
        required=True,
        choices=["list", "create", "delete", "upload", "download"],
        help="Operation to perform"
    )

    args = parser.parse_args()
    cfg = load_config(args.config)
    s3 = get_s3_client(cfg)

    actions = {
        "list": list_buckets,
        "create": create_bucket,
        "delete": delete_bucket,
        "upload": upload_files,
        "download": download_files
    }

    actions[args.operation](s3, cfg)


if __name__ == "__main__":
    main()

