import json
import os
import shutil

import appdirs
import wx
import wx.adv


class ProfileDialog(wx.Dialog):
    def __init__(self, parent, user_data, messenger, keys_file):
        super().__init__(parent, title="Profile", size=(500, 600))
        self.userid_ctrl = None
        self.pubkey_ctrl = None
        self.onion_ctrl = None
        self.username_ctrl = None
        self.profile_image = None
        self.user_data = user_data
        self.messenger = messenger
        self.keys_file = keys_file
        self.init_ui()
        self.Center()
        self.app_name = "JustSocial"
        self.data_dir = appdirs.user_data_dir(self.app_name)

    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Profile Picture Section
        main_sizer.Add(self.create_profile_section(panel), 0, wx.EXPAND | wx.ALL, 10)

        # Separator
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)

        # Connection Info Section
        main_sizer.Add(self.create_connection_section(panel), 0, wx.EXPAND | wx.ALL, 10)

        # Security Section
        main_sizer.Add(self.create_security_section(panel), 0, wx.EXPAND | wx.ALL, 10)

        # Bottom Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(panel, wx.ID_OK, "Save")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        button_sizer.Add(save_btn, 0, wx.ALL, 5)
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(main_sizer)

    def create_profile_section(self, parent):
        box = wx.StaticBox(parent, label="Profile")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Profile picture panel
        pic_panel = wx.Panel(parent)
        pic_sizer = wx.BoxSizer(wx.VERTICAL)

        # Profile picture
        with open(self.keys_file, 'r') as f:
            data = json.load(f)
        if 'profile_picture' in data:
            profile_image = wx.Image(data['profile_picture'], wx.BITMAP_TYPE_ANY).Scale(120, 120).ConvertToBitmap()
        else:
            profile_image = self.create_default_avatar(120)

        self.profile_image = wx.StaticBitmap(
            pic_panel,
            # bitmap=self.create_default_avatar(120),
            bitmap=profile_image,
            size=(120, 120)

        )

        # Change picture button
        change_pic_btn = wx.Button(pic_panel, label="Change Picture")
        change_pic_btn.Bind(wx.EVT_BUTTON, self.on_change_picture)

        pic_sizer.Add(self.profile_image, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        pic_sizer.Add(change_pic_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        pic_panel.SetSizer(pic_sizer)

        # User info
        info_grid = wx.FlexGridSizer(2, 2, 10, 10)

        # Username
        info_grid.Add(wx.StaticText(parent, label="Username:"))
        self.username_ctrl = wx.TextCtrl(parent)
        if 'username' in self.user_data:
            self.username_ctrl.SetValue(self.user_data['username'])
        info_grid.Add(self.username_ctrl, 1, wx.EXPAND)

        # Status
        info_grid.Add(wx.StaticText(parent, label="Status:"))
        self.status_ctrl = wx.TextCtrl(parent)
        if 'status' in self.user_data:
            self.status_ctrl.SetValue(self.user_data['status'])
        info_grid.Add(self.status_ctrl, 1, wx.EXPAND)

        info_grid.AddGrowableCol(1, 1)

        # Add all to main sizer
        sizer.Add(pic_panel, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(info_grid, 0, wx.EXPAND | wx.ALL, 10)

        return sizer

    def create_connection_section(self, parent):
        box = wx.StaticBox(parent, label="Connection Information")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Get connection info
        connection_info = self.messenger.get_connection_info()

        # Grid for connection info
        grid = wx.FlexGridSizer(3, 3, 10, 10)

        # Onion Address
        grid.Add(wx.StaticText(parent, label="Onion Address:"))
        self.onion_ctrl = wx.TextCtrl(
            parent,
            value=connection_info['onion_address'],
            style=wx.TE_READONLY
        )
        grid.Add(self.onion_ctrl, 1, wx.EXPAND)
        copy_onion_btn = wx.Button(parent, label="Copy", size=(60, -1))
        copy_onion_btn.Bind(
            wx.EVT_BUTTON,
            lambda evt: self.copy_to_clipboard(self.onion_ctrl.GetValue())
        )
        grid.Add(copy_onion_btn)

        # Public Key
        grid.Add(wx.StaticText(parent, label="Public Key:"))
        self.pubkey_ctrl = wx.TextCtrl(
            parent,
            value=connection_info['public_key'],
            style=wx.TE_READONLY
        )
        grid.Add(self.pubkey_ctrl, 1, wx.EXPAND)
        copy_key_btn = wx.Button(parent, label="Copy", size=(60, -1))
        copy_key_btn.Bind(
            wx.EVT_BUTTON,
            lambda evt: self.copy_to_clipboard(self.pubkey_ctrl.GetValue())
        )
        grid.Add(copy_key_btn)

        # User ID
        grid.Add(wx.StaticText(parent, label="User ID:"))
        self.userid_ctrl = wx.TextCtrl(
            parent,
            value=connection_info['user_id'],
            style=wx.TE_READONLY
        )
        grid.Add(self.userid_ctrl, 1, wx.EXPAND)
        copy_id_btn = wx.Button(parent, label="Copy", size=(60, -1))
        copy_id_btn.Bind(
            wx.EVT_BUTTON,
            lambda evt: self.copy_to_clipboard(self.userid_ctrl.GetValue())
        )
        grid.Add(copy_id_btn)

        grid.AddGrowableCol(1, 1)

        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)

        # Add note
        note = wx.StaticText(
            parent,
            label="Share this information securely with your contacts to receive messages."
        )
        note.SetForegroundColour(wx.Colour(128, 128, 128))
        sizer.Add(note, 0, wx.ALL, 10)

        return sizer

    def create_security_section(self, parent):
        box = wx.StaticBox(parent, label="Security")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Connection status
        status_text = wx.StaticText(parent, label="Tor Status: Connected")
        status_text.SetForegroundColour(wx.Colour(0, 128, 0))  # Green
        sizer.Add(status_text, 0, wx.ALL, 5)

        # Encryption info
        encryption_text = wx.StaticText(
            parent,
            label="End-to-end encryption enabled using NaCl"
        )
        sizer.Add(encryption_text, 0, wx.ALL, 5)

        return sizer

    def create_default_avatar(self, size):
        """Create a default avatar bitmap"""
        bitmap = wx.Bitmap(size, size)
        dc = wx.MemoryDC(bitmap)

        # Draw circle background
        dc.SetBackground(wx.Brush(wx.Colour(200, 200, 200)))
        dc.Clear()

        # Draw circle
        dc.SetBrush(wx.Brush(wx.Colour(150, 150, 150)))
        dc.SetPen(wx.Pen(wx.Colour(150, 150, 150)))
        dc.DrawCircle(size // 2, size // 2, size // 2)

        return bitmap

    def on_change_picture(self, event):
        """Handle profile picture change"""
        with wx.FileDialog(
                self,
                "Choose a profile picture",
                wildcard="Image files (*.jpg;*.jpeg;*.png)|*.jpg;*.jpeg;*.png",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:

            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            path = dialog.GetPath()
            try:
                image = wx.Image(path)
                # Scale image to fit
                image = self.scale_image(image, 120)
                # Make circular
                # image = self.make_circular_image(image)
                self.profile_image.SetBitmap(wx.Bitmap(image))

                dest_dir = f"{self.data_dir}/media/images/profile"
                os.makedirs(dest_dir, exist_ok=True)
                copied_path = shutil.copy(path, dest_dir)

                with open(self.keys_file, 'r') as f:
                    data = json.load(f)
                data['profile_picture'] = copied_path

                with open(self.keys_file, 'w') as f:
                    json.dump(data, f, indent=4)


            except Exception as e:
                wx.MessageBox(
                    f"Error loading image: {str(e)}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )

    def scale_image(self, image, size):
        """Scale image to specified size maintaining aspect ratio"""
        w = image.GetWidth()
        h = image.GetHeight()
        if w > h:
            new_w = size
            new_h = int(h * size / w)
        else:
            new_h = size
            new_w = int(w * size / h)
        return image.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)

    def make_circular_image(self, image):
        """Make the image circular with alpha channel"""
        size = min(image.GetWidth(), image.GetHeight())
        output = wx.Bitmap(size, size)

        dc = wx.MemoryDC(output)
        dc.SetBackground(wx.Brush("white", wx.TRANSPARENT))
        dc.Clear()

        gc = wx.GraphicsContext.Create(dc)
        if gc:
            path = gc.CreatePath()
            path.AddCircle(size / 2, size / 2, size / 2)
            gc.SetClipPath(path)
            gc.DrawBitmap(wx.Bitmap(image), 0, 0, size, size)

        dc.SelectObject(wx.NullBitmap)
        return output.ConvertToImage()

    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox(
                "Copied to clipboard!",
                "Success",
                wx.OK | wx.ICON_INFORMATION
            )

    def get_user_data(self):
        """Get the updated user data"""
        self.user_data.update({
            'username': self.username_ctrl.GetValue(),
            'status': self.status_ctrl.GetValue()
        })
        return self.user_data
