import os
import asyncio
import logging
import re
import base64
import requests
from dotenv import load_dotenv
# import uuid
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

load_dotenv()

# Configure logging to see events in 'docker logs'
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Fetch settings from environment variables (defined in docker-compose.yml or .env)
TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_ID = int(os.getenv("MY_USER_ID", "0"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
PIC_DIR = "pic"

# Agent Zero API Settings
AGENT_ZERO_URL = os.getenv("AGENT_ZERO_URL", "http://localhost:5000")
AGENT_ZERO_API_KEY = os.getenv("AGENT_ZERO_API_KEY")  # Find this in Agent Zero Settings > External Services

if os.name != "nt":
    # Linux/Mac
    logging.info("Running in Linux.")
    if "AGENT_ZERO_URL" not in os.environ:
        AGENT_ZERO_URL = "http://host.docker.internal:5000"

# Ensure the pictures directory exists
os.makedirs(PIC_DIR, exist_ok=True)
context_id = None


def reset_session():
    global context_id
    context_id = None
    logging.info("Session reset. Context ID cleared.")


async def run_agent_sync(
    prompt, is_scheduled=False, screenshot_path=None, attachments=None
):

    global context_id
    try:
        headers = {"Content-Type": "application/json", "X-API-KEY": AGENT_ZERO_API_KEY}
        payload = {"message": prompt, "lifetime_hours": 24}
        if attachments:
            payload["attachments"] = attachments
        if context_id and not is_scheduled:
            payload["context_id"] = context_id
            logging.info(f"Sending request with context_id: {context_id}")
        # Run the synchronous requests.post in a separate thread to avoid blocking the async event loop
        response = await asyncio.to_thread(
            requests.post,
            f"{AGENT_ZERO_URL}/api_message",
            json=payload,
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            # LOG THE FULL RESPONSE TO SEE WHAT AGENT ZERO IS ACTUALLY SENDING
            logging.info(f"RAW API RESPONSE: {data}")
            if not is_scheduled:
                # Try multiple possible keys that Agent Zero might be using for the ID
                new_context_id = (
                    data.get("context_id")
                    or data.get("id")
                    or data.get("session_id")
                    or data.get("chat_id")
                )
                if new_context_id:
                    context_id = new_context_id
                    logging.info(f"Updated context_id to: {context_id}")
                else:
                    logging.warning(
                        "WARNING: Could not find any ID in the Agent Zero response!"
                    )
            bot_response = data.get(
                "response",
                "I processed your message, but didn't generate a final text response.",
            )
            logging.info(f"🤖 BOT RESPONSE: {bot_response}")
            # Extract image paths from the response
            image_paths = re.findall(r"!\[.*?\]\((.*?)\)", bot_response)
            # Clean up paths (remove img:// prefix if present)
            cleaned_paths = [path.replace("img://", "") for path in image_paths]
            downloaded_images = []
            if cleaned_paths:
                logging.info(f"Found image paths in response: {cleaned_paths}")
                try:
                    files_response = await asyncio.to_thread(
                        requests.post,
                        f"{AGENT_ZERO_URL}/api_files_get",
                        json={"paths": cleaned_paths},
                        headers=headers,
                    )
                    if files_response.status_code == 200:
                        files_data = files_response.json()
                        for filename, base64_content in files_data.items():
                            try:
                                image_data = base64.b64decode(base64_content)
                                # Use the original filename from the path, not the key from the response
                                # because the key might just be the filename, but we want to save it locally
                                local_path = os.path.join(PIC_DIR, filename)
                                with open(local_path, "wb") as f:
                                    f.write(image_data)
                                downloaded_images.append(local_path)
                                logging.info(
                                    f"Successfully downloaded image to {local_path}"
                                )
                            except Exception as e:
                                logging.error(
                                    f"Error decoding/saving image {filename}: {e}"
                                )
                    else:
                        logging.error(
                            f"Failed to fetch images. Status code: {files_response.status_code}"
                        )
                except Exception as e:
                    logging.error(f"Error fetching images from Agent Zero: {e}")
            # Remove the markdown image links from the text response so they don't show up as broken links in Telegram
            clean_bot_response = re.sub(r"!\[.*?\]\(.*?\)", "", bot_response).strip()
            return clean_bot_response, downloaded_images
        else:
            error_msg = f"API Error {response.status_code}: {response.text}"
            logging.error(error_msg)
            return f"I'm having trouble connecting to Agent Zero API. {error_msg}", []

    except Exception as e:
        error_msg = f"Error during API execution: {e}"
        logging.error(error_msg)
        return (
            "I'm having trouble connecting to my internal tools. Try asking me a simple question without code!",
            [],
        )


async def process_agent_task(
    prompt: str,
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    is_scheduled: bool = False,
    attachments: list = None,
):
    prefix = "⏰ Scheduled Task" if is_scheduled else "🚀 Task"
    await context.bot.send_message(
        chat_id=chat_id, text=f"{prefix} starting: '{prompt}'..."
    )
    try:
        screenshot_path = f"action_{chat_id}.png"
        # FIX: Await the async function directly instead of using to_thread
        result, downloaded_images = await run_agent_sync(
            prompt, is_scheduled, screenshot_path, attachments
        )
        # Send the text response
        await context.bot.send_message(
            chat_id=chat_id, text=f"✅ {prefix} Completed!\n\nResponse:\n{result}"
        )
        # Send the downloaded images to the user
        for img_path in downloaded_images:
            if os.path.exists(img_path):
                try:
                    with open(img_path, "rb") as photo:
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=f"Here is the image: {os.path.basename(img_path)}",
                        )
                except Exception as e:
                    logging.error(f"Failed to send photo {img_path}: {e}")
                    # Fallback to sending as document if photo fails (e.g., due to dimensions)
                    try:
                        with open(img_path, "rb") as doc:
                            await context.bot.send_document(
                                chat_id=chat_id,
                                document=doc,
                                caption=f"Image sent as document due to size/dimension limits: {os.path.basename(img_path)}",
                            )
                    except Exception as doc_e:
                        logging.error(f"Failed to send document {img_path}: {doc_e}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"❌ Could not send the image '{os.path.basename(img_path)}'. It might be too large or have invalid dimensions.",
                        )
        # Send the screenshot to the user if it exists
        if os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption="Here is the visual result from the browser:",
                )
            os.remove(screenshot_path)  # Clean up the temporary file
    except Exception as e:
        logging.error(f"Error during OpenClaw execution: {e}")
        await context.bot.send_message(
            chat_id=chat_id, text=f"❌ Error executing task: {str(e)}"
        )


async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Security check: Only allow the authorized user
    if update.message.from_user.id != MY_ID:
        logging.warning(
            f"Unauthorized access attempt by ID: {update.message.from_user.id}"
        )
        return

    user_query = update.message.text
    chat_id = update.message.chat_id
    # Print what the user sent
    logging.info(
        f"💬 RECV [Text] from {update.message.from_user.first_name} ({update.message.from_user.id}): {user_query}"
    )
    # Check if the user is asking for a specific picture
    if user_query.lower().startswith("get pic "):
        pic_name = user_query[8:].strip()
        full_path = os.path.join(PIC_DIR, pic_name)
        if os.path.exists(full_path):
            with open(full_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id, photo=photo, caption=f"Here is {pic_name}"
                )
        else:
            await update.message.reply_text(
                f"❌ Could not find picture named '{pic_name}' in '{PIC_DIR}/'"
            )
        return
    # Process the task asynchronously
    asyncio.create_task(process_agent_task(user_query, chat_id, context))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming photos and saves them with their caption or a default name."""
    if update.message.from_user.id != MY_ID:
        return
    photo_file = await update.message.photo[-1].get_file()
    caption = update.message.caption if update.message.caption else "[No Caption]"
    logging.info(
        f"📸 RECV [Photo] from {update.message.from_user.first_name} ({update.message.from_user.id}) - Caption: {caption}"
    )
    # Use caption as filename if provided, otherwise use a default name
    if update.message.caption:
        # Sanitize the caption to be a valid filename
        # Replace invalid characters and newlines with underscores
        safe_caption = re.sub(r'[<>:"/\\|?*\n\r]', "_", update.message.caption)
        # Limit length to avoid too long filenames
        filename = safe_caption[:50].strip()
    else:
        filename = f"photo_{update.message.message_id}"
    # Ensure it has an extension
    if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
        filename += ".jpg"
    full_path = os.path.join(PIC_DIR, filename)
    await photo_file.download_to_drive(full_path)
    await update.message.reply_text(
        f"✅ Photo saved as '{full_path}'. You can ask for it later using 'get pic {filename}'"
    )
    # Send the photo to Agent Zero
    try:
        with open(full_path, "rb") as f:
            base64_content = base64.b64encode(f.read()).decode("utf-8")
        attachments = [{"filename": filename, "base64": base64_content}]
        prompt = (
            update.message.caption
            if update.message.caption
            else "Please analyze this image."
        )
        asyncio.create_task(
            process_agent_task(
                prompt, update.message.chat_id, context, attachments=attachments
            )
        )
    except Exception as e:
        logging.error(f"Error sending photo to Agent Zero: {e}")
        await update.message.reply_text(f"❌ Error sending photo to Agent Zero: {e}")


async def scheduled_job(context: ContextTypes.DEFAULT_TYPE):
    """The job that runs on a schedule."""
    job = context.job
    prompt = job.data["prompt"]
    chat_id = job.data["chat_id"]
    await process_agent_task(prompt, chat_id, context, is_scheduled=True)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to schedule a recurring task. Usage: /schedule <name> <seconds> <prompt>"""
    if update.message.from_user.id != MY_ID:
        return
    logging.info(
        f"📜 COMMAND [Schedule] from {update.message.from_user.first_name}: {update.message.text}"
    )
    try:
        name = context.args[0]
        interval = int(context.args[1])
        prompt = " ".join(context.args[2:])
        if not prompt:
            await update.message.reply_text(
                "Please provide a prompt. Usage: /schedule <name> <seconds> <prompt>"
            )
            return
        chat_id = update.message.chat_id
        # Check if job with this name already exists
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if current_jobs:
            await update.message.reply_text(
                f"❌ A schedule named '{name}' already exists."
            )
            return
        # Add job to queue
        context.job_queue.run_repeating(
            scheduled_job,
            interval=interval,
            first=5,  # run first time after 5 seconds
            data={"prompt": prompt, "chat_id": chat_id, "interval": interval},
            name=name,
            job_kwargs={
                "max_instances": 2
            },  # Allow up to 5 overlapping instances of this specific job
        )
        await update.message.reply_text(
            f"✅ Scheduled task '{name}' added! Will run '{prompt}' every {interval} seconds."
        )
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /schedule <name> <seconds> <prompt>")


async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to stop scheduled tasks. Usage: /stopschedule [name]"""
    if update.message.from_user.id != MY_ID:
        return
    logging.info(
        f"📜 COMMAND [StopSchedule] from {update.message.from_user.first_name}: {update.message.text}"
    )
    if context.args:
        name = context.args[0]
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            await update.message.reply_text(
                f"❌ No scheduled task found with name '{name}'."
            )
            return
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text(f"✅ Scheduled task '{name}' stopped.")
    else:
        current_jobs = context.job_queue.jobs()
        if not current_jobs:
            await update.message.reply_text("No scheduled tasks running.")
            return
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("✅ All scheduled tasks stopped.")


async def schedules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to list all scheduled tasks."""
    if update.message.from_user.id != MY_ID:
        return
    logging.info(f"📜 COMMAND [Schedules] from {update.message.from_user.first_name}")
    current_jobs = context.job_queue.jobs()
    if not current_jobs:
        await update.message.reply_text("No scheduled tasks running.")
        return
    text = "📅 Running Schedules:\n"
    for job in current_jobs:
        interval = job.data.get("interval", "unknown")
        prompt = job.data.get("prompt", "unknown")
        text += f"• {job.name} (every {interval}s): {prompt}\n"
    await update.message.reply_text(text)


async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to start a new session."""
    if update.message.from_user.id != MY_ID:
        return
    logging.info(f"📜 COMMAND [New] from {update.message.from_user.first_name}")
    reset_session()
    await update.message.reply_text(
        "✨ New session started. Conversation history cleared."
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to stop the current conversation."""
    if update.message.from_user.id != MY_ID:
        return
    logging.info(f"📜 COMMAND [Stop] from {update.message.from_user.first_name}")
    reset_session()
    await update.message.reply_text("🛑 Conversation stopped and session cleared.")


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to restart the session."""
    if update.message.from_user.id != MY_ID:
        return
    logging.info(f"📜 COMMAND [Restart] from {update.message.from_user.first_name}")
    reset_session()
    await update.message.reply_text(
        "🔄 Session restarted. Ready for a new conversation."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show all available features and commands."""
    if update.message.from_user.id != MY_ID:
        return
    logging.info(f"📜 COMMAND [Help] from {update.message.from_user.first_name}")
    # Properly escape ENVIRONMENT for MarkdownV2
    safe_env = ENVIRONMENT.replace("-", "\\-").replace(".", "\\.")
    help_text = (
        "🤖 *OpenClaw/Agent Zero Bot Help*\n\n"
        "*Commands:*\n"
        "/new \\- Start a new session \\(clear conversation history\\)\\.\n"
        "/stop \\- Stop the current conversation and clear session\\.\n"
        "/restart \\- Restart the session \\(same as /new and /stop\\)\\.\n"
        "/schedule \\<name\\> \\<seconds\\> \\<prompt\\> \\- Schedule a recurring task\\.\n"
        "  _Example: /schedule btc 600 Check the price of Bitcoin_\n"
        "/stopschedule \\[name\\] \\- Stop a specific schedule by name, or all if no name provided\\.\n"
        "/schedules \\- List all running schedules\\.\n"
        "/help \\- Show this information\\.\n\n"
        "*Features:*\n"
        "• *Chatting:* Simply send any text message to get a response from Agent Zero\\.\n"
        "• *Storing Photos:* Send a photo to the bot to save it\\. If you provide a caption, the photo will be saved with that name \\(e\\.g\\., `my_document`\\)\\. The photo will also be sent to Agent Zero for analysis\\.\n"
        "• *Retrieving Photos:* Type `get pic \\<filename\\>` to have the bot send a saved photo back to you\\.\n\n"
        "Current Mode: `" + safe_env + "`"
    )
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")


def main():
    # Verify environment variables are present
    if not TOKEN or MY_ID == 0:
        logging.error("TELEGRAM_TOKEN or MY_USER_ID environment variables are missing!")
        return
    # Build the Telegram Application
    application = Application.builder().token(TOKEN).build()
    # Handle text messages (excluding commands)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request)
    )
    # Handle incoming photos
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # Handle commands for scheduling
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("stopschedule", stop_schedule_command))
    application.add_handler(CommandHandler("schedules", schedules_command))
    # Handle session commands
    application.add_handler(CommandHandler("new", new_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("restart", restart_command))
    # Handle the help command
    application.add_handler(CommandHandler("help", help_command))
    logging.info(f"Bot started successfully for authorized user: {MY_ID}")
    logging.info(f"Environment: {ENVIRONMENT}")
    # Start the bot
    application.run_polling()


if __name__ == "__main__":

    main()
