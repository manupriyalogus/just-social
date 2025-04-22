import wx
import os
import sys
import logging
from gui.main_window import MainWindow
from gui.login_dialog import LoginDialog
from utils.config import Config
from utils.database import Database
from utils.websocket_client import WebSocketClient
from utils.logger import Logger
from utils.theme_manager import ThemeManager
from utils.notification_handler import NotificationHandler
from utils.file_handler import FileHandler


class JustSocial(wx.App):
    def InitLogging(self):
        """Initialize logging before anything else"""
        try:
            self.logger = Logger().get_logger()
            return True
        except Exception as e:
            print(f"Failed to initialize logger: {e}")
            return False

    def OnInit(self):
        """Initialize the application"""
        # Initialize logging first
        if not self.InitLogging():
            wx.MessageBox("Failed to initialize logging system.",
                          "Error", wx.OK | wx.ICON_ERROR)
            return False

        self.logger.info("Starting WhatsApp Clone application")

        try:
            # Initialize core components
            self.config = Config()
            self.db = Database()
            self.theme_manager = ThemeManager(self.config)
            self.notification_handler = NotificationHandler(self.config)
            self.file_handler = FileHandler(self.config)
            self.websocket = None

            # Set application name and vendor
            self.SetAppName("WhatsApp Clone")
            self.SetVendorName("Your Company Name")

            # Initialize the database
            self.logger.info("Initializing database")
            self.db.initialize()

            # Check for single instance
            if not self.ensure_single_instance():
                return False

            # Show login dialog first
            self.logger.info("Showing login dialog")
            login_result = self.show_login_dialog()

            if login_result:
                # Initialize main window
                self.logger.info("Initializing main window")
                self.init_main_window()
                return True
            else:
                self.logger.info("Login cancelled")
                return False

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error during application initialization: {e}")
            wx.MessageBox(f"Error starting application: {str(e)}",
                          "Error", wx.OK | wx.ICON_ERROR)
            return False

    def ensure_single_instance(self):
        """Ensure only one instance of the application is running"""
        self.instance_checker = wx.SingleInstanceChecker("JustSocial-" + wx.GetUserId())

        if self.instance_checker.IsAnotherRunning():
            wx.MessageBox("Another instance of WhatsApp Clone is already running.",
                          "Already Running",
                          wx.OK | wx.ICON_INFORMATION)
            return False

        return True

    def show_login_dialog(self):
        """Show login dialog and handle authentication"""
        login_dialog = LoginDialog(None)
        result = login_dialog.ShowModal()

        if result == wx.ID_OK:
            credentials = login_dialog.get_credentials()
            login_dialog.Destroy()

            # Initialize Tor messenger with user credentials
            try:
                self.logger.info("Initializing Tor messenger")
                from utils.tor_messenger import TorMessenger
                self.messenger = TorMessenger(
                    credentials['user_id'],
                    message_callback=self.on_message_received
                )
                return True
            except Exception as e:
                self.logger.error(f"Tor messenger initialization failed: {e}")
                wx.MessageBox(
                    "Failed to initialize Tor messenger. Please ensure Tor is running.",
                    "Connection Error",
                    wx.OK | wx.ICON_ERROR
                )
                return False
        else:
            login_dialog.Destroy()
            return False

    def on_message_received(self, message_data):
        """Handle received messages"""
        print("msg receiveddddd..........")
        print(message_data)
        try:
            # Update UI with new message
            self.frame.handle_new_message(message_data)
        except Exception as e:
            self.logger.error(f"Error handling received message: {e}")

    def init_main_window(self):
        """Initialize and show the main application window"""
        try:
            self.frame = MainWindow(
                parent=None,
                config=self.config,
                db=self.db,
                messenger=self.messenger,
                theme_manager=self.theme_manager,
                notification_handler=self.notification_handler,
                file_handler=self.file_handler
            )

            # Apply theme
            if self.theme_manager:
                self.theme_manager.apply_theme_to_window(self.frame)

            # Show the window
            self.frame.Show()

            # Set as top window
            self.SetTopWindow(self.frame)

            # Handle command line arguments if any
            self.handle_command_line()

        except Exception as e:
            self.logger.error(f"Error initializing main window: {e}")
            raise

    def handle_command_line(self):
        """Handle any command line arguments"""
        if len(sys.argv) > 1:
            # Handle arguments like opening specific chats
            chat_id = sys.argv[1]
            wx.CallAfter(self.frame.open_chat, chat_id)

    def OnExit(self):
        """Clean up resources when the application exits"""
        try:
            if hasattr(self, 'logger'):
                self.logger.info("Application shutting down")

            # Close websocket connection
            if hasattr(self, 'websocket') and self.websocket:
                self.websocket.close()

            # Save any pending configurations
            if hasattr(self, 'config'):
                self.config.save_config()

            # Clean up temporary files
            if hasattr(self, 'file_handler'):
                self.file_handler.cleanup_temp_files()

            return super().OnExit()

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error during shutdown: {e}")
            return False

    def Restart(self):
        """Restart the application"""
        if hasattr(self, 'logger'):
            self.logger.info("Restarting application")

        # Get current executable path
        executable = sys.executable
        args = sys.argv[:]

        # Add restart flag to prevent infinite restart loop
        args.insert(0, sys.executable)
        if '--restarted' not in args:
            args.append('--restarted')

        # Close current instance
        if hasattr(self, 'frame'):
            self.frame.Close()

        # Start new instance
        os.execv(executable, args)


def main():
    # Set up basic logging configuration
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        # Create and start the application
        app = JustSocial()
        app.MainLoop()
        return 0
    except Exception as e:
        logging.error(f"Unhandled exception in main loop: {e}")
        # Show error dialog if possible
        try:
            wx.MessageBox(f"An unexpected error occurred: {str(e)}",
                          "Error",
                          wx.OK | wx.ICON_ERROR)
        except:
            print(f"Fatal error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())