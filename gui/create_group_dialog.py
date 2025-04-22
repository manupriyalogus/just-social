import wx
import wx.adv
import os
import uuid


class CreateGroupDialog(wx.Dialog):
    def __init__(self, parent, db, user_id):
        super().__init__(parent, title="Create Group", size=(400, 500))
        self.contacts_data = None
        self.contact_list = None
        self.desc_ctrl = None
        self.avatar = None
        self.name_ctrl = None
        self.db = db
        self.user_id = user_id
        self.selected_contacts = []
        self.group_avatar_path = ""
        self.main_window = wx.GetTopLevelParent(self)  # Get reference to main window

        self.init_ui()

    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Group info section
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Group avatar
        self.avatar = wx.StaticBitmap(
            panel,
            bitmap=self.create_placeholder_avatar(80),
            size=(80, 80)
        )
        avatar_button = wx.Button(panel, label="Set Avatar")
        avatar_button.Bind(wx.EVT_BUTTON, self.on_set_avatar)

        avatar_sizer = wx.BoxSizer(wx.VERTICAL)
        avatar_sizer.Add(self.avatar, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        avatar_sizer.Add(avatar_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # Group name and description
        fields_sizer = wx.BoxSizer(wx.VERTICAL)

        name_label = wx.StaticText(panel, label="Group Name:")
        self.name_ctrl = wx.TextCtrl(panel)

        desc_label = wx.StaticText(panel, label="Description (optional):")
        self.desc_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 60))

        fields_sizer.Add(name_label, 0, wx.ALL, 5)
        fields_sizer.Add(self.name_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        fields_sizer.Add(desc_label, 0, wx.ALL, 5)
        fields_sizer.Add(self.desc_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        info_sizer.Add(avatar_sizer, 0, wx.ALL, 10)
        info_sizer.Add(fields_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # Add members section
        members_label = wx.StaticText(panel, label="Add Members:")

        # Contact list with checkboxes
        self.contact_list = wx.CheckListBox(panel, size=(-1, 200))
        self.load_contacts()

        # Buttons
        button_sizer = wx.StdDialogButtonSizer()
        create_button = wx.Button(panel, wx.ID_OK, "Create Group")
        cancel_button = wx.Button(panel, wx.ID_CANCEL)

        button_sizer.AddButton(create_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        # Add everything to main sizer
        main_sizer.Add(info_sizer, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(members_label, 0, wx.ALL, 5)
        main_sizer.Add(self.contact_list, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_create, id=wx.ID_OK)

        panel.SetSizer(main_sizer)
        self.Center()

    def load_contacts(self):
        """Load contacts from database into the list"""
        contacts = self.db.get_contacts()

        contact_names = []
        self.contacts_data = []

        for contact in contacts:
            # Skip self contact if it exists
            if contact['id'] == self.user_id:
                continue

            contact_names.append(contact['name'])
            self.contacts_data.append(contact)

        self.contact_list.SetItems(contact_names)

    def on_set_avatar(self, event):
        """Handle setting group avatar"""
        with wx.FileDialog(
                self, "Choose an image", wildcard="Image files (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            path = dialog.GetPath()

            # Create a copy of the image in the app data directory
            filename = os.path.basename(path)
            # Use your app's data directory structure
            target_dir = os.path.join(self.db.data_dir, "avatars")
            os.makedirs(target_dir, exist_ok=True)

            # Generate unique name to avoid conflicts
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            target_path = os.path.join(target_dir, unique_filename)

            # Copy file
            import shutil
            shutil.copy2(path, target_path)

            # Update avatar display
            self.group_avatar_path = target_path
            self.update_avatar_display()

    def update_avatar_display(self):
        """Update the avatar display with selected image"""
        if os.path.exists(self.group_avatar_path):
            img = wx.Image(self.group_avatar_path, wx.BITMAP_TYPE_ANY)
            # Scale to fit
            img = self.scale_and_crop_image(img, 80)
            self.avatar.SetBitmap(wx.Bitmap(img))

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

    def on_create(self, event):
        """Handle group creation"""
        group_name = self.name_ctrl.GetValue().strip()
        description = self.desc_ctrl.GetValue().strip()

        if not group_name:
            wx.MessageBox("Please enter a group name", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Get selected contacts
        selections = self.contact_list.GetCheckedItems()
        if not selections:
            wx.MessageBox("Please select at least one contact", "Error", wx.OK | wx.ICON_ERROR)
            return

        selected_contacts = [self.contacts_data[i] for i in selections]

        # Save for access by the caller
        self.group_name = group_name
        self.group_description = description
        self.selected_contacts = selected_contacts

        # Continue with default dialog behavior (will close with ID_OK)
        event.Skip()

    def get_group_data(self):
        """Return the data needed to create the group"""
        return {
            'id': uuid.uuid4().hex,
            'name': self.group_name,
            'description': self.group_description,
            'avatar_path': self.group_avatar_path,
            'members': self.selected_contacts,
            'created_by': self.user_id
        }

    def send_group_invitation(self, group_data):
        """Send group invitation to all members"""
        if not hasattr(self.main_window, 'messenger'):
            wx.MessageBox("Cannot access messenger to sync group", "Error", wx.OK | wx.ICON_ERROR)
            return False

        # Get all the members to send invitation to
        members = group_data['members']

        # Send invitation using the messenger
        results = self.main_window.messenger.send_group_invitation(group_data, members)

        if results.get('success'):
            wx.MessageBox(
                f"Group created successfully and invitation sent to {results.get('sent_count')} members.",
                "Group Created",
                wx.OK | wx.ICON_INFORMATION
            )
            return True
        else:
            wx.MessageBox(
                f"Group created, but could not send invitations to all members. Only reached {results.get('sent_count')} out of {results.get('total_members')} members.",
                "Partial Success",
                wx.OK | wx.ICON_WARNING
            )
            return False

class GroupInfoDialog(wx.Dialog):
    def __init__(self, parent, db, group_id, messenger=None):
        super().__init__(parent, title="Group Info", size=(400, 500))
        self.db = db
        self.group_id = group_id
        self.messenger = messenger

        # Load group data
        self.group = self.db.get_group(group_id)
        self.members = self.db.get_group_members(group_id)

        self.init_ui()

    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Group info section
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Group avatar
        avatar_path = self.group.get('avatar_path', '')
        if avatar_path and os.path.exists(avatar_path):
            img = wx.Image(avatar_path, wx.BITMAP_TYPE_ANY)
            img = self.scale_and_crop_image(img, 80)
            avatar_bitmap = wx.Bitmap(img)
        else:
            avatar_bitmap = self.create_placeholder_avatar(80)

        self.avatar = wx.StaticBitmap(
            panel, bitmap=avatar_bitmap, size=(80, 80)
        )

        # Group name and description
        fields_sizer = wx.BoxSizer(wx.VERTICAL)

        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_label = wx.StaticText(panel, label="Group Name:")
        self.name_text = wx.StaticText(panel, label=self.group.get('name', 'Unknown Group'))
        name_font = self.name_text.GetFont()
        name_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.name_text.SetFont(name_font)

        name_sizer.Add(name_label, 0, wx.RIGHT, 5)
        name_sizer.Add(self.name_text, 1)

        desc_sizer = wx.BoxSizer(wx.VERTICAL)
        desc_label = wx.StaticText(panel, label="Description:")
        self.desc_text = wx.StaticText(panel, label=self.group.get('description', ''))

        desc_sizer.Add(desc_label, 0)
        desc_sizer.Add(self.desc_text, 0, wx.TOP, 5)

        fields_sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)
        fields_sizer.Add(desc_sizer, 0, wx.EXPAND | wx.ALL, 5)

        info_sizer.Add(self.avatar, 0, wx.ALL, 10)
        info_sizer.Add(fields_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # Members section
        members_label = wx.StaticText(panel, label=f"Members ({len(self.members)}):")

        # Member list
        self.member_list = wx.ListCtrl(
            panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL, size=(-1, 200)
        )
        self.member_list.InsertColumn(0, "Name", width=200)
        self.member_list.InsertColumn(1, "Role", width=100)

        self.load_members()

        # Buttons for admin actions
        admin_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Only show these buttons if user is an admin
        is_admin = False
        for member in self.members:
            if member.get('id') == self.messenger.user_id and member.get('role') == 'admin':
                is_admin = True
                break

        if is_admin:
            self.add_member_btn = wx.Button(panel, label="Add Member")
            self.remove_member_btn = wx.Button(panel, label="Remove Member")

            self.add_member_btn.Bind(wx.EVT_BUTTON, self.on_add_member)
            self.remove_member_btn.Bind(wx.EVT_BUTTON, self.on_remove_member)

            admin_sizer.Add(self.add_member_btn, 0, wx.RIGHT, 5)
            admin_sizer.Add(self.remove_member_btn, 0)

        # Close button
        button_sizer = wx.StdDialogButtonSizer()
        close_button = wx.Button(panel, wx.ID_CLOSE)
        button_sizer.AddButton(close_button)
        button_sizer.Realize()

        # Add everything to main sizer
        main_sizer.Add(info_sizer, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(members_label, 0, wx.ALL, 5)
        main_sizer.Add(self.member_list, 1, wx.EXPAND | wx.ALL, 5)

        if is_admin:
            main_sizer.Add(admin_sizer, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_close, id=wx.ID_CLOSE)

        panel.SetSizer(main_sizer)
        self.Center()

    def load_members(self):
        """Load group members into the list"""
        self.member_list.DeleteAllItems()

        for i, member in enumerate(self.members):
            index = self.member_list.InsertItem(i, member.get('name', 'Unknown'))
            self.member_list.SetItem(index, 1, member.get('role', 'member'))

    def on_add_member(self, event):
        """Handle adding a new member to the group"""
        # Get contacts not in the group yet
        all_contacts = self.db.get_contacts()
        current_member_ids = [m.get('id') for m in self.members]

        available_contacts = []
        for contact in all_contacts:
            if contact.get('id') not in current_member_ids:
                available_contacts.append(contact)

        if not available_contacts:
            wx.MessageBox("All contacts are already in this group", "Information",
                          wx.OK | wx.ICON_INFORMATION)
            return

        # Show dialog to select contacts
        dlg = wx.MultiChoiceDialog(
            self, "Select contacts to add:", "Add Members",
            [c.get('name', 'Unknown') for c in available_contacts]
        )

        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            selected_contacts = [available_contacts[i] for i in selections]

            for contact in selected_contacts:
                self.db.add_group_member(self.group_id, contact.get('id'))

            # Refresh member list
            self.members = self.db.get_group_members(self.group_id)
            self.load_members()

            # Update member count label
            for child in self.GetChildren():
                if isinstance(child, wx.StaticText) and "Members" in child.GetLabel():
                    child.SetLabel(f"Members ({len(self.members)}):")
                    break

        dlg.Destroy()

    def on_remove_member(self, event):
        """Handle removing a member from the group"""
        selected = self.member_list.GetFirstSelected()
        if selected == -1:
            wx.MessageBox("Please select a member to remove", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        member = self.members[selected]

        # Confirm removal
        dlg = wx.MessageDialog(
            self,
            f"Are you sure you want to remove {member.get('name', 'this member')} from the group?",
            "Confirm Removal",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        )

        if dlg.ShowModal() == wx.ID_YES:
            self.db.remove_group_member(self.group_id, member.get('id'))

            # Refresh member list
            self.members = self.db.get_group_members(self.group_id)
            self.load_members()

            # Update member count label
            for child in self.GetChildren():
                if isinstance(child, wx.StaticText) and "Members" in child.GetLabel():
                    child.SetLabel(f"Members ({len(self.members)}):")
                    break

        dlg.Destroy()

    def on_close(self, event):
        """Handle dialog close"""
        self.EndModal(wx.ID_CLOSE)

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
