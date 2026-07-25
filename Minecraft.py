#!/usr/bin/env python3
"""
🎮 Minecraft Server + Telegram Bot All-in-One Auto Installer
Run: sudo python3 install_all.py
"""

import os
import sys
import subprocess
import shutil
import time
import requests
import json
from pathlib import Path

# ============================================
# CONFIGURATION
# ============================================
BOT_TOKEN = "8824199783:AAFxvFuoQwc1X44H6Wy_9zhYEQAQawoYqOU"
CHAT_ID = "5414763698"
SERVER_DIR = "/home/minecraft/server"
BOT_DIR = "/home/minecraft/bot"
MINECRAFT_VERSION = "1.20.4"
RAM_SIZE = "4G"
SERVER_PORT = 25565
# ============================================

# Colors for terminal
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_header():
    """Print fancy header"""
    print(f"{Colors.BLUE}========================================{Colors.NC}")
    print(f"{Colors.GREEN}  🎮 Minecraft Server + Bot Installer  {Colors.NC}")
    print(f"{Colors.BLUE}========================================{Colors.NC}")
    print(f"{Colors.CYAN}  Token: {BOT_TOKEN[:20]}...{Colors.NC}")
    print(f"{Colors.CYAN}  Chat ID: {CHAT_ID}{Colors.NC}")
    print(f"{Colors.BLUE}========================================{Colors.NC}\n")

