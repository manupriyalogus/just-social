import html
import re
from datetime import datetime


def format_message(message):
    """Format a message for HTML display"""

    # Determine message class based on type
    message_class = 'sent' if message['type'] == 'sent' else 'received'

    # Start message container
    html_content = f'<div class="message {message_class}">'

    # Format text content
    if message['content']:
        content = html.escape(message['content'])
        # Convert URLs to links
        content = convert_urls_to_links(content)
        # Convert emojis
        content = convert_emojis(content)
        html_content += f'<div class="content">{content}</div>'

    # Add attachments if present
    if message.get('attachments'):
        html_content += format_attachments(message['attachments'])

    # Add timestamp
    timestamp = format_timestamp(message['timestamp'])
    html_content += f'<div class="timestamp">{timestamp}</div>'

    # Add status indicators for sent messages
    if message['type'] == 'sent':
        html_content += f'<div class="status">{format_status(message["status"])}</div>'

    # Close message container
    html_content += '</div>'

    return html_content


def convert_urls_to_links(text):
    """Convert URLs in text to clickable links"""
    url_pattern = r'(https?://\S+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)


def convert_emojis(text):
    """Convert emoji shortcodes to actual emojis"""
    # Add more emoji mappings as needed
    emoji_map = {
        ':)': '😊',
        ':(': '😢',
        ':D': '😃',
        ';)': '😉',
        ':P': '😛',
        '<3': '❤️'
    }

    for code, emoji in emoji_map.items():
        text = text.replace(code, emoji)
    return text


def format_attachments(attachments):
    """Format message attachments for display"""
    html_content = '<div class="attachments">'

    for attachment in attachments:
        if attachment['type'] == 'image':
            html_content += f'''
                <img src="file://{attachment['path']}" 
                     class="media" 
                     alt="{attachment['name']}"
                     onclick="window.location='file://{attachment['path']}'"
                />
            '''
        elif attachment['type'] == 'video':
            html_content += f'''
                <video class="media" controls>
                    <source src="file://{attachment['path']}" 
                            type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            '''
        elif attachment['type'] == 'pdf':
            html_content += f'''
                <div class="file-attachment pdf">
                    <img src="pdf-icon.png" class="file-icon" />
                    <span>{attachment['name']}</span>
                </div>
            '''
        else:
            html_content += f'''
                <div class="file-attachment">
                    <img src="file-icon.png" class="file-icon" />
                    <span>{attachment['name']}</span>
                </div>
            '''

    html_content += '</div>'
    return html_content


def format_timestamp(timestamp):
    """Format message timestamp"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    now = datetime.now()

    if timestamp.date() == now.date():
        # Today, show time only
        return timestamp.strftime('%I:%M %p')
    elif timestamp.date().year == now.date().year:
        # This year, show month and day
        return timestamp.strftime('%b %d, %I:%M %p')
    else:
        # Different year, show full date
        return timestamp.strftime('%b %d %Y, %I:%M %p')


def format_status(status):
    """Format message status indicator"""
    status_map = {
        'sent': '✓',
        'delivered': '✓✓',
        'read': '✓✓',  # Use blue color in CSS
        'failed': '❌'
    }

    return status_map.get(status, '')
