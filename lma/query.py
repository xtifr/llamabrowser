#!/usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

"""Connect to and download records from the Live Music Archive.

The Query class is used to construct queries, and will iterate through
the results.

The ProgressIter class allows hooking a UI callback into a Query."""

import time
import urllib2

# Hostname to access
ARCHIVE_URL = "http://www.archive.org"

# main fields we'll want to use
# (if you add/remove any, don't forget to fix import list in __init__.py)
IDENTIFIER="identifier"
COLLECTION="collection"
MEDIATYPE="mediatype"
TITLE="title"
PUBDATE="publicdate"
DATE="date"
YEAR="year"
FORMAT="format"

BAND_QUERY="collection:etree AND mediatype:collection"
def CONCERT_QUERY(id):
    return "collection:%s AND mediatype:etree" % str(id)
STANDARD_FIELDS=[IDENTIFIER, TITLE]

# A sample version of the type of URL we'll be using to query the LMA is:
# http://archive.org/advancedsearch.php?q=mediatype%3Acollection%20AND%20collection%3Aetree&fl[]=identifier&sort[]=&sort[]=&sort[]=&rows=50&page=1&output=json

def archive_open(path, search=False):
    """URL handler wrapper for Internet Archive addresses.

    Takes two arguments: a relative path (or search string) and a
    search flag, which defaults to false.  If the search flag set to
    True, this sends a query to the Archive's search engine,
    otherwise, it opens a downloadable file."""

    if search:
        op = "/advancedsearch.php?"
    else:
        op = "/download/"
    return urllib2.urlopen(ARCHIVE_URL + op + path)


class _Result (object):
    """Internal class returned from an instance of the Query class.

    Encapsulates the state of the query at the time it's created,
    and can then be used to iterate through the results."""

    def __init__(self, query, field, sort, rows=50, date=None):
        self._query = query
        self._field = list(field)
        self._sort = list(sort)
        self._rows = rows
        self._date = date
        self._page = 0
        self._results = 0
        self._current = 0
        self._data = []
        self._refill_data()

    def calc_query(self):
        """Calculate the full query including date restriction."""
        if self._date == None:
            return self._query
        today = time.strftime("%Y-%m-%d", time.gmtime())
        return "%s AND publicdate:[%s TO %s]" % (self._query, self._date, today)

    def _make_json_url(self):
        """Make the URL to use to get a page of json data.  (Internal)"""
        body = (["q=" + urllib2.quote(self.calc_query()),
                 "rows=" + str(self._rows),
                 "page=" + str(self._page),
                 "output=json"] +
                ["fl[]=" + urllib2.quote(f) for f in self._field] +
                ["sort[]=" + urllib2.quote(s) for s in self._sort])
        return "&".join(body)

    def _read_page(self):
        """Read the next page of data from the Archive. (Internal)"""
        
        hand = archive_open(self._make_json_url(), search=True)
        try:
            data = hand.read()
        finally:
            hand.close()
        return data

    def _refill_data(self):
        """Read and parse next page of data from the Archive. (Internal)"""
        import json
        j = json.loads(self._read_page())
        response=j["response"]
        self._results = response["numFound"]
        self._data = response["docs"]

    def next(self):
        """Return the next result, reading in data if necessary."""
        # calculate offset into current page
        offset = self._current % self._rows

        if self._current >= self._results:
            raise StopIteration

        # don't refill on first page, since we already did to get _results
        if offset == 0 and self._current > 0:
            self._page += 1
            self._refill_data()
            # double check here in case the number of results changed.
            if self._current >= self._results:
                raise StopIteration

        # set up for next call, now that we're past the raises.
        self._current += 1
        return self._data[offset]

    def __iter__(self):
        """Required for proper iterator-like behavior."""
        return self

    def current(self):
        """Return current record (useful for UI callback functions)."""
        return self._current;

    def total(self):
        """Return total records (useful for UI callback functions)."""
        return self._results

class Query (object):
    """Defines an Archive query.

    Used to set up a query and then create an iterator which encapsulates
    the query.  Each iterator can is independent; a single Query object
    can be define multiple queries, each represented by an iterator."""

    def __init__(self, query=None):
        """Query initialization."""
        self.reset()
        if (query != None):
            self.set_query(query)

    def reset(self):
        """Reset all values for new query."""
        self._query = ""
        self._field=[]
        self._sort = []
        self._rows = 50
        self._date = None

    def set_query(self, query):
        """Set main search string."""
        self._query = str(query)

    def add_field(self, field):
        """Add to list of fields that query will return."""
        self._field.append(str(field))

    def add_fields(self, fields):
        """Add multiple entries to list of fields that query will return."""
        for f in fields:
            self._field.append(str(f))

    def add_sort(self, field):
        """Add to list of fields to sort by (max 3)."""
        if len(self._sort) < 3:
            self._field.append(str(field))
        else:
            raise IndexError

    def set_pagesize(self, rows):
        """set number of results to get in each call to Archive."""
        a = int(rows)
        if a < 1:
            raise ValueError
        self._rows = a

    def newer_than(self, date):
        """Define a limiting date for the query."""
        self._date = date

    def __iter__(self):
        """Return iterator encapsulating current parameters."""
        field = self._field
        # set default value for returned field if none given
        if len(field) == 0:
            field = [IDENTIFIER]
        return _Result(self._query, field, self._sort, self._rows, self._date)

class ProgressIter(object):
    """Wrap an LMA query with a progress callback object."""
    def __init__(self, query, callback):
        self._iter = iter(query)
        self._callback = callback
        self._count = 0
        callback.start()

    def next(self):
        """Iterate on the wrapped iterator."""
        try:
            value = self._iter.next()
        except:
            self._callback.end()
            raise

        if (self._count % self._callback.frequency) == 0:
            self._callback.update(self._iter.current(), self._iter.total())
        self._count += 1
        return value

    def __iter__(self):
        return self

if __name__ == '__main__':
    # grab two quick pages to see
    import pprint
    mypagesize = 10
    q = Query(BAND_QUERY)
    q.add_fields(BAND_FIELDS)
    q.set_pagesize(mypagesize)

    i = q.__iter__()
    print("First page of output -- %d items" % (mypagesize))
    for j in xrange(mypagesize):
        pprint.pprint(i.next())
    print("Second page of output -- %d items" % (mypagesize))
    for j in xrange(mypagesize):
        pprint.pprint(i.next())
