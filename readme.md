nohup ./env/bin/langgraph dev --host 0.0.0.0 --port 2024 > langgraph.log 2>&1 &

ps aux | grep langgraph | grep -v grep