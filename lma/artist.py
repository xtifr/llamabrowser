#! /usr/bin/env python

import time
from . import database
from . import query
from . import progress

#
# Artist database access
#

def download_artists(bar = progress.NullProgressBar):
    """Download artist records from LMA."""
    db = database.Db()

    # get the last update date
    c = db.cursor()
    c.execute("SELECT last_artist_read from lma_config where recnum = 1");
    lastdate = c.fetchone()[0]

    # form the archive query (including lastdate)
    aquery = query.Query(query.BAND_QUERY)
    aquery.add_fields(query.BAND_FIELDS)
    aquery.add_sort(query.PUBDATE)
    aquery.newer_than(lastdate)

    # create the progress bar callback
    callback = progress.ProgressCallback("Live Music Archive Download",
                                         "Retrieve Artists from LMA", bar)

    # push the records into our database, with callback
    c.executemany("INSERT OR IGNORE INTO artist (aname, lmaid)"
                   "   VALUES (:title, :identifier)",
                   query.ProgressIter(aquery, callback))

    # now update the last-updated field
    c.execute("UPDATE lma_config SET last_artist_read = date('now')"
               "WHERE recnum = 1")
    db.commit()
    c.close()

#
# Prepare a list of artists
#
class ArtistList(object):
    """Generic representation of artist list."""
    def __init__(self, bar = progress.NullProgressBar):
        self._bar = bar
        self.refresh()

    def refresh(self):
        """Reload the data from the DB."""
        db = database.Db()
        c = db.cursor()
        c.execute("""SELECT a.aname, b.browsedate, f.artistid from artist AS a
    LEFT JOIN lastbrowse AS b ON b.aid = a.aid
    LEFT JOIN favorite AS f ON f.artistid = a.aid
    ORDER BY a.aname""")
        self._data = c.fetchall()

    def repopulate(self):
        """Update the DB from the internet, then refresh."""
        download_artists(self._bar)
        self.refresh()

    def getResult(self, row, col):
        """Return the value for a given row and column."""
        value = self._data[row][col]
        if value == None:
            return ""
        if col == 2:
            return "Y"
        return value

    def getCount(self):
        """Return the current number of rows."""
        return len(self._data)
