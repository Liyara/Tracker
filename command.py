import asyncio

class CommandError(Exception):
		pass

class Command:

	@classmethod
	async def define(cls, name, func, mod, amin = None, amax = None):
		self = Command()
		if (callable(func)):
			self.func = func
		else:
			raise CommandError("Invalid callback given!")
		try:
			self.name = str(name)
			self.argMin = amin
			self.argMax = amax
			self.module = mod
		except ValueError:
			raise CommandError("Invalid propeties given to command!")
		return self

	async def execute(self, message, *args):
		if (self.argMin is not None):
			if (self.argMax is not None):
				if (len(args) < self.argMin or len(args) > self.argMax):
					raise CommandError("Wronmg arguments for command!")
			else:
				if (len(args) < self.argMin):
					raise CommandError("Wronmg arguments for command!")
		await (self.func(message, self.module, *args))