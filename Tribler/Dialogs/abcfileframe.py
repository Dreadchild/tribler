import wx
import os
import images
from base64 import b64encode
from Tribler.CacheDB.CacheDBHandler import TorrentDBHandler, MyPreferenceDBHandler
from Tribler.utilities import friendly_time, sort_dictlist
from common import CommonTriblerList



def showInfoHash(infohash):
    if infohash.startswith('torrent'):    # for testing
        return infohash
    try:
        n = int(infohash)
        return str(n)
    except:
        pass
    return b64encode(infohash)
#    try:
#        return encodestring(infohash)
#    except:
#        return infohash


class MyPreferenceList(CommonTriblerList):
    def __init__(self, parent, window_size):
        self.parent = parent
        self.mypref_db = parent.mypref_db
        self.min_rank = -1
        self.max_rank = 5
        CommonTriblerList.__init__(self, parent, window_size)

    def getColumns(self):
        format = wx.LIST_FORMAT_CENTER
        columns = [
            ('Torrent Name', format, 10),
            ('Content Name', format, 15),
            ('Rank', format, 8),
            ('Size', format, 8),
            ('Last Seen', format, 10)  
            ]
        return columns
        
    def getListKey(self):
        return ['torrent_name', 'content_name', 'rank', 'length', 'last_seen']
        
    def getCurrentSortColumn(self):
        return 1

    def getMaxNum(self):
        return 100
        
    def getText(self, data, row, col):
        key = self.list_key[col]
        original_data = data[row][key]
        if key == 'length':
            length = original_data/1024/1024.0
            return '%.2f MB'%(length)
        if key == 'last_seen':
            if original_data == 0:
                return 'Never'
            return friendly_time(original_data)
        return str(original_data)
        
    def reloadData(self):
        myprefs = self.mypref_db.getPrefList()
        keys = ['infohash', 'torrent_name', 'info', 'content_name', 'rank', 'last_seen']
        self.data = self.mypref_db.getPrefs(myprefs, keys)
        for i in xrange(len(self.data)):
            info = self.data[i]['info']
            self.data[i]['length'] = info.get('length', 0)
            if self.data[i]['torrent_name'] == '':
                self.data[i]['torrent_name'] = '\xff'
            if self.data[i]['content_name'] == '':
                self.data[i]['content_name'] = '\xff'
        
    def getMenuItems(self, min_rank, max_rank):
        menu_items = {}
        for i in range(min_rank, max_rank+1):
            id = wx.NewId()
            func = 'OnRank' + str(i - min_rank)
            func = getattr(self, func)
            if i == -1:
                label = "Fake File"
            elif i == 0:
                label = "No Rate"
            else:
                label = "*" * i
            menu_items[i] = {'id':id, 'func':func, 'label':label}
        return menu_items

    def OnRightClick(self, event=None):
        curr_idx = self.getSelectedItems()
        if not hasattr(self, "adjustRankID"):
            self.adjustRankID = wx.NewId()
            self.menu_items = self.getMenuItems(self.min_rank, self.max_rank)
            for i in self.menu_items:
                self.Bind(wx.EVT_MENU, self.menu_items[i]['func'], id=self.menu_items[i]['id'])
        if not hasattr(self, "deletePrefID"):
            self.deletePrefID = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnDeletePref, id=self.deletePrefID)
            
        # menu for change torrent's rank
        sm = wx.Menu()
        
        curr_rank = self.data[curr_idx[0]]['rank']
        for i in curr_idx[1:]:
            if self.data[i]['rank'] != curr_rank:
                curr_rank = None

        submenu = wx.Menu()
        idx = self.menu_items.keys()
        idx.sort()
        idx.reverse()    
        for i in idx:    # 5..-1
            if i == curr_rank:
                label = '> '+self.menu_items[i]['label']
            else:
                label = '   '+self.menu_items[i]['label']
            submenu.Append(self.menu_items[i]['id'], label)
            
        sm.AppendMenu(self.adjustRankID, "Rank items", submenu)
        sm.Append(self.deletePrefID, 'Delete')
        
        self.PopupMenu(sm, event.GetPosition())
        sm.Destroy()
        
    def changeRank(self, curr_idx, rank):
        torrent = self.data[curr_idx]
        torrent['rank'] = rank
        self.mypref_db.updateRank(torrent['infohash'], rank)
        self.SetStringItem(curr_idx, 2, str(rank))
        #print "Set torrent", showInfoHash(torrent['infohash']), "rank", rank
        
    def OnRank0(self, event=None):
        selected = self.getSelectedItems()
        for i in selected:
            self.changeRank(i, 0+self.min_rank)
        
    def OnRank1(self, event=None):
        selected = self.getSelectedItems()
        for i in selected:
            self.changeRank(i, 1+self.min_rank)
        
    def OnRank2(self, event=None):
        selected = self.getSelectedItems()
        for i in selected:
            self.changeRank(i, 2+self.min_rank)
        
    def OnRank3(self, event=None):
        selected = self.getSelectedItems()
        for i in selected:
            self.changeRank(i, 3+self.min_rank)
        
    def OnRank4(self, event=None):
        selected = self.getSelectedItems()
        for i in selected:
            self.changeRank(i, 4+self.min_rank)
        
    def OnRank5(self, event=None):
        selected = self.getSelectedItems()
        for i in selected:
            self.changeRank(i, 5+self.min_rank)
        
    def OnRank6(self, event=None):
        selected = self.getSelectedItems()
        for i in selected:
            self.changeRank(i, 6+self.min_rank)
        
    def OnDeletePref(self, event=None):
        selected = self.getSelectedItems()
        j = 0
        for i in selected:
            infohash = self.data[i]['infohash']
            self.mypref_db.deletePreference(infohash)
            self.DeleteItem(i-j)
            self.data.pop(i-j)
            j += 1
        self.mypref_db.sync()


class FileList(CommonTriblerList):
    def __init__(self, parent, window_size):
        self.parent = parent
        self.torrent_db = parent.torrent_db
        self.min_rank = -1
        self.max_rank = 5
        CommonTriblerList.__init__(self, parent, window_size)

    def getColumns(self):
        format = wx.LIST_FORMAT_CENTER
        columns = [
            ('Torrent ID', format, 8),
            ('Torrent Name', format, 10),
            ('Content Name', format, 15),
            ('Recommendation', format, 8),
            ('Size', format, 7),
            ('Seeder', format, 6),
            ('Leecher', format, 6),  
            ]
        return columns
        
    def getListKey(self):
        return ['infohash', 'torrent_name', 'content_name', 'relevance', 'length', 'seeder', 'leecher']
        
    def getCurrentSortColumn(self):
        return 3
        
    def getCurrentOrders(self):
         return [0, 0, 0, 1, 0, 0, 0]

    def getMaxNum(self):
        return 1000
        
    def getText(self, data, row, col):
        key = self.list_key[col]
        original_data = data[row][key]
        if key == 'relevance':
            return '%.2f'%(original_data/1000.0)
        if key == 'infohash':
            return showInfoHash(original_data)
        if key == 'length':
            length = original_data/1024/1024.0
            return '%.2f MB'%(length)
        if key == 'seeder' or key == 'leecher':
            if original_data < 0:
                return '-'
        return str(original_data)
        
    def reloadData(self):
        torrent_list = self.torrent_db.getOthersTorrentList()
        key = ['infohash', 'torrent_name', 'torrent_dir', 'relevance', 'info']
        self.data = self.torrent_db.getTorrents(torrent_list, key)

        for i in xrange(len(self.data)):
            info = self.data[i]['info']
            self.data[i]['length'] = info.get('length', 0)
            self.data[i]['content_name'] = info.get('name', 'unknown')
            if self.data[i]['torrent_name'] == '':
                self.data[i]['torrent_name'] = 'unknown'
            self.data[i]['seeder'] = -1
            self.data[i]['leecher'] = -1

    def OnDeleteTorrent(self, event=None):
        selected = self.getSelectedItems()
        j = 0
        for i in selected:
            infohash = self.data[i]['infohash']
            self.torrent_db.deleteTorrent(infohash)
            self.DeleteItem(i-j)
            self.data.pop(i-j)
            j += 1
        self.torrent_db.sync()
            
    def OnRightClick(self, event=None):
        if not hasattr(self, "deleteTorrentID"):
            self.deleteTorrentID = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnDeleteTorrent, id=self.deleteTorrentID)
            
        # menu for change torrent's rank
        sm = wx.Menu()
        sm.Append(self.deleteTorrentID, 'Delete')
        
        self.PopupMenu(sm, event.GetPosition())
        sm.Destroy()
        
    def OnActivated(self, event):
        self.curr_idx = event.m_itemIndex
        src = os.path.join(self.data[self.curr_idx]['torrent_dir'], self.data[self.curr_idx]['torrent_name'])
        if os.path.isfile(src):
            infohash = self.data[self.curr_idx]['infohash']
            str = "Start downloading " + showInfoHash(infohash) + "?"
            dlg = wx.MessageDialog(self, str,
                                   'Click and Download',
                                   #wx.OK | wx.ICON_INFORMATION
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION
                                   )
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_YES:
                src = os.path.join(self.data[self.curr_idx]['torrent_dir'], self.data[self.curr_idx]['torrent_name'])
                if os.path.isfile(src):
                    self.parent.clickAndDownload(src)


class MyPreferencePanel(wx.Panel):
    def __init__(self, frame, parent):
        self.parent = parent
        self.utility = frame.utility
        
        self.mypref_db = frame.mypref_db
        self.torrent_db = frame.torrent_db
        wx.Panel.__init__(self, parent, -1)

        mainbox = wx.BoxSizer(wx.VERTICAL)
        self.list=MyPreferenceList(self, frame.window_size)
        mainbox.Add(self.list, 1, wx.EXPAND|wx.ALL, 5)
        label = wx.StaticText(self, -1, "Right click on a torrent to assign a 1--5 star rating")
        mainbox.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(mainbox)
        self.SetAutoLayout(True)
        #self.Fit()
        self.Show(True)
        

class FilePanel(wx.Panel):
    def __init__(self, frame, parent):
        self.parent = parent
        self.utility = frame.utility
        
        self.mypref_db = frame.mypref_db
        self.torrent_db = frame.torrent_db
        wx.Panel.__init__(self, parent, -1)
        
        mainbox = wx.BoxSizer(wx.VERTICAL)
        self.list=FileList(self, frame.window_size)
        mainbox.Add(self.list, 1, wx.EXPAND|wx.ALL, 5)
        label = wx.StaticText(self, -1, "Double click on a torrent to start downloading")
        mainbox.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(mainbox)
        self.SetAutoLayout(True)
        #self.Fit()
        self.Show(True)
        
    def clickAndDownload(self, src):
        self.utility.queue.addtorrents.AddTorrentFromFile(src, forceasklocation = True)


class ABCFileFrame(wx.Frame):
    def __init__(self, parent):
        self.utility = parent.utility
        self.utility.abcfileframe = self
        
        width = 600
        height = 500
        self.window_size = wx.Size(width, height)
        wx.Frame.__init__(self, None, -1, self.utility.lang.get('tb_file_short'), size=wx.Size(width+20, height+60))
       
        self.mypref_db = self.utility.mypref_db
        self.torrent_db = self.utility.torrent_db


        # 1. Topbox contains the notebook
        mainbox = wx.BoxSizer(wx.VERTICAL)
        topbox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.notebook = wx.Notebook(self, -1)

        self.filePanel = FilePanel(self, self.notebook)
        self.notebook.AddPage(self.filePanel, "Recommended Torrents")

        self.myPreferencePanel = MyPreferencePanel(self, self.notebook)
        self.notebook.AddPage(self.myPreferencePanel, "My Download History")

        topbox.Add(self.notebook, 1, wx.EXPAND|wx.ALL, 5)

        # 2. Bottom box contains "Close" button
        botbox = wx.BoxSizer(wx.HORIZONTAL)

        button = wx.Button(self, -1, self.utility.lang.get('close'), style = wx.BU_EXACTFIT)
        wx.EVT_BUTTON(self, button.GetId(), self.OnCloseWindow)
        botbox.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

        # 3. Pack boxes together
        mainbox.Add(topbox, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        mainbox.Add(botbox, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
        self.SetSizerAndFit(mainbox)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Show()

    def updateMyPref(self):
        self.myPreferencePanel.list.loadList()
        
    def updateFile(self):
        self.filePanel.list.loadList()

    def OnCloseWindow(self, event = None):
        self.utility.frame.fileFrame = None
        self.utility.abcfileframe = None
        
        self.Destroy()
        
