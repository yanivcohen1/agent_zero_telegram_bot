 # to start
 systemctl --user start openclaw-gateway.service
 
 # to disable it for startup
 systemctl --user disable openclaw-gateway.service
 systemctl --user stop openclaw-gateway.service
 
 # to enable it on startup
 systemctl --user enable openclaw-gateway.service
 systemctl --user start openclaw-gateway.service
 

 # configure openclaw
 ollama launch openclaw

 # change model
 ollama launch openclaw --config

  # TUI (to chat)
 openclaw tui
 
 # web gui
 openclaw dashboard --no-open
 ssh -L 18789:127.0.0.1:18789 yanivc@192.168.0.155
 
 # lOG
 openclaw logs --follow
 
  # service log
 journalctl --user -u openclaw-gateway -f

 # openclaw status
  openclaw gateway status

 # openclaw stop
 openclaw gateway stop
 
 # change model
 openclaw config set agents.defaults.model.primary "ollama/gemma2:2b"
 openclaw gateway restart
 
 # msg
 openclaw sessions tail --session-key "agent:main:main"

 # pairing see readme_telegram.md (send /start and get the paring code)
 openclaw pairing approve telegram ZADX65W4



 # restart docker
 docker restart openclaw_main
 
 # all 
 clear && docker exec -it openclaw_main rm -rf /root/.openclaw/agents/main/sessions/ && docker restart openclaw_main &&  docker logs -f openclaw_main
 
 # see docker log
 docker logs -f openclaw_main
 
 # user premition
 sudo chown -R $USER:$USER ~/openclaw-bot
 
 # clear session
 docker exec -it openclaw_main openclaw sessions clear
 docker exec -it openclaw_main rm -rf /root/.openclaw/agents/main/sessions/*
 
 # ollama ps
 docker exec -it openclaw_main ollama ps
 
 # ollama chat
 ollama run orieg/gemma3-tools:4b
 
 docker exec -it openclaw_main ollama ls
 
 docker stop openclaw_main
 
 # init 
 docker exec -it openclaw_main openclaw agents add custom-127-0-0-1-11434
 