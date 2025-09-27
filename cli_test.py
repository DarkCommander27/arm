#!/usr/bin/env python3
"""
Command-line interface for testing Android TV Remote Control functionality.
This allows testing the core features without GUI.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '/workspaces/arm')

from remote_control import RemoteControl
import history

class CLIRemote:
    def __init__(self):
        self.remote_control = RemoteControl()
        self.is_connected = False
        
        # Ensure keys directory exists
        Path('keys').mkdir(parents=True, exist_ok=True)
    
    async def discover_devices(self):
        """Discover Android TV devices on the network."""
        print("🔍 Scanning for Android TV devices...")
        addresses = await self.remote_control.find_android_tv()
        
        if addresses:
            print(f"✓ Found {len(addresses)} device(s):")
            for i, addr in enumerate(addresses, 1):
                print(f"  {i}. {addr}")
            return addresses
        else:
            print("❌ No Android TV devices found on the network")
            return []
    
    def show_history(self):
        """Display connection history and favorites."""
        hist = history.get_history()
        favorites = history.get_favorites()
        
        print("\n📱 Device History:")
        if not hist:
            print("  No devices in history")
        else:
            print("\n⭐ Favorites:")
            if favorites:
                for i, entry in enumerate(favorites, 1):
                    print(f"  {i}. {entry['device_name']} ({entry['ip']})")
            else:
                print("  No favorite devices")
            
            print("\n📋 All History:")
            for i, entry in enumerate(hist, 1):
                fav = "⭐" if entry.get('favorite') else "  "
                print(f"  {fav} {i}. {entry['device_name']} ({entry['ip']}) - {entry['last_connected']}")
    
    def add_test_device(self):
        """Add a test device to history for demonstration."""
        test_devices = [
            ("Living Room TV", "192.168.1.100"),
            ("Bedroom TV", "192.168.1.101"),
            ("Kitchen TV", "192.168.1.102")
        ]
        
        print("\n🔧 Adding test devices to history...")
        for name, ip in test_devices:
            history.update_history(name, ip, False)
        
        # Make one a favorite
        history.set_favorite("192.168.1.100", True)
        print("✓ Added 3 test devices (Living Room TV marked as favorite)")
    
    def toggle_favorite(self):
        """Toggle favorite status of a device."""
        hist = history.get_history()
        if not hist:
            print("❌ No devices in history")
            return
        
        print("\n📱 Select device to toggle favorite:")
        for i, entry in enumerate(hist, 1):
            fav = "⭐" if entry.get('favorite') else "  "
            print(f"  {fav} {i}. {entry['device_name']} ({entry['ip']})")
        
        try:
            choice = int(input("\nEnter device number: ")) - 1
            if 0 <= choice < len(hist):
                entry = hist[choice]
                new_fav = not entry.get('favorite', False)
                history.set_favorite(entry['ip'], new_fav)
                status = "added to" if new_fav else "removed from"
                print(f"✓ {entry['device_name']} {status} favorites")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    async def simulate_connection(self):
        """Simulate connecting to a device."""
        hist = history.get_history()
        if not hist:
            print("❌ No devices in history to connect to")
            return
        
        print("\n📱 Select device to simulate connection:")
        for i, entry in enumerate(hist, 1):
            fav = "⭐" if entry.get('favorite') else "  "
            print(f"  {fav} {i}. {entry['device_name']} ({entry['ip']})")
        
        try:
            choice = int(input("\nEnter device number: ")) - 1
            if 0 <= choice < len(hist):
                entry = hist[choice]
                print(f"🔗 Simulating connection to {entry['device_name']} ({entry['ip']})...")
                
                # Update last connected time
                history.update_history(entry['device_name'], entry['ip'], entry.get('favorite', False))
                
                print("✓ Connection simulation complete!")
                self.is_connected = True
                return entry
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
        
        return None
    
    def show_remote_controls(self):
        """Show available remote control commands."""
        if not self.is_connected:
            print("❌ Not connected to any device. Please simulate a connection first.")
            return
        
        commands = [
            ("Power", "POWER"),
            ("Home", "HOME"), 
            ("Back", "BACK"),
            ("Menu", "MENU"),
            ("Volume Up", "VOLUME_UP"),
            ("Volume Down", "VOLUME_DOWN"),
            ("Mute", "VOLUME_MUTE"),
            ("Channel Up", "CHANNEL_UP"),
            ("Channel Down", "CHANNEL_DOWN"),
            ("D-Pad Up", "DPAD_UP"),
            ("D-Pad Down", "DPAD_DOWN"),
            ("D-Pad Left", "DPAD_LEFT"),
            ("D-Pad Right", "DPAD_RIGHT"),
            ("D-Pad Center/OK", "DPAD_CENTER")
        ]
        
        print("\n🎮 Available Remote Commands:")
        for i, (name, cmd) in enumerate(commands, 1):
            print(f"  {i:2}. {name}")
        
        print("\nNote: In a real connection, these would send commands to the TV.")
    
    async def main_menu(self):
        """Main interactive menu."""
        while True:
            print("\n" + "="*50)
            print("📺 Android TV Remote Control - CLI Test Mode")
            print("="*50)
            print(f"Connection Status: {'🟢 Connected' if self.is_connected else '🔴 Disconnected'}")
            print("\nOptions:")
            print("1. 🔍 Discover Android TV devices")
            print("2. 📱 Show device history & favorites")
            print("3. 🔧 Add test devices to history")
            print("4. ⭐ Toggle device favorite status")
            print("5. 🔗 Simulate connection to device")
            print("6. 🎮 Show remote control commands")
            print("7. 🚪 Exit")
            
            try:
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if choice == '1':
                    await self.discover_devices()
                elif choice == '2':
                    self.show_history()
                elif choice == '3':
                    self.add_test_device()
                elif choice == '4':
                    self.toggle_favorite()
                elif choice == '5':
                    await self.simulate_connection()
                elif choice == '6':
                    self.show_remote_controls()
                elif choice == '7':
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-7.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")

async def main():
    """Entry point for the CLI test interface."""
    cli = CLIRemote()
    await cli.main_menu()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")