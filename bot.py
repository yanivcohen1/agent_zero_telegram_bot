import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Configure logging to see events in 'docker logs'
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Fetch settings from environment variables (defined in docker-compose.yml)
TOKEN = os.getenv("TELEGRAM_TOKEN", "8531898414:AAHe2o9A1Nb7Q3gd3m0PHKSV23tBjdTxOdU")
MY_ID = int(os.getenv("MY_USER_ID", "6977408305"))
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
PIC_DIR = "pic"

# Ensure the pictures directory exists
os.makedirs(PIC_DIR, exist_ok=True)

agent = None

if ENVIRONMENT == "dev":
    import ollama
    logging.info("Running in DEV mode using direct Ollama client.")
else:
    from agent_zero import Agent
    from langchain_community.llms import Ollama
    logging.info("Running in PROD mode using Agent Zero.")
    if os.name == 'nt':  # Windows
        logging.info("Running in Windows.")
        OLLAMA_URL = "http://localhost:11434"
    else:  # Linux/Mac
        logging.info("Running in Linux.")
        OLLAMA_URL = "http://host.docker.internal:11434"
    # 1. Initialize the LLM - Using local Ollama
    llm = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
    # 2. Initialize the Agent Zero Agent
    agent = Agent(llm=llm, headless=True)

def run_agent_sync(prompt: str, screenshot_path: str) -> str:
    """Runs the agent synchronously. This is executed in a separate thread."""
    if ENVIRONMENT == "dev":
        client = ollama.Client(host=OLLAMA_URL)
        response = client.chat(model=OLLAMA_MODEL, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return response['message']['content']
    else:
        result = agent.run(prompt)
        if hasattr(agent, 'browser') and agent.browser:
            agent.browser.page.screenshot(path=screenshot_path)
        return result

async def process_agent_task(prompt: str, chat_id: int, context: ContextTypes.DEFAULT_TYPE, is_scheduled: bool = False):
    prefix = "⏰ Scheduled Task" if is_scheduled else "🚀 Task"
    await context.bot.send_message(chat_id=chat_id, text=f"{prefix} starting: '{prompt}'...")

    try:
        screenshot_path = f"action_{chat_id}.png"
        
        # Run the agent task in a separate thread to avoid blocking the Telegram bot event loop
        result = await asyncio.to_thread(run_agent_sync, prompt, screenshot_path)

        # Send the text response
        await context.bot.send_message(chat_id=chat_id, text=f"✅ {prefix} Completed!\n\nResponse:\n{result}")

        # Send the screenshot to the user if it exists
        if os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id, 
                    photo=photo, 
                    caption="Here is the visual result from the browser:"
                )
            os.remove(screenshot_path) # Clean up the temporary file

    except Exception as e:
        logging.error(f"Error during OpenClaw execution: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error executing task: {str(e)}")

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Security check: Only allow the authorized user
    if update.message.from_user.id != MY_ID:
        logging.warning(f"Unauthorized access attempt by ID: {update.message.from_user.id}")
        await update.message.reply_text("⛔ Access Denied: You are not my administrator.")
        return

    user_query = update.message.text
    chat_id = update.message.chat_id
    
    # Check if the user is asking for a specific picture
    if user_query.lower().startswith("get pic "):
        pic_name = user_query[8:].strip()
        full_path = os.path.join(PIC_DIR, pic_name)
        if os.path.exists(full_path):
            with open(full_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id, 
                    photo=photo, 
                    caption=f"Here is {pic_name}"
                )
        else:
            await update.message.reply_text(f"❌ Could not find picture named '{pic_name}' in '{PIC_DIR}/'")
        return
    
    # Process the task asynchronously
    asyncio.create_task(process_agent_task(user_query, chat_id, context))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming photos and saves them with their caption or a default name."""
    if update.message.from_user.id != MY_ID:
        return

    photo_file = await update.message.photo[-1].get_file()
    
    # Use caption as filename if provided, otherwise use a default name
    filename = update.message.caption if update.message.caption else f"photo_{update.message.message_id}.jpg"
    
    # Ensure it has an extension
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        filename += ".jpg"
        
    full_path = os.path.join(PIC_DIR, filename)
    await photo_file.download_to_drive(full_path)
    await update.message.reply_text(f"✅ Photo saved as '{full_path}'. You can ask for it later using 'get pic {filename}'")

async def scheduled_job(context: ContextTypes.DEFAULT_TYPE):
    """The job that runs on a schedule."""
    job = context.job
    prompt = job.data['prompt']
    chat_id = job.data['chat_id']
    await process_agent_task(prompt, chat_id, context, is_scheduled=True)

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to schedule a recurring task. Usage: /schedule <seconds> <prompt>"""
    if update.message.from_user.id != MY_ID:
        await update.message.reply_text("⛔ Access Denied.")
        return

    try:
        interval = int(context.args[0])
        prompt = " ".join(context.args[1:])
        
        if not prompt:
            await update.message.reply_text("Please provide a prompt. Usage: /schedule <seconds> <prompt>")
            return
            
        chat_id = update.message.chat_id
        
        # Add job to queue
        context.job_queue.run_repeating(
            scheduled_job, 
            interval=interval, 
            first=5, # run first time after 5 seconds
            data={'prompt': prompt, 'chat_id': chat_id},
            name=f"{chat_id}_{prompt[:10]}"
        )
        
        await update.message.reply_text(f"✅ Scheduled task added! Will run '{prompt}' every {interval} seconds.")
        
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /schedule <seconds> <prompt>")

async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to stop all scheduled tasks."""
    if update.message.from_user.id != MY_ID:
        return
    
    current_jobs = context.job_queue.jobs()
    if not current_jobs:
        await update.message.reply_text("No scheduled tasks running.")
        return
        
    for job in current_jobs:
        job.schedule_removal()
        
    await update.message.reply_text("✅ All scheduled tasks stopped.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show all available features and commands."""
    if update.message.from_user.id != MY_ID:
        return

    help_text = (
        "🤖 *OpenClaw/Agent Zero Bot Help*\n\n"
        "*Commands:*\n"
        "/schedule <seconds> <prompt> \\- Schedule a recurring task\\.\n"
        "/stopschedule \\- Stop all currently running scheduled tasks\\.\n"
        "/help \\- Show this information\\.\n\n"
        "*Features:*\n"
        "• *Chatting:* Simply send any text message to get a response from the model \\(`" + OLLAMA_MODEL + "`\\)\\.\n"
        "• *Storing Photos:* Send a photo to the bot to save it\\. If you provide a caption, the photo will be saved with that name \\(e\\.g\\., `my_document`\\)\\.\n"
        "• *Retrieving Photos:* Type `get pic <filename>` to have the bot send a saved photo back to you\\.\n\n"
        "Current Mode: `" + ENVIRONMENT + "`"
    )
    
    await update.message.reply_text(help_text, parse_mode='MarkdownV2')

def main():
    # Verify environment variables are present
    if not TOKEN or MY_ID == 0:
        logging.error("TELEGRAM_TOKEN or MY_USER_ID environment variables are missing!")
        return

    # Build the Telegram Application
    application = Application.builder().token(TOKEN).build()

    # Handle text messages (excluding commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request))
    
    # Handle incoming photos
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Handle commands for scheduling
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("stopschedule", stop_schedule_command))
    
    # Handle the help command
    application.add_handler(CommandHandler("help", help_command))

    logging.info(f"Bot started successfully for authorized user: {MY_ID}")
    logging.info(f"Using Ollama Model: {OLLAMA_MODEL} at {OLLAMA_URL}")
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
