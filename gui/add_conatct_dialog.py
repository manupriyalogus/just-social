import wx
import wx.adv


class AddContactDialog(wx.Dialog):
    def __init__(self, parent, user_data, messenger, db):
        super().__init__(parent, title="Add Contact", size=(500, 400))
        self.db = db
        self.user_data = user_data
        self.messenger = messenger
        self.init_ui()
        self.Center()

    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Separator
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)

        # Connection Info Section
        main_sizer.Add(self.user_profile_section(panel), 0, wx.EXPAND | wx.ALL, 10)

        # Bottom Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(panel, label="Save")
        cancel_btn = wx.Button(panel, label="Cancel")

        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        button_sizer.Add(save_btn, 0, wx.ALL, 5)
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(main_sizer)

    def user_profile_section(self, parent):
        box = wx.StaticBox(parent, label="User Information")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        grid = wx.FlexGridSizer(3, 2, 10, 10)  # 3 rows, 2 columns (label + input)

        # User Name
        grid.Add(wx.StaticText(parent, label="Name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.username_ctrl = wx.TextCtrl(parent)
        grid.Add(self.username_ctrl, 1, wx.EXPAND)

        # Onion Address
        grid.Add(wx.StaticText(parent, label="Onion Address:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.onion_ctrl = wx.TextCtrl(parent)
        grid.Add(self.onion_ctrl, 1, wx.EXPAND)

        # Public Key
        grid.Add(wx.StaticText(parent, label="Public Key:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.pubkey_ctrl = wx.TextCtrl(parent, style=wx.TE_MULTILINE)
        grid.Add(self.pubkey_ctrl, 1, wx.EXPAND)

        grid.AddGrowableCol(1, 1)  # Make the text fields expand horizontally
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)

        return sizer

    def get_user_data(self):
        """Get the updated user data"""
        return {
            'username': self.username_ctrl.GetValue(),
            'onion_address': self.onion_ctrl.GetValue(),
            'public_key': self.pubkey_ctrl.GetValue()
        }

    def on_save(self, event):
        """Handles the Save button click"""
        self.db.add_new_contact(self.get_user_data().get("username"), self.get_user_data().get("onion_address"),
                                self.get_user_data().get("public_key"))
        self.user_data.update(self.get_user_data())
        wx.MessageBox("Contact saved successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        """Handles the Cancel button click"""
        self.EndModal(wx.ID_CANCEL)