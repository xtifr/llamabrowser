#!/usr/bin/env python
#
# lmabrowser - browse and download concerts from the Internet Archive's
#               Live Music Archive (the LMA, aka "the llama").
#
#   copyright 2012 by Chris Waters <xtifr.w@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""GUI browser using the lma library to access the Live Music Archive.

This is intended in part as a demo of the underlying lma library, which
I hope to use to build add-ons for standalone music systems like
Gnome's Rhythmbox and KDE's Amarok.  But it works well enough for now."""

import lma
import wx

# temporary def used until we set up gettext
_ = str

#
# some global ids
#
ARTIST_LIST_ID = 10
CONCERT_LIST_ID = 11
DETAILS_LIST_ID = 12

# ARTIST_BACK_BUTTON_ID = 20 # doesn't exist
CONCERT_BACK_BUTTON_ID = 21
DETAILS_BACK_BUTTON_ID = 22

#
# progress bar for download callback
#

class ProgressBar(object):
    """Provide progress bars for downloading."""
    def __init__(self, title, msg, max=100, can_cancel=False):
        style = wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_AUTO_HIDE
        if can_cancel:
            style = style | wx.PD_CAN_ABORT
        self._dialog = wx.ProgressDialog(title, msg, maximum = max, style=style)
    def update(self, percent):
        """Update progress bar, maybe message, and return cancel status."""
        ## This may have to change with wxwidgets 2.9
        return self._dialog.Update(percent)

    def done(self, error=None):
        if error != None:
            warn = wx.MessageDialog(self._dialog, error, style=wx.ICON_ERROR)
            warn.ShowModal()
            warn.Destroy()
        self._dialog.Destroy()

#
# Download dialog (for songs)
#
class DownloadDialog(wx.Dialog):
    """Download songs.  Call run() method to use."""
    def __init__(self, parent, id, songs, concert):
        cfg = lma.Config()
        self._songs = songs
        self._concert = concert
        self._subdir = cfg.artist_subdir

        formats = self._songs.formats
        # check for the default format (lossless is first, and always works)
        format_idx = 0
        if cfg.preferred_format != lma.default_formats[format_idx]:
            # see if we can find the preferred format
            for i, fmt in enumerate(formats):
                if fmt.lower() == cfg.preferred_format:
                    format_idx = i
                    break
        self._songs.current_format = formats[format_idx]

        title = _(u"Download %s") % songs.concert.name
        super(DownloadDialog, self).__init__(parent, id, title)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # format selection line
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, _(u"Format: "))
        tmpsizer.Add(label, 0, wx.ALIGN_CENTER)
        self._choice = wx.Choice(self, -1, choices=self._songs.formats)
        self._choice.SetSelection(format_idx)
        self.Bind(wx.EVT_CHOICE, self.OnFormat, self._choice)
        tmpsizer.Add(self._choice, 0, wx.ALIGN_CENTER)

        self._total = wx.StaticText(self, -1, "")
        tmpsizer.Add(self._total, 0, wx.ALIGN_CENTER|wx.LEFT, 5)
        sizer.Add(tmpsizer, 0, wx.LEFT, 5)

        # directory selection line
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _(u"Save in: "))
        tmpsizer.Add(label, 0, wx.ALIGN_CENTER)

        self._dir = wx.DirPickerCtrl(self, -1)
        # choose default path according to best available format
        if format_idx > 0:
            self._dir.SetPath(cfg.download_path)
        else:
            self._dir.SetPath(cfg.lossless_path)
        tmpsizer.Add(self._dir, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0, wx.LEFT, 5)

        # checkbox to create Artist subdirectory
        check = wx.CheckBox(self, -1, label=_(u"Use Artist Subdirectory?"))
        check.SetValue(self._subdir)
        self.Bind(wx.EVT_CHECKBOX, self.OnSubdir, check)
        sizer.Add(check, 0, wx.LEFT, 5)

        # now the main songlist
        names = [song['title'] for song in self._songs]
        self._list = wx.CheckListBox(self, -1, choices=names)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnSongChecked, self._list)
        # check them all by default
        for i in range(len(self._songs)):
            self._list.Check(i, True)

        sizer.Add(self._list, 1, wx.ALL, 5)

        bsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        if bsizer != None:
            sizer.Add(bsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.showTotal()
        self.SetSizer(sizer)

    def showTotal(self):
        """Display total for current format."""
        total = sum([int(song['size']) for i,song in enumerate(self._songs)
                    if self._list.IsChecked(i)])
        if total < 1e6:
            val = "%.2fk" % (total/1e3)
        elif total < 1e9:
            val = "%.2fM" % (total/1e6)
        else:
            val = "%.2fG" % (total/1e9)
        self._total.SetLabel(_(u"Total Size: %s") % val)

    def run(self):
        """Shows self, and then tries to download if OK selected."""
        while self.ShowModal() == wx.ID_OK:
            artist = None
            if self._subdir:
                artist =self._concert.artist.name
            to_get = [song for i, song in enumerate(self._songs)
                      if self._list.IsChecked(i)]
            if lma.download_files(to_get, self._concert, self._dir.GetPath(),
                                  artist, ProgressBar):
                break
        self.Destroy()

    # event bindings
    def OnFormat(self, event):
        """Select the file format"""
        format = event.GetString()
        cfg = lma.Config()
        self._songs.current_format = format
        self.showTotal()
        # change dir to match
        if (format == self._songs.LosslessFormat()):
            if (self._dir.GetPath() == cfg.download_path):
                self._dir.SetPath(cfg.lossless_path)
        elif (self._dir.GetPath() == cfg.lossless_path):
            self._dir.SetPath(cfg.download_path)

    def OnSubdir(self, event):
        self._subdir = event.IsChecked()
    def OnSongChecked(self, event):
        """Just update the totals"""
        self.showTotal()

#
# Configuration
#
class ConfigurationDialog(wx.Dialog):
    """Set configuration items."""
    def __init__(self, parent, id):
        super(ConfigurationDialog, self).__init__(parent, id,
                                                  _(u"Configuration"))
        cfg = lma.Config()
        sizer = wx.BoxSizer(wx.VERTICAL)
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)

        # main download directory
        label = wx.StaticText(self, -1, _(u"Default download directory: "))
        tmpsizer.Add(label, 0, wx.ALIGN_CENTER)
        self.dlpick = wx.DirPickerCtrl(self, -1)
        self.dlpick.SetPath(cfg.download_path)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDownloadPick, self.dlpick)
        tmpsizer.Add(self.dlpick, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0, wx.ALL, 5)

        # optional extra directory for lossless downloads
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _(u"Lossless directory (optional): "))
        tmpsizer.Add(label, 0, wx.ALIGN_CENTER)
        self.llpick = wx.DirPickerCtrl(self, -1)
        self.llpick.SetPath(cfg.lossless_path)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnLosslessPick, self.llpick)
        tmpsizer.Add(self.llpick, 0, wx.ALIGN_CENTER)
        self.llcheck = wx.CheckBox(self, -1)
        if cfg.download_path != cfg.lossless_path:
            self.llcheck.SetValue(True)
        else:
            self.llpick.Enable(False)
        self.Bind(wx.EVT_CHECKBOX, self.OnLosslessCheck, self.llcheck)
        tmpsizer.Add(self.llcheck, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0, wx.ALL, 5)

        # use artist subdirectory?
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        check = wx.CheckBox(self, -1,
                            _(u"Put concert folder in separate artist folder?"))
        if cfg.artist_subdir:
            check.SetValue(True)
        self.Bind(wx.EVT_CHECKBOX, self.OnArtistCheck, check)
        tmpsizer.Add(check, 0)
        sizer.Add(tmpsizer, 0, wx.ALL, 5)

        # preferred format
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1,
                              _(u"Preferred (default) format to download: "))
        tmpsizer.Add(label, 0, wx.ALIGN_CENTER)
        self._choice = wx.Choice(self, -1, choices=lma.default_formats)
        for i,fmt in enumerate(lma.default_formats):
            if fmt == cfg.preferred_format:
                self._choice.SetSelection(i)
        self.Bind(wx.EVT_CHOICE, self.OnFormatChoice, self._choice)
        tmpsizer.Add(self._choice, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0, wx.ALL, 5)

        bsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        if bsizer != None:
            sizer.Add(bsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.SetSizer(sizer)

    # event bindings
    def OnDownloadPick(self, event):
        cfg = lma.Config()
        cfg.download_path = self.dlpick.GetPath()
    def OnLosslessPick(self, event):
        cfg = lma.Config()
        cfg.lossless_path = self.llpick.GetPath()
    def OnLosslessCheck(self, event):
        cfg = lma.Config()
        self.llpick.Enable(self.llcheck.GetValue())
        if not self.llcheck.GetValue():
            self.llpick.SetPath(cfg.download_path)
    def OnArtistCheck(self, event):
        cfg = lma.Config()
        cfg.artist_subdir = bool(event.GetInt())
    def OnFormatChoice(self, event):
        cfg = lma.Config()
        cfg.preferred_format = event.GetString()

#
# artist listings
#
class ArtistListCtrl(wx.ListCtrl):
    """List box for artists."""
    def __init__(self, parent, id=-1, 
                 style = (wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL
                          | wx.LC_HRULES | wx.LC_VRULES)):
        super(ArtistListCtrl, self).__init__(parent, id, style=style)
        self.alist = lma.ArtistList(ProgressBar)

        self.InsertColumn(0, _(u"Artist Name"))
        self.InsertColumn(1, _(u"Last Browsed"))
        self.InsertColumn(2, _(u"Favorite"))

        self.SetColumnWidth(0, 350)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 75)

        # mark columns as centered
        li = self.GetColumn(1)
        li.SetAlign(wx.LIST_FORMAT_CENTER)
        self.SetColumn(1, li)
        li = self.GetColumn(2)
        li.SetAlign(wx.LIST_FORMAT_CENTER)
        self.SetColumn(2, li)

        self.reset()

    def reset(self):
        self.SetItemCount(len(self.alist))
    def setMode(self, mode):
        self.alist.mode = mode
        self.reset()
    def setSearch(self, string):
        self.alist.search = string
        self.reset()
    def clearSearch(self):
        del(self.alist.search)
        self.reset()
    def download(self):
        self.alist.repopulate()
        self.reset()
    def clearNew(self):
        self.alist.clearNew()
        self.reset()
    def getArtist(self, row):
        return self.alist[row]

    # override widget methods
    def OnGetItemText(self, item, column):
        if column == 0:
            return self.alist[item].name
        elif column == 1:
            return self.alist[item].browsedate
        elif column == 2:
            if self.alist[item].favorite:
                return u"\u2665" # unicode heart
            return ""

class ArtistListPanel(wx.Panel):
    """Panel for listing the LMA's artists."""
    def __init__(self, parent, id=-1):
        super(ArtistListPanel, self).__init__(parent, id)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # create the list widget
        self._listctrl = ArtistListCtrl(self, ARTIST_LIST_ID)

        # create the top row of widgets
        search = wx.SearchCtrl(self, -1, style = wx.TE_PROCESS_ENTER)
        search.SetDescriptiveText(_(u"Search Artists"))
        search.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch)
        label = wx.StaticText(self, -1, "Select:")
        select = wx.Choice(self, -1, choices=lma.AVIEW_SELECTORS)
        self.Bind(wx.EVT_CHOICE, self.setArtistMode)

        # make a sizer for the top row
        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        topsizer.Add(search, 0, wx.ALIGN_CENTER)
        topsizer.AddStretchSpacer()
        topsizer.Add(label, 0, wx.ALIGN_CENTER)
        topsizer.Add(select, 0, wx.ALIGN_CENTER)

        # make a sizer for the panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topsizer, 0, wx.EXPAND)
        sizer.Add(self._listctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def download(self):
        self._listctrl.download()
    def clearNew(self):
        self._listctrl.clearNew()
    def getArtist(self, row):
        return self._listctrl.getArtist(row)

    # method handlers
    def setArtistMode(self, event):
        """Event handler, sets display mode."""
        self._listctrl.setMode(event.GetString())
    def OnSearch(self, event):
        """Event handler for search widget."""
        self._listctrl.setSearch(event.GetString())
    def OnCancelSearch(self, event):
        """Event handler to clear search widget"""
        self._listctrl.clearSearch()

#
# concert listings
#
class ConcertListCtrl(wx.ListCtrl):
    """List box for concerts.  Must be initialized with setArtist()."""
    def __init__(self, parent, id=-1,
                 style = (wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL
                          | wx.LC_HRULES | wx.LC_VRULES)):
        super(ConcertListCtrl, self).__init__(parent, id, style=style)
        self._artist = None
        self.clist = None

        self.InsertColumn(0, _(u"Date"))
        self.InsertColumn(1, _(u"Concert Venue"))
        self.InsertColumn(2, _(u"Favorite"))

        self.SetColumnWidth(0, 100)
        self.SetColumnWidth(1, 350)
        self.SetColumnWidth(2, 75)

        # mark column as centered
        li = self.GetColumn(0)
        li.SetAlign(wx.LIST_FORMAT_CENTER)
        self.SetColumn(0, li)
        li = self.GetColumn(2)
        li.SetAlign(wx.LIST_FORMAT_CENTER)
        self.SetColumn(2, li)

    def reset(self):
        if self.clist != None:
            self.SetItemCount(len(self.clist))
    def setMode(self, mode):
        if self.clist != None:
            self.clist.mode = mode
            self.reset()
    def setSearch(self, string):
        if self.clist != None:
            self.clist.search = string
            self.reset()
    def clearSearch(self):
        if self.clist != None:
            del(self.clist.search)
            self.reset()
    def download(self):
        if self.clist != None:
            self.clist.repopulate()
            self.reset()
    def clearNew(self):
        if self.clist != None:
            self.clist.clearNew()
            self.reset()
    def getConcert(self, row):
        return self.clist[row]
    def setArtist(self, artist):
        """Set artist to display concerts for.  Must be called before using."""
        self._artist = artist
        self.clist = lma.ConcertList(artist, ProgressBar)
        # move to top
        if self.GetItemCount() > 0:
            self.EnsureVisible(0)
        self.reset()
    def getArtistName(self):
        return self.clist.artistName
    def toggleFavorite(self):
        self._artist.favorite = not self._artist.favorite
        if self._artist.favorite:
            msg = _(u"%s is now marked as a favorite") % self._artist.name
            cap = _(u"Favorite set")
            style = wx.ICON_INFORMATION | wx.OK
        else:
            msg = _(u"%s is no longer marked as a favorite") % self._artist.name
            cap = _(u"Favorite cleared")
            style = wx.ICON_EXCLAMATION | wx.OK
        popup = wx.MessageDialog(self, msg, caption=cap, style=style)
        popup.ShowModal()
        popup.Destroy()

    # override widget methods
    def OnGetItemText(self, row, column):
        if column == 0:
            return self.clist[row].date
        elif column == 1:
            return self.clist[row].name
        elif column == 2:
            if self.clist[row].favorite:
                return "\u2665" # unicode heart
            return ""

class ConcertListPanel(wx.Panel):
    """Panel for listing an artist's concerts.

    Must call setArtist() before first use."""

    def __init__(self, parent, id=-1):
        super(ConcertListPanel, self).__init__(parent, id)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # create the list widget
        self._listctrl = ConcertListCtrl(self, CONCERT_LIST_ID)

        # label field at top
        self._label = wx.StaticText(self, -1, "")
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        tmpsizer.AddStretchSpacer()
        tmpsizer.Add(self._label, 0)
        tmpsizer.AddStretchSpacer()
        sizer.Add(tmpsizer, 0, wx.ALIGN_CENTER)

        # create the top row of widgets
        self._search = wx.SearchCtrl(self, -1, style = wx.TE_PROCESS_ENTER)
        self._search.SetDescriptiveText(_(u"Search Concerts"))
        self._search.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch)
        label = wx.StaticText(self, -1, _(u"Select:"))
        self._choice = wx.Choice(self, -1, choices=lma.CVIEW_SELECTORS)
        self.Bind(wx.EVT_CHOICE, self.setConcertMode, self._choice)

        # make a sizer for the top row
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        tmpsizer.Add(self._search, 0, wx.ALIGN_CENTER)
        tmpsizer.AddStretchSpacer()
        tmpsizer.Add(label, 0, wx.ALIGN_CENTER)
        tmpsizer.Add(self._choice, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0, wx.EXPAND)

        # now it's time to add the listctrl
        sizer.Add(self._listctrl, 1, wx.EXPAND)

        # make a back button at the bottom
        button = wx.Button(self, CONCERT_BACK_BUTTON_ID, _(u"Back"))
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        tmpsizer.Add(button, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0)

        self.SetSizer(sizer)

    def setArtist(self, artist):
        """Choose the artist to display.  Must be called before using."""
        self._listctrl.setArtist(artist)
        self._label.SetLabel(artist.name)
        # reset search/choice widgets
        self._search.Clear()
        self._choice.SetSelection(0)

    def download(self):
        self._listctrl.download()
    def clearNew(self):
        self._listctrl.clearNew()
    def getConcert(self, row):
        return self._listctrl.getConcert(row)
    def toggleFavorite(self):
        self._listctrl.toggleFavorite()

    # method handlers
    def setConcertMode(self, event):
        self._listctrl.setMode(event.GetString())
    def OnSearch(self, event):
        """Event handler for search widget."""
        self._listctrl.setSearch(event.GetString())
    def OnCancelSearch(self, event):
        """Event handler to clear search widget."""
        self._listctrl.clearSearch()

#
# Concert details panel
#
class ConcertDetailsMetaWindow(wx.ScrolledWindow):
    """Sub-panel for displaying concert meta info (like the desciption).

    Must call setConcert() before actually using."""

    def __init__(self, parent, id=-1):
        super(ConcertDetailsMetaWindow, self).__init__(parent, id)
        self.SetScrollRate(20, 20)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # create static box sizers for description, notes, etc.
        box = wx.StaticBox(self, -1, _(u"Description"))
        txtstyle = wx.TE_READONLY | wx.TE_MULTILINE
        self._description = wx.TextCtrl(self, -1, "", style=txtstyle)

        tmpsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        tmpsizer.Add(self._description, 1, wx.EXPAND)
        sizer.Add(tmpsizer, 1, wx.EXPAND)

        box = wx.StaticBox(self, -1, _(u"Notes"))
        self._notes = wx.TextCtrl(self, -1, "", style=txtstyle)

        tmpsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        tmpsizer.Add(self._notes, 1, wx.EXPAND)
        sizer.Add(tmpsizer, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def setConcert(self, concert):
        """Add details to fields, make panel ready for use."""
        self._concert = concert
        self._details = lma.ConcertDetails(concert)

        # replace description and notes, and move to top
        self._description.Replace(0, self._description.GetLastPosition(),
                                  self._details.description)
        self._description.ShowPosition(0)
        self._notes.Replace(0, self._notes.GetLastPosition(), 
                            self._details.notes)
        self._notes.ShowPosition(0)

class ConcertSongListWindow(wx.ListCtrl):
    """Sub-panel for displaying individual songs.

    Must call setConcert() before actual use."""

    def __init__(self, parent, id=-1):
        style = (wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL
                 | wx.LC_HRULES | wx.LC_VRULES)
        super(ConcertSongListWindow, self).__init__(parent, id, style=style)
        self._concert = None
        self._flist = None

        self.InsertColumn(0, _(u"Track"))
        self.InsertColumn(1, _(u"Title"))
        self.InsertColumn(2, _(u"Format"))
        self.InsertColumn(3, _(u"Has Lossy"))

        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 350)
        self.SetColumnWidth(2, 80)
        self.SetColumnWidth(3, 80)

        # mark columns as centered
        li = self.GetColumn(0)
        li.SetAlign(wx.LIST_FORMAT_CENTER)
        self.SetColumn(0, li)
        li = self.GetColumn(2)
        li.SetAlign(wx.LIST_FORMAT_CENTER)
        self.SetColumn(2, li)
        li = self.GetColumn(3)
        li.SetAlign(wx.LIST_FORMAT_CENTER)
        self.SetColumn(3, li)

    def reset(self):
        if self._flist != None:
            self.SetItemCount(len(self._flist))

    def setConcert(self, concert):
        """Add songs to fields."""
        self._concert = concert
        # move to top
        if self.GetItemCount() > 0:
            self.EnsureVisible(0)
        self._flist = lma.ConcertFileList(concert)
        self.reset()

    def OnGetItemText(self, row, column):
        if column == 0:
            return str(row+1)
        if column == 1:
            song = self._flist[row]
            return song['title']
        if column == 2:
            return self._flist.LosslessFormat()
        if column == 3:
            return self._flist.hasLossy()
    def toggleFavorite(self):
        self._concert.favorite = not self._concert.favorite
        if self._concert.favorite:
            msg = _(u"%s is now marked as a favorite") % self._concert.name
            cap = _(u"Favorite set")
            style = wx.ICON_INFORMATION | wx.OK
        else:
            msg = _(u"%s is no longer marked as a favorite") % self._concert.name
            cap = _(u"Favorite cleared")
            style = wx.ICON_EXCLAMATION | wx.OK
        popup = wx.MessageDialog(self, msg, caption=cap, style=style)
        popup.ShowModal()
        popup.Destroy()
    def download(self):
        frame = DownloadDialog(self, -1, self._flist, self._concert)
        result = frame.run()
        frame.Destroy()

