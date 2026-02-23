py -m venv .venv
.venv\Scripts\activate
py where
.\run.cmd

# or manualy
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -r /a0/requirements.txt
py -m pip install --upgrade pip

# run it with dev default
py agent_zero_telegram_bot.py

# bot RUN
/a0/usr/workdir/telegram_bot/agent_zero_telegram_bot.py.
docker cp .\agent_zero_telegram_bot.py agent-zero:/a0/usr/workdir/telegram_bot/
# run in new session not dettach mode kill it when exit
docker exec -it agent-zero /bin/bash
cd /a0/usr/workdir/telegram_bot/
chmod +x run.sh
. .venv/bin/activate
which python3
# Install build headers if needed (for numpy source build in Python 3.13 in some environments)
apt update && apt install -y python3-dev build-essential
# Use only-binary orjson to avoid Rust compiler issues we saw earlier
cd /a0/usr/workdir/telegram_bot/;. .venv/bin/activate
export ENVIRONMENT=prod;python3 agent_zero_telegram_bot.py
./run.sh
# stop the run
exit
# run in new session not dettach mode kill it when exit
docker exec -e ENVIRONMENT=prod -d agent-zero ./run.sh
docker logs -f agent-zero
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