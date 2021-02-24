import slack
import os
import re
import json
import requests
import concurrent.futures
import redis
from six.moves.urllib.request import urlopen
from functools import wraps
from jose import jwt
from urllib.parse import unquote
from slackeventsapi import SlackEventAdapter
from threading import Thread
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, _request_ctx_stack
from flask_cors import CORS, cross_origin
from SearchByKeyword import ByKeyword
from SearchRandomNews import RandomNews
from SearchByURL import ByURL
from HelpMessage import HelpMessage
from functions import check_url, clean_urls
from Auth import get_token_auth_header

# dotenv configuration
env_path = Path("./") / ".env"
load_dotenv(dotenv_path=env_path)

# flask initialization and slack api implementation
app = Flask(__name__)
CORS(app)
slack_event_adapter = SlackEventAdapter(
    os.environ["SIGNING_SECRET"], "/slack/events", app
)
client = slack.WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]

# cache initialization
r = redis.from_url(os.environ.get("REDIS_URL"))

#auth0 error handling. Standard code required by auth0 in python.
AUTH0_DOMAIN = 'ddr.eu.auth0.com'
API_AUDIENCE = "https://neutral-news.herokuapp.com/api/identifier"
ALGORITHMS = ["RS256"]
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
def requires_auth(f):
    """Determines if the Access Token is valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header(AuthError)
        jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer="https://"+AUTH0_DOMAIN+"/"
                )
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired",
                                "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims",
                                "description":
                                    "incorrect claims,"
                                    "please check the audience and issuer"}, 401)
            except Exception:
                raise AuthError({"code": "invalid_header",
                                "description":
                                    "Unable to parse authentication"
                                    " token."}, 401)

            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                        "description": "Unable to find appropriate key"}, 401)
    return decorated

#auth0 token validation
def requires_scope(required_scope):
    token = get_token_auth_header(AuthError)
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
            token_scopes = unverified_claims["scope"].split()
            for token_scope in token_scopes:
                if token_scope == required_scope:
                    return True
    return False

# slack-specific events:

@slack_event_adapter.on("message")
def message(payload):
    """check if the bot is mentioned in a thread every time a message is posted
    """
    # get basic information
    event = payload.get("event", {})
    text = event.get("text", {})
    cid = event.get("channel")
    thread_ts = event.get("thread_ts", None)
    # check if the bot is mentioned in a thread
    if BOT_ID in text and thread_ts:
        # if yes, get the original message and try to get URL(s) out of it
        res = client.conversations_history(
            channel=cid, latest=thread_ts, inclusive=True, limit=1
        )
        message_str = res.get("messages", [{}])[0].get("text", None)
        raw_urls = check_url(message_str)
        urls = []
        # if there are URLSs, clean the link from the markdown stuff
        if raw_urls:
            urls = clean_urls(raw_urls)
            #check if some of the urls are cached
            for url in urls:
                if (r.get("markdown-"+url)):
                    client.chat_postMessage(channel=cid, thread_ts=thread_ts, blocks=r.get("markdown-"+url))
                    #remove the url so that it w
                    urls.remove(url)

            # for each of the clean URLs, search news by URL
            for url in urls:
                news = ByURL(url, cid, None, client, thread=thread_ts, cache=r)
                thr = Thread(target=news.go_thread)
                try:
                    thr.start()
                except:
                    return client.chat_postMessage(
                        channel=cid, thread_ts=thread_ts, text="Something went wrong..."
                    )
        else:
            return client.chat_postMessage(
                channel=cid, thread_ts=thread_ts, text="No URL detected"
            )

@slack_event_adapter.on("reaction_added")
def check_reaction(payload):
    """reaction handler that deletes a message if it was sent from the bot and the user reacts with :x:
    """
    # get basic info
    event = payload.get("event", {})
    channel_id = event.get("item", {}).get("channel")
    # if the reaction is :x:, delete the message
    if payload["event"]["reaction"] == "x":
        try:
            client.chat_delete(channel=channel_id, ts=payload["event"]["item"]["ts"])
        except:
            pass

# slack slash commands:

@app.route("/test", methods=["POST"])
def test():
    """test command to check if the bot is installed in a channel
    """
    # get basic info
    data = request.form
    cid = data.get("channel_id")
    cname = data.get("channel_name")
    # send message
    client.chat_postMessage(
        channel=cid, text=f"This app is working properly in #{cname}"
    )
    return Response(), 200

# 
@app.route("/help", methods=["POST"])
def help():
    """help command, returns a list of available commands.
    """
    # Send slack response if the method is POST or return some json if the method is GET
    # get basic info
    data = request.form
    cid = data.get("channel_id")
    txt = data.get("text")
    response_url = data.get("response_url")
    # initialize class
    help_msg = HelpMessage(cid, response_url, client, txt)
    thr = Thread(target=help_msg.go)
    try:
        # try to send the message
        thr.start()
    except:
        return requests.post(response_url, data=json.dumps({"text": "Fatal Error"}))
    return Response(), 200

@app.route("/search-news", methods=["POST"])
def keywordSearch():
    """search news by keyword
    """
    # Send slack response if the method is POST or return some json if the method is GET
    # get basic data
    data = request.form
    cid = data.get("channel_id")
    txt = data.get("text")
    response_url = data.get("response_url")
    # if there is a keyword, search for it
    if txt.strip() != "":
        # tell the user he'll get his news
        payload = {"text": "please wait..."}
        requests.post(response_url, data=json.dumps(payload))
        #chck if the news is cached and if yes return it
        if r.get("markdown-"+txt):
            return client.chat_postMessage(channel=cid, blocks=r.get("markdown-"+txt))
        # initialize the class
        news = ByKeyword(txt, cid, response_url, client, cache=r)
        thr = Thread(target=news.go)
        # try to execute the code, if it fails return an error
        try:
            thr.start()
        except:
            return requests.post(response_url, data=json.dumps({"text": "Fatal Error"}))
    else:
        requests.post(response_url, data=json.dumps({"text": "search for a keyword"}))
    return Response(), 200

@app.route("/random-news", methods=["POST"])
def random_news():
    """returns random news
    """
    # Send slack response if the method is POST or return some json if the method is GET
    # get basic info
    data = request.form
    cid = data.get("channel_id")
    response_url = data.get("response_url")
    # tell the user he'll get his response
    payload = {"text": "please wait (this operation can take a while)..."}
    requests.post(response_url, data=json.dumps(payload))
    # initialize the class
    news = RandomNews(cid, response_url, client)
    thr = Thread(target=news.go)
    # try to respond
    try:
        thr.start()
    except:
        return requests.post(response_url, data=json.dumps({"text": "Fatal Error"}))
    return Response(), 200

@app.route("/search-url", methods=["POST"])
def urlSearch():
    """searches for news by url
    """
    # Send slack response if the method is POST or return some json if the method is GET
    # get basic info
    data = request.form
    cid = data.get("channel_id")
    input_url = data.get("text")
    response_url = data.get("response_url")
    # i f the url is specifies proceed
    if input_url.strip() != "":
        # tell the suer he'll get his response
        payload = {"text": "please wait..."}
        requests.post(response_url, data=json.dumps(payload))
        #check if the news is cached and if yes return it
        if r.get("markdown-"+input_url):
            return client.chat_postMessage(channel=cid, blocks=r.get("markdown-"+input_url))
        # initialize the class
        news = ByURL(input_url, cid, response_url, client, cache=r)
        thr = Thread(target=news.go)
        # try to respond
        try:
            thr.start()
        except:
            return requests.post(response_url, data=json.dumps({"text": "Fatal Error"}))
    else:
        requests.post(
            response_url, data=json.dumps({"text": "please search for an url"})
        )
    return Response(), 200

#API

@app.route("/api/identifier")
def identifier():
    """auth0 identifier
    """
    return Response(), 200

@app.route("/api/search-keyword", methods=["GET"])
@cross_origin(headers=["Content-Type", "Authorization"])
@requires_auth
def apiKeyword():
    """search by keyword from  web API
    """
    # in order to return some json, check if there is a keyword
    if request.args.get("keyword"):
        keyword = unquote(request.args.get("keyword"))
        # if the result is cached, return it
        if r.get(keyword):
            return Response(r.get(keyword)), 200
        # initialize the class
        news = ByKeyword(keyword, None, None, None)
        raw = {}
        # try to get a response...
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(news.web)
                raw = future.result()
        except:
            return Response(), 500
        # ...and return only the part of data not formatted for slack
        if raw:
            # get the data
            data = raw.get("raw_res")
            # cache the result
            r.set(keyword, json.dumps(data), 3600)
            # return the result
            return Response(json.dumps(data)), 200
        else:
            return Response(json.dumps({"Error": "No Results"})), 404
    else:
        return Response(json.dumps({"Error": "No keyword"})), 404

@app.route("/api/random", methods=["GET"])
@cross_origin(headers=["Content-Type", "Authorization"])
@requires_auth
def apiRandom():
    """random news from web API
    """
    # initialize the class for the API
    news = RandomNews(None, None, None)
    raw = {}
    # try to get data
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futureRes = executor.submit(news.web)
            raw = futureRes.result()
    except:
        return (
            Response(json.dumps({"Error": "An unexpected internal error occured"})),
            500,
        )
    # return only the non markdown data
    if raw:
        data = raw.get("raw_res")
        return Response(json.dumps(data)), 200
    else:
        return Response(json.dumps({"Error": "Maximum attempts reached"})), 504

@app.route("/api/search-url", methods=["GET"])
@cross_origin(headers=["Content-Type", "Authorization"])
@requires_auth
def apiURL():
    """search by URL from web API
    """
    # in order to return some json, check if there is a specified URL
    if request.args.get("url"):
        _url = unquote(request.args.get("url"))
        # if the result is cached, return it
        if r.get(_url):
            return Response(r.get(_url)), 200
        # initialize the class
        news = ByURL(_url, None, None, None)
        raw = {}
        # try to fetch some data
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(news.web)
                raw = future.result()
        except:
            return Response(), 500
        # if there is data only return the non formatted data
        if raw:
            data = raw.get("raw_res")
            # cache the result
            r.set(_url, json.dumps(data), 3600)
            # return the result
            return Response(json.dumps(data)), 200
        else:
            return Response(json.dumps({"Error": "No Results"})), 404
    else:
        return Response(json.dumps({"Error": "No URL"})), 404


if __name__ == "__main__":
    app.run()
