import wx
import os


class GroupItem(wx.Panel):
    """Group item for the contact list"""

    def __init__(self, parent, group):
        super().__init__(parent)
        self.group = group
        self.selected = False
        self.init_ui()

        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave)

    def on_paint(self, event):
        """Handle paint event to draw selection background"""
        dc = wx.PaintDC(self)
        if self.selected:
            dc.SetBrush(wx.Brush(wx.Colour(240, 240, 240)))
            dc.SetPen(wx.Pen(wx.Colour(240, 240, 240)))
            dc.DrawRectangle(0, 0, self.GetSize().width, self.GetSize().height)
        event.Skip()

    def on_mouse_enter(self, event):
        if not self.selected:
            self.SetBackgroundColour(wx.Colour(245, 245, 245))
            self.Refresh()

    def on_mouse_leave(self, event):
        if not self.selected:
            self.SetBackgroundColour(wx.WHITE)
            self.Refresh()

    def init_ui(self):
        # Main horizontal sizer
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Group avatar (placeholder)
        profile_size = 40

        # Use custom avatar if available
        avatar_path = self.group.get('avatar_path', '')
        if avatar_path and os.path.exists(avatar_path):
            img = wx.Image(avatar_path, wx.BITMAP_TYPE_ANY)
            img = self.scale_and_crop_image(img, profile_size)
            avatar_bitmap = wx.Bitmap(img)
        else:
            avatar_bitmap = self.create_group_avatar(profile_size)

        self.profile_pic = wx.StaticBitmap(
            self,
            bitmap=avatar_bitmap,
            size=(profile_size, profile_size)
        )

        # Group info (vertical sizer)
        vbox_info = wx.BoxSizer(wx.VERTICAL)

        # Group name
        self.name = wx.StaticText(self, label=self.group.get('name', 'Unknown Group'))
        name_font = self.name.GetFont()
        name_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.name.SetFont(name_font)

        # Member count or last message
        members_count = "Group"  # Default placeholder
        if 'member_count' in self.group:
            members_count = f"{self.group['member_count']} members"

        self.status = wx.StaticText(self, label=members_count)

        vbox_info.Add(self.name, 0, wx.EXPAND)
        vbox_info.Add(self.status, 0, wx.EXPAND)

        # Timestamp and unread count (vertical sizer)
        vbox_meta = wx.BoxSizer(wx.VERTICAL)

        # Add unread count if available
        unread_count = self.group.get('unread', 0)
        if unread_count > 0:
            self.unread = wx.StaticText(self, label=str(unread_count))
            self.unread.SetBackgroundColour(wx.Colour(0, 132, 255))
            self.unread.SetForegroundColour(wx.WHITE)
            vbox_meta.Add(self.unread, 0, wx.ALIGN_RIGHT)

        # Add components to main sizer
        hbox.Add(self.profile_pic, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.Add(vbox_info, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.Add(vbox_meta, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.SetSizer(hbox)
        self.Layout()

        # Set minimum size for item
        self.SetMinSize((-1, 60))

    def create_group_avatar(self, size):
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

    def set_selected(self, selected):
        self.selected = selected
        self.SetBackgroundColour(
            wx.Colour(240, 240, 240) if selected else wx.WHITE
        )
        self.Refresh()