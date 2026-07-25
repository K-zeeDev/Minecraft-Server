#!/usr/bin/env python3
"""
🎮 Minecraft Server Telegram Bot - All-in-One
"""

import os
import sys
import subprocess
import re
import time
import asyncio
import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8824199783:AAFxvFuoQwc1X44H6Wy_9zhYEQAQawoYqOU")
CHAT_ID = os.getenv("CHAT_ID", "5414763698")
SERVER_DIR = os.getenv("SERVER_DIR", "/home/minecraft/server")
RAM_SIZE = os.getenv("RAM_SIZE", "4G")
SERVER_PORT = int(os.getenv("SERVER_PORT", "25565"))
# ============================

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin IDs
ADMIN_IDS = [5414763698]

def is_server_running():
    """Check if Minecraft server is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "server.jar"],
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except:
        return False

def get_server_uptime():
    """Get server uptime"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "server.jar"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pid = result.stdout.strip()
            uptime = subprocess.run(
                ["ps", "-p", pid, "-o", "etime="],
                capture_output=True,
                text=True
            )
            return uptime.stdout.strip() or "Unknown"
        return "Not running"
    except:
        return "Unknown"

def get_online_players():
    """Get list of online players"""
    try:
        log_file = f"{SERVER_DIR}/logs/latest.log"
        if not os.path.exists(log_file):
            return []
        
        with open(log_file, "r") as f:
            lines = f.readlines()[-100:]
        
        players = []
        for line in lines:
            # Look for player join messages
            match = re.search(r"(\w{3,16}) joined the game", line)
            if match:
                name = match.group(1)
                if name not in players:
                    players.append(name)
            
            # Look for player leave messages
            match = re.search(r"(\w{3,16}) left the game", line)
            if match:
                name = match.group(1)
                if name in players:
                    players.remove(name)
        
        return players
    except:
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with keyboard"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "⛔ *Access Denied*\n\nYou are not authorized.",
            parse_mode="Markdown"
        )
        return
    
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
        ],
        [
            InlineKeyboardButton("💾 Backup", callback_data="backup"),
            InlineKeyboardButton("📁 Files", callback_data="files"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_emoji = "🟢" if is_server_running() else "🔴"
    status_text = "Running" if is_server_running() else "Stopped"
    
    await update.message.reply_text(
        f"🎮 *Minecraft Server Control*\n\n"
        f"📊 Status: `{status_emoji} {status_text}`\n"
        f"📁 Server: `{SERVER_DIR}`\n"
        f"💾 RAM: `{RAM_SIZE}`\n"
        f"🔌 Port: `{SERVER_PORT}`\n"
        f"⏱️ Uptime: `{get_server_uptime()}`\n\n"
        f"Use buttons below to control your server.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text(
            "⛔ *Access Denied*\n\nYou are not authorized.",
            parse_mode="Markdown"
        )
        return
    
    command = query.data
    
    if command == "status":
        await check_status(query)
    elif command == "start_server":
        await start_server_cmd(query)
    elif command == "stop_server":
        await stop_server_cmd(query)
    elif command == "players":
        await list_players(query)
    elif command == "logs":
        await show_logs(query)
    elif command == "restart_server":
        await restart_server_cmd(query)
    elif command == "backup":
        await backup_server(query)
    elif command == "files":
        await list_files(query)

async def check_status(query):
    """Check server status"""
    running = is_server_running()
    status_emoji = "🟢" if running else "🔴"
    status_text = "Running" if running else "Stopped"
    uptime = get_server_uptime() if running else "N/A"
    players = get_online_players()
    
    message = (
        f"📊 *Server Status*\n\n"
        f"Status: `{status_emoji} {status_text}`\n"
        f"Uptime: `{uptime}`\n"
        f"Players: `{len(players)} online`\n"
    )
    
    if players:
        message += f"👥 `{', '.join(players)}`\n"
    
    await query.edit_message_text(message, parse_mode="Markdown")

async def start_server_cmd(query):
    """Start Minecraft server"""
    if is_server_running():
        await query.edit_message_text("⚠️ *Server is already running*", parse_mode="Markdown")
        return
    
    await query.edit_message_text("⏳ *Starting server...*", parse_mode="Markdown")
    
    try:
        os.chdir(SERVER_DIR)
        subprocess.Popen([
            "java", 
            f"-Xmx{RAM_SIZE}", 
            f"-Xms{RAM_SIZE}",
            "-jar", 
            "server.jar", 
            "nogui"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        await asyncio.sleep(10)
        
        if is_server_running():
            await query.edit_message_text(
                "✅ *Server started successfully!*\n\n"
                f"⏱️ Uptime: `{get_server_uptime()}`",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ *Server failed to start*\n\n"
                "Check logs for details.",
                parse_mode="Markdown"
            )
    except Exception as e:
        await query.edit_message_text(f"❌ *Error:* `{e}`", parse_mode="Markdown")

async def stop_server_cmd(query):
    """Stop Minecraft server"""
    if not is_server_running():
        await query.edit_message_text("⚠️ *Server is already stopped*", parse_mode="Markdown")
        return
    
    await query.edit_message_text("⏳ *Stopping server...*", parse_mode="Markdown")
    
    try:
        subprocess.run(["pkill", "-f", "server.jar"], capture_output=True)
        await asyncio.sleep(3)
        
        if not is_server_running():
            await query.edit_message_text("✅ *Server stopped successfully*", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ *Failed to stop server*", parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"❌ *Error:* `{e}`", parse_mode="Markdown")

async def restart_server_cmd(query):
    """Restart Minecraft server"""
    await query.edit_message_text("⏳ *Restarting server...*", parse_mode="Markdown")
    
    # Stop
    if is_server_running():
        subprocess.run(["pkill", "-f", "server.jar"], capture_output=True)
        await asyncio.sleep(5)
    
    # Start
    try:
        os.chdir(SERVER_DIR)
        subprocess.Popen([
            "java", 
            f"-Xmx{RAM_SIZE}", 
            f"-Xms{RAM_SIZE}",
            "-jar", 
            "server.jar", 
            "nogui"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        await asyncio.sleep(10)
        
        if is_server_running():
            await query.edit_message_text(
                "✅ *Server restarted successfully*",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ *Server failed to restart*\n\n"
                "Check logs for details.",
                parse_mode="Markdown"
            )
    except Exception as e:
        await query.edit_message_text(f"❌ *Error:* `{e}`", parse_mode="Markdown")

async def list_players(query):
    """List online players"""
    players = get_online_players()
    
    if players:
        await query.edit_message_text(
            f"👥 *Online Players*\n\n"
            f"Total: `{len(players)}`\n\n"
            f"📝 `{', '.join(players)}`",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("👤 *No players online*", parse_mode="Markdown")

async def show_logs(query):
    """Show recent logs"""
    log_file = f"{SERVER_DIR}/logs/latest.log"
    
    if not os.path.exists(log_file):
        await query.edit_message_text("⚠️ *Log file not found*", parse_mode="Markdown")
        return
    
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()[-20:]
        
        log_text = "".join(lines[-20:])
        if len(log_text) > 4000:
            log_text = log_text[-4000:]
        
        await query.edit_message_text(
            f"📜 *Recent Logs*\n\n"
            f"```\n{log_text}\n```",
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.edit_message_text(f"❌ *Error:* `{e}`", parse_mode="Markdown")

async def backup_server(query):
    """Create backup"""
    await query.edit_message_text("⏳ *Creating backup...*", parse_mode="Markdown")
    
    try:
        backup_dir = f"{SERVER_DIR}/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/backup_{timestamp}.tar.gz"
        
        # Backup world and config
        subprocess.run([
            "tar", "-czf", backup_file,
            "-C", SERVER_DIR,
            "world", "server.properties", "eula.txt"
        ], capture_output=True)
        
        if os.path.exists(backup_file):
            size = os.path.getsize(backup_file) / (1024 * 1024)
            await query.edit_message_text(
                f"✅ *Backup created successfully*\n\n"
                f"📁 `{backup_file}`\n"
                f"📦 Size: `{size:.2f} MB`",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ *Backup failed*", parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"❌ *Error:* `{e}`", parse_mode="Markdown")

async def list_files(query):
    """List server files"""
    try:
        files = os.listdir(SERVER_DIR)
        file_list = []
        
        for f in files[:20]:
            path = f"{SERVER_DIR}/{f}"
            if os.path.isdir(path):
                file_list.append(f"📁 `{f}/`")
            else:
                size = os.path.getsize(path) / 1024
                if size < 1024:
                    file_list.append(f"📄 `{f}` ({size:.1f} KB)")
                else:
                    file_list.append(f"📄 `{f}` ({size/1024:.1f} MB)")
        
        message = f"📁 *Server Files*\n\n" + "\n".join(file_list)
        if len(files) > 20:
            message += f"\n\n... and {len(files) - 20} more"
        
        await query.edit_message_text(message, parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"❌ *Error:* `{e}`", parse_mode="Markdown")

def main():
    """Main function"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("🤖 Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
