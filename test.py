import main as nginx

def test():
	return nginx.Conf(nginx.Server(nginx.Comment('This is a test comment'), nginx.Key('server_name', 'localhost'),
		nginx.Key('root', '/var/www'), nginx.Location('/', nginx.Key('test', 'true'), nginx.Key('test2', 'false'))))

def messy():
	return nginx.loads("""
		# This is an example of a messy config
		upstream php { server unix:/tmp/php-cgi.socket; }
		server { server_name localhost; #this is the server server_name
		location /{ test_key test_value; }}
		""")
