class TObserver(object):
    def __init__(self,observer):
        self.events = []
        observer.bind('change',self.handler)

    def handler(self,event):
        self.events.append(event)