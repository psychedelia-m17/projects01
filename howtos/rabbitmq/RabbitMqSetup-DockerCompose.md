This setup completely decouples Traefik's routing logic from your Docker Compose labels, moving everything into the dynamic file provider. This is a much cleaner approach for production-grade environments where you want to manage routing separately from infrastructure.

---

## 1. Docker Infrastructure

We have removed all `traefik.*` labels from the RabbitMQ service. Traefik will now look for the `rabbitmq` service name on the internal Docker network.

### `docker-compose.yml`

```yaml
services:
  traefik:
    image: traefik:v3.1
    container_name: traefik
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yaml:ro
      - ./traefik/dynamic_conf.yml:/etc/traefik/dynamic_conf.yaml:ro
      - ./traefik/certs:/etc/traefik/certs:ro
    networks:
      - web

  rabbitmq:
    image: rabbitmq:4.2.3-management
    container_name: rabbitmq
    hostname: rabbit-node
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=password
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - web

networks:
  web:
    external: false

volumes:
  rabbitmq_data:

```

---

## 2. Traefik Configuration

The static config tells Traefik *where* to look, and the dynamic config tells it *what* to do.

### Static Configuration (`./traefik/traefik.yml`)

```yaml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  file:
    filename: /etc/traefik/dynamic_conf.yaml
    watch: true # Reloads config automatically when file changes

```

### Dynamic Configuration (`./traefik/dynamic_conf.yml`)

This file now contains the routing logic and the TLS certificate references.

```yaml
http:
  routers:
    rabbit-mgmt:
      rule: "Host(`rabbitmq.local`)"
      service: rabbit-service
      entryPoints:
        - websecure
      tls: {}

  services:
    rabbit-service:
      loadBalancer:
        servers:
          # Use the container name 'rabbitmq' and the management port
          - url: "http://rabbitmq:15672"

tls:
  certificates:
    - certFile: /etc/traefik/certs/local-cert.crt
      keyFile: /etc/traefik/certs/local-key.key

```

---

## 3. RabbitMQ Setup (REST API)

Run these commands once the containers are up (`docker compose up -d`).

### Create Virtual Host & User

```bash
# Create vhost
curl -i -u admin:password -X PUT http://localhost:15672/api/vhosts/my_vhost

# Create User
curl -i -u admin:password -X PUT http://localhost:15672/api/users/app_user \
  -d '{"password":"app_password","tags":"management"}'

# Set Permissions
curl -i -u admin:password -X PUT http://localhost:15672/api/permissions/my_vhost/app_user \
  -d '{"configure":".*","write":".*","read":".*"}'

```

### Create Messaging Structure

```bash
# Create Direct Exchange
curl -i -u admin:password -X PUT http://localhost:15672/api/exchanges/my_vhost/my_exchange \
  -d '{"type":"direct","durable":true}'

# Create Durable Queue
curl -i -u admin:password -X PUT http://localhost:15672/api/queues/my_vhost/my_queue \
  -d '{"durable":true}'

# Bind Queue to Exchange with Routing Key
curl -i -u admin:password -X POST http://localhost:15672/api/bindings/my_vhost/e/my_exchange/q/my_queue \
  -d '{"routing_key":"my_key"}'

```

---

## 4. Python Integration Scripts

Make sure you have `pika` installed: `pip install pika`.

### A. The Producer (Enqueue)

```python
import pika

def send_message():
    creds = pika.PlainCredentials('app_user', 'app_password')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost', virtual_host='my_vhost', credentials=creds))
    channel = connection.channel()

    message = "Task data payload"
    channel.basic_publish(
        exchange='my_exchange',
        routing_key='my_key',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2) # Persistent on disk
    )
    print(f" [x] Sent: {message}")
    connection.close()

if __name__ == "__main__":
    send_message()

```

### B. The Subscriber (Real-time Consumer)

```python
import pika

def process_msg(ch, method, properties, body):
    print(f" [x] Processing: {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

creds = pika.PlainCredentials('app_user', 'app_password')
conn = pika.BlockingConnection(pika.ConnectionParameters(
    host='localhost', virtual_host='my_vhost', credentials=creds))
channel = conn.channel()

channel.basic_qos(prefetch_count=1) # Don't give more than 1 msg to a worker at a time
channel.basic_consume(queue='my_queue', on_message_callback=process_msg)

print(' [*] Waiting for real-time messages. CTRL+C to exit.')
channel.start_consuming()

```

### C. The Periodic Poller (Dequeue on demand)

```python
import pika
import time

def poll_queue():
    creds = pika.PlainCredentials('app_user', 'app_password')
    params = pika.ConnectionParameters(host='localhost', virtual_host='my_vhost', credentials=creds)
    
    while True:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Pull a single message
        method_frame, header_frame, body = channel.basic_get(queue='my_queue', auto_ack=True)
        
        if method_frame:
            print(f" [x] Polled and dequeued: {body.decode()}")
        else:
            print(" [.] Queue empty. Sleeping 10s...")
        
        connection.close()
        time.sleep(10)

if __name__ == "__main__":
    poll_queue()

```

