#!/usr/bin/env python3
"""Complete pipeline runner with error handling."""

import sys
from pathlib import Path

# Tarkista että käytetään virtuaaliympäristön Pythonia
venv_python = Path(__file__).parent / "venv" / "bin" / "python"
if venv_python.exists() and sys.executable != str(venv_python):
    print("⚠️  Varoitus: Käytät järjestelmän Pythonia, ei virtuaaliympäristön Pythonia!")
    print(f"   Nykyinen: {sys.executable}")
    print(f"   Suositeltu: {venv_python}")
    print("\n💡 Vinkki: Aktivoi virtuaaliympäristö ensin:")
    print("   source venv/bin/activate")
    print("   tai")
    print("   ./activate.sh")
    print("\n   Sitten aja:")
    print("   python run_pipeline.py")
    print("\n" + "=" * 60)
    response = input("Jatketaanko silti? (y/N): ")
    if response.lower() != 'y':
        sys.exit(1)
    print("=" * 60 + "\n")

# Lisää src-hakemisto polkuun
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import process_file, process_new_files
from src.config import DEFAULT_CSV_PATH, RAW_DATA_DIR
import os

def main():
    """Run the complete pipeline."""
    
    print("=" * 60)
    print("💰 Finance Transaction Pipeline")
    print("=" * 60)
    
    try:
        # Jos DEFAULT_CSV_PATH on asetettu, käytä sitä
        if DEFAULT_CSV_PATH and os.path.exists(DEFAULT_CSV_PATH):
            print(f"\n📂 CSV-tiedosto: {DEFAULT_CSV_PATH}")
            print("\n🔄 Aloitetaan prosessointi...")
            df = process_file(
                csv_path=DEFAULT_CSV_PATH,
                start_date='2025-01-01',
                verbose=True
            )
        # Muuten yritä käyttää data/raw/ -kansiota
        elif RAW_DATA_DIR.exists() and any(RAW_DATA_DIR.glob("*.csv")):
            print(f"\n📂 Etsitään CSV-tiedostoja kansiosta: {RAW_DATA_DIR}")
            print("\n🔄 Aloitetaan prosessointi...")
            df = process_new_files(
                directory=RAW_DATA_DIR,
                start_date='2025-01-01',
                verbose=True
            )
            if df is None or df.empty:
                print("\n⚠️  Ei löytynyt käsiteltäviä CSV-tiedostoja.")
                print("💡 Vinkki: Lisää CSV-tiedostoja data/raw/ -kansioon tai aseta DEFAULT_CSV_PATH .env-tiedostossa")
                return 0  # Ei virhe, vain ei dataa
        else:
            print("⚠️  Ei löytynyt CSV-tiedostoja.")
            print("\n💡 Vinkit:")
            print("   1. Lisää CSV-tiedostoja data/raw/ -kansioon, TAI")
            print("   2. Kopioi .env.example tiedosto .env-tiedostoksi:")
            print("      cp .env.example .env")
            print("   3. Muokkaa .env-tiedostoa ja aseta DEFAULT_CSV_PATH")
            return 0  # Ei virhe, vain ei dataa
        
        # Näytä tulokset
        if df is not None and not df.empty:
            print("\n" + "=" * 60)
            print("✅ Pipeline valmis!")
            print("=" * 60)
            print(f"📊 Käsiteltyjä rivejä: {len(df)}")
            print(f"📅 Aikaväli: {df['date'].min()} - {df['date'].max()}")
            print(f"💰 Kokonaissumma: €{df['adjusted_amount'].sum():,.2f}")
            print(f"📈 Kategorioita: {df['category'].nunique()}")
            print(f"🏪 Kauppoja: {df['merchant'].nunique()}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Virhe prosessoinnissa: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

