# Agent-Zero Telegram Bot

A Telegram bot interface designed to work side-by-side with [Agent-Zero](https://github.com/agent0ai). This project spins up a multi-container Docker environment containing an isolated Agent-Zero instance and a connected Telegram Bot.

## Architecture

The system runs using `docker-compose` and spinning up three intertwined containers:
1. **Firewall**: Alpine-based network admin restricting external API calls and keeping Agent-Zero secure.
2. **Agent-Zero**: The AI agent executing tasks (`agent0ai/agent-zero:latest`), communicating via the firewall network.
3. **Bot**: The Python Telegram Bot listening to your Telegram messages and dispatching them to Agent-Zero over the internal network.

---

## 🛠️ How to Build & Setup

### 1. Prerequisites
- [Docker](https://www.docker.com/) and `docker-compose` installed.
- A Telegram Bot Token. 
  - Go to Telegram and message **[@BotFather](https://t.me/BotFather)**.
  - Send `/newbot`, give it a name and a username.
  - Copy the **HTTP API Token** provided.
- Your Telegram User ID.
  - Go to **[@userinfobot](https://t.me/userinfobot)** on Telegram and click Start. The bot will reply with your ID (a 9-10 digit number).

### 2. Configure Environment `.env`
Create a `.env` file in the root directory (alongside `docker-compose.yml`) to securely store your credentials without modifying the YAML files:

```ini
TELEGRAM_TOKEN=1234567890:ABCdefGHiJkLmNoPqRsTuVwXyZ
MY_USER_ID=1234567890
AGENT_ZERO_API_KEY=your_agent_zero_api_key_here
```
*(Optional: Provide an explicitly generated API key from Agent-Zero's External Services settings if needed.)*

### 3. Build & Run
Open your terminal in the project directory where the `docker-compose.yml` is located and run:

```bash
docker-compose up -d --build --force-recreate
```

This will:
- Spin up the firewall container.
- Download and run the `agent-zero` container.
- Build dependencies inside the `bot` container natively on startup and connect to Telegram.

---

## 🤖 How to Use It

Once your containers are running, you can connect to your bot:
1. Open the **Telegram application**.
2. Search for your bot using its `@Username`.
3. Click **Start**.
4. **Send a message:** Type whatever you'd like your agent to research or do (e.g., *"Check the weather today in New York"*).

### Available Commands
- `/help` - Show the help menu with all available commands and features.
- `/new` - Start a new session (clear conversation history).
- `/stop` - Stop the current conversation (this does NOT affect schedules).
- `/restart` - Restart the session (completes a stop followed by a new session).
- `/schedule <name> <seconds> <prompt>` - Schedule a recurring task.
  - Example: `/schedule btc 600 Check the price of Bitcoin`
- `/stopschedule [name]` - Stop a specific schedule by name, or all if no name is provided.
- `/schedules` - List all currently running schedules.

You can also:
- Send any text message to chat with the bot.
- Send a photo to save it (use the caption as the filename).
- Type `get pic <filename>` to retrieve a saved photo.

---

## 🔍 Troubleshooting (Debugging)

If the setup fails or the bot isn't responding, utilize Docker's logging features:

1. **Check if containers are running:**
```bash
docker ps
```
2. **View live logs for the Telegram Bot:**
```bash
docker logs -f agent-zero-telegram-bot
```
3. **View live logs for Agent-Zero:**
```bash
docker logs -f agent-zero-isolated
```
4. **Rerstart container**
```bash
Container agent-zero-telegram-bot Restarting
```

## Agent-Zero website
You can also manually access the Agent-Zero web UI locally:
[http://localhost:5000](http://localhost:5000)