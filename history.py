import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

HISTORY_FILE = Path('connection_history.json')

def load_history() -> List[Dict]:
    if not HISTORY_FILE.exists():
        return []
    with open(HISTORY_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_history(history: List[Dict]):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def update_history(device_name: str, ip: str, favorite: bool = False):
    history = load_history()
    now = datetime.now().isoformat()
    # Remove any existing entry for this IP
    history = [entry for entry in history if entry['ip'] != ip]
    # Add new/updated entry at the top
    history.insert(0, {
        'device_name': device_name,
        'ip': ip,
        'last_connected': now,
        'favorite': favorite,
    })
    save_history(history)

def set_favorite(ip: str, favorite: bool):
    history = load_history()
    for entry in history:
        if entry['ip'] == ip:
            entry['favorite'] = favorite
    save_history(history)

def get_favorites() -> List[Dict]:
    return [entry for entry in load_history() if entry.get('favorite')]

def get_history() -> List[Dict]:
    # Favorites first, then others by last_connected
    history = load_history()
    return sorted(history, key=lambda x: (not x.get('favorite', False), -datetime.fromisoformat(x['last_connected']).timestamp()))
