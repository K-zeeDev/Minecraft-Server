import asyncio
import subprocess
import re
from telegram import Bot
from telegram.ext import Application, CommandHandler

# ---------- CONFIG ----------
BOT_TOKEN = "8771965327:AAH-ruWkMTiC4Kp7tQnw945QWbaXvzxdAxQ"
CHAT_ID = "5414763698"
MINECRAFT_SERVER_PATH = "/path/to/your/minecraft/server"  # ခင်ဗျားရဲ့ server folder
# ----------------------------

bot = Bot(token=BOT_TOKEN)

async def start(update, context):
    await update.message.reply_text("🎮 Minecraft Server Bot is running!\n"
                                    "Commands:\n"
                                    "/status - Check server status\n"
                                    "/start_server - Start server\n"
                                    "/stop_server - Stop server\n"
                                    "/players - List online players")

async def status(update, context):
    try:
        # Check if server is running
        result = subprocess.run(["pgrep", "-f", "server.jar"], capture_output=True)
        if result.stdout:
            await update.message.reply_text("✅ Server is **running**", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Server is **offline**", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def start_server(update, context):
    await update.message.reply_text("⏳ Starting server...")
    try:
        # Start server in background using screen
        subprocess.Popen(["screen", "-dmS", "minecraft", "java", "-Xmx4G", "-jar", 
                         f"{MINECRAFT_SERVER_PATH}/server.jar", "nogui"])
        await update.message.reply_text("✅ Server starting! Wait 30-60 seconds.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def stop_server(update, context):
    await update.message.reply_text("⏳ Stopping server...")
    try:
        # Send stop command to server console
        subprocess.run(["screen", "-S", "minecraft", "-X", "stuff", "stop\\n"])
        await update.message.reply_text("✅ Server stopped!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def players(update, context):
    try:
        # Read from server log
        with open(f"{MINECRAFT_SERVER_PATH}/logs/latest.log", "r") as f:
            lines = f.readlines()
        # Find online players (customize regex based on your server)
        online = []
        for line in lines[-100:]:  # Check last 100 lines
            if "joined the game" in line:
                name = re.search(r"([a-zA-Z0-9_]{3,16}) joined", line)
                if name and name.group(1) not in online:
                    online.append(name.group(1))
            if "left the game" in line:
                name = re.search(r"([a-zA-Z0-9_]{3,16}) left", line)
                if name and name.group(1) in online:
                    online.remove(name.group(1))
        if online:
            await update.message.reply_text(f"👥 Online players: {', '.join(online)}")
        else:
            await update.message.reply_text("👤 No players online")
    except Exception as e:
        await update.message.reply_text(f"Error reading log: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("start_server", start_server))
    app.add_handler(CommandHandler("stop_server", stop_server))
    app.add_handler(CommandHandler("players", players))
    
    print("🤖 Bot started! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()