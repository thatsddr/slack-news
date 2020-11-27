import slack
import os
import json
import requests
from slackeventsapi import SlackEventAdapter
from threading import Thread
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from ByKeyword import ByKeyword
from RandomNews import RandomNews
from ByURL import ByURL

#dotenv configuration
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

#flask initialization and slack api implementation
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")["user_id"]


#reaction handler that deletes a message if it was sent from the bot and the user reacts with :x:
@slack_event_adapter.on('reaction_added')
def check_reaction(payload):
    event = payload.get('event', {})
    channel_id = event.get("item", {}).get("channel")

    if payload["event"]["reaction"] == "x":
        try:
            client.chat_delete(
                channel=channel_id, ts=payload["event"]["item"]["ts"]
            )
        except:
            pass

#slack slash commands

#test command to check if the bot is installed
@app.route("/test", methods=["POST"])
def test():
    data = request.form
    cid = data.get("channel_id")
    cname = data.get("channel_name")
    client.chat_postMessage(channel=cid, text=f"This app is working properly in #{cname}", icon_emoji=":newspaper:")
    return Response(), 200


#help command
@app.route("/help", methods=["POST"])
def help():
    data = request.form
    cid = data.get("channel_id")
    client.chat_postMessage(channel=cid, text=f"This command will give you some help", icon_emoji=":newspaper:")
    return Response(), 200



@app.route("/search-news", methods=["POST"])
def keywordSearch():
    data = request.form
    cid = data.get("channel_id")
    txt = data.get("text")
    response_url = data.get("response_url")
    if txt.strip() != "":
        payload = {"text":"please wait...","username": "slack-news", "icon_emoji":":newspaper:"}
        requests.post(response_url,data=json.dumps(payload))
        news = ByKeyword(txt, cid, response_url, client)
        thr = Thread(target=news.go)
        thr.start()
    else:
        requests.post(response_url,data=json.dumps({"text":"search for a keyword","username": "slack-news", "icon_emoji":":newspaper:"})) 
    return Response(), 200


@app.route("/random-news", methods=["POST"])
def random_news():
    data = request.form
    cid = data.get("channel_id")
    response_url = data.get("response_url")
    payload = {"text":"please wait...","username": "slack-news", "icon_emoji":":newspaper:"}
    requests.post(response_url,data=json.dumps(payload))
    news = RandomNews(cid, response_url, client)
    thr = Thread(target=news.go)
    thr.start()
    return Response(), 200


#searches for news by url
@app.route("/search-url", methods=["POST"])
def urlSearch():
    data = request.form
    cid = data.get("channel_id")
    input_url = data.get("text")
    response_url = data.get("response_url")
    payload = {"text":"please wait...","username": "slack-news", "icon_emoji":":newspaper:"}
    requests.post(response_url,data=json.dumps(payload))
    
    news = ByURL(input_url, cid, response_url, client)
    thr = Thread(target=news.go)
    thr.start()
    return Response(), 200


#deletes all the messages sent from the bot, to be deleted after testing
def nukeAction(url, cid, msgs): 
    for m in msgs:
        try:
            client.chat_delete(channel=cid, ts=m["ts"])
        except:
            pass
    requests.post(url,data=json.dumps({"text":"your task is complete","username": "slack-news", "icon_emoji":":newspaper:"})) 
@app.route("/nuke", methods=["POST"])
def nuke():
    data = request.form
    cid = data.get("channel_id")
    response_url = data.get("response_url")
    res = client.conversations_history(channel=cid)
    thr = Thread(target=nukeAction, args=[response_url, cid, res["messages"]])
    thr.start()
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)
    