import requests
from bs4 import BeautifulSoup as bs
from urls import URLS
import random

class NewsMessage:
    def __init__(self):
        self.findings = []
        self.links = ""
        self.main_title = ""
        self.results = ""
        self.url = ""


    def get_items(self):
        headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
        res = {}
        try:
            res = requests.get(url=self.url, headers=headers)
        except:
            return None

        soup = bs(res.content, "html.parser")

        self.findings = []
        for itm in soup.find_all("item"):
            obj = {}
            obj["title"] = itm.title.string
            obj["link"] = itm.link.next_sibling
            obj["source"] = itm.find_all("source")[0].get("url")
            self.findings.append(obj)

        return self.findings

    def get_results(self):
        if self.findings == None:
            return None
        self.results = {}
        bias_covered = []
        for i in self.findings:
            if i["source"][8:] in URLS:
                bias = URLS[i["source"][8:]]["bias"]
                if bias not in bias_covered:
                    self.results[bias] = i
                    bias_covered.append(bias)
                elif random.randint(1,15) == 1:
                    self.results[bias] = i
            if len(bias_covered) > 2:
                break

        if len(bias_covered) > 0:
            self.links = ""
            for k, v in self.results.items():
                source = v["source"][8:]
                name = URLS[source]["name"]
                link = v["link"]
                self.links += f"from the {k}: <{link}|{name}>\n"

            bias_type = bias_covered[random.randint(0, len(bias_covered)-1)]
            self.main_title = self.results[bias_type]["title"]

            return {"links":self.links, "main_title":self.main_title, "len":len(self.results)}
        else:
            return None
        
    def url_info(self, url):
        headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
        res = {}
        try:
            res = requests.get(url=url, headers=headers)
        except:
            return None

        soup = bs(res.content, "html.parser")
        self.main_title = soup.find_all("h1").string