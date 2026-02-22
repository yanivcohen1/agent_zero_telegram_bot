import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openclaw import Agent
from langchain_community.llms import Ollama

# Configure logging to see events in 'docker logs'
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Fetch settings from environment variables (defined in docker-compose.yml)
TOKEN = os.getenv("TELEGRAM_TOKEN", "8531898414:AAHe2o9A1Nb7Q3gd3m0PHKSV23tBjdTxOdU")
MY_ID = int(os.getenv("MY_USER_ID", "6977408305"))
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# 1. Initialize the LLM - Using local Ollama
# Ensure the model is pulled locally (e.g., 'ollama pull llama3')
llm = Ollama(model="gemma3:4b", base_url=OLLAMA_URL)

# 2. Initialize the OpenClaw Agent
# headless=True is mandatory for running inside a Docker container
agent = Agent(llm=llm, headless=True)

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Security check: Only allow the authorized user
    if update.message.from_user.id != MY_ID:
        logging.warning(f"Unauthorized access attempt by ID: {update.message.from_user.id}")
        await update.message.reply_text("⛔ Access Denied: You are not my administrator.")
        return

    user_query = update.message.text
    chat_id = update.message.chat_id
    
    await update.message.reply_text(f"🚀 OpenClaw agent starting task: '{user_query}'...")

    try:
        # Run the agent task
        # The agent will browse the web, analyze data, and return a result
        result = agent.run(user_query)

        # Capture a screenshot of the final browser state
        screenshot_path = "last_action.png"
        agent.browser.page.screenshot(path=screenshot_path)

        # Send the text response
        await update.message.reply_text(f"✅ Task Completed!\n\nResponse:\n{result}")

        # Send the screenshot to the user
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
        await update.message.reply_text(f"❌ Error executing task: {str(e)}")

def main():
    # Verify environment variables are present
    if not TOKEN or MY_ID == 0:
        logging.error("TELEGRAM_TOKEN or MY_USER_ID environment variables are missing!")
        return

    # Build the Telegram Application
    application = Application.builder().token(TOKEN).build()

    # Handle text messages (excluding commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request))

    logging.info(f"Bot started successfully for authorized user: {MY_ID}")
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
