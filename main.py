import re

INDENT = '    '

class Conf(object):
	def __init__(self, *args):
		self.blocks = list(args)
		self.servers = []
		self.upd()

	def add(self, *args):
		self.blocks.extend(args)
		self.upd()
		return self.blocks

	def remove(self, *args):
		self.blocks.remove(*args)
		self.upd()
		return self.blocks

	def upd(self):
		svr = []
		for x in self.blocks:
			if isinstance(x, Server):
				svr.append(x)
		self.servers = svr

	def all(self):
		return self.blocks

	def as_list(self):
		ret = []
		for x in self.blocks:
			ret.append(x.as_list())
		return ret

	def as_block(self):
		ret = []
		for x in self.blocks:
			if isinstance(x, (Key, Comment)):
				ret.append(x.as_block())
			else:
				for y in x.as_block():
					ret.append(y)
		return ret


class Server(object):
	def __init__(self, *args):
		self.blocks = list(args)
		self.locations = []
		self.comments = []
		self.keys = []
		self.upd()

	def add(self, *args):
		self.blocks.extend(args)
		self.upd()
		return self.blocks

	def remove(self, *args):
		self.blocks.remove(*args)
		self.upd()
		return self.blocks

	def upd(self):
		l, c, k = [], [], []
		for x in self.blocks:
			if isinstance(x, Location):
				l.append(x)
			elif isinstance(x, Comment):
				c.append(x)
			elif isinstance(x, Key):
				k.append(x)
		self.locations, self.comments, self.keys = l, c, k

	def all(self):
		return self.blocks

	def as_list(self):
		ret = []
		for x in self.blocks:
			ret.append(x.as_list())
		return ['server', '', ret]

	def as_block(self):
		ret = []
		ret.append('server {\n')
		for x in self.blocks:
			if isinstance(x, (Key, Comment)):
				ret.append(INDENT + x.as_block())
			elif isinstance(x, Container):
				y = x.as_block()
				ret.append('\n'+INDENT+y[0])
				for z in y[1:]:
					ret.append(INDENT+z)
		ret.append('}\n')
		return ret


class Container(object):
	def __init__(self, value, *args):
		self.name = ''
		self.value = value
		self.comments = []
		self.keys = []
		self.blocks = list(args)
		self.upd()

	def add(self, *args):
		self.blocks.extend(args)
		self.upd()
		return self.blocks

	def remove(self, *args):
		self.blocks.remove(*args)
		self.upd()
		return self.blocks

	def upd(self):
		c, k = [], []
		for x in self.blocks:
			if isinstance(x, Comment):
				c.append(x)
			elif isinstance(x, Key):
				k.append(x)
		self.comments, self.keys = c, k

	def all(self):
		return self.blocks

	def as_list(self):
		ret = []
		for x in self.blocks:
			ret.append(x.as_list())
		return [self.name, self.value, ret]

	def as_block(self):
		ret = []
		ret.append(self.name + ' ' + self.value + ' {\n')
		for x in self.blocks:
			if isinstance(x, (Key, Comment)):
				ret.append(INDENT + x.as_block())
			else:
				y = x.as_block()
				ret.append(INDENT+y)
		ret.append('}\n\n')
		return ret


class Comment(object):
	def __init__(self, comment):
		self.comment = comment

	def as_list(self):
		return [self.comment]

	def as_block(self):
		return '# ' + self.comment + '\n'


class Location(Container):
	def __init__(self, value, *args):
		super(Location, self).__init__(value, *args)
		self.name = 'location'


class LimitExcept(Container):
	name = 'limit_except'


class Types(Container):
	name = 'types'


class If(Container):
	name = 'if'


class Upstream(Container):
	name = 'upstream'


class Key(object):
	def __init__(self, name, value):
		self.name = name
		self.value = value

	def as_list(self):
		return [self.name, self.value]

	def as_block(self):
		return self.name + ' ' + self.value + ';\n'


def loads(data):
	f = Conf()
	lopen = []
	for line in data.split('\n'):
		if re.match('\s*server\s*{', line):
			s = Server()
			lopen.insert(0, s)
		if re.match('\s*location.*{', line):
			lpath = re.match('\s*location\s*(.*)\s*{', line).group(1)
			l = Location(lpath)
			lopen.insert(0, l)
		if re.match('.*;', line):
			kname, kval = re.match('.*(?:^|{\s*)(\S+)\s(.+);', line).group(1, 2)
			k = Key(kname, kval)
			lopen[0].add(k)
		if re.match('.*}', line):
			closenum = len(re.findall('}', line))
			while closenum > 0:
				if isinstance(lopen[0], Server):
					f.add(lopen[0])
					lopen.pop(0)
				elif isinstance(lopen[0], Location):
					l = lopen[0]
					lopen.pop(0)
					lopen[0].add(l)
				closenum = closenum - 1
		if re.match('\s*#\s*', line):
			c = Comment(re.match('\s*#\s*(.*)$', line).group(1))
			if len(lopen):
				lopen[0].add(c)
			else:
				f.add(c)
	return f

def load(fobj):
	return loads(fobj.read())

def loadf(path):
	return load(open(path, 'r'))

def dumps(obj):
	return ''.join(obj.as_block())

def dump(obj, fobj):
	fobj.write(dumps(obj))
	return fobj

def dumpf(obj, path):
	dump(obj, open(path, 'w'))
	return path
