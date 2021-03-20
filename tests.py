"""
Testing module for python-nginx.

python-nginx
(c) 2016 Jacob Cook
Licensed under GPLv3, see LICENSE.md
"""

# flake8: noqa
import pytest

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
    check_http_send "GET /alive.html  HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx http_3xx;
}

upstream test1 {
    ip_hash;
    server 2.2.2.2:9000;
    check_http_send 'GET /alive.html  HTTP/1.0\r\n\r\n';
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

TESTBLOCK_CASE_8 = """
location /M01 {
    proxy_pass http://backend;
    limit_except GET POST {deny all;}
}
"""

TESTBLOCK_CASE_9 = """
location test9 {
    add_header X-XSS-Protection "1;mode-block";
}

if ( $http_user_agent = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)" ) {
    return 403;
}

location ~* ^/portal {
    proxy_set_header Connection "";
    rewrite ^/portal(.*) $1 break;
}
"""

TESTBLOCK_CASE_10 = """
types {
    application/CEA                                 cea;
    application/cellml+xml                          cellml cml;
    application/clue_info+xml                       clue;
    application/cms                                 cmsc;
}
"""

TESTBLOCK_CASE_11 = """
server{
    listen 80;
    #OPEN-PORT-443
    listen 443 ssl;
    server_name www.xxx.com;
    root /wwww/wwww;

    location ~ .*\.(js|css)?$ {
        expires 12h;
        error_log off;
        access_log /dev/null  # MISSING SEMICOLON
    }
}
"""

TESTBLOCK_CASE_12 = """
server {
    listen 80;
    server_name test.example.com;

    location ~ "^/(test|[0-9a-zA-Z]{6})$" {
        if ($query_string ~ pid=(111)) {
            return 403;
        }

        proxy_pass http://127.0.0.1:81;
    }
}
"""

TESTBLOCK_CASE_13 = """
server{
}"""

TESTBLOCK_CASE_14 = """user  nginx;"""


class TestPythonNginx(unittest.TestCase):
    def test_basic_load(self):
        self.assertTrue(nginx.loads(TESTBLOCK_CASE_1) is not None)

    def test_messy_load(self):
        data = nginx.loads(TESTBLOCK_CASE_4)
        self.assertTrue(data is not None)
        self.assertTrue(len(data.server.comments), 1)
        self.assertTrue(len(data.server.locations), 1)

    def test_comment_parse(self):
        data = nginx.loads(TESTBLOCK_CASE_1)
        self.assertEqual(len(data.server.comments), 4)
        self.assertEqual(data.server.comments[2].comment, 'And also this one')

    def test_key_parse(self):
        data = nginx.loads(TESTBLOCK_CASE_1)
        self.assertEqual(len(data.server.keys), 5)
        firstKey = data.server.keys[0]
        thirdKey = data.server.keys[3]
        self.assertEqual(firstKey.name, 'listen')
        self.assertEqual(firstKey.value, '80')
        self.assertEqual(thirdKey.name, 'mykey')
        self.assertEqual(thirdKey.value, '"myvalue; #notme myothervalue"')

    def test_key_parse_complex(self):
        data = nginx.loads(TESTBLOCK_CASE_2)
        self.assertEqual(len(data.server.keys), 6)
        firstKey = data.server.keys[0]
        thirdKey = data.server.keys[3]
        fourthKey = data.server.keys[4]
        self.assertEqual(firstKey.name, 'listen')
        self.assertEqual(firstKey.value, '80')
        self.assertEqual(thirdKey.name, 'mykey')
        self.assertEqual(thirdKey.value, '"myvalue; #notme myothervalue"')
        self.assertEqual(
            data.server.locations[-1].keys[0].value,
            "301 $scheme://$host:$server_port${request_uri}bitbucket/"
        )
        self.assertEqual(fourthKey.name, '"quoted_key"')
        self.assertEqual(fourthKey.value, '"quoted_value"')

    def test_location_parse(self):
        data = nginx.loads(TESTBLOCK_CASE_1)
        self.assertEqual(len(data.server.locations), 1)
        firstLoc = data.server.locations[0]
        self.assertEqual(firstLoc.value, '~ \.php(?:$|/)')
        self.assertEqual(len(firstLoc.keys), 1)

    def test_brace_position(self):
        data = nginx.loads(TESTBLOCK_CASE_3)
        self.assertEqual(len(data.filter('Upstream')), 3)

    def test_single_value_keys(self):
        data = nginx.loads(TESTBLOCK_CASE_3)
        single_value_key = data.filter('Upstream')[0].keys[0]
        self.assertEqual(single_value_key.name, 'ip_hash')
        self.assertEqual(single_value_key.value, '')

    def test_reflection(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_1)
        out_data = '\n' + nginx.dumps(inp_data)
        self.assertEqual(TESTBLOCK_CASE_1, out_data)

    def test_quoted_key_value(self):
        data = nginx.loads(TESTBLOCK_CASE_5)
        out_data = '\n' + nginx.dumps(data)
        self.assertEqual(out_data, TESTBLOCK_CASE_5)

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

    def test_limit_expect(self):
        data = nginx.loads(TESTBLOCK_CASE_8)
        self.assertEqual(len(data.filter("Location")), 1)
        self.assertEqual(len(data.filter("Location")[0].children), 2)
        self.assertEqual(len(data.filter("Location")[0].filter("LimitExcept")), 1)
        limit_except = data.filter("Location")[0].filter("LimitExcept")[0]
        self.assertEqual(limit_except.value, "GET POST")
        self.assertEqual(len(limit_except.children), 1)
        first_key = limit_except.filter("Key")[0]
        self.assertEqual(first_key.name, "deny")
        self.assertEqual(first_key.value, "all")

    def test_key_value_quotes(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_9)
        self.assertEqual(len(inp_data.filter("Location")), 2)
        location_children = inp_data.filter("Location")[0].children
        self.assertEqual(len(location_children), 1)
        self.assertEqual(location_children[0].name, "add_header")
        self.assertEqual(location_children[0].value, 'X-XSS-Protection "1;mode-block"')
        self.assertEqual(len(inp_data.filter("If")), 1)
        self.assertEqual(inp_data.filter("If")[0].value, "( $http_user_agent = \"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)\" )")
        self.assertEqual(inp_data.filter("Location")[1].filter("Key", "proxy_set_header")[0].value, "Connection \"\"")

    def test_types_block(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_10)
        self.assertEqual(len(inp_data.filter("Types")), 1)
        self.assertEqual(len(inp_data.filter("Types")[0].children), 4)
        self.assertEqual(len(inp_data.filter("Types")[0].filter("Key")), 4)
        data_type = inp_data.filter("Types")[0].filter("Key")[0]
        self.assertEqual(data_type.value, "cea")

    def test_missing_semi_colon(self):
        with pytest.raises(nginx.ParseError) as e:
            nginx.loads(TESTBLOCK_CASE_11)
        self.assertEqual(str(e.value), "Config syntax, missing ';' at index: 189")

    def test_brace_inside_block_param(self):
        inp_data = nginx.loads(TESTBLOCK_CASE_12)
        self.assertEqual(len(inp_data.server.filter("Location")), 1)
        self.assertEqual(inp_data.server.filter("Location")[0].value, "~ \"^/(test|[0-9a-zA-Z]{6})$\"")

    def test_server_without_last_linebreak(self):
        self.assertTrue(nginx.loads(TESTBLOCK_CASE_13) is not None)
        self.assertTrue(nginx.loads(TESTBLOCK_CASE_14) is not None)


if __name__ == '__main__':
    unittest.main()
