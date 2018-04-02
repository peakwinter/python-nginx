"""
Testing module for python-nginx.

python-nginx
(c) 2016 Jacob Cook
Licensed under GPLv3, see LICENSE.md
"""

# flake8: noqa

import nginx
import unittest


TESTBLOCK_CASE_1 = """
include conf.d/pre/*.cfg;
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

TESTBLOCK_CASE_2 = """
upstream php
{
    server unix:/tmp/php-fcgi.socket;
}
server
{
listen 80;  # This comment should be present;
    # And this one
    server_name localhost 127.0.0.1;
root /srv/http;  # And also this one
    mykey "myvalue; #notme myothervalue";
     "quoted_key" "quoted_value";
    # This one too
    index index.php;
if (!-e $request_filename)
{
    rewrite ^(.+)$ /index.php?q=$1 last;
}

if (!-e $request_filename) {
    rewrite ^(.+)$ /index.php?q=$1 last;
}
    location ~ \.php(?:$|/) {
        fastcgi_pass php;
    }

    # location from the issue #10
     location / {
return 301 $scheme://$host:$server_port${request_uri}bitbucket/;
 }
}
"""

TESTBLOCK_CASE_3="""
upstream test0 {
    ip_hash;
    server 127.0.0.1:8080;
    keepalive 16;
}
upstream test1{
    server 127.0.0.2:8080;
    keepalive 16;
}
upstream test2
{
    server 127.0.0.3:8080;
    keepalive 16;
}

server {
    listen       80;
    server_name  example.com;

    location = /
    {
        root html;
    }
}
"""

TESTBLOCK_CASE_4 = """
# This is an example of a messy config
upstream php { server unix:/tmp/php-cgi.socket; }
server { server_name localhost; #this is the server server_name
location /{ test_key test_value; }}
"""


TESTBLOCK_CASE_5 = """
upstream test0 {
    server 1.1.1.1:8080;
    send "some request";
}

upstream test1 {
    server 1.1.1.1:8080;
    send 'some request';
}

server {
    server_name "www.example.com";

    location / {
        root html;
    }
}
"""

TESTBLOCK_CASE_6 = """
upstream test0 {
    server 1.1.1.1:8080;
    check interval=3000 rise=2 fall=3 timeout=3000 type=http;
    check_http_send "GET /alive.html  HTTP/1.0";
    check_http_expect_alive http_2xx http_3xx;
}

upstream test1 {
    ip_hash;
    server 2.2.2.2:9000;
    check_http_send 'GET /alive.html  HTTP/1.0';
}
"""

TESTBLOCK_CASE_7 = """
upstream xx.com_backend {
    server 10.193.2.2:9061 weight=1 max_fails=2 fail_timeout=30s;
    server 10.193.2.1:9061 weight=1 max_fails=2 fail_timeout=30s;
    session_sticky;
}

server {
    listen 80;

    location / {
        set $xlocation 'test';
        proxy_pass http://xx.com_backend;
    }
}
"""

TESTBLOCK_CASE_8 = r"""
server {
    double_qoted "GET /alive.html  HTTP/1.0\r\n\r\n";
    single_quoted 'GET /alive.html  HTTP/1.0\r\n\r\n';
    two_keys "\n \t";
    "\nthree" "\rkeys" '\tkeys';
    different_chars "\n\r\t\x01\x02\x03";
}
"""


class TestPythonNginx(unittest.TestCase):
    def test_basic_load(self):
        self.assertTrue(nginx.loads(TESTBLOCK_CASE_1) is not None)

    def test_messy_load(self):
        data = nginx.loads(TESTBLOCK_CASE_4)
        self.assertTrue(data is not None)
        self.assertTrue(1, len(data.server.comments))
        self.assertTrue(1, len(data.server.locations))

    def test_comment_parse(self):
        data = nginx.loads(TESTBLOCK_CASE_1)
        self.assertEqual(4, len(data.server.comments))
        self.assertEqual('And also this one', data.server.comments[2].comment)

    def test_key_parse(self):
        data = nginx.loads(TESTBLOCK_CASE_1)
        self.assertEqual(5, len(data.server.keys))
        firstKey = data.server.keys[0]
        thirdKey = data.server.keys[3]
        self.assertEqual('listen', firstKey.name)
        self.assertEqual('80', firstKey.value)
        self.assertEqual('mykey', thirdKey.name)
        self.assertEqual('"myvalue; #notme myothervalue"', thirdKey.value)

    def test_key_parse_complex(self):
        data = nginx.loads(TESTBLOCK_CASE_2)
        self.assertEqual(6, len(data.server.keys))
        firstKey = data.server.keys[0]
        thirdKey = data.server.keys[3]
        fourthKey = data.server.keys[4]
        self.assertEqual('listen', firstKey.name)
        self.assertEqual('80', firstKey.value)
        self.assertEqual('mykey', thirdKey.name)
        self.assertEqual('"myvalue; #notme myothervalue"', thirdKey.value)
        self.assertEqual(
            "301 $scheme://$host:$server_port${request_uri}bitbucket/",
            data.server.locations[-1].keys[0].value
        )
        self.assertEqual('"quoted_key"', fourthKey.name)
        self.assertEqual('"quoted_value"', fourthKey.value)

    def test_location_parse(self):
        data = nginx.loads(TESTBLOCK_CASE_1)
        self.assertEqual(1, len(data.server.locations))
        firstLoc = data.server.locations[0]
        self.assertEqual('~ \.php(?:$|/)', firstLoc.value)
        self.assertEqual(1, len(firstLoc.keys))

    def test_brace_position(self):
        data = nginx.loads(TESTBLOCK_CASE_3)
        self.assertEqual(3, len(data.filter('Upstream')))

    def test_single_value_keys(self):
        data = nginx.loads(TESTBLOCK_CASE_3)
        single_value_key = data.filter('Upstream')[0].keys[0]
        self.assertEqual('ip_hash', single_value_key.name)
        self.assertEqual('', single_value_key.value)

    def test_reflection(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_1)
        out_data = '\n' + nginx.dumps(inp_data)
        self.assertEqual(TESTBLOCK_CASE_1, out_data)

    def test_quoted_key_value(self):
        data = nginx.loads(TESTBLOCK_CASE_5)
        out_data = '\n' + nginx.dumps(data)
        self.assertEqual(TESTBLOCK_CASE_5, out_data)

    def test_complex_upstream(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_6)
        out_data = '\n' + nginx.dumps(inp_data)
        self.assertEqual(TESTBLOCK_CASE_6, out_data)

    def test_session_sticky(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_7)
        out_data = '\n' + nginx.dumps(inp_data)
        self.assertEqual(TESTBLOCK_CASE_7, out_data)

    def test_filtering(self):
        data = nginx.loads(TESTBLOCK_CASE_1)
        self.assertEqual(len(data.server.filter('Key', 'mykey')), 1)
        self.assertEqual(data.server.filter('Key', 'nothere'), [])

    def test_special_chars(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_8)
        out_data = '\n' + nginx.dumps(inp_data)
        self.assertEqual(TESTBLOCK_CASE_8, out_data)


if __name__ == '__main__':
    unittest.main()
