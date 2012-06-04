#!/usr/bin/env python
"""Find and process any user configuration for the LMA access.

This still needs a better cross-platform way to find a place to
store user data that isn't specific to an application, since this
library can, in theory, be used by different application, but
nobody would want two copies of the LMA database.  *sigh*"""

import sys, os
import cPickle

# configuration items include:
# path to store lossless files
# path to store lossy files
# flag to add intermediate artist subdir
# flag to autoconvert convert shn to flac

# for the paths, we need to know stuff about how to form a
# unique path depending on the artist name, concert name, etc.

class Config(object):
    """Create a configuration object."""
    _dir = None
    _data = {}
    @classmethod
    def cfile(Cls):
        return os.path.join(Cls._dir, "Config")

    def __init__(self, datadir=None, create=False):
        """Return the singleton.  Must be initialized with a path.
        
        if no path was provided on the first call to __init__,
        will throw ValueError."""
        if Config._dir != None:
            return
        if datadir == None:
            raise ValueError("class 'lma.Config' has no data directory.")
        Config._dir = os.path.abspath(os.path.expanduser(datadir))
        if not os.path.isdir(Config._dir):
            if not create:
                Config._dir = None
                raise IOError("No such directory: " + datadir)
            os.makedirs(Config._dir)
        # now we know where the config file goes
        try:
            self.read()
        except IOError:
            self.makeConfig()
            self.write()

    # access methods
    def cfgpath(self, f):
        """Returns the path to the given file in the config dir"""
        return os.path.join(Config._dir, f)
    def dbpath(self):
        """Returns the path to the database file."""
        return self.cfgpath("lma.db")
    def home(self):
        """Returns the path to user's home dir. Unix-specific for now."""
        return os.path.expanduser("~")
    def homepath(self, f):
        """If not absolute path, must be relative to home."""
        if os.path.isabs(f):
            return f
        return os.path.join(self.home(), f)
    def striphome(self, f):
        """if path is under home, return relative path."""
        f = os.path.normpath(os.path.expanduser(f))
        # if it's not absolute, don't do anything
        if os.path.isabs(f):
            h = self.home()
            if len(f) > len(h) and f.startswith(h):
                # must have a path sep following, so skip len(h) + 1
                return f[len(h) + 1:]
        return f

    # properties for config items
    @property
    def download_path(self):
        """Return the path where lossy files should go."""
        return self.homepath(Config._data['download_dir'])
    @download_path.setter
    def download_path(self, f):
        f = self.striphome(f)
        Config._data['download_dir'] = f
    @property
    def lossless_path(self):
        """Return the path where flac/shn files should go (can be None)."""
        if Config._data['lossless_dir']:
            return self.homepath(Config._data['lossless_dir'])
        return self.download_path
    @lossless_path.setter
    def lossless_path(self, f):
        if f != None:
            f = self.striphome(f)
        Config._data['lossless_dir'] = f
    @property
    def artist_subdir(self):
        """Flag: use artist-name subdirectories?"""
        return Config._data['artist_subdir']
    @artist_subdir.setter
    def artist_subdir(self, b):
        Config._data['artist_subdir'] = bool(b)
    @property
    def shn_to_flac(self):
        """Auto-convert downloaded .shn files to .flac?"""
        return Config._data['shn_to_flac']
    @shn_to_flac.setter
    def shn_to_flac(self, b):
        Config._data['shn_to_flac'] = bool(b)

    # methods to access the config file
    def makeConfig(self):
        """Set default configuration data"""
        if len(Config._data) == 0:
            Config._data = {
                "download_dir"  : "Music",
                "lossless_dir"  : None,
                "artist_subdir" : True,
                "shn_to_flac"   : False }
    def read(self):
        """Read default configuration."""
        handle = open(self.cfgpath(Config.cfile()), "r")
        try:
            data = cPickle.load(handle)
        finally:
            handle.close()
        # version check would go here...
        Config._data = data
    def write(self):
        """Write out configuration."""
        handle = open(self.cfgpath(Config.cfile()), "w")
        try:
            cPickle.dump(Config._data, handle)
        finally:
            handle.close()
