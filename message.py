import os
import asyncio
from user import User

class MessageError(Exception):
	pass

class Message:

	@classmethod
	async def create(cls, **args):
		self = Message()
		self.channel = args.get("channel")
		self.text = args.get("text")
		self.user = args.get("user", (await User.create()))
		if (self.channel is None or self.text is None or not isinstance(self.user, User)):
			raise MessageError("Invalid message construction!")
		return self

class Embed(Message):

	@classmethod
	async def create(cls, **pargs):
		self = Embed()
		self.channel = pargs.get("channel")
		self.text = pargs.get("text")
		self.user = pargs.get("user", (await User.create()))
		self.title = pargs.get("title")
		self.color = pargs.get("color", 0xFFFFFF)
		self.image = pargs.get("image")
		self.description = pargs.get("description", self.text)
		self.thumbnail = pargs.get("thumbnail")
		self.url = pargs.get("url")
		self.fields = pargs.get("fields", [])
		self.author = pargs.get("author")
		self.footer = pargs.get("footer")
		return self

	async def setAuthor(self, a):
		self.author = a

	async def setFooter(self, f):
		self.footer = f

	async def addField(self, f):
		self.fields.append(f)

	class Author:

		@classmethod
		async def create(cls, **args):
			self = Embed.Author()
			self.name = args.get("name")
			self.url = args.get("url")
			self.iconURL = args.get("icon_url")
			return self

	class Footer:

		@classmethod
		async def create(cls, **args):
			self = Embed.Footer()
			self.text = args.get("text")
			self.iconURL = args.get("icon_url")
			return self

	class Field:

		@classmethod
		async def create(cls, **args):
			self = Embed.Field()
			self.name = args.get("name")
			self.value = args.get("value")
			self.inline = args.get("inline", True)
			return self
