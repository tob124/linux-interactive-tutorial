#!/usr/bin/env bash
# Optional host prerequisite. Inspect before running. Never called by the web API.
set -euo pipefail
if command -v docker >/dev/null; then
  echo 'Docker already exists. Preserve it and follow the official rootless setup instructions.'
  exit 1
fi
. /etc/os-release
if [ "$ID" != ubuntu ] || [ "$VERSION_ID" != 24.04 ]; then
  echo 'This setup targets Ubuntu 24.04 only.'; exit 1
fi
sudo apt-get update
sudo apt-get install -y ca-certificates curl uidmap dbus-user-session
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
course_arch=$(dpkg --print-architecture)
printf 'Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: noble\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' "$course_arch" | sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-ce-rootless-extras
# This fresh install is exclusively for the user's rootless course runtime.
sudo systemctl disable --now docker.service docker.socket
dockerd-rootless-setuptool.sh install
systemctl --user start docker
docker --context rootless info
