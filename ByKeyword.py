from NewsMessage import NewsMessage
from urllib.parse import quote
import requests
import json

class ByKeyword(NewsMessage):
    def __init__(self, text, cid, response_url, client):
        super().__init__()
        self.text = text
        self.url = f"https://news.google.com/rss/search?q={quote(self.text)}&hl=en-US&gl=US&ceid=US:en"
        self.cid = cid
        self.response_url = response_url
        self.client = client
    
    def format(self):
        return [{
            "type": "section",
            "text" : {
                "type": "mrkdwn",
                "text":(f":mag: Here is what I've found about '{self.text}'\n\n")
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
        final = self.get_results()
        if final == None:
            return requests.post(url=self.response_url,data=json.dumps({"text":"an error occured","username": "slack-news", "icon_emoji":":newspaper:"})) 

        if final["len"] > 0:
            blocks = self.format()
            return self.client.chat_postMessage(channel=self.cid, icon_emoji=":newspaper:", blocks=blocks, username="LATEST NEWS")
        else:
            requests.post(url=self.response_url,data=json.dumps({"text":"no sources in our database","username": "slack-news", "icon_emoji":":newspaper:"})) 
