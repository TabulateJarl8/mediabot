from discord.ext import commands
import psutil
import os
import logging
import datetime
import requests
from urllib.parse import urlparse
import discord
import audioread
import time

class InvalidAudioFormatError(commands.CommandError):
	def __init__(self, filename, *args, **kwargs):
		self.filename = filename
		super().__init__(*args, **kwargs)

class NotInChannelError(commands.CommandError):
	def __init__(self, id, *args, **kwargs):
		self.mention = "<@" + str(id) + ">"
		super().__init__(*args, **kwargs)

class NoAttachmentError(commands.CommandError):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

startupTime = datetime.datetime.utcnow()
workingDir = os.path.abspath(os.path.dirname(__file__))

bot = commands.Bot(command_prefix="|")

def restart_program():
	os.chdir(workingDir)
	print("Restart")
	"""Restarts the current program, with file objects and descriptors
	cleanup
	"""
	try:
		p = psutil.Process(os.getpid())
		for handler in p.open_files() + p.connections():
			os.close(handler.fd)
	except Exception as e:
		logging.error(e)

@bot.event
async def on_ready():
	print("Connected")

@bot.command(pass_context=True, brief="Status", description="Get the bot status")
async def status(ctx):
	answer = "Bot: Online :green_circle:\n"
	messageTime = ctx.message.created_at
	currentTime = datetime.datetime.utcnow()
	latency = currentTime - messageTime
	answer += "Latency: " + str(latency)
	if latency.total_seconds() < 1:
		answer += " :green_circle:\n"
	elif latency.total_seconds() < 5:
		answer += " :yellow_circle:\n"
	else:
		answer += " :red_circle:\n"
	answer += "Last startup: " + str(startupTime) + "\n"
	answer += "Uptime: " + str(currentTime - startupTime) + "\n"
	await ctx.send(answer)

async def playAudioFile(ctx, channel, filename):
	# Gets voice channel of message author
	vc = await channel.connect()
	vc.play(discord.FFmpegPCMAudio(source=filename))
	# Sleep while audio is playing.
	while vc.is_playing():
		with audioread.audio_open(filename) as f:
			time.sleep(f.duration)
		await vc.disconnect()
	# Delete command after the audio is done playing.
	# await ctx.message.delete()

@bot.command(pass_context=True, brief="Play audio file", description="Join your current voice channel and play the audio file")
async def play(ctx, message_id: str, index_of_attachment=0):
	try:
		channel = ctx.author.voice.channel
	except Exception:
		raise NotInChannelError(ctx.author.id)
	msg = await ctx.fetch_message(message_id.split("-")[-1])
	if msg.attachments:
		if len(msg.attachments) >= index_of_attachment + 1:
			url = msg.attachments[index_of_attachment].url
			content_type = requests.head(url).headers['Content-Type']
			if not 'audio' in content_type:
				raise InvalidAudioFormatError(os.path.basename(urlparse(url).path))
			else:
				await ctx.send("Downloading `" + os.path.basename(urlparse(url).path) + "`...")
				# Valid audio file, download and play it
				try:
					file = requests.get(url, allow_redirects=True).content
					with open(os.path.basename(urlparse(url).path), 'wb') as f:
						f.write(file)
					await playAudioFile(ctx, channel, os.path.basename(urlparse(url).path))
				finally:
					if os.path.isfile(os.path.basename(urlparse(url).path)):
						os.remove(os.path.basename(urlparse(url).path))
		else:
			raise NoAttachmentError
	else:
		raise NoAttachmentError

@play.error
async def play_error(ctx, error):
	if isinstance(error, InvalidAudioFormatError):
		await ctx.send("`" + error.filename + "` is not a valid audio file")
	elif isinstance(error, NoAttachmentError):
		await ctx.send("No attachment for specified message")
	elif isinstance(error, NotInChannelError):
		await ctx.send(error.mention + " is not currently in a voice channel")
	else:
		await ctx.send(str(type(error).__name__) + ": " + str(error))

with open(os.path.join(workingDir, "secure", "client_secret.txt")) as f:
	secret = f.read().rstrip()
bot.run(secret)
del secret