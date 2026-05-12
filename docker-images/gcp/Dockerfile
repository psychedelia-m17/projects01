# Use the official Google Cloud SDK image as the base
FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:stable

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive


# 1. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    software-properties-common \
    lsb-release \
    apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# 2. Install kubectl (Official Kubernetes Repository)
# We add the keyring and the repository specifically for kubectl
RUN curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
    chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | tee -a /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update && \
    apt-get install -y kubectl && \
    rm -rf /var/lib/apt/lists/*

# 2a. gke-gcloud-auth-plugin plugin is now required for kubectl to authenticate with Google Kubernetes Engine (GKE) clusters.
RUN curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
     chmod 644 /usr/share/keyrings/cloud.google.gpg && \ 
     echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
     apt-get update && \
     apt-get install -y google-cloud-cli-gke-gcloud-auth-plugin && \
     rm -rf /var/lib/apt/lists/*

# 3. Install Terraform (HashiCorp official repo)
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && \
    apt-get install -y terraform && \
    rm -rf /var/lib/apt/lists/*

# 4. Install Helm (Official installation script)
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Final verification
RUN gcloud --version && \
    kubectl version --client && \
    terraform --version && \
    helm version

CMD ["/bin/bash"]

