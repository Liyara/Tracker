import asyncio

class ChannelError(Exception):
	pass

class Channel:

	@classmethod 
	async def create(cls, **args):
		self = Channel()
		self.server = args.get("server", args.get("server_id"))
		self.name = args.get("name", "")
		self.id = args.get("id")
		return self

	@classmethod
	async def fromDB(cls, db, id):
		self = Channel()
		r = (await db.get("_channels", "*", ["id=" + id]))
		if ((await r.rowCount()) > 0):
			r = (await r.row(0))
			self.server = r["server_id"]
			self.name = r["name"]
			self.id = r["id"]
		else:
			raise ChannelError("Channel not found in db!")
		return self

	async def updateInDB(self, db):
		await (db.insertOrUpdate(
			table = "_channels",
			columns = ["id", "name", "server_id"],
			keys = ["id"],
			values = [self.id, self.name, self.server]
		))

