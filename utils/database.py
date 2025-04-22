import sqlite3
import os
import json

import appdirs


class Database:
    def __init__(self):
        self.app_name = "JustSocial"
        self.data_dir = appdirs.user_data_dir(self.app_name)
        self.db_file = os.path.join(self.data_dir, "chat.db")

        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        # Log the database directory
        print(f"Database directory: {self.data_dir}")  # Using f-string for cleaner formatting
        print(f"Database file: {self.db_file}")

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def initialize(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create contacts table with Tor-specific fields
            cursor.execute('''
                       CREATE TABLE IF NOT EXISTS contacts (
                           id TEXT PRIMARY KEY,
                           name TEXT NOT NULL,
                           status TEXT,
                           avatar_path TEXT,
                           last_seen TIMESTAMP,
                           onion_address TEXT,
                           public_key TEXT,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                   ''')

            # Create messages table with status and message_id fields
            cursor.execute('''
                            CREATE TABLE IF NOT EXISTS messages (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                chat_id TEXT NOT NULL,
                                content TEXT,
                                type TEXT NOT NULL,
                                status TEXT DEFAULT 'sent',
                                attachments TEXT,
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                message_id TEXT,
                                group_id TEXT,
                                FOREIGN KEY (chat_id) REFERENCES contacts (id),
                                FOREIGN KEY (group_id) REFERENCES groups (id)
                            )
                        ''')

            # Create chats table
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS chats (
                               id TEXT PRIMARY KEY,
                               contact_id TEXT NOT NULL,
                               last_message_id INTEGER,
                               unread_count INTEGER DEFAULT 0,
                               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               FOREIGN KEY (contact_id) REFERENCES contacts (id),
                               FOREIGN KEY (last_message_id) REFERENCES messages (id)
                           )
                       ''')

            # Create groups table
            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS groups (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT,
                            avatar_path TEXT,
                            created_by TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_message_id INTEGER,
                            FOREIGN KEY (created_by) REFERENCES contacts (id),
                            FOREIGN KEY (last_message_id) REFERENCES messages (id)
                        )
                    ''')

            # Create group_members table for many-to-many relationship
            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS group_members (
                            group_id TEXT NOT NULL,
                            member_id TEXT NOT NULL,
                            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            role TEXT DEFAULT 'member',
                            PRIMARY KEY (group_id, member_id),
                            FOREIGN KEY (group_id) REFERENCES groups (id),
                            FOREIGN KEY (member_id) REFERENCES contacts (id)
                        )
                    ''')

            conn.commit()

    def add_contact(self, contact_id, name, status="", avatar_path=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO contacts (id, name, status, avatar_path)
                VALUES (?, ?, ?, ?)
            ''', (contact_id, name, status, avatar_path))

            # Create or update chat for this contact
            cursor.execute('''
                INSERT OR IGNORE INTO chats (id, contact_id)
                VALUES (?, ?)
            ''', (contact_id, contact_id))

            conn.commit()

    def add_new_contact(self, name,onion_address, public_key, status="ACTIVE", avatar_path=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                 INSERT INTO contacts (id, name, status, onion_address, public_key, avatar_path)
                 VALUES (?, ?, ?, ?, ?, ?)
             ''', (public_key, name, status, onion_address, public_key, avatar_path))

            # # Create or update chat for this contact
            # cursor.execute('''
            #      INSERT OR IGNORE INTO chats (id, contact_id)
            #      VALUES (?, ?)
            #  ''', (uuid.uuid4().hex, contact_id))

            conn.commit()

    def get_contacts(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, COUNT(m.id) as unread
                FROM contacts c
                LEFT JOIN messages m ON c.id = m.chat_id 
                    AND m.status = 'received' 
                    AND m.type = 'unread'
                GROUP BY c.id
                ORDER BY m.timestamp DESC
            ''')

            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_contact(self, contact_id):
        print(f"DEBUG: get_contact from {contact_id}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    def add_message(self, chat_id, content, message_type, timestamp=None, status='sent',
                    message_id=None):
        """Add a message to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:

                # Use current time if no timestamp provided
                if timestamp is None:
                    import time
                    timestamp = time.time()

                # Always include message_id in the initial insertion
                # This is the key fix - we store the UUID when creating the message
                cursor.execute('''
                    INSERT INTO messages (chat_id, content, type, timestamp, status, message_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (chat_id, content, message_type, timestamp, status, message_id))

                message_id_db = cursor.lastrowid

                # Update chat's last message reference
                cursor.execute('''
                    UPDATE chats 
                    SET last_message_id = ?,
                        unread_count = CASE 
                            WHEN ? = 'received' THEN unread_count + 1
                            ELSE unread_count
                        END
                    WHERE contact_id = ?
                ''', (message_id_db, message_type, chat_id))

                conn.commit()
                return message_id_db

            except Exception as e:
                print(f"ERROR in add_message: {e}")
                conn.rollback()
                raise

    def get_chat_messages(self, chat_id, limit=50):
        """Get all messages for a specific contact ordered by timestamp"""
        print(f"DEBUG: Attempting to get chat messages for contact ID: {chat_id}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM messages 
                WHERE chat_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (chat_id, limit))

            columns = [col[0] for col in cursor.description]
            messages = []

            for row in cursor.fetchall():
                message = dict(zip(columns, row))

                # Parse attachments JSON if present
                if message['attachments']:
                    message['attachments'] = json.loads(message['attachments'])
                else:
                    message['attachments'] = []

                messages.append(message)

            return list(reversed(messages))

    def mark_messages_as_read(self, chat_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages 
                SET status = 'read'
                WHERE chat_id = ? AND type = 'received' AND status = 'unread'
            ''', (chat_id,))

            cursor.execute('''
                UPDATE chats
                SET unread_count = 0
                WHERE contact_id = ?
            ''', (chat_id,))

            conn.commit()

    def update_message_status(self, message_id, new_status):
        """Update the status of a message by its message_id or database ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Use different approaches to find the message
                updated = False

                # Extract base message ID if this is an extended group message ID
                base_message_id = message_id
                if isinstance(message_id, str) and message_id.startswith('grp_') and '_' in message_id:
                    # Extract the group message ID part (before the recipient ID)
                    parts = message_id.split('_')
                    base_message_id = f"grp_{parts[1]}"

                # 1. Try with base message ID first
                cursor.execute('''
                    UPDATE messages
                    SET status = ?
                    WHERE message_id = ?
                ''', (new_status, base_message_id))

                if cursor.rowcount > 0:
                    updated = True
                    print(f"DEBUG: Updated message by base message_id: {base_message_id}")

                # 2. If that fails, try with the full extended ID
                if not updated:
                    cursor.execute('''
                        UPDATE messages
                        SET status = ?
                        WHERE message_id = ?
                    ''', (new_status, message_id))

                    if cursor.rowcount > 0:
                        updated = True
                        print(f"DEBUG: Updated message by full message_id: {message_id}")

                # 3. If message_id is an integer, try database ID update
                if not updated and isinstance(message_id, int):
                    cursor.execute('''
                        UPDATE messages
                        SET status = ?
                        WHERE id = ?
                    ''', (new_status, message_id))

                    if cursor.rowcount > 0:
                        updated = True
                        print(f"DEBUG: Updated message by database ID: {message_id}")

                conn.commit()

                # Debug the result
                if updated:
                    print(f"DEBUG: Successfully updated message status to {new_status}")
                    return True
                else:
                    print(f"DEBUG: Failed to update any message with ID {message_id}")
                    return False

            except Exception as e:
                print(f"ERROR in update_message_status: {e}")
                conn.rollback()
                return False

    def get_unread_count(self, chat_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT unread_count FROM chats WHERE contact_id = ?", (chat_id,))
            result = cursor.fetchone()
            return result[0] if result else 0  # Return 0 if no unread count is found

    def create_group(self, group_id, name, description="", created_by=None, avatar_path=""):
        """Create a new group"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO groups (id, name, description, created_by, avatar_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (group_id, name, description, created_by, avatar_path))
            conn.commit()
            return group_id

    def add_group_member(self, group_id, member_id, role="member"):
        """Add a member to a group"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO group_members (group_id, member_id, role)
                VALUES (?, ?, ?)
            ''', (group_id, member_id, role))
            conn.commit()

    def remove_group_member(self, group_id, member_id):
        """Remove a member from a group"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM group_members 
                WHERE group_id = ? AND member_id = ?
            ''', (group_id, member_id))
            conn.commit()

    def get_group(self, group_id):
        """Get group details by id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM groups WHERE id = ?
            ''', (group_id,))
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    def get_groups(self):
        """Get all groups the user is a member of"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.*, COUNT(m.id) as unread
                FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                LEFT JOIN messages m ON g.id = m.group_id 
                    AND m.status = 'received' 
                    AND m.type = 'unread'
                GROUP BY g.id
                ORDER BY m.timestamp DESC
            ''')

            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_group_members(self, group_id):
        """Get all members of a group"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, gm.role
                FROM contacts c
                JOIN group_members gm ON c.id = gm.member_id
                WHERE gm.group_id = ?
            ''', (group_id,))

            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_group_message(self, group_id, sender_id, content, message_type,
                          attachments=None, timestamp=None, status='sent', message_id=None):
        """Add a message to a group chat"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Convert attachments to JSON
                if attachments:
                    import json
                    attachments_json = json.dumps(attachments)
                else:
                    attachments_json = None

                # Use current time if no timestamp provided
                if timestamp is None:
                    import time
                    timestamp = time.time()

                # Insert group message - make sure group_id is included
                cursor.execute('''
                    INSERT INTO messages (chat_id, content, type, attachments, timestamp, status, message_id, group_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sender_id, content, message_type, attachments_json, timestamp, status, message_id, group_id))

                message_id_db = cursor.lastrowid

                # Update group's last message reference
                cursor.execute('''
                    UPDATE groups
                    SET last_message_id = ?
                    WHERE id = ?
                ''', (message_id_db, group_id))

                conn.commit()
                return message_id_db

            except Exception as e:
                print(f"ERROR in add_group_message: {e}")
                conn.rollback()
                raise

    def get_group_messages(self, group_id, limit=50):
        """Get messages for a specific group ordered by timestamp"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            print(f"DEBUG: Fetching group messages for group ID: {group_id}")

            cursor.execute('''
                SELECT m.*, c.name as sender_name
                FROM messages m
                JOIN contacts c ON m.chat_id = c.id
                WHERE m.group_id = ?
                ORDER BY m.timestamp ASC
                LIMIT ?
            ''', (group_id, limit))

            columns = [col[0] for col in cursor.description]
            messages = []

            for row in cursor.fetchall():
                message = dict(zip(columns, row))

                # Parse attachments JSON if present
                if message['attachments']:
                    message['attachments'] = json.loads(message['attachments'])
                else:
                    message['attachments'] = []

                messages.append(message)

            print(f"DEBUG: Found {len(messages)} messages for group ID: {group_id}")
            return messages
