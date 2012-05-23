#!/usr/bin/env python

from . import database
from . import query
from . import progress

#
# Concert database access
#

def download_concerts(aid, bar = progress.NullProgressBar):
    """Download concert records for given artist from LMA."""
    db = database.Db()

    # get the last update date
    c = db.cursor()
    c.execute("SELECT a.lmaid, a.aname, l.browsedate FROM artist AS a"
              "  LEFT JOIN lastbrowse AS l ON a.aid = l.aid"
              "  WHERE a.aid = ?", (aid,))
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
                                         bar)

    # push the records into our database, with callback
    c.executemany("INSERT OR IGNORE INTO concert (ctitle, lmaid, cyear, cdate)"
                  "  VALUES (:title, :identifier, :year, date(:date))",
                  query.ProgressIter(cquery, callback))

    # now update the last-updated field
    c.execute("INSERT OR REPLACE INTO lastbrowse (aid, browsedate)"
              "  VALUES (?, date('now'))", (aid,))
    db.commit()
    c.close()
