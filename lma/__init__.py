# The lma library provides access to the Internet Archive's Live Music Archive.
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

"""Module for access to the Internet Archive's Live Music Archive.

The 'Query' class provides raw access to the Archive's database.

The LMA data from the Archive is cached locally, and accessed through
the 'ArtistList' and 'ConcertList' classes. Concert details are
retrieved with the 'ConcertFileList' and 'ConcertDetails' classes. Songs
from a specific concert are downloaded with the 'download_files'
function.

The database module provides common base classes for the 'Artist',
'Concert', 'ArtistList', and 'ConcertList' classes.
"""

__version__ = '0.1'

from lma.config import (Config)

from lma.progress import (ProgressCallback, NullProgressBar,
                          NullMultiProgressBar)

from lma.query import (archive_open, Query, ProgressIter,
                       IDENTIFIER, TITLE, COLLECTION, MEDIATYPE, PUBDATE, DATE, YEAR,
                       FORMAT, BAND_QUERY, CONCERT_QUERY, STANDARD_FIELDS)

from lma.database import (ArDb, DbList, DbRecord)

from lma.artist import (ArtistList, Artist, AVIEW_SELECTORS)

from lma.concert import (ConcertList, Concert, CVIEW_SELECTORS)

from lma.details import (ConcertDetails, ConcertFileList, default_formats)

from lma.download import (download_files)
