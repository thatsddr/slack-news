import json
import requests 
class HelpMessage:
    def __init__(self, cid, response_url, client, command=None):
        self.cid=cid
        self.response_url= response_url
        self.client = client
        self.possible_commands = {"help":{
                                        "description": ":black_nib: /help [command]\n\n:question: This command gives help on either one specified command or all of them if no command is specified.",
                                        "example":"/help\n/help search-news"},
                                "search-news":{
                                        "description":":black_nib: /search-news keyword(s)\n\n:question: This command will search for news related to the specified keyword(s) from all sides of the political spectrum. It will return an error if no keyword is specified.", 
                                        "example": "/search-news coronavirus vaccine\n/search-news Trump"}, 
                                "search-url":{
                                        "description":":black_nib: /search-url URL\n\n:question: This command will try to get the title of article related to the link you've specified. If the url is supported, this command will tell what kind of bias the source has and search for articles only from sources with a different bias.",
                                        "example": "/search-url https://edition.cnn.com/2020/11/28/politics/donald-trump-election-georgia-runoffs/index.html"
                                    }, 
                                "random-news": {
                                        "description":":black_nib: /random-news\n\n:question: This command finds a random news and searches for it among sources with different kinds of political bias.",
                                        "example":"/random-news"
                            }}
        self.command = command
        if len(self.command) > 0:
            self.command = self.command if self.command[0] != '/' else self.command[1:]
    
    def format(self):
        blocks = []
        if self.command == "":
            blocks.append({"type": "section",
                "text" : {
                    "type": "mrkdwn",
                    "text":(f":rocket:Here is some help about all the commands\n\n")
                }})
            for k,v in self.possible_commands.items():
                blocks.append({"type":"divider"})
                blocks.append({"type": "section",
                    "text" : {
                        "type": "mrkdwn",
                        "text":(f"{v['description']}\n\n:white_check_mark: Examples:\n{v['example']}\n\n")
                    }})
            blocks.append({"type":"divider"})
            blocks.append({"type": "section",
                "text" : {
                    "type": "mrkdwn",
                    "text":(f"Tip: you can react with :x: to delete messages sent by this bot.")
                }})
        elif self.possible_commands.get(self.command) != None:
            blocks = [{"type": "section",
                    "text" : {
                        "type": "mrkdwn",
                        "text":(f":rocket:Here is some help about {self.command}\n\n")
                    }
                }, 
                {"type":"divider"},
                {"type": "section",
                    "text" : {
                        "type": "mrkdwn",
                        "text":(f"{self.possible_commands[self.command]['description']}\n\n:white_check_mark: Examples:\n{self.possible_commands[self.command]['example']}\n\n")
                    }
                },
                {"type":"divider"},
                {"type": "section",
                "text" : {
                    "type": "mrkdwn",
                    "text":(f"Tip: you can react with :x: to delete messages sent by this bot.")
                }}
                ]
        else:
            return requests.post(url=self.response_url,data=json.dumps({"text":f"No command named {self.command}","username": "slack-news", "icon_emoji":":newspaper:"})) 

        return blocks

    def go(self):
        blocks = self.format()
        if blocks == None:
            return None
        return self.client.chat_postMessage(channel=self.cid, icon_emoji=":newspaper:", blocks=blocks, username="LATEST NEWS")