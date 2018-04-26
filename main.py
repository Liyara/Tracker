import asyncio
from bot import Bot
from message import Message
from message import Embed
from tracker_manager import Manager
from osu_tracker import OsuTracker
from db_handler import DBHandler
from command import Command
from channel import Channel
from user import User
import os

class Main:

	def __init__(self):
		print("Bot starting...")
		self.__bot = Bot(
			on_ready = self.onReady,
			on_message = self.onMessage,
			background = self.bg,
			timer = 1
		)
		self.__manager = Manager()
		self._commands = []
		self.__db = None
		self.__init = False
		self.__bot.begin(os.environ.get("BOT_TOKEN"))

	# event listeners

	async def onReady(self):
		if (not self.__init):
			self.__db = (await DBHandler.connect(
				name = os.environ.get("DB_NAME"),
				user = os.environ.get("DB_USER"),
				host = os.environ.get("DB_HOST"),
				password = os.environ.get("DB_PASS")
			))
			await (self.__manager.addModule((await OsuTracker.initialize(self.__db))))
			osuMod = (await self.__manager.getModule("osu"))
			self._commands = [
				(await Command.define("track_osu", self.track_many_osu, osuMod, 1)),
				(await Command.define("untrack_osu", self.untrack_osu, osuMod, 1))
			]
			self.__init = True
		self.__bot.green = True
		print("Bot ready.")

	async def onMessage(self, msg):
		channel = (await Channel.create(
			id = msg.channel.id, 
			name = msg.channel.name,
			server = msg.server.id,
		))
		sender = (await User.create(
			id = msg.author.id,
			name = msg.author.name
		))
		message = (await Message.create(
			channel = channel,
			text = msg.content,
			user = sender
		))
		args = (message.text.split(' '))
		cmdt = args.pop(0)
		if (len(cmdt) > 1 and cmdt[0] == '!'):
			cmdt = cmdt[1:]
			for cmd in self._commands:
				if (cmdt == cmd.name):
					await (cmd.execute(message, *args))

	async def bg(self):
		responses = (await self.__manager.pollModules())
		for moduleResponse in responses:
			for moduleName, response in moduleResponse.items():
				if (moduleName == "osu"):
					records = response["records"]
					for record in records:
						scores = record["scores"]
						for score in scores:
							for ch in score["channels"]:
								score["embed"].channel = ch
								await (self.__bot.sendMessage(score["embed"]))

	# commands

	async def track_osu(self, message, mod, *args):
		if (len(args) == 1):
			lim = 100
		else:
			lim = args[1]
		succ = (await (mod.trackPlayer(args[0], lim, message.channel)))
		if (succ):
			punc = "'"
			if (args[0][-1] != 's'):
				punc += 's'
			m = (await Message.create(
				channel = message.channel,
				text = ":white_check_mark: Now tracking " + args[0] + punc + " top " + str(lim) + " plays."
			))
		else:
			m = (await Message.create(
				channel = message.channel,
				text = ":x: Failed to track player \"" + args[0] + "\" in this channel."
			))
		await (self.__bot.sendMessage(m))

	async def track_many_osu(self, message, mod, *args):
		nArgs = (await self._parseOsuArgs(*args))
		for name, lim in nArgs.items():
			await (self.track_osu(message, mod, *[name, lim]))
			
	async def untrack_osu(self, message, mod, *args):
		m = (await Message.create(
			channel = message.channel,
			text = ""
		))
		for arg in args:
			if ((await mod.untrackPlayer(arg, message.channel))):
				punc = "'"
				if (arg[-1] != 's'):
					punc += 's'
				m.text = ":white_check_mark: No longer tracking " + arg + punc + " plays."
			else:
				m.text = ":x: That player is already not tracked!"
			await (self.__bot.sendMessage(m))

	# helpers

	async def _parseOsuArgs(self, *args):
		build = None
		nArgs = {}
		lim = None
		name = None
		for arg in args:
			if (arg[0] == '"'):
				if (arg[-1] == '"'):
					name = arg[1:-1]
				elif (build is None):
					build = arg[1:]
				else:
					raise
			elif (build is not None):
				if (arg[-1] == '"'):
					name = build + arg[0:-1]
					build = None
				else:
					build += arg
			else:
				try:
					lim = int(arg)
					if (lim > 100 or lim < 1):
						raise ValueError
				except ValueError:
					if (name is not None):
						nArgs[name] = 100
					name = arg

			if (lim is not None and name is not None):
				nArgs[name] = lim
				lim = None
				name = None
		if (name is not None and lim is None):
			nArgs[name] = 100
		return nArgs

r = Main()

