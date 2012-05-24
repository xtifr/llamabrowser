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

#
# reset new concert list for given artist
#

def clear_new_concerts(artist):
    """Clear an artist's new concert list."""
    artist = str(int(artist))        # make sure
    db = database.Db()
    db.execute("DELETE FROM newconcert WHERE cid IN "
               "  (SELECT cid FROM concert WHERE artistid = ?)", (artist,))
    db.commit()

#
# Prepare a list of concerts
#

# selectors for display mode, separated out for l10n
CVIEW_ALL = _(u"All Concerts")
CVIEW_FAVORITES = _(u"Favorites")
CVIEW_NEW = _(u"New Concerts")
CVIEW_SELECTORS = [CVIEW_ALL, CVIEW_FAVORITES, CVIEW_NEW]

class ConcertList(object):
    """Generic representation of a concert list."""
    def __init__(self, artist, progbar = progress.NullProgressBar):
        self._artist = str(int(artist))
        self._progbar = progbar
        self._mode = CVIEW_ALL
        self.refresh()

    # properties for each selection
    @property
    def mode(self):
        """The current selection/display mode -- a value from mode_list.

        Setting this may trigger a refresh."""
        return self._mode
    @mode.setter
    def mode(self, value):
        assert(value in self.mode_list)
        if self._mode != value:
            self._mode = value
            self.refresh()
    @property
    def mode_list(self):
        """List of available selection/display modes.

        This is a psuedo property, referring to a global list."""
        return CVIEW_SELECTORS

    def refresh(self):
        """Set up to access the DB according to the current mode."""

        # by default, use left joins, with regular joins to select a type.
        fav_join = browse_join = new_join = "LEFT"
        if self.mode == CVIEW_FAVORITES:
            fav_join = ""
        elif self.mode == CVIEW_NEW:
            new_join = ""

        # now call select using the appropriate join
        db = database.Db()
        c = db.cursor()
        c.execute("SELECT c.cid,c.ctitle,c.cdate,f.concertid,c.cyear,n.cid "
                  "  FROM concert AS c "
                  "  %s JOIN favconcert AS f ON f.concertid = c.cid "
                  "  %s JOIN newconcert AS n ON n.cid = c.cid "
                  "  WHERE c.artistid = '%s' "
                  "  ORDER BY c.cdate" % (fav_join, new_join, self._artist))
        self._data = c.fetchall()
        c.close()

    def repopulate(self):
        """Update the DB from the internet, then refresh."""
        download_concerts(self._artist, self._progbar)
        self.refresh()

    def clearNew(self):
        clear_new_artists(self._artist)
        self.refresh()

    # methods used directly by the UI
    def getResult(self, row, col):
        """Return the value for a given row and column."""
        value = self._data[row][col+1]
        if value == None:
            return ""
        if col == 2:
            return "Y"
        return value

    def getCount(self):
        """Return the current number of rows."""
        return len(self._data)

    def getConcertID(self, row):
        """Get specified row's main key."""
        return self._data[row][0]
