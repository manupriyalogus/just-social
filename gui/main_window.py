import wx
import wx.aui
import time

from .add_conatct_dialog import AddContactDialog
from .chat_panel import ChatPanel
from .contact_list import ContactList
from .settings_dialog import SettingsDialog
from .profile_dialog import ProfileDialog
from .group_message_bubble import GroupChatPanel
import os

# Define the custom event type
wxEVT_CONTACT_LIST_UPDATE = wx.NewEventType()
EVT_CONTACT_LIST_UPDATE = wx.PyEventBinder(wxEVT_CONTACT_LIST_UPDATE, 1)


class MainWindow(wx.Frame):
    def __init__(self, parent, config, db, messenger, theme_manager=None,
                 notification_handler=None, file_handler=None):
        super().__init__(parent, title="Just Social",
                         size=(1000, 700))

        self.config = config
        self.db = db
        self.messenger = messenger
        self.theme_manager = theme_manager
        self.notification_handler = notification_handler
        self.file_handler = file_handler
        self.logger = wx.GetApp().logger
        self.keys_file = f"{self.messenger.user_id}_keys.json"
        self.splitter = None
        self.contact_list = None
        self.chat_panel = None
        self.group_chat_panel = None
        self.panel = None
        self.profile_pic = None

        # Initialize user data
        self.user_data = {
            'username': self.messenger.user_id,
            'status': 'Available',
            'profile_picture': None
        }

        # Initialize UI components
        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()

        # Center the window
        self.Center()

        # Bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Bind(EVT_CONTACT_LIST_UPDATE, self.on_contact_list_update)  # Bind the event
        self.connect_panels()

    def init_ui(self):
        # Create the main panel
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create top bar
        top_bar = self.create_top_bar()
        main_sizer.Add(top_bar, 0, wx.EXPAND)

        # Add separator line
        main_sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND)

        # Create main content area
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create splitter window
        self.splitter = wx.SplitterWindow(self.panel, style=wx.SP_LIVE_UPDATE)

        # Create contact list panel
        self.contact_list = ContactList(self.splitter, self.db)

        # Create notebook for different chat types
        self.chat_notebook = wx.Notebook(self.splitter)

        # Create regular chat panel
        self.chat_panel = ChatPanel(self.chat_notebook, self.db, self.messenger, self.config)

        # Create group chat panel
        self.group_chat_panel = GroupChatPanel(self.chat_notebook, self.db, self.messenger)

        # Add panels to notebook
        self.chat_notebook.AddPage(self.chat_panel, "Chats")
        self.chat_notebook.AddPage(self.group_chat_panel, "Group Chats")

        # Hide the notebook tabs - we'll control which page is shown programmatically
        self.chat_notebook.SetPadding((0, 0))

        # Set up splitter
        self.splitter.SplitVertically(self.contact_list, self.chat_notebook, 300)
        self.splitter.SetMinimumPaneSize(200)
        self.splitter.SetSashPosition(300)

        # Add splitter to content sizer
        content_sizer.Add(self.splitter, 1, wx.EXPAND)

        # Add content sizer to main sizer
        main_sizer.Add(content_sizer, 1, wx.EXPAND)

        # Set main sizer
        self.panel.SetSizer(main_sizer)

        # Bind contact selection event
        self.contact_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_contact_selected)

    def on_contact_list_update(self, event):
        """Handle contact list update event"""
        print("Debug: MainWindow.on_contact_list_update called")
        wx.CallAfter(self.contact_list.refresh_contacts)

    def create_top_bar(self):
        panel = wx.Panel(self.panel)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Profile section (left)
        profile_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Profile picture
        self.profile_pic = self.create_profile_bitmap(32)
        profile_btn = wx.BitmapButton(panel, bitmap=self.profile_pic, size=(32, 32))
        profile_btn.Bind(wx.EVT_BUTTON, self.on_profile)

        # Username
        username = wx.StaticText(panel, label=self.user_data['username'])
        username_font = username.GetFont()
        username_font.SetWeight(wx.FONTWEIGHT_BOLD)
        username.SetFont(username_font)

        profile_sizer.Add(profile_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        profile_sizer.Add(username, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Tools section (right)
        tools_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Search
        self.search_ctrl = wx.SearchCtrl(panel, size=(200, -1))
        self.search_ctrl.ShowSearchButton(True)
        self.search_ctrl.ShowCancelButton(True)

        # Settings button
        settings_btn = wx.Button(panel, label="🔧", size=(40, -1))
        settings_btn.Bind(wx.EVT_BUTTON, self.on_settings)

        # add contact
        add_contact_btn = wx.Button(panel, label="➕", size=(40, -1))
        add_contact_btn.Bind(wx.EVT_BUTTON, self.on_add_contact)

        tools_sizer.Add(self.search_ctrl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        tools_sizer.Add(add_contact_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        tools_sizer.Add(settings_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Add to main sizer
        sizer.Add(profile_sizer, 1, wx.EXPAND)
        sizer.Add(tools_sizer, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        return panel

    def create_menu_bar(self):
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        settings_item = file_menu.Append(wx.ID_PREFERENCES, "Settings")
        file_menu.AppendSeparator()
        logout_item = file_menu.Append(wx.ID_ANY, "Logout")
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit")

        # View menu
        view_menu = wx.Menu()
        self.dark_mode_item = view_menu.AppendCheckItem(wx.ID_ANY, "Dark Mode")

        # Help menu
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "About")

        menubar.Append(file_menu, "File")
        menubar.Append(view_menu, "View")
        menubar.Append(help_menu, "Help")

        self.SetMenuBar(menubar)

        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
        self.Bind(wx.EVT_MENU, self.on_logout, logout_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_dark_mode, self.dark_mode_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def create_status_bar(self):
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetFieldsCount(2)
        self.status_bar.SetStatusWidths([-2, -1])
        self.update_status("Ready", "Online")

    def update_status(self, message, connection_status):
        self.status_bar.SetStatusText(message, 0)
        self.status_bar.SetStatusText(connection_status, 1)

    def create_profile_bitmap(self, size):
        """Create a circular profile bitmap"""
        bitmap = wx.Bitmap(size, size)
        dc = wx.MemoryDC(bitmap)

        # Draw circle background
        dc.SetBackground(wx.Brush(wx.Colour(200, 200, 200)))
        dc.Clear()

        # Draw circle
        dc.SetBrush(wx.Brush(wx.Colour(150, 150, 150)))
        dc.SetPen(wx.Pen(wx.Colour(150, 150, 150)))
        dc.DrawCircle(size // 2, size // 2, size // 2)

        dc.SelectObject(wx.NullBitmap)
        return bitmap

    def on_profile(self, event):
        """Handle profile button click"""
        dialog = ProfileDialog(self, self.user_data, self.messenger, self.keys_file)
        if dialog.ShowModal() == wx.ID_OK:
            self.user_data = dialog.get_user_data()
            # Update profile display
            if 'profile_picture' in self.user_data and self.user_data['profile_picture']:
                self.load_profile_picture()
        dialog.Destroy()

    def on_settings(self, event):
        dialog = SettingsDialog(self, self.config)
        dialog.ShowModal()
        dialog.Destroy()

    def on_add_contact(self, event):
        dialog = AddContactDialog(self, self.user_data, self.messenger, self.db)
        dialog.ShowModal()
        dialog.Destroy()
        self.on_contact_list_update(self)

    def on_logout(self, event):
        dlg = wx.MessageDialog(self,
                               "Are you sure you want to logout?",
                               "Confirm Logout",
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

        if dlg.ShowModal() == wx.ID_YES:
            self.Close()
            wx.GetApp().Restart()

        dlg.Destroy()

    def on_exit(self, event):
        self.Close()

    def on_toggle_dark_mode(self, event):
        is_dark = self.dark_mode_item.IsChecked()
        if self.theme_manager:
            self.theme_manager.set_theme('dark' if is_dark else 'light')
            self.theme_manager.apply_theme_to_window(self)

    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("WhatsApp Clone")
        info.SetVersion("1.0")
        info.SetDescription("A secure messaging application using Tor network")
        info.SetCopyright("(C) 2025")
        wx.adv.AboutBox(info)

    def on_close(self, event):
        """Handle window close event"""
        try:
            # Clean up messenger
            if hasattr(self, 'messenger') and self.messenger:
                self.messenger.close()

            # Save any pending configurations
            if hasattr(self, 'config'):
                self.config.save_config()

            # Clean up file handler
            if hasattr(self, 'file_handler'):
                self.file_handler.cleanup_temp_files()

            event.Skip()

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            event.Skip()

    def handle_new_message(self, message_data):
        """Handle incoming messages"""
        try:
            # Check if this is a group invitation
            if message_data.get('is_group_invitation'):
                self.handle_group_invitation(message_data)
                return

            # Check if this is a group message
            if message_data.get('is_group_message'):
                # Handle group messages
                group_id = message_data.get('group_id')

                # Save to database
                self.db.add_group_message(
                    group_id,
                    message_data['sender_id'],
                    message_data['message'],
                    'received',
                    None,  # No attachments for now
                    message_data.get('timestamp', time.time())
                )

                # Update UI if this is the current group chat
                if self.chat_notebook.GetSelection() == 1 and \
                        hasattr(self.group_chat_panel, 'current_group_id') and \
                        self.group_chat_panel.current_group_id == group_id:
                    self.group_chat_panel.update_messages()
                else:
                    # Show notification
                    group = self.db.get_group(group_id)
                    if self.notification_handler:
                        self.notification_handler.show_notification(
                            "New Group Message",
                            f"New message in {group['name'] if group else 'a group'}"
                        )

                # Update group list to show unread message
                self.contact_list.update_unread_count(group_id, 1, is_group=True)

                # Refresh contact/group list
                wx.CallAfter(self.contact_list.refresh_contacts)

            else:
                # Handle direct messages
                sender_id = message_data['sender_id']
                message = message_data['message']
                sender_public_key = message_data['sender_public_key']
                timestamp = message_data.get('timestamp', time.time())

                contact = self.db.get_contact(sender_id)
                if not contact:
                    # Add new contact to database
                    self.db.add_contact(sender_public_key, sender_id)  # Use sender_id as name if not available

                # Add message to database
                self.db.add_message(
                    sender_id,
                    message,
                    'received'
                )

                # Refresh contact list - try both methods for reliability
                # Method 1: Direct call with CallAfter
                wx.CallAfter(self.contact_list.refresh_contacts)

                # Method 2: Event-based approach
                event = wx.PyCommandEvent(wxEVT_CONTACT_LIST_UPDATE, self.GetId())
                wx.PostEvent(self, event)

                # Update UI if this is the current chat
                if self.chat_notebook.GetSelection() == 0 and \
                        hasattr(self.chat_panel, 'current_chat_id') and \
                        self.chat_panel.current_chat_id == sender_id:
                    self.chat_panel.update_messages()
                else:
                    # Show notification
                    contact = self.db.get_contact(sender_id)
                    if self.notification_handler:
                        self.notification_handler.show_notification(
                            "New Message",
                            f"New message from {contact['name'] if contact else sender_id}"
                        )

                # Update contact list to show unread message
                self.contact_list.update_unread_count(sender_id,
                                                      self.db.get_unread_count(sender_id))

        except Exception as e:
            self.logger.error(f"Error handling new message: {e}")
            import traceback
            traceback.print_exc()

    def handle_group_invitation(self, message_data):
        """Handle incoming group invitation"""
        try:
            group_id = message_data.get('group_id')
            group_name = message_data.get('group_name')
            description = message_data.get('group_description', '')
            created_by = message_data.get('created_by')
            members = message_data.get('members', [])
            avatar_path = message_data.get('avatar_path', '')

            # Check if group already exists
            existing_group = self.db.get_group(group_id)
            if not existing_group:
                # Create the group
                self.db.create_group(
                    group_id,
                    group_name,
                    description,
                    created_by,
                    avatar_path
                )

                # Add members
                for member_id in members:
                    # Add all members from the invitation
                    try:
                        # Check if contact exists in database
                        contact = self.db.get_contact(member_id)
                        if contact:
                            role = 'admin' if member_id == created_by else 'member'
                            self.db.add_group_member(group_id, member_id, role)
                    except Exception as e:
                        print(f"Error adding member {member_id} to group: {e}")

                # Add current user if not already in members
                if self.messenger.user_id not in members:
                    self.db.add_group_member(
                        group_id,
                        self.messenger.user_id,
                        'member'
                    )

                # Show notification
                if self.notification_handler:
                    self.notification_handler.show_notification(
                        "New Group",
                        f"You've been added to group: {group_name}"
                    )

                # Refresh contact list
                wx.CallAfter(self.contact_list.refresh_contacts)

        except Exception as e:
            self.logger.error(f"Error handling group invitation: {e}")
            import traceback
            traceback.print_exc()

    def load_profile_picture(self):
        """Load and update profile picture"""
        try:
            path = self.user_data['profile_picture']
            if os.path.exists(path):
                image = wx.Image(path)
                image = self.scale_and_crop_image(image, 32)
                self.profile_pic = wx.Bitmap(image)
                # Update button bitmap
                for child in self.GetChildren():
                    if isinstance(child, wx.BitmapButton):
                        child.SetBitmap(self.profile_pic)
                        break
        except Exception as e:
            self.logger.error(f"Error loading profile picture: {e}")

    def scale_and_crop_image(self, image, size):
        """Scale and crop image to square"""
        # Scale to correct size while maintaining aspect ratio
        w = image.GetWidth()
        h = image.GetHeight()
        if w > h:
            new_w = w * size / h
            new_h = size
        else:
            new_h = h * size / w
            new_w = size
        image = image.Scale(int(new_w), int(new_h), wx.IMAGE_QUALITY_HIGH)

        # Crop to square
        if new_w > size:
            x = (new_w - size) / 2
            image = image.GetSubImage((x, 0, size, size))
        elif new_h > size:
            y = (new_h - size) / 2
            image = image.GetSubImage((0, y, size, size))

        return image

    def on_contact_selected(self, event):
        print("Debug: MainWindow.on_contact_selected called")
        try:
            contact_id = self.contact_list.get_selected_contact_id()
            is_group = self.contact_list.is_selected_item_group()
            print(f"Debug: Selected item ID: {contact_id}, is_group: {is_group}")

            if contact_id:
                if is_group:
                    # Switch to group chat notebook page
                    self.chat_notebook.SetSelection(1)
                    print(f"Debug: Loading group chat with ID: {contact_id}")
                    self.group_chat_panel.load_group(contact_id)
                else:
                    # Switch to regular chat notebook page
                    self.chat_notebook.SetSelection(0)
                    print(f"Debug: Loading regular chat with ID: {contact_id}")
                    self.chat_panel.load_chat(contact_id)
            else:
                print("Debug: No contact ID available")
        except Exception as e:
            print(f"ERROR in on_contact_selected: {e}")
            import traceback
            traceback.print_exc()

    # Add this to MainWindow after creating contact_list and chat_panel
    def connect_panels(self):
        """Connect the contact_list and chat panels directly"""
        try:
            # Create a simple handler that only loads the chat with the selected ID
            def on_contact_selected_direct(item_data, is_group=False):
                item_id = item_data['id']
                print(f"Debug: Direct selection handler called with ID: {item_id}, is_group: {is_group}")

                if is_group:
                    # For groups, switch to group chat panel and load group
                    self.chat_notebook.SetSelection(1)
                    self.group_chat_panel.load_group(item_id)
                else:
                    # For direct chats, switch to regular chat panel and load chat
                    self.chat_notebook.SetSelection(0)
                    self.chat_panel.load_chat(item_id)

            # Add a direct selection handler to contact_list
            self.contact_list.set_direct_selection_handler(on_contact_selected_direct)
            print("Debug: Successfully connected panels directly")
        except Exception as e:
            print(f"ERROR in connect_panels: {e}")
            import traceback
            traceback.print_exc()