#!/usr/bin/env python3
"""
Quick test to see if pressing Pair button opens the dialog.
Run this and press the Pair button to see logs.
"""

import sys
import asyncio
import logging
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from main import MainWindow

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pair_test.log')
        ]
    )
    
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    print("=" * 50)
    print("PAIR BUTTON TEST")
    print("=" * 50)
    print("1. App window will open")
    print("2. Click the '🔗 Pair' button")
    print("3. Watch console output and pair_test.log")
    print("4. A dialog should appear if working correctly")
    print("=" * 50)
    
    window = MainWindow()
    window.show()
    
    with loop:
        sys.exit(loop.run_forever())