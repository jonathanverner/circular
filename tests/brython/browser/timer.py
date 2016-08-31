class Timer:
    _timers = {}

    @classmethod
    def run_deferred(cls,elapsed):
        timers = cls._timers.copy()
        for timer in timers.keys():
            if timer.interval < elapsed:
                timer.run()
                timer.clear()


    def __init__(self,meth,interval):
        self._timers[self] = (interval,meth)
        self.interval = interval
        self.meth = meth

    def run(self):
        self.meth()

    def clear(self):
        try:
            del self._timers[self]
        except:
            pass


def set_interval(meth,msec):
    meth()
    return None

def clear_interval(timer):
    return
