#! /usr/bin/env python

import time
from . import database
from . import query
from . import progress

# temporary def used till we set up gettext
def _(text):
    return text

#
# Artist database access
#

def download_artists(bar = progress.NullProgressBar):
    """Download artist records from LMA."""
    # reset the new list, in preparation for repopulating it
    clear_new_artists()

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
                                         "Retrieve Artists from LMA", bar)

    # push the records into our database, with callback
    c.executemany("INSERT OR IGNORE INTO artist (aname, lmaid)"
                  "  VALUES (:title, :identifier)",
                   query.ProgressIter(aquery, callback))

    # now update the last-updated field
    c.execute("UPDATE lma_config SET last_artist_read = date('now')"
               "WHERE recnum = 1")
    db.commit()
    c.close()

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
VIEW_ALL = _(u"All Artists")
VIEW_FAVORITES = _(u"Favorites")
VIEW_BROWSED = _(u"With Concerts")
VIEW_NEW = _(u"New Artists")
VIEW_SELECTORS = [VIEW_ALL, VIEW_FAVORITES, VIEW_BROWSED, VIEW_NEW]

class ArtistList(object):
    """Generic representation of artist list."""
    def __init__(self, progress = progress.NullProgressBar):
        self._progress = progress
        self._mode = VIEW_ALL
        self.refresh()

    # properties for mode selection
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

        This is a pseudo property, referring to a global list."""
        return VIEW_SELECTORS

    def refresh(self):
        """Set up to access the DB according to the current mode."""

        # by default, use left joins with both favorite and lastbrowse.
        # use a regular join instead to limit records to just that type.
        fav_join = browse_join = new_join = "LEFT"
        if self.mode == VIEW_FAVORITES:
            fav_join = ""
        elif self.mode == VIEW_BROWSED:
            browse_join = ""
        elif self.mode == VIEW_NEW:
            new_join = ""

        # now call selec using the appropriate join
        db = database.Db()
        c = db.cursor()
        c.execute("SELECT a.aname, b.browsedate, f.artistid, a.aid, n.aid "
                  "  FROM artist AS a "
                  "  %s JOIN favorite AS f ON f.artistid = a.aid "
                  "  %s JOIN lastbrowse AS b ON b.aid = a.aid "
                  "  %s JOIN newartist AS n ON n.aid = a.aid "
                  "  ORDER BY a.aname" % (fav_join, browse_join, new_join))
        self._data = c.fetchall()
        c.close()

    def repopulate(self):
        """Update the DB from the internet, then refresh."""
        download_artists(self._progress)
        self.refresh()

    # methods used directly by the UI
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

    def getArtistID(self, row):
        """Get specified row's main key."""
        return self._data[row][3]
