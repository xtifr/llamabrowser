"""Module for access to the Internet Archive's Live Music Archive.

The download_artists() function gets new artist data from the Archive,
access is provided through the ArtistList class.
''art = ArtistList()''

The download_concerts() function gets concert data for a given artist,
access is provided through the ConcertList class.
''con = ConcertList(art[n])'' where 'n' is the index of a given artist.

Individual concert details are re-read by default, rather than cached
like the artist and concert lists.  Overall details are accessed
through the ConcertDetails class, and the songs and other files
are access through the ConcertFileList class."""

__version__ = '0.1'

from lma.config import (Config)

from lma.archive import (archive_open, full_path)

from lma.query import (Query, ProgressIter, IDENTIFIER, TITLE, COLLECTION,
                       MEDIATYPE, PUBDATE, DATE, YEAR, FORMAT,
                       BAND_QUERY, CONCERT_QUERY, STANDARD_FIELDS)

from lma.progress import (ProgressCallback, NullProgressBar)

from lma.database import (Db)

from lma.artist import (download_artists, 
                        clear_new_artists, 
                        ArtistList, Artist,
                        AVIEW_SELECTORS)

from lma.concert import (download_concerts,
                         clear_new_concerts,
                         ConcertList, Concert,
                         CVIEW_SELECTORS)

from lma.details import (ConcertDetails, ConcertFileList)

from download import (download_files)
