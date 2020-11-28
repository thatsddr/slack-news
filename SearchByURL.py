from NewsMessage import NewsMessage
from bs4 import BeautifulSoup as bs
from urllib.parse import quote
import requests
import json

class ByURL(NewsMessage):
    def __init__(self, input_url, cid, response_url, client):
        super().__init__()
        self.input_url = input_url
        self.url = ""
        self.cid = cid
        self.response_url = response_url
        self.client = client
        self.text = ""
        self.info = {}
        self.exclude = []
    
    def format(self):
        return [{
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f":mag: Here is what other sources say about <{self.url}|{self.text}> (bias: {self.info.get('bias')})\n\n")
            }
        },
        {"type": "divider"},
            {
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f"{self.main_title}\n")
                }
        },
        {"type": "divider"},
            {
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f"\n\n{self.links}")
            }
        }]
    
    def url_info(self):
        headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
        res = {}
        try:
            res = requests.get(url=self.input_url, headers=headers)
        except:
            self.info = {"Error": "Error"}
            return self.info

        soup = bs(res.content, "html.parser")
        self.text = soup.find_all("h1")[0].get_text()

        if self.text == "" or self.text == None:
            self.info = {"Error": "Error"}
            return self.info

        self.info = {"supported": False, "text":self.text}

        baseURL = self.input_url[self.input_url.index("//")+2:]
        toSearch = ""
        try:
            toSearch = baseURL[0:baseURL.index("/")]
        except:
            toSearch = baseURL

        supportedUrl = self.URLS.get(toSearch)
        if supportedUrl != None:
            self.info["supported"] = True
            self.info["name"] = supportedUrl["name"]
            self.info["bias"] = supportedUrl["bias"]
            self.exclude.append(self.info["bias"])
        
        if self.info["supported"] == False:
            self.info["name"] = "unknown"
            self.info["bias"] = "unknown, unsupported source"

    def go(self):
        self.url_info()
        if self.info.get("Error") == "Error":
            return requests.post(url=self.response_url,data=json.dumps({"text":f"No results for {self.input_url}","username": "slack-news", "icon_emoji":":newspaper:"})) 
        
        if self.text != None and self.text != "":
            self.url = f"https://news.google.com/rss/search?q={quote(self.text)}&hl=en-US&gl=US&ceid=US:en"
            self.get_items()
            final = self.get_results(exclude=self.exclude)
            if final == None:
                return requests.post(url=self.response_url,data=json.dumps({"text":f"No results for {self.text}","username": "slack-news", "icon_emoji":":newspaper:"})) 
            if final["len"] > 0:
                blocks = self.format()
                return self.client.chat_postMessage(channel=self.cid, icon_emoji=":newspaper:", blocks=blocks, username="LATEST NEWS")
        else:
            return requests.post(url=self.response_url,data=json.dumps({"text":"Something went wrong...","username": "slack-news", "icon_emoji":":newspaper:"})) 
          