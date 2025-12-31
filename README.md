# Job Alert Telegram Bot 🤖

A Python bot that scrapes job listings from various sources (Google Jobs, RemoteOK, WeWorkRemotely) and sends alerts to a Telegram chat. It supports filtering by role, location, and experience level (Fresher/Experienced).

## Features

- **Multi-Source Scraping**: Fetches jobs from Google Jobs (India & USA), RemoteOK, and WeWorkRemotely.
- **Smart Filtering**: Filters jobs based on role keywords (e.g., "Frontend", "Backend") and experience level.
- **Interactive Setup**: Asks you whether you are looking for "Fresher" or "Experienced" roles upon startup.
- **Telegram Notifications**: Sends instant job alerts with direct apply links to your Telegram chat.
- **Duplicate Prevention**: Keeps track of seen jobs to avoid sending duplicate alerts.

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Your Telegram Chat ID (you can use [@userinfobot](https://t.me/userinfobot) to find this)

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/JobAlertTelegramBot.git
    cd JobAlertTelegramBot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the bot:**
    - Rename `config.example.json` to `config.json`.
    - Open `config.json` and replace the placeholder values with your actual Telegram Bot Token and Chat ID.

    ```json
    {
        "telegram_bot_token": "YOUR_ACTUAL_BOT_TOKEN",
        "telegram_chat_id": "YOUR_ACTUAL_CHAT_ID",
        ...
    }
    ```
    - You can also customize `keywords_include`, `keywords_exclude`, and `roles` in `config.json` to match your specific job search criteria.

4.  **Run the bot:**
    ```bash
    python job_bot.py
    ```

## Usage

- When you first run the bot, it will send a message to your Telegram chat asking if you are looking for **Fresher** or **Experienced** jobs.
- Reply to the bot with your preference.
- The bot will then start scanning for jobs and send you alerts based on your choice.
- The bot checks for new jobs every `scan_interval_minutes` (configured in `config.json`).

## Files

- `job_bot.py`: The main bot script.
- `config.json`: Configuration file for tokens and search filters (ignored by Git).
- `config.example.json`: Template for the configuration file.
- `seen_jobs.json`: Stores IDs of jobs already sent to avoid duplicates (ignored by Git).
- `bot.log`: Log file for debugging (ignored by Git).

## Disclaimer

This bot scrapes public job listings. Please respect the terms of service of the websites being scraped. The scraper logic may need updates if the source websites change their layout.
