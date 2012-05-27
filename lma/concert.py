#!/usr/bin/env python

from . import database
from . import query
from . import progress

# temporary def used till we set up gettext
def _(text):
    return text

#
# Concert database access
#

def download_concerts(artist, progbar = progress.NullProgressBar):
    """Download concert records for given artist from LMA."""
    artist = str(int(artist)) # make sure we have an integer
    db = database.Db()

    # get the last update date
    c = db.cursor()
    c.execute("SELECT a.lmaid, a.aname, l.browsedate FROM artist AS a"
              "  LEFT JOIN lastbrowse AS l ON a.aid = l.aid"
              "  WHERE a.aid = ?", (artist,))
    lmaid, aname, lastdate = c.fetchone()

    # form the archive query (including lastdate)
    cquery = query.Query(query.CONCERT_QUERY(lmaid))
    cquery.add_fields(query.STANDARD_FIELDS)
    cquery.add_fields([query.DATE, query.YEAR])
    cquery.add_sort(query.PUBDATE)
    cquery.newer_than(lastdate)

    # create the progress bar callback
    callback = progress.ProgressCallback("Live Music Archive Download",
                                         "Retrieve %s Concert List" % aname,
                                         progbar)

    # push the records into our database, with callback
    c.executemany("INSERT OR IGNORE INTO concert"
                  " (ctitle, lmaid, cyear, cdate, artistid) VALUES"
                  "  (:title, :identifier, :year, date(:date), %s)" % artist,
                  query.ProgressIter(cquery, callback))

    # now update the artist's last-updated field
    c.execute("INSERT OR REPLACE INTO lastbrowse (aid, browsedate)"
              "  VALUES (?, date('now'))", (artist,))

    db.commit()
    c.close()

    # clear newlist on first time through
    if lastdate == None:
        clear_new_concerts(artist)


#
# reset new concert list for given artist
#

def clear_new_concerts(artist):
    """Clear an artist's new concert list."""
    artist = str(int(artist))
    db = database.Db()
    c = db.cursor()
    c.execute("DELETE FROM newconcert WHERE cid IN "
               "  (SELECT cid FROM concert WHERE artistid = ?)", (artist,))
    db.commit()
    c.close()

#
# Prepare a list of concerts
#

# selectors for display mode, separated out for l10n
CVIEW_ALL = _(u"All Concerts")
CVIEW_FAVORITES = _(u"Favorites")
CVIEW_NEW = _(u"New Concerts")
CVIEW_SELECTORS = [CVIEW_ALL, CVIEW_FAVORITES, CVIEW_NEW]

#
# db wrapper for a concert id
#

class Concert(database.DbRecord):
    """Object to wrap a concert ID and calculate various attributes."""
    def __init__(self, concert):
        super(Concert, self).__init__(concert)
    @property
    def name(self):
        return super(Concert,self).getDbInfo("concert", "ctitle", "cid")
    @property
    def date(self):
        return super(Concert,self).getDbInfo("concert", "cdate", "cid")
    @property
    def favorite(self):
        return super(Concert,self).getDbBool("favconcert", "concertid")

class ConcertList(object):
    """Generic representation of a concert list."""
    def __init__(self, artist, progbar = progress.NullProgressBar):
        self._artist = artist
        self._progbar = progbar
        self._mode = CVIEW_ALL
        self._search = None
        self.refresh()

    def refresh(self):
        """Set up to access the DB according to the current mode."""

        db = database.Db()
        c = db.cursor()

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

        # search uses like
        like = ""
        if self.search:
            like = "AND c.ctitle LIKE '%%%s%%'" % self.search

        # now call select using the appropriate join
        c.execute("SELECT c.cid FROM concert AS c %s"
                  "  WHERE c.artistid = '%s' %s"
                  "  ORDER BY c.cdate" % (joinon, str(self._artist), like))
        self._data = [Concert(x[0]) for x in c.fetchall()]
        c.close()

    def repopulate(self):
        """Update the DB from the internet, then refresh."""
        download_concerts(self._artist, self._progbar)
        self.refresh()

    def clearNew(self):
        clear_new_concerts(self._artist)
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
    def search(self):
        """current search string, limiting the selection."""
        return self._search
    @search.setter
    def search(self, string):
        self._search = str(string)
        self.refresh()
    @search.deleter
    def search(self):
        self._search = None
        self.refresh()

    @property
    def artistName(self):
        return(self._artist.name)

    # support reading like an array
    def __getitem__(self, i):
        return self._data[i]
    def __len__(self):
        return len(self._data)
