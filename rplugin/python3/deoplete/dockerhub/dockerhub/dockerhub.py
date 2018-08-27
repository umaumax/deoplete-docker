# Copyright 2016 Koichi Shiraishi. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

try:
    import ujson as json
except ImportError:
    import json
import certifi
import urllib3
import os


class DockerHub(object):

    def __init__(self, url=None, version=None):
        self.version = version or 'v2'
        self.url = url or '{0}/{1}'.format(
            'https://hub.docker.com', self.version
        )
        option = {'cert_reqs': 'CERT_REQUIRED', 'ca_certs': certifi.where()}
        http_proxy = os.getenv("http_proxy")
        self.http = urllib3.ProxyManager(http_proxy, **option) if http_proxy else urllib3.PoolManager(**option)

    def _request(self, path):
        return self.http.request('GET', '{0}/{1}/'.format(self.url, path))

    def search(self, user):
        next = None
        resp = self._request('repositories/{0}'.format(user)).data.decode('utf8')

        while True:
            if next:
                resp = self.http.request('GET', next).data.decode('utf8')

            resp = json.loads(resp)

            for i in resp['results']:
                yield i

            if resp['next']:
                next = resp['next']
                continue

            return

    def tags(self, image):
        user = 'library'
        if '/' in image:
            user, image = image.split('/', 1)

        r = self._request('repositories/{0}/{1}/tags'.format(user, image))
        status = r.status
        if status == 200:
            return json.loads(r.data.decode('utf8'))['results']
        elif status == 404:
            raise ValueError(
                '{0}{1} repository does not exist'.format(user, image)
            )
        else:
            raise ConnectionError(
                '{0} download failed with status {1}'.format(image, status)
            )