class ConcertDetailsPanel(wx.Panel):
    """Panel for listing details of a particular concert.

    Must call setConcert() before actual use.  This will also initialize
    its metadata and song listing subpanels."""

    def __init__(self, parent, id=-1):
        super(ConcertDetailsPanel, self).__init__(parent, id)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # details widget and songlist widget in notebook frame
        self._pad = wx.Notebook(self, -1, style=wx.NB_TOP)
        self._details = ConcertDetailsMetaWindow(self._pad, -1)
        self._slist = ConcertSongListWindow(self._pad, DETAILS_LIST_ID)
        self._pad.AddPage(self._details, _(u"Details"), True)
        self._pad.AddPage(self._slist, _(u"Songs"), False)

        # label field at top
        self._label = wx.StaticText(self, -1, "")
        tmpsizer = wx.BoxSizer()
        tmpsizer.AddStretchSpacer()
        tmpsizer.Add(self._label, 0)
        tmpsizer.AddStretchSpacer()
        sizer.Add(tmpsizer, 0, wx.ALIGN_CENTER)

        # Add the notebook (with details and songlist)
        sizer.Add(self._pad, 1, wx.EXPAND)

        # make a back button at the bottom
        button = wx.Button(self, DETAILS_BACK_BUTTON_ID, _(u"Back"))
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        tmpsizer.Add(button, 0)
        sizer.Add(tmpsizer, 0)

        self.SetSizer(sizer)

    def setConcert(self, concert):
        """Choose concert to display.  Must be called before using."""
        self._label.SetLabel(concert.name)
        self._details.setConcert(concert)
        self._slist.setConcert(concert)

    def toggleFavorite(self):
        self._slist.toggleFavorite()

    def download(self):
        """Downloader for concert files."""
        self._slist.download()
#
# Set up main frame
#
class LMAFrame(wx.Frame):
    def __init__(self, parent, ID, title, size=(600, 450)):
        super(LMAFrame, self).__init__(parent, ID, title, size=size)

        self._artist = ArtistListPanel(self, -1)
        self._concert = ConcertListPanel(self, -1)
        self._details = ConcertDetailsPanel(self, -1)
        self._panel = self._artist
        self._concert.Hide()
        self._details.Hide()

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._artist, 1, wx.EXPAND)
        self.SetSizer(self._sizer)

        # some general navigation bindings
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListItem)
        self.Bind(wx.EVT_BUTTON, self.OnButton)

        # create statusbar
        self.CreateStatusBar()
        self.SetStatusText("")

        # create menus
        menubar = wx.MenuBar()

        # file menu
        self._fileMenu = wx.Menu()
        self._fileMenu.Append(101, _(u"&Download"),
                              _(u"Fetch/update from LMA"))
        self._fileMenu.Append(102, _(u"&Clear New List"),
                              _(u"Mark all as seen."))
        self._fileMenu.Append(103, _(u"&Mark Favorite"),
                              _(u"Mark this as a favorite."))
        self._fileMenu.Enable(103, False)
        self._fileMenu.Append(wx.ID_EXIT, _(u"&Quit"), _(u"Exit program"))
        menubar.Append(self._fileMenu, _(u"&File"))

        # edit menu
        self._editMenu = wx.Menu()
        self._editMenu.Append(201, _(u"Preferences"), _(u"Set preferences"))
        menubar.Append(self._editMenu, _(u"Edit"))

        # help menu
        self._helpMenu = wx.Menu()
        self._helpMenu.Append(wx.ID_ABOUT, _(u"&About"), _(u"About LMABrowser"))
        menubar.Append(self._helpMenu, _(u"&Help"))

        self.SetMenuBar(menubar)

        # bind menus
        self.Bind(wx.EVT_MENU, self.menuFetch, id=101)
        self.Bind(wx.EVT_MENU, self.menuClearNew, id=102)
        self.Bind(wx.EVT_MENU, self.menuFavorite, id=103)

        self.Bind(wx.EVT_MENU, self.menuPreferences, id=201)

        self.Bind(wx.EVT_MENU, self.menuQuit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.menuAbout, id=wx.ID_ABOUT)

    #
    def replacePanel(self, new):
        """Choose a new panel."""
        if new == self._panel:
            return
        self.Freeze()
        self._panel.Hide()
        new.Show()
        self._sizer.Replace(self._panel, new)
        self._sizer.Layout()
        self._panel = new
        self.Thaw()

    # event methods
    def OnListItem(self, event):
        """Method to handle list item selection."""
        ID = event.GetId()
        row = event.GetIndex()
        if ID == ARTIST_LIST_ID:
            self._concert.setArtist(self._artist.getArtist(row))
            self.replacePanel(self._concert)
            self._fileMenu.Enable(103, True) # allow toggling favorites
        elif ID == CONCERT_LIST_ID:
            self._details.setConcert(self._concert.getConcert(row))
            self.replacePanel(self._details)
            self._fileMenu.Enable(102, False) # no new list to clear

    def OnButton(self, event):
        """Method to handle various buttons."""
        ID = event.GetId()
        if ID == CONCERT_BACK_BUTTON_ID:
            self.replacePanel(self._artist)
            self._fileMenu.Enable(103, False) # no toggling favorites
        elif ID == DETAILS_BACK_BUTTON_ID:
            self.replacePanel(self._concert)
            self._fileMenu.Enable(102, True) # allow clearing new-list

    ## menu methods
                 
    def menuFetch(self, event):
        self._panel.download()
    def menuClearNew(self, event):
        self._panel.clearNew()
    def menuFavorite(self, event):
        self._panel.toggleFavorite()
    def menuQuit(self, event):
        self.Close()

    def menuPreferences(self, event):
        cfg = lma.Config()
        win = ConfigurationDialog(self, -1)
        if win.ShowModal() == wx.ID_OK:
            cfg.write()
        else:
            cfg.read()
        win.Destroy()

    def menuAbout(self, event):
        """Create and display 'About' window."""
        from wx.lib.wordwrap import wordwrap
        info = wx.AboutDialogInfo()
        info.Name = _(u"LMA Browser")
        info.Version = lma.__version__
        info.Copyright = (u"\u24d2 2012 Chris Waters")
        info.Description = wordwrap(
            _(u"Browse and download concert recordings from the "
            "Internet Archive's Live Music Archive (LMA). "
            "The LMA features live concert recordings from "
            "thousands of taper-friendly bands, free for personal use.\n\n"

            "Recordings are available in lossless format (FLAC or SHN), and "
            "in many cases, as lossy MP3 or Ogg Vorbis as well."),
            350, wx.ClientDC(self))
        info.Developers = ["Chris Waters <xtifr.w@gmail.org>"]
        wx.AboutBox(info)

#
# main app
#

class LMAApp(wx.App):
    def OnInit(self):
        self.SetAppName("LMA Browser")
        win = LMAFrame(None, -1, _(u"LMA Browser"))
        win.Show()
        return True

def main():
    lma.Config("~/.LMABrowser", create=True)
    app = LMAApp()
    app.MainLoop()

if __name__ == '__main__':
    main()
