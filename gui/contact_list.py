import wx
import wx.lib.scrolledpanel as scrolled

# Define the custom event type
wxEVT_CONTACT_LIST_UPDATE = wx.NewEventType()
EVT_CONTACT_LIST_UPDATE = wx.PyEventBinder(wxEVT_CONTACT_LIST_UPDATE, 1)


class ContactItem(wx.Panel):
    def __init__(self, parent, contact):
        super().__init__(parent)
        self.contact = contact
        self.selected = False
        self.init_ui()

        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)  # This binding causes the error
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave)

    # Missing method definition
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

        # Profile picture (placeholder)
        profile_size = 40
        self.profile_pic = wx.StaticBitmap(
            self,
            bitmap=self.create_profile_bitmap(profile_size),
            size=(profile_size, profile_size)
        )

        # Contact info (vertical sizer)
        vbox_info = wx.BoxSizer(wx.VERTICAL)

        # Contact name
        self.name = wx.StaticText(self, label=self.contact.get('name', 'Unknown'))
        name_font = self.name.GetFont()
        name_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.name.SetFont(name_font)

        # Last message or status
        status_text = self.contact.get('status', '')
        self.status = wx.StaticText(self, label=status_text)

        vbox_info.Add(self.name, 0, wx.EXPAND)
        vbox_info.Add(self.status, 0, wx.EXPAND)

        # Timestamp and unread count (vertical sizer)
        vbox_meta = wx.BoxSizer(wx.VERTICAL)

        # Add unread count if available
        unread_count = self.contact.get('unread', 0)
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

    def set_selected(self, selected):
        self.selected = selected
        self.SetBackgroundColour(
            wx.Colour(240, 240, 240) if selected else wx.WHITE
        )
        self.Refresh()


class ContactList(scrolled.ScrolledPanel):
    def __init__(self, parent, db):
        super().__init__(parent, style=wx.BORDER_SIMPLE)  # Add a border for visibility
        self.direct_selection_handler = None
        self.db = db
        self.contacts = {}
        self.contact_items = {}
        self.selected_contact = None

        # Initialize instance attributes in __init__
        self.contacts_panel = None
        self.contacts_sizer = None
        self.search_ctrl = None

        self.init_ui()
        self.load_contacts()
        self.Bind(EVT_CONTACT_LIST_UPDATE, self.refresh_contacts)

        # Debugging: Print the number of contacts loaded
        print(f"Loaded {len(self.contact_items)} contacts")

    def init_ui(self):
        # Main vertical sizer
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Search box
        search_panel = wx.Panel(self)
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_ctrl = wx.SearchCtrl(search_panel, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.ShowSearchButton(True)
        self.search_ctrl.ShowCancelButton(True)
        search_sizer.Add(self.search_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        search_panel.SetSizer(search_sizer)

        # Contacts list
        self.contacts_panel = wx.Panel(self)
        self.contacts_sizer = wx.BoxSizer(wx.VERTICAL)
        self.contacts_panel.SetSizer(self.contacts_sizer)

        vbox.Add(search_panel, 0, wx.EXPAND)
        vbox.Add(wx.StaticLine(self), 0, wx.EXPAND)
        vbox.Add(self.contacts_panel, 1, wx.EXPAND)

        self.SetSizer(vbox)
        self.SetupScrolling()
        self.SetBackgroundColour(wx.WHITE)  # Set a background color for visibility

    def set_direct_selection_handler(self, handler):
        """Set a direct handler for contact selection"""
        self.direct_selection_handler = handler

    def load_contacts(self):
        self.contacts_sizer.Clear(True)
        self.contact_items.clear()
        self.contacts = self.db.get_contacts()

        for contact in self.contacts:
            print(f"Debug: Contact data: {contact}")
            contact_item = ContactItem(self.contacts_panel, contact)
            self.contact_items[contact['id']] = contact_item
            self.contacts_sizer.Add(contact_item, 0, wx.EXPAND)
            contact_item.Bind(wx.EVT_LEFT_DOWN, lambda evt, c=contact: self.on_contact_selected(evt, c))

            # Debugging: Print contact details
            print(f"Added contact: {contact}")

        self.contacts_panel.Layout()
        self.Layout()
        self.FitInside()
        self.Refresh()

    def on_search(self, event):
        search_text = self.search_ctrl.GetValue().lower()

        # Filter contacts based on search text
        for contact_id, item in self.contact_items.items():
            contact_name = item.contact['name'].lower()
            item.Show(search_text in contact_name)

        self.contacts_panel.Layout()
        self.Layout()

    def on_search_cancel(self, event):
        self.search_ctrl.SetValue("")
        # self.on_search(event)

    def on_contact_selected(self, event, contact):
        # Deselect previous contact
        if self.selected_contact and self.selected_contact['id'] in self.contact_items:
            self.contact_items[self.selected_contact['id']].set_selected(False)

        # Select new contact
        self.selected_contact = contact
        self.contact_items[contact['id']].set_selected(True)

        print(f"Debug: Contact selected: {contact['id']}")

        # Use direct handler if available
        if self.direct_selection_handler:
            print(f"Debug: Calling direct selection handler for contact {contact['id']}")
            self.direct_selection_handler(contact)
        else:
            # Create and post event with client data
            evt = wx.CommandEvent(wx.wxEVT_LIST_ITEM_SELECTED, self.GetId())
            evt.SetClientData(contact)  # Set the contact as client data
            wx.PostEvent(self.GetParent(), evt)
            print(f"Debug: Posted selection event for contact {contact['id']}")

    def get_selected_contact_id(self):
        """Get the ID of the currently selected contact"""
        return self.selected_contact['id'] if self.selected_contact else None

    def update_contact_status(self, contact_id, status):
        """Update the status of a contact"""
        if contact_id in self.contact_items:
            self.contact_items[contact_id].status.SetLabel(status)

    def update_unread_count(self, contact_id, count):
        """Update the unread message count for a contact"""
        if contact_id in self.contact_items:
            # Reload the contact item to update the unread count
            contact = self.db.get_contact(contact_id)
            index = self.contacts_sizer.GetItemIndex(self.contact_items[contact_id])

            # Remove old item
            self.contacts_sizer.Remove(index)
            self.contact_items[contact_id].Destroy()

            # Create new item
            contact_item = ContactItem(self.contacts_panel, contact)
            self.contact_items[contact_id] = contact_item
            self.contacts_sizer.Insert(index, contact_item, 0, wx.EXPAND)

            # Rebind click event
            contact_item.Bind(wx.EVT_LEFT_DOWN,
                              lambda evt, c=contact: self.on_contact_selected(evt, c))

            self.contacts_panel.Layout()

    def refresh_contacts(self):
        """Reload all contacts from the database"""
        self.load_contacts()
