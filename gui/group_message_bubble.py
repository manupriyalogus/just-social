import json
import uuid

import wx
import wx.lib.scrolledpanel as scrolled
import os
import time
from datetime import datetime

from .message_input import MessageInput, EVT_MESSAGE_SEND


class GroupMessageBubble(wx.Panel):
    def __init__(self, parent, message, is_self=False):
        super().__init__(parent)
        self.message = message
        self.is_self = is_self
        self.init_ui()

    def init_ui(self):
        # Main vertical sizer
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Sender name if not self
        if not self.is_self:
            sender_name = self.message.get('sender_name', 'Unknown')
            sender_text = wx.StaticText(self, label=sender_name)
            sender_font = sender_text.GetFont()
            sender_font.SetWeight(wx.FONTWEIGHT_BOLD)
            sender_text.SetFont(sender_font)
            sender_text.SetForegroundColour(wx.Colour(50, 50, 50))
            vbox.Add(sender_text, 0, wx.BOTTOM, 2)

        # Bubble containing the message
        bubble_panel = wx.Panel(self)
        bubble_sizer = wx.BoxSizer(wx.VERTICAL)

        # Message content
        content = self.message.get('content', '')

        # Try to parse content as JSON in case it's a structured message
        try:
            content_obj = json.loads(content)
            if isinstance(content_obj, dict) and 'type' in content_obj:
                if content_obj['type'] == 'txt':
                    content = content_obj.get('content', '')
                elif content_obj['type'] == 'img':
                    # For image content, this would need special handling
                    content = "[Image]"  # Placeholder
        except:
            # If not JSON, just use the content as is
            pass

        msg_text = wx.StaticText(bubble_panel, label=content)
        msg_text.Wrap(250)  # Wrap text to fit in bubble

        # Timestamp and status
        time_text = wx.StaticText(bubble_panel, label=self.format_time())
        time_text.SetForegroundColour(wx.Colour(100, 100, 100))
        time_font = time_text.GetFont()
        time_font.SetPointSize(time_font.GetPointSize() - 1)
        time_text.SetFont(time_font)

        # Add to bubble
        bubble_sizer.Add(msg_text, 0, wx.EXPAND | wx.ALL, 5)
        bubble_sizer.Add(time_text, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 5)

        # Set bubble background and alignment
        if self.is_self:
            bubble_panel.SetBackgroundColour(wx.Colour(220, 248, 198))  # Light green for sent
            align_flag = wx.ALIGN_RIGHT
        else:
            bubble_panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # White for received
            align_flag = wx.ALIGN_LEFT

        bubble_panel.SetSizer(bubble_sizer)

        # Add bubble to the main sizer - FIX: Don't combine align_flag with wx.EXPAND
        vbox.Add(bubble_panel, 0, align_flag)  # Removed wx.EXPAND here

        # Set panel sizer
        self.SetSizer(vbox)
        vbox.Fit(self)

    def format_time(self):
        """Format timestamp for display"""
        try:
            timestamp = self.message.get('timestamp', time.time())
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%I:%M %p")
        except Exception as e:
            print(f"Error formatting time: {e}")
            return "Unknown time"


class GroupChatPanel(wx.Panel):
    def __init__(self, parent, db, messenger):
        super().__init__(parent)
        self.message_input = None
        self.messages_sizer = None
        self.messages_panel = None
        self.info_btn = None
        self.header_panel = None
        self.group_avatar = None
        self.db = db
        self.messenger = messenger
        self.current_group_id = None
        self.init_ui()

    def init_ui(self):
        # Main vertical sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Chat header with group info
        self.header_panel = wx.Panel(self)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Group avatar (placeholder for now)
        self.group_avatar = wx.StaticBitmap(
            self.header_panel,
            bitmap=self.create_placeholder_avatar(32),
            size=(32, 32)
        )

        # Group info (name and members count)
        info_sizer = wx.BoxSizer(wx.VERTICAL)
        self.group_name = wx.StaticText(self.header_panel, label="Select a Group")
        self.group_members = wx.StaticText(self.header_panel, label="")
        name_font = self.group_name.GetFont()
        name_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.group_name.SetFont(name_font)

        info_sizer.Add(self.group_name, 0, wx.EXPAND)
        info_sizer.Add(self.group_members, 0, wx.EXPAND)

        # Group info button
        self.info_btn = wx.Button(self.header_panel, label="ℹ", size=(30, -1))
        self.info_btn.Bind(wx.EVT_BUTTON, self.on_group_info)

        # Add components to header
        header_sizer.Add(self.group_avatar, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        header_sizer.Add(info_sizer, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        header_sizer.Add(self.info_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.header_panel.SetSizer(header_sizer)

        # Create scrolled panel for messages - use scrolled.ScrolledPanel instead of wx.ScrolledWindow
        self.messages_panel = scrolled.ScrolledPanel(self, style=wx.BORDER_THEME)
        self.messages_panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        self.messages_sizer = wx.BoxSizer(wx.VERTICAL)
        self.messages_panel.SetSizer(self.messages_sizer)

        # Setup scrolling properly
        self.messages_panel.SetupScrolling(scroll_x=False, scroll_y=True)

        # Message input area
        self.message_input = MessageInput(self)
        self.message_input.Bind(EVT_MESSAGE_SEND, self.on_send_message)

        # Add all components to main sizer
        main_sizer.Add(self.header_panel, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        main_sizer.Add(self.messages_panel, 1, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        main_sizer.Add(self.message_input, 0, wx.EXPAND)

        self.SetSizer(main_sizer)

        # Show placeholder
        self.show_placeholder()

    def show_placeholder(self):
        """Show placeholder when no group is selected"""
        self.messages_sizer.Clear(True)

        placeholder = wx.Panel(self.messages_panel)
        placeholder_sizer = wx.BoxSizer(wx.VERTICAL)

        message = wx.StaticText(placeholder, label="Select a group to start chatting")
        message.SetForegroundColour(wx.Colour(120, 120, 120))

        placeholder_sizer.AddStretchSpacer()
        placeholder_sizer.Add(message, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        placeholder_sizer.AddStretchSpacer()

        placeholder.SetSizer(placeholder_sizer)
        self.messages_sizer.Add(placeholder, 1, wx.EXPAND)

        self.messages_panel.Layout()
        self.Layout()

    def load_group(self, group_id):
        """Load a group chat"""
        self.current_group_id = group_id

        # Get group info
        group = self.db.get_group(group_id)
        if not group:
            print(f"Error: Group {group_id} not found")
            return

        # Get group members
        members = self.db.get_group_members(group_id)

        # Update header
        self.group_name.SetLabel(group.get('name', 'Unknown Group'))
        self.group_members.SetLabel(f"{len(members)} members")

        # Update avatar if available
        avatar_path = group.get('avatar_path', '')
        if avatar_path and os.path.exists(avatar_path):
            img = wx.Image(avatar_path, wx.BITMAP_TYPE_ANY)
            img = self.scale_and_crop_image(img, 32)
            self.group_avatar.SetBitmap(wx.Bitmap(img))
        else:
            self.group_avatar.SetBitmap(self.create_placeholder_avatar(32))

        # Load messages
        self.update_messages()

        # Enable group info button
        self.info_btn.Enable()

    def update_messages(self):
        """Update the messages display"""
        if not self.current_group_id:
            return

        print(f"DEBUG: Updating messages for group ID: {self.current_group_id}")

        # Get messages
        messages = self.db.get_group_messages(self.current_group_id)
        print(f"DEBUG: Retrieved {len(messages)} group messages for group ID: {self.current_group_id}")

        # Debug: print message details
        for msg in messages:
            print(
                f"DEBUG: Group message - ID: {msg.get('id')}, message_id: {msg.get('message_id')}, status: {msg.get('status')}")

        # Clear current messages
        self.messages_sizer.Clear(True)

        # Add each message as a bubble
        for message in messages:
            is_self = message.get('chat_id') == self.messenger.user_id
            bubble = GroupMessageBubble(self.messages_panel, message, is_self)

            if is_self:
                self.messages_sizer.Add(bubble, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.TOP, 10)
            else:
                self.messages_sizer.Add(bubble, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        # Add extra space at the bottom
        self.messages_sizer.Add((0, 20), 0)

        # Update layout
        self.messages_panel.Layout()

        # Important: Call this after layout to ensure proper scrolling
        self.messages_panel.SetupScrolling(scroll_x=False, scroll_y=True)

        # Scroll to the bottom after a short delay to ensure layout is complete
        wx.CallLater(100, self.scroll_to_bottom)

        # Mark messages as read
        self.db.mark_messages_as_read(self.current_group_id)

    def on_send_message(self, event):
        """Handle sending a message"""
        if not self.current_group_id:
            wx.MessageBox("No group selected", "Error", wx.OK | wx.ICON_ERROR)
            return

        message_text = event.message
        attachments = event.attachments

        if not message_text and not attachments:
            return

        # Get group members with connection info
        members = self.db.get_group_members(self.current_group_id)

        # Generate message ID
        message_id = f"grp_{str(uuid.uuid4())}"
        print(f"DEBUG: Generated base group message ID: {message_id}")

        # First save to local database
        db_message_id = self.db.add_group_message(
            self.current_group_id,
            self.messenger.user_id,
            message_text,
            'sent',
            None,  # No attachments for now
            time.time(),
            'sending',
            message_id  # Use the base message ID
        )

        # Update UI immediately
        self.update_messages()

        # Send to all members async
        wx.CallAfter(self.send_to_members, members, message_text, message_id)

    def send_to_members(self, members, message, message_id):
        """Send message to all group members"""
        try:
            results = self.messenger.send_group_message(
                self.current_group_id,
                members,
                message,
                message_id
            )

            # Log the results
            print(f"Group message send results: {results}")

            # Update message status based on results
            if results.get('success'):
                # Update database with successful send
                self.db.update_message_status(message_id, 'sent')
                self.update_messages()
            else:
                # Update database with failed send
                self.db.update_message_status(message_id, 'failed')
                self.update_messages()

                # Show error message
                wx.MessageBox(
                    f"Failed to send message to all group members. Only reached {results.get('sent_count')} out of {results.get('total_members')} members.",
                    "Partial Send",
                    wx.OK | wx.ICON_WARNING
                )

        except Exception as e:
            print(f"Error sending group message: {e}")
            wx.MessageBox(
                f"Error sending group message: {e}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def on_group_info(self, event):
        """Show group info dialog"""
        if not self.current_group_id:
            return

        # Import here to avoid circular imports
        from .create_group_dialog import GroupInfoDialog

        dialog = GroupInfoDialog(self, self.db, self.current_group_id, self.messenger)
        dialog.ShowModal()
        dialog.Destroy()

        # Refresh group info in case it changed
        self.load_group(self.current_group_id)

    def scroll_to_bottom(self):
        """Scroll message panel to the bottom"""
        try:
            # Get virtual size of the scrolled area
            x, y = self.messages_panel.GetViewStart()
            _, max_y = self.messages_panel.GetVirtualSize()
            _, vh = self.messages_panel.GetClientSize()

            if max_y > vh:  # Only scroll if content exceeds visible area
                # Calculate the scroll position needed to see the bottom
                # The constant 20 is an approximation to account for scroll unit difference
                y_pos = (max_y - vh) // 20

                print(f"DEBUG: Scrolling to y position: {y_pos}")
                self.messages_panel.Scroll(0, y_pos)
        except Exception as e:
            print(f"Error scrolling to bottom: {e}")

    def handle_new_message(self, message_data):
        """Handle incoming group message"""
        # Check if this is a group message for the current group
        if message_data.get('is_group_message') and message_data.get('group_id') == self.current_group_id:
            # Update messages
            self.update_messages()

    def create_placeholder_avatar(self, size):
        """Create a placeholder group avatar"""
        bitmap = wx.Bitmap(size, size)
        dc = wx.MemoryDC(bitmap)

        # Draw circle background
        dc.SetBackground(wx.Brush(wx.Colour(100, 150, 200)))
        dc.Clear()

        # Draw circle
        dc.SetBrush(wx.Brush(wx.Colour(70, 120, 180)))
        dc.SetPen(wx.Pen(wx.Colour(70, 120, 180)))
        dc.DrawCircle(size // 2, size // 2, size // 2)

        # Draw group icon (a simple people icon)
        dc.SetBrush(wx.Brush(wx.WHITE))
        dc.SetPen(wx.Pen(wx.WHITE, 2))

        # Draw people silhouettes
        center_x = size // 2
        center_y = size // 2

        # Head
        head_radius = size // 8
        dc.DrawCircle(center_x, center_y - head_radius, head_radius)

        # Body
        dc.DrawRoundedRectangle(center_x - head_radius, center_y,
                                head_radius * 2, head_radius * 2,
                                head_radius // 2)

        dc.SelectObject(wx.NullBitmap)
        return bitmap

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