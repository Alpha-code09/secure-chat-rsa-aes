# client_pyqt.py
import sqlite3
from datetime import datetime

import sys
import os
import base64
import threading
import time
import json
from functools import partial
import requests
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
)
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

API_BASE = "http://127.0.0.1:8000"  # backend

KEYS_DIR = os.path.expanduser("~/.secure_chat_keys")
HISTORY_DIR = os.path.expanduser("~/.secure_chat_history")
if not os.path.exists(KEYS_DIR):
    os.makedirs(KEYS_DIR, exist_ok=True)
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR, exist_ok=True)

def save_private_key(username: str, private_key):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    path = os.path.join(KEYS_DIR, f"{username}_priv.pem")
    with open(path, "wb") as f:
        f.write(pem)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    return path

def load_private_key(username: str):
    path = os.path.join(KEYS_DIR, f"{username}_priv.pem")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        pem = f.read()
    return serialization.load_pem_private_key(pem, password=None)

def export_public_der_b64(pubkey):
    der = pubkey.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(der).decode()

class SecureChatClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Chat — PyQt5 (RSA+AES)")
        self.resize(900, 600)

        self.username = None
        self.private_key = None
        self.public_key_b64 = None
        self.current_peer = None

        self.history_path = None

        self._build_ui()

        # Polling timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.poll_inbox)
        self.timer.start(2000)  # every 2s

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # Left sidebar (users + register)
        left = QVBoxLayout()
        left.addWidget(QLabel("Your username:"))
        self.username_input = QLineEdit()
        left.addWidget(self.username_input)
        self.register_btn = QPushButton("Generate Keys & Register")
        self.register_btn.clicked.connect(self.on_register)
        left.addWidget(self.register_btn)

        left.addSpacing(10)
        left.addWidget(QLabel("Users:"))
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.on_user_selected)
        left.addWidget(self.user_list)
        self.refresh_btn = QPushButton("Refresh Users")
        self.refresh_btn.clicked.connect(self.load_users)
        left.addWidget(self.refresh_btn)

        main_layout.addLayout(left, 1)

        # Right area (chat)
        right_layout = QVBoxLayout()
        self.chat_header = QLabel("No chat open")
        right_layout.addWidget(self.chat_header)
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        right_layout.addWidget(self.chat_area, 8)

        send_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        send_layout.addWidget(self.msg_input, 5)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)
        send_layout.addWidget(self.send_btn, 1)

        right_layout.addLayout(send_layout)
        main_layout.addLayout(right_layout, 3)

        # status
        self.status_label = QLabel("")
        right_layout.addWidget(self.status_label)

    def set_status(self, text):
        self.status_label.setText(text)

    # ---------- History DB helpers ----------
    def init_history_db(self):
        # history path depends on username
        self.history_path = os.path.expanduser(os.path.join(HISTORY_DIR, f"{self.username}.db"))
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        conn = sqlite3.connect(self.history_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS history (
                peer TEXT,
                sender TEXT,
                message TEXT,
                timestamp INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def save_history(self, peer, sender, message, ts=None):
        if not self.history_path:
            return
        if ts is None:
            ts = int(time.time())
        conn = sqlite3.connect(self.history_path)
        c = conn.cursor()
        c.execute("INSERT INTO history (peer, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                  (peer, sender, message, ts))
        conn.commit()
        conn.close()

    def load_history(self, peer):
        if not self.history_path:
            return
        conn = sqlite3.connect(self.history_path)
        c = conn.cursor()
        c.execute("SELECT sender, message, timestamp FROM history WHERE peer = ? ORDER BY timestamp ASC", (peer,))
        rows = c.fetchall()
        conn.close()

        for sender, message, ts in rows:
            time_str = datetime.fromtimestamp(ts).strftime("%I:%M %p")
            if sender == self.username:
                display_sender = "You"
            else:
                display_sender = sender
            self.chat_area.append(f"[{time_str}] {display_sender}: {message}")
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        sb = self.chat_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ---------- Registration ----------
    def on_register(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", "Enter a username first")
            return
        # generate RSA keypair
        self.set_status("Generating RSA keypair (this may take a moment)...")
        QtWidgets.QApplication.processEvents()
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        pub_b64 = export_public_der_b64(public_key)
        try:
            resp = requests.post(f"{API_BASE}/register", json={
                "username": username,
                "public_key_spki_b64": pub_b64
            }, timeout=5)
            if resp.status_code not in (200, 201):
                QMessageBox.critical(self, "Register failed", f"Server returned: {resp.status_code} {resp.text}")
                self.set_status("")
                return
        except Exception as e:
            QMessageBox.critical(self, "Register failed", f"HTTP error: {e}")
            self.set_status("")
            return

        # save locally
        save_private_key(username, private_key)
        self.username = username
        self.private_key = private_key
        self.public_key_b64 = pub_b64
        # init history DB now that username exists
        self.init_history_db()
        self.set_status(f"Registered as {username}")
        self.load_users()

    # ---------- User list ----------
    def load_users(self):
        try:
            res = requests.get(f"{API_BASE}/users", timeout=5)
            users = res.json()
        except Exception as e:
            self.set_status(f"Error fetching users: {e}")
            return
        self.user_list.clear()
        for u in users:
            if u == self.username:
                continue
            self.user_list.addItem(u)
        self.set_status("User list updated")

    # ---------- Chat actions ----------
    def on_user_selected(self, item):
        peer = item.text()
        self.current_peer = peer
        self.chat_header.setText(f"Chat with: {peer}")
        self.chat_area.clear()
        # load history for this peer
        self.load_history(peer)
        # optionally fetch messages immediately
        self.poll_inbox_once()

    def on_send(self):
        if not self.username or not self.private_key:
            QMessageBox.warning(self, "Not registered", "Register yourself before sending messages.")
            return
        if not self.current_peer:
            QMessageBox.warning(self, "No peer", "Select a user to chat with.")
            return
        text = self.msg_input.text().strip()
        if not text:
            return

        try:
            r = requests.get(f"{API_BASE}/public-key/{self.current_peer}", timeout=5)
            if r.status_code != 200:
                QMessageBox.critical(self, "Error", f"Could not fetch public key for {self.current_peer}")
                return
            data = r.json()
            recipient_pub_b64 = data["public_key_spki_b64"]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"HTTP error: {e}")
            return

        # encrypt with AES-GCM and wrap key with recipient RSA
        aes_key = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(aes_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, text.encode("utf-8"), None)  # includes tag
        # load recipient public key
        recipient_pub_der = base64.b64decode(recipient_pub_b64)
        recipient_pub = serialization.load_der_public_key(recipient_pub_der)

        enc_key = recipient_pub.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

        payload = {
            "from_user": self.username,
            "to_user": self.current_peer,
            "enc_key": base64.b64encode(enc_key).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "timestamp": int(time.time())
        }

        try:
            r2 = requests.post(f"{API_BASE}/send", json=payload, timeout=5)
            if r2.status_code == 200:
                ts = datetime.now().strftime("%I:%M %p")
                self.chat_area.append(f"[{ts}] You: {text}")
                self.scroll_to_bottom()
                # save to local history
                self.save_history(self.current_peer, self.username, text)
                self.msg_input.clear()
            else:
                QMessageBox.critical(self, "Send failed", f"Server returned: {r2.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Send failed", f"HTTP error: {e}")

    # ---------- Polling ----------
    def poll_inbox(self):
        # non-blocking wrapper around poll_inbox_once()
        threading.Thread(target=self.poll_inbox_once, daemon=True).start()

    def poll_inbox_once(self):
        if not self.username:
            return
        try:
            r = requests.get(f"{API_BASE}/fetch/{self.username}", timeout=5)
            if r.status_code != 200:
                return
            data = r.json()
            messages = data.get("messages", [])
            if not messages:
                return
            for m in messages:
                try:
                    pt = self.decrypt_message_blob(m)
                    # send "sender||message" to UI thread for consistent handling
                    payload = f"{m['from_user']}||{pt}"
                    QtCore.QMetaObject.invokeMethod(self, "append_chat_text", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(str, payload))
                except Exception as e:
                    print("Decrypt error", e)
        except Exception:
            pass

    # ---------- UI slot ----------
    @QtCore.pyqtSlot(str)
    def append_chat_text(self, text):
        """
        text is expected in form "sender||message" when called from poll_inbox.
        For other uses, raw text will be appended.
        """
        # If formatted payload, parse it
        if "||" in text:
            sender, msg = text.split("||", 1)
            ts = datetime.now().strftime("%I:%M %p")
            display_sender = sender if sender != self.username else "You"
            self.chat_area.append(f"[{ts}] {display_sender}: {msg}")
            self.scroll_to_bottom()
            # Save incoming message to history
            if sender != self.username and self.history_path:
                # peer is sender
                self.save_history(sender, sender, msg)
        else:
            # fallback: append raw
            ts = datetime.now().strftime("%I:%M %p")
            self.chat_area.append(f"[{ts}] {text}")
            self.scroll_to_bottom()

    # ---------- Decrypt helper ----------
    def decrypt_message_blob(self, m):
        enc_key_b64 = m["enc_key"]
        nonce_b64 = m["nonce"]
        ciphertext_b64 = m["ciphertext"]

        enc_key = base64.b64decode(enc_key_b64)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)

        aes_key = self.private_key.decrypt(
            enc_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

        aesgcm = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")

def main():
    app = QApplication(sys.argv)
    win = SecureChatClient()
    win.show()

    # Try to auto-load current user keys if present
    # (not intrusive) - if you have a key file, we could load it automatically here
    win.load_users()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
