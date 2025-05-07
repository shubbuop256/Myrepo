import os
import requests
import time
import sys
import paramiko

TOKEN_FILE = 'token.txt'
DB_FILE = 'db.txt'

def get_github_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as file:
            return [line.strip() for line in file if line.strip().startswith("ghp_")]
    return []

def get_last_command():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as file:
            data = file.readlines()
            if data:
                return data[0].strip()
    return None

def store_last_command(command):
    with open(DB_FILE, 'w') as file:
        file.write(command + '\n')

def get_used_options():
    used_options = set()
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as file:
            data = file.readlines()
            if len(data) > 1:
                used_options = set(data[1].strip().split(','))
    return used_options

def store_used_option(option):
    used_options = get_used_options()
    used_options.add(option)
    last_command = get_last_command()
    with open(DB_FILE, 'w') as file:
        if last_command:
            file.write(f"{last_command}\n")
        else:
            file.write("\n")
        file.write(",".join(used_options))

def authenticate_github(token):
    session = requests.Session()
    session.headers.update({'Authorization': f'token {token}'})
    response = session.get('https://api.github.com/user')
    if response.status_code == 200:
        print(f"[✔] Authenticated: {response.json().get('login')} ({token[:10]}...)")
        return session
    elif response.status_code in [402, 403]:
        print(f"[✘] Token blocked or forbidden: {token[:10]}... ({response.status_code}) - Removing token")
        remove_token(token)
    else:
        print(f"[✘] Authentication failed: {token[:10]}... ({response.status_code})")
    return None

def remove_token(token):
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as file:
            tokens = file.readlines()
        tokens = [line for line in tokens if line.strip() != token]
        with open(TOKEN_FILE, 'w') as file:
            file.writelines(tokens)

def wait_for_terminal(session, codespace_name, command):
    print(f"⏳ Waiting for Codespace {codespace_name} to become available...")
    while True:
        codespace_url = f"https://api.github.com/user/codespaces/{codespace_name}"
        response = session.get(codespace_url)
        if response.status_code == 200:
            codespace = response.json()
            if codespace['state'] == 'Available':
                print(f"✅ Codespace {codespace_name} is now available. Executing command...")
                execute_command(session, codespace_name, command)
                break
        else:
            print(f"❌ Failed to get Codespace status: {response.status_code}")
        time.sleep(5)

def execute_command(session, codespace_name, command):
    print(f"⚙️ Simulating command execution: '{command}' on {codespace_name}")

def keep_codespaces_alive(session, command):
    codespaces_url = "https://api.github.com/user/codespaces"
    codespaces_response = session.get(codespaces_url)
    if codespaces_response.status_code == 200:
        codespaces = codespaces_response.json()
        all_running = True
        for codespace in codespaces['codespaces']:
            if codespace['state'] == 'Shutdown':
                all_running = False
                start_url = f"https://api.github.com/user/codespaces/{codespace['name']}/start"
                start_response = session.post(start_url)
                if start_response.status_code in [200, 202]:
                    print(f"🟢 Starting Codespace: {codespace['name']}")
                    wait_for_terminal(session, codespace['name'], command)
                else:
                    print(f"❌ Failed to start Codespace: {codespace['name']} - {start_response.status_code}")
            else:
                print(f"✅ Codespace {codespace['name']} is already running.")
        return not all_running
    else:
        print(f"⚠️ Failed to fetch Codespaces: {codespaces_response.status_code} - {codespaces_response.text}")
        return False

def run_command_on_vps(command):
    ssh_host = '157.173.210.253'
    ssh_user = 'root'
    ssh_password = 'Mama@52662@7262'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=ssh_user, password=ssh_password)

    print(f"🔁 Running on VPS: {command}")
    stdin, stdout, stderr = ssh.exec_command(f'{command} > /dev/null 2>&1 &')
    print(stdout.read().decode(), stderr.read().decode())
    ssh.close()

def main():
    command = get_last_command()
    if not command:
        command = input("🔧 Enter the command to run on Codespaces: ")
        store_last_command(command)

    print(f"🔁 Starting keep-alive loop...\n")

    while True:
        tokens = get_github_tokens()
        if not tokens:
            print("⚠️ No tokens found. Waiting for tokens to be added...")
            time.sleep(10)
            continue

        for index, token in enumerate(tokens):
            print(f"\n➡️ Checking token {index + 1}/{len(tokens)}...")
            session = authenticate_github(token)
            if session:
                started_any = keep_codespaces_alive(session, command)
                if not started_any:
                    print(f"⏭️ All Codespaces already running for token {index + 1}.")
            time.sleep(3)
        print("\n🔄 Completed one full cycle. Restarting from top...\n")
        time.sleep(10)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        main()
    else:
        print("Usage: python3 soul.py run")

