#!/usr/bin/env python3
"""
Fix Unicode Characters in Automation Scripts
Replaces problematic Unicode emoji/symbols with ASCII text for Windows compatibility
"""

import re
import os

def fix_unicode_in_file(filepath):
    """Replace Unicode characters with ASCII equivalents"""
    print(f"Fixing Unicode in: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define replacements
    replacements = {
        '🤖': '[BOT]',
        '❌': '[ERROR]',
        '✅': '[SUCCESS]',
        '⚠️': '[WARNING]',
        '🔧': '[FIX]',
        '📋': '[REPORT]',
        '🚀': '[DEPLOY]',
        '🛠️': '[REPAIR]',
        '🎯': '[TARGET]',
        '⏱️': '[TIME]',
        '🔄': '[LOOP]',
        '📊': '[STATS]',
        '🔍': '[CHECK]',
        '→': '->',
        '🧪': '[TEST]',
        '🕐': '[CLOCK]',
        '🔗': '[LINK]',
        '⏰': '[TIMER]',
        '💬': '[MSG]',
        '📱': '[PHONE]',
        '🔑': '[KEY]',
        '🌐': '[WEB]',
        '⭐': '[STAR]',
        '📝': '[NOTE]',
        '🔔': '[BELL]',
        '📄': '[DOC]',
        '🔒': '[LOCK]',
        '🎨': '[DESIGN]',
        '🚨': '[ALERT]',
        '✨': '[SPARK]',
        '🏆': '[TROPHY]',
        '📈': '[CHART]',
        '🔥': '[FIRE]',
        '💻': '[COMPUTER]',
        '🎪': '[CIRCUS]',
        '🎭': '[THEATER]',
        '🎹': '[MUSIC]',
        '🎨': '[ART]',
        '🔬': '[SCIENCE]',
        '🧬': '[DNA]',
        '⚡': '[LIGHTNING]',
        '🌟': '[STAR]',
        '🏁': '[FLAG]',
        '🎉': '[CELEBRATION]',
        '🎊': '[CONFETTI]',
        '🏃': '[RUNNING]',
        '🚶': '[WALKING]',
        '🎲': '[DICE]',
        '🎮': '[GAME]',
        '🎯': '[DART]',
        '🎳': '[BOWLING]',
        '⚽': '[SOCCER]',
        '🏀': '[BASKETBALL]',
        '🏈': '[FOOTBALL]',
        '🎾': '[TENNIS]',
        '🏐': '[VOLLEYBALL]',
        '🏓': '[PING_PONG]',
        '🥅': '[GOAL]',
        '🏋️': '[WEIGHT]',
        '🤸': '[CARTWHEEL]',
        '🧘': '[MEDITATION]',
        '🛡️': '[SHIELD]',
        '⚔️': '[SWORDS]',
        '🔪': '[KNIFE]',
        '💊': '[PILL]',
        '💉': '[SYRINGE]',
        '🩹': '[BANDAGE]',
        '🩺': '[STETHOSCOPE]',
        '🔬': '[MICROSCOPE]',
        '🧪': '[TEST_TUBE]',
        '🧬': '[DNA_HELIX]',
        '🦠': '[MICROBE]',
        '💀': '[SKULL]',
        '☠️': '[SKULL_BONES]',
        '🤢': '[NAUSEA]',
        '🤮': '[VOMIT]',
        '🤧': '[SNEEZE]',
        '🤒': '[FEVER]',
        '🤕': '[BANDAGED]',
        '🤴': '[PRINCE]',
        '👑': '[CROWN]',
        '🎩': '[TOP_HAT]',
        '🧢': '[CAP]',
        '👒': '[HAT]',
        '🎓': '[GRADUATION]',
        '⛑️': '[HELMET]',
        '📿': '[PRAYER_BEADS]',
        '💄': '[LIPSTICK]',
        '💍': '[RING]',
        '💎': '[DIAMOND]',
        '\u274c': '[X]',
        '\u2705': '[CHECK]',
        '\u26a0': '[WARNING]',
        '\U0001f916': '[ROBOT]',
        '\U0001f6a7': '[CONSTRUCTION]',
        '\U0001f504': '[ARROWS]'
    }
    
    # Apply replacements
    for unicode_char, ascii_replacement in replacements.items():
        content = content.replace(unicode_char, ascii_replacement)
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed Unicode in: {filepath}")

def main():
    """Fix Unicode in all automation files"""
    files_to_fix = [
        'tests/auto_fix_retest_loop.py',
        'tests/comprehensive_multi_event_automation.py',
        'tests/run_master_automation.py'
    ]
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            fix_unicode_in_file(filepath)
        else:
            print(f"File not found: {filepath}")
    
    print("All Unicode fixes applied!")

if __name__ == "__main__":
    main()
