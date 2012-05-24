#!/usr/bin/env python

from . import database
from . import query
from . import progress

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
