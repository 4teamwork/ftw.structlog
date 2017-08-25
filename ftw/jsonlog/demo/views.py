from plone.rest import Service
from Products.Five.browser import BrowserView
import json


class Ping(BrowserView):

    def __call__(self):
        return 'pong'


class InternalServerError(BrowserView):

    def __call__(self):
        raise Exception('Boom')


class Unauthorized(BrowserView):

    def __call__(self):
        self.request.response.setStatus(401)


class Redirect(BrowserView):

    def __call__(self):
        target = self.context.absolute_url() + '/@@ping'
        return self.request.response.redirect(target)


class SendHundredBytes(BrowserView):

    def __call__(self):
        return 'x' * 100


class RESTEndpoint(Service):

    def render(self):
        self.request.response.setHeader("Content-Type", "application/json")
        return json.dumps({'status': 'ok'})
