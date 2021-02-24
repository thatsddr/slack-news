# Neutral News
Neutral News is a slack app and a API that searches the web for the same news by sources with different political biases (accoridng to the [Media Bias Chart](https://www.adfontesmedia.com/static-mbc/)) and returns one article for each kind of bias (left, center, and right).

>This app is not published as an API nor a slack app. However, if you have a token or know how to obtain one, the app is running at this link: neutral-news.herokuapp.com.

## Installation

If you want to install this app locally, these are the steps you need to foolow:

Prerequisites: python3.8 (probably works with python3.9 as well) and pip3.

1. Download the app and install the requirements with these commands:
   ```
   gh repo clone thatsddr/slack-news
   cd slack-news
   pip3 install -r requirements.txt
   ```  
2. Create a .env in the root directory file with a ```REDIS_URL``` variable or at line 39 in main.py create a local redis instance (the code should look like this: ```r = redis.Redis(host='localhost', port=6379, db=0)```)
3.
   * If you want to use the app in slack, make sure to be the admin of the workspace you want to install the app in, then go to https://api.slack.com, and configure a new app (if you don't know how to do it, you can start at https://api.slack.com/authentication/basics). After configuring the app, go to the .env file and add these 2 variables with the variables retrieved from the configuration: ```SLACK_TOKEN``` and ```SIGNING_SECRET```
   * If you want to use the app as an API you have 2 options: 
      1. If you don't want to use AUTH0 remove every line that contains ```@requires_auth``` in the main.py file, the functions that will not be used anymore, and the Auth.py file.
      2. Otherwise, if you want to use AUTH0, configure a new app on https://manage.auth0.com and then change the values of ```AUTH0_DOMAIN``` and ```API_AUDIENCE``` with those of your application at lines 42 and 43 in the main.py file.
4. run ```python3 code/main.py``` to start a development server.

## Usage

### Slack

Once the app is installed in the workspace, you can use the /help command to get a list of all the possible commands and how to use them.

### API

The API has the following endpoints:

* neutral-news.herokuapp.com/api/identifier

Used as AUTH0 API Audience, can also be used to check if a token is valid. Returns 200 or an authentication error.

* neutral-news.herokuapp.com/api/random
* neutral-news.herokuapp.com/api/search-keyword?keyword=YOUR-KEYWORD(S)-HERE
* neutral-news.herokuapp.com/api/search-url?url=YOUR-URL-HERE

These 3 methods accept GET requests and require the following header: ```Authorization: Bearer YOUR-VALID-TOKEN-HERE```.
If the token is valid they return data in the following format:
```
{
  "left":{"title":TITLE, "link":LINK, "source":SOURCE},
  "center":{"title":TITLE, "link":LINK, "source":SOURCE},
  "right":{"title":TITLE, "link":LINK, "source":SOURCE}
 }
```
or ```{"Error":ERROR-MESSAGE}```.

