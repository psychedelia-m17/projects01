# Read Me - app_docker_hub

# hub_manager

This app requires the Docker Hub's Personal Access Token to be defined in the environment variable `DH_PAT`. The `DH_PAT` environment variable could be defined either in the `.env` file or in the shell.

# Using curl
> Note: Change the Docker Hub Pat and the Docker Hub account name, tag
```bash
export DH_PAT="<Docker Hub Personal Access Token>";

TOKEN=$(curl -sk -H "Content-Type: application/json" -X POST -d "{\"username\": \"theco*\", \"password\": \"${DH_PAT}\"}" https://hub.docker.com/v2/users/login/ | jq -r .token)

curl -s -H "Authorization: Bearer ${TOKEN}" \
"https://hub.docker.com/v2/repositories/theco*/cumulator-biz/tags/v4.4-oo*-oo*-0323-0244/" | jq .
```
