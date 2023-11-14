# JSNotify

This script monitors specified JavaScript files for changes. When a change is detected, it sends a notification via Telegram with a detailed comparison of the changes.

## Features

- **Monitors JavaScript files** for changes
- **Sends notifications through Telegram** with detailed change logs
- **Highlights significant changes** for easy identification

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x installed on your system
- A Telegram bot and chat ID (Instructions below on how to obtain these)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/leetIbrahim/JSNotify
2. **Install the required Python packages:**
   ```bash
   pip install -r requirements.txt
## Configuration
1. **Create a** .env **file in the root directory of the project with the following content:**
   ```bash
   TELEGRAM_TOKEN=[Your_Telegram_Bot_Token]
   TELEGRAM_CHAT_ID=[Your_Telegram_Chat_ID]
Replace `[Your_Telegram_Bot_Token]` and `[Your_Telegram_Chat_ID]` with your actual Telegram bot token and chat ID.

2. **To obtain a** Telegram bot token and chat ID **, follow the instructions provided** [here](https://blog.r0b.re/automation/bash/2020/06/30/setup-telegram-notifications-for-your-shell.html).

## Usage

1. **Prepare a text file** containing the URLs of the JavaScript files you want to monitor, one URL per line.

2. **Run the script** and follow the prompts:
   ```bash
   python3 monitor.py

3. **Enter the path to your file containing the URLs when prompted.**

4. **The script will monitor these URLs and send notifications via Telegram if any changes are detected.**

## Example Notification
**Below is an example of what the notification looks like:**

![Alt Text](https://i.imgur.com/o9IZJSG.png)



Follow me on Twitter [@leetibrahim](https://twitter.com/leetibrahim) for updates.
