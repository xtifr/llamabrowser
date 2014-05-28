#
# callback interface, for UIs
#
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

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

# multi-part progress bar stub for download filesets
class NullMultiProgressBar(object):
    """Provide methods for UI multi-part progress bar wrappers."""

    def __init__(self, title, msg, max=1000):
        pass
    def StartPart(self, msg, max=100, msg2=None):
        pass
    def update(self, percent):
        return True
    def Done(self, error=None):
        pass
