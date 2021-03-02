from discord.ext import commands
import psutil
import os
import logging
import datetime
import requests
from urllib.parse import urlparse
import discord
import mutagen
import time
import fitz
from gtts import gTTS
import shutil
import cv2
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import numpy
import traceback
import shlex
import tempfile

startupTime = datetime.datetime.utcnow()
workingDir = os.path.abspath(os.path.dirname(__file__))

bot = commands.Bot(command_prefix="|")

class InvalidAudioFormatError(commands.CommandError):
	def __init__(self, filename, *args, **kwargs):
		self.filename = filename
		super().__init__(*args, **kwargs)

class InvalidPDFFormatError(commands.CommandError):
	def __init__(self, filename, *args, **kwargs):
		self.filename = filename
		super().__init__(*args, **kwargs)

class InvalidImageFormatError(commands.CommandError):
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

class MessageNotFoundError(commands.CommandError):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class NoTextFoundError(commands.CommandError):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

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

# Utility Functions

async def playAudioFile(ctx, channel, filename):
	# Gets voice channel of message author
	vc = await channel.connect()
	vc.play(discord.FFmpegPCMAudio(source=filename))
	# Sleep while audio is playing.
	while vc.is_playing():
		audiofile = mutagen.File(filename)
		time.sleep(audiofile.info.length + 3)
		await vc.disconnect()
	# Delete command after the audio is done playing.
	# await ctx.message.delete()

def getTextFromImageObject(image):
	# Convert to CV2 format
	image = image.convert("RGB")
	image = numpy.array(image)
	image = image[:, :, ::-1].copy()
	# gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	# blur = cv2.GaussianBlur(gray, (3, 3), 0)
	# thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

	# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
	# opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
	# invert = 255 - opening
	data = pytesseract.image_to_string(image, lang='eng')
	return data


def getTextFromPDF(path, ocr):
	if ocr == True:
		text = ""
		doc = convert_from_path(path)
		for page_number, page_data in enumerate(doc):
			text += getTextFromImageObject(page_data)
	else:
		text = ""
		doc = fitz.open(path)
		for page in doc:
			text += page.getText()
		if text == "":
			doc = convert_from_path(path)
			for page_number, page_data in enumerate(doc):
				text += getTextFromImageObject(Image.fromarray(page_data))
	return text

# End Utility Functions

# Core bot commands

@bot.command(pass_context=True, brief="Play audio file", description="Join your current voice channel and play the specified audio file")
async def play(ctx, message_id: str, index_of_attachment=0):
	try:
		channel = ctx.author.voice.channel
	except Exception:
		raise NotInChannelError(ctx.author.id)
	try:
		msg = message_id.split("-")
		if len(msg) >= 2:
			try:
				message_channel = bot.get_channel(int(msg[0]))
				msg = await message_channel.fetch_message(int(msg[-1]))
			except Exception:
				msg = await ctx.fetch_message(int(msg[-1]))
		else:
			msg = await ctx.fetch_message(int(msg[-1]))
	except Exception:
		raise MessageNotFoundError
	if msg.attachments:
		if len(msg.attachments) >= index_of_attachment + 1:
			url = msg.attachments[index_of_attachment].url
			content_type = requests.head(url).headers['Content-Type']
			if not 'audio' in content_type:
				raise InvalidAudioFormatError(os.path.basename(urlparse(url).path))
			else:
				with tempfile.NamedTemporaryFile(suffix=os.path.splitext(os.path.basename(urlparse(url).path))[1]) as f:
					await ctx.send("Downloading `" + os.path.basename(urlparse(url).path) + "`...")
					# Valid audio file, download and play it
					file = requests.get(url, allow_redirects=True).content
					f.write(file)
					f.seek(0)
					await playAudioFile(ctx, channel, f.name)
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
	elif isinstance(error, MessageNotFoundError):
		await ctx.send("Message not found")
	else:
		traceback.print_exc()
		await ctx.send(str(type(error).__name__) + ": " + str(error))

@bot.command(pass_context=True, brief="PDF TTS", description="Join your current voice channel and read the text found in the specified PDF aloud")
async def speakPDF(ctx, message_id: str, forceOCR=False, language='en', tld='com', index_of_attachment=0):
	try:
		channel = ctx.author.voice.channel
	except Exception:
		raise NotInChannelError(ctx.author.id)
	try:
		msg = message_id.split("-")
		if len(msg) >= 2:
			try:
				message_channel = bot.get_channel(int(msg[0]))
				msg = await message_channel.fetch_message(int(msg[-1]))
			except Exception:
				msg = await ctx.fetch_message(int(msg[-1]))
		else:
			msg = await ctx.fetch_message(int(msg[-1]))
	except Exception:
		raise MessageNotFoundError
	if msg.attachments:
		if len(msg.attachments) >= index_of_attachment + 1:
			url = msg.attachments[index_of_attachment].url
			content_type = requests.head(url).headers['Content-Type']
			if content_type != 'application/pdf':
				raise InvalidPDFFormatError(os.path.basename(urlparse(url).path))
			else:
				with tempfile.NamedTemporaryFile(suffix=os.path.splitext(os.path.basename(urlparse(url).path))[1]) as f:
					progressMsg = await ctx.send("Downloading `" + os.path.basename(urlparse(url).path) + "`...")
					# Valid audio file, download and play it
					file = requests.get(url, allow_redirects=True).content
					f.write(file)
					f.seek(0)
					await progressMsg.edit(content=progressMsg.content + "\nExtracting text from PDF...")
					pdfText = getTextFromPDF(f.name, ocr=forceOCR)
				await progressMsg.edit(content=progressMsg.content + "\nConverting text to audio...")
				try:
					speech = gTTS(text=pdfText, lang=language, tld=tld, slow=False)
				except (ValueError, gtts.tts.gTTSError):
					speech = gTTS(text=pdfText, lang='en', slow=False)
				with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
					try:
						speech.save(f.name)
					except AssertionError:
						raise NoTextFoundError
					f.seek(0)
					await playAudioFile(ctx, channel, f.name)
		else:
			raise NoAttachmentError
	else:
		raise NoAttachmentError

@speakPDF.error
async def speakPDF_error(ctx, error):
	if isinstance(error, InvalidPDFFormatError):
		await ctx.send("`" + error.filename + "` is not a valid PDF document")
	elif isinstance(error, NoAttachmentError):
		await ctx.send("No attachment for specified message")
	elif isinstance(error, NotInChannelError):
		await ctx.send(error.mention + " is not currently in a voice channel")
	elif isinstance(error, MessageNotFoundError):
		await ctx.send("Message not found")
	elif isinstance(error, NoTextFoundError):
		await ctx.send("No text found in PDF")
	else:
		traceback.print_exc()
		await ctx.send(str(type(error).__name__) + ": " + str(error))

@bot.command(pass_context=True, brief="Image TTS", description="Join your current voice channel and read the text from the specified image aloud")
async def speakImage(ctx, message_id: str, index_of_attachment=0, tld='com', language='en'):
	try:
		channel = ctx.author.voice.channel
	except Exception:
		raise NotInChannelError(ctx.author.id)
	try:
		msg = message_id.split("-")
		if len(msg) >= 2:
			try:
				message_channel = bot.get_channel(int(msg[0]))
				msg = await message_channel.fetch_message(int(msg[-1]))
			except Exception:
				msg = await ctx.fetch_message(int(msg[-1]))
		else:
			msg = await ctx.fetch_message(int(msg[-1]))
	except Exception:
		raise MessageNotFoundError
	if msg.attachments:
		if len(msg.attachments) >= index_of_attachment + 1:
			url = msg.attachments[index_of_attachment].url
			content_type = requests.head(url).headers['Content-Type']
			if not 'image' in content_type:
				raise InvalidImageFormatError(os.path.basename(urlparse(url).path))
			else:
				with tempfile.NamedTemporaryFile(suffix=os.path.splitext(os.path.basename(urlparse(url).path))[1]) as f:
					progressMsg = await ctx.send("Downloading `" + os.path.basename(urlparse(url).path) + "`...")
					# Valid audio file, download and play it
					file = requests.get(url, allow_redirects=True).content
					f.write(file)
					f.seek(0)
					await progressMsg.edit(content=progressMsg.content + "\nExtracting text from Image...")
					imageText = getTextFromImageObject(Image.open(f.name))
				await progressMsg.edit(content=progressMsg.content + "\nConverting text to audio...")
				try:
					speech = gTTS(text=imageText, lang=language, tld=tld, slow=False)
				except (ValueError, gtts.tts.gTTSError):
					speech = gTTS(text=imageText, lang='en', slow=False)

				with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
					try:
						speech.save(f.name)
					except AssertionError:
						raise NoTextFoundError
					f.seek(0)
					await playAudioFile(ctx, channel, f.name)
		else:
			raise NoAttachmentError
	else:
		raise NoAttachmentError

@speakImage.error
async def speakImage_error(ctx, error):
	if isinstance(error, InvalidImageFormatError):
		await ctx.send("`" + error.filename + "` is not a valid image")
	elif isinstance(error, NoAttachmentError):
		await ctx.send("No attachment for specified message")
	elif isinstance(error, NotInChannelError):
		await ctx.send(error.mention + " is not currently in a voice channel")
	elif isinstance(error, NoTextFoundError):
		await ctx.send("No text found in image")
	elif isinstance(error, MessageNotFoundError):
		await ctx.send("Message not found")
	else:
		traceback.print_exc()
		await ctx.send(str(type(error).__name__) + ": " + str(error))

@bot.command(pass_context=True, brief="Speak Text", description="Join your current voice channel and read the text after the command. Specify --lang for a language, or --tld with a TLD for an accent. Default en, com")
async def speakText(ctx, *, args):
	language='en'
	tld='com'
	args = shlex.split(args)
	words = []
	for index, item in enumerate(args):
		if not item.startswith("--") and (index - 1 != -1 and not args[index - 1].startswith('--')) or index == 0:
			words.append(item)
	text = ' '.join(words)
	args = {k.strip('-'): True if v.startswith('-') else v for k,v in zip(args, args[1:]+["--"]) if k.startswith('-')}
	if 'lang' in args:
		language = args['lang']
	if 'tld' in args:
		tld = args['tld']
	try:
		channel = ctx.author.voice.channel
	except Exception:
		raise NotInChannelError(ctx.author.id)

	await ctx.send("Converting text to audio...")
	try:
		speech = gTTS(text=text, lang=language, tld=tld, slow=False)
	except (ValueError, gtts.tts.gTTSError):
		speech = gTTS(text=text, lang='en', slow=False)

	with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
		try:
			speech.save(f.name)
		except AssertionError:
			raise NoTextFoundError
		await playAudioFile(ctx, channel, f.name)


@speakText.error
async def speakText_error(ctx, error):
	if isinstance(error, NotInChannelError):
		await ctx.send(error.mention + " is not currently in a voice channel")
	elif isinstance(error, NoTextFoundError):
		await ctx.send("No text provided")
	else:
		traceback.print_exc()
		await ctx.send(str(type(error).__name__) + ": " + str(error))

@bot.command(pass_context=True, brief="Speak Message", description="Join your current voice channel and read the specified message aloud")
async def speakMessage(ctx, message_id: str, language='en', tld='com'):
	try:
		channel = ctx.author.voice.channel
	except Exception:
		raise NotInChannelError(ctx.author.id)

	try:
		msg = message_id.split("-")
		if len(msg) >= 2:
			try:
				message_channel = bot.get_channel(int(msg[0]))
				msg = await message_channel.fetch_message(int(msg[-1]))
			except Exception:
				msg = await ctx.fetch_message(int(msg[-1]))
		else:
			msg = await ctx.fetch_message(int(msg[-1]))
	except Exception:
		raise MessageNotFoundError

	await ctx.send("Converting text to audio...")
	try:
		speech = gTTS(text=msg.content, lang=language, tld=tld, slow=False)
	except (ValueError, gtts.tts.gTTSError):
		speech = gTTS(text=msg.content, lang='en', slow=False)

	with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
		try:
			speech.save(f.name)
		except AssertionError:
			raise NoTextFoundError
		await playAudioFile(ctx, channel, f.name)


@speakMessage.error
async def speakMessage_error(ctx, error):
	if isinstance(error, NotInChannelError):
		await ctx.send(error.mention + " is not currently in a voice channel")
	elif isinstance(error, NoTextFoundError):
		await ctx.send("No text found in message")
	elif isinstance(error, MessageNotFoundError):
		await ctx.send("Message not found")
	else:
		traceback.print_exc()
		await ctx.send(str(type(error).__name__) + ": " + str(error))

# End Core Bot Commands
with open(os.path.join(workingDir, "secure", "client_secret.txt")) as f:
	secret = f.read().rstrip()
bot.run(secret)
del secret