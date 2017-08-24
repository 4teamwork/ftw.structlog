from Products.Five.browser import BrowserView


class Ping(BrowserView):

    def __call__(self):
        return 'pong'
