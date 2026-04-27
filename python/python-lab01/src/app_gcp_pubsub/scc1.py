import os
import json
import time
from datetime import datetime
from google.cloud import pubsub_v1
from google.cloud import storage

# --- Configuration ---
# It's best practice to set these via environment variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
SUBSCRIPTION_ID = os.getenv("GCP_SUBSCRIPTION_ID", "your-subscription-id")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-target-bucket")
# ---------------------

# Initialize Clients
storage_client = storage.Client()
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)


def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    """Processes the incoming Pub/Sub message and saves to GCS."""
    try:
        # 1. Extract message data
        data = message.data.decode("utf-8")
        msg_id = message.message_id

        # 2. Generate a unique filename using timestamp and message ID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"findings/msg_{timestamp}_{msg_id}.json"

        print(f"[*] Received message {msg_id}. Writing to {filename}...")

        # 3. Upload to GCS
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(data, content_type='application/json')

        # 4. Acknowledge the message so it's not redelivered
        message.ack()
        print(f"[+] Successfully stored and ACKed message {msg_id}")

    except Exception as e:
        print(f"[!] Error processing message {message.message_id}: {e}")
        # Nack tells Pub/Sub to try sending this message again later
        message.nack()


def listen_to_pubsub():
    """Starts the subscriber loop."""
    print(f"--- Listening for messages on {subscription_path} ---")

    # flow_control helps manage memory if your bucket is slow
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=callback,
        flow_control=pubsub_v1.types.FlowControl(max_messages=10)
    )

    with subscriber:
        try:
            # Keep the main thread alive while the subscriber works in the background
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print("\n--- Subscriber stopped by user ---")
        except Exception as e:
            streaming_pull_future.cancel()
            print(f"--- Subscriber failed: {e} ---")


if __name__ == "__main__":
    # Ensure bucket exists or permissions are correct before starting
    try:
        storage_client.get_bucket(BUCKET_NAME)
        listen_to_pubsub()
    except Exception as e:
        print(f"Critical Error: Could not access bucket {BUCKET_NAME}. {e}")

