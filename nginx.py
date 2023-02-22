"""
Python library for editing NGINX serverblocks.

python-nginx
(c) 2016 Jacob Cook
Licensed under GPLv3, see LICENSE.md
"""

import re
import logging

INDENT = '    '
DEBUG=False

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG if DEBUG else logging.INFO)

class Error(Exception):
    pass


class ParseError(Error):
    pass


def bump_child_depth(obj, depth):
    children = getattr(obj, 'children', [])
    for child in children:
        child._depth = depth + 1
        bump_child_depth(child, child._depth)


class Conf(object):
    """
    Represents an nginx configuration.

    A `Conf` can consist of any number of server blocks, as well as Upstream
    and other types of containers. It can also include top-level comments.
    """

    def __init__(self, *args):
        """
        Initialize object.

        :param *args: Any objects to include in this Conf.
        """
        self.children = list(args)

    def add(self, *args):
        """
        Add object(s) to the Conf.

        :param *args: Any objects to add to the Conf.
        :returns: full list of Conf's child objects
        """
        self.children.extend(args)
        return self.children

    def remove(self, *args):
        """
        Remove object(s) from the Conf.

        :param *args: Any objects to remove from the Conf.
        :returns: full list of Conf's child objects
        """
        for x in args:
            self.children.remove(x)
        return self.children

    def filter(self, btype='', name=''):
        """
        Return child object(s) of this Conf that satisfy certain criteria.

        :param str btype: Type of object to filter by (e.g. 'Key')
        :param str name: Name of key OR container value to filter by
        :returns: full list of matching child objects
        """
        filtered = []
        for x in self.children:
            if name and isinstance(x, Key) and x.name == name:
                filtered.append(x)
            elif isinstance(x, Container) and x.__class__.__name__ == btype \
                    and x.value == name:
                filtered.append(x)
            elif not name and btype and x.__class__.__name__ == btype:
                filtered.append(x)
        return filtered

    @property
    def servers(self):
        """Return a list of child Server objects."""
        return [x for x in self.children if isinstance(x, Server)]

    @property
    def server(self):
        """Convenience property to fetch the first available server only."""
        return self.servers[0]

    @property
    def as_list(self):
        """Return all child objects in nested lists of strings."""
        return [x.as_list for x in self.children]

    @property
    def as_dict(self):
        """Return all child objects in nested dict."""
        return {'conf': [x.as_dict for x in self.children]}

    @property
    def as_strings(self):
        """Return the entire Conf as nginx config strings."""
        ret = []
        for x in self.children:
            if isinstance(x, (Key, Comment)):
                ret.append(x.as_strings)
            else:
                for y in x.as_strings:
                    ret.append(y)
        if ret:
            ret[-1] = re.sub('}\n+$', '}\n', ret[-1])
        return ret


class Container(object):
    """
    Represents a type of child block found in an nginx config.

    Intended to be subclassed by various types of child blocks, like
    Locations or Geo blocks.
    """

    def __init__(self, value, *args):
        """
        Initialize object.

        :param str value: Value to be used in name (e.g. regex for Location)
        :param *args: Any objects to include in this Conf.
        """
        self.name = ''
        self.value = value
        self._depth = 0
        self.children = list(args)
        bump_child_depth(self, self._depth)

    def add(self, *args):
        """
        Add object(s) to the Container.

        :param *args: Any objects to add to the Container.
        :returns: full list of Container's child objects
        """
        self.children.extend(args)
        bump_child_depth(self, self._depth)
        return self.children

    def remove(self, *args):
        """
        Remove object(s) from the Container.

        :param *args: Any objects to remove from the Container.
        :returns: full list of Container's child objects
        """
        for x in args:
            self.children.remove(x)
        return self.children

    def filter(self, btype='', name=''):
        """
        Return child object(s) of this Server block that meet certain criteria.

        :param str btype: Type of object to filter by (e.g. 'Key')
        :param str name: Name of key OR container value to filter by
        :returns: full list of matching child objects
        """
        filtered = []
        for x in self.children:
            if name and isinstance(x, Key) and x.name == name:
                filtered.append(x)
            elif isinstance(x, Container) and x.__class__.__name__ == btype \
                    and x.value == name:
                filtered.append(x)
            elif not name and btype and x.__class__.__name__ == btype:
                filtered.append(x)
        return filtered

    @property
    def locations(self):
        """Return a list of child Location objects."""
        return [x for x in self.children if isinstance(x, Location)]

    @property
    def comments(self):
        """Return a list of child Comment objects."""
        return [x for x in self.children if isinstance(x, Comment)]

    @property
    def keys(self):
        """Return a list of child Key objects."""
        return [x for x in self.children if isinstance(x, Key)]

    @property
    def as_list(self):
        """Return all child objects in nested lists of strings."""
        return [self.name, self.value, [x.as_list for x in self.children]]

    @property
    def as_dict(self):
        """Return all child objects in nested dict."""
        dicts = [x.as_dict for x in self.children]
        return {'{0} {1}'.format(self.name, self.value): dicts}

    @property
    def as_strings(self):
        """Return the entire Container as nginx config strings."""
        ret = []
        container_title = (INDENT * self._depth)
        container_title += '{0}{1} {{\n'.format(
            self.name, (' {0}'.format(self.value) if self.value else '')
        )
        ret.append(container_title)
        for x in self.children:
            if isinstance(x, Key):
                ret.append(INDENT + x.as_strings)
            elif isinstance(x, Comment):
                if x.inline and len(ret) >= 1:
                    ret[-1] = ret[-1].rstrip('\n') + '  ' + x.as_strings
                else:
                    ret.append(INDENT + x.as_strings)
            elif isinstance(x, Container):
                y = x.as_strings
                ret.append('\n' + y[0])
                for z in y[1:]:
                    ret.append(INDENT + z)
            else:
                y = x.as_strings
                ret.append(INDENT + y)
        ret[-1] = re.sub('}\n+$', '}\n', ret[-1])
        ret.append('}\n\n')
        return ret


class Comment(object):
    """Represents a comment in an nginx config."""

    def __init__(self, comment, inline=False):
        """
        Initialize object.

        :param str comment: Value of the comment
        :param bool inline: This comment is on the same line as preceding item
        """
        self.comment = comment
        self.inline = inline

    def __repr__(self):
        return "<nginx.Comment object ({0})>".format(self.comment)

    @property
    def as_list(self):
        """Return comment as nested list of strings."""
        return [self.comment]

    @property
    def as_dict(self):
        """Return comment as dict."""
        return {'#': self.comment}

    @property
    def as_strings(self):
        """Return comment as nginx config string."""
        return '# {0}\n'.format(self.comment)


class Http(Container):
    """Container for HTTP sections in the main NGINX conf file."""

    def __init__(self, *args):
        """Initialize."""
        super(Http, self).__init__('', *args)
        self.name = 'http'


class Server(Container):
    """Container for server block configurations."""

    def __init__(self, *args):
        """Initialize."""
        super(Server, self).__init__('', *args)
        self.name = 'server'

    @property
    def as_dict(self):
        """Return all child objects in nested dict."""
        return {'server': [x.as_dict for x in self.children]}


class Location(Container):
    """Container for Location-based options."""

    def __init__(self, value, *args):
        """Initialize."""
        super(Location, self).__init__(value, *args)
        self.name = 'location'

    def __repr__(self):
        return "<nginx.Location object ({0})>".format(self.value)


class Events(Container):
    """Container for Event-based options."""

    def __init__(self, *args):
        """Initialize."""
        super(Events, self).__init__('', *args)
        self.name = 'events'


class LimitExcept(Container):
    """Container for specifying HTTP method restrictions."""

    def __init__(self, value, *args):
        """Initialize."""
        super(LimitExcept, self).__init__(value, *args)
        self.name = 'limit_except'


class Types(Container):
    """Container for MIME type mapping."""

    def __init__(self, *args):
        """Initialize."""
        super(Types, self).__init__('', *args)
        self.name = 'types'


class If(Container):
    """Container for If conditionals."""

    def __init__(self, value, *args):
        """Initialize."""
        super(If, self).__init__(value, *args)
        self.name = 'if'


class Upstream(Container):
    """Container for upstream configuration (reverse proxy)."""

    def __init__(self, value, *args):
        """Initialize."""
        super(Upstream, self).__init__(value, *args)
        self.name = 'upstream'

    def __repr__(self):
        return "<nginx.Upstream object ({0})>".format(self.value)


class Geo(Container):
    """
    Container for geo module configuration.

    See docs here: http://nginx.org/en/docs/http/ngx_http_geo_module.html
    """

    def __init__(self, value, *args):
        """Initialize."""
        super(Geo, self).__init__(value, *args)
        self.name = 'geo'


class Map(Container):
    """Container for map configuration."""

    def __init__(self, value, *args):
        """Initialize."""
        super(Map, self).__init__(value, *args)
        self.name = 'map'

    def __repr__(self):
        return "<nginx.Map object ({0})>".format(self.value)


class Stream(Container):
    """Container for stream sections in the main NGINX conf file."""

    def __init__(self, *args):
        """Initialize."""
        super(Stream, self).__init__('', *args)
        self.name = 'stream'


class Key(object):
    """Represents a simple key/value object found in an nginx config."""

    def __init__(self, name, value):
        """
        Initialize object.

        :param *args: Any objects to include in this Server block.
        """
        self.name = name
        self.value = value

    def __repr__(self):
        return "<nginx.Key object ({0})>".format(self.name)

    @property
    def as_list(self):
        """Return key as nested list of strings."""
        return [self.name, self.value]

    @property
    def as_dict(self):
        """Return key as dict key/value."""
        return {self.name: self.value}

    @property
    def as_strings(self):
        """Return key as nginx config string."""
        if self.value == '' or self.value is None:
            return '{0};\n'.format(self.name)
        if type(self.value) == str and '"' not in self.value and (';' in self.value or '#' in self.value):
            return '{0} "{1}";\n'.format(self.name, self.value)
        return '{0} {1};\n'.format(self.name, self.value)


def loads(data, conf=True):
    """
    Load an nginx configuration from a provided string.

    :param str data: nginx configuration
    :param bool conf: Load object(s) into a Conf object?
    """
    f = Conf() if conf else []
    lopen = []
    index = 0

    while True:
        m = re.compile(r'^\s*events\s*{').search(data[index:])
        if m:
            log.debug("Open (Events)")
            e = Events()
            lopen.insert(0, e)
            index += m.end()
            continue

        m = re.compile(r'^\s*http\s*{').search(data[index:])
        if m:
            log.debug("Open (Http)")
            h = Http()
            lopen.insert(0, h)
            index += m.end()
            continue

        m = re.compile(r'^\s*stream\s*{').search(data[index:])
        if m:
            log.debug("Open (Stream)")
            s = Stream()
            lopen.insert(0, s)
            index += m.end()
            continue

        m = re.compile(r'^\s*server\s*{').search(data[index:])
        if m:
            log.debug("Open (Server)")
            s = Server()
            lopen.insert(0, s)
            index += m.end()
            continue

        n = re.compile(r'(?!\B"[^"]*);(?![^"]*"\B)')
        m = re.compile(r'^\s*location\s+(.*?".*?".*?|.*?)\s*{').search(data[index:])
        if m and not n.search(m.group()):
            log.debug("Open (Location) {0}".format(m.group(1)))
            l = Location(m.group(1))
            lopen.insert(0, l)
            index += m.end()
            continue

        m = re.compile(r'^\s*if\s+(.*?".*?".*?|.*?)\s*{').search(data[index:])
        if m and not n.search(m.group()):
            log.debug("Open (If) {0}".format(m.group(1)))
            ifs = If(m.group(1))
            lopen.insert(0, ifs)
            index += m.end()
            continue

        m = re.compile(r'^\s*upstream\s+(.*?)\s*{').search(data[index:])
        if m and not n.search(m.group()):
            log.debug("Open (Upstream) {0}".format(m.group(1)))
            u = Upstream(m.group(1))
            lopen.insert(0, u)
            index += m.end()
            continue

        m = re.compile(r'^\s*geo\s+(.*?".*?".*?|.*?)\s*{').search(data[index:])
        if m and not n.search(m.group()):
            log.debug("Open (Geo) {0}".format(m.group(1)))
            g = Geo(m.group(1))
            lopen.insert(0, g)
            index += m.end()
            continue

        m = re.compile(r'^\s*map\s+(.*?".*?".*?|.*?)\s*{').search(data[index:])
        if m and not n.search(m.group()):
            log.debug("Open (Map) {0}".format(m.group(1)))
            g = Map(m.group(1))
            lopen.insert(0, g)
            index += m.end()
            continue

        m = re.compile(r'^\s*limit_except\s+(.*?".*?".*?|.*?)\s*{').search(data[index:])
        if m and not n.search(m.group()):
            log.debug("Open (LimitExcept) {0}".format(m.group(1)))
            l = LimitExcept(m.group(1))
            lopen.insert(0, l)
            index += m.end()
            continue

        m = re.compile(r'^\s*types\s*{').search(data[index:])
        if m:
            log.debug("Open (Types)")
            l = Types()
            lopen.insert(0, l)
            index += m.end()
            continue

        m = re.compile(r'^(\s*)#[ \r\t\f]*(.*?)\n').search(data[index:])
        if m:
            log.debug("Comment ({0})".format(m.group(2)))
            c = Comment(m.group(2), inline='\n' not in m.group(1))
            if lopen and isinstance(lopen[0], Container):
                lopen[0].add(c)
            else:
                f.add(c) if conf else f.append(c)
            index += m.end() - 1
            continue

        m = re.compile(r'^\s*}').search(data[index:])
        if m:
            if isinstance(lopen[0], Container):
                log.debug("Close ({0})".format(lopen[0].__class__.__name__))
                c = lopen[0]
                lopen.pop(0)
                if lopen and isinstance(lopen[0], Container):
                    lopen[0].add(c)
                else:
                    f.add(c) if conf else f.append(c)
            index += m.end()
            continue

        if ";" not in data[index:] and "}" in data[index:]:
            # If there is still something to parse, expect ';' otherwise
            # the Key regexp can get stuck due to regexp catastrophic backtracking
            raise ParseError("Config syntax, missing ';' at index: {}".format(index))

        double = r'\s*"[^"]*"'
        single = r'\s*\'[^\']*\''
        normal = r'\s*[^;\s]*'
        s1 = r'{}|{}|{}'.format(double, single, normal)
        s = r'^\s*({})\s*((?:{})+);'.format(s1, s1)
        m = re.compile(s).search(data[index:])
        if m:
            log.debug("Key {0} {1}".format(m.group(1), m.group(2)))
            k = Key(m.group(1), m.group(2))
            if lopen and isinstance(lopen[0], (Container, Server)):
                lopen[0].add(k)
            else:
                f.add(k) if conf else f.append(k)
            index += m.end()
            continue

        m = re.compile(r'^\s*(\S+);').search(data[index:])
        if m:
            log.debug("Key {0}".format(m.group(1)))
            k = Key(m.group(1), '')
            if lopen and isinstance(lopen[0], (Container, Server)):
                lopen[0].add(k)
            else:
                f.add(k) if conf else f.append(k)
            index += m.end()
            continue

        break

    return f


def load(fobj):
    """
    Load an nginx configuration from a provided file-like object.

    :param obj fobj: nginx configuration
    """
    return loads(fobj.read())


def loadf(path):
    """
    Load an nginx configuration from a provided file path.

    :param file path: path to nginx configuration on disk
    """
    with open(path, 'r') as f:
        return load(f)


def dumps(obj):
    """
    Dump an nginx configuration to a string.

    :param obj obj: nginx object (Conf, Server, Container)
    :returns: nginx configuration as string
    """
    return ''.join(obj.as_strings)


def dump(obj, fobj):
    """
    Write an nginx configuration to a file-like object.

    :param obj obj: nginx object (Conf, Server, Container)
    :param obj fobj: file-like object to write to
    :returns: file-like object that was written to
    """
    fobj.write(dumps(obj))
    return fobj


def dumpf(obj, path):
    """
    Write an nginx configuration to file.

    :param obj obj: nginx object (Conf, Server, Container)
    :param str path: path to nginx configuration on disk
    :returns: path the configuration was written to
    """
    with open(path, 'w') as f:
        dump(obj, f)
    return path
