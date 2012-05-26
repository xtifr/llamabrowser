#!/usr/bin/env python
import lma
import wx

#
# some global ids
#
ARTIST_LIST_ID = 10
CONCERT_LIST_ID = 11

CONCERT_BACK_BUTTON_ID = 21

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
    def __init__(self, parent, id=-1):
        super(ArtistListPanel, self).__init__(parent, id)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # create the list widget
        self._listctrl = ArtistListCtrl(self, ARTIST_LIST_ID)

        # create the top row of widgets
        search = wx.SearchCtrl(self, -1)
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
    def download(self):
        if self.clist != None:
            self.clist.repopulate()
            self.reset()
    def clearNew(self):
        if self.clist != None:
            self.clist.clearNew()
            self.reset()
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
        search = wx.SearchCtrl(self, -1)
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

    # method handlers
    def setConcertMode(self, event):
        self._listctrl.setMode(event.GetString())
#
# Set up main frame
#
class WxLMAFrame(wx.Frame):
    def __init__(self, parent, ID, title, pos=wx.DefaultPosition,
                 size=(600, 400), style=wx.DEFAULT_FRAME_STYLE):
        super(WxLMAFrame, self).__init__(parent, ID, title, pos, size, style)

        self._artist = ArtistListPanel(self, -1)
        self._concert = ConcertListPanel(self, -1)
        self._panel = self._artist
        self._concert.Hide()

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

    def OnButton(self, event):
        """Method to handle various buttons."""
        ID = event.GetId()
        if ID == CONCERT_BACK_BUTTON_ID:
            self.replacePanel(self._artist)

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
