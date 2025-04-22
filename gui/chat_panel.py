import base64
import os
import time
from datetime import datetime
import uuid
import wx
import wx.html2
import json

from utils.file_handler import FileHandler
from .message_input import MessageInput, EVT_MESSAGE_SEND  # Import the custom event


class ChatPanel(wx.Panel):
    def __init__(self, parent, db, messenger, config):
        super().__init__(parent)
        self.message_input = None
        self.messages_view = None
        self.contact_status = None
        self.contact_name = None
        self.header = None
        self.refresh_timer = None
        self.last_loaded_chat_id = None
        self.config = None
        self.db = db
        self.messenger = messenger
        self.current_chat_id = None
        self.file_handler = FileHandler(config)

        # Flag to track if the panel has been initialized
        self.is_initialized = False

        # Register status update callback with messenger
        if hasattr(self.messenger, 'set_status_update_callback'):
            print("DEBUG: Registering status update callback with messenger")
            self.messenger.set_status_update_callback(self.on_message_status_update)
        else:
            print("WARNING: Messenger does not support status update callbacks")

        self.init_ui()
        self.is_initialized = True

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Chat header
        self.header = wx.Panel(self)
        hbox_header = wx.BoxSizer(wx.HORIZONTAL)

        self.contact_name = wx.StaticText(self.header, label="Select a chat")
        self.contact_status = wx.StaticText(self.header, label="")

        hbox_header.Add(self.contact_name, 1, wx.ALL | wx.EXPAND, 5)
        hbox_header.Add(self.contact_status, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.header.SetSizer(hbox_header)

        # Chat messages area using WebView
        self.messages_view = wx.html2.WebView.New(self)
        self.messages_view.SetPage(self.get_messages_html([]), "")

        # Message input area
        self.message_input = MessageInput(self)

        # Add components to main sizer
        vbox.Add(self.header, 0, wx.EXPAND | wx.ALL, 2)
        vbox.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 0)
        vbox.Add(self.messages_view, 1, wx.EXPAND | wx.ALL, 2)
        vbox.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 0)
        vbox.Add(self.message_input, 0, wx.EXPAND | wx.ALL, 2)

        self.SetSizer(vbox)

        # Bind events
        self.message_input.Bind(EVT_MESSAGE_SEND, self.on_message_send)

        # Set up a timer to periodically refresh message statuses
        self.refresh_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_refresh_timer, self.refresh_timer)
        self.refresh_timer.Start(5000)  # Refresh every 5 seconds

    def on_refresh_timer(self, event):
        """Periodically refresh messages to ensure statuses are up to date"""
        if self.current_chat_id and self.is_initialized:
            self.update_messages()

    def load_chat(self, contact_id):
        """Load chat for a specific contact"""
        print(f"DEBUG: ChatPanel.load_chat called with contact_id: {contact_id}")
        try:
            self.current_chat_id = contact_id

            # Get contact info
            contact = self.db.get_contact(contact_id)
            if contact:
                self.contact_name.SetLabel(contact['name'])
                self.contact_status.SetLabel(contact.get('status', ''))

                # Load chat history
                messages = self.db.get_chat_messages(contact_id)
                print(f"DEBUG: Got {len(messages)} messages for contact {contact_id}")

                # Print first message for debugging if any exist
                if messages:
                    print(f"DEBUG: First message: {messages[0]}")

                # Update messages display
                self.update_messages(messages)

                # Mark messages as read
                self.db.mark_messages_as_read(contact_id)
            else:
                print(f"ERROR: Contact not found for ID: {contact_id}")
        except Exception as e:
            print(f"ERROR in load_chat: {e}")
            import traceback
            traceback.print_exc()

    def update_messages(self, messages=None):
        """Update the messages display"""
        print(f"DEBUG: Updating messages view")

        if messages is None:
            if self.current_chat_id:
                messages = self.db.get_chat_messages(self.current_chat_id)
                print(f"DEBUG: Retrieved {len(messages)} messages from database")
            else:
                messages = []
                print("DEBUG: No current chat ID, using empty message list")

        # First, get the current scroll information before updating content
        try:
            position_script = """
            (function() {
                var scrollPos = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop;
                var scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;
                var clientHeight = document.documentElement.clientHeight || window.innerHeight;

                // Check if we're at the bottom
                var atBottom = (scrollHeight - scrollPos - clientHeight < 50);

                return JSON.stringify({
                    pos: scrollPos,
                    atBottom: atBottom
                });
            })();
            """

            result = self.messages_view.RunScript(position_script)
            if result:
                scroll_info = json.loads(result)
                at_bottom = scroll_info.get('atBottom', True)  # Default to True if undefined
                print(f"DEBUG: User was at bottom: {at_bottom}")
            else:
                at_bottom = True
        except Exception as e:
            print(f"DEBUG: Error getting scroll position: {e}")
            at_bottom = True  # Default if there's an error

        # Generate HTML content without any auto-scroll scripts
        html_content = self.get_messages_html(messages)

        # Set the content
        self.messages_view.SetPage(html_content, "")
        print("DEBUG: Set page content in WebView")

        # Only scroll to bottom if the user was already at the bottom
        # or if this is a fresh chat (first load)
        if at_bottom or not hasattr(self, 'last_loaded_chat_id') or self.last_loaded_chat_id != self.current_chat_id:
            # We use a delayed approach to ensure the content is fully rendered
            def do_scroll_to_bottom():
                try:
                    scroll_script = "window.scrollTo(0, document.body.scrollHeight);"
                    self.messages_view.RunScript(scroll_script)
                    print("DEBUG: Scrolled to bottom")
                except Exception as e:
                    print(f"WARNING: Could not scroll to bottom: {e}")

            # Delay the scroll to ensure rendering is complete
            wx.CallLater(100, do_scroll_to_bottom)

        # Remember which chat we last loaded
        self.last_loaded_chat_id = self.current_chat_id

        # Mark messages as read
        self.db.mark_messages_as_read(self.current_chat_id)

    def scroll_to_bottom(self):
        """Scroll the message view to the bottom"""
        try:
            self.messages_view.RunScript("setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 100);")
            print("DEBUG: Executed scroll script")
        except AttributeError:
            # Try alternative method for older wxPython versions
            try:
                self.messages_view.ExecuteJavascript("window.scrollTo(0, document.body.scrollHeight);")
                print("DEBUG: Executed scroll script (using ExecuteJavascript)")
            except Exception as e:
                print(f"WARNING: Could not scroll to bottom: {e}")

    def get_messages_html(self, messages):
        """Generate HTML for messages"""
        html = """
        <html>
        <head>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 10px;
                    background-color: #f0f0f0;
                }
                .message {
                    max-width: 70%;
                    margin: 5px;
                    padding: 10px;
                    border-radius: 10px;
                    clear: both;
                    position: relative;
                }
                .sent {
                    background-color: #DCF8C6;
                    float: right;
                }
                .received {
                    background-color: #FFFFFF;
                    float: left;
                }
                .meta-info {
                    font-size: 0.8em;
                    color: #888;
                    margin-top: 5px;
                    display: flex;
                    justify-content: space-between;
                }
                .timestamp {
                    margin-right: 5px;
                }
                .status::after {
                    margin-left: 5px;
                }
                .status-sending::after {
                    content: "⏱️ Sending...";
                }
                .status-sent::after {
                    content: "✓";
                }
                .status-delivered::after {
                    content: "✓✓";
                }
                .status-read::after {
                    content: "✓✓ Read";
                    color: #4FC3F7;
                }
                .status-failed::after {
                    content: "❌ Failed";
                    color: #F44336;
                }
                .status-error::after {
                    content: "⚠️ Error";
                    color: #F44336;
                }
                .status-timeout::after {
                    content: "⏱️ Timeout";
                    color: #FF9800;
                }
                .status-connection_error::after {
                    content: "⚠️ Connection Failed";
                    color: #F44336;
                }
            </style>
            <script>
                // Simple JavaScript to allow dynamic updates
                function updateMessageStatus(messageId, newStatus) {
                    console.log("Updating message " + messageId + " to status: " + newStatus);
                    var msgElement = document.getElementById(messageId);
                    if (msgElement) {
                        var statusElement = msgElement.querySelector('.status');
                        if (statusElement) {
                            statusElement.className = 'status status-' + newStatus;
                            return true;
                        }
                    }
                    return false;
                }
            </script>
        </head>
        <body>
        """

        for message in messages:
            message_class = 'sent' if message['type'] == 'sent' else 'received'
            status = message.get('status', 'sent')
            status_class = f"status-{status}"
            message_id = message.get('message_id', f"msg_{message.get('id', '')}")

            # Debug status
         #   print(f"DEBUG: Message {message_id} has status: {status}")

            # Parse timestamp correctly based on its format
            try:
                # Handle timestamp as string in format "2025-02-25 14:15:02"
                if isinstance(message['timestamp'], str):
                    timestamp = datetime.strptime(message['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p')
                # Handle timestamp as integer (unix timestamp)
                else:
                    timestamp = datetime.fromtimestamp(message['timestamp']).strftime('%I:%M %p')
            except Exception as e:
                print(f"Error parsing timestamp: {e}, using current time instead")
                timestamp = datetime.now().strftime('%I:%M %p')

            html += f'<div class="message {message_class}" id="{message_id}">'
            # print("=============================")
            # print(message)
            # print(message["content"])
            inner_content={}
            try:
                inner_content = json.loads(message["content"])
            except json.JSONDecodeError:
                inner_content["type"] = "txt"
                inner_content["content"] = message["content"]
            #print(inner_content)
            # json_message= json.loads(str(message))
            # content = json_message["content"]
            # print(json_message["content"])
            #print(content["type"])
            if inner_content["type"] == "img" :
                # with open(inner_content["content"] , 'rb') as image_file:
                #     image_data = base64.b64encode(image_file.read()).decode('utf-8')
                html += f'<div class="image"><img src="data:image/jpeg;base64,{inner_content["content"]}" style="max-width: 300px; height: 300px" /></div>'
            else:
                html += f'<div class="content">{inner_content["content"]}</div>'

            # Put timestamp and status on the same line
            html += '<div class="meta-info">'
            html += f'<span class="timestamp">{timestamp}</span>'

            # Add status indicator for sent messages
            if message['type'] == 'sent':
                html += f'<span class="status {status_class}"></span>'

            html += '</div>'  # Close meta-info div
            html += '</div>'  # Close message div

        html += """
        </body>
        </html>
        """
        return html

    def on_message_send(self, event):
        """Handle message send event"""
        print(f"DEBUG: current_chat_id: {self.current_chat_id}")
        if not self.current_chat_id:
            return

        message_text = event.message
        attachments = event.attachments
        message_json = {}

        # Convert attachments to JSON
        if attachments:
            print("***********8")
            print(attachments)
            with open(attachments[0]["path"], 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            filename = os.path.basename(attachments[0]["path"])
            message_json['type'] = "img"
            print("===here goes image content==")
            print(image_data)
            message_json['content'] = image_data
            #attachments_json = json.dumps(attachments)
            cc=self.db.get_contact(self.current_chat_id)
            #message_json['content'] = self.file_handler.save_sent_image(cc['onion_address'], image_data, filename)
            #self.file_handler.save_sent_image(cc['onion_address'], image_data, filename)
        else:
            message_json['type'] = "txt"
            message_json['content'] = message_text
            #attachments_json = None
        message = json.dumps(message_json)

        if message or attachments:
            # Get contact info for sending
            contact = self.db.get_contact(self.current_chat_id)
            if contact and contact.get('onion_address') and contact.get('public_key'):
                # Generate a unique message ID
                message_id = f"msg_{str(uuid.uuid4())}"
                print(f"DEBUG: Generated message_id: {message_id}")

                # Save to database with initial 'sending' status
                try:
                    # Try to save with status parameter if database supports it
                    msg_id = self.db.add_message(
                        self.current_chat_id,
                        message,
                        'sent',
                        time.time(),
                        'sending',
                        message_id
                    )
                    print(f"DEBUG: Added message to database with id: {msg_id}, message_id: {message_id}")
                except TypeError:
                    # Fall back to old method if database doesn't support status
                    msg_id = self.db.add_message(
                        self.current_chat_id,
                        message,
                        'sent',
                        attachments
                    )
                    print(f"DEBUG: Added message to database with id: {msg_id} (no status)")
                    # Try to update status afterward
                    try:
                        self.db.update_message_status(msg_id, 'sending')
                    except (AttributeError, Exception) as e:
                        print(f"WARNING: Could not update message status: {e}")

                # Update messages display
                self.update_messages()

                # Check if messenger supports asynchronous sending
                if hasattr(self.messenger, 'send_message') and callable(getattr(self.messenger, 'send_message')):
                    # If messenger has async method signature
                    try:
                        # Try with message_id parameter
                        print(f"DEBUG: Sending message with id: {message_id}")
                        self.messenger.send_message(
                            contact['onion_address'],
                            contact['public_key'],
                            message,
                            message_id
                        )
                    except TypeError:
                        # Fall back to original method without message_id
                        print(f"DEBUG: Sending message without message_id")
                        success = self.messenger.send_message(
                            contact['onion_address'],
                            contact['public_key'],
                            message
                        )

                        # Handle synchronous response
                        if not success:
                            wx.MessageBox("Failed to send message. Please try again.",
                                          "Error", wx.OK | wx.ICON_ERROR)
                            try:
                                self.db.update_message_status(msg_id, 'failed')
                                self.update_messages()
                            except:
                                pass
                else:
                    wx.MessageBox("Message sending not available.",
                                  "Error", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("Contact information is incomplete.",
                              "Error", wx.OK | wx.ICON_ERROR)

    def on_message_status_update(self, message_id, new_status):
        """Update message status in UI when callback is received"""
        print(f"DEBUG: Status update received for message {message_id}: {new_status}")

        # Update database if it supports the method
        try:
            updated = self.db.update_message_status(message_id, new_status)
            print(f"DEBUG: Database update {'successful' if updated else 'failed'}")
        except (AttributeError, Exception) as e:
            print(f"WARNING: Could not update message status in database: {e}")

        # Use wx.CallAfter to ensure this runs in the main thread
        wx.CallAfter(self._update_ui_status, message_id, new_status)

    def _update_ui_status(self, message_id, new_status):
        """Update the UI with new status (called in main thread)"""
        print(f"DEBUG: Updating UI for message {message_id} with status {new_status}")

        # First try using JavaScript to update just the one message
        success = False
        try:
            # Create a JavaScript command to update the status
            js_script = f"updateMessageStatus('{message_id}', '{new_status}');"
            print(f"DEBUG: Running JavaScript: {js_script}")

            # Try multiple WebView JavaScript execution methods
            try:
                result = self.messages_view.RunScript(js_script)
                print(f"DEBUG: RunScript result: {result}")
                success = True
            except AttributeError:
                try:
                    result = self.messages_view.ExecuteJavascript(js_script)
                    print(f"DEBUG: ExecuteJavascript result: {result}")
                    success = True
                except Exception as e:
                    print(f"DEBUG: ExecuteJavascript failed: {e}")
                    success = False
        except Exception as e:
            print(f"ERROR updating message status with JavaScript: {e}")
            success = False

        # If JavaScript update fails or we're not sure it worked, refresh the entire view
        if not success:
            print("DEBUG: JavaScript update failed or uncertain, refreshing entire view")
            self.update_messages()