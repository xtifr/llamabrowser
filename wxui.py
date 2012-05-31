#!/usr/bin/env python
import lma
import wx

#
# some global ids
#
ARTIST_LIST_ID = 10
CONCERT_LIST_ID = 11
DETAILS_LIST_ID = 12

# ARIST_BACK_BUTTON_ID = 20 # doesn't exist
CONCERT_BACK_BUTTON_ID = 21
DETAILS_BACK_BUTTON_ID = 22

#
# progress bar for download callback
#

class WxProgressBar(object):
    """Provide progress bars for downloading."""
    def __init__(self, title, msg, max):
        self._dialog = wx.ProgressDialog(title, msg, maximum = max,
                                         style = wx.PD_APP_MODAL
                                         | wx.PD_AUTO_HIDE
                                         | wx.PD_ELAPSED_TIME)
    def update(self, percent):
        self._dialog.Update(percent)

    def done(self, max):
        self._dialog.Update(max)
        self._dialog.Destroy()

#
# artist listings
#

class ArtistListCtrl(wx.ListCtrl):
    """List box for artists."""
    def __init__(self, parent, id=-1, 
                 style = (wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL
                          | wx.LC_HRULES | wx.LC_VRULES)):
        super(ArtistListCtrl, self).__init__(parent, id, style=style)
        self.alist = lma.ArtistList(WxProgressBar)

        self.InsertColumn(0, "Artist Name")
        self.InsertColumn(1, "Last Browsed")
        self.InsertColumn(2, "Favorite")

        self.SetColumnWidth(0, 350)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 75)

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
                return "Y"
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
    """List box for concerts."""
    def __init__(self, parent, id=-1,
                 style = (wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL
                          | wx.LC_HRULES | wx.LC_VRULES)):
        super(ConcertListCtrl, self).__init__(parent, id, style=style)
        self._artist = None
        self.clist = None

        self.InsertColumn(0, "Concert Venue")
        self.InsertColumn(1, "Date")
        self.InsertColumn(2, "Favorite")

        self.SetColumnWidth(0, 350)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 75)

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
        self.clist = lma.ConcertList(artist, WxProgressBar)
        self.reset()
    def getArtistName(self):
        return self.clist.artistName

    # override widget methods
    def OnGetItemText(self, row, column):
        if column == 0:
            return self.clist[row].name
        elif column == 1:
            return self.clist[row].date
        elif column == 2:
            if self.clist[row].favorite:
                return "Y"
            return ""

class ConcertListPanel(wx.Panel):
    """Panel for listing an artist's concerts."""
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
        search = wx.SearchCtrl(self, -1, style = wx.TE_PROCESS_ENTER)
        search.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch)
        label = wx.StaticText(self, -1, "Select:")
        select = wx.Choice(self, -1, choices=lma.CVIEW_SELECTORS)
        self.Bind(wx.EVT_CHOICE, self.setConcertMode)

        # make a sizer for the top row
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        tmpsizer.Add(search, 0, wx.ALIGN_CENTER)
        tmpsizer.AddStretchSpacer()
        tmpsizer.Add(label, 0, wx.ALIGN_CENTER)
        tmpsizer.Add(select, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0, wx.EXPAND)

        # now it's time to add the listctrl
        sizer.Add(self._listctrl, 1, wx.EXPAND)

        # make a back button at the bottom
        button = wx.Button(self, CONCERT_BACK_BUTTON_ID, "Back")
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        tmpsizer.Add(button, 0, wx.ALIGN_CENTER)
        sizer.Add(tmpsizer, 0)

        self.SetSizer(sizer)

    def setArtist(self, artist):
        self._listctrl.setArtist(artist)
        self._label.SetLabel(artist.name)
    def download(self):
        self._listctrl.download()
    def clearNew(self):
        self._listctrl.clearNew()
    def getConcert(self, row):
        return self._listctrl.getConcert(row)


    # method handlers
    def setConcertMode(self, event):
        self._listctrl.setMode(event.GetString())
    def OnSearch(self, event):
        """Event handler for search widget."""
        self._listctrl.setSearch(event.GetString())
    def OnCancelSearch(self, event):
        """Event andler to clear search widget."""
        self._listctrl.clearSearch()

#
# Concert details panel
#
class ConcertDetailsMetaWindow(wx.ScrolledWindow):
    """Sub-panel for displaying concert meta info (like the desciption)."""
    def __init__(self, parent, id=-1):
        super(ConcertDetailsMetaWindow, self).__init__(parent, id)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # create a Static Box Sizer wrapping everything but the title
        sbox = wx.StaticBox(self, -1)
        sbsizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)

        # create inner static box sizers for description, notes, etc.
        box = wx.StaticBox(self, -1, "Description")
        self._description = wx.StaticText(self, -1, "")

        tmpsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        tmpsizer.Add(self._description, 0)
        sbsizer.Add(tmpsizer, 1)

        box = wx.StaticBox(self, -1, "Notes")
        self._notes = wx.StaticText(self, -1, "")

        tmpsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        tmpsizer.Add(self._notes, 0)
        sbsizer.Add(tmpsizer, 1)

        sizer.Add(sbsizer, 1)
        self.SetSizer(sizer)

    def setConcert(self, concert):
        """Add details to fields."""
        self._concert = concert
        self._details = lma.ConcertDetails(concert)
        self._description.SetLabel(self._details.description)
        self._notes.SetLabel(self._details.notes)

class ConcertSonglistWindow(wx.ListCtrl):
    """Sub-panel for displaying individual songs."""
    def __init__(self, parent, id=-1):
        style = (wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL
                 | wx.LC_HRULES | wx.LC_VRULES)
        super(ConcertSonglistWindow, self).__init__(parent, id, style=style)
        self._concert = None
        self._flist = None

        self.InsertColumn(0, "Track")
        self.InsertColumn(1, "Title")
        self.InsertColumn(2, "Formats")

        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 300)
        self.SetColumnWidth(2, 200)

    def reset(self):
        if self._flist != None:
            self.SetItemCount(len(self._flist))

    def setConcert(self, concert):
        """Add songs to fields."""
        self._concert = concert
        self._flist = lma.ConcertFileList(concert)
        self.reset()

    # override widget methods
    def OnGetItemText(self, row, column):
        if column == 0:
            return str(row+1)
        if column == 1:
            song = self._flist[row]
            if song.has_key('title'):
                return song['title']
            return song['name']
        if column == 2:
            return ",".join(self._flist.getFormats(row))

class ConcertDetailsPanel(wx.Panel):
    """Panel for listing details of a particular concert."""
    def __init__(self, parent, id=-1):
        super(ConcertDetailsPanel, self).__init__(parent, id)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # details widget and songlist widget in splitter window
        sstyle = wx.SP_LIVE_UPDATE | wx.SP_3D
        self._splitter = wx.SplitterWindow(self, -1, style=sstyle)
        self._details = ConcertDetailsMetaWindow(self._splitter, -1)
        self._slist = ConcertSonglistWindow(self._splitter, DETAILS_LIST_ID)

        # label field at top
        self._label = wx.StaticText(self, -1, "")
        tmpsizer = wx.BoxSizer()
        tmpsizer.AddStretchSpacer()
        tmpsizer.Add(self._label, 0)
        tmpsizer.AddStretchSpacer()
        sizer.Add(tmpsizer, 0, wx.ALIGN_CENTER)

        # add the splitter (with details and songlist), then split
        self._splitter.SetMinimumPaneSize(20) # prevents killing one
        self._splitter.SetSashGravity(0.5)
        self._splitter.SplitHorizontally(self._details, self._slist, 0)
        sizer.Add(self._splitter, 1, wx.EXPAND)

        # make a back button at the bottom
        button = wx.Button(self, DETAILS_BACK_BUTTON_ID, "Back")
        tmpsizer = wx.BoxSizer(wx.HORIZONTAL)
        tmpsizer.Add(button, 0)
        sizer.Add(tmpsizer, 0)

        self.SetSizer(sizer)

    def setConcert(self, concert):
        self._label.SetLabel(concert.name)
        self._details.setConcert(concert)
        self._slist.setConcert(concert)
        # now we should know how big the window is, so we can set the
        # sash in the middle.
        size = self._splitter.GetSize()
        self._splitter.SetSashPosition(size.GetHeight() / 2)

#
# Set up main frame
#
class WxLMAFrame(wx.Frame):
    def __init__(self, parent, ID, title, pos=wx.DefaultPosition,
                 size=(600, 400), style=wx.DEFAULT_FRAME_STYLE):
        super(WxLMAFrame, self).__init__(parent, ID, title, pos, size, style)

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
        fileMenu = wx.Menu()
        fileMenu.Append(101, "&Fetch Records", "Fetch/update from LMA")
        fileMenu.Append(102, "&Clear New List", "Mark all artists seen.")
        fileMenu.Append(199, "&Quit", "Exit program")
        menubar.Append(fileMenu, "&File")

        # help menu
        helpMenu = wx.Menu()
        helpMenu.Append(201, "&About", "About LMABrowser")
        menubar.Append(helpMenu, "&Help")

        self.SetMenuBar(menubar)

        # bind menus
        self.Bind(wx.EVT_MENU, self.menuFetch, id=101)
        self.Bind(wx.EVT_MENU, self.menuClearNew, id=102)
        self.Bind(wx.EVT_MENU, self.menuQuit, id=199)

        self.Bind(wx.EVT_MENU, self.menuAbout, id=201)

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
        elif ID == CONCERT_LIST_ID:
            self._details.setConcert(self._concert.getConcert(row))
            self.replacePanel(self._details)

    def OnButton(self, event):
        """Method to handle various buttons."""
        ID = event.GetId()
        if ID == CONCERT_BACK_BUTTON_ID:
            self.replacePanel(self._artist)
        elif ID == DETAILS_BACK_BUTTON_ID:
            self.replacePanel(self._concert)

    ## menu methods
                 
    def menuFetch(self, event):
        self._panel.download()
    def menuClearNew(self, event):
        self._panel.clearNew()
    def menuQuit(self, event):
        self.Close()

    def menuAbout(self, event):
        """Create and display 'About' window."""
        from wx.lib.wordwrap import wordwrap
        info = wx.AboutDialogInfo()
        info.Name = "LMA Browser"
        info.Version = lma.__version__
        info.Copyright = ("(c) 2012 Chris Waters")
        info.Description = wordwrap(
            "Browse and download concert recordings from the "
            "Internet Archive's Live Music Archive (LMA). "
            "The LMA features live concert recordings from "
            "thousands of taper-friendly bands, free for personal use.\n\n"

            "Recordings are available in lossless format (FLAC or SHN), and "
            "in many cases, as lossy MP3 or Ogg Vorbis as well.",
            350, wx.ClientDC(self))
        info.Developers = ["Chris Waters"]
        wx.AboutBox(info)

#
# main app
#

class LMAApp(wx.App):
    def OnInit(self):
        self.SetAppName("LMA Browser")
        win = WxLMAFrame(None, -1, "LMA Browser")
        win.Show()
        return True

def main():
    app = LMAApp()
    app.MainLoop()

if __name__ == '__main__':
    main()
