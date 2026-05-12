# Use the official AWS CLI image as the base
FROM amazon/aws-cli:latest

# 1. Install system prerequisites
# dnf-plugins-core provides 'dnf config-manager'
RUN dnf update -y && dnf install -y \
    dnf-plugins-core \
    shadow-utils \
    tar \
    gzip \
    unzip \
    openssl \
    && dnf clean all

# 2. Install Terraform using HashiCorp's Amazon Linux repository
RUN dnf config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo && \
    dnf install -y terraform && \
    dnf clean all

# 3. Install kubectl
RUN cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.36/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.36/rpm/repodata/repomd.xml.key
EOF
RUN dnf install -y kubectl && dnf clean all

# 4. Install Helm
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
    chmod 700 get_helm.sh && \
    ./get_helm.sh && \
    rm get_helm.sh

# IMPORTANT: Reset ENTRYPOINT to allow shell access.
# The base image defaults to ["aws"], which would block other commands.
ENTRYPOINT ["/bin/bash"]
