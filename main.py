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
from ByKeyword import ByKeyword
from RandomNews import RandomNews

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
    "abcnews.go.com":{"name": "ABC", "bias": "left"},
    "www.washingtonpost.com": {"name": "Washington Post", "bias": "left"},
    "apnews.com": {"name": "Associated Press", "bias":"center"},
    "www.reuters.com": {"name": "Reuters", "bias":"center"},
    "www.ft.com": {"name": "Financial Times", "bias":"center"},
    "www.thehill.com": {"name": "The Hill", "bias": "center"},
    "upi.com": {"name": "UPI", "bias": "center"},
    "fortune.com": {"name": "Fortune", "bias": "center"},
    "www.foxnews.com": {"name": "Fox News", "bias":"right"},
    "www.nypost.com": {"name": "New York Post", "bias":"right"},
    "www.wsj.com": {"name": "Wall Street Journal", "bias":"right"},
    "www.nationalreview.com": {"name": "National Review", "bias":"right"},
    "reason.com": {"name": "Reason", "bias": "right"},
    "bostonherald.com": {"name":"Boston Herald", "bias": "right"}
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


#give an url, get an object of 3
def get_items(url):
    headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
    res = {}
    try:
        res = requests.get(url=url, headers=headers)
    except:
        return None

    soup = bs(res.content, "html.parser")

    findings = []
    for itm in soup.find_all("item"):
        obj = {}
        obj["title"] = itm.title.string
        obj["link"] = itm.link.next_sibling
        obj["source"] = itm.find_all("source")[0].get("url")
        findings.append(obj)

    return findings

def get_results(obj):
    if obj == None:
        return None
    results = {}
    bias_covered = []
    for i in obj:
        if i["source"][8:] in URLS:
            bias = URLS[i["source"][8:]]["bias"]
            if bias not in bias_covered:
                results[bias] = i
                bias_covered.append(bias)
            elif random.randint(1,15) == 1:
                print("SWITCH")
                results[bias] = i
        if len(bias_covered) > 2:
            break

    if len(bias_covered) > 0:
        links = ""
        for k, v in results.items():
            source = v["source"][8:]
            name = URLS[source]["name"]
            link = v["link"]
            links += f"from the {k}: <{link}|{name}>\n"

        bias_type = bias_covered[random.randint(0, len(bias_covered)-1)]
        main_title = results[bias_type]["title"]

        return {"links":links, "main_title":main_title, "len":len(results)}
    else:
        return None

#search news by keyword & relevant functions
'''
def to_markdown_keyword(text, main_title, links):
    return [{
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f":mag: Here is what I've found about '{text}'\n\n")
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

def keywordAction(url, cid, text):
    utext = quote(text)
    
    final = get_results(get_items(f"https://news.google.com/rss/search?q={utext}&hl=en-US&gl=US&ceid=US:en"))
    if final == None:
        return requests.post(url=url,data=json.dumps({"text":"an error occured","username": "slack-news", "icon_emoji":":newspaper:"})) 

    main_title = final["main_title"]
    links = final["links"]

    if final["len"] > 0:
        blocks = to_markdown_keyword(text, main_title, links)
        return client.chat_postMessage(channel=cid, icon_emoji=":newspaper:", blocks=blocks, username="LATEST NEWS")
    else:
        requests.post(url=url,data=json.dumps({"text":"no sources in our database","username": "slack-news", "icon_emoji":":newspaper:"})) 
'''
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


#gets random news
'''
def to_markdown_random(main_title, links):
    return [{
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f":mag: Here are some of the latest news\n\n")
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

def randomAction(url, cid):

    results = get_results(get_items("https://news.google.com/rss?oc=5&hl=en-US&gl=US&ceid=US:en"))
    if results == None:
        payload = {"text":"an error occured","username": "slack-news", "icon_emoji":":newspaper:"}
        return requests.post(url=url,data=json.dumps(payload)) 

    random_news = results["main_title"][0:results["main_title"].index("-")]
    utext = quote(random_news)

    final = get_results(get_items(f"https://news.google.com/rss/search?q={utext}&hl=en-US&gl=US&ceid=US:en"))
    if final == None:
        return requests.post(url=url,data=json.dumps({"text":"an error occured","username": "slack-news", "icon_emoji":":newspaper:"})) 

    main_title = final["main_title"]
    links = final["links"]

    if final["len"] > 0:
        blocks = to_markdown_random(main_title, links)
        return client.chat_postMessage(channel=cid, icon_emoji=":newspaper:", blocks=blocks, username="LATEST NEWS")
    else:
        requests.post(url=url,data=json.dumps({"text":"no sources in our database","username": "slack-news", "icon_emoji":":newspaper:"})) 
'''
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
    '''
    thr = Thread(target=randomAction, args=[response_url, cid])
    thr.start()
    '''
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
    