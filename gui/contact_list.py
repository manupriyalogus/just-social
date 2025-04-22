import wx
import wx.lib.scrolledpanel as scrolled
from gui.group_item import GroupItem
from gui.create_group_dialog import CreateGroupDialog

# Define the custom event type
wxEVT_CONTACT_LIST_UPDATE = wx.NewEventType()
EVT_CONTACT_LIST_UPDATE = wx.PyEventBinder(wxEVT_CONTACT_LIST_UPDATE, 1)


class ContactItem(wx.Panel):
    def __init__(self, parent, contact):
        super().__init__(parent)
        self.unread = None
        self.status = None
        self.profile_pic = None
        self.name = None
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
    def __init__(self, parent, db, messenger=None):
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        self.create_group_btn = None
        self.direct_selection_handler = None
        self.db = db
        self.messenger = messenger
        self.contacts = {}
        self.groups = {}
        self.contact_items = {}
        self.group_items = {}
        self.selected_contact = None
        self.selected_group = None
        self.is_group_selected = False

        # Initialize instance attributes
        self.contacts_panel = None
        self.groups_panel = None
        self.contacts_sizer = None
        self.groups_sizer = None
        self.search_ctrl = None

        self.init_ui()
        self.load_contacts_and_groups()
        self.Bind(EVT_CONTACT_LIST_UPDATE, self.refresh_contacts)

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

        # Tabs for Contacts and Groups
        tabs_panel = wx.Panel(self)
        tabs_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.contacts_tab = wx.Button(tabs_panel, label="Contacts", style=wx.BORDER_NONE)
        self.groups_tab = wx.Button(tabs_panel, label="Groups", style=wx.BORDER_NONE)

        # Set active tab initially
        self.contacts_tab.SetBackgroundColour(wx.Colour(240, 240, 240))

        # Bind events
        self.contacts_tab.Bind(wx.EVT_BUTTON, self.on_contacts_tab)
        self.groups_tab.Bind(wx.EVT_BUTTON, self.on_groups_tab)

        # Add to sizer
        tabs_sizer.Add(self.contacts_tab, 1, wx.EXPAND)
        tabs_sizer.Add(self.groups_tab, 1, wx.EXPAND)
        tabs_panel.SetSizer(tabs_sizer)

        # Contacts list
        self.contacts_panel = wx.Panel(self)
        self.contacts_sizer = wx.BoxSizer(wx.VERTICAL)
        self.contacts_panel.SetSizer(self.contacts_sizer)

        # Groups list (initially hidden)
        self.groups_panel = wx.Panel(self)
        self.groups_sizer = wx.BoxSizer(wx.VERTICAL)
        self.groups_panel.SetSizer(self.groups_sizer)
        self.groups_panel.Hide()

        # Create group button
        create_group_panel = wx.Panel(self)
        create_group_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.create_group_btn = wx.Button(create_group_panel, label="Create Group")
        self.create_group_btn.Bind(wx.EVT_BUTTON, self.on_create_group)

        create_group_sizer.Add(self.create_group_btn, 1, wx.EXPAND | wx.ALL, 5)
        create_group_panel.SetSizer(create_group_sizer)

        # Add all components to main sizer
        vbox.Add(search_panel, 0, wx.EXPAND)
        vbox.Add(tabs_panel, 0, wx.EXPAND)
        vbox.Add(wx.StaticLine(self), 0, wx.EXPAND)
        vbox.Add(self.contacts_panel, 1, wx.EXPAND)
        vbox.Add(self.groups_panel, 1, wx.EXPAND)
        vbox.Add(wx.StaticLine(self), 0, wx.EXPAND)
        vbox.Add(create_group_panel, 0, wx.EXPAND)

        self.SetSizer(vbox)
        self.SetupScrolling()
        self.SetBackgroundColour(wx.WHITE)

        # Bind search events
        self.search_ctrl.Bind(wx.EVT_TEXT, self.on_search)
        self.search_ctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.on_search_cancel)

    def on_contacts_tab(self, event):
        """Switch to contacts tab"""
        self.contacts_tab.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.groups_tab.SetBackgroundColour(wx.NullColour)
        self.contacts_panel.Show()
        self.groups_panel.Hide()
        self.create_group_btn.Show()
        self.Layout()

    def on_groups_tab(self, event):
        """Switch to groups tab"""
        self.groups_tab.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.contacts_tab.SetBackgroundColour(wx.NullColour)
        self.contacts_panel.Hide()
        self.groups_panel.Show()
        self.create_group_btn.Show()
        self.Layout()

    def on_create_group(self, event):
        """Handle create group button click"""
        # Find the MainWindow which has the messenger attribute
        main_window = wx.GetTopLevelParent(self)

        if not hasattr(main_window, 'messenger'):
            wx.MessageBox("Cannot access messenger to create group", "Error", wx.OK | wx.ICON_ERROR)
            return

        user_id = main_window.messenger.user_id
        dialog = CreateGroupDialog(self, self.db, user_id)

        if dialog.ShowModal() == wx.ID_OK:
            group_data = dialog.get_group_data()

            # Create the group in the database
            self.db.create_group(
                group_data['id'],
                group_data['name'],
                group_data['description'],
                group_data['created_by'],
                group_data['avatar_path']
            )

            # Add self as admin
            self.db.add_group_member(
                group_data['id'],
                group_data['created_by'],
                'admin'
            )

            # Add selected members
            for member in group_data['members']:
                self.db.add_group_member(
                    group_data['id'],
                    member['id']
                )

            # Refresh the groups list
            self.load_contacts_and_groups()

            # Switch to groups tab
            self.on_groups_tab(None)

        dialog.Destroy()

    def load_contacts_and_groups(self):
        """Load both contacts and groups"""
        self.load_contacts()
        self.load_groups()

    def load_contacts(self):
        """Load contacts from database"""
        self.contacts_sizer.Clear(True)
        self.contact_items.clear()
        self.contacts = self.db.get_contacts()

        for contact in self.contacts:
            contact_item = ContactItem(self.contacts_panel, contact)
            self.contact_items[contact['id']] = contact_item
            self.contacts_sizer.Add(contact_item, 0, wx.EXPAND)
            contact_item.Bind(wx.EVT_LEFT_DOWN, lambda evt, c=contact: self.on_contact_selected(evt, c))

        self.contacts_panel.Layout()
        self.Layout()
        self.FitInside()
        self.Refresh()

    def load_groups(self):
        """Load groups from database"""
        self.groups_sizer.Clear(True)
        self.group_items.clear()
        self.groups = self.db.get_groups()

        for group in self.groups:
            # Add member count data
            members = self.db.get_group_members(group['id'])
            group['member_count'] = len(members)

            group_item = GroupItem(self.groups_panel, group)
            self.group_items[group['id']] = group_item
            self.groups_sizer.Add(group_item, 0, wx.EXPAND)
            group_item.Bind(wx.EVT_LEFT_DOWN, lambda evt, g=group: self.on_group_selected(evt, g))

        self.groups_panel.Layout()
        self.Layout()
        self.FitInside()
        self.Refresh()

    def on_contact_selected(self, event, contact):
        # Deselect previous contact or group
        if self.is_group_selected and self.selected_group and self.selected_group['id'] in self.group_items:
            self.group_items[self.selected_group['id']].set_selected(False)
            self.is_group_selected = False
        elif self.selected_contact and self.selected_contact['id'] in self.contact_items:
            self.contact_items[self.selected_contact['id']].set_selected(False)

        # Select new contact
        self.selected_contact = contact
        self.contact_items[contact['id']].set_selected(True)

        print(f"Debug: Contact selected: {contact['id']}")

        # Use direct handler if available
        if self.direct_selection_handler:
            print(f"Debug: Calling direct selection handler for contact {contact['id']}")
            self.direct_selection_handler(contact, False)
        else:
            # Create and post event with client data
            evt = wx.CommandEvent(wx.wxEVT_LIST_ITEM_SELECTED, self.GetId())
            evt.SetClientData(contact)  # Set the contact as client data
            wx.PostEvent(self.GetParent(), evt)
            print(f"Debug: Posted selection event for contact {contact['id']}")

    def on_group_selected(self, event, group):
        # Deselect previous contact or group
        if not self.is_group_selected and self.selected_contact and self.selected_contact['id'] in self.contact_items:
            self.contact_items[self.selected_contact['id']].set_selected(False)
        elif self.is_group_selected and self.selected_group and self.selected_group['id'] in self.group_items:
            self.group_items[self.selected_group['id']].set_selected(False)

        # Select new group
        self.selected_group = group
        self.group_items[group['id']].set_selected(True)
        self.is_group_selected = True

        print(f"Debug: Group selected: {group['id']}")

        # Use direct handler if available
        if self.direct_selection_handler:
            print(f"Debug: Calling direct selection handler for group {group['id']}")
            self.direct_selection_handler(group, True)
        else:
            # Create and post event with client data and flag indicating it's a group
            evt = wx.CommandEvent(wx.wxEVT_LIST_ITEM_SELECTED, self.GetId())
            group['is_group'] = True  # Add flag
            evt.SetClientData(group)
            wx.PostEvent(self.GetParent(), evt)
            print(f"Debug: Posted selection event for group {group['id']}")

    def get_selected_contact_id(self):
        """Get the ID of the currently selected contact/group"""
        if self.is_group_selected:
            return self.selected_group['id'] if self.selected_group else None
        else:
            return self.selected_contact['id'] if self.selected_contact else None

    def is_selected_item_group(self):
        """Return whether the currently selected item is a group"""
        return self.is_group_selected

    def on_search(self, event):
        search_text = self.search_ctrl.GetValue().lower()

        # Filter contacts based on search text
        for contact_id, item in self.contact_items.items():
            contact_name = item.contact['name'].lower()
            item.Show(search_text in contact_name)

        # Filter groups based on search text
        for group_id, item in self.group_items.items():
            group_name = item.group['name'].lower()
            item.Show(search_text in group_name)

        self.contacts_panel.Layout()
        self.groups_panel.Layout()
        self.Layout()

    def on_search_cancel(self, event):
        self.search_ctrl.SetValue("")
        self.on_search(event)

    def refresh_contacts(self, event=None):
        """Reload all contacts and groups from the database"""
        self.load_contacts_and_groups()

    def update_unread_count(self, item_id, count, is_group=False):
        """Update the unread message count for a contact or group"""
        if is_group:
            if item_id in self.group_items:
                # Reload the group item to update the unread count
                group = self.db.get_group(item_id)
                if group:
                    # Add member count data
                    members = self.db.get_group_members(group['id'])
                    group['member_count'] = len(members)

                    index = self.groups_sizer.GetItemIndex(self.group_items[item_id])

                    # Remove old item
                    self.groups_sizer.Remove(index)
                    self.group_items[item_id].Destroy()

                    # Create new item
                    group_item = GroupItem(self.groups_panel, group)
                    self.group_items[item_id] = group_item
                    self.groups_sizer.Insert(index, group_item, 0, wx.EXPAND)

                    # Rebind click event
                    group_item.Bind(wx.EVT_LEFT_DOWN,
                                    lambda evt, g=group: self.on_group_selected(evt, g))

                    self.groups_panel.Layout()
        else:
            if item_id in self.contact_items:
                # Reload the contact item to update the unread count
                contact = self.db.get_contact(item_id)
                index = self.contacts_sizer.GetItemIndex(self.contact_items[item_id])

                # Remove old item
                self.contacts_sizer.Remove(index)
                self.contact_items[item_id].Destroy()

                # Create new item
                contact_item = ContactItem(self.contacts_panel, contact)
                self.contact_items[item_id] = contact_item
                self.contacts_sizer.Insert(index, contact_item, 0, wx.EXPAND)

                # Rebind click event
                contact_item.Bind(wx.EVT_LEFT_DOWN,
                                  lambda evt, c=contact: self.on_contact_selected(evt, c))

                self.contacts_panel.Layout()

    def set_direct_selection_handler(self, handler):
        """Set a direct handler for contact selection"""
        self.direct_selection_handler = handler
        print("Debug: Direct selection handler set successfully")