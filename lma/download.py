#!/usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

"""Simple download manager for LMABrowser."""

import os
import hashlib # for md5

from . import archive
from . import progress
from . import details

# quick hack till we set up gettext
_ = str

BUFFER_SIZE = 8192 # this may be too small, but we'll try it

#
# In the future, it might be nice to make a fancy, multithreaded queue
# or something, but for a first attempt, this should do.

#
# main download function
#
def download_files(songlist, concert, targetdir, artist=None,
                   callback=progress.NullProgressBar):
    """Download songs to given directory (or subdir if artist specified)."""

    # make sure target directory exists
    abspath = os.path.abspath(os.path.expanduser(targetdir))
    if not os.path.isdir(abspath):
        raise IOError("No directory: %s" % targetdir)
    # if we need an artist subdirectory, go ahead and make it
    if artist:
        abspath = os.path.join(abspath, artist)
        if not os.path.isdir(abspath):
            os.mkdir(abspath)

    # now make the subdir for the concert
    abspath = os.path.join(abspath, concert.lmaid)
    if not os.path.isdir(abspath):
        os.mkdir(abspath)

    # time to download
    for song in songlist:
        if not download_one_file(concert, song, abspath, callback):
            return False
    return True
            
def download_one_file(concert, song, targetdir, callback):
    """Download one file, updating callback as necessary."""

    # first, make sure we don't already have this one
    filename = os.path.join(targetdir, song['name'])
    filesize = int(song['size'])
    if os.path.exists(filename):
        # it's there--is it the right size?
        if os.stat(filename).st_size == filesize:
            return True
        # not right size, just remove it
        os.remove(filename)

    cb = callback(_(u"Download File"), song['name'], can_cancel=True)

    # don't use os.path.join here, because the name is for remote system
    downloaded = 0
    chksum = hashlib.md5()
    path = "%s/%s" % (concert.lmaid, song['name'])
    rhand = archive.archive_open(path)
    lhand = open(filename, "wb")
    try:
        data = rhand.read(BUFFER_SIZE)
        while len(data) > 0:
            downloaded += len(data)
            chksum.update(data)
            lhand.write(data)
            if not cb.update(downloaded * 100/filesize):
                break
            data = rhand.read(BUFFER_SIZE)
    finally:
        lhand.close()
        rhand.close()

    # now, make sure our checksum matches
    if chksum.hexdigest() == song['md5']:
        cb.done()
        return True
    # we failed, remove the partial download
    os.remove(filename)
    cb.done(_("Download Failed"))
    return False
