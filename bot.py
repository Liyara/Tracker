import os
import discord
from discord.ext.commands import Bot
from discord.utils import get
from discord.ext import commands
import asyncio

from message import Message
from message import Embed
from user import User
from channel import Channel

class BotError(Exception):
	pass

class Bot(commands.Bot):
	def __init__(self, command_prefix = '!', **options):
		super().__init__(command_prefix, **options)
		self.__callbacks = {
			"on_ready": None,
			"on_message": None,
			"background": None
		}
		self.timer = options.get("timer")
		if (self.timer is None):
			self.timer = 0
		self.green = False
		self.setCallbacks(**options)

	def setCallbacks(self, **options):
		for callbackName in self.__callbacks:
			func = options.get(callbackName)
			if (func is not None and callable(func)):
				self.__callbacks[callbackName] = func
			else:
				raise BotError("Uncallable callback given!")

	async def getUser(self):
		return self._user

	@asyncio.coroutine
	async def on_ready(self):
		await (self.__callbacks["on_ready"]())

	@asyncio.coroutine
	async def on_message(self, message):
		await (self.__callbacks["on_message"](message))

	async def sendMessage(self, message):
		message.user = (await User.create(name = self.user.name, id = self.user.id))
		if (isinstance(message, Embed)):
			em = discord.Embed(title = message.title, description = message.description, color = message.color, url = message.url)
			if (message.image is not None):
				em.set_image(url = message.image)
			if (message.thumbnail is not None):
				em.set_thumbnail(url = message.thumbnail)
			if (message.author is not None):
				eaurl = message.author.url if message.author.url is not None else discord.Embed.Empty
				eaurlico = message.author.iconURL if message.author.iconURL is not None else discord.Embed.Empty
				em.set_author(name = message.author.name, url = eaurl, icon_url = eaurlico)
			if (message.footer is not None):
				efurlico = message.footer.iconURL if message.footer.iconURL is not None else discord.Embed.Empty
				em.set_footer(text = message.footer.text, icon_url = efurlico)
			for field in message.fields:
				em.add_field(name = field.name, value = field.value, inline = field.inline)
			try:
				await (self.send_message(self.get_channel(message.channel.id), message.text, embed = em))
			except Exception as e:
				raise BotError("Problem reporting score. (" + e + ")")
		elif (isinstance(message, Message)):
			await (self.send_message(self.get_channel(message.channel.id), message.text))
		else:
			raise BotError("Invalid message queued to send!")	

	async def bg(self):
		await (self.wait_until_ready())
		process = self.__callbacks["background"]
		if (self.timer > 0 and process is not None and callable(process)):
			while not self.is_closed:
				try:
					if (self.green):
						await (process())	
					await (asyncio.sleep(self.timer))
				except Exception as e:
					print(e)
			print("bg closed!")

	def begin(self, token):
		try:
			self.loop.create_task(self.bg())
		except Exception as e:
			print(str(e))
			self.restart(token)
		try:
			self.run(token)
		except Exception as e:
			print(str(e))

	def restart(self, token):
		for task in asyncio.Task.all_tasks():
			task.cancel()
		self.begin(token)
	



