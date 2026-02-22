py -m venv .venv
.venv\Scripts\activate
py where
py -m pip install -r .\requirements.txt
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
export ENVIRONMENT=prod;./run.sh
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