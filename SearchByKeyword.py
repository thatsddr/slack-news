from NewsMessage import NewsMessage
from urllib.parse import quote
import requests
import json

#class that searches news by keyword
class ByKeyword(NewsMessage):
    def __init__(self, text, cid, response_url, client):
        super().__init__()
        self.text = text
        self.url = f"https://news.google.com/rss/search?q={quote(self.text)}&hl=en-US&gl=US&ceid=US:en"
        self.cid = cid
        self.response_url = response_url
        self.client = client
    
    #mathod that formats in markdown
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

    #this method calls format and send a slack message with the news found
    def go(self):
        self.get_items()
        final = self.get_results()
        if final == None:
            return requests.post(url=self.response_url,data=json.dumps({"text":"No results"})) 

        if final["len"] > 0:
            blocks = self.format()
            return self.client.chat_postMessage(channel=self.cid, blocks=blocks)
    
    #this method returns some json with the news found
    def web(self):
        self.get_items()
        return self.get_results()