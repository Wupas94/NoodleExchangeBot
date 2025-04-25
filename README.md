# Discord Auto-Delete Bot

A Discord bot that automatically deletes its own messages after 12 hours.

## Features

- Automatically deletes bot's messages after 12 hours
- Simple and efficient message tracking
- Error handling for message deletion

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the root directory and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   ```

3. Make sure your bot has the following permissions:
   - Manage Messages
   - Read Messages/View Channels
   - Send Messages

## Running the Bot

Run the bot using:
```bash
python bot.py
```

## Notes

- The bot will only delete messages that are less than 14 days old (Discord API limitation)
- Messages are tracked in memory, so they will be lost if the bot restarts
- Make sure to keep your bot token secure and never share it publicly 