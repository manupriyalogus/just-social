import wx
import json
import threading
import websocket
import time

# Custom event for message receiving
wxEVT_MESSAGE_RECEIVED = wx.NewEventType()
EVT_MESSAGE_RECEIVED = wx.PyEventBinder(wxEVT_MESSAGE_RECEIVED, 1)


class MessageReceivedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, message):
        super().__init__(etype, eid)
        self.message = message


class WebSocketClient(wx.EvtHandler):
    def __init__(self, user_id, server_url="ws://localhost:8765"):
        super().__init__()
        self.user_id = user_id
        self.server_url = server_url
        self.ws = None
        self.connected = False
        self.reconnect_thread = None
        self.connect()

    def connect(self):
        """Initialize WebSocket connection"""

        def on_message(ws, message):
            """Handle incoming messages"""
            try:
                data = json.loads(message)
                # Post event to main thread
                evt = MessageReceivedEvent(wxEVT_MESSAGE_RECEIVED, -1, data)
                wx.PostEvent(self, evt)
            except json.JSONDecodeError:
                print(f"Invalid message format: {message}")

        def on_error(ws, error):
            """Handle connection errors"""
            print(f"WebSocket error: {error}")
            self.connected = False
            self.start_reconnect_thread()

        def on_close(ws, close_status_code, close_msg):
            """Handle connection closure"""
            print("WebSocket connection closed")
            self.connected = False
            self.start_reconnect_thread()

        def on_open(ws):
            """Handle successful connection"""
            print("WebSocket connection established")
            self.connected = True
            # Send authentication message
            self.ws.send(json.dumps({
                'type': 'auth',
                'user_id': self.user_id
            }))

        # Initialize WebSocket with callbacks
        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        # Start WebSocket connection in a separate thread
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()

    def start_reconnect_thread(self):
        """Start a thread to handle reconnection"""
        if self.reconnect_thread is None or not self.reconnect_thread.is_alive():
            self.reconnect_thread = threading.Thread(target=self.reconnect)
            self.reconnect_thread.daemon = True
            self.reconnect_thread.start()

    def reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        wait_time = 1
        max_wait_time = 60

        while not self.connected:
            print(f"Attempting to reconnect in {wait_time} seconds...")
            time.sleep(wait_time)

            try:
                self.connect()
                if self.connected:
                    print("Reconnection successful")
                    break
            except Exception as e:
                print(f"Reconnection failed: {e}")

            # Increase wait time exponentially
            wait_time = min(wait_time * 2, max_wait_time)

    def send_message(self, message):
        """Send a message through the WebSocket connection"""
        if not self.connected:
            print("Not connected. Message will be queued.")
            return False

        try:
            self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def close(self):
        """Close the WebSocket connection"""
        if self.ws:
            self.ws.close()
