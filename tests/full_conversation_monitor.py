#!/usr/bin/env python3
"""
FULL CALIBOT CONVERSATION MONITOR
Sends user queries, streams live logs from Render, and captures full session
"""

import requests
import time
import json
from datetime import datetime, timedelta
import threading
import os

# Configuration - SAVED FOR AUTOMATIC USE
BOT_TOKEN = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
GROUP_CHAT_ID = -4627994150
RENDER_API_KEY = "rnd_VYOGhxRGLVFUQJWNm8FgtKZXPJFz"  # From previous sessions
SERVICE_ID = "srv-ct0fqlq3esus73clk930"  # CaliBOT service ID
DELAY_BETWEEN_MESSAGES = 8  # 8 seconds to allow processing
LOG_CHECK_INTERVAL = 2  # Check logs every 2 seconds

class FullConversationMonitor:
    def __init__(self, bot_token: str, chat_id: int):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/full_conversation_{self.session_id}.log"
        self.monitoring = False
        
        # Initialize log file
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"CALIBOT FULL CONVERSATION MONITOR - SESSION {self.session_id}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n\n")
    
    def log_event(self, message: str):
        """Log event to file and console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
    
    def send_user_message(self, message: str, user_name: str = "TestUser") -> bool:
        """Send a message as a simulated user"""
        payload = {
            "chat_id": self.chat_id,
            "text": f"👤 <b>{user_name}:</b> {message}",
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            if response.status_code == 200:
                self.log_event(f"✅ USER MESSAGE SENT ({user_name}): {message}")
                return True
            else:
                self.log_event(f"❌ FAILED TO SEND USER MESSAGE: {response.text}")
                return False
        except Exception as e:
            self.log_event(f"❌ ERROR SENDING MESSAGE: {e}")
            return False
    
    def stream_render_logs(self):
        """Stream live logs from Render API"""
        if not RENDER_API_KEY or not SERVICE_ID:
            self.log_event("⚠️ RENDER API credentials not available - skipping log streaming")
            return
        
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
        
        try:
            # Get recent logs
            url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"
            response = requests.get(url, headers=headers, params={"limit": 50})
            
            if response.status_code == 200:
                logs = response.json()
                self.log_event(f"📊 FETCHED {len(logs)} LOG ENTRIES FROM RENDER")
                
                for log_entry in logs[-10:]:  # Last 10 entries
                    timestamp = log_entry.get('timestamp', 'unknown')
                    message = log_entry.get('message', '').strip()
                    if message:
                        self.log_event(f"🔍 RENDER LOG: {message}")
            else:
                self.log_event(f"❌ FAILED TO FETCH RENDER LOGS: {response.status_code}")
                
        except Exception as e:
            self.log_event(f"❌ ERROR STREAMING LOGS: {e}")
    
    def monitor_conversation_response(self, expected_trigger: str):
        """Monitor for CaliBOT response after trigger"""
        self.log_event(f"👀 MONITORING for CaliBOT response to: {expected_trigger}")
        
        # Check logs immediately
        self.stream_render_logs()
        
        # Wait and check again
        for i in range(3):
            time.sleep(3)
            self.log_event(f"⏱️ WAITING... ({i+1}/3) for CaliBOT response")
            self.stream_render_logs()
    
    def run_monitored_conversation(self):
        """Run conversation with full monitoring"""
        self.log_event("🚀 STARTING FULL MONITORED CONVERSATION")
        self.log_event("=" * 60)
        
        # Get initial system state
        self.log_event("📊 CHECKING INITIAL SYSTEM STATE")
        self.stream_render_logs()
        
        scenarios = [
            ("Alice", "Create a meeting tomorrow at 2 PM", "Simple event creation"),
            ("Bob", "Schedule a team standup every Monday at 9 AM", "Recurring event"),
            ("Carol", "What meetings do I have this week?", "Event listing"),
            ("Dave", "Cancel my meeting tomorrow", "Event deletion"),
            ("Eve", "Delete all meetings on Friday", "Multi-event deletion"),
            ("Frank", "Move my 2 PM meeting to 3 PM", "Event modification"),
            ("Grace", "Schedule something important", "Unclear request handling"),
            ("Henry", "Create a doctor appointment next Monday at 10 AM", "Calendar selection"),
        ]
        
        for i, (user, message, description) in enumerate(scenarios, 1):
            self.log_event(f"\n🎬 SCENARIO {i}/8: {description}")
            self.log_event("-" * 50)
            
            # Send user message
            success = self.send_user_message(message, user)
            if not success:
                self.log_event("❌ SKIPPING SCENARIO due to send failure")
                continue
            
            # Monitor for response
            self.monitor_conversation_response(message)
            
            # Longer pause between scenarios
            self.log_event(f"⏸️ PAUSING {DELAY_BETWEEN_MESSAGES} seconds before next scenario")
            time.sleep(DELAY_BETWEEN_MESSAGES)
        
        # Final system check
        self.log_event("\n🔍 FINAL SYSTEM STATE CHECK")
        self.log_event("-" * 40)
        self.stream_render_logs()
        
        self.log_event("\n🎉 MONITORED CONVERSATION COMPLETED!")
        self.log_event(f"📄 Full log saved to: {self.log_file}")
        
    def create_summary_report(self):
        """Create a summary analysis of the session"""
        summary_file = f"logs/conversation_summary_{self.session_id}.json"
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": 8,
            "log_file": self.log_file,
            "configuration": {
                "bot_token": f"{self.bot_token[:15]}...",
                "group_chat_id": self.chat_id,
                "delay_between_messages": DELAY_BETWEEN_MESSAGES,
                "log_check_interval": LOG_CHECK_INTERVAL
            },
            "monitoring_results": "See full log file for detailed analysis"
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log_event(f"📊 SUMMARY REPORT: {summary_file}")

def main():
    """Main execution"""
    try:
        monitor = FullConversationMonitor(BOT_TOKEN, GROUP_CHAT_ID)
        monitor.run_monitored_conversation()
        monitor.create_summary_report()
        
        print(f"\n📁 SESSION FILES CREATED:")
        print(f"  📄 Full log: {monitor.log_file}")
        print(f"  📊 Summary: logs/conversation_summary_{monitor.session_id}.json")
        
    except Exception as e:
        print(f"❌ Monitor failed: {e}")

if __name__ == "__main__":
    main()
