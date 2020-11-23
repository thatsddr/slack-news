import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from Welcome import WelcomeMessage

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")["user_id"]

message_count={}
welcome_messages = {}

def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_msg()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    welcome_messages[channel][user] = welcome

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    if user_id != None and BOT_ID != user_id:
        if user_id in message_count:
            message_count[user_id] += 1
        else:
            message_count[user_id] = 1
    
        if text.lower() == "bot, welcome me":
            send_welcome_message(channel_id, user_id)


@slack_event_adapter.on('reaction_added')
def check_reaction(payload):
    event = payload.get('event', {})
    channel_id = event.get("item", {}).get("channel")
    user_id = event.get("user")

    if payload["event"]["reaction"] == "x":
        try:
            client.chat_delete(
                channel=payload["event"]["item"]["channel"], ts=payload["event"]["item"]["ts"]
            )
        except:
            print("no")

    if channel_id not in welcome_messages:
        return
    
    welcome = welcome_messages[channel_id][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    message = welcome.get_msg()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message["ts"]


#slash commands
@app.route("/count-messages", methods=["POST"])
def count_messages():
    data = request.form
    uid = data.get("user_id")
    cid = data.get("channel_id")
    current_num = message_count.get(uid,0)
    client.chat_postMessage(channel=cid, text=f"since the development server is on, {uid} sent {current_num} messages")
    return Response(), 200

@app.route("/nuke", methods=["POST"])
def nuke():
    data = request.form
    uid = data.get("user_id")
    cid = data.get("channel_id")
    res = client.conversations_history(channel=cid)
    for m in res["messages"]:
        print(m)
        print("\n")
        try:
            client.chat_delete(channel=cid, ts=m["ts"])
        except:
            print("failed to delete")
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True)