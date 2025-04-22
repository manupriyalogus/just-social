import wx


class ThemeManager:
    def __init__(self, config):
        self.config = config
        self.current_theme = self.config.get('theme', 'light')
        self.themes = {
            'light': {
                'background': wx.Colour(255, 255, 255),
                'foreground': wx.Colour(0, 0, 0),
                'chat_bg': wx.Colour(240, 240, 240),
                'sent_message_bg': wx.Colour(220, 248, 198),
                'received_message_bg': wx.Colour(255, 255, 255),
                'message_text': wx.Colour(0, 0, 0),
                'timestamp': wx.Colour(128, 128, 128),
                'link': wx.Colour(0, 102, 204),
                'sidebar_bg': wx.Colour(240, 240, 240),
                'sidebar_selected': wx.Colour(230, 230, 230),
                'border': wx.Colour(224, 224, 224),
                'input_bg': wx.Colour(255, 255, 255),
                'button_bg': wx.Colour(0, 128, 105),
                'button_fg': wx.Colour(255, 255, 255),
                'hover_bg': wx.Colour(245, 245, 245)
            },
            'dark': {
                'background': wx.Colour(33, 33, 33),
                'foreground': wx.Colour(255, 255, 255),
                'chat_bg': wx.Colour(17, 27, 33),
                'sent_message_bg': wx.Colour(5, 97, 98),
                'received_message_bg': wx.Colour(38, 45, 49),
                'message_text': wx.Colour(255, 255, 255),
                'timestamp': wx.Colour(178, 178, 178),
                'link': wx.Colour(0, 175, 255),
                'sidebar_bg': wx.Colour(28, 28, 28),
                'sidebar_selected': wx.Colour(38, 38, 38),
                'border': wx.Colour(54, 54, 54),
                'input_bg': wx.Colour(51, 51, 51),
                'button_bg': wx.Colour(0, 150, 136),
                'button_fg': wx.Colour(255, 255, 255),
                'hover_bg': wx.Colour(45, 45, 45)
            }
        }

    def get_color(self, element):
        """Get color for a specific element in current theme"""
        return self.themes[self.current_theme].get(element)

    def set_theme(self, theme):
        """Set current theme (light/dark)"""
        if theme in self.themes:
            self.current_theme = theme
            self.config.set('theme', theme)
            return True
        return False

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        return self.set_theme(new_theme)

    def apply_theme_to_window(self, window):
        """Apply current theme to a window and all its children"""
        bg_color = self.get_color('background')
        fg_color = self.get_color('foreground')

        window.SetBackgroundColour(bg_color)
        window.SetForegroundColour(fg_color)

        self._apply_theme_to_children(window)
        window.Refresh()

    def _apply_theme_to_children(self, parent):
        """Recursively apply theme to all child widgets"""
        for child in parent.GetChildren():
            if isinstance(child, wx.Window):
                self._apply_theme_to_widget(child)
                self._apply_theme_to_children(child)

    def _apply_theme_to_widget(self, widget):
        """Apply theme to a specific widget based on its type"""
        if isinstance(widget, wx.TextCtrl):
            widget.SetBackgroundColour(self.get_color('input_bg'))
            widget.SetForegroundColour(self.get_color('foreground'))

        elif isinstance(widget, wx.Button):
            widget.SetBackgroundColour(self.get_color('button_bg'))
            widget.SetForegroundColour(self.get_color('button_fg'))

        elif isinstance(widget, wx.Panel):
            widget.SetBackgroundColour(self.get_color('background'))
            widget.SetForegroundColour(self.get_color('foreground'))

        elif isinstance(widget, wx.ListCtrl):
            widget.SetBackgroundColour(self.get_color('sidebar_bg'))
            widget.SetForegroundColour(self.get_color('foreground'))

        # Add more widget types as needed

    def get_css(self):
        """Get CSS for web-based components"""
        theme = self.themes[self.current_theme]
        return f"""
            body {{
                background-color: {theme['chat_bg'].GetAsString(wx.C2S_HTML_SYNTAX)};
                color: {theme['message_text'].GetAsString(wx.C2S_HTML_SYNTAX)};
            }}
            .message.sent {{
                background-color: {theme['sent_message_bg'].GetAsString(wx.C2S_HTML_SYNTAX)};
            }}
            .message.received {{
                background-color: {theme['received_message_bg'].GetAsString(wx.C2S_HTML_SYNTAX)};
            }}
            .timestamp {{
                color: {theme['timestamp'].GetAsString(wx.C2S_HTML_SYNTAX)};
            }}
            a {{
                color: {theme['link'].GetAsString(wx.C2S_HTML_SYNTAX)};
            }}
        """
