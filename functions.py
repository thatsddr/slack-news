import re

#function to check if a string contains a URL
def check_url(string):    
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)       
    return [x[0] for x in url]

#clean urls of markdown sintax
def clean_urls(raw_urls):
    urls = []
    for url in raw_urls:
        index = None
        try:
            index = url.index("|")
        except:
            index = None
        if index!=None:
            temp = url[:index]
            if temp not in urls:
                urls.append(temp)
        else:
            if url not in urls:
                urls.append(url)
    return urls