from NewsMessage import NewsMessage
from urllib.parse import quote
import requests
import json
import random

class RandomNews(NewsMessage):
    """class to handle random news searches
    """
    def __init__(self, cid, response_url, client):
        super().__init__()
        self.url = "https://news.google.com/rss?oc=5&hl=en-US&gl=US&ceid=US:en"
        self.cid = cid
        self.response_url = response_url
        self.client = client
    
    def format(self):
        """method that formats the data
        """
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

    def get_data(self):
        """get a random title and search for it
        """
        self.get_items()
        random_news = self.findings[random.randint(0,len(self.findings) - 1)]
        to_search = random_news["title"][0:random_news["title"].index("-")]
        self.url = f"https://news.google.com/rss/search?q={quote(to_search)}&hl=en-US&gl=US&ceid=US:en"
        self.get_items()
        return self.get_results()
    
    def is_enough(self, data):
        """method that checks if there are less than 2 sources
        """
        if data == None:
                return False
        if len(data["raw_res"]) < 2:
            return False
        return True

    def go(self):
        """returns a slack message after getting and formatting the date
        """
        final = self.get_data()
        attempts = 0
        while not self.is_enough(final) and attempts<=15:
            final = self.get_data()
            attempts += 1
        if attempts>15:
            return requests.post(self.response_url,data=json.dumps({"text":"Maximum attempts"})) 
        if final != None:
            blocks = self.format()
            return self.client.chat_postMessage(channel=self.cid, blocks=blocks)

    def web(self):
        """returns some json after getting the data
        """
        final = self.get_data()
        attempts = 0
        while not self.is_enough(final) and attempts<=9:
            final = self.get_data()
            attempts += 1
        if attempts>9:
            return None
        return final