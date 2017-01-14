"""
Python library for editing NGINX serverblocks.

python-nginx
(c) 2016 Jacob Cook
Licensed under GPLv3, see LICENSE.md
"""

import re

INDENT = '    '


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
            elif isinstance(x, Container) and x.__class__.__name__ == btype\
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
        return ret


class Server(object):
    """
    Represents an nginx server block.

    A `Server` contains a list of key-values used to set up the web server
    for a particular site. Can also contain other objects like Location blocks.
    """

    def __init__(self, *args):
        """
        Initialize object.

        :param *args: Any objects to include in this Server block.
        """
        self.children = list(args)

    def add(self, *args):
        """
        Add object(s) to the Server block.

        :param *args: Any objects to add to the Server block.
        :returns: full list of Server block's child objects
        """
        self.children.extend(args)
        return self.children

    def remove(self, *args):
        """
        Remove object(s) from the Server block.

        :param *args: Any objects to remove from the Server block.
        :returns: full list of Server block's child objects
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
            elif isinstance(x, Container) and x.__class__.__name__ == btype\
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
        return ['server', '', [x.as_list for x in self.children]]

    @property
    def as_dict(self):
        """Return all child objects in nested dict."""
        return {'server': [x.as_dict for x in self.children]}

    @property
    def as_strings(self):
        """Return the entire Server block as nginx config strings."""
        ret = []
        ret.append('server {\n')
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
                ret.append('\n' + INDENT + y[0])
                for z in y[1:]:
                    ret.append(INDENT+z)
        ret.append('}\n')
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
        self.children = list(args)

    def add(self, *args):
        """
        Add object(s) to the Container.

        :param *args: Any objects to add to the Container.
        :returns: full list of Container's child objects
        """
        self.children.extend(args)
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
        ret.append('{0} {1} {{\n'.format(self.name, self.value))
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
                ret.append('\n' + INDENT + INDENT + y[0])
                for z in y[1:]:
                    ret.append(INDENT + z)
            else:
                y = x.as_strings
                ret.append(INDENT + y)
        ret.append('}\n')
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


class Location(Container):
    """Container for Location-based options."""

    def __init__(self, value, *args):
        """Initialize."""
        super(Location, self).__init__(value, *args)
        self.name = 'location'


class LimitExcept(Container):
    """Container for specifying HTTP method restrictions."""

    def __init__(self, value, *args):
        """Initialize."""
        super(LimitExcept, self).__init__(value, *args)
        self.name = 'limit_except'


class Types(Container):
    """Container for MIME type mapping."""

    def __init__(self, value, *args):
        """Initialize."""
        super(Types, self).__init__(value, *args)
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


class Geo(Container):
    """
    Container for geo module configuration.

    See docs here: http://nginx.org/en/docs/http/ngx_http_geo_module.html
    """

    def __init__(self, value, *args):
        """Initialize."""
        super(Geo, self).__init__(value, *args)
        self.name = 'geo'


class Key(object):
    """Represents a simple key/value object found in an nginx config."""

    def __init__(self, name, value):
        """
        Initialize object.

        :param *args: Any objects to include in this Server block.
        """
        self.name = name
        self.value = value

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
        return '{0} {1};\n'.format(self.name, self.value)


def loads(data, conf=True):
    """
    Load an nginx configuration from a provided string.

    :param str data: nginx configuration
    :param bool conf: Load object(s) into a Conf object?
    """
    f = Conf() if conf else []
    lopen = []
    for line in data.split('\n'):
        line_outside_quotes = re.sub(r'"([^"]+)"|\'([^\']+)\'|\\S+', '', line)
        if re.match(r'\s*server\s*{', line):
            s = Server()
            lopen.insert(0, s)
        if re.match(r'\s*location.*{', line):
            lpath = re.match(r'\s*location\s*(.*\S+)\s*{', line).group(1)
            l = Location(lpath)
            lopen.insert(0, l)
        if re.match(r'\s*if.*{', line):
            ifs = re.match('\s*if\s*(.*\S+)\s*{', line).group(1)
            ifs = If(ifs)
            lopen.insert(0, ifs)
        if re.match(r'\s*upstream.*{', line):
            ups = re.match(r'\s*upstream\s*(.*\S+)\s*{', line).group(1)
            u = Upstream(ups)
            lopen.insert(0, u)
        if re.match(r'\s*geo\s*\$.*\s{', line):
            geo = re.match('\s*geo\s+(\$.*)\s{', line).group(1)
            s = Geo(geo)
            lopen.insert(0, s)
        if re.match(r'.*;', line):
            cmt_regex = r'(.*)#\s*(?![^\'\"]*[\'\"])'
            key_regex = r'.*(?:^|^\s*|{\s*)(\S+)\s(.+);'
            to_eval = line
            if re.match(cmt_regex, line):
                to_eval = re.match(cmt_regex, line).group(1)
            if re.match(key_regex, to_eval):
                kname, kval = re.match(key_regex, to_eval).group(1, 2)
                if "#" not in kname:
                    k = Key(kname, kval)
                    lopen[0].add(k)
        if re.match(r'.*}', line_outside_quotes):
            closenum = len(re.findall('}', line_outside_quotes))
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
        if re.match(r'.*#\s*(?![^\'\"]*[\'\"])', line):
            cmt_regex = r'.*#\s*(.*)(?![^\'\"]*[\'\"])'
            c = Comment(re.match(cmt_regex, line).group(1),
                        inline=not re.match(r'^\s*#.*', line))
            if len(lopen):
                lopen[0].add(c)
            else:
                f.add(c) if conf else f.append(c)
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
