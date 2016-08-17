#!/usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

import lma

# temporary def used till we set up gettext
_ = str

#
# Prepare a list of concerts
#

# selectors for display mode, separated out for l10n
CVIEW_ALL = _(u"All Concerts")
CVIEW_FAVORITES = _(u"Favorites")
CVIEW_NEW = _(u"New Concerts")
CVIEW_DL = _(u"Downloaded")
CVIEW_SELECTORS = [CVIEW_ALL, CVIEW_FAVORITES, CVIEW_NEW, CVIEW_DL]

#
# db wrapper for a concert id
#
class Concert(lma.DbRecord):
    """Object to wrap a concert ID and calculate various attributes."""
    def __init__(self, db, concert):
        super(Concert, self).__init__(db, concert)

    def fileList(self):
        """Return the songs associated with this concert."""
        return ConcertFileList(self)

    def details(self):
        """Return the details for this concert."""
        return lma.ConcertDetails(self._db, self)

    def markDownloaded(self):
        """Mark this concert as having been downloaded."""
        c = self._db.cursor()
        c.execute("INSERT OR REPLACE INTO dlconcert (cid, dldate)"
                  "  VALUES (?, date('now'))", (str(self),))
        self._db.commit()
        c.close()

    # properties
    @property
    def name(self):
        return self.getDbInfo("concert", "ctitle", "cid")
    @property
    def date(self):
        return self.getDbInfo("concert", "cdate", "cid")
    @property
    def favorite(self):
        """Favorite flag (read/write)."""
        return self.getDbBool("favconcert", "concertid")
    @favorite.setter
    def favorite(self, flag):
        self.setDbBool("favconcert", "concertid", flag)
    @property
    def lmaid(self):
        return self.getDbInfo("concert", "lmaid", "cid")
    @property
    def dldate(self):
        return self.getDbInfo("dlconcert", "dldate", "cid")

    @property
    def artist(self):
        return lma.Artist(self._db,
                          self.getDbInfo("concert", "artistid", "cid"))

#
# list of Concerts
#
class ConcertList(lma.DbList):
    """Generic representation of a concert list."""

    def __init__(self, db, artist):
        self._artist = artist
        self._mode = CVIEW_ALL
        super(ConcertList, self).__init__(db, Concert)

    def refresh(self):
        """Set up to access the DB according to the current mode."""

        c = self._db.cursor()

        # get the name and id
        c.execute("SELECT aname,lmaid FROM artist where aid = ?",
                  (str(self._artist),))
        (self._aname, self._lmaid) = c.fetchone()

        # modes user inner join to restrict output
        joinon = ""
        if self.mode == CVIEW_FAVORITES:
            joinon = "JOIN favconcert AS f ON f.concertid = c.cid"
        elif self.mode == CVIEW_NEW:
            joinon = "JOIN newconcert AS n ON n.cid = c.cid"
        elif self.mode == CVIEW_DL:
            joinon = "JOIN dlconcert AS d ON d.cid = c.cid"

        # search uses like
        like = ""
        if self.search:
            like = "AND c.ctitle LIKE '%%%s%%'" % self.search

        # now call select using the appropriate join
        c.execute("SELECT c.cid FROM concert AS c %s"
                  "  WHERE c.artistid = '%s' %s"
                  "  ORDER BY c.cdate" % (joinon, str(self._artist), like))
        self._data = [x[0] for x in c.fetchall()]
        c.close()

    def repopulate(self, progbar = lma.NullProgressBar):
        """Update the DB from the internet, then refresh."""

        c = self._db.cursor()
        c.execute("SELECT lmaid, aname FROM artist"
                  "  WHERE aid = ?", (str(self._artist),))
        lmaid, aname = c.fetchone()

        lastdate = self.lastUpdate()

        # form the archive query (including lastdate)
        cquery = lma.Query(lma.CONCERT_QUERY(lmaid))
        cquery.add_fields(lma.STANDARD_FIELDS)
        cquery.add_fields([lma.DATE, lma.YEAR])
        cquery.add_sort(lma.PUBDATE)
        cquery.newer_than(lastdate)

        # create the progress bar callback
        callback = lma.ProgressCallback("Live Music Archive Download",
                                        "Retrieve %s Concert List" % aname,
                                        progbar)

        # push the records into our database, with callback
        c.executemany("INSERT OR IGNORE INTO concert"
                      " (ctitle, lmaid, cyear, cdate, artistid) VALUES"
                      "  (:title, :identifier, :year, date(:date), %s)" %
                      str(self._artist), lma.ProgressIter(cquery, callback))

        # now update the artist's last-updated field
        c.execute("INSERT OR REPLACE INTO lastbrowse (aid, browsedate)"
                  "  VALUES (?, date('now'))", (str(self._artist),))

        self._db.commit()
        c.close()

        # clear newlist on first time through
        if lastdate == None:
            self._clearNew()

        self.refresh()

    def _clearNew(self):
        """Internal: clear 'new' concerts list, but don't refresh!"""
        c = self._db.cursor()
        c.execute("DELETE FROM newconcert WHERE cid IN "
                  "  (SELECT cid FROM concert WHERE artistid = ?)", (str(self._artist),))
        self._db.commit()
        c.close()

    def clearNew(self):
        """Clear the 'new' concerts list."""
        self._clearNew()
        self.refresh()

    def numNew(self):
        """Report the current size of the 'new' concerts list."""
        c = self._db.cursor()
        c.execute("SELECT COUNT(n.cid) FROM newconcert AS n"
                  "  JOIN concert AS c ON c.cid = n.cid"
                  "  WHERE c.artistid = ?", (str(self._artist),))
        n = int(c.fetchone()[0])
        c.close()
        return n

    def lastUpdate(self):
        """Return the date of the last time we repopulated the list."""
        c = self._db.cursor()
        c.execute("SELECT browsedate FROM lastbrowse"
                  "  WHERE aid = ?", (str(self._artist),))
        lastdate = c.fetchone()[0]
        c.close()
        return lastdate

    def forget(self):
        """Remove all concerts from db; create blank slate..."""
        c = self._db.cursor()

        # get rid of any dependent records first
        self._clearNew()
        c.execute("DELETE FROM favconcert WHERE concertid IN "
                  "  (SELECT cid FROM concert WHERE artistid = ?)",
                  (str(self._artist),))
        c.execute("DELETE FROM dlconcert WHERE cid IN "
                  "  (SELECT cid FROM concert WHERE artistid = ?)",
                  (str(self._artist),))

        # now clear the database and forget we ever downloaded anything
        c.execute("DELETE FROM concert WHERE artistid = ?",
                  (str(self._artist),))
        c.execute("DELETE FROM lastbrowse WHERE aid = ?",
                  (str(self._artist),))

        self._db.commit()
        c.close()
        self.refresh()

    # properties for each selection
    @property
    def mode(self):
        """The current selection/display mode.

        Setting this may trigger a refresh."""
        return self._mode
    @mode.setter
    def mode(self, value):
        assert(value in CVIEW_SELECTORS)
        if self._mode != value:
            self._mode = value
            self.refresh()

    @property
    def artistName(self):
        return(self._artist.name)
