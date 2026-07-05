FROM kalilinux/kali-rolling

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Update and install core tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    golang \
    netcat-traditional \
    telnet \
    rpcbind \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install Recon & Asset Discovery tools
RUN apt-get update && apt-get install -y \
    amass \
    subfinder \
    httpx-toolkit \
    dnsx \
    whois \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Install Port Scanning & Service Fingerprinting tools
RUN apt-get update && apt-get install -y \
    nmap \
    masscan \
    && rm -rf /var/lib/apt/lists/*

# Install RustScan via .deb
RUN wget https://github.com/RustScan/RustScan/releases/download/2.3.0/rustscan_2.3.0_amd64.deb \
    && dpkg -i rustscan_2.3.0_amd64.deb \
    && rm rustscan_2.3.0_amd64.deb

# Install Web Application Enumeration tools
RUN apt-get update && apt-get install -y \
    ffuf \
    nuclei \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install Katana via Go
RUN go install github.com/projectdiscovery/katana/cmd/katana@latest && cp /root/go/bin/katana /usr/local/bin/

# Install Vulnerability Scanning tools
RUN apt-get update && apt-get install -y \
    wpscan \
    nikto \
    trivy \
    && rm -rf /var/lib/apt/lists/*

# Install Exploitation & Payload Management tools
RUN apt-get update && apt-get install -y \
    metasploit-framework \
    exploitdb \
    sqlmap \
    xsstrike \
    && rm -rf /var/lib/apt/lists/*

# Install jwt-tool via Git
RUN git clone https://github.com/ticarpi/jwt_tool /opt/jwt_tool \
    && pip3 install --break-system-packages -r /opt/jwt_tool/requirements.txt \
    && chmod +x /opt/jwt_tool/jwt_tool.py \
    && ln -s /opt/jwt_tool/jwt_tool.py /usr/local/bin/jwt-tool

# Install Credential & Auth Testing tools
RUN apt-get update && apt-get install -y \
    hydra \
    hashcat \
    john \
    && rm -rf /var/lib/apt/lists/*

# Install Kerbrute via Go (usually faster/easier than searching for specific deb)
RUN go install github.com/ropnop/kerbrute@latest && cp /root/go/bin/kerbrute /usr/local/bin/

# Install Post-Exploitation & Lateral Movement tools
RUN apt-get update && apt-get install -y \
    netexec \
    python3-impacket \
    bloodhound.py \
    evil-winrm \
    && rm -rf /var/lib/apt/lists/*

# Install Evasion & C2 tools
RUN apt-get update && apt-get install -y \
    chisel \
    && rm -rf /var/lib/apt/lists/*

# Create a non-privileged user for the agent to run as
RUN useradd -m heker
USER heker
WORKDIR /home/heker

CMD ["/bin/bash"]
