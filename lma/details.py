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
FMT_MP3 = "vbr mp3"
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
            if name in ['original', 'md5', 'format', 'album',
                        'title', 'track', 'size']:
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
    derivatives = {}
    other = []
    lossless = ""

    # we're going to sort with lower-case formats, but we want to be
    # able to recover the mixed-case formats for a nice display after.
    # this translate table will help us achieve that.
    xlate_fmt = {}

    for f in files:
        f_name = f['name']

        # make sure all of these have a title field
        if not 'title' in f:
            f['title'] = f_name

        # find the file's format
        if not 'format' in f:
            other.append(f)
            continue

        f_format = f['format']
        f_formatlc = f_format.lower()
        f_source = f['source'].lower()

        # lossless audio formats will always be the original
        if f_formatlc in lossless_audio_formats:
            songs[f_name] = f
            lossless = f_format
            continue

        # check for derivative audio file
        if f_formatlc in lossy_audio_formats and 'original' in f:
            # now we make the translate table (only needs lossy formats)
            derivatives.setdefault(f_formatlc, {})[f['original']] = f
            xlate_fmt[f_formatlc] = f_format
            continue

        # everything else goes in other
        other.append(f)

    # now sort the song filenames alphabetically
    tracks = songs.keys()
    tracks.sort()
    # build a 2d list of songs in track order
    songlist = []
    for trk in tracks:
        item = [songs[trk]]
        for fmt in lossy_audio_formats:
            if fmt in derivatives:
                if trk in derivatives[fmt]:
                    item.append(derivatives[fmt][trk])
                else: 
                    # we hope this never happens
                    item.append(None)
        songlist.append(item)
    # now build a table of formats using our xlate_table from above
    fmtlist = [lossless]
    for k in derivatives:
        fmtlist.append(xlate_fmt[k])

    return (songlist, other, fmtlist)

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
            if not field in self._data:
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
        self.concert = concert
        self.loadFromArchive()

    def loadFromArchive(self):
        """Get Files/Songlist from Archive."""
        data = get_filelist_data(self.concert.lmaid)
        (self._songs, self.others, self.formats) = organize_filelist(data)
        # this converts a type into a column# for the songs table
        self._idx = {fmt : i for i,fmt in enumerate(self.formats)}
        # default to first (lossless) format
        self.current_format = self.LosslessFormat()

    # support reading like an array
    # (need to add access to self._other too at some point)
    def __len__(self):
        return len(self._songs)
    def __getitem__(self, i):
        """Return a song of the currently selected format"""
        return self._songs[i][self._idx[self.current_format]]
    def __iter__(self):
        """Create an iterator for the songs"""
        for song in self._songs:
            yield song[self._idx[self.current_format]]
    @property
    def current_format(self):
        return self._current_format
    @current_format.setter
    def current_format(self, value):
        if value in self.formats:
            self._current_format = value
    def hasLossy(self):
        return len(self.formats) > 1
    def LosslessFormat(self):
        """Return the lossless format for this concert"""
        return self.formats[0]
