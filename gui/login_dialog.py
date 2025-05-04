import wx
import wx.adv
import json
import os
from utils.encryption import MessageEncryption


class LoginDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Login to Just Social",
                         size=(400, 450),
                         style=wx.DEFAULT_DIALOG_STYLE)

        self.credentials = {}
        self.encryption = MessageEncryption()
        self.init_ui()
        self.load_saved_credentials()
        self.Center()

    def init_ui(self):
        # Main panel
        panel = wx.Panel(self)

        # Main vertical box sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Logo/Banner
        logo_panel = self.create_logo_panel(panel)
        main_sizer.Add(logo_panel, 0, wx.EXPAND | wx.ALL, 10)

        # Add a line separator
        line = wx.StaticLine(panel)
        main_sizer.Add(line, 0, wx.EXPAND | wx.ALL, 5)

        # Create login form
        form_panel = self.create_form_panel(panel)
        main_sizer.Add(form_panel, 1, wx.EXPAND | wx.ALL, 10)

        # Add buttons
        button_panel = self.create_button_panel(panel)
        main_sizer.Add(button_panel, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)

    def create_logo_panel(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # App title
        title = wx.StaticText(panel, label="Just Social")
        title_font = title.GetFont()
        title_font.SetPointSize(20)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)

        # Subtitle
        subtitle = wx.StaticText(panel,
                                 label="Sign in to start messaging")
        subtitle_font = subtitle.GetFont()
        subtitle_font.SetPointSize(10)
        subtitle.SetFont(subtitle_font)
        subtitle.SetForegroundColour(wx.Colour(128, 128, 128))

        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(subtitle, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def create_form_panel(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Username field
        username_label = wx.StaticText(panel, label="Username or Email:")
        self.username_ctrl = wx.TextCtrl(panel, size=(250, -1))

        # Password field
        # password_label = wx.StaticText(panel, label="Password:")
        # self.password_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD,
        #                                  size=(250, -1))
        #
        # # Remember me checkbox
        # self.remember_cb = wx.CheckBox(panel, label="Remember me")

        # Add fields to sizer with some spacing
        sizer.AddSpacer(10)
        sizer.Add(username_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(self.username_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        sizer.AddSpacer(10)
        self.password_ctrl =''
        self.remember_cb = True
        # sizer.Add(password_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        # sizer.Add(self.password_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        # sizer.AddSpacer(10)
        #
        # sizer.Add(self.remember_cb, 0, wx.ALL, 10)

        panel.SetSizer(sizer)
        return panel

    def create_button_panel(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create buttons
        login_button = wx.Button(panel, wx.ID_OK, "Login")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        # Add buttons to sizer
        sizer.Add(login_button, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(cancel_button, 1, wx.EXPAND | wx.ALL, 5)

        # Bind events
        login_button.Bind(wx.EVT_BUTTON, self.on_login)

        panel.SetSizer(sizer)
        return panel

    def on_login(self, event):
        """Handle login button click"""
        username = self.username_ctrl.GetValue().strip()
        # password = self.password_ctrl.GetValue().strip()
        if not username:
            wx.MessageBox("Please enter both username and password",
                          "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        # Store credentials
        self.credentials = {
            'user_id': username,
       #     'password': password,  # In real app, this should be hashed
            'password': "",  # In real app, this should be hashed
        #    'remember': self.remember_cb.GetValue()
            'remember': True

        }

        # Save credentials if remember me is checked
        # if self.remember_cb.GetValue():
        #     self.save_credentials()

        event.Skip()

    def load_saved_credentials(self):
        """Load saved credentials if they exist"""
        try:
            app = wx.GetApp()
            if hasattr(app, 'config'):
                creds_file = os.path.join(app.config.config_dir, "credentials.enc")
                if os.path.exists(creds_file):
                    # Read the file content
                    with open(creds_file, 'rb') as f:
                        encrypted_data = f.read()

                    # Only try to decrypt if we have data
                    if encrypted_data:
                        decrypted_data = self.encryption.decrypt_message(encrypted_data)
                        if decrypted_data:
                            saved_creds = json.loads(decrypted_data)
                            self.username_ctrl.SetValue(saved_creds.get('user_id', ''))
                            self.password_ctrl.SetValue(saved_creds.get('password', ''))
                            self.remember_cb.SetValue(True)

        except Exception as e:
            # Just log the error, don't show to user
            print(f"Note: No saved credentials found: {e}")

    def save_credentials(self):
        """Save credentials securely"""
        try:
            app = wx.GetApp()
            if hasattr(app, 'config'):
                # Ensure the config directory exists
                os.makedirs(app.config.config_dir, exist_ok=True)

                creds_file = os.path.join(app.config.config_dir, "credentials.enc")

                # Encrypt and save credentials
                encrypted_data = self.encryption.encrypt_message(
                    json.dumps(self.credentials)
                )

                with open(creds_file, 'wb') as f:
                    f.write(encrypted_data)

        except Exception as e:
            print(f"Error saving credentials: {e}")
            # Don't show error to user, just log it

    def get_credentials(self):
        """Get the entered credentials"""
        return self.credentials