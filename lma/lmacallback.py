#
# callback interface, for UIs
#
class BaseProgressCallback(object):
    """Base class (interface) for hooking UI-specific progress meters.

    To make a version for a specific UI, create versions of the
    start(), update(cur,total), and end() methods."""
    def __init__(self, frequency = 100):
        """frequency argument defines how many records between updates."""
        self._frequency = frequency

    @property
    def frequency(self):
        """how many records between calls to update()."""
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        self._frequency = value

    def start(self):
        """Called when starting.  Override this for your UI."""
        pass

    def update(self, current, total):
        """Called every 'frequency' records.  Override this for your UI."""
        pass

    def end(self):
        """Called when done reading records.  Override this for your UI."""
        pass

# create a no-op callback for defaults.
nil_callback = BaseProgressCallback()
