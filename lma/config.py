#!/usr/bin/env python
"""Find and process any user configuration for the LMA access.

This still needs a better cross-platform way to find a place to
store user data that isn't specific to an application, since this
library can, in theory, be used by different application, but
nobody would want two copies of the database.  *sigh*"""

import sys, os

# configuration items include:
# path to store lossless files
# path to store lossy files
# flag to autoconvert convert shn to flac

# for the paths, we need to know stuff about how to form a
# unique path depending on the artist name, concert name, etc.

# this all gets even messier when you consider platform independence
# Q: how does rhythmbox do it?
# A: a list of Artist/, Album/, Artist - Album/, Artist/Album/ and
#    Artist/Artist - Album/.

# for now, we'll hard-code to my preferences.

class Config(object):
    """Create a configuration object."""
    _dir = None
    def __init__(self, datadir=None):
        """Return the singleton.  Must be initialized with a path.
        
        if no path was provided on the first call to __init__,
        will throw ValueError."""
        if Config._dir != None:
            return
        if datadir == None:
            raise ValueError("class 'lma.Config' has no data directory.")
        Config._dir = os.path.abspath(os.path.expanduser(datadir))
        if not os.path.isdir(Config._dir):
            os.makedirs(Config._dir)
    def path(self, f):
        """Returns the path to the given file in the config dir"""
        return os.path.join(Config._dir, f)
    def dbpath(self):
        """Returns the path to the database file."""
        return self.path("lma.db")
    def lossless_path(self, artist, concert):
        """Return the path where flac/shn files should go."""
        return os.path.join("~/pub/etree/new", concert.lmaid)
    def lossy_path(self, artist, concert):
        """Return the path where lossy files should go."""
        return os.path.join("~/Music", artist.name, concert.lmaid)
