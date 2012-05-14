#!/usr/bin/env python

import urllib2

# main fields we'll want to use
# (if you add/remove any, don't forget to fix import list in __init__.py)
IDENTIFIER="identifier"
COLLECTION="collection"
MEDIATYPE="mediatype"
TITLE="title"
DATE="date"
YEAR="year"
FORMAT="format"

BAND_QUERY="%s:%s AND %s:%s" % (MEDIATYPE, COLLECTION, COLLECTION, "etree")
BAND_FIELDS=[IDENTIFIER, TITLE]
CONCERT_FIELDS=[IDENTIFIER, TITLE]

# An sample version of the type of URL we'll be using to query the LMA is:
# http://archive.org/advancedsearch.php?q=mediatype%3Acollection%20AND%20collection%3Aetree&fl[]=identifier&sort[]=&sort[]=&sort[]=&rows=50&page=1&output=json

class Result (object):
    """Internal class returned from an instance of the Query class.

    Encapsulates the state of the query at the time it's created,
    and can then be used to iterate through the results."""

    def __init__(self, query, field, sort, rows):
        self._query = query
        self._field = list(field)
        self._sort = list(sort)
        self._rows = rows
        self._page = 0
        self._results = 0
        self._current = 0
        self._data = []

    def make_json_url(self):
        """Make the URL to use to get a page of json data.  (Internal)"""
        body = (["q=" + urllib2.quote(self._query),
                 "rows=" + str(self._rows),
                 "page=" + str(self._page),
                 "output=json"] +
                ["fl[]=" + urllib2.quote(f) for f in self._field] +
                ["sort[]=" + urllib2.quote(s) for s in self._sort])
        return ("http://archive.org/advancedsearch.php?" + "&".join(body))

    def read_page(self):
        """Read the next page of data from the Archive. (Internal)"""
        
        hand = urllib2.urlopen(self.make_json_url())
        try:
            data = hand.read()
        finally:
            hand.close()
        return data

    def refill_data(self):
        """Read and parse next page of data from the Archive. (Internal)"""
        import json
        j = json.loads(self.read_page())
        response=j["response"]
        self._results = response["numFound"]
        self._data = response["docs"]

    def next(self):
        """Return the next result, reading in data if necessary."""
        # calculate offset into current page
        offset = self._current % self._rows

        if offset == 0:
            # starting a new page -- make sure we need it.
            # (always need at least one, so skip check if _page is zero.)
            if self._current >= self._results and self._page > 0:
                raise StopIteration
            self._page = self._page + 1
            self.refill_data()

        # if we refilled the data, this test is semi-redundant,
        # but still useful in case the number of results changed.
        if self._current >= self._results:
            raise StopIteration

        # set up for next call, now that we're past the raises.
        self._current = self._current + 1
        return self._data[offset]

    def __iter__(self):
        """Required for proper iterator-like behavior."""
        return self

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

    def __iter__(self):
        """Return iterator encapsulating current parameters."""
        field = self._field
        # set default value for returned field if none given
        if len(field) == 0:
            field = [IDENTIFIER]
        return Result(self._query, field, self._sort, self._rows)

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
