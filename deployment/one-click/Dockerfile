FROM python:3.13-slim-trixie

RUN apt-get update
RUN apt-get install --no-install-recommends -y vim less curl jq unzip zip binutils git-all apt-transport-https ca-certificates gnupg


# Terraform
RUN curl -s -qL -o terraform_install.zip https://releases.hashicorp.com/terraform/$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version' | tr -d "v")/terraform_$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version' | tr -d "v")_linux_amd64.zip && \
    unzip terraform_install.zip -d /usr/bin/ && \
    chmod +x /usr/bin/terraform

RUN curl -sSLo ./terraform-docs.tar.gz https://terraform-docs.io/dl/v0.20.0/terraform-docs-v0.20.0-$(uname)-amd64.tar.gz && \
    tar -xzf terraform-docs.tar.gz && \
    chmod +x terraform-docs && \
    mv terraform-docs /usr/bin/terraform-docs

# AWS-CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && ./aws/install

# Node.js (for building React UI)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install --no-install-recommends -y nodejs

RUN pip install -U pyinstaller

WORKDIR /app

COPY ./one-click.py ./one-click.py
COPY ./terraform ./terraform
COPY ./ui ./ui

RUN pyinstaller one-click.py --onefile -n one-click
RUN mv ./dist/one-click /usr/bin/ && chmod +x /usr/bin/one-click

RUN rm -rf ./build ./dist ./one-click.spec
