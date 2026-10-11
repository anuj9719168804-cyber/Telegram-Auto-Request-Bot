<p align="center">
  <img src="assets/banner.png" alt="Auto Approval Bot Banner" width="780"/>
</p>

<h1 align="center">🚀 Auto Approval Bot</h1>

<p align="center">
  <b>✨ Smart Telegram Join-Request Automation • Advanced Moderation • Powerful Admin Tools</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"/>
  <img src="https://img.shields.io/badge/Database-MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/>
  <img src="https://img.shields.io/badge/License-MIT-success?style=for-the-badge" alt="MIT License"/>
</p>

<p align="center">
  Automate join requests, welcome new members, manage communities, send broadcasts, and monitor activity — all from one feature-packed Telegram bot.
</p>

<p align="center">
  <b>⚡ Fast</b> &nbsp;•&nbsp; <b>🛡️ Security-minded</b> &nbsp;•&nbsp; <b>🧩 Configurable</b> &nbsp;•&nbsp; <b>👨‍💻 Developer-friendly</b>
</p>

---

## 🌟 Overview

**Auto Approval Bot** is a Telegram automation and community-management project built for group and channel administrators. It combines configurable join-request handling with moderation tools, force-subscribe checks, broadcasts, activity logs, analytics, and backup utilities.

> 💡 **Designed for admins:** configure approval behavior per chat and manage common community tasks through Telegram commands or the web admin panel.

## ✨ Feature Highlights

### 🤝 Join-Request Automation
- ⚡ Automatically approve requests immediately or by configured limit, count, or time window (IST).
- 🕹️ Choose manual mode, automatic rejection, or delayed approval with send-only mode.
- 📋 Review pending requests and approve or decline them in bulk, with confirmation, live progress, and a Stop button.
- 🧩 Add CAPTCHA verification before approval and optionally require a username.
- 🧹 Automatically decline stale requests older than a configured number of hours.

### 📢 Force Subscribe
- 🔗 Require membership in one or more channels before users continue.
- ✅ Display subscription status and provide a **Check Again** button.
- 🔄 Support join-request channels configured for approval.

### 👋 Welcome & Notifications
- 💬 Send customizable approval DMs with placeholders such as `{name}`, `{first_name}`, `{username}`, `{mention}`, and `{chat_title}`.
- 🖼️ Include a photo, video, or GIF in approval messages.
- 🔘 Add inline URL buttons and optional auto-delete timers.
- 🎉 Configure group welcome and goodbye messages, leave alerts, and rejoin DMs.

### 🛡️ Moderation & Community Tools
- 🚫 Global ban/unban, temporary bans, mute/unmute, and warnings.
- 🔒 Lock links, stickers, photos, videos, forwards, or other configured content.
- 🧱 Block selected words with blacklist controls.
- 📝 Save notes and create keyword-based automatic replies.
- 🚨 Let members report messages to administrators.
- 👑 Assign owner, co-owner, and admin roles.

### 📣 Broadcast & Administration
- 📤 Broadcast messages with preview and confirmation.
- 📌 Optionally pin broadcasts, add link buttons, and set auto-delete timers.
- 🖥️ Use the web admin panel to manage users, chats, bans, and broadcasts.
- 📊 View analytics, activity logs, and dashboard statistics.
- 💾 Back up and restore settings using JSON.
- 📁 Export supported data to CSV and list users, chats, and unassigned items.

---

## 🤖 Command Reference

### 👤 General Commands

| Command | Description |
|---|---|
| `/start` | 🚀 Open the welcome screen with ABOUT, HELP, and SETTINGS |
| `/cmds`, `/help` | 📚 View commands and setup instructions |
| `/setup` | 🧭 Start the step-by-step setup guide |
| `/settings` | ⚙️ View groups, leave alerts, account details, and admin tools |
| `/about`, `/privacy` | 🔎 View bot information and privacy details |
| `/ping` | ⚡ Check latency and uptime |
| `/feedback <text>` | 💌 Send feedback to the owner |

### 👮 Group & Channel Admin Commands

| Command | Description |
|---|---|
| `/autoapprove` | ✅ Enable or disable auto-approval for the current chat |
| `/autoreject on\|off` | 🚫 Automatically decline new requests |
| `/sendonly on [delay]` | ⏳ Approve after a delay, for example `12h` |
| `/dmdelete 10s\|30s\|1m\|5m\|never` | 🧹 Set approval-DM auto-delete timing |
| `/stalecleanup <hours>\|off` | 🕰️ Decline requests older than the specified age |
| `/setdmwelcome <text>` | 💬 Set approval DM text; reply to media to attach it |
| `/setwelcomebuttons` | 🔘 Configure approval-DM buttons |
| `/pending`, `/approve_all` | 📋 Manage pending requests (logged-in admin session required) |
| `/chatperms lock\|nomedia\|open` | 🔐 Set default member permissions |
| `/ban`, `/unban`, `/kick`, `/mute`, `/unmute`, `/tban`, `/tmute` | 🛡️ Manage member access and restrictions |
| `/warn`, `/warns`, `/unwarn`, `/resetwarn` | ⚠️ Manage warnings (3 warnings = auto-ban, as configured) |
| `/lock`, `/unlock`, `/locks` | 🔒 Manage content locks |
| `/blacklist`, `/unblacklist`, `/blacklists` | 🧱 Manage blocked words |
| `/save`, `/get`, `/notes`, `/clear` | 📝 Save and manage notes using `#name` |
| `/filter`, `/stop`, `/filters` | 🤖 Manage keyword auto-replies |
| `/report` | 🚨 Report a message to admins |

### 🧰 Private Chat — Admin Commands

| Command | Description |
|---|---|
| `/groups` | 🗂️ Manage groups, toggles, and per-group settings |
| `/login`, `/logout`, `/cancel` | 🔑 Manage the userbot session (OTP and 2FA supported) |
| `/admin` | 🎛️ Open the admin control panel |
| `/dashboard`, `/analytics`, `/stats` | 📊 View statistics and analytics |
| `/broadcast`, `/pbroadcast` | 📣 Broadcast with preview and confirmation |
| `/send <user_id>` | ✉️ Send a message to one user |
| `/user <id or @username>` | 👤 View a user card and available ban controls |
| `/banuser`, `/tempban`, `/unbanuser`, `/banned` | 🚫 Manage global bans |
| `/maintenance on\|off` | 🔧 Toggle maintenance mode |
| `/fjoin add\|remove\|list` | 🔗 Manage force-subscribe channels |
| `/setlog <channel_id>` | 🧾 Configure the activity-log channel |
| `/chanban`, `/chanunban`, `/chanbanned` | ⛔ Manage chats the bot should ignore |
| `/autopost add\|list\|del` | 🗓️ Manage scheduled auto-posts |
| `/backup`, `/restore` | 💾 Back up or restore settings |
| `/exportcsv`, `/exportchannels`, `/users`, `/chats`, `/unassigned` | 📁 Export data and inspect lists |
| `/promote <user> [admin\|owner]`, `/demote <user>`, `/admins` | 👑 Manage admin roles |
| `/setbanner`, `/restart` | 🖼️ Set the banner or restart the bot |

---

## ⚙️ Configuration

Set the required values before running the bot. Keep credentials private.

| Variable | Location | Purpose |
|---|---|---|
| `BOT_TOKEN` | `bot.py` | 🔐 Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `OWNER_ID` | `bot.py` | 👑 Telegram user ID of the main owner |
| `API_ID` | `bot.py` | 🔑 Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | `bot.py` | 🔑 Telegram API hash used by the userbot |
| `MONGO_URI` | Environment | 🗄️ MongoDB connection string; if empty, JSON files under `data/` are used |
| `REQUIRED_CHANNEL` | Environment | 🔗 Optional channel users must join before using the bot |
| `PORT` | Environment | 🌐 Host-provided port for health checks and the web admin panel |

### 🔒 Security Checklist
- ✅ Never commit real bot tokens, passwords, API hashes, or database connection strings.
- 🔐 Prefer environment variables or your hosting provider's secret settings.
- ♻️ Rotate any credential that has been exposed publicly.
- 🧰 Give the bot only the Telegram permissions it needs.

---

## 🚀 Deployment Guide

### ☁️ Deploy on Render

1. Connect your Git repository to Render.
2. Set the **Build Command** to:

   ```bash
   pip install -r requirements.txt
   ```

3. Set the **Start Command** to:

   ```bash
   python bot.py
   ```

4. Add `MONGO_URI` and, if needed, `REQUIRED_CHANNEL` in the **Environment** tab.
5. Configure the health-check path as `/health`.

> ℹ️ Render free services may spin down after inactivity, so the first request after idle time can take longer.

### 🖥️ Deploy on a VPS or Local Machine

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the bot
python bot.py
```

If your system uses `python3` instead of `python`, run `python3 bot.py`.

### 🐳 Deploy with Docker

```bash
# Build the image
docker build -t auto-approval-bot .

# Start the container
docker run -d --name auto-approval-bot auto-approval-bot
```

### 🔧 Telegram Setup

1. ➕ Add the bot to your group or channel as an administrator.
2. 🛂 Grant **Invite Users via Link** and **Manage Join Requests** permissions.
3. 🔗 Enable **Approval Required** for the invite link.
4. 💬 Send `/autoapprove` in the chat and enable the feature.

---

## 📁 Project Structure

```text
.
├── bot.py             # Main bot: handlers, storage, web panel, background tasks
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker image configuration
├── Procfile           # Process configuration
├── runtime.txt        # Python runtime version
├── app.json           # App metadata
├── assets/            # Banner and other assets
└── data/              # Runtime JSON storage when MongoDB is not configured
```

## 🧪 Health Check

After deployment, open your service URL with the `/health` path to verify that the health endpoint responds.

## 🤝 Contributing

Suggestions, bug reports, and improvements are welcome. Before submitting a change:

1. 🧹 Keep changes focused and readable.
2. 🧪 Test the affected commands and workflows.
3. 🔐 Never include secrets or personal credentials in commits.
4. 📝 Update this README when adding or changing features.

## 📄 License

This project is distributed under the **MIT License**.

---

<p align="center">
  <b>👨‍💻 Auto Approval Bot</b><br/>
  <sub>⚡ Fast • 🛡️ Configurable • 📊 Feature-rich • 🧩 Developer-friendly</sub><br/><br/>
  <b>❤️ Powered by <a href="https://t.me/anujedits76">Anuj Kumar</a></b>
</p>
