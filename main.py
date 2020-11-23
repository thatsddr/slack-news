import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")["user_id"]

message_count={}

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    if BOT_ID != user_id:
        if user_id in message_count:
            message_count[user_id] += 1
        else:
            message_count[user_id] = 1
        #client.chat_postMessage(channel=channel_id, text=f"{user_id} said {text}")

#slash commands
@app.route("/count-messages", methods=["POST"])
def count_messages():
    data = request.form
    uid = data.get("user_id")
    cid = data.get("channel_id")
    current_num = message_count.get(uid,0)
    client.chat_postMessage(channel=cid, text=f"since the development server is on, {uid} sent {current_num} messages")
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)