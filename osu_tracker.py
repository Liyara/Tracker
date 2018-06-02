import os
from player import Player
from db_handler import DBHandler
from db_handler import DBError
from date_time_handler import DateTime
import time
import asyncio
from message import Embed
from flags import Flags
import aiohttp
from tracker_module import TrackerModule
from channel import Channel
import async_timeout
import socket

class OsuTracker(TrackerModule):

	@classmethod
	async def initialize(cls, db):
		self = OsuTracker()
		self.__db = db
		self.apiKey = os.environ.get("OSU_API_KEY")
		self.__outQueue = []
		self.__errQueue = []
		self.players = (await self.retrievePlayersFromDB())
		return self

	async def __queue(self, **args):
		out = args.get("out", None)
		err = args.get("err", None)
		if (out is not None):
			if (isinstance(out, str)):
				self.__outQueue.append(out)
			elif (isinstance(out, list)):
				self.__outQueue.extend(out)
			else:
				self.__outQueue.extend([out])
		if (err is not None):
			if (isinstance(err, str) or isinstance(err, Exception)):
				self.__errQueue.append(str(err))
			elif (isinstance(err, list)):
				self.__errQueue.extend(err)

	async def retrievePlayersFromDB(self):
		print("Retrieving tracked players... ", end="")
		result = []
		try:
			q = (await self.__db.get("_players", "id"))
		except DBError as e:
			await (self.__queue(err = e))
			return None
		for i in range (0, (await q.rowCount())):
			result.append((await Player.fromDB(self.__db, (await q.row(i))["id"], (await self.getName()))))
		print("complete.")
		return result

	async def getPlayerByID(self, id):
		for player in self.players:
			if (player.id == str(id)):
				return player
		return None

	async def getPlayerByName(self, name):
		for player in self.players:
			if (player.name == str(name)):
				return player
		return None

	async def replacePlayer(self, player):
		for i in range(0, len(self.players)):
			if (self.players[i].id == player.id):
				self.players[i] = player
				await (self.players[i].updateInDB(self.__db))
				return True
		return False

	async def parseJSON(self, session, addr):
		parsed_json = None
		string = None
		# print("parsing", end = "")
		try:
			async with async_timeout.timeout(3):
				async with session.get(addr) as response:
					# print("... ", end = "")
					parsed_json = (await response.json())
		except asyncio.TimeoutError:
			# print(" [FAILED]")
			return (await self.parseJSON(session, addr))
		# print("complete.")
		return parsed_json

	async def getData(self, page, **args):
		url = "https://osu.ppy.sh/api/" + page + "?k=" + self.apiKey
		for key, value in args.items():
			url += '&' + str(key) + '=' + str(value)
		dconn = aiohttp.TCPConnector(
			family=socket.AF_INET,
        	verify_ssl=False
        )
		async with aiohttp.ClientSession(connector = dconn) as session:
			data = (await self.parseJSON(session, url))
			return data

	async def getName(self):
		return "osu"

	async def trackPlayer(self, name, limit, channel):
		p = (await self.getPlayerByName(name))
		if (p is None):
			data = (await (self.getData("get_user", u = name, type = "string")))
			if (data is not None and len(data) > 0):
				data = data[0]
			else:
				await (self.__queue(err = "Could not find player data"))
				return False
			if (data["user_id"] is not None):
				curDate = (await DateTime.utc())
				self.players.append((await Player.create(
					id = data["user_id"],
					name = str(name),
					rank = data["pp_rank"],
					checked = curDate,
					module = (await self.getName()),
					misc = {channel.id: str(limit)}
				)))
				self.players[-1].channels.append(channel)
				return (await (self.players[-1].updateInDB(self.__db)))
			else:
				await (self.__queue(err = "Player data incorrect"))
				return False
		else:
			if (channel.id in p.misc):
				await (self.__queue(err = "Duplicate track"))
				return False
			else:
				p.channels.append(channel)
				p.misc[channel.id] = limit
				return (await self.replacePlayer(p))

	async def untrackPlayer(self, name, channel):
		for i in range (0, len(self.players)):
			if (self.players[i].name.upper() == name.upper()):
				await (self.players[i].unregister(self.__db, channel, (await self.getName())))
				for ii in range(0, len(self.players[i].channels)):
					if (self.players[i].channels[ii].id == channel.id):
						self.players[i].channels.pop(ii)
						self.players[i].misc.pop(channel.id)
						if (len(self.players[i].channels) == 0):
							self.players.pop(i)
						break
				return True
		await (self.__queue(err = "Player not found"))
		return False

	async def parseMods(self, mn):
		if (int(mn) > 0):
			modFlags = OsuTracker.Mods(int(mn))
			result = []
			if (modFlags & OsuTracker.Mods.Hidden):
				result.append("hd")
			if (modFlags & OsuTracker.Mods.HardRock):
				result.append("hr")
			if (modFlags & OsuTracker.Mods.DoubleTime or (modFlags & (OsuTracker.Mods.DoubleTime | OsuTracker.Mods.Nightcore))):
				result.append("dt")
			if (modFlags & OsuTracker.Mods.Flashlight):
				result.append("fl")
			if (modFlags & OsuTracker.Mods.Easy):
				result.append("ez")
			if (modFlags & OsuTracker.Mods.HalfTime):
				result.append("ht")
			if (len(result) > 3):
				result = result[0:3]
			return result
		else:
			return ["nm"]

	async def __getModIcons(self, mods):
		mdb = (await self.__db.get("images", "*"))
		for i in range(0, (await mdb.rowCount())):
			row = (await mdb.row(i))
			rowMods = row["mods"].split(' ')
			if (len(rowMods) != len(mods)):
				match = False
			else:
				match = True
				for mod in mods:
					if (mod not in rowMods):
						match = False
			if (match):
				return row["address"]

	async def updatePlayer(self, player):
		data = (await self.getData("get_user", u = player.id, type = "id"))

		if (data is None or len(data) == 0):
			await (self.__queue(err = "Failed to grab player data."))
			return None
		else:
			data = data[0]

		player.name = data["username"]
		rank_diff =  int(player.rank) - int(data["pp_rank"])
		player.rank = data["pp_rank"]

		scores = (await self.getData("get_user_best", u = player.id, type = "id", limit = 100))

		if (scores is None):
			await (self.__queue(err = "Failed to grab player scores."))
			return None

		result = {"player": player, "scores": []}

		"""diffs = {
			"easy": "<:easy:433270655769903104>",
			"normal": "<:normal:433272715424563202>",
			"hard": "<:hard:433272728380899358>",
			"insane": "<:insane:433272738036056064>",
			"extra": "<:extra:433272754264080394>"
		}"""

		if (player.checked != None):
			c = 0
			for score in scores:
				c = c + 1
				dt = (await DateTime.fromString(score["date"]))
				
				if (await (dt.moreRecentThan(player.checked))):
					
					mods = (await self.parseMods(score["enabled_mods"]))
					modIconURL = (await self.__getModIcons(mods))
					bmap = (await self.getData("get_beatmaps", b = score["beatmap_id"], m = 0))[0]

					if (bmap is None):
						await (self.__queue(err = "Failed to grab beatmap data."))
						return None

					pp = str(int(round(float(score["pp"]), 0)))
					strMods = ""
					for bmod in mods:
						strMods += bmod + ", "
					strMods = strMods[0:-2]

					"""bdiffn = float(bmap["difficultyrating"])
					if (bdiffn >= 5.2):
						bdiff = "extra"
					elif (bdiffn < 5.2 and bdiffn >= 4.0):
						bdiff = "insane"
					elif (bdiffn < 4.0 and bdiffn >= 2.2):
						bdiff = "hard"
					elif (bdiffn < 2.2 and bdiffn >= 1.5):
						bdiff = "normal"
					elif (bdiffn < 1.5):
						bdiff = "easy"""

					if (c == 1):
						col = 0xFFDF00
					elif (int(c) <= 10):
						col = 0x00FF00
					else:
						col = 0xFFFFFF

					accNum = float(50.0 * int(score["count50"]) + 100.0 * int(score["count100"]) + 300.0 * int(score["count300"]))
					accDen = float(300.0 * (int(score["countmiss"]) + int(score["count50"]) + int(score["count100"]) + int(score["count300"])))
					accuracy = float(accNum / accDen) * 100.0

					em = (await Embed.create(
						channel = None,
						description = None,
						color = col,
						title = bmap["artist"] + " - " + bmap["title"] + " [" + bmap["version"] + ']',
						image = "https://assets.ppy.sh/beatmaps/" + bmap["beatmapset_id"] + "/covers/cover.jpg",
						thumbnail = modIconURL,
						url = "https://osu.ppy.sh/beatmapsets/" + bmap["beatmapset_id"],

						author = (await Embed.Author.create(
							name = player.name,
							url = "https://osu.ppy.sh/users/" + player.id,
							icon_url = "https://a.ppy.sh/" + player.id
						)),

						fields = [
							(await Embed.Field.create(
								name = "<:s_:433281051679522836> " + pp + "pp   " + str(round(accuracy, 2)) + "%   PB #" + str(c),
								value = score["countmiss"] + " x miss\t" + score["count100"] + " x 100\t" + score["count50"] + " x 50\t" + 
									score["maxcombo"] + " / " + bmap["max_combo"],
								inline = False
							))
						]
					))

					result["scores"].append({"embed": em, "channels": []})
					for channel in player.channels:
						if (channel.id in player.misc and c <= int(player.misc[channel.id])):
							result["scores"][-1]["channels"].append(channel)
							
		player.checked = (await DateTime.utc())
		await (player.updateInDB(self.__db))
		print (player.name + " updated " + (await player.checked.asString()))
		return result

	async def generateResponse(self):
		scores = []
		for player in self.players:
			score = (await self.updatePlayer(player))
			if (score is not None):
				scores.append(score)
			else:
				await (self.__queue(err = "Problem retrieving score!"))
		response = {
			"err": self.__errQueue,
			"out": self.__outQueue,
			"records": scores
		}
		self.__outQueue = []
		self.__errQueue = []
		return response

	class Mods(Flags):
		NoFail         = 1
		Easy           = 2
		NoVideo        = 4
		Hidden         = 8
		HardRock       = 16
		SuddenDeath    = 32
		DoubleTime     = 64
		Relax          = 128
		HalfTime       = 256
		Nightcore      = 512
		Flashlight     = 1024
		Autoplay       = 2048
		SpunOut        = 4096
		Relax2         = 8192
		Perfect        = 16384
		Key4           = 32768
		Key5           = 65536
		Key6           = 131072
		Key7           = 262144
		Key8           = 524288
		FadeIn         = 1048576
		Random         = 2097152
		LastMod        = 4194304
		Key9           = 16777216
		Key10          = 33554432
		Key1           = 67108864
		Key3           = 134217728
		Key2           = 268435456
