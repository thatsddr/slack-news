import requests
from bs4 import BeautifulSoup as bs
import random
import json

#class wirh common properties for all the other news-related classes (not the help one)
class NewsMessage:
    def __init__(self):
        #initialize some basic variables
        self.findings = []
        self.links = ""
        self.main_title = ""
        self.results = {}
        self.url = ""
        self.bias_covered = []
        self.URLS = []
        #get the supported urls
        with open("urls.json", "r") as u:
            try:
                self.URLS = json.load(u)
                u.close()
            except Exception:
                raise (Exception)
        
    #this method returns a list of dictionaries with all the news
    def get_items(self):
        headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
        res = {}
        #try to rech the specified URL
        try:
            res = requests.get(url=self.url, headers=headers)
        except:
            return None

        #manipulate the response to only get what's needed and put it into an array
        soup = bs(res.content, "html.parser")
        self.findings = []
        for itm in soup.find_all("item"):
            obj = {}
            obj["title"] = itm.title.string
            obj["link"] = itm.link.next_sibling
            obj["source"] = itm.find_all("source")[0].get("url")
            self.findings.append(obj)
        
        #return the array
        return self.findings

    #this method filters the findings to only get relevant information
    def get_results(self, exclude = []):
        if self.findings == None:
            return None
        self.results = {}
        #if some kind of bias is to be excluded, exclude it
        self.bias_covered = exclude if len(exclude) > 0 else []

        #if the source is knows and the bias is not ocvered, add the article to the results
        for i in self.findings:
            if i["source"][8:] in self.URLS:
                bias = self.URLS[i["source"][8:]]["bias"]
                if bias not in self.bias_covered:
                    self.results[bias] = i
                    self.bias_covered.append(bias)
                #or if the bias is already covered, give a chance to replace the news so that the user doesn't always sees the same sources
                elif random.randint(1,15) == 1 and exclude == []:
                    self.results[bias] = i
            #if there are 3 biases, stop the loop
            if len(self.bias_covered) > 2:
                break
            
        #add links in markdown style
        if len(self.results) > 0:
            self.links = ""
            for k, v in self.results.items():
                source = v["source"][8:]
                name = self.URLS[source]["name"]
                link = v["link"]
                self.links += f"from the {k}: <{link}|{name}>\n"

            # get a random main title    
            ok = False
            while not ok:
                bias_type = self.bias_covered[random.randint(0, len(self.bias_covered)-1)]
                if self.results.get(bias_type):
                    self.main_title = self.results[bias_type]["title"]
                    ok = True
            
            #return the findings
            return {"links":self.links, "main_title":self.main_title, "len":len(self.results), "raw_res":self.results}
        else:
            return None