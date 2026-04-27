import os
import yaml
import json
from datetime import datetime
from google.cloud import pubsub_v1
from google.cloud import storage


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def callback(message: pubsub_v1.subscriber.message.Message, config, storage_client):
    """Processes message: writes to local file AND GCS bucket."""
    try:
        data = message.data.decode("utf-8")
        msg_id = message.message_id
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # 1. Write to Local File (Append mode)
        local_file = config['local_output_file']
        with open(local_file, "a") as f:
            # Writing as a log entry with a newline
            f.write(f"[{timestamp}] ID: {msg_id} | Data: {data}\n")

        # 2. Store in GCS Bucket (Unique file per message)
        bucket_name = config['bucket_name']
        # Creating a unique path in the bucket for this specific message
        gcs_filename = f"uploads/{datetime.utcnow().strftime('%Y/%m/%d')}/{msg_id}.json"

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_filename)
        blob.upload_from_string(data, content_type='application/json')

        print(f"--- Processed {msg_id} ---")
        print(f"Local: Appended to {local_file}")
        print(f"Cloud: Uploaded to gs://{bucket_name}/{gcs_filename}")

        # Acknowledge completion
        message.ack()

    except Exception as e:
        print(f"Error processing message {message.message_id}: {e}")
        message.nack()


def main():
    # Load settings
    cfg = load_config("config.yaml")

    # Initialize Clients
    storage_client = storage.Client(project=cfg['project_id'])
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        cfg['project_id'],
        cfg['subscription_id']
    )

    print(f"Listening for messages on {subscription_path}...")

    # We use a lambda to pass extra arguments (config and client) to the callback
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=lambda msg: callback(msg, cfg, storage_client)
    )

    with subscriber:
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print("\nStopped by user.")
        except Exception as e:
            streaming_pull_future.cancel()
            print(f"Stopped due to error: {e}")


if __name__ == "__main__":
    main()
