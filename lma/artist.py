#! /usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

import time
from . import database
from . import query
from . import progress

# temporary def used till we set up gettext
_ = str

#
# Artist database access
#

def download_artists(progbar = progress.NullProgressBar):
    """Download artist records from LMA."""
    # get the last update date
    db = database.Db()
    c = db.cursor()
    c.execute("SELECT last_artist_read from lma_config where recnum = 1");
    lastdate = c.fetchone()[0]

    # form the archive query (including lastdate)
    aquery = query.Query(query.BAND_QUERY)
    aquery.add_fields(query.STANDARD_FIELDS)
    aquery.add_sort(query.PUBDATE)
    aquery.newer_than(lastdate)

    # create the progress bar callback
    callback = progress.ProgressCallback("Live Music Archive Download",
                                         "Retrieve Artists from LMA", progbar)

    # push the records into our database, with callback
    c.executemany("INSERT OR IGNORE INTO artist (aname, lmaid)"
                  "  VALUES (:title, :identifier)",
                   query.ProgressIter(aquery, callback))

    # now update the last-updated field
    c.execute("UPDATE lma_config SET last_artist_read = date('now')"
               "WHERE recnum = 1")

    db.commit()
    c.close()

    # clear newlist on first time through
    if lastdate == None:
        clear_new_artists()


#
# reset the new artist list
#
def clear_new_artists():
    """Clear the new artist list."""
    db = database.Db()
    db.execute("DELETE FROM newartist")
    db.commit()

#
# Prepare a list of artists
#

# selectors for display mode, separated out for l10n
AVIEW_ALL = _(u"All Artists")
AVIEW_FAVORITES = _(u"Favorites")
AVIEW_BROWSED = _(u"With Concerts")
AVIEW_NEW = _(u"New Artists")
AVIEW_SELECTORS = [AVIEW_ALL, AVIEW_FAVORITES, AVIEW_BROWSED, AVIEW_NEW]

#
# db wrapper for an artist ID
#
class Artist(database.DbRecord):
    """Object to wrap an artist ID and calculate various attributes."""
    def __init__(self, artist):
        super(Artist, self).__init__(artist)
    @property
    def name(self):
        return super(Artist, self).getDbInfo("artist", "aname", "aid")
    @property
    def browsedate(self):
        return super(Artist, self).getDbInfo("lastbrowse", "browsedate", "aid")
    @property
    def favorite(self):
        return super(Artist, self).getDbBool("favorite", "artistid")
    @favorite.setter
    def favorite(self, flag):
        super(Artist, self).setDbBool("favorite", "artistid", flag)

class ArtistList(object):
    """Generic representation of artist list."""
    def __init__(self, progbar = progress.NullProgressBar):
        self._progbar = progbar
        self._mode = AVIEW_ALL
        self._search = None
        self.refresh()

    def refresh(self):
        """Set up to access the DB according to the current mode."""

        # modes use inner join to restrict output
        joinon = ""
        if self.mode == AVIEW_FAVORITES:
            joinon = "JOIN favorite AS f ON f.artistid = a.aid"
        elif self.mode == AVIEW_BROWSED:
            joinon = "JOIN lastbrowse AS b ON b.aid = a.aid"
        elif self.mode == AVIEW_NEW:
            joinon = "JOIN newartist as n ON n.aid = a.aid"

        # search uses "like"
        like = ""
        if self.search:
            like = "WHERE a.aname LIKE '%%%s%%'" % self.search

        # now call select using the appropriate join
        db = database.Db()
        c = db.cursor()
        c.execute("SELECT a.aid FROM artist AS a %s %s "
                  "  ORDER BY a.aname" % (joinon, like))
        self._data = [Artist(x[0]) for x in c.fetchall()]
        c.close()

    def repopulate(self):
        """Update the DB from the internet, then refresh."""
        download_artists(self._progbar)
        self.refresh()

    def clearNew(self):
        """Clear the new list, then refresh."""
        clear_new_artists()
        self.refresh()

    # properties for mode selection
    @property
    def mode(self):
        """The current selection/display mode.

        Setting this may trigger a refresh."""
        return self._mode
    @mode.setter
    def mode(self, value):
        assert(value in AVIEW_SELECTORS)
        if self._mode != value:
            self._mode = value
            self.refresh()

    @property
    def search(self):
        """The current search string, limiting the selection."""
        return self._search
    @search.setter
    def search(self, string):
        self._search = str(string)
        self.refresh()
    @search.deleter
    def search(self):
        self._search = None
        self.refresh()

    # support reading like an array
    def __getitem__(self, i):
        return self._data[i]
    def __len__(self):
        return len(self._data)
