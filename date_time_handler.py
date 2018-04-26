import pytz
from datetime import datetime
from datetime import timedelta
import asyncio

class DateError(Exception):
		pass

class TimeError(Exception):
	pass

class DateTimeError(TimeError, DateError):
	pass

class DateTime:

	@classmethod
	async def at(cls, date, time):
		self = DateTime()
		await (self.init())
		await (self.setDate(date))
		await (self.setTime(time))
		return self

	@classmethod
	async def utc(cls, hours = 0):
		self = DateTime()
		await (self.init())
		t = str(datetime.utcnow().replace(tzinfo=pytz.utc))
		t = t[0:t.find('.')]
		await (self.setAll(t))
		await (self.offset(hours = hours))
		return self

	@classmethod
	async def fromString(cls, s):
		self = DateTime()
		await (self.init())
		await (self.setAll(s))
		return self

	async def init(self):
		self.__dn = [
			"year",
			"month",
			"day",
			"hour",
			"minute",
			"second"
		]
		self.__dt = {}
		for n in self.__dn:
			self.__dt[n] = None

	async def _max(self, n):
		i = self.__dn.index(n)
		switcher = {
			0: 9999,
			1: 12,
			2: -1,
			3: 23,
			4: 59,
			5: 59
		}
		rm = switcher.get(i)
		if (rm < 0):
			dic = {
				31: [1, 3, 5, 7, 8, 10, 12],
				30: [4, 6, 9, 11],
				28: [2],
				29: []
			}
			if (self.__dt["year"] % 4 == 0):
				dic[29].append(disc[28].pop(0))
			for days, months in dic.items():
				for m in months:
					if (m == self.__dt["month"]):
						rm = days
		return rm

	async def _min(self, n):
		i = self.__dn.index(n)
		switcher = {
			0: 0,
			1: 1,
			2: 1,
			3: 0,
			4: 0,
			5: 0
		}
		return switcher.get(i)

	async def offset(self, **args):
		for t, v in args.items():
			t = t[:-1]
			if t in self.__dn:
				adder = int(v)
				self.__dt[t] = int(self.__dt[t]) + adder
				mi = (await self._min(t))
				while True:
					ma = (await self._max(t))
					if (self.__dt[t] <= ma):
						break
					self.__dt[t] -= ma - (1 - mi)
					dic = {}
					dic[str(self.__dn[self.__dn.index(t) - 1]) + 's'] = 1
					await (self.offset(**dic))
			else:
				raise DateTimeError("Invalid string for offset (" + str(t) + ")")

	async def get(self, n):
		return self.__dt[n]

	async def set(self, **args):
		for t, v in args.items():
			if t in self.__dn:
				self.__dt[t] = int(v)
			else:
				raise DateTimeError("Invalid string for set")

	async def setAll(self, dt):
		dt = str(dt).split(' ')
		if (len(dt) == 2):
			await (self.setDate(dt[0]))
			await (self.setTime(dt[1]))
		else:
			raise DateTimeError("Invalid DateTime format!")

	async def setDate(self, date):
		date = str(date).replace(' ', '')
		dp = date.split('-')
		if (len(dp) == 3):
			await (self.set(
				year = int(dp[0]),
				month = int(dp[1]),
				day = int(dp[2])
			))
		else:
			raise DateError("Invalid date passed!")

	async def setTime(self, time):
		time = str(time).replace(' ', '')
		tp = time.split(':')
		if (len(tp) == 3):
			tp[0] = tp[0][0:2]
			tp[1] = tp[1][0:2]
			tp[2] = tp[2][0:2]
			await (self.set(
				hour = int(tp[0]),
				minute = int(tp[1]),
				second = int(tp[2])
			))
		else:
			raise TimeError("Invalid time passed! " + str(tp))

	async def _asString(self, data, l = 2):
		data = str(self.__dt[str(data)])
		while (len(data) < l):
			data = '0' + data
		return data

	async def dateAsString(self):
		yyyy = (await self._asString("year", 4))
		mm = (await self._asString("month"))
		dd = (await self._asString("day"))
		return (yyyy + '-' + mm + '-' + dd)

	async def timeAsString(self):
		hh = (await self._asString("hour"))
		mm = (await self._asString("minute"))
		ss = (await self._asString("second"))
		return (hh + ':' + mm + ':' + ss)

	async def asString(self):
		return ((await self.dateAsString()) + ' ' + (await self.timeAsString()))

	async def _compare(self, other):
		for i in range(0, len(self.__dn)):
			c = self.__dn[i]
			si = self.__dt[c]
			oi = (await other.get(c))
			if (si == oi):
				continue
			elif (si > oi):
				return 0
			else:
				return 1
		return -1

	async def asRecentAs(self, other):
		return ((await self._compare(other)) == -1)

	async def lessRecentThan(self, other):
		return ((await self._compare(other)) == 1)

	async def moreRecentThan(self, other):
		return ((await self._compare(other)) == 0)
