#!/usr/bin/env python
"""Manage concert details info from the Archive.

Unlike artists and concerts, this doesn't use the Query class to load
details from the archive, because the details are stored in XML files."""

import os
import xml.sax
import xml.sax.handler as xmlhandler
import hashlib # for sha1
from . import archive
from . import concert

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
        if name in ["description", "coverage", "uploader", "md5s",
                    "taper", "lineage", "has_mp3", "discs"]:
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
            else:
                raise xml.sax.SAXParseException("Malformed _files.xml file")
    def endDocument(self):
        pass
    def getData(self):
        return self._data
                
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
