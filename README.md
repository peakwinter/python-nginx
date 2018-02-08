## python-nginx

[![](https://travis-ci.org/peakwinter/python-nginx.svg?branch=master)](https://travis-ci.org/peakwinter/python-nginx)

A module for easily creating and modifying nginx serverblock configurations in Python (including comments!).

### Install

    pip install python-nginx

### Examples

Create an nginx serverblock and save it to file:

    >>> import nginx
    >>> c = nginx.Conf()
    >>> u = nginx.Upstream('php',
    ...     nginx.Key('server', 'unix:/tmp/php-fcgi.socket')
    ...	)
    >>> c.add(u)
    >>> s = nginx.Server()
    >>> s.add(
    ...     nginx.Key('listen', '80'),
    ...     nginx.Comment('Yes, python-nginx can read/write comments!'),
    ...     nginx.Key('server_name', 'localhost 127.0.0.1'),
    ...     nginx.Key('root', '/srv/http'),
    ...     nginx.Key('index', 'index.php'),
    ...     nginx.Location('= /robots.txt',
    ...          nginx.Key('allow', 'all'),
    ...          nginx.Key('log_not_found', 'off'),
    ...          nginx.Key('access_log', 'off')
    ...     )
    ...     nginx.Location('~ \.php$',
    ...          nginx.Key('include', 'fastcgi.conf'),
    ...          nginx.Key('fastcgi_intercept_errors', 'on'),
    ...          nginx.Key('fastcgi_pass', 'php')
    ...     )
    ... )
    >>> c.add(s)
    >>> nginx.dumpf(c, '/etc/nginx/sites-available/mysite')

Load an nginx serverblock from a file:

    >>> import nginx
    >>> c = nginx.loadf('/etc/nginx/sites-available/testsite')
    >>> c.children
    [<main.Server object at 0x7f1ed4573890>]
    >>> c.server.children
    [<main.Comment object at 0x7f1ed45736d0>, <main.Key object at 0x7f1ed4573750>, <main.Key object at 0x7f1ed4573790>, <main.Location object at 0x7f1ed4573850>]
    >>> c.as_dict
    {'conf': [{'server': [{'#': 'This is a test comment'}, {'server_name': 'localhost'}, {'root': '/srv/http'}, {'location /': [{'allow': 'all'}]}]}]}

Format an nginx serverblock into a string (change the amount of spaces (or tabs) for each indentation level by modifying `nginx.INDENT` first):

    >>> c.servers
    [<main.Server object at 0x7f1ed4573890>]
    >>> c.as_strings
    ['server {\n', '    # This is a test comment\n', '    server_name localhost;\n', '    root /srv/http;\n', '\n    location / {\n', '        allow all;\n', '    }\n\n', '}\n']

Find where you put your keys:

    >>> import nginx
    >>> c = nginx.loadf('/etc/nginx/sites-available/testsite')
    >>> c.filter('Server')
    [<main.Server object at 0x7f1ed4573890>]
    >>> c.filter('Server')[0].filter('Key', 'root')
    [<main.Key object at 0x7f1ed4573790>]
    >>> c.filter('Server')[0].filter('Location')
    [<main.Location object at 0x7f1ed4573850>]

Or just get everything by its type:

    >>> import nginx
    >>> c = nginx.loadf('/etc/nginx/sites-available/testsite')
    >>> c.servers
    [<main.Server object at 0x7f1ed4573890>]
    >>> c.servers[0].keys
    [<main.Key object at 0x7f1ed4573750>, <main.Key object at 0x7f1ed4573790>]
