# Just Social: A Secure Cross-Platform Messaging Application Using Tor protocol.

Just Social is a private, secure messaging application that uses the Tor network to enable anonymous communication. This README provides instructions for setting up and running Just Social on different operating systems.

## Features

- End-to-end encrypted messaging
- Tor-based anonymous communication
- Group chat functionality with automatic synchronization
- Local message storage with SQLite database
- File attachments and image sharing
- Cross-platform support

## Requirements

- Python 3.7 or higher
- Tor service installed on your system
- wxPython for the GUI
- Additional Python packages: stem, cryptography, requests, flask

## Installation

### Step 1: Install Tor

#### Windows
1. Download the Tor Browser from the [official website](https://www.torproject.org/download/).
2. Install and run it once to ensure Tor is working properly.
3. You can close the browser afterward, but make sure the Tor service continues running in the background.

#### macOS
1. Install Tor using Homebrew:
2. Alternatively, you can download the Tor Browser from the [official website](https://www.torproject.org/download/).

#### Linux (Debian/Ubuntu)
```
sudo apt update
sudo apt install tor
```
#### Linux (Fedora/RHEL)
```
sudo dnf install tor
```
### Step 2: Install Python Dependencies
```
pip install wxPython stem cryptography requests flask pynacl
```
### Step 3: Clone or Download the Application
```
cd just-social
```
## Running the Application
### Windows
1. Make sure Tor is running in the background.
2. Open a command prompt in the application directory.
3. Run:
```
python main.py
```
### macOS
1. Start the Tor service:
```
brew services start tor
```
Or if you're using the Tor Browser, make sure it's running.
2. Run the application:
```
python main.py
```

### Linux
1. Start the Tor service:
```
sudo systemctl start tor
```
2. Run the application:
```
python main.py
```


## Troubleshooting
### Tor Connection Issues
If you encounter Tor connection errors:

1. Verify Tor is running:
````
# Windows
tasklist | findstr tor

# macOS/Linux
ps aux | grep tor
````

2. Make sure the SOCKS port (default: 9050) is not blocked by a firewall.
3. If you're still having issues, try editing the configuration in tor_service.py to use an existing Tor instance:
```
# Modify the tor_config to use an existing Tor instance
tor_config = {
    'SocksPort': str(self.socks_port),
    'ControlPort': '9051',
    # Use an existing data directory
    'DataDirectory': '/path/to/existing/tor/data',
    'HiddenServiceDir': self.hidden_service_dir,
    'HiddenServicePort': f'{self.hidden_service_port} 127.0.0.1:{self.hidden_service_port}'
}
````

### Permission Issues
On macOS and Linux, ensure the hidden service directory has the correct permissions:
````
bashchmod 700 ~/.tor
chmod 700 ~/.tor/hidden_service
````
### Group Chat Issues
If group chat synchronization is not working:
1. Make sure all members are using the same version of the application.
2. Verify that all members have proper network connectivity.
3. Check the logs for any specific error messages.

## Usage Tips
### Creating Groups
1. Click on the "+" button in the top bar.
2. Select "Create Group" from the menu.
3. Add a group name, description, and select members.
4. Click "Create" to create the group and send invitations.

### Sending Messages
1. Select a contact or group from the sidebar.
2. Type your message in the input field at the bottom.
3. Click "Send" or press Enter to send the message.

### Sharing Files
1. Click the attachment icon (📎) in the message input area.
2. Select the file you want to share.
3. Click "Send" to share the file.

## Security Considerations

Just Social uses Tor and end-to-end encryption to protect your privacy.
Messages are stored locally on your device and are not saved on any central server.
Your connection information should be shared securely with your contacts.
Avoid sharing personally identifiable information in your messages.