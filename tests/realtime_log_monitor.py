#!/usr/bin/env python3
"""
Real-Time Log Monitor - Streams logs while testing Calibot
"""

import asyncio
import subprocess
import time
from datetime import datetime

class RealTimeLogMonitor:
    def __init__(self):
        self.monitoring = False
        
    async def start_monitoring(self):
        """Start monitoring logs in background."""
        self.monitoring = True
        
        print("🔄 Starting real-time log monitoring...")
        print("=" * 50)
        
        while self.monitoring:
            try:
                # Run the quick logs script
                result = subprocess.run(
                    ["python", "quick_logs.py"], 
                    capture_output=True, 
                    text=True, 
                    cwd="../scripts"
                )
                
                if result.returncode == 0:
                    # Filter for recent entries (last 5 minutes)
                    current_time = datetime.now()
                    print(f"\n📊 LOG UPDATE - {current_time.strftime('%H:%M:%S')}")
                    print("-" * 30)
                    
                    # Show last few lines
                    lines = result.stdout.split('\n')
                    recent_lines = [line for line in lines[-20:] if line.strip()]
                    for line in recent_lines:
                        if any(keyword in line.lower() for keyword in ['info:', 'error:', 'warning:', 'debug:']):
                            print(line)
                
                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"❌ Log monitoring error: {e}")
                await asyncio.sleep(10)
    
    def stop_monitoring(self):
        """Stop log monitoring."""
        self.monitoring = False
        print("\n⏹️ Log monitoring stopped")

async def main():
    """Run log monitor with test option."""
    
    print("📊 REAL-TIME LOG MONITOR + TESTER")
    print("=" * 50)
    
    backend_url = input("Enter your Calibot backend URL: ").strip()
    
    if not backend_url:
        print("❌ Backend URL required")
        return
    
    if not backend_url.startswith("http"):
        backend_url = f"https://{backend_url}"
    
    print(f"🎯 Target: {backend_url}")
    print()
    
    monitor = RealTimeLogMonitor()
    
    # Start log monitoring in background
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    try:
        print("🧪 TESTING OPTIONS:")
        print("1. Send test message and watch logs")
        print("2. Test critical intent extraction")
        print("3. Just monitor logs")
        
        choice = input("Choose (1-3): ").strip()
        
        if choice in ["1", "2"]:
            # Import and run the backend tester
            from backend_bridge_tester import BackendBridgeTester
            
            async with BackendBridgeTester(backend_url) as tester:
                if choice == "1":
                    message = input("Enter test message: ").strip()
                    if message:
                        print(f"\n🚀 Sending test message: '{message}'")
                        result = await tester.send_webhook_payload(message)
                        print(f"📋 Result: {result.get('success', False)}")
                
                elif choice == "2":
                    print("\n🎯 Testing critical intent extraction...")
                    await tester.test_critical_intent_extraction()
        
        elif choice == "3":
            print("📊 Monitoring logs only...")
            await asyncio.sleep(60)  # Monitor for 1 minute
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
    finally:
        monitor.stop_monitoring()
        monitor_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
