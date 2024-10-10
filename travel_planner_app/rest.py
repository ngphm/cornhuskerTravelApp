import base64
import json

from kivy.network.urlrequest import UrlRequest
from urllib.parse import quote


class RESTConnection:
    def __init__(self, authority, port, root_path, username=None, password=None):
        self.authority = authority
        self.port = port
        self.root_path = root_path
        self.headers = {
            'Content-type': 'application/json',
        }
        if username is not None and password is not None:
            credentials = base64.standard_b64encode(f'{username}:{password}'.encode('UTF8')).decode('UTF8')
            self.headers['Authorization'] = f'Basic {credentials}'

    def construct_url(self, resource, get_parameters=None):
        parameter_string = '&'.join(f'{quote(str(key))}={quote(str(value))}' for key, value in get_parameters.items()) \
            if get_parameters is not None else ''
        return f'https://{self.authority}:{self.port}{self.root_path}/{resource}?{parameter_string}'

    def send_request_by_url(self, url, post_parameters, on_success, on_failure, on_error):
        UrlRequest(url, req_headers=self.headers,
                   req_body=json.dumps(post_parameters) if post_parameters is not None else None,
                   on_success=on_success, on_failure=on_failure, on_error=on_error)

    def send_request(self, resource, get_parameters, post_parameters, on_success, on_failure, on_error):
        url = self.construct_url(resource, get_parameters)
        print(url)
        self.send_request_by_url(url, post_parameters, on_success, on_failure, on_error)
