import argparse
import yaml
import boto3
import os
import re
from botocore.client import Config
from botocore.exceptions import ClientError


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_s3_client(config):
    return boto3.client(
        's3',
        endpoint_url=config['s3_url'],
        aws_access_key_id=config['access_key'],
        aws_secret_access_key=config['secret'],
        config=Config(signature_version='s3v4')
    )


def list_buckets(client, config):
    """Lists all buckets available on the account/endpoint."""
    print(f"--- Fetching All Buckets from {config['s3_url']} ---")
    try:
        response = client.list_buckets()
        print(f"{'BUCKET NAME':<40} {'CREATION DATE'}")
        print("-" * 65)
        for bucket in response.get('Buckets', []):
            print(f"{bucket['Name']:<40} {bucket['CreationDate']}")
    except ClientError as e:
        print(f"Error listing buckets: {e}")


def create_buckets(client, config):
    for name in config['buckets']:
        print(f"--- Creating Bucket: {name} ---")
        try:
            client.create_bucket(Bucket=name)
            print(f"Successfully created: {name}")
        except ClientError as e:
            print(f"Error creating {name}: {e}")


def delete_buckets(client, config):
    for name in config['buckets']:
        print(f"--- Deleting Bucket: {name} ---")
        try:
            # Empty bucket first
            paginator = client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=name):
                if 'Contents' in page:
                    items = [{'Key': obj['Key']} for obj in page['Contents']]
                    client.delete_objects(Bucket=name, Delete={'Objects': items})

            client.delete_bucket(Bucket=name)
            print(f"Successfully deleted: {name}")
        except ClientError as e:
            print(f"Error deleting {name}: {e}")


def upload_files(client, config):
    target_prefix = config['target_path'].strip('/')
    local_reg = re.compile(config['local_regex'])

    for bucket in config['buckets']:
        print(f"--- Uploading to Bucket: {bucket} ---")
        for root, _, files in os.walk("."):
            for file in files:
                clean_path = os.path.relpath(os.path.join(root, file))
                if local_reg.match(clean_path):
                    remote_key = f"{target_prefix}/{clean_path}" if target_prefix else clean_path
                    try:
                        client.upload_file(clean_path, bucket, remote_key)
                        print(f"Uploaded: {clean_path} to {bucket}")
                    except ClientError as e:
                        print(f"Failed to upload {clean_path} to {bucket}: {e}")


def download_files(client, config):
    remote_prefix = config['target_path'].strip('/')
    root_download_dir = config['download_path']
    down_reg = re.compile(config['download_regex'])

    for bucket in config['buckets']:
        # Requirement: Create directory with bucket name under download_path
        bucket_local_dir = os.path.join(root_download_dir, bucket)
        os.makedirs(bucket_local_dir, exist_ok=True)

        print(f"--- Downloading from Bucket: {bucket} into {bucket_local_dir} ---")
        paginator = client.get_paginator('list_objects_v2')

        try:
            for page in paginator.paginate(Bucket=bucket, Prefix=remote_prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']

                        # Requirement: Filter by download_regex
                        if down_reg.match(key):
                            rel_path = os.path.relpath(key, remote_prefix) if remote_prefix else key
                            local_dest = os.path.join(bucket_local_dir, rel_path)

                            os.makedirs(os.path.dirname(local_dest), exist_ok=True)
                            client.download_file(bucket, key, local_dest)
                            print(f"Downloaded: {key} -> {local_dest}")
        except ClientError as e:
            print(f"Error accessing bucket {bucket}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Multi-Bucket S3/GCS Management Tool")
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
        "create": create_buckets,
        "delete": delete_buckets,
        "upload": upload_files,
        "download": download_files
    }

    actions[args.operation](s3, cfg)


if __name__ == "__main__":
    main()

