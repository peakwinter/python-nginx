import re

class Conf(object):
	def __init__(self, blocks=[]):
		self.blocks = list(blocks)

	def append(self, obj):
		self.blocks.append(obj)
		return self.blocks

	def server(self):
		# Convenience function. Return all Server objects
		ret = []
		for x in self.blocks:
			ret.append(x if isinstance(x, Server) else None)
		return (ret[0] if len(ret) == 1 else (ret if ret else None))

	def get_all(self):
		return self.blocks

	def get_as_list(self):
		ret = []
		for x in self.blocks:
			ret.append(x.get_as_list())
		return ret

	def get_as_block(self):
		ret = []
		for x in self.blocks:
			if isinstance(x, (Key, Comment)):
				ret.append(x.get_as_block())
			else:
				for y in x.get_as_block():
					ret.append(y)
		return ret


class Server(object):
	def __init__(self, blocks=[]):
		self.blocks = list(blocks)

	def append(self, obj):
		self.blocks.append(obj)
		return self.blocks

	def get_all(self):
		return self.blocks

	def get_as_list(self):
		ret = []
		for x in self.blocks:
			ret.append(x.get_as_list())
		return ['server', '', ret]

	def get_as_block(self):
		ret = []
		ret.append('server {\n')
		for x in self.blocks:
			if isinstance(x, (Key, Comment)):
				ret.append('\t' + x.get_as_block())
			elif isinstance(x, Container):
				y = x.get_as_block()
				ret.append('\n\t'+y[0])
				for z in y[1:]:
					ret.append('\t'+z)
		ret.append('}\n')
		return ret


class Container(object):
	def __init__(self, value, blocks=[]):
		self.name = ''
		self.value = value
		self.blocks = list(blocks)

	def append(self, obj):
		self.blocks.append(obj)
		return self.blocks

	def get_all(self):
		return self.blocks

	def get_as_list(self):
		ret = []
		for x in self.blocks:
			ret.append(x.get_as_list())
		return [self.name, self.value, ret]

	def get_as_block(self):
		ret = []
		ret.append(self.name + ' ' + self.value + ' {\n')
		for x in self.blocks:
			if isinstance(x, (Key, Comment)):
				ret.append('\t' + x.get_as_block())
			else:
				y = x.get_as_block()
				ret.append('\t'+y)
		ret.append('}\n\n')
		return ret


class Comment(object):
	def __init__(self, comment):
		self.comment = comment

	def get_as_list(self):
		return [self.comment]

	def get_as_block(self):
		return '# ' + self.comment + '\n'


class Location(Container):
	def __init__(self, value, blocks=[]):
		super(Location, self).__init__(value, blocks)
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

	def get_as_list(self):
		return [self.name, self.value]

	def get_as_block(self):
		return self.name + ' ' + self.value + ';\n'


def test():
	return Server([Comment('This is a test comment'), Key('server_name', 'localhost'),
		Key('root', '/var/www'), Location('/', [Key('test', 'true')])])

def loads(data):
	f = Conf()
	lopen = []
	for line in data.split('\n'):
		if re.match('^\s*server {$', line):
			s = Server()
			lopen.insert(0, s)
		elif re.match('^\s*location .*{$', line):
			lpath = re.match('^\s*location (.*) {$', line).group(1)
			l = Location(lpath)
			lopen.insert(0, l)
		elif re.match('.*}$', line):
			if isinstance(lopen[0], Server):
				f.append(lopen[0])
				lopen.pop(0)
			elif isinstance(lopen[0], Location):
				l = lopen[0]
				lopen.pop(0)
				lopen[0].append(l)
		elif re.match('^\s*# ', line):
			c = Comment(re.match('^\s*# (.*)$', line).group(1))
			if len(lopen):
				lopen[0].append(c)
			else:
				f.append(c)
		elif re.match('.*;$', line):
			kname, kval = re.match('^\s*(.*) (.*);$', line).group(1, 2)
			k = Key(kname, kval)
			lopen[0].append(k)
	return f

def load(fobj):
	return loads(fobj.read())

def loadf(path):
	return load(open(path, 'r'))

def dumps(obj):
	return ''.join(obj.get_as_block())

def dump(obj, fobj):
	fobj.write(dumps(obj))
	return fobj

def dumpf(obj, path):
	dump(obj, open(path, 'w'))
	return path