def run_command(cmd, error_msg=None, check=True):
    """Run shell command and print output"""
    print(f"{Colors.YELLOW}▶ Running: {cmd}{Colors.NC}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(f"{Colors.GREEN}✓ {result.stdout.strip()}{Colors.NC}")
        return result
    except subprocess.CalledProcessError as e:
        if error_msg:
            print(f"{Colors.RED}❌ {error_msg}{Colors.NC}")
        print(f"{Colors.RED}❌ Error: {e.stderr}{Colors.NC}")
        if check:
            sys.exit(1)
        return None

def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        print(f"{Colors.RED}❌ Please run as root: sudo python3 install_all.py{Colors.NC}")
        sys.exit(1)

def install_dependencies():
    """Install system packages"""
    print(f"\n{Colors.GREEN}[1/7] Installing system dependencies...{Colors.NC}")
    
    # Update package list
    run_command("apt update -y", "Failed to update package list")
    
    # Install packages
    packages = [
        "openjdk-17-jre-headless",
        "openjdk-17-jdk",
        "python3",
        "python3-pip",
        "python3-venv",
        "screen",
        "curl",
        "wget",
        "git",
        "unzip",
        "net-tools",
        "ufw",
        "htop",
        "nano",
        "software-properties-common"
    ]
    
    for pkg in packages:
        run_command(f"apt install -y {pkg}", f"Failed to install {pkg}")
    
    print(f"{Colors.GREEN}✅ System dependencies installed!{Colors.NC}")

def install_python_packages():
    """Install Python packages"""
    print(f"\n{Colors.GREEN}[2/7] Installing Python packages...{Colors.NC}")
    
    python_packages = [
        "python-telegram-bot==20.7",
        "requests==2.31.0",
        "psutil==5.9.6"
    ]
    
    for pkg in python_packages:
        run_command(f"pip3 install {pkg}", f"Failed to install {pkg}")
    
    print(f"{Colors.GREEN}✅ Python packages installed!{Colors.NC}")

def create_directories():
    """Create necessary directories"""
    print(f"\n{Colors.GREEN}[3/7] Creating directories...{Colors.NC}")
    
    Path(SERVER_DIR).mkdir(parents=True, exist_ok=True)
    Path(BOT_DIR).mkdir(parents=True, exist_ok=True)
    Path(f"{SERVER_DIR}/logs").mkdir(exist_ok=True)
    Path(f"{SERVER_DIR}/world").mkdir(exist_ok=True)
    
    # Set permissions
    run_command(f"chmod -R 755 /home/minecraft")
    
    print(f"{Colors.GREEN}✅ Directories created!{Colors.NC}")

def download_minecraft_server():
    """Download Minecraft server.jar"""
    print(f"\n{Colors.GREEN}[4/7] Downloading Minecraft Server {MINECRAFT_VERSION}...{Colors.NC}")
    
    os.chdir(SERVER_DIR)
    
    # Try official Mojang download
    jar_urls = [
        f"https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar",
        f"https://launcher.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar",
        "https://meta.fabricmc.net/v2/versions/loader/1.20.4/0.15.11/1.0.0/server.jar"  # Fabric fallback
    ]
    
    downloaded = False
    for url in jar_urls:
        print(f"  Trying: {url}")
        result = run_command(f"wget -O server.jar {url}", check=False)
        if result and result.returncode == 0 and os.path.exists("server.jar"):
            downloaded = True
            break
    
    if not downloaded:
        print(f"{Colors.RED}❌ Failed to download server.jar{Colors.NC}")
        sys.exit(1)
    
    # Accept EULA
    with open("eula.txt", "w") as f:
        f.write("eula=true\n")
    
    print(f"{Colors.GREEN}✅ Minecraft server downloaded!{Colors.NC}")

def create_start_scripts():
    """Create start and bot scripts"""
    print(f"\n{Colors.GREEN}[5/7] Creating scripts...{Colors.NC}")
    
    # Start script for Minecraft server
    start_script = f"""#!/bin/bash
cd {SERVER_DIR}
screen -dmS minecraft java -Xmx{RAM_SIZE} -Xms{RAM_SIZE} -jar server.jar nogui
echo "Server started in screen session 'minecraft'"
echo "To attach: screen -r minecraft"
"""
    
    with open(f"{SERVER_DIR}/start.sh", "w") as f:
        f.write(start_script)
    os.chmod(f"{SERVER_DIR}/start.sh", 0o755)
    
    # Stop script
    stop_script = f"""#!/bin/bash
screen -S minecraft -X stuff "stop\\n"
echo "Server stopped"
"""
    
    with open(f"{SERVER_DIR}/stop.sh", "w") as f:
        f.write(stop_script)
    os.chmod(f"{SERVER_DIR}/stop.sh", 0o755)
    
    print(f"{Colors.GREEN}✅ Start scripts created!{Colors.NC}")

def create_bot_script():
    """Create Telegram bot script"""
    print(f"\n{Colors.GREEN}[6/7] Creating Telegram Bot...{Colors.NC}")
    
    bot_script = f'''#!/usr/bin/env python3
"""
🎮 Minecraft Server Telegram Bot
"""

import asyncio
import subprocess
import re
import os
import sys
import time
from pathlib import Path
from datetime import datetime

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== CONFIG ==========
BOT_TOKEN = "{BOT_TOKEN}"
CHAT_ID = "{CHAT_ID}"
SERVER_DIR = "{SERVER_DIR}"
LOG_FILE = f"{{SERVER_DIR}}/logs/latest.log"
# ============================

# Admin IDs (add your Telegram user IDs here)
ADMIN_IDS = [5414763698]  # Replace with actual numeric user IDs

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("▶️ Start", callback_data="start_server"),
        ],
        [
            InlineKeyboardButton("⏹️ Stop", callback_data="stop_server"),
            InlineKeyboardButton("👥 Players", callback_data="players"),
        ],
        [
            InlineKeyboardButton("📜 Logs", callback_data="logs"),
            InlineKeyboardButton("🔄 Restart", callback_data="restart_server"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎮 *Minecraft Server Control Bot*\n\n"
        "Use the buttons below to control your server.\n"
        f"📁 Server: `{SERVER_DIR}`\n"
        f"💾 RAM: {RAM_SIZE}\n"
        f"🔌 Port: {SERVER_PORT}",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    command = query.data
    
    if command == "status":
        await check_status(query.message)
    elif command == "start_server":
        await start_server_cmd(query.message)
    elif command == "stop_server":
        await stop_server_cmd(query.message)
    elif command == "players":
        await list_players(query.message)
    elif command == "logs":
        await show_logs(query.message)
    elif command == "restart_server":
        await restart_server_cmd(query.message)

async def check_status(message):
    """Check if server is running"""
    try:
        result = subprocess.run(["pgrep", "-f", "server.jar"], capture_output=True, text=True)
        if result.stdout.strip():
            # Get server uptime
            uptime_cmd = subprocess.run(["ps", "-p", result.stdout.strip(), "-o", "etime="], capture_output=True, text=True)
            uptime = uptime_cmd.stdout.strip() if uptime_cmd.stdout else "Unknown"
            await message.reply_text(f"✅ *Server is running*\\n⏱️ Uptime: `{uptime}`", parse_mode="Markdown")
        else:
            await message.reply_text("❌ *Server is offline*", parse_mode="Markdown")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

async def start_server_cmd(message):
    """Start Minecraft server"""
    await message.reply_text("⏳ *Starting server...*", parse_mode="Markdown")
    try:
        os.chdir(SERVER_DIR)
        subprocess.Popen(["screen", "-dmS", "minecraft", "java", f"-Xmx{RAM_SIZE}", "-jar", "server.jar", "nogui"])
        await asyncio.sleep(5)
        await message.reply_text("✅ *Server starting!*\\n⏳ Wait 30-60 seconds for full startup.", parse_mode="Markdown")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

async def stop_server_cmd(message):
    """Stop Minecraft server"""
    await message.reply_text("⏳ *Stopping server...*", parse_mode="Markdown")
    try:
        subprocess.run(["screen", "-S", "minecraft", "-X", "stuff", "stop\\\\n"])
        await asyncio.sleep(3)
        await message.reply_text("✅ *Server stopped!*", parse_mode="Markdown")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

async def restart_server_cmd(message):
    """Restart Minecraft server"""
    await stop_server_cmd(message)
    await asyncio.sleep(5)
    await start_server_cmd(message)

async def list_players(message):
    """List online players"""
    try:
        # Send command to server
        subprocess.run(["screen", "-S", "minecraft", "-X", "stuff", "list\\\\n"])
        await asyncio.sleep(2)
        
        # Read last few lines from log
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-50:]
            
            players_found = []
            for line in lines:
                match = re.search(r"There are (\\d+) of a max of", line)
                if match:
                    count = match.group(1)
                    # Try to get player names
                    player_match = re.search(r": (.*)", line)
                    if player_match:
                        names = player_match.group(1).strip()
                        await message.reply_text(f"👥 *Online Players:* {count}\\n📝 `{names}`", parse_mode="Markdown")
                        return
            
            await message.reply_text("👤 *No players online*", parse_mode="Markdown")
        else:
            await message.reply_text("⚠️ Log file not found", parse_mode="Markdown")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

async def show_logs(message):
    """Show recent logs"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-15:]
            log_text = "".join(lines[-15:])
            if len(log_text) > 4000:
                log_text = log_text[-4000:]
            await message.reply_text(f"📜 *Recent Logs:*\\n```\\n{log_text}\\n```", parse_mode="Markdown")
        else:
            await message.reply_text("⚠️ Log file not found", parse_mode="Markdown")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

def main():
    """Main function"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Bot started! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
'''
    
    with open(f"{BOT_DIR}/bot.py", "w") as f:
        f.write(bot_script)
    os.chmod(f"{BOT_DIR}/bot.py", 0o755)
    
    print(f"{Colors.GREEN}✅ Bot script created!{Colors.NC}")

def configure_firewall():
    """Configure firewall"""
    print(f"\n{Colors.GREEN}[7/7] Configuring firewall...{Colors.NC}")
    
    # Allow SSH, Minecraft port, and Telegram webhook
    ports = [22, SERVER_PORT, 443, 80]
    for port in ports:
        run_command(f"ufw allow {port}", f"Failed to allow port {port}", check=False)
    
    run_command("ufw --force enable", check=False)
    
    print(f"{Colors.GREEN}✅ Firewall configured!{Colors.NC}")

def create_service():
    """Create systemd service for auto-start"""
    print(f"\n{Colors.GREEN}Creating systemd service...{Colors.NC}")
    
    service_file = f"""[Unit]
Description=Minecraft Server
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory={SERVER_DIR}
ExecStart={SERVER_DIR}/start.sh
ExecStop={SERVER_DIR}/stop.sh
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
    
    with open("/etc/systemd/system/minecraft.service", "w") as f:
        f.write(service_file)
    
    bot_service = f"""[Unit]
Description=Telegram Bot
After=network.target minecraft.service

[Service]
Type=simple
User=root
WorkingDirectory={BOT_DIR}
ExecStart=/usr/bin/python3 {BOT_DIR}/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open("/etc/systemd/system/minecraft-bot.service", "w") as f:
        f.write(bot_service)
    
    run_command("systemctl daemon-reload")
    run_command("systemctl enable minecraft.service", check=False)
    run_command("systemctl enable minecraft-bot.service", check=False)
    
    print(f"{Colors.GREEN}✅ Services created!{Colors.NC}")

def display_summary():
    """Show installation summary"""
    print(f"\n{Colors.BLUE}========================================{Colors.NC}")
    print(f"{Colors.GREEN}✅ INSTALLATION COMPLETE!{Colors.NC}")
    print(f"{Colors.BLUE}========================================{Colors.NC}")
    print(f"""
{Colors.CYAN}📁 Minecraft Server:{Colors.NC} {SERVER_DIR}
{Colors.CYAN}🤖 Bot Directory:{Colors.NC} {BOT_DIR}
{Colors.CYAN}🔌 Server Port:{Colors.NC} {SERVER_PORT}
{Colors.CYAN}💾 RAM Allocated:{Colors.NC} {RAM_SIZE}

{Colors.YELLOW}📋 Commands:{Colors.NC}
  Start server:  {SERVER_DIR}/start.sh
  Stop server:   {SERVER_DIR}/stop.sh
  Start bot:     python3 {BOT_DIR}/bot.py
  
{Colors.YELLOW}🔧 Systemd Services:{Colors.NC}
  minecraft      - Auto-start server
  minecraft-bot  - Auto-start bot

{Colors.YELLOW}📱 Telegram Commands:{Colors.NC}
  /start         - Show control panel
  /status        - Check server status
  /start_server  - Start server
  /stop_server   - Stop server
  /players       - List online players
  /logs          - Show recent logs

{Colors.GREEN}🎮 Bot is ready! Send /start to your bot!{Colors.NC}
{Colors.BLUE}========================================{Colors.NC}
""")

def main():
    """Main installation function"""
    print_header()
    check_root()
    
    # Run installation steps
    install_dependencies()
    install_python_packages()
    create_directories()
    download_minecraft_server()
    create_start_scripts()
    create_bot_script()
    configure_firewall()
    create_service()
    
    # Start services
    print(f"\n{Colors.GREEN}Starting services...{Colors.NC}")
    run_command("systemctl start minecraft.service", check=False)
    run_command("systemctl start minecraft-bot.service", check=False)
    
    display_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Installation interrupted{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.NC}")
        sys.exit(1)
