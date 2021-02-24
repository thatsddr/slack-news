from NewsMessage import NewsMessage
from urllib.parse import quote
import requests
import json

class ByKeyword(NewsMessage):
    """class that handles searches by keyword
    """
    def __init__(self, text, cid, response_url, client, cache=None):
        super().__init__()
        self.text = text
        self.url = f"https://news.google.com/rss/search?q={quote(self.text)}&hl=en-US&gl=US&ceid=US:en"
        self.cid = cid
        self.response_url = response_url
        self.client = client
        self.cache = cache
    
    def format(self):
        """method that formats in markdown
        """
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
        """this method calls format and send a slack message with the news found
        """
        self.get_items()
        final = self.get_results()
        #throw an error if there are no results
        if final == None:
            return requests.post(url=self.response_url,data=json.dumps({"text":"No results"})) 
        #cahce and return value if there are results
        if final["len"] > 0:
            blocks = self.format()
            #set cache
            if self.cache:
                self.cache.set("markdown-"+self.text, json.dumps(blocks), 3600)
            #post result
            return self.client.chat_postMessage(channel=self.cid, blocks=blocks)
    
    def web(self):
        """this method returns some json with the news found
        """
        self.get_items()
        return self.get_results()