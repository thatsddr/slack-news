from NewsMessage import NewsMessage
from urllib.parse import quote
import requests
import json
import random

class RandomNews(NewsMessage):
    def __init__(self, cid, response_url, client):
        super().__init__()
        self.url = "https://news.google.com/rss?oc=5&hl=en-US&gl=US&ceid=US:en"
        self.cid = cid
        self.response_url = response_url
        self.client = client
    
    def format(self):
        return [{
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f":mag: Here are some random news\n\n")
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

    def go(self):
        self.get_items()

        random_news = self.findings[random.randint(0,len(self.findings) - 1)]
        
        to_search = random_news["title"][0:random_news["title"].index("-")]
        self.url = f"https://news.google.com/rss/search?q={quote(to_search)}&hl=en-US&gl=US&ceid=US:en"

        self.get_items()
        final = self.get_results()

        if final == None:
            return requests.post(url=self.response_url,data=json.dumps({"text":"an error occured","username": "slack-news", "icon_emoji":":newspaper:"})) 

        if final["len"] > 0:
            blocks = self.format()
            return self.client.chat_postMessage(channel=self.cid, icon_emoji=":newspaper:", blocks=blocks, username="LATEST NEWS")
        
    def web(self):
        self.get_items()
        random_news = self.findings[random.randint(0,len(self.findings) - 1)]
        to_search = random_news["title"][0:random_news["title"].index("-")]
        self.url = f"https://news.google.com/rss/search?q={quote(to_search)}&hl=en-US&gl=US&ceid=US:en"
        self.get_items()
        return self.get_results()