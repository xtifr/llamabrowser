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
