#!/usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

"""Simple download manager for LMABrowser."""

import os
import hashlib # for md5

import lma

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
                   callback=lma.NullMultiProgressBar):
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

    # prepare the progress bar
    totalbytes = sum(int(song['size']) for song in songlist)
    progress_bar = callback(_(u'Download Concert'), _(u'All Songs'), totalbytes)

    # time to download
    for song in songlist:
        progress_bar.StartPart(song['name'], int(song['size']))
        if not download_one_file(concert, song, abspath, progress_bar):
            progress_bar.Done("Download failed.")
            return False
    progress_bar.Done()

    # success, mark the concert as downloaded
    # (yes, it may be partial, but we still downloaded it.
    concert.markDownloaded()
    c.close()

    return True

def download_one_file(concert, song, targetdir, progress_bar):
    """Download one file, updating callback as necessary."""

    # if there's an extra subdirectory, create it
    filename = os.path.join(targetdir, os.path.normpath(song['name']))
    (head, tail) = os.path.split(filename)
    if not os.path.isdir(head):
        os.mkdir(head)

    # make sure we don't already have this one
    filesize = int(song['size'])
    if os.path.exists(filename):
        # it's there--is it the right size?
        if os.stat(filename).st_size == filesize:
            return True
        # not right size, just remove it
        os.remove(filename)

    # don't use os.path.join here, because the name is for remote system
    downloaded = 0
    chksum = hashlib.md5()
    path = "%s/%s" % (concert.lmaid, song['name'])
    rhand = lma.archive_open(path)
    lhand = open(filename, "wb")
    try:
        data = rhand.read(BUFFER_SIZE)
        while len(data) > 0:
            downloaded += len(data)
            lhand.write(data)
            chksum.update(data)
            if not progress_bar.update(downloaded):
                break
            data = rhand.read(BUFFER_SIZE)
    except IOError:
        # nothing really to do, but we want to catch this anyway.
        pass
    finally:
        lhand.close()
        rhand.close()

    # now, make sure our checksum matches
    if chksum.hexdigest() == song['md5']:
        return True
    # we failed, remove the partial download
    os.remove(filename)
    return False
