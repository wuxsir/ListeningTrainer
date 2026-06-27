"""
Vercel Serverless入口 - 适配Flask应用
"""
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import parse_qs, urlparse
import json

# 导入Flask应用
from app import app


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless处理程序"""

    def do_GET(self):
        self._handle_request('GET')

    def do_POST(self):
        self._handle_request('POST')

    def do_PUT(self):
        self._handle_request('PUT')

    def do_DELETE(self):
        self._handle_request('DELETE')

    def do_OPTIONS(self):
        self._handle_request('OPTIONS')

    def _handle_request(self, method):
        """处理HTTP请求并转发给Flask应用"""
        try:
            # 解析URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_string = parsed_url.query

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''

            # 构建环境变量
            environ = {
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'QUERY_STRING': query_string,
                'SERVER_NAME': self.headers.get('Host', 'localhost').split(':')[0],
                'SERVER_PORT': '443',
                'HTTP_HOST': self.headers.get('Host', 'localhost'),
                'CONTENT_TYPE': self.headers.get('Content-Type', ''),
                'CONTENT_LENGTH': str(content_length),
                'wsgi.input': BytesIO(body),
                'wsgi.errors': BytesIO(),
                'wsgi.version': (1, 0),
                'wsgi.run_once': True,
                'wsgi.url_scheme': 'https',
                'wsgi.multithread': False,
                'wsgi.multiprocess': True,
            }

            # 添加所有HTTP头
            for header, value in self.headers.items():
                key = f'HTTP_{header.upper().replace("-", "_")}'
                environ[key] = value

            # 调用Flask应用
            response = app(environ, self._start_response)

            # 发送响应
            for chunk in response:
                self.wfile.write(chunk)

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())

    def _start_response(self, status, headers):
        """WSGI start_response回调"""
        status_code = int(status.split(' ')[0])
        self.send_response(status_code)
        for header, value in headers:
            self.send_header(header, value)
        self.end_headers()
        return self.wfile.write
