#!/bin/bash
# Run this ONCE on a fresh machine to set up the full dev environment.
# Usage: bash scripts/setup-dev.sh
set -e

echo "=== EventPulse Dev Setup ==="

# Add current user to docker group (avoids needing sudo for docker commands)
if ! groups | grep -q docker; then
  echo "Adding $USER to docker group..."
  sudo usermod -aG docker "$USER"
  echo "✓ Added to docker group — IMPORTANT: run 'newgrp docker' or log out/in before continuing"
fi

# Install tools if missing
BIN="$HOME/.local/bin"
mkdir -p "$BIN"

if ! command -v poetry &>/dev/null; then
  echo "Installing Poetry..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v kubectl &>/dev/null; then
  echo "Installing kubectl..."
  curl -sL "https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl" -o "$BIN/kubectl"
  chmod +x "$BIN/kubectl"
fi

if ! command -v minikube &>/dev/null; then
  echo "Installing Minikube..."
  curl -sL https://storage.googleapis.com/minikube/releases/v1.32.0/minikube-linux-amd64 -o "$BIN/minikube"
  chmod +x "$BIN/minikube"
fi

if ! command -v terraform &>/dev/null; then
  echo "Installing Terraform..."
  curl -sL https://releases.hashicorp.com/terraform/1.7.4/terraform_1.7.4_linux_amd64.zip -o /tmp/tf.zip
  unzip -q /tmp/tf.zip -d "$BIN/"
fi

if ! command -v k6 &>/dev/null; then
  echo "Installing k6..."
  curl -sL https://github.com/grafana/k6/releases/download/v0.50.0/k6-v0.50.0-linux-amd64.tar.gz | tar -xz -C /tmp/
  cp /tmp/k6-v0.50.0-linux-amd64/k6 "$BIN/k6"
  chmod +x "$BIN/k6"
fi

# Add ~/.local/bin to PATH permanently
if ! grep -q '.local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$HOME/.local/share/pypoetry/venv/bin:$PATH"' >> ~/.bashrc
fi

# Install Python dependencies
echo "Installing Python dependencies..."
poetry install

# Copy .env if missing
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ Created .env from .env.example"
fi

echo ""
echo "=== Setup Complete ==="
echo "Tools installed: poetry, kubectl, minikube, terraform, k6"
echo ""
echo "NEXT STEPS:"
echo "  1. Run: newgrp docker   (or log out and back in)"
echo "  2. Run: make up         (start the stack)"
echo "  3. Run: make logs       (watch startup)"
