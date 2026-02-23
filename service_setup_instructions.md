# Instructions for running the bot inside the Agent Zero Docker container

Since your container uses **Supervisor** to manage processes, the best way to ensure your bot starts automatically is to add it directly to the Supervisor configuration.

### 1. Add your bot directly to the Supervisor config
Run the following command in your container's terminal. This will append the bot's configuration to the end of the main `supervisord.conf` file:

```bash
cat <<EOF >> /etc/supervisor/conf.d/supervisord.conf

[program:telegram_bot]
command=/bin/bash /a0/usr/workdir/telegram_bot/run.sh
directory=/a0/usr/workdir/telegram_bot
user=root
autostart=true
autorestart=true
stopwaitsecs=10
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
startretries=3
stopasgroup=true
killasgroup=true
EOF
```
*(Note: This configuration maps the bot's logs to `/dev/stdout`, so they will appear directly in the main Docker container logs.)*

### 2. Reload Supervisor to start the bot
Run these commands to tell Supervisor about the new process:

```bash
supervisorctl reread
supervisorctl update
```

### 3. Manage the bot
You can now control the bot using these commands:
* **Check status:** `supervisorctl status telegram_bot`
* **Restart bot:** `supervisorctl restart telegram_bot`
* **Stop bot:** `supervisorctl stop telegram_bot`
* **View all processes:** `supervisorctl status`

### 4. How to view logs
Since the logs are now integrated with Docker, you can view them using your usual Docker log viewer, or by running:
```bash
tail -f /a0/usr/workdir/telegram_bot/bot.out.log
```
(If you didn't change the log-to-stdout setting).

