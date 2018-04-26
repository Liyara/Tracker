import asyncio

class TrackerModule:

	@classmethod
	async def initialize(cls, db):
		raise NotImplementedError("initialize was not implemented.")

	async def getName(self):
		raise NotImplementedError("getName was not implemented.")

	async def generateResponse(self):
		raise NotImplementedError("generateResponse was not implemented.")