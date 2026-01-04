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

from src.pipeline import process_file
from src.config import DEFAULT_CSV_PATH
import os

def main():
    """Run the complete pipeline."""
    
    print("=" * 60)
    print("💰 Finance Transaction Pipeline")
    print("=" * 60)
    
    # Tarkista että CSV-tiedosto on asetettu ja olemassa
    if not DEFAULT_CSV_PATH:
        print("❌ Virhe: DEFAULT_CSV_PATH ei ole asetettu!")
        print("\n💡 Vinkki: Aseta DEFAULT_CSV_PATH ympäristömuuttujana tai .env-tiedostossa")
        print("   1. Kopioi .env.example tiedosto .env-tiedostoksi:")
        print("      cp .env.example .env")
        print("   2. Muokkaa .env-tiedostoa ja aseta DEFAULT_CSV_PATH")
        print("   3. Tai käytä data/raw/ -kansiota CSV-tiedostoillesi")
        return 1
    
    if not os.path.exists(DEFAULT_CSV_PATH):
        print(f"❌ Virhe: CSV-tiedosto ei löydy!")
        print(f"   Polku: {DEFAULT_CSV_PATH}")
        print(f"\n💡 Vinkki: Tarkista polku .env-tiedostossa tai aseta DEFAULT_CSV_PATH ympäristömuuttujana")
        return 1
    
    print(f"\n📂 CSV-tiedosto: {DEFAULT_CSV_PATH}")
    
    try:
        # Aja pipeline
        print("\n🔄 Aloitetaan prosessointi...")
        df = process_file(
            csv_path=DEFAULT_CSV_PATH,
            start_date='2025-01-01',
            verbose=True
        )
        
        # Näytä tulokset
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

