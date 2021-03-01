from discord.ext import commands
import psutil
import os
import logging
import datetime

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

@bot.command(pass_context=True, brief="Play audio file", description="Join your current voice channel and play the audio file")
async def play(ctx, message_id: int):
	msg = await ctx.fetch_message(message_id)

	channel = ctx.author.voice.channel
	await channel.connect()

with open(os.path.join(workingDir, "secure", "client_secret.txt")) as f:
	secret = f.read().rstrip()
bot.run(secret)
del secret