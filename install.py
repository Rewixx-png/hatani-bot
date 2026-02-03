import os
import sys
import subprocess
import shutil
import socket

COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m"
}

def log(message, color="ENDC"):
    print(f"{COLORS.get(color, COLORS['ENDC'])}{message}{COLORS['ENDC']}")

def run_command(command, shell=False, check=True):
    try:
        if shell:
            subprocess.run(command, shell=True, check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(command.split(), check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def run_visible_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_input(prompt_text, default=None):
    prompt = f"{COLORS['BOLD']}{prompt_text}{COLORS['ENDC']}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    
    value = input(prompt).strip()
    return value if value else default

def find_free_port(start_port=6379):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                port += 1
    return start_port

def create_env_file():
    log("\n--- Configuration Setup ---", "HEADER")
    
    current_env = {}
    if os.path.exists(".env"):
        log("[!] Existing .env found. Loading values...", "WARNING")
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    current_env[key] = val

    bot_token = get_input("Enter Telegram BOT_TOKEN", current_env.get("BOT_TOKEN"))
    if not bot_token:
        log("Error: BOT_TOKEN is required.", "FAIL")
        sys.exit(1)

    mistral_key = get_input("Enter MISTRAL_API_KEY", current_env.get("MISTRAL_API_KEY"))
    if not mistral_key:
        log("Error: MISTRAL_API_KEY is required.", "FAIL")
        sys.exit(1)

    allowed_group = get_input("Enter ALLOWED_GROUP_ID", current_env.get("ALLOWED_GROUP_ID", "-1002033901364"))
    allowed_user = get_input("Enter ALLOWED_USER_ID", current_env.get("ALLOWED_USER_ID", "7485721661"))
    
    log("[*] Searching for free Redis port...", "BLUE")
    redis_port = find_free_port(6379)
    if redis_port != 6379:
        log(f"[!] Port 6379 is busy. Using port {redis_port} for Redis mapping.", "WARNING")
    else:
        log(f"[+] Port 6379 is available.", "GREEN")

    redis_url = current_env.get("REDIS_URL", "redis://redis:6379/0")

    with open(".env", "w") as f:
        f.write(f"BOT_TOKEN={bot_token}\n")
        f.write(f"MISTRAL_API_KEY={mistral_key}\n")
        f.write(f"ALLOWED_GROUP_ID={allowed_group}\n")
        f.write(f"ALLOWED_USER_ID={allowed_user}\n")
        f.write(f"REDIS_URL={redis_url}\n")
        f.write(f"REDIS_PORT={redis_port}\n")
    
    log("[+] .env file created successfully.", "GREEN")
    return redis_url

def check_dependency(name, cmd_check):
    log(f"[*] Checking {name}...", "BLUE")
    if run_command(cmd_check, shell=True, check=True):
        log(f"[+] {name} found.", "GREEN")
        return True
    else:
        log(f"[-] {name} NOT found.", "FAIL")
        return False

def install_docker():
    log("\n--- Docker Deployment ---", "HEADER")
    
    if not check_dependency("Docker", "docker --version"):
        log("Please install Docker first: https://docs.docker.com/get-docker/", "FAIL")
        sys.exit(1)
    
    compose_cmd = None
    
    if run_command("docker compose version", shell=True, check=False):
        log("[+] Docker Compose Plugin (V2) detected.", "GREEN")
        compose_cmd = "docker compose"
    elif shutil.which("docker-compose"):
        log("[+] Docker Compose Legacy (V1) detected.", "GREEN")
        compose_cmd = "docker-compose"
    else:
        log("Docker Compose not found. Please install it.", "FAIL")
        sys.exit(1)

    log(f"[*] Building and starting containers using '{compose_cmd}'...", "BLUE")
    success = run_visible_command(f"{compose_cmd} up -d --build")
    
    if success:
        log("\n[SUCCESS] Bot deployed via Docker!", "GREEN")
        log(f"Logs: {compose_cmd} logs -f", "BLUE")
    else:
        log("\n[FAIL] Docker deployment failed.", "FAIL")

def install_local(redis_url):
    log("\n--- Local System Deployment ---", "HEADER")
    
    if not check_dependency("Python 3", "python3 --version"):
        log("Python 3 is required.", "FAIL")
        sys.exit(1)
        
    log("[*] Installing Python dependencies...", "BLUE")
    run_visible_command("pip3 install -r requirements.txt")

    if "localhost" in redis_url or "127.0.0.1" in redis_url:
        log("[?] Local Redis URL detected.", "WARNING")
        if not check_dependency("Redis Server", "redis-server --version"):
            choice = get_input("Install Redis locally? (y/n)", "y")
            if choice.lower() == 'y':
                if sys.platform == "linux":
                    run_visible_command("sudo apt-get update && sudo apt-get install redis-server -y")
                    run_visible_command("sudo systemctl enable redis-server")
                    run_visible_command("sudo systemctl start redis-server")
                else:
                    log("Please install Redis manually for your OS.", "FAIL")

    log("[*] Starting Bot...", "BLUE")
    try:
        run_visible_command("python3 main.py")
    except KeyboardInterrupt:
        log("\nBot stopped.", "WARNING")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    log("==========================================", "HEADER")
    log("      HATANI BOT INTELLIGENT INSTALLER    ", "HEADER")
    log("==========================================", "HEADER")
    
    redis_url = create_env_file()
    
    log("\nSelect Deployment Method:", "BOLD")
    log("1) Docker Compose (Recommended - Isolated)", "BLUE")
    log("2) Local System (Python Direct)", "BLUE")
    
    choice = get_input("Enter choice", "1")
    
    if choice == "1":
        install_docker()
    elif choice == "2":
        install_local(redis_url)
    else:
        log("Invalid choice.", "FAIL")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n[!] Installation aborted by user.", "WARNING")
        sys.exit(0)
    except Exception as e:
        log(f"\n[!] Unexpected error: {e}", "FAIL")
        sys.exit(1)