module.exports = {
  apps: [
    {
      name: "sentiment-bot",
      script: "bot/main.py",
      interpreter: "venv/bin/python",
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};
