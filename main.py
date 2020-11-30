import slack
import os
import re
import json
import requests
import concurrent.futures
from urllib.parse import unquote
from slackeventsapi import SlackEventAdapter
from threading import Thread
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from SearchByKeyword import ByKeyword
from SearchRandomNews import RandomNews
from SearchByURL import ByURL
from HelpMessage import HelpMessage

#dotenv configuration
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

#flask initialization and slack api implementation
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")["user_id"]

#new messages handled here
@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    text = event.get("text", {})
    cid = event.get("channel")
    thread_ts = event.get("thread_ts", None)
    def check_url(string):    
        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(regex,string)       
        return [x[0] for x in url]
    if BOT_ID in text and thread_ts:
        res = client.conversations_history(channel=cid, latest=thread_ts, inclusive=True,limit=1)
        message_str = res.get('messages', [{}])[0].get("text", None)
        raw_urls = (check_url(message_str))
        urls = []
        if raw_urls:
            for url in raw_urls:
                index = None
                try:
                    index = url.index("|")
                except:
                    index = None
                if index!=None:
                    temp = url[:index]
                    if temp not in urls:
                        urls.append(temp)
                else:
                    if url not in urls:
                        urls.append(url)
            for url in urls:
                news = ByURL(url, cid, None, client, thread=thread_ts)
                thr = Thread(target=news.go_thread)
                try:
                    thr.start()
                except:
                    return client.chat_postMessage(channel=cid, thread_ts=thread_ts, text="Something went wrong...")
        else:
            return client.chat_postMessage(channel=cid, thread_ts=thread_ts, text="No URL detected")


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
@app.route("/test", methods=["POST", "GET"])
def test():
    if request.method == "POST":
        data = request.form
        cid = data.get("channel_id")
        cname = data.get("channel_name")
        client.chat_postMessage(channel=cid, text=f"This app is working properly in #{cname}")
        return Response(), 200
    else:
        return json.dumps({"message":"visit /help to get started"})


#help command
@app.route("/help", methods=["POST", "GET"])
def help():
    if request.method == "POST":
        data = request.form
        cid = data.get("channel_id")
        txt = data.get("text")
        response_url = data.get("response_url")
        help_msg = HelpMessage(cid, response_url, client, txt)
        thr = Thread(target=help_msg.go)
        try:
            thr.start()
        except:
            return requests.post(response_url,data=json.dumps({"text":"Fatal Error"})) 
        return Response(), 200
    else:
        _help = HelpMessage(None, None, None, request.args.get("command"))
        raw = {}
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_help.web)
                raw = future.result()
        except:
            return Response(), 500
        return Response(json.dumps(raw)), 200

#search news by keyword
@app.route("/search-news", methods=["POST", "GET"])
def keywordSearch():
    if request.method == "POST":
        data = request.form
        cid = data.get("channel_id")
        txt = data.get("text")
        response_url = data.get("response_url")
        if txt.strip() != "":
            payload = {"text":"please wait..."}
            requests.post(response_url,data=json.dumps(payload))
            news = ByKeyword(txt, cid, response_url, client)
            thr = Thread(target=news.go)
            try:
                thr.start()
            except:
                return requests.post(response_url,data=json.dumps({"text":"Fatal Error"})) 
        else:
            requests.post(response_url,data=json.dumps({"text":"search for a keyword"})) 
        return Response(), 200
    else:
        if request.args.get("keyword"):
            keyword = unquote(request.args.get("keyword"))
            news = ByKeyword(keyword, None, None, None)
            raw = {}
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(news.web)
                    raw = future.result()
            except:
                return Response(), 500
            if raw:
                data = raw.get("raw_res")
                return Response(json.dumps(data)), 200
            else:
                return Response(json.dumps({"Error":"No Results"})), 404
        else:
            return Response(json.dumps({"Error":"No keyword"})), 404


#random news
@app.route("/random-news", methods=["POST", "GET"])
def random_news():
    if request.method == "POST":
        data = request.form
        cid = data.get("channel_id")
        response_url = data.get("response_url")
        payload = {"text":"please wait (this operation can take a while)..."}
        requests.post(response_url,data=json.dumps(payload))
        news = RandomNews(cid, response_url, client)
        thr = Thread(target=news.go)
        try:
            thr.start()
        except:
            return requests.post(response_url,data=json.dumps({"text":"Fatal Error"})) 
        return Response(), 200
    else:
        news = RandomNews(None, None, None)
        #thr = Thread(target=news.web)
        raw = {}
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(news.web)
                raw = future.result()
        except:
            return Response(json.dumps({"Error":"An unexpected internal error occured"})), 500
        if raw:
            data = raw.get("raw_res")
            return Response(json.dumps(data)), 200
        else:
            return Response(json.dumps({"Error":"Maximum attempts reached"})), 504


#searches for news by url
@app.route("/search-url", methods=["POST", "GET"])
def urlSearch():
    if request.method == "POST":
        data = request.form
        cid = data.get("channel_id")
        input_url = data.get("text")
        response_url = data.get("response_url")
        if input_url.strip() != "":
            payload = {"text":"please wait..."}
            requests.post(response_url,data=json.dumps(payload))
            news = ByURL(input_url, cid, response_url, client)
            thr = Thread(target=news.go)
            try:
                thr.start()
            except:
                return requests.post(response_url,data=json.dumps({"text":"Fatal Error"})) 
        else:
            requests.post(response_url,data=json.dumps({"text":"please search for an url"})) 
        return Response(), 200
    else:
        if request.args.get("url"):
            _url = unquote(request.args.get("url"))
            news = ByURL(_url, None, None, None)
            raw = {}
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(news.web)
                    raw = future.result()
            except:
                return Response(), 500
            if raw:
                data = raw.get("raw_res")
                return Response(json.dumps(data)), 200
            else:
                return Response(json.dumps({"Error":"No Results"})), 404
        else:
            return Response(json.dumps({"Error":"No URL"})), 404

if __name__ == "__main__":
    app.run()
    