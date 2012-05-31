#!/usr/bin/env python
"""Manage concert details info from the Archive.

Unlike artists and concerts, this doesn't use the Query class to load
details from the archive, because the details are stored in XML files."""

import os
import xml.sax
import xml.sax.handler as xmlhandler
import hashlib # for md5/sha1
from . import database
from . import archive
from . import concert

# define audio formats:

# lossless
FMT_FLAC = "flac"
FMT_FLAC24 = "24bit flac"
FMT_SHN = "shorten"
FMT_WAV = "wave"
FMT_AIFF = "aiff"
FMT_WMA = "windows media audio"
FMT_ALA = "apple lossless audio"

lossless_audio_formats = [FMT_FLAC, FMT_FLAC24, FMT_SHN, FMT_WAV, FMT_AIFF,
                          FMT_WMA, FMT_ALA]

# lossy (derivative) formats
FMT_OGG = "ogg vorbis"
FMT_MP3 = "vbr mpt"
FMT_64MP3 = "64kbps mp3"

lossy_audio_formats = [FMT_OGG, FMT_MP3, FMT_64MP3 ]

# other assorted formats:
FMT_JPG = "jpeg"
FMT_PNG = "png"
FMT_GIF = "gif"
graphics_formats = [FMT_JPG, FMT_PNG, FMT_GIF]

# key fields in archive XML files
meta_fields = ["description", "coverage", "notes", "lineage",
               "taper", "transferer"]

#
# metadata SAX handler
#
class MetaXMLHandler(xmlhandler.ContentHandler):
    """Parser for the _meta.xml file.

    Fortunately, this file has a very simple, flat structure, so we don't
    have to worry about nested elements, just elements of interest."""
    def startDocument(self):
        """Set up the fields to store data."""
        self._data = {}
        self._key = None
        pass
    def startElement(self, name, attrs):
        """Check for elements of interest."""
        if name in meta_fields:
            self._key = name
            self._value = []
    def characters(self, content):
        """Accumulate data if we're in an element of interest."""
        if self._key != None:
            self._value.append(content)
    def endElement(self, name):
        """Finalize an element."""
        if self._key != None:
            self._data[self._key] = "".join(self._value).strip(" \n")
            self._key = None
    def endDocument(self):
        pass
    def getData(self):
        return self._data

def get_meta_data(lmaid):
    """Get the _meta.xml file with the concert description."""
    # relative path is concertid/concertid_meta.xml
    reader = MetaXMLHandler()
    hand = archive.archive_open("%s/%s_meta.xml" % (lmaid, lmaid))
    try:
        xml.sax.parse(hand, reader)
    finally:
        hand.close()
    return reader.getData()

#
# filelist SAX handler
#
class FileXMLHandler(xmlhandler.ContentHandler):
    """Parser for the _files.xml file.

    This one's a little trickier to parse than the meta file, as we have
    some mild nesting: file details are children of the file element."""
    def startDocument(self):
        """Set up the fields to store the data."""
        self._data = []
        self._filedata = None
        self._key = None
    def startElement(self, name, attrs):
        if name == "file":
            # found a new file
            self._filedata = {}
            self._filedata["name"] = attrs.getValue("name")
            self._filedata["source"] = attrs.getValue("source")
        elif self._filedata != None:
            # we're processing a file
            if name in ['original', 'md5', 'format', 'album', 'title', 'track']:
                self._key = name
                self._value = []
    def characters(self, content):
        """we only care about text in file subelements."""
        if self._key != None:
            self._value.append(content)
    def endElement(self, name):
        """Finalize an element."""
        if self._filedata != None:
            if self._key != None:
                self._filedata[self._key] = "".join(self._value).strip(" \n")
                self._key = None
            elif name == "file":
                self._data.append(self._filedata)
                self._filedata = None
    def endDocument(self):
        pass
    def getData(self):
        return self._data
                
#
# routines for downloading the filelist
#

def get_filelist_data(lmaid):
    """Get the _files.xml file with the song listing."""
    # relative path is concertid/concertid_files.xml
    reader = FileXMLHandler()
    hand = archive.archive_open("%s/%s_files.xml" % (lmaid, lmaid))
    try:
        xml.sax.parse(hand, reader)
    finally:
        hand.close()
    return reader.getData()


