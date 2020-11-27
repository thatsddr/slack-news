import slack
import os
import string
import json
import random
import requests
from slackeventsapi import SlackEventAdapter
from threading import Thread
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
import pprint
from urllib.parse import quote
from bs4 import BeautifulSoup as bs

pp = pprint.PrettyPrinter(indent=4)

#dotenv configuration
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

#flask initialization and slack api implementation
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")["user_id"]

#important
URLS = {
    "www.cnn.com": {"name": "CNN", "bias":"left"},
    "www.nytimes.com": {"name": "New York Times", "bias":"left"},
    "www.theguardian.com": {"name": "The Guardian", "bias":"left"},
    "apnews.com": {"name": "Associated Press", "bias":"center"},
    "www.reuters.com": {"name": "Reuters", "bias":"center"},
    "www.ft.com": {"name": "Financial Times", "bias":"center"},
    "www.thehill.com": {"name": "The Hill", "bias": "center"},
    "www.foxnews.com": {"name": "Fox News", "bias":"right"},
    "www.nypost.com": {"name": "New York Post", "bias":"right"},
    "www.wsj.com": {"name": "Wall Street Journal", "bias":"right"},
    "www.nationalreview.com": {"name": "National Review", "bias":"right"},
    "reason.com": {"name": "Reason", "bias":"right"}
}

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

#gets random news
@app.route("/random-news", methods=["POST"])
def random_news():
    data = request.form
    cid = data.get("channel_id")
    client.chat_postMessage(channel=cid, text=f"this command will return random news", icon_emoji=":newspaper:")
    return Response(), 200


#searches for news by keyword
def keywordAction(url, cid, text):
    ut = quote(text)
    headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
    
    res = requests.get(f"https://news.google.com/rss/search?q={ut}&hl=en-US&gl=US&ceid=US:en", headers=headers)
    soup = bs(res.content, "html.parser")

    findings = []
    for itm in soup.find_all("item"):
        obj = {}
        obj["title"] = itm.title.string
        obj["link"] = itm.link.next_sibling
        obj["source"] = itm.find_all("source")[0].get("url")
        findings.append(obj)
    
    results = {}
    bias_covered = []
    while len(bias_covered) < 3:
        for i in findings:
            if i["source"][8:] in URLS:
                bias = URLS[i["source"][8:]]["bias"]
                if bias not in bias_covered:
                    results[bias] = i
                    bias_covered.append(bias)
                    print("ADDED")
    
    if len(bias_covered) > 0:
        links = ""
        for k, v in results.items():
            source = v["source"][8:]
            name = URLS[source]["name"]
            link = v["link"]
            links += f"from the {k}: <{link}|{name}>\n"

        index = int(random.randrange(len(bias_covered)-1))
        bias_type = bias_covered[index]
        main_title = results[bias_type]["title"]
        blocks = [{
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f"Here is what I've found about '{text}'\n\n")
            }
            },
            {"type": "divider"},
            {
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f"{main_title}\n")
                }
            },
            {"type": "divider"},
            {
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f"\n\n{links}")
            }
        }]
        client.chat_postMessage(channel=cid, icon_emoji=":newspaper:", blocks=blocks, username="LATEST NEWS")
    else:
        payload = {"text":"couldn't find enough","username": "slack-news", "icon_emoji":":newspaper:"}
        requests.post(url=url,data=json.dumps(payload)) 

@app.route("/search-news", methods=["POST"])
def keywordSearch():
    data = request.form
    cid = data.get("channel_id")
    txt = data.get("text")
    response_url = data.get("response_url")
    if txt.strip() != "":
        payload = {"text":"please wait...","username": "slack-news", "icon_emoji":":newspaper:"}
        requests.post(response_url,data=json.dumps(payload)) 
        thr = Thread(target=keywordAction, args=[response_url, cid, txt])
        thr.start()
    else:
        payload = {"text":"your task cannot be completed","username": "slack-news", "icon_emoji":":newspaper:"}
        requests.post(response_url,data=json.dumps(payload)) 
    return Response(), 200


#searches for news by url
@app.route("/search-url", methods=["POST"])
def urlSearch():
    data = request.form
    cid = data.get("channel_id")
    client.chat_postMessage(channel=cid, text=f"this command will return news from a similar url", icon_emoji=":newspaper:")
    return Response(), 200


#deletes all the messages sent from the bot, to be deleted after testing
def nukeAction(url, cid, msgs): 
    for m in msgs:
        try:
            client.chat_delete(channel=cid, ts=m["ts"])
        except:
            pass
    payload = {"text":"your task is complete","username": "slack-news", "icon_emoji":":newspaper:"}
    requests.post(url,data=json.dumps(payload)) 
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
    