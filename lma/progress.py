#
# callback interface, for UIs
#

# create a no-op callback for defaults.
class NullProgressBar(object):
    """Provide these methods for UI progress bar wrappers."""
    def __init__(self, title, msg, max=100, can_cancel=False):
        pass
    def update(self, percent, msg=None):
        return True
    def done(self, error=None):
        pass

class ProgressCallback(object):
    """Interface for hooking progress dialogs."""
    def __init__(self, title, msg, bar=NullProgressBar, frequency = 100):
        """Passed a class for creating a progress bar, plus update frequency"""
        self._title = title
        self._msg = msg
        self._bar = bar
        self._frequency = frequency

    def start(self):
        """Called when starting.  Creates the progress bar."""
        self._dialog = self._bar(self._title, self._msg, 100)

    def update(self, current, total):
        """Called every 'frequency' records."""
        if total == 0:
            # technically we're 100% done
            percent = 100
        else:
            assert current <= total
            percent = (current * 100.0) / total
        self._dialog.update(percent)

    def end(self):
        """Called when done reading records"""
        self._dialog.done()

    @property
    def frequency(self):
        """how many records between calls to update()."""
        return self._frequency
    @frequency.setter
    def frequency(self, value):
        self._frequency = value


