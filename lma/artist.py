#! /usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

import time
import lma

# temporary def used till we set up gettext
_ = str

# selectors for display mode, separated out for l10n
AVIEW_ALL = _(u"All Artists")
AVIEW_FAVORITES = _(u"Favorites")
AVIEW_BROWSED = _(u"With Concerts")
AVIEW_NEW = _(u"New Artists")
AVIEW_SELECTORS = [AVIEW_ALL, AVIEW_FAVORITES, AVIEW_BROWSED, AVIEW_NEW]

#
# db wrapper for an artist ID
#
class Artist(lma.DbRecord):
    """Object to wrap an artist ID and calculate various attributes."""
    def __init__(self, db, artist_id):
        super(Artist, self).__init__(db, artist_id)

    def concertList(self):
        """Return the list of concerts associated with this artist."""
        return lma.ConcertList(self._db, self)

    # properties (db access)
    @property
    def name(self):
        return self.getDbInfo("artist", "aname", "aid")
    @property
    def browsedate(self):
        return self.getDbInfo("lastbrowse", "browsedate", "aid")
    @property
    def favorite(self):
        return self.getDbBool("favorite", "artistid")
    @favorite.setter
    def favorite(self, flag):
        self.setDbBool("favorite", "artistid", flag)

#
# ArtistList represents the full set of known artists
#
class ArtistList(lma.DbList):
    """Generic representation of artist list."""
    def __init__(self, db):
        self._mode = AVIEW_ALL
        super(ArtistList, self).__init__(db, Artist)

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
        c = self._db.cursor()
        c.execute("SELECT a.aid FROM artist AS a %s %s "
                  "  ORDER BY a.aname" % (joinon, like))
        self._data = [x[0] for x in c.fetchall()]
        c.close()

    def repopulate(self, progbar = lma.NullProgressBar):
        """Update the DB from the internet, then refresh."""

        # get the last update date
        lastdate = self.lastUpdate()

        # form the archive query (including lastdate)
        aquery = lma.Query(lma.BAND_QUERY)
        aquery.add_fields(lma.STANDARD_FIELDS)
        aquery.add_sort(lma.PUBDATE)
        aquery.newer_than(lastdate)

        # create the progress bar callback
        callback = lma.ProgressCallback("Live Music Archive Download",
                                        "Retrieve Artists from LMA", progbar)

        c = self._db.cursor()
        # push the records into our database, with callback
        c.executemany("INSERT OR IGNORE INTO artist (aname, lmaid)"
                      "  VALUES (:title, :identifier)",
                       lma.ProgressIter(aquery, callback))

        # now update the last-updated field
        c.execute("UPDATE lma_config SET last_artist_read = date('now')"
                   "WHERE recnum = 1")

        self._db.commit()
        c.close()

        # clear newlist on first time through
        if lastdate == None:
            self.clearNew()
        else:
            self.refresh()

    def clearNew(self):
        """Clear the new list, then refresh."""
        self._db.execute("DELETE FROM newartist")
        self._db.commit()
        self.refresh()

    def numNew(self):
        """Report the current number of 'new' artists."""
        c = self._db.cursor()
        c.execute("SELECT COUNT(aid) FROM newartist;")
        n = int(c.fetchone()[0])
        c.close()
        return n

    def lastUpdate(self):
        c = self._db.cursor()
        c.execute("SELECT last_artist_read from lma_config where recnum = 1");
        lastdate = c.fetchone()[0]
        c.close()
        return lastdate

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
