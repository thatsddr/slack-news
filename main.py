import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from Welcome import WelcomeMessage
import string
from datetime import datetime, timedelta

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")["user_id"]

message_count={}
welcome_messages = {}

FILTER = ['trump won', 'biden stole the election', "qanon is true", "coronavirus is fake"]

SCHEDULED_IDS = []

def send_welcome_message(channel, user):
    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    if user not in welcome_messages[channel]:
        welcome = WelcomeMessage(channel, user)
        message = welcome.get_msg()
        response = client.chat_postMessage(**message)
        welcome.timestamp = response['ts']
        welcome_messages[channel][user] = welcome
    else:
        client.chat_postMessage(channel=channel, text=f"You've already been welcomed without completing the task", icon_emoji=":newspaper:")

def check_fake(message):
    msg = message.lower()
    msg = msg.translate(str.maketrans('','', string.punctuation))

    return any(word in msg for word in FILTER)

def schedule_message(msg):
    response = client.chat_scheduleMessage(channel=msg["channel"], text=msg['text'], post_at=msg['post_at'], icon_emoji=msg["icon_emoji"]).data
    id_ = response.get('scheduled_message_id')
    return id_

def delete_scheduled(ids, channel):
    try:
        for _id in ids:
            client.chat_deleteScheduledMessage(channel=channel, scheduled_message_id=_id)
            print("DELETED")
    except:
        print("no")


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
        elif check_fake(text):
            ts = event.get('ts')
            client.chat_postMessage(channel=channel_id, thread_ts=ts, text="We detected misleading or fake informations in this message", icon_emoji=":newspaper:")


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
    del welcome_messages[channel_id]

#slash commands
@app.route("/count-messages", methods=["POST"])
def count_messages():
    data = request.form
    uid = data.get("user_id")
    cid = data.get("channel_id")
    name = data.get("user_name")
    current_num = message_count.get(uid,0)
    print(data)
    client.chat_postMessage(channel=cid, text=f"since the development server is on, {name} sent {current_num} messages", icon_emoji=":newspaper:")
    return Response(), 200

@app.route("/nuke", methods=["POST"])
def nuke():
    data = request.form
    cid = data.get("channel_id")
    res = client.conversations_history(channel=cid)
    for m in res["messages"]:
        try:
            client.chat_delete(channel=cid, ts=m["ts"])
        except:
            print("failed to delete")
    return Response(), 200

@app.route("/test", methods=["POST"])
def test():
    data = request.form
    cid = data.get("channel_id")
    cname = data.get("channel_name")
    client.chat_postMessage(channel=cid, text=f"This app is working properly in #{cname}", icon_emoji=":newspaper:")
    return Response(), 200

@app.route("/schedule", methods=["POST"])
def schedule():
    data = request.form
    cid = data.get("channel_id")
    SCHEDULED_IDS.append(schedule_message({"text":"Scheduled message", "post_at": (datetime.now() + timedelta(minutes=1)).timestamp(), "channel": cid, "icon_emoji":":newspaper:"}))
    return Response(), 200

@app.route("/unschedule", methods=["POST"])
def unschedule():
    data = request.form
    cid = data.get("channel_id")
    delete_scheduled(SCHEDULED_IDS, cid)
    for i in SCHEDULED_IDS:
        SCHEDULED_IDS.remove(i)
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True)
    
    