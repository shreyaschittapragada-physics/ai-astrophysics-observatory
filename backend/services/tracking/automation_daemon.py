import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys

# Align workspace system path context
sys.path.append(os.getcwd())

from backend.services.database.db_manager import DatabaseManager

class ObservatoryAutomationDaemon:
    def __init__(self, check_interval_seconds=1):
        self.check_interval = check_interval_seconds
        self.db = DatabaseManager()
        self.is_running = False
        self.current_state = "IDLE"  # States: IDLE, ARMED, RECORDING
        
        # Using modern, timezone-aware UTC datetime tracking
        self.pass_timetable = [
            {
                "target": "ISS (ZARYA)",
                "aos": datetime.now(timezone.utc) + timedelta(seconds=3),  # 3 seconds out
                "los": datetime.now(timezone.utc) + timedelta(seconds=10)  # 10 seconds out
            }
        ]
        print("🤖 Autonomous Edge Daemon Management Core Initialized.")

    async def start_orchestration_loop(self):
        """Main asynchronous event loop managing camera state transitions."""
        self.is_running = True
        print("⏰ Automation scheduling loop activated. Scanning timetable...\n")
        
        while self.is_running:
            now = datetime.now(timezone.utc)
            
            for execution_pass in list(self.pass_timetable):
                target = execution_pass["target"]
                aos = execution_pass["aos"]
                los = execution_pass["los"]
                
                # State 1: Target approaching within 5 seconds -> ARM system
                if now < aos and (aos - now).total_seconds() <= 5 and self.current_state == "IDLE":
                    self.current_state = "ARMED"
                    print(f"🚨 [STATE: ARMED] Target {target} approaching horizon. Initializing pre-motion memory ring buffers...")
                
                # State 2: Target visible -> RECORD
                elif aos <= now <= los and self.current_state != "RECORDING":
                    self.current_state = "RECORDING"
                    print(f"📸 [STATE: RECORDING] Target {target} is above horizon footprint! Optical CV frame processing active.")
                
                # State 3: Target lost -> Return to IDLE & save resources
                elif now > los and self.current_state == "RECORDING":
                    self.current_state = "IDLE"
                    print(f"💤 [STATE: IDLE] Target {target} dropped below horizon. Spinning down CV camera matrix threads to save power.\n")
                    self.pass_timetable.remove(execution_pass)
            
            await asyncio.sleep(self.check_interval)

    def stop(self):
        self.is_running = False
        print("🛑 Automation scheduling loop halted safely.")

async def main():
    daemon = ObservatoryAutomationDaemon(check_interval_seconds=1)
    try:
        # Fixed the simulation timeout window to 15 seconds to catch all state changes cleanly
        await asyncio.wait_for(daemon.start_orchestration_loop(), timeout=15.0)
    except TimeoutError:
        # Caught the native standard TimeoutError properly
        daemon.stop()

if __name__ == "__main__":
    asyncio.run(main())
