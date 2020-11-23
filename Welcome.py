class WelcomeMessage:
    START_TEXT = {
        "type": "section",
        "text" : {
            "type": "mrkdwn",
            "text":('Welcome to this channel! \n\n'
                    '*complete a task to get started*')
        }
    }
    DIVIDER = {"type": "divider"}
    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji= ":robot_face:"
        self.timestamp = ""
        self.completed = False

    def get_msg(self):
        return {"ts": self.timestamp, "channel": self.channel, "username": "News Welcome", "icon_emoji": self.icon_emoji, "blocks": [self.START_TEXT, self.DIVIDER, self._get_reaction_task()]}
    
    def _get_reaction_task(self):
        checkmark =":white_check_mark:"
        if not self.completed:
            checkmark = ':white_large_square:'
        
        text = f"{checkmark} *react to this message*"
        return {'type': "section", "text":{"type": "mrkdwn", "text": text}}
