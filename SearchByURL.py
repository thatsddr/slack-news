from NewsMessage import NewsMessage
from bs4 import BeautifulSoup as bs
from urllib.parse import quote
import requests
import json

class ByURL(NewsMessage):
    def __init__(self, input_url, cid, response_url, client, thread=None):
        super().__init__()
        self.input_url = input_url
        self.url = ""
        self.cid = cid
        self.response_url = response_url
        self.client = client
        self.text = ""
        self.info = {}
        self.exclude = []
        self.thread = thread
    
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
        if self.input_url[0:8] != "https://" and self.input_url[0:7] != "http://":
            self.input_url = "https://"+self.input_url
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
            return requests.post(url=self.response_url,data=json.dumps({"text":f"No results for {self.input_url}"})) 
        
        if self.text != None and self.text != "":
            self.url = f"https://news.google.com/rss/search?q={quote(self.text)}&hl=en-US&gl=US&ceid=US:en"
            self.get_items()
            final = self.get_results(exclude=self.exclude)
            if final == None:
                return requests.post(url=self.response_url,data=json.dumps({"text":f"No results for {self.text}"})) 
            if final["len"] > 0:
                blocks = self.format()
                return self.client.chat_postMessage(channel=self.cid, blocks=blocks)
        else:
            return requests.post(url=self.response_url,data=json.dumps({"text":"Something went wrong..."}))

    def go_thread(self):
        self.url_info()
        if self.info.get("Error") == "Error":
            return self.client.chat_postMessage(channel=self.cid, thread_ts=self.thread, text="Error fetching the url")
        if self.text != None and self.text != "":
            self.url = f"https://news.google.com/rss/search?q={quote(self.text)}&hl=en-US&gl=US&ceid=US:en"
            self.get_items()
            final = self.get_results(exclude=self.exclude)
            if final == None:
                return self.client.chat_postMessage(channel=self.cid, thread_ts=self.thread, text="No matches in other sources")
            if final["len"] > 0:
                blocks = self.format()
                return self.client.chat_postMessage(channel=self.cid, thread_ts=self.thread, blocks=blocks)
        else:
            return self.client.chat_postMessage(channel=self.cid, thread_ts=self.thread, text="Something went wrong...",)

    def web(self):
        self.url_info()
        if self.info.get("Error") == "Error":
            return None
        if self.text != None and self.text != "":
            self.url = f"https://news.google.com/rss/search?q={quote(self.text)}&hl=en-US&gl=US&ceid=US:en"
            self.get_items()
            return self.get_results(exclude=self.exclude)
        else:
            return None
        
          