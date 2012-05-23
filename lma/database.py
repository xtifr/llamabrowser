#!/usr/bin/env python
"""Local database access for LMA data.

Assuming sqlite3 for now.  May allow other DBs for shared access in
future versions."""
import os
import sqlite3

#
# TODO: expand this to use the appropriate config directory & stuff
_db_name = "lma.db"

class Db(object):
    """A handle for the singleton DB access."""
    _db = None
    _name = None
    def __init__(self, fname=_db_name):
        """make sure db is open."""
        # if we get a different name, we have to open a new db
        if Db._name != fname:
            self.close()
            Db._Name = fname
        # now see if we actually need to open anything
        if Db._db == None:
            # if there's no db there, we'll also have to populate it.
            found = os.path.exists(fname)
            Db._db = sqlite3.connect(fname)
            if not found:
                _populate_db(Db._db)
    def close(self):
        if Db._db:
            Db._db.close()
            Db._db = None

    def __getattr__(self, name):
        """Delegate unknown attributes to the singleton DB handle."""
        return getattr(Db._db, name)

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
    recnum INTEGER,
    version INTEGER,
    last_artist_read date
);
-- create single record
BEGIN;
INSERT INTO lma_config (recnum, version, last_artist_read) 
       VALUES (1, 1, NULL);
COMMIT;

-- drop in reverse order of creation to avoid foreign-key problems
DROP TABLE IF EXISTS song;
DROP TABLE IF EXISTS concert;
DROP TABLE IF EXISTS lastbrowse;
DROP TABLE IF EXISTS favorite;
DROP TABLE IF EXISTS newartist;
DROP TRIGGER IF EXISTS afterartist;
DROP INDEX IF EXISTS artistidx;
DROP TABLE IF EXISTS artist;

-- main artist table
CREATE TABLE artist (
    aid INTEGER PRIMARY KEY, 
    aname TEXT NOT NULL,
    lmaid TEXT UNIQUE NOT NULL -- LMA identifier
);

CREATE TABLE favorite (
    artistid INTEGER REFERENCES artist(aid)
);

CREATE TABLE lastbrowse (
    aid INTEGER REFERENCES artist(aid),
    browsedate DATE
);

CREATE TABLE newartist (
    aid INTEGER REFERENCES artist(aid)
);

CREATE TRIGGER afterartist AFTER INSERT ON artist
  FOR EACH ROW BEGIN
    INSERT INTO newartist (aid) VALUES (NEW.aid);
  END;

-- main concert table
CREATE TABLE concert (
    cid INTEGER PRIMARY KEY,
    ctitle TEXT NOT NULL,          --displayable name
    lmaid TEXT UNIQUE NOT NULL,
    cyear TEXT NOT NULL,
    cdate DATE,
    artistid INTEGER REFERENCES artist(aid)
);

-- song table
CREATE TABLE song (
    sid INTEGER PRIMARY KEY,
    sname TEXT NOT NULL,
    base_fname TEXT NOT NULL,  -- base filename (without extension)
    concertid INTEGER REFERENCES concert(cid)
);""")