#!/usr/bin/env python
# Part of the Live Music Archive access library (lma)
#
# This library is copyright 2012 by Chris Waters.
# It is licensed under a liberal MIT/X11 style license;
# see the file "LICENSE" in this directory for details.

"""Local database access for LMA data.

Assuming sqlite3 for now.  May allow other DBs for shared access in
future versions."""
import sqlite3

import lma

class ArDb(object):
    """Handle for a local Internet Archive database."""

    def __init__(self, path):
        """Open db and create tables if necessary."""
        import os
        found = os.path.exists(str(path))
        self._db = sqlite3.connect(str(path))

        if not found:
            _populate_db(self._db)

    def close(self):
        if self._db:
            self._db.close()
            self._db = None

    def __getattr__(self, name):
        """Delegate unknown attributes to the DB handle."""
        return getattr(self._db, name)


class DbList(object):
    """Abstract base class for lists of DB records."""

    def __init__(self, db, ctor):
        """db is a handle for the database.
        ctor is the constructor for the list element type."""

        self._db = db
        self._search = None
        self._ctor = ctor
        # TODO: handle modes...
        self._data = []
        self.refresh() # virtual function defined by base classes

    def refresh():
        """Pure virtual function."""
        pass

    @property
    def search(self):
        """The current search string, limiting the selection."""
        return self._search
    @search.setter
    def search(self, string):
        self._search = str(string)
        self.refresh()
    @search.deleter
    def search(self):
        self._search = None
        self.refresh()

    # support reading like an array
    def __getitem__(self, i):
        return self._ctor(self._db, self._data[i])
    def __len__(self):
        return len(self._data)

class DbRecord(object):
    """Abstract base class for defining virtual records.
    
    Derived classes can define attributes that use getDBInfo to
    look up their values."""
    def __init__(self, db, Id):
        self._db = db
        self._value = str(int(Id))

    def getDbInfo(self, table, col, matchcol):
        """Find entry in table matching self."""
        c = self._db.cursor()
        value = c.execute("SELECT %s FROM %s WHERE %s = ?" % (
                col, table, matchcol), (self._value,)).fetchone()
        c.close()
        if value == None:
            return ""
        return value[0]

    def getDbBool(self, table, col, matchcol=None):
        """Special query for a boolean column."""
        if matchcol == None: matchcol = col
        val = self.getDbInfo(table, col, matchcol)
        if val == "": return False
        return True

    def setDbBool(self, table, col, flag):
        """Set the boolean by adding or deleting from a table."""
        c = self._db.cursor()
        # since this is a bool, we either add or delete
        if flag:
            c.execute("INSERT OR REPLACE INTO %s (%s) VALUES (?)" %
                      (table, col), (self._value,))
        else:
            c.execute("DELETE FROM %s WHERE %s = ?" %
                      (table, col), (self._value,))
        c.close()
        db.commit()

    def __str__(self):
        return str(self._value)
    def __int__(self):
        return int(self._value)

#
# Function to create our initial tables
#
def _populate_db(db):
    """Setup new database."""
    db.executescript("""
PRAGMA foreign_key = ON;

-- config table
DROP TABLE IF EXISTS lma_config;
CREATE TABLE lma_config (
    recnum INTEGER UNIQUE PRIMARY KEY,
    version INTEGER,
    last_artist_read DATE
);
-- create single record
BEGIN;
INSERT INTO lma_config (recnum, version, last_artist_read) 
       VALUES (1, 1, NULL);
COMMIT;

-- drop in reverse order of creation to avoid foreign-key problems
DROP TABLE IF EXISTS concert;
DROP TABLE IF EXISTS lastbrowse;
DROP TABLE IF EXISTS favorite;
DROP TABLE IF EXISTS newartist;
DROP TRIGGER IF EXISTS afterartist;
DROP INDEX IF EXISTS artistidx;
DROP TABLE IF EXISTS artist;

-- main artist table
CREATE TABLE artist (
    aid   INTEGER UNIQUE PRIMARY KEY, 
    aname VARCHAR(100) NOT NULL,
    lmaid VARCHAR(100) UNIQUE NOT NULL -- LMA identifier
);

CREATE TABLE favorite (
    artistid INTEGER UNIQUE REFERENCES artist(aid)
);

-- last time concert list downloaded for given artist
CREATE TABLE lastbrowse (
    aid INTEGER UNIQUE REFERENCES artist(aid),
    browsedate DATE
);

CREATE TABLE newartist (
    aid INTEGER UNIQUE REFERENCES artist(aid)
);
CREATE TRIGGER afterartist AFTER INSERT ON artist
  FOR EACH ROW BEGIN
    INSERT INTO newartist (aid) VALUES (NEW.aid);
  END;

-- main concert table
CREATE TABLE concert (
    cid      INTEGER UNIQUE PRIMARY KEY,
    ctitle   VARCHAR(100) NOT NULL,          --displayable name
    lmaid    VARCHAR(100) UNIQUE NOT NULL,
    cyear    CHAR(4) NOT NULL,
    cdate    DATE,
    artistid INTEGER REFERENCES artist(aid)
);

CREATE TABLE favconcert (
    concertid INTEGER UNIQUE REFERENCES concert(cid)
);

CREATE TABLE newconcert (
     cid INTEGER UNIQUE REFERENCES concert(cid)
);
CREATE TRIGGER afterconcert AFTER INSERT ON concert
  FOR EACH ROW BEGIN
    INSERT INTO newconcert (cid) VALUES (NEW.cid);
  END;

CREATE TABLE dlconcert (
    cid INTEGER UNIQUE REFERENCES concert(cid),
    dldate DATE
);

CREATE TABLE details (
    cid INTEGER UNIQUE REFERENCES concert(cid),
    coverage    VARCHAR(50),
    taper       VARCHAR(50),
    transferer  VARCHAR(50),
    lineage     TEXT,
    description TEXT,
    notes       TEXT
);
""")
