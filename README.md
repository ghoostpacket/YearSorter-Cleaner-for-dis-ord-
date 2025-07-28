# Discord Token Utility Suite

> A dual-purpose Python toolkit for managing Discord tokens:  
> • **Token Sorter**: 100% offline — decodes and organizes tokens by account creation year.  
> • **Account Cleaner**: Uses the Discord API to remove friends, messages, groups, and leave all servers.

---

## 📦 Features

### 🗂️ Token Sorter (Offline)
- Works entirely offline — no Discord API required
- Decodes tokens to extract account creation timestamp
- Sorts tokens into `output/YYYY.txt` based on creation year
- Logs malformed lines to `nopassword.txt`

### 🧹 Account Cleaner (Online)
- Validates and categorizes tokens: cleaned, locked, invalid, or failed
- Deletes:
  - Friends
  - Messages
  - Group DMs
  - Leaves joined servers
- Uses Discord’s REST API and WebSocket gateway
- Live stats in console title and output logs
- Supports proxies and multi-threading (up to 100 threads)

---

## ⚙️ Installation

```
pip install tls-client websocket-client colorama
```
🚀 Usage
▶️ Token Sorter
bash
Tokens will be organized into output/YYYY.txt files

▶️ Account Cleaner

python cleaner.py
You’ll be asked to enter a thread count (recommended: 5–50).

⚠️ Disclaimer
This tool is for educational and personal use only.
Do not use it to violate Discord’s Terms of Service.
The author assumes no responsibility for misuse.
