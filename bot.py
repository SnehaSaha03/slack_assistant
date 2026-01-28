import slack
import os
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask,request,Response
from slackeventsapi import SlackEventAdapter
from openai import OpenAI
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(
    os.environ['SLACK_SIGNING_SECRET'], "/slack/events", app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")["user_id"]
LLMclient=OpenAI(
  api_key=os.environ['GEMINI_API_KEY'],
  base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
def process_with_llm(text):
    try:
        response = LLMclient.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[
                {"role": "system", "content": "You are a samrt content writen that enhances the content of the user's message keep the content short and concise and make it more engaging and interesting and text like a human"},
                {"role": "user", "content": text}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"
@slack_events_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if BOT_ID != user_id:
        llm_response = process_with_llm(text)
        client.chat_postMessage(channel=channel_id, text=llm_response)
if __name__ == '__main__':
    app.run(debug=True)