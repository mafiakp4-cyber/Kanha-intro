import os
import threading
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask

# 🔑 Config
API_ID = int(os.environ.get("API_ID", 21302239))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8040887080:AAGrOVmImlAQDJi9VhuL0o_yvaKUTdo2hnU")

# Pyrogram Client
app = Client(
    "IntroAdderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Dummy Flask app (for Render)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Intro Adder Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# 🌟 User intros dictionary
user_intros = {}

# 🎬 Start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply_text(
        "👋 Welcome to **2-sec Fast Intro Bot**!\n\n"
        "📽 Use `/setintro` with a video to save your intro.\n"
        "🎥 Then send me any video, I’ll add a 2-sec intro 🚀"
    )

# 📽 Set Intro Command
@app.on_message(filters.command("setintro") & filters.private)
async def set_intro(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply_text("❌ Reply to a video with `/setintro` to save it as intro.")
        return

    try:
        status = await message.reply_text("⬇️ Saving intro...")

        # Save intro as user-specific file
        intro_file_path = os.path.join(os.getcwd(), f"intro_{message.from_user.id}.mp4")
        downloaded_path = await client.download_media(message.reply_to_message.video.file_id, file_name=intro_file_path)

        # Trim intro to 2 sec using FFmpeg ultrafast
        trimmed_intro = os.path.join(os.getcwd(), f"intro_trim_{message.from_user.id}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", downloaded_path,
            "-t", "2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            trimmed_intro
        ], check=True)

        # Store trimmed intro path
        user_intros[message.from_user.id] = trimmed_intro

        # Safe edit_text to avoid MESSAGE_NOT_MODIFIED
        try:
            await status.edit_text("✅ Intro saved and trimmed to 2-sec! अब कोई भी video भेजो 🚀")
        except:
            await message.reply_text("✅ Intro saved and trimmed to 2-sec! अब कोई भी video भेजो 🚀")

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 📽 Handle Video
@app.on_message(filters.video & filters.private)
async def add_intro(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        if user_id not in user_intros or not os.path.exists(user_intros[user_id]):
            await message.reply_text("⚠️ Please set an intro first using `/setintro`.")
            return

        intro_path = user_intros[user_id]

        status = await message.reply_text("⚡ Adding 2-sec intro to your video...")

        # Download user video
        user_video = await client.download_media(message.video.file_id, file_name=os.path.join(os.getcwd(), "user_video.mp4"))

        # Merge file list
        file_list = "file_list.txt"
        with open(file_list, "w") as f:
            f.write(f"file '{os.path.abspath(intro_path)}'\n")
            f.write(f"file '{os.path.abspath(user_video)}'\n")

        # Output video
        output_video = "output.mp4"

        # FFmpeg concat fast
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", file_list, "-c", "copy", output_video],
            check=True
        )

        # Send new video
        await message.reply_video(output_video, caption="✅ 2-sec Intro added successfully!")

        # Cleanup
        os.remove(user_video)
        os.remove(output_video)
        os.remove(file_list)
        await status.delete()

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("🚀 2-sec Intro Adder Bot started...")
    app.run()
