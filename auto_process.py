#!/usr/bin/env python3
"""Automatic CSV file processor using watchdog."""

import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import process_file
from src.config import RAW_DATA_DIR

class CSVHandler(FileSystemEventHandler):
    """Handle CSV file events."""
    
    def __init__(self):
        self.processed_files = set()
    
    def on_created(self, event):
        """Called when a file is created."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process CSV files
        if file_path.suffix.lower() == '.csv':
            # Wait a bit to ensure file is fully written
            time.sleep(2)
            
            print(f"\n🔄 Uusi CSV-tiedosto havaittu: {file_path.name}")
            
            try:
                # Process the file
                df = process_file(
                    str(file_path),
                    start_date='2025-01-01',
                    verbose=True
                )
                
                if not df.empty:
                    print(f"✅ Käsitelty {len(df)} tapahtumaa")
                else:
                    print("⚠️  Tiedosto oli tyhjä tai ei sisältänyt uusia tapahtumia")
                    
            except Exception as e:
                print(f"❌ Virhe käsiteltäessä tiedostoa: {e}")

def main():
    """Start the file watcher."""
    print("=" * 60)
    print("👀 CSV-tiedostojen automaattinen käsittely")
    print("=" * 60)
    print(f"📂 Tarkkaillaan kansiota: {RAW_DATA_DIR}")
    print("\n💡 Kopioi CSV-tiedostot tähän kansioon, ne käsitellään automaattisesti")
    print("   Paina Ctrl+C lopettaaksesi\n")
    
    # Ensure directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create event handler and observer
    event_handler = CSVHandler()
    observer = Observer()
    observer.schedule(event_handler, str(RAW_DATA_DIR), recursive=False)
    
    # Start watching
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n👋 Lopetetaan tarkkailu...")
    
    observer.join()

if __name__ == "__main__":
    main()
