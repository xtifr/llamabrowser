#!/usr/bin/env python
import lma
import wx

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

class WxArtistListCtrl(wx.ListCtrl):
    """List box for artists."""
    def __init__(self, parent, id=-1, 
                 style = (wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL
                          | wx.LC_HRULES | wx.LC_VRULES)):
        super(WxArtistListCtrl, self).__init__(parent, id, style=style)
        self._list = lma.ArtistList(WxProgressBar)

        self.InsertColumn(0, "Name")
        self.InsertColumn(1, "Last Browsed")
        self.InsertColumn(2, "Favorite")

        self.SetColumnWidth(0, 350)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 75)

        self.reset()

    @property
    def list(self):
        """Access to the underlying artist list object."""
        return self._list
    def reset(self):
        self.SetItemCount(self.list.getCount())
    def setMode(self, mode):
        self.list.mode = mode
        self.reset()
    def download(self):
        self.list.repopulate()
        self.reset()

    # override widget methods
    def OnGetItemText(self, item, column):
        return self.list.getResult(item, column)
#
# Set up main frame
#
class WxLMAFrame(wx.Frame):
    def __init__(self, parent, ID, title, pos=wx.DefaultPosition,
                 size=(600, 400), style=wx.DEFAULT_FRAME_STYLE):
        super(WxLMAFrame, self).__init__(parent, ID, title, pos, size, style)

        panel = wx.Panel(self, -1)
        outersizer = wx.BoxSizer(wx.VERTICAL)
        innersizer = wx.BoxSizer(wx.HORIZONTAL)

        # add the inner sizer and the artist list to the outer sizer
        self._alist = WxArtistListCtrl(panel, -1)
        outersizer.Add(innersizer, 0, wx.EXPAND)
        outersizer.Add(self._alist, 1, wx.EXPAND)

        # create search and select widgets
        search = wx.SearchCtrl(panel, -1)
        sel_label = wx.StaticText(panel, -1, "Select: ")
        select = wx.Choice(panel, -1, choices=self._alist.list.mode_list)
        self.Bind(wx.EVT_CHOICE, self.setArtistMode)

        # add the select and search buttons to the inner sizer
        innersizer.Add(search, 0, wx.ALIGN_CENTER)
        innersizer.AddStretchSpacer()
        innersizer.Add(sel_label, 0, wx.ALIGN_CENTER)
        innersizer.Add(select, 0, wx.ALIGN_CENTER)

        # attach outer size, add status bar
        panel.SetSizer(outersizer)

        self.CreateStatusBar()
        self.SetStatusText("")

        # create menus
        menubar = wx.MenuBar()

        # file menu
        fileMenu = wx.Menu()
        fileMenu.Append(101, "&Fetch Artists", "Fetch/update artist list")
        fileMenu.Append(102, "&Clear New List", "Mark all artists seen.")
        fileMenu.Append(199, "&Quit", "Exit program")
        menubar.Append(fileMenu, "&File")

        # help menu
        helpMenu = wx.Menu()
        helpMenu.Append(201, "&About", "About LMABrowser")
        menubar.Append(helpMenu, "&Help")

        self.SetMenuBar(menubar)

        # bind menus
        self.Bind(wx.EVT_MENU, self.menuFetchArtists, id=101)
        self.Bind(wx.EVT_MENU, self.menuClearNewArtists, id=102)
        self.Bind(wx.EVT_MENU, self.menuQuit, id=199)

        self.Bind(wx.EVT_MENU, self.menuAbout, id=201)

    def setArtistMode(self, event):
        """Event handler, sets display mode."""
        self._alist.setMode(event.GetString())

    ## menu methods
                 
    def menuFetchArtists(self, event):
        self._alist.download()
    def menuClearNewArtists(self, event):
        self._alist.list.clearNew()
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
