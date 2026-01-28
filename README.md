## SlackAssistant

A small toolkit that helps you draft and manage LinkedIn content and also run a Slack bot that enhances messages using an LLM. It includes:

- Slack bot with Flask + Slack Events API (`bot.py`)
- LinkedIn content co-writer with Notion integration (`tools.py`)
- CLI helpers for brainstorming/writing posts (`tollCalling.py`)
- Experimental Gemini/Streamlit snippet (`audin.py`)

### What you can do
- Draft short, engaging LinkedIn posts powered by Gemini
- Brainstorm ideas, refine drafts, and save final posts to Notion
- Reply in Slack channels with improved, concise rewrites of user messages

## Repository structure
- `bot.py`: Flask server + Slack Events API webhook; listens to messages and replies with an LLM-enhanced version
- `tools.py`: Co-writer workflow (brainstorm → draft → finalize) and a Notion saver; includes a simple interactive CLI
- `tollCalling.py`: Standalone CLI utilities for brainstorming and simple daily reminders
- `audin.py`: Experimental Gemini/Streamlit snippet for quick content generation (not wired into the others)
- `ngrok.exe`: Local tunneling binary for exposing your Flask server to Slack during development
- `.gitignore`: Ensures local secrets, caches are ignored

## Prerequisites
- Python 3.10+ (Windows supported)
- A Slack workspace and permission to create apps
- A Notion account and a database to store posts
- Gemini (Google Generative AI) API key
- Ngrok for local callbacks during Slack development

## Setup

### 1) Create and activate a virtual environment
```powershell
cd M:\SlackAssistant
py -3 -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
```

### 2) Install dependencies
```powershell
pip install flask slackclient slackeventsapi python-dotenv openai httpx requests google-generativeai streamlit langchain langchain-community
```

If you prefer, generate a `requirements.txt` later with:
```powershell
pip freeze > requirements.txt
```

### 3) Create a `.env` file
Never commit this file. Add it to `.gitignore` (already included here). Example:
```env
SLACK_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

GEMINI_API_KEY=...

# Notion (for saving finalized LinkedIn posts)
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Configure external services

### Slack app
1. Create a Slack app (From scratch) in your workspace
2. Add a Bot user and install the app to the workspace
3. Copy the Bot User OAuth Token → `SLACK_TOKEN`
4. Copy the Signing Secret → `SLACK_SIGNING_SECRET`
5. Enable Event Subscriptions:
   - Request URL: will be `https://<your-ngrok-domain>/slack/events`
   - Subscribe to bot events: at minimum, `message.channels` (or events relevant to your bot)
6. Bot Token Scopes typically needed: `chat:write`, `channels:history`, `app_mentions:read` (adjust for your needs)

### Notion
1. Create an internal integration and copy the token → `NOTION_TOKEN`
2. Create a database and share it with the integration
3. Obtain the database ID → `NOTION_DATABASE_ID`
4. Ensure the database has the following properties (names must match):
   - `Post ID` (rich text)
   - `Title` (title)
   - `Content` (rich text)
   - `Status` (select; values include: `Idea`, `Draft`, `Final`, `Posted`)
   - `Date` (date)

### Gemini (Google Generative AI)
1. Get an API key and set `GEMINI_API_KEY` in your `.env`

## Running the apps

### A) Slack bot (`bot.py`)
Start the Flask server:
```powershell
python bot.py
```

Expose it to Slack with ngrok in a separate terminal:
```powershell
./ngrok.exe http 5000
```

Copy the forwarding HTTPS URL and paste it into Slack’s Event Subscriptions Request URL as `https://<ngrok-domain>/slack/events`.

What it does: for each message the bot can see, it calls Gemini to produce a concise, engaging rewrite, and posts that back to the channel.

### B) LinkedIn co-writer CLI (`tools.py`)
`tools.py` includes an interactive assistant that can brainstorm, draft, and optionally save to Notion.

Run it:
```powershell
python tools.py
```

Flow overview:
- You provide an idea; it generates insights/audience/action
- It drafts a concise LinkedIn post (150–280 chars)
- You can say “noted” to save the final post to Notion

### C) CLI utilities (`tollCalling.py`)
This script provides brainstorming and a simple daily reminder flow.
```powershell
python tollCalling.py
```

### D) Experimental snippet (`audin.py`)
Contains a Streamlit/Gemini example function. It’s not integrated with the rest of the app. Consider refactoring before use.

## Security and secrets hygiene
- Keep secrets in `.env` and never commit them
- `.gitignore` already ignores `.env`, but double-check before committing
- If you accidentally committed a secret, rotate it immediately at the provider
- GitHub Push Protection: if a push is blocked for “contains secrets,” remove the secret from your commit(s) and rewrite history if needed

### Cleaning leaked secrets from Git history (quick guide)
1) Stop tracking the file going forward:
```powershell
git rm --cached .env
git commit -m "Stop tracking .env"
```
2) Rewrite history to remove the secret from past commits (choose one):
- Using `git filter-repo` (recommended)
```powershell
pip install git-filter-repo
git filter-repo --path .env --invert-paths
git push --force-with-lease
```
- Or use BFG Repo-Cleaner (see its docs)

3) Rotate the leaked token(s) at the provider (Slack/Notion/Google)

## Troubleshooting
- Slack Request URL fails to verify: ensure ngrok is running, use HTTPS URL, and the path is `/slack/events`
- Bot not responding: confirm the app is installed in the channel, events are subscribed, and tokens/secrets are correct
- Notion save fails: verify database sharing with the integration, property names, and `NOTION_DATABASE_ID`
- SSL/proxy issues calling Gemini: `tools.py` uses an explicit `httpx.Client()` to help with proxies; confirm outbound connectivity

## Notes on code quality and next steps
- Consider migrating `import slack` to `slack_sdk` for the latest API
- Move any hard-coded keys in experimental files into `.env`
- Add tests and a `requirements.txt`
- Containerize for easier deployment if needed

## License
Add a license of your choice (MIT/Apache-2.0/etc.).

