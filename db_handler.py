import os
import aiopg
import asyncio

class DBError(Exception):
	pass

class DBHandler:

	class QueryResult:

		@classmethod
		async def create(cls, qr):
			self = DBHandler.QueryResult()
			self.__raw = qr
			return self

		@classmethod
		async def fromCursor(cls, cur):
			self = DBHandler.QueryResult()
			cols = [desc[0] for desc in cur.description]
			f = (await cur.fetchall())
			result = {}
			for row in f:
				c = 0
				for value in row:
					if cols[c] in result:
						result[cols[c]].append(value)
					else:
						result[cols[c]] = [value]
					c += 1
			self.__raw = result
			return self

		async def row(self, n):
			result = {}
			for column, vals in self.__raw.items():
				result[column] = vals[int(n)]
			return result

		async def rowData(self, n):
			result = []
			for column, vals in self.__raw.items():
				result.append(vals[int(n)])
			return result

		async def col(self, n):
			try:
				n = int(n)
				c = 0
				for column, vals in self.__raw.items():
					if (c == n):
						return vals
					c += 1
			except ValueError:
				n = str(n)
				for column, vals in self.__raw.items():
					if (column == n):
						return vals

		async def retrieve(self):
			return self.__raw

		async def rowCount(self):
			for col, values in self.__raw.items():
				return len(values)
			return 0

		async def colCount(self):
			return len(self.__raw)

	@classmethod
	async def connect(cls, **args):
		self = DBHandler()
		self.__pool = None
		self.__db = None
		self.__sql = None
		await (self.setDatabase(
			args.get("name", args.get("dbname")), 
			args.get("user", args.get("username")), 
			args.get("host", args.get("addr")), 
			args.get("pass", args.get("password")) 
		))
		return self
		
	async def setDatabase(self, n, u, h, p):
		try:
			self.name = str(n)
			self.user = str(u)
			self.host = str(h)
			self.password = str(p)
			self._dbString = "dbname='" + n + "' user='" + u + "' host='" + h + "' password='" + p + "'"
		except ValueError:
			raise DBError("Invalid parameters types for setDatabase()")
		try:
			self.__pool = (await aiopg.create_pool(self._dbString))
		except:
			raise DBError("Could not connect to database!")

	async def get(self, table, columns, where = []):

		if (not isinstance(where, list)):
			raise DBError("Wrong format for where condition")
		sqlstr = "select " + columns + " from " + table + " "
		sqldat = (await self.__parseWhere(where))
		sqlvals = sqldat["vals"]

		try:
			async with self.__pool.acquire() as conn:
				async with conn.cursor() as sql:
					if (len(sqlvals) > 0):
						sqlstr += sqldat["str"]
						await (sql.execute(sqlstr, sqlvals))
					else:
						await (sql.execute(sqlstr))
					result = (await DBHandler.QueryResult.fromCursor(sql))
					return result
		except Exception as e:
			raise DBError("Error retrieving data from database.")

	async def insertOrUpdate(self, **args):

		table = str(args.get("table"))
		columns = args.get("columns")
		keys = args.get("keys")
		values = args.get("values")

		if (table is None or keys is None or values is None or columns is None or (len(columns) != len(values))):
			raise DBError("Not enough information given to insert of update records.")
		else:
			
			strcols = ','.join(columns)
			strkeys = ','.join(keys)
			sqlvals = []
			sqlstr = "insert into " + table + " (" + strcols + ") values ("
			for value in values:
				sqlstr += "%s,"
				sqlvals.append(value)
			sqlstr = sqlstr[:-1] + ") on conflict (" + strkeys + ") do update set "
			for i in range(0, len(columns)):
				if columns[i] not in keys:
					sqlstr += columns[i] + "=%s,"
					sqlvals.append(values[i])
			sqlstr = sqlstr[:-1] + ';'

			try:
				async with self.__pool.acquire() as conn:
					async with conn.cursor() as sql:
						await (sql.execute(sqlstr, sqlvals))
			except:
				raise DBError("Error inserting data into database.")

	async def __parseWhere(self, where):
		sqlvals = []
		swhere = " where "
		for condition in where:
			cond = condition.split('=')
			if (len(cond) != 2):
				raise DBError("Wrong format for where condition.")
			swhere += cond[0] + "=%s and "
			sqlvals.append(cond[1])
		swhere = swhere[:-5]
		return {"vals": sqlvals, "str": swhere}

	async def delete(self, table, where):

		sqlstr = "delete from " + table + " "
		sqldat = (await self.__parseWhere(where))
		sqlstr += sqldat["str"]
		sqlvals = sqldat["vals"]

		try:
			async with self.__pool.acquire() as conn:
					async with conn.cursor() as sql:
						await (sql.execute(sqlstr, sqlvals))
		except:
			raise DBError("Error deleting data from database.")	


