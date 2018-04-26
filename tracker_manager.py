from tracker_module import TrackerModule
import asyncio

class ModuleError(Exception):
		pass

class Manager:

	def __init__(self, m = None):
		self.modules = []
		if (m is not None and isinstance(m, list)):
			for module in m:
				if (isinstance(module, TrackerModule)):
					self.modules.append(module)
				else:
					raise ModuleError("Invalid module given!")

	async def addModule(self, m):
		for module in self.modules:
			if ((await module.getName()) == (await m.getName())):
				raise ModuleError("Attempt to add duplicate module '" + module.getName() + "'!")
		self.modules.append(m)

	async def removeModule(self, n):
		for i in range(0, len(self.modules)):
			if ((await self.modules[i].getName()) == str(n)):
				del self.modules[i]
				return
		raise ModuleError("Module " + str(n) + " not found!")

	async def getModule(self, name):
		for module in self.modules:
			if ((await (module.getName())) == str(name)):
				return module
		raise ModuleError("Module " + str(name) + " not found!")

	async def pollModules(self):
		responses = []
		for module in self.modules:
			response = dict((await module.generateResponse()))
			for o in response.pop("out"):
				print(str(o), end = "")
			for e in response.pop("err"):
				print((await module.getName()) + " -> " + str(e) + '\n')
			responses.append({
				str((await module.getName())): response
			})
		return responses
