py -m venv .venv
.venv\Scripts\activate
py where
py -m pip install -r .\requirements.txt
py -m pip install --upgrade pip

# run it with dev default
py agent_zero_telegram_bot.py

# bot location
/a0/usr/workdir/agent_zero_telegram_bot.py.
docker cp .\agent_zero_telegram_bot.py agent-zero:/a0/usr/workdir/telegram_bot/
chmod +x run.sh
./run.sh
---

## Bot Commands

- `/help` - Show the help menu.
- `/new` - Start a new session (clear history).
- `/stop` - Stop current conversation (not schedules).
- `/restart` - Restart conversation session.
- `/schedule <name> <seconds> <prompt>` - Schedule a recurring task.
  - Example: `/schedule btc 600 Check the price of Bitcoin`
- `/stopschedule [name]` - Stop a specific schedule by name, or all if no name is provided.
- `/schedules` - List all currently running schedules.
- `get pic <filename>` - Retrieve a saved photo.