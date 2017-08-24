from Products.Five.browser import BrowserView


class Ping(BrowserView):

    def __call__(self):
        return 'pong'


class InternalServerError(BrowserView):

    def __call__(self):
        raise Exception('Boom')


class SendHundredBytes(BrowserView):

    def __call__(self):
        return 'x' * 100
