#!/bin/sh
sudo yum install -y amazon-linux-extras git
sudo amazon-linux-extras enable php7.4
sudo yum install php-cli
git clone https://github.com/geteduroam/cattenbak.git
cd cattenbak
systemctl link $(pwd)/contrib/systemd/cattenbak.service
systemctl enable --now $(pwd)/contrib/systemd/cattenbak.timer
