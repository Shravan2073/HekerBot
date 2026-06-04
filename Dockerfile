FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install common tools and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    nmap \
    sqlmap \
    nikto \
    dnsutils \
    netcat \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install ffuf
RUN wget https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz \
    && tar -xvf ffuf_2.1.0_linux_amd64.tar.gz \
    && mv ffuf /usr/local/bin/ \
    && rm ffuf_2.1.0_linux_amd64.tar.gz

# Create a non-privileged user for the agent to run as
RUN useradd -m heker
USER heker
WORKDIR /home/heker

CMD ["/bin/bash"]
