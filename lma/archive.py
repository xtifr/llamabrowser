#!/usr/bin/env python
"""Access to the Internet Archive: search engine and downloads."""

import urllib2

ARCHIVE_URL = "http://www.archive.org"

def _full_path(path, search):
    if search:
        return "%s/advancedsearch.php?%s" % (ARCHIVE_URL, path)
    return "%s/download/%s" % (ARCHIVE_URL, path)

def archive_open(path, search=False):
    """URL handler wrapper for Internet Archive addresses.

    Takes two arguments: a relative path (or search string) and a
    search flag, which defaults to false.  If the search flag set to
    True, this sends a query to the Archive's search engine,
    otherwise, it opens a downloadable file."""

    return urllib2.urlopen(_full_path(path, search))
