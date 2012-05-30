"""Module for access to the Internet Archive's Live Music Archive.

Data is read from the Live Music Archive and stored internally in a
SQLite database which can then be browsed using various specialized
classes and methods provided by this module.

Reading data from the Live Music Access is done through the use of the
Query class.  Instances of Query can generate iterators which will
step through records from the Archive's data, live.

The ProgressCallback class is a base class used to create a progress
bar while downloading.  It can be specialized for different UIs.  The
ProgressIter class combines a ProgressCallback with a Query to make an
iterator that automatically updates a progress bar.

The functions download_artists and download_concerts do what they say.
They build appropriate Query objects internally, and take an optional
ProgressCallback instance as a parameter.

The ArtistList and ConcertList classes are wrappers for the records
stored in the local database."""

__version__ = '0.1'

from lma.archive import (archive_open)

from lma.query import (Query, ProgressIter, IDENTIFIER, TITLE, COLLECTION,
                       MEDIATYPE, PUBDATE, DATE, YEAR, FORMAT,
                       BAND_QUERY, CONCERT_QUERY, STANDARD_FIELDS)

from lma.progress import (ProgressCallback, NullProgressBar)

from lma.database import (Db)

from lma.artist import (download_artists, 
                        clear_new_artists, 
                        ArtistList, 
                        AVIEW_SELECTORS)

from lma.concert import (download_concerts,
                         clear_new_concerts,
                         ConcertList,
                         CVIEW_SELECTORS)

from lma.details import (ConcertDetails, ConcertFileList)
