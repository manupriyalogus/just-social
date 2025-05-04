import wx
import wx.adv
import pyperclip


class ConnectionInfoDialog(wx.Dialog):
    def __init__(self, parent, connection_info):
        super().__init__(parent, title="Your Connection Information",
                         size=(500, 300))

        self.connection_info = connection_info
        self.init_ui()
        self.Center()

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Add header
        header = wx.StaticText(panel,
                               label="Share this information with your contacts")
        header_font = header.GetFont()
        header_font.SetPointSize(12)
        header.SetFont(header_font)

        # Add information fields
        info_grid = wx.FlexGridSizer(3, 2, 10, 10)

        # Onion Address
        onion_label = wx.StaticText(panel, label="Onion Address:")
        self.onion_text = wx.TextCtrl(panel,
                                      value=self.connection_info['onion_address'],
                                      style=wx.TE_READONLY)
        copy_onion_btn = wx.Button(panel, label="Copy")
        copy_onion_btn.Bind(wx.EVT_BUTTON,
                            lambda evt: self.copy_text(self.onion_text.GetValue()))

        # Public Key
        key_label = wx.StaticText(panel, label="Public Key:")
        self.key_text = wx.TextCtrl(panel,
                                    value=self.connection_info['public_key'],
                                    style=wx.TE_READONLY)
        copy_key_btn = wx.Button(panel, label="Copy")
        copy_key_btn.Bind(wx.EVT_BUTTON,
                          lambda evt: self.copy_text(self.key_text.GetValue()))

        # User ID
        user_label = wx.StaticText(panel, label="User ID:")
        self.user_text = wx.TextCtrl(panel,
                                     value=self.connection_info['user_id'],
                                     style=wx.TE_READONLY)
        copy_user_btn = wx.Button(panel, label="Copy")
        copy_user_btn.Bind(wx.EVT_BUTTON,
                           lambda evt: self.copy_text(self.user_text.GetValue()))

        # Add to grid
        info_grid.AddMany([
            (onion_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
            (wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND),
            (key_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
            (wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND),
            (user_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
            (wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
        ])

        # Add text controls and buttons to horizontal sizers
        onion_sizer = info_grid.GetItem(1).GetSizer()
        onion_sizer.Add(self.onion_text, 1, wx.EXPAND)
        onion_sizer.Add(copy_onion_btn, 0, wx.LEFT, 5)

        key_sizer = info_grid.GetItem(3).GetSizer()
        key_sizer.Add(self.key_text, 1, wx.EXPAND)
        key_sizer.Add(copy_key_btn, 0, wx.LEFT, 5)

        user_sizer = info_grid.GetItem(5).GetSizer()
        user_sizer.Add(self.user_text, 1, wx.EXPAND)
        user_sizer.Add(copy_user_btn, 0, wx.LEFT, 5)

        # Add note about sharing
        note = wx.StaticText(panel,
                             label=("Note: Share this information securely with your contacts.\n"
                                    "They will need this to send you messages."))
        note.SetForegroundColour(wx.Colour(128, 128, 128))

        # Add buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "OK")
        btn_sizer.Add(ok_button, 0, wx.ALL, 5)

        # Add everything to main sizer
        vbox.Add(header, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        vbox.Add(info_grid, 0, wx.ALL | wx.EXPAND, 10)
        vbox.Add(note, 0, wx.ALL, 10)
        vbox.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(vbox)

    def copy_text(self, text):
        """Copy text to clipboard"""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox("Copied to clipboard!", "Success",
                          wx.OK | wx.ICON_INFORMATION)