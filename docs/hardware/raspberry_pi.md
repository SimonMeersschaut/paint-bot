# Raspberry Pi

We flashed the Raspberry Pi with `Raspberry Pi OS Lite (64-bit)` with hostname `paintbot`, so we can find it via the network. We used username `paintbot` and connected it to the local wifi network. This way we can connect to it via SSH.

The Pi has a camera module 3 wide attached to make a timelapse while painting.

The pi was also configured with the following commands:

```bash
sudo apt install -y git
git clone https://github.com/SimonMeersschaut/paint-bot.git
# sudo apt install -y python3-pip
# sudo apt install -y python3-setuptoold
# sudo apt install -y python3-tk #tkinter
# SSH
ssh-keygen -t ed25519 -C "simon.meersschaut@gmail.com"
git config --global user.name "Simon Meersschaut"
git config --global user.email "simon.meersschaut@gmail.com"
# open project
cd paint-bot
# python3 setup.py
code .
```