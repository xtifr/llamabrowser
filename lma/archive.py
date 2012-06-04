#!/usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

"""Access to the Internet Archive: search engine and downloads."""

import urllib2

ARCHIVE_URL = "http://www.archive.org"

def full_path(path, search=False):
    if search:
        return "%s/advancedsearch.php?%s" % (ARCHIVE_URL, path)
    return "%s/download/%s" % (ARCHIVE_URL, path)

def archive_open(path, search=False):
    """URL handler wrapper for Internet Archive addresses.

    Takes two arguments: a relative path (or search string) and a
    search flag, which defaults to false.  If the search flag set to
    True, this sends a query to the Archive's search engine,
    otherwise, it opens a downloadable file."""

    return urllib2.urlopen(full_path(path, search))