def organize_filelist(files):
    """organize the file data into something useful."""

    songs = {}
    derivatives = {} # orig_name : [record,...]
    other = []

    for f in files:
        # find the file's format
        if not f.has_key('format'):
            other.append(f)
            continue

        f_name = f['name']
        f_format = f['format'].lower()
        f_source = f['source'].lower()

        # lossless audio formats will always be the original
        if f_format in lossless_audio_formats:
            songs[f_name] = f
            continue

        # check for derivative audio file
        if ((f_format in lossy_audio_formats) and f.has_key('original')):
            # make value list if it doesn't exist
            if not derivatives.has_key(f['original']):
                derivatives[f['original']] = []
            # add record to value list
            derivatives[f['original']].append(f)
            continue

        # everything else goes in other
        other.append(f)

    # now sort the song filenames alphabetically
    tracks = songs.keys()
    tracks.sort()

    # also sort the derivative types
    for k in derivatives.iterkeys():
        derivatives[k].sort(lambda x,y : cmp(x['format'], y['format']))
    return (tracks, songs, derivatives, other)

#
# Concert details, like description, notes, etc.
#
class ConcertDetails(object):
    """Wrapper class for concert details.

    We get them from the LMA unless we have them cached locally.
    We don't save them (cache them) unless specifically asked."""
    def __init__(self, concert):
        """Get the details either from local cache or the LMA."""
        self._concert = concert
        self._saved = False
        self._data = None
        self.loadFromCache()
        if self._data == None:
            self.loadFromArchive()

    def loadFromArchive(self):
        """Get the details from the Archive."""
        lmaid = self._concert.lmaid
        self._data = get_meta_data(lmaid)
        # make sure we have all fields defined
        for field in meta_fields:
            if not self._data.has_key(field):
                self._data[field] = ""

    def saveToCache(self):
        """Write the details to the cache if necessary."""
        if self._saved == True:
            return
        db = database.Db()
        c = db.cursor()
        # make text versions of field list, with and without colons
        f1 = ",".join(meta_fields)
        f2 = ":" + ", :".join(meta_fields)
        # use field lists to insert into database
        c.execute("INSERT OR REPLACE INTO details"
                  " (cid, %s) VALUES (:cid, %s)" % (f1, f2), self._data)
        c.close()
        db.commit()
        self._saved = True

    def loadFromCache(self):
        """Try to get concert details from db.  If not there, return None."""

        db = database.Db()
        c = db.cursor()
        f1 = ",".join(meta_fields)
        c.execute("SELECT %s FROM details WHERE cid = ?" % f1,
                  (str(self._concert),))
        result = c.fetchone()
        if result == None:
            return
        self._data = {x : y  for x,y in zip(meta_fields, result)}
        self._saved = True

    @property
    def description(self):
        return self._data['description']
    @property
    def notes(self):
        return self._data['notes']

#
# general class representing list of archive files.
#

class ConcertFileList(object):
    """Represents a list of songs for a given show."""
    def __init__(self, concert):
        self._concert = concert
        self.loadFromArchive()

    def loadFromArchive(self):
        """Get Files/Songlist from Archive."""
        data = get_filelist_data(self._concert.lmaid)
        (tracks, songs, derivatives, others) = organize_filelist(data)
        self._tracks = tracks
        self._songs = songs
        self._derivatives = derivatives
        self._others = others

        self.types = [self.song(0)['format']]
        for rec in self.derivatives(0):
            self.types.append(rec['format'])

        # cache formats, as gathered from the first track
        self._formats = self.getFormats(0)

    def song(self, num):
        return self._songs[self._tracks[num]]
    def derivatives(self, num):
        return self._derivatives[self._tracks[num]]

    # support reading like an array
    # (need to add access to self._other too at some point)
    def __len__(self):
        return len(self._songs)
    def __getitem__(self, i):
        """Return an item -- either a song or a file."""
        return self.song(i)
    def getDerivatives(self, i):
        return self.derivatives(i)
    def getFormats(self, i):
        fmt = [self.song(i)['format']]
        for d in self.derivatives(i):
            fmt.append(d['format'])
        return fmt
    def getFormatFile(self, i, format):
        """Return the file of the specified type, or None."""
        if format.lower() == self.formats[0]:
            return self.song(i)
        for d in self.derivatives(i):
            if d['format'].lower() == format.lower():
                return d
        return None
    def getSongRemotePath(self, i, format):
        return "%s/%s" % (self._concert.lmaid,
                          self.getFormatFile(i, format)['name'])
