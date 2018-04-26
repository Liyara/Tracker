import os
from channel import Channel
from channel import ChannelError
from db_handler import DBHandler
from db_handler import DBError
from date_time_handler import DateTime
import asyncio

class PlayerError:
	pass

class Player:

	@classmethod
	async def create(cls, **args):
		self = Player()
		self.name = str(args.get("name", ""))
		self.id = str(args.get("id", ""))
		self.checked = args.get("checked", None)
		self.rank = str(args.get("rank", ""))
		self.channels = args.get("channels", [])
		self.module = str(args.get("module", ""))
		self.misc = dict(args.get("misc", {}))
		return self

	@classmethod
	async def fromDB(cls, db, id, module):
		self = Player()
		data = (await db.get("_players", "*", ["id=" + str(id), "module=" + str(module)]))
		if ((await data.rowCount()) > 0):
			data = (await data.row(0))
			self.id = data["id"]
			self.name = data["name"]
			self.checked = (await DateTime.fromString(data["checked"]))
			self.rank = data["rank"]
			self.module = data["module"]
			self.channels = []
			self.misc = {}

			data = (await db.get("_tracks", "*", ["player_id=" + self.id, "module=" + str(module)]))
			rows = (await data.rowCount())

			if (rows > 0):
				for i in range(0, rows):
					chid = (await data.row(i))["channel_id"]
					ch = (await Channel.fromDB(db, chid))
					self.channels.append(ch)
					self.misc[chid] = (await data.row(i))["misc"]
			else:
				raise PlayerError("Requested player is not being tracked!")
		else:
			raise PlayerError("Player not found in db!")

		return self

	async def updateInDB(self, db):

		dt = (await self.checked.asString())

		try:
			await (db.insertOrUpdate(
				table = "_players", 
				columns = ["id", "name", "checked", "rank", "module"],
				keys = ["id", "module"],
				values = [self.id, self.name, dt, self.rank, self.module]
			))
		except DBError:
			return False

		for channel in self.channels:

			try:
				await (channel.updateInDB(db))

				await (db.insertOrUpdate(
					table = "_tracks",
					columns = ["player_id", "channel_id", "module", "misc"],
					keys = ["player_id", "channel_id", "module"],
					values = [self.id, channel.id, self.module, self.misc[channel.id]]
				))
			except (ChannelError, DBError):
				return False
		return True

	async def unregister(self, db, channel, mod):
		try:
			if (channel is not None):
				await (db.delete("_tracks", ["channel_id=" + channel.id, "player_id=" + self.id, "module=" + mod]))
			else:
				for channeln in self.channels:
					await (db.delete("_tracks", ["channel_id=" + channeln.id, "player_id=" + self.id, "module=" + mod]))
			tracks = (await (db.get("_tracks", "*", ["player_id=" + self.id, "module=" + mod])))
			if ((await (tracks.rowCount())) == 0):
				await (db.delete("_players", ["id=" + self.id, "module=" + mod]))
			if (channel is not None):
				tracks = (await (db.get("_tracks", "*", ["channel_id=" + channel.id])))
				if ((await (tracks.rowCount())) == 0):
					await (db.delete("_channels", ["id=" + channel.id]))
			else:
				for channeln in self.channels:
					tracks = (await (db.get("_tracks", "*", ["channel_id=" + channeln.id])))
					if ((await (tracks.rowCount())) == 0):
						await (db.delete("_channels", ["id=" + channeln.id]))
		except DBError:
			return False
		return True