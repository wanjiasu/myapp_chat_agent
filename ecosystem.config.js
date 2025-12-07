module.exports = {
  apps: [
    {
      name: "tele_agentchat",
      cwd: ".",
      script: "env/bin/python",
      args: "-m langgraph dev --host 0.0.0.0 --port 8005",
      autorestart: true,
      watch: false,
      max_memory_restart: "512M",
      out_file: "logs/tele_agentchat.out.log",
      err_file: "logs/tele_agentchat.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    }
  ]
};
