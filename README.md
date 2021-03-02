# mediabot

Mediabot is a bot that can, you probably guessed it, do stuff with media in Discord. The prefix is `|`, and most of the commands work by just specifying a message ID after the command. Message IDs can be obtained by enabling "Developer Mode" in the Discord appearance settings. You then can right click (hold down on mobile) on any message and click "Copy ID" to copy the message ID.

### Features

- Play audio files sent by users
- Join a user's voice channel and speak text that is in an image
- Join a user's voice channel and speak text that is in a PDF
- Speak text from messages or as an argument

### Use this bot
Currently, I'm not hosting this bot anywhere, so you'll have to run it yourself. You are, however, free to run it on your own computer or server. I am not sure if it works on Windows, and if it did it would probably be insanely difficult to get running, so I'd recommend running this on Linux. After you clone this repository with `git clone https://github.com/TabulateJarl8/mediabot.git`, cd into the `mediabot` directory. Here you need to install the requirements, so just type `pip3 install -r requirements.txt`. After this is done you will need to install Tesseract. This isn't required if you're not planning on using the PDF feature. On Ubuntu this can be installed with `sudo apt install tesseract-ocr`, and on Arch distros this can be installed with `sudo pacman -S tesseract`. After you install the dependencies, you will need to go to the [Discord developer portal](https://discord.com/developers/applications) and create a new application. Once created, go to the "bot" tab and make that application a bot. Now you're going to want to go to the "General information" tab. Copy your client ID and replace the placeholder in this invite URL with that id: `https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID_HERE&permissions=3214336&scope=bot`. After doing that, you should be able to paste that link into your browser to invite the bot to your server.