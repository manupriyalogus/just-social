import shutil

import wx
import os
import wx.adv


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, config):
        super().__init__(parent, title="Settings", size=(500, 400))
        self.config = config
        self.init_ui()

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create notebook for different settings categories
        notebook = wx.Notebook(panel)

        # Add settings pages
        general_page = GeneralSettingsPage(notebook, self.config)
        notifications_page = NotificationSettingsPage(notebook, self.config)
        privacy_page = PrivacySettingsPage(notebook, self.config)
        storage_page = StorageSettingsPage(notebook, self.config)

        notebook.AddPage(general_page, "General")
        notebook.AddPage(notifications_page, "Notifications")
        notebook.AddPage(privacy_page, "Privacy")
        notebook.AddPage(storage_page, "Storage")

        vbox.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)

        # Add buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "OK")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        apply_button = wx.Button(panel, wx.ID_APPLY, "Apply")

        btn_sizer.Add(ok_button, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_button, 0, wx.ALL, 5)
        btn_sizer.Add(apply_button, 0, wx.ALL, 5)

        vbox.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        # Bind events
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        apply_button.Bind(wx.EVT_BUTTON, self.on_apply)

        panel.SetSizer(vbox)
        self.Center()

    def on_ok(self, event):
        self.apply_settings()
        event.Skip()

    def on_apply(self, event):
        self.apply_settings()

    def apply_settings(self):
        """Apply settings from all pages"""
        for page in self.GetChildren()[0].GetChildren()[0].GetChildren():
            if hasattr(page, 'apply_settings'):
                page.apply_settings()


class GeneralSettingsPage(wx.Panel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Theme settings
        theme_box = wx.StaticBox(self, label="Theme")
        theme_sizer = wx.StaticBoxSizer(theme_box, wx.VERTICAL)

        self.dark_mode = wx.CheckBox(self, label="Dark mode")
        self.dark_mode.SetValue(self.config.get('theme') == 'dark')
        theme_sizer.Add(self.dark_mode, 0, wx.ALL, 5)

        # Language settings
        lang_box = wx.StaticBox(self, label="Language")
        lang_sizer = wx.StaticBoxSizer(lang_box, wx.VERTICAL)

        languages = ['English', 'Spanish', 'French', 'German', 'Italian']
        self.language = wx.Choice(self, choices=languages)
        current_lang = self.config.get('language', 'English')
        self.language.SetSelection(languages.index(current_lang))
        lang_sizer.Add(self.language, 0, wx.ALL | wx.EXPAND, 5)

        # Startup settings
        startup_box = wx.StaticBox(self, label="Startup")
        startup_sizer = wx.StaticBoxSizer(startup_box, wx.VERTICAL)

        self.start_minimized = wx.CheckBox(self, label="Start minimized")
        self.start_with_system = wx.CheckBox(self, label="Start with system")

        self.start_minimized.SetValue(self.config.get('start_minimized', False))
        self.start_with_system.SetValue(self.config.get('start_with_system', False))

        startup_sizer.Add(self.start_minimized, 0, wx.ALL, 5)
        startup_sizer.Add(self.start_with_system, 0, wx.ALL, 5)

        # Add all sections to main sizer
        vbox.Add(theme_sizer, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(startup_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(vbox)

    def apply_settings(self):
        self.config.set('theme', 'dark' if self.dark_mode.GetValue() else 'light')
        self.config.set('language', self.language.GetString(self.language.GetSelection()))
        self.config.set('start_minimized', self.start_minimized.GetValue())
        self.config.set('start_with_system', self.start_with_system.GetValue())

        # Apply theme immediately if changed
        if self.dark_mode.GetValue() != (self.config.get('theme') == 'dark'):
            wx.GetApp().GetTopWindow().apply_theme()


class NotificationSettingsPage(wx.Panel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Notification settings
        notif_box = wx.StaticBox(self, label="Notifications")
        notif_sizer = wx.StaticBoxSizer(notif_box, wx.VERTICAL)

        self.enable_notifications = wx.CheckBox(self, label="Enable notifications")
        self.show_preview = wx.CheckBox(self, label="Show message preview")
        self.play_sound = wx.CheckBox(self, label="Play notification sound")

        self.enable_notifications.SetValue(self.config.get('notifications.enabled', True))
        self.show_preview.SetValue(self.config.get('notifications.preview', True))
        self.play_sound.SetValue(self.config.get('notifications.sound', True))

        notif_sizer.Add(self.enable_notifications, 0, wx.ALL, 5)
        notif_sizer.Add(self.show_preview, 0, wx.ALL, 5)
        notif_sizer.Add(self.play_sound, 0, wx.ALL, 5)

        # Do Not Disturb settings
        dnd_box = wx.StaticBox(self, label="Do Not Disturb")
        dnd_sizer = wx.StaticBoxSizer(dnd_box, wx.VERTICAL)

        self.enable_dnd = wx.CheckBox(self, label="Enable Do Not Disturb")

        time_panel = wx.Panel(self)
        time_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.dnd_start = wx.adv.TimePickerCtrl(time_panel)
        self.dnd_end = wx.adv.TimePickerCtrl(time_panel)

        time_sizer.Add(wx.StaticText(time_panel, label="From:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        time_sizer.Add(self.dnd_start, 0, wx.ALL, 5)
        time_sizer.Add(wx.StaticText(time_panel, label="To:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        time_sizer.Add(self.dnd_end, 0, wx.ALL, 5)

        time_panel.SetSizer(time_sizer)

        dnd_sizer.Add(self.enable_dnd, 0, wx.ALL, 5)
        dnd_sizer.Add(time_panel, 0, wx.ALL, 5)

        # Add all sections to main sizer
        vbox.Add(notif_sizer, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(dnd_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(vbox)

    def apply_settings(self):
        self.config.set('notifications.enabled', self.enable_notifications.GetValue())
        self.config.set('notifications.preview', self.show_preview.GetValue())
        self.config.set('notifications.sound', self.play_sound.GetValue())
        self.config.set('notifications.dnd.enabled', self.enable_dnd.GetValue())
        self.config.set('notifications.dnd.start', self.dnd_start.GetValue().Format("%H:%M"))
        self.config.set('notifications.dnd.end', self.dnd_end.GetValue().Format("%H:%M"))


class PrivacySettingsPage(wx.Panel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Privacy settings
        privacy_box = wx.StaticBox(self, label="Privacy")
        privacy_sizer = wx.StaticBoxSizer(privacy_box, wx.VERTICAL)

        self.read_receipts = wx.CheckBox(self, label="Send read receipts")
        self.last_seen = wx.CheckBox(self, label="Show last seen")
        self.typing_indicator = wx.CheckBox(self, label="Show typing indicator")

        self.read_receipts.SetValue(self.config.get('privacy.read_receipts', True))
        self.last_seen.SetValue(self.config.get('privacy.last_seen', True))
        self.typing_indicator.SetValue(self.config.get('privacy.typing_indicator', True))

        privacy_sizer.Add(self.read_receipts, 0, wx.ALL, 5)
        privacy_sizer.Add(self.last_seen, 0, wx.ALL, 5)
        privacy_sizer.Add(self.typing_indicator, 0, wx.ALL, 5)

        # Security settings
        security_box = wx.StaticBox(self, label="Security")
        security_sizer = wx.StaticBoxSizer(security_box, wx.VERTICAL)

        self.enable_encryption = wx.CheckBox(self, label="Enable end-to-end encryption")
        self.screen_lock = wx.CheckBox(self, label="Enable screen lock")

        security_sizer.Add(self.enable_encryption, 0, wx.ALL, 5)
        security_sizer.Add(self.screen_lock, 0, wx.ALL, 5)

        # Add all sections to main sizer
        vbox.Add(privacy_sizer, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(security_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(vbox)

    def apply_settings(self):
        self.config.set('privacy.read_receipts', self.read_receipts.GetValue())
        self.config.set('privacy.last_seen', self.last_seen.GetValue())
        self.config.set('privacy.typing_indicator', self.typing_indicator.GetValue())
        self.config.set('security.encryption', self.enable_encryption.GetValue())
        self.config.set('security.screen_lock', self.screen_lock.GetValue())


class StorageSettingsPage(wx.Panel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Storage location settings
        location_box = wx.StaticBox(self, label="Storage Location")
        location_sizer = wx.StaticBoxSizer(location_box, wx.VERTICAL)

        location_panel = wx.Panel(self)
        location_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.storage_path = wx.TextCtrl(location_panel)
        browse_button = wx.Button(location_panel, label="Browse")

        current_path = self.config.get('storage.download_location',
                                       os.path.expanduser("~/Downloads"))
        self.storage_path.SetValue(current_path)

        location_panel_sizer.Add(self.storage_path, 1, wx.EXPAND | wx.RIGHT, 5)
        location_panel_sizer.Add(browse_button, 0)

        location_panel.SetSizer(location_panel_sizer)
        location_sizer.Add(location_panel, 0, wx.EXPAND | wx.ALL, 5)

        # Auto-download settings
        download_box = wx.StaticBox(self, label="Auto-download")
        download_sizer = wx.StaticBoxSizer(download_box, wx.VERTICAL)

        self.auto_images = wx.CheckBox(self, label="Images")
        self.auto_videos = wx.CheckBox(self, label="Videos")
        self.auto_documents = wx.CheckBox(self, label="Documents")

        # Set current values
        self.auto_images.SetValue(self.config.get('storage.auto_download.images', True))
        self.auto_videos.SetValue(self.config.get('storage.auto_download.videos', False))
        self.auto_documents.SetValue(self.config.get('storage.auto_download.documents', False))

        download_sizer.Add(self.auto_images, 0, wx.ALL, 5)
        download_sizer.Add(self.auto_videos, 0, wx.ALL, 5)
        download_sizer.Add(self.auto_documents, 0, wx.ALL, 5)

        # Network settings for downloads
        network_box = wx.StaticBox(self, label="Network Settings")
        network_sizer = wx.StaticBoxSizer(network_box, wx.VERTICAL)

        self.download_wifi = wx.CheckBox(self, label="Download media only on Wi-Fi")
        self.download_wifi.SetValue(self.config.get('storage.wifi_only', True))

        network_sizer.Add(self.download_wifi, 0, wx.ALL, 5)

        # Storage management
        management_box = wx.StaticBox(self, label="Storage Management")
        management_sizer = wx.StaticBoxSizer(management_box, wx.VERTICAL)

        # Storage info
        info_panel = wx.Panel(self)
        info_sizer = wx.GridBagSizer(5, 5)

        # Add storage usage information
        storage_info = self.get_storage_info()
        row = 0
        for label, value in storage_info.items():
            info_sizer.Add(wx.StaticText(info_panel, label=label),
                           pos=(row, 0), flag=wx.ALL, border=2)
            info_sizer.Add(wx.StaticText(info_panel, label=value),
                           pos=(row, 1), flag=wx.ALL | wx.ALIGN_RIGHT, border=2)
            row += 1

        info_panel.SetSizer(info_sizer)
        management_sizer.Add(info_panel, 0, wx.EXPAND | wx.ALL, 5)

        # Add buttons for management actions
        button_panel = wx.Panel(self)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        clear_cache_button = wx.Button(button_panel, label="Clear Cache")
        clear_data_button = wx.Button(button_panel, label="Clear All Data")

        button_sizer.Add(clear_cache_button, 0, wx.RIGHT, 5)
        button_sizer.Add(clear_data_button, 0)

        button_panel.SetSizer(button_sizer)
        management_sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        # Add all sections to main sizer
        vbox.Add(location_sizer, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(download_sizer, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(network_sizer, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(management_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(vbox)

        # Bind events
        browse_button.Bind(wx.EVT_BUTTON, self.on_browse)
        clear_cache_button.Bind(wx.EVT_BUTTON, self.on_clear_cache)
        clear_data_button.Bind(wx.EVT_BUTTON, self.on_clear_data)

    def on_browse(self, event):
        """Handle browse button click"""
        dlg = wx.DirDialog(self, "Choose download location:",
                           defaultPath=self.storage_path.GetValue(),
                           style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            self.storage_path.SetValue(dlg.GetPath())

        dlg.Destroy()

    def on_clear_cache(self, event):
        """Handle clear cache button click"""
        dlg = wx.MessageDialog(self,
                               "Are you sure you want to clear the cache?\n"
                               "This will free up space but may slow down the app temporarily.",
                               "Clear Cache",
                               wx.YES_NO | wx.ICON_QUESTION)

        if dlg.ShowModal() == wx.ID_YES:
            self.clear_cache()
            wx.MessageBox("Cache cleared successfully!", "Success",
                          wx.OK | wx.ICON_INFORMATION)

        dlg.Destroy()

    def on_clear_data(self, event):
        """Handle clear all data button click"""
        dlg = wx.MessageDialog(self,
                               "Are you sure you want to clear all data?\n"
                               "This will remove all messages, media files, and settings.\n"
                               "This action cannot be undone!",
                               "Clear All Data",
                               wx.YES_NO | wx.ICON_WARNING)

        if dlg.ShowModal() == wx.ID_YES:
            confirm_dlg = wx.PasswordEntryDialog(self,
                                                 "Please enter your password to confirm:",
                                                 "Confirm Clear Data")

            if confirm_dlg.ShowModal() == wx.ID_OK:
                if self.verify_password(confirm_dlg.GetValue()):
                    self.clear_all_data()
                    wx.MessageBox("All data cleared successfully!\n"
                                  "The application will now restart.",
                                  "Success", wx.OK | wx.ICON_INFORMATION)
                    wx.GetApp().Restart()
                else:
                    wx.MessageBox("Incorrect password!", "Error",
                                  wx.OK | wx.ICON_ERROR)

            confirm_dlg.Destroy()

        dlg.Destroy()

    def get_storage_info(self):
        """Get storage usage information"""
        # This is a placeholder - implement actual storage calculation
        return {
            "Total Space Used": "1.2 GB",
            "Images": "600 MB",
            "Videos": "400 MB",
            "Documents": "150 MB",
            "Cache": "50 MB"
        }

    def clear_cache(self):
        """Clear application cache"""
        cache_dir = os.path.join(self.config.get_app_data_dir(), "cache")
        if os.path.exists(cache_dir):
            try:
                for filename in os.listdir(cache_dir):
                    filepath = os.path.join(cache_dir, filename)
                    try:
                        if os.path.isfile(filepath):
                            os.unlink(filepath)
                        elif os.path.isdir(filepath):
                            shutil.rmtree(filepath)
                    except Exception as e:
                        print(f"Error deleting {filepath}: {e}")
            except Exception as e:
                print(f"Error clearing cache: {e}")

    def clear_all_data(self):
        """Clear all application data"""
        try:
            # Clear database
            self.config.reset_to_defaults()

            # Clear all data directories
            data_dir = self.config.get_app_data_dir()
            for item in ['media', 'cache', 'temp']:
                item_path = os.path.join(data_dir, item)
                if os.path.exists(item_path):
                    shutil.rmtree(item_path)

        except Exception as e:
            print(f"Error clearing all data: {e}")

    def verify_password(self, password):
        """Verify user password"""
        # Implement actual password verification
        return True  # Placeholder

    def apply_settings(self):
        """Apply storage settings"""
        self.config.set('storage.download_location', self.storage_path.GetValue())
        self.config.set('storage.auto_download.images', self.auto_images.GetValue())
        self.config.set('storage.auto_download.videos', self.auto_videos.GetValue())
        self.config.set('storage.auto_download.documents', self.auto_documents.GetValue())
        self.config.set('storage.wifi_only', self.download_wifi.GetValue())
