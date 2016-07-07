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
        for x in args:
            self.blocks.remove(x)
        self.upd()
        return self.blocks

    def filter(self, btype='', name=''):
        flist = []
        for x in self.blocks:
            if name and isinstance(x, Key) and x.name == name:
                flist.append(x)
            elif isinstance(x, Container) and x.__class__.__name__ == btype and x.value == name:
                flist.append(x)
            elif not name and btype and x.__class__.__name__ == btype:
                flist.append(x)
        return flist

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

    def as_dict(self):
        return {'conf': [x.as_dict() for x in self.blocks]}

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
        for x in args:
            self.blocks.remove(x)
        self.upd()
        return self.blocks

    def filter(self, btype='', name=''):
        flist = []
        for x in self.blocks:
            if name and isinstance(x, Key) and x.name == name:
                flist.append(x)
            elif isinstance(x, Container) and x.__class__.__name__ == btype and x.value == name:
                flist.append(x)
            elif not name and btype and x.__class__.__name__ == btype:
                flist.append(x)
        return flist

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

    def as_dict(self):
        return {'server': [x.as_dict() for x in self.blocks]}

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
        for x in args:
            self.blocks.remove(x)
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

    def as_dict(self):
        return {'{0} {1}'.format(self.name, self.value): [x.as_dict() for x in self.blocks]}

    def as_block(self):
        ret = []
        ret.append('{0} {1} {{\n'.format(self.name, self.value))
        for x in self.blocks:
            if isinstance(x, (Key, Comment)):
                ret.append(INDENT + x.as_block())
            elif isinstance(x, Container):
                y = x.as_block()
                ret.append('\n'+INDENT+INDENT+y[0])
                for z in y[1:]:
                    ret.append(INDENT+z)
            else:
                y = x.as_block()
                ret.append(INDENT+y)
        ret.append('}\n')
        return ret


class Comment(object):
    def __init__(self, comment):
        self.comment = comment

    def as_list(self):
        return [self.comment]

    def as_dict(self):
        return {'#': self.comment}

    def as_block(self):
        return '# {0}\n'.format(self.comment)


class Location(Container):
    def __init__(self, value, *args):
        super(Location, self).__init__(value, *args)
        self.name = 'location'


class LimitExcept(Container):
    def __init__(self, value, *args):
        super(LimitExcept, self).__init__(value, *args)
        self.name = 'limit_except'


class Types(Container):
    def __init__(self, value, *args):
        super(Types, self).__init__(value, *args)
        self.name = 'types'


class If(Container):
    def __init__(self, value, *args):
        super(If, self).__init__(value, *args)
        self.name = 'if'


class Upstream(Container):
    def __init__(self, value, *args):
        super(Upstream, self).__init__(value, *args)
        self.name = 'upstream'


class Geo(Container):
    """
    Container for geo module configuration
    See docs here: http://nginx.org/en/docs/http/ngx_http_geo_module.html
    """
    def __init__(self, value, *args):
        super(Geo, self).__init__(value, *args)
        self.name = 'geo'


class Key(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def as_list(self):
        return [self.name, self.value]

    def as_dict(self):
        return {self.name: self.value}

    def as_block(self):
        return '{0} {1};\n'.format(self.name, self.value)


def loads(data, conf=True):
    f = Conf() if conf else []
    lopen = []
    for line in data.split('\n'):
        if re.match('\s*server\s*{', line):
            s = Server()
            lopen.insert(0, s)
        if re.match('\s*location.*{', line):
            lpath = re.match('\s*location\s*(.*\S+)\s*{', line).group(1)
            l = Location(lpath)
            lopen.insert(0, l)
        if re.match('\s*if.*{', line):
            ifs = re.match('\s*if\s*(.*\S+)\s*{', line).group(1)
            ifs = If(ifs)
            lopen.insert(0, ifs)
        if re.match('\s*upstream.*{', line):
            ups = re.match('\s*upstream\s*(.*\S+)\s*{', line).group(1)
            u = Upstream(ups)
            lopen.insert(0, u)
        if re.match('\s*geo\s*\$.*\s{', line):
            geo = re.match('\s*geo\s+(\$.*)\s{', line).group(1)
            s = Geo(geo)
            lopen.insert(0, s)
        if re.match('.*;', line):
            kname, kval = re.match('.*(?:^|^\s*|{\s*)(\S+)\s(.+);', line).group(1, 2)
            if "#" not in kname:
                k = Key(kname, kval)
                lopen[0].add(k)
        if re.match('.*}', line):
            closenum = len(re.findall('}', line))
            while closenum > 0:
                if isinstance(lopen[0], Server):
                    f.add(lopen[0]) if conf else f.append(lopen[0])
                    lopen.pop(0)
                elif isinstance(lopen[0], Container):
                    c = lopen[0]
                    lopen.pop(0)
                    if lopen:
                        lopen[0].add(c)
                    else:
                        f.add(c) if conf else f.append(c)
                closenum = closenum - 1
        if re.match('\s*#\s*', line):
            c = Comment(re.match('\s*#\s*(.*)$', line).group(1))
            if len(lopen):
                lopen[0].add(c)
            else:
                f.add(c) if conf else f.append(c)
    return f

def load(fobj):
    return loads(fobj.read())

def loadf(path):
    with open(path, 'r') as f:
        return load(f)

def dumps(obj):
    return ''.join(obj.as_block())

def dump(obj, fobj):
    fobj.write(dumps(obj))
    return fobj

def dumpf(obj, path):
    with open(path, 'w') as f:
        dump(obj, f)
    return path
