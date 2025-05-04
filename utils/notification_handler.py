import wx
import platform
import os

class NotificationHandler:
    def __init__(self, config):
        self.config = config
        self.os_type = platform.system()
        self.notifications_enabled = self.config.get('notifications.enabled', True)
        self.sound_enabled = self.config.get('notifications.sound', True)
        self.preview_enabled = self.config.get('notifications.preview', True)
        
    def show_notification(self, title, message, icon_path=None):
        """Show a system notification"""
        if not self.notifications_enabled:
            return
            
        # Truncate preview if disabled
        if not self.preview_enabled:
            message = "New message received"
            
        try:
            if self.os_type == 'Windows':
                self._show_windows_notification(title, message, icon_path)
            elif self.os_type == 'Darwin':  # macOS
                self._show_macos_notification(title, message)
            else:  # Linux
                self._show_linux_notification(title, message, icon_path)
                
            if self.sound_enabled:
                self._play_notification_sound()
                
        except Exception as e:
            print(f"Error showing notification: {e}")
            
    def _show_windows_notification(self, title, message, icon_path):
        """Show notification on Windows"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                icon_path=icon_path,
                duration=5,
                threaded=True
            )
        except ImportError:
            # Fallback to wx.NotificationMessage
            self._show_wx_notification(title, message)
            
    def _show_macos_notification(self, title, message):
        """Show notification on macOS"""
        try:
            os.system(f"""
                osascript -e 'display notification "{message}" with title "{title}"'
            """)
        except:
            # Fallback to wx.NotificationMessage
            self._show_wx_notification(title, message)
            
    def _show_linux_notification(self, title, message, icon_path):
        """Show notification on Linux"""
        try:
            import notify2
            notify2.init("WhatsApp Clone")
            notification = notify2.Notification(
                title,
                message,
                icon_path
            )
            notification.show()
        except ImportError:
            # Fallback to wx.NotificationMessage
            self._show_wx_notification(title, message)
            
    def _show_wx_notification(self, title, message):
        """Show notification using wxPython"""
        notification = wx.NotificationMessage(title, message)
        notification.Show(timeout=5)  # Show for 5 seconds
            
    def _play_notification_sound(self):
        """Play notification sound"""
        if not self.sound_enabled:
            return
            
        try:
            if self.os_type == 'Windows':
                import winsound
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            elif self.os_type == 'Darwin':
                os.system("afplay /System/Library/Sounds/Ping.aiff")
            else:
                os.system("paplay /usr/share/sounds/freedesktop/stereo/message.oga")
        except Exception as e:
            print(f"Error playing notification sound: {e}")
            
    def update_settings(self, settings):
        """Update notification settings"""
        self.notifications_enabled = settings.get('enabled', self.notifications_enabled)
        self.sound_enabled = settings.get('sound', self.sound_enabled)
        self.preview_enabled = settings.get('preview', self.preview_enabled)
        
        # Save to config
        self.config.set('notifications.enabled', self.notifications_enabled)
        self.config.set('notifications.sound', self.sound_enabled)
        self.config.set('notifications.preview', self.preview_enabled)