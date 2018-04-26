
class User:

	@classmethod
	async def create(cls, **args):
		self = User()
		self.name = args.get("name", "")
		self.id = args.get("id", "")
		return self