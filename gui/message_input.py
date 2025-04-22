import wx
import wx.adv
import os

# Custom event for message sending
wxEVT_MESSAGE_SEND = wx.NewEventType()
EVT_MESSAGE_SEND = wx.PyEventBinder(wxEVT_MESSAGE_SEND, 1)


class MessageEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, message="", attachments=None):
        super().__init__(etype, eid)
        self.message = message
        self.attachments = attachments or []


class MessageInput(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.send_btn = None
        self.input_ctrl = None
        self.attach_btn = None
        self.emoji_btn = None
        self.attachments = []
        self.init_ui()

    def init_ui(self):
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Emoji button
        self.emoji_btn = wx.Button(self, label="😊", size=(40, -1))

        # Attachment button
        self.attach_btn = wx.Button(self, label="📎", size=(40, -1))

        # Message input - Add wxTE_PROCESS_ENTER flag
        self.input_ctrl = wx.TextCtrl(self,
                                      style=wx.TE_MULTILINE |
                                            wx.TE_RICH2 |
                                            wx.TE_PROCESS_ENTER)

        # Send button
        self.send_btn = wx.Button(self, label="Send", size=(60, -1))

        # Add components to sizer
        hbox.Add(self.emoji_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        hbox.Add(self.attach_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        hbox.Add(self.input_ctrl, 1, wx.ALL | wx.EXPAND, 2)
        hbox.Add(self.send_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)

        self.SetSizer(hbox)

        # Bind events
        self.emoji_btn.Bind(wx.EVT_BUTTON, self.on_emoji)
        self.attach_btn.Bind(wx.EVT_BUTTON, self.on_attach)
        self.send_btn.Bind(wx.EVT_BUTTON, self.on_send)
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_send)

    def on_emoji(self, event):
        # Create and show emoji picker
        emoji_picker = EmojiPicker(self)
        emoji_picker.Bind(EVT_EMOJI_SELECT, self.on_emoji_selected)
        emoji_picker.Show()

    def on_emoji_selected(self, event):
        self.input_ctrl.WriteText(event.emoji)

    def on_attach(self, event):
        with wx.FileDialog(self, "Choose files", wildcard="All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as dialog:

            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            # Get paths of selected files
            paths = dialog.GetPaths()

            # Store attachments
            for path in paths:
                self.attachments.append({
                    'path': path,
                    'name': os.path.basename(path),
                    'type': self.get_file_type(path)
                })

            # Update attachment count
            self.update_attachment_button()

    def on_send(self, event):
        message = self.input_ctrl.GetValue().strip()

        if not message and not self.attachments:
            return

        # Create and post message event
        evt = MessageEvent(wxEVT_MESSAGE_SEND, self.GetId(),
                           message, self.attachments)
        wx.PostEvent(self, evt)

        # Clear input
        self.input_ctrl.SetValue("")
        self.attachments = []
        self.update_attachment_button()

    def update_attachment_button(self):
        if self.attachments:
            self.attach_btn.SetLabel(f"📎({len(self.attachments)})")
        else:
            self.attach_btn.SetLabel("📎")

    def get_file_type(self, path):
        _, ext = os.path.splitext(path)
        ext = ext.lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'image'
        elif ext in ['.mp4', '.avi', '.mov']:
            return 'video'
        elif ext == '.pdf':
            return 'pdf'
        else:
            return 'file'


class EmojiPicker(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title="Emoji Picker",
                         style=wx.FRAME_FLOAT_ON_PARENT | wx.FRAME_TOOL_WINDOW)

        self.init_ui()

    def init_ui(self):
        panel = wx.Panel(self)
        grid = wx.GridSizer(8, 8, 2, 2)

        # Basic emoji set
        emojis = ["😊", "😂", "😍", "🤔", "😅", "😭", "😘", "🙄",
                  "😩", "😡", "😢", "😜", "😞", "😱", "😳", "😴",
                  "👍", "👎", "👌", "✌️", "🤞", "👊", "✋", "🤚",
                  "❤️", "💔", "💖", "💙", "💚", "💛", "💜", "🖤"]

        for emoji in emojis:
            btn = wx.Button(panel, label=emoji, size=(30, 30))
            btn.Bind(wx.EVT_BUTTON, lambda evt, e=emoji: self.on_emoji_select(evt, e))
            grid.Add(btn, 0, wx.ALL, 1)

        panel.SetSizer(grid)
        self.Fit()

    def on_emoji_select(self, event, emoji):
        # Create and post emoji select event
        evt = EmojiEvent(wxEVT_EMOJI_SELECT, self.GetId(), emoji)
        wx.PostEvent(self.GetParent(), evt)
        self.Close()


# Custom event for emoji selection
wxEVT_EMOJI_SELECT = wx.NewEventType()
EVT_EMOJI_SELECT = wx.PyEventBinder(wxEVT_EMOJI_SELECT, 1)


class EmojiEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, emoji):
        super().__init__(etype, eid)
        self.emoji = emoji
