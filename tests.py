"""
Testing module for python-nginx.

python-nginx
(c) 2016 Jacob Cook
Licensed under GPLv3, see LICENSE.md
"""

import nginx
import unittest


TESTBLOCK = """
upstream php {
    server unix:/tmp/php-fcgi.socket;
}
server {
    listen 80;  # This comment should be present;
    # And this one
    server_name localhost 127.0.0.1;
    root /srv/http;  # And also this one
    mykey "myvalue; #notme myothervalue";
    # This one too
    index index.php;

    location ~ \.php(?:$|/) {
        fastcgi_pass php;
    }
}
"""

MESSYBLOCK = """
# This is an example of a messy config
upstream php { server unix:/tmp/php-cgi.socket; }
server { server_name localhost; #this is the server server_name
location /{ test_key test_value; }}
"""


class TestPythonNginx(unittest.TestCase):
    def test_basic_load(self):
        self.assertTrue(nginx.loads(TESTBLOCK) is not None)

    def test_messy_load(self):
        data = nginx.loads(MESSYBLOCK)
        self.assertTrue(data is not None)
        self.assertTrue(len(data.server.comments), 1)
        self.assertTrue(len(data.server.locations), 1)

    def test_comment_parse(self):
        data = nginx.loads(TESTBLOCK)
        self.assertEquals(len(data.server.comments), 4)
        self.assertEquals(data.server.comments[2].comment, 'And also this one')

    def test_key_parse(self):
        data = nginx.loads(TESTBLOCK)
        self.assertEquals(len(data.server.keys), 5)
        firstKey = data.server.keys[0]
        thirdKey = data.server.keys[3]
        self.assertEquals(firstKey.name, 'listen')
        self.assertEquals(firstKey.value, '80')
        self.assertEquals(thirdKey.name, 'mykey')
        self.assertEquals(thirdKey.value, '"myvalue; #notme myothervalue"')

    def test_location_parse(self):
        data = nginx.loads(TESTBLOCK)
        self.assertEquals(len(data.server.locations), 1)
        firstLoc = data.server.locations[0]
        self.assertEquals(firstLoc.value, '~ \.php(?:$|/)')
        self.assertEquals(len(firstLoc.keys), 1)

    def test_reflection(self):
        inp_data = nginx.loads(TESTBLOCK)
        out_data = '\n' + nginx.dumps(inp_data)
        self.assertEqual(TESTBLOCK, out_data)


if __name__ == '__main__':
    unittest.main()
