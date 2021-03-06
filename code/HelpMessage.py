import json
import requests 
class HelpMessage:
    def __init__(self, cid, response_url, client, command=None):
        #initialize some basic values
        self.baseURL = "neutral-news.herokuapp.com"
        self.cid=cid
        self.response_url= response_url
        self.client = client
        self.possible_commands = {"help":{
                                        "description": ":black_nib: /help [command]\n\n:question: This command gives help on either one specified command or all of them if no command is specified.",
                                        "example":"/help\n/help search-news",
                                        "api_example":f"{self.baseURL}/help\n{self.baseURL}/help?command=search-news"},
                                "search-news":{
                                        "description":":black_nib: /search-news keyword(s)\n\n:question: This command will search for news related to the specified keyword(s) from all sides of the political spectrum. It will return an error if no keyword is specified.", 
                                        "example": "/search-news coronavirus vaccine\n/search-news Trump",
                                        "api_example": f"{self.baseURL}/search-news?keyword=coronavirus%20vaccine"}, 
                                "search-url":{
                                        "description":":black_nib: /search-url URL\n\n:question: This command will try to get the title of article related to the link you've specified. If the url is supported, this command will tell what kind of bias the source has and search for articles only from sources with a different bias.",
                                        "example": "/search-url https://edition.cnn.com/2020/11/28/politics/donald-trump-election-georgia-runoffs/index.html",
                                        "api_example": f"{self.baseURL}/search-url?url=https://edition.cnn.com/2020/11/28/politics/donald-trump-election-georgia-runoffs/index.html"}, 
                                "random-news": {
                                        "description":":black_nib: /random-news\n\n:question: This command finds a random news and searches for it among sources with different kinds of political bias.",
                                        "example":"/random-news",
                                        "api_example":f"{self.baseURL}/random-news"
                            }}
        self.command = command
        #if a command is specified, only consider the text, not the /
        if self.command:
            if len(self.command) > 0:
                self.command = self.command if self.command[0] != '/' else self.command[1:]
    
    def format(self):
        """this method just returns markdown, of either everything or just one, or returns an error if a non-existent command is specified
        """
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
                    "text":(f"Tips:\n1)You can react with :x: to delete messages sent by this bot.\n2)Slash commands are not supported in threads.\n3)You can mention this bot in a thread where the main post has one or more links in it to search them.")
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
                    "text":(f"Tips:\n1)You can react with :x: to delete messages sent by this bot.\n2)Slash commands are not supported in threads.\n3)You can mention this bot in a thread where the main post has one or more links in it to search them.")
                }}
                ]
        else:
            return requests.post(url=self.response_url,data=json.dumps({"text":f"No command named {self.command}"})) 

        return blocks

    def go(self):
        """this method calls format and send a slack message
        """
        blocks = self.format()
        if blocks == None:
            return None
        return self.client.chat_postMessage(channel=self.cid, blocks=blocks)
    
    def web(self):
        """this method returns some json of either one or all the commands
        """
        if self.command == None:
            return self.possible_commands
        elif self.possible_commands.get(self.command) != None:
            return self.possible_commands.get(self.command)
        else:
            return None