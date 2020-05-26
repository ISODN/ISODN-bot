# ISODN-bot
A discord bot for the International Science Olympiad Discord Network.

## Hosting
### System Requirements
 - Python 3.5.3+
 - A valid internet connection

### Installation
1. Download/fork the master github
2. Open terminal in the main directory and run `pip install -r requirements.txt`

### Setup
1. Bot token  
a. Sign in to Discord's [bot portal](https://discordapp.com/developers/applications/).  
b. Create a new application  
c. Add the bot under the "Bot" tab  
d. Copy the bot token and paste it in `config/token.txt`
2. Google API token ([tutorial](https://easyspeech2text.com/blog/use-google-api-json-credentials/))  
a. Create the secret json  
b. Rename it to `credentials.json` and move it to the `config` folder

### Running the discord bot
Open terminal in the main directory and run `python bot.py`. If you have both python 2 and python 3 installed, the command may be `python3 bot.py`.