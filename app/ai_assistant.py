"""AI Assistant component for Streamlit app."""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_api_key() -> str:
    """Get OpenAI API key from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            return st.secrets['OPENAI_API_KEY']
    except Exception:
        pass
    # Fall back to environment variable (for local development)
    return os.getenv('OPENAI_API_KEY', '')

from src.data_formatter import format_data_for_llm
from src.llm_client import get_llm_response
from src.vector_store import (
    initialize_vector_store,
    store_transactions,
    search_relevant_transactions
)
from src.config import VECTOR_DB_PATH
from src.ai_assistant_agent import answer_with_tools


def ensure_dt(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame has 'dt' column (date + time) for accurate sorting.
    
    Args:
        df: DataFrame with 'date' and optionally 'time' columns
        
    Returns:
        DataFrame with 'dt' column added
    """
    df = df.copy()
    # date voi olla "YYYY-MM-DD" tai datetime; time voi puuttua
    date = pd.to_datetime(df.get("date"), errors="coerce")
    if "time" in df.columns:
        # yhdistä date + time turvallisesti
        time = pd.to_timedelta(df["time"].astype(str), errors="coerce")
        df["dt"] = date + time.fillna(pd.Timedelta(0))
    else:
        df["dt"] = date
    return df


def df_fingerprint(df: pd.DataFrame) -> int:
    """
    Create a lightweight fingerprint of DataFrame for cache invalidation.
    
    Args:
        df: DataFrame to fingerprint
        
    Returns:
        Hash value representing the DataFrame state
    """
    # kevyt: rivimäärä + viimeisin dt + sarakkeet
    tmp = ensure_dt(df)
    latest = tmp["dt"].max()
    return hash((len(df), str(latest), tuple(df.columns)))


def format_tx(row: pd.Series, amount_col: str) -> str:
    """
    Format a single transaction row as a readable string.
    
    Args:
        row: Transaction row from DataFrame
        amount_col: Column name for amount ('adjusted_amount' or 'amount')
        
    Returns:
        Formatted transaction string
    """
    dt_str = row['dt'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row.get('dt')) else str(row.get('date', ''))
    return (f"{dt_str} | "
            f"{row.get('merchant', '')} | €{row.get(amount_col, 0):.2f} | "
            f"{row.get('category', '')} / {row.get('2nd category', '')}")


def handle_order_query(df_sorted: pd.DataFrame, query_lower: str) -> str:
    """
    Handle order-based queries deterministically without LLM.
    
    Args:
        df_sorted: DataFrame sorted by 'dt' descending (newest first)
        query_lower: Lowercase query text
        
    Returns:
        Formatted answer string
    """
    amount_col = "adjusted_amount" if "adjusted_amount" in df_sorted.columns else "amount"
    
    # Determine which transaction to get
    if "kolmanneksi" in query_lower or "third" in query_lower:
        idx = 2
        label = "Kolmanneksi viimeisin"
    elif "toiseksi" in query_lower or "second" in query_lower or "edellinen" in query_lower or "previous" in query_lower or "sitä edellinen" in query_lower:
        idx = 1
        label = "Toiseksi viimeisin"
    else:
        idx = 0
        label = "Viimeisin"
    
    if len(df_sorted) <= idx:
        return f"En löytänyt tarpeeksi tapahtumia. Tietokannassa on {len(df_sorted)} tapahtumaa."
    
    row = df_sorted.iloc[idx]
    tx_str = format_tx(row, amount_col)
    return f"{label} tapahtuma: {tx_str}"


def render_ai_assistant_tab(df: pd.DataFrame):
    """
    Render AI Assistant tab in Streamlit app.
    
    Args:
        df: DataFrame with transaction data
    """
    st.header("🤖 AI Assistant")
    st.markdown("Kysy rahoitustapahtumistasi ja saa analyysejä ja suosituksia.")
    
    # Debug mode checkbox
    debug_mode = st.checkbox("🔍 Debug mode", value=False, key="ai_debug_mode")
    
    # Model selection - default to gpt-4o-mini (gpt-5-nano returned empty responses)
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "gpt-4o-mini"
    
    # Check for API key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ OpenAI API-avain puuttuu")
        st.markdown("""
        ### Asennusohjeet:
        
        1. **Hanki OpenAI API-avain:**
           - Mene osoitteeseen: https://platform.openai.com/api-keys
           - Luo uusi API-avain
        
        2. **Aseta ympäristömuuttuja (paikallinen kehitys):**
           - Luo `.env`-tiedosto projektin juureen
           - Lisää rivi: `OPENAI_API_KEY=sk-...`
        
        3. **Tai Streamlit Cloud:**
           - Mene App Settings → Secrets
           - Lisää: `OPENAI_API_KEY = "sk-..."`
        
        4. **Käynnistä sovellus uudelleen**
        
        Katso tarkemmat ohjeet: `AI_ASSISTANT_SETUP.md`
        """)
        return
    
    # Initialize chat history
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []
    
    # Initialize formatted data cache with fingerprint-based invalidation
    fp = df_fingerprint(df)
    if st.session_state.get("ai_data_fp") != fp or 'ai_formatted_data' not in st.session_state:
        with st.spinner("Päivitetään analyysidata..."):
            formatted_data = format_data_for_llm(df)
            st.session_state.ai_formatted_data = formatted_data
            st.session_state.ai_data_fp = fp
    
    formatted_data = st.session_state.ai_formatted_data
    
    # Initialize vector store (RAG)
    vector_db_path = str(VECTOR_DB_PATH)
    collection_name = "transactions"
    
    # Check if vector store needs to be updated
    # Compare Excel file modification time with vector DB
    excel_path = os.getenv("DEFAULT_EXCEL_PATH", "")
    if not excel_path:
        from src.config import DEFAULT_EXCEL_PATH
        excel_path = DEFAULT_EXCEL_PATH or ""
    
    vector_db_exists = Path(vector_db_path).exists() and any(Path(vector_db_path).iterdir())
    excel_modified = Path(excel_path).stat().st_mtime if excel_path and Path(excel_path).exists() else 0
    
    # Initialize or update vector store if needed
    if not vector_db_exists or 'vector_db_initialized' not in st.session_state:
        try:
            with st.spinner("Luodaan vektoritietokantaa (ensimmäinen käyttö voi kestää hetken)..."):
                store_transactions(df, collection_name, api_key, vector_db_path, clear_existing=True)
                st.session_state.vector_db_initialized = True
                st.session_state.vector_db_timestamp = excel_modified
        except Exception as e:
            st.warning(f"⚠️ Vektoritietokannan luonti epäonnistui: {str(e)}")
            st.info("Käytetään yhteenvetoa ilman RAG-ominaisuutta.")
            vector_db_exists = False
    elif excel_modified > st.session_state.get('vector_db_timestamp', 0):
        # Data has changed, update vector store
        try:
            with st.spinner("Päivitetään vektoritietokantaa..."):
                # Clear existing and recreate (clear_existing=True handles this)
                store_transactions(df, collection_name, api_key, vector_db_path, clear_existing=True)
                st.session_state.vector_db_timestamp = excel_modified
        except Exception as e:
            st.warning(f"⚠️ Vektoritietokannan päivitys epäonnistui: {str(e)}")
    
    # Get current date for context
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # System prompt - yksinkertaistettu ja selkeä, sisältää tietomallin kuvauksen
    system_prompt = f"""Olet rahoitustapahtumien analysointiapuri. Analysoit käyttäjän rahoitustapahtumadataa ja vastaat suomeksi.

KRIITTINEN: NYKYINEN PÄIVÄMÄÄRÄ on {current_date} ({current_datetime}).
- Käytä tätä päivämäärää vertaillaksesi tapahtumien päivämääriä
- "Viimeisin" tarkoittaa tapahtumaa, joka on lähinnä nykyistä päivämäärää
- "Viime kuukausi" tarkoittaa kuukautta ennen {current_date}
- Jos kysytään "mikä päivä nyt on?", vastaa: "Tänään on {current_date}"

================================================================================
TAPAHTUMADATAN TIETOMALLI - KRIITTINEN TIETO HAKUJEN TEKEMISEEN
================================================================================

Jokainen tapahtuma sisältää seuraavat kentät:
- 📅 date: Päivämäärä (muoto: YYYY-MM-DD, esim. "2025-12-29")
- 🕐 time: Aika (muoto: HH:MM:SS, esim. "15:30:21")
- 🏪 merchant: Kaupan/kauppiaan nimi (esim. "Prisma", "K-Market Vuorela")
- 💰 amount: Alkuperäinen summa euroina (esim. 50.00)
- 💶 adjusted_amount: Korjattu summa (jos kustannusjako on käytössä, muuten sama kuin amount)
- 💳 card: Kortin nimi (esim. "crypto.com", "norwegian", "OP")
- 📂 category: Pääkategoria suomeksi (esim. "Ruokakauppa", "Ostokset", "Tapahtumat & Viihde")
- 📁 2nd category: Alakategoria suomeksi (esim. "Yleinen", "Perhe", "Henkilökohtainen")
- 📝 notes: Muistiinpanot (voi sisältää kustannusjaon prosentit, esim. "/50%")
- 📆 year: Vuosi (esim. 2025)
- 📅 month: Kuukausi (1-12)

KATEGORIAT (pääkategoriat):
- Ruokakauppa
- Ostokset
- Tapahtumat & Viihde
- Autoilu & Liikkuminen
- Ulkona syöminen
- Striimaus & Palvelut
- Terveys
- Matkailu
- Harrastukset
- Koulutus, Kirjallisuus & Kehittäminen

================================================================================
KRIITTISET SÄÄNNÖT - LUETTELO TARKASTI
================================================================================

KRIITTINEN SÄÄNTÖ #1: Jos saat "=== TAPAHTUMAT ===" -osion, SINUN ON PAKOLLISTA käyttää sitä!
- ÄLÄ käytä yhteenvetodataa jos tapahtumalista on saatavilla
- ÄLÄ keksi tai arvaa tietoja
- Käytä TÄYSIN samaa päivämäärää, kauppaa, summaa kuin listassa

KRIITTINEN SÄÄNTÖ #2: Tapahtumat on järjestetty päivämäärän mukaan - UUSIMMAT ENSIN!
- TAPAHTUMA #1 = UUSIN (uusin päivämäärä)
- TAPAHTUMA #2 = TOISEKSI UUSIN
- TAPAHTUMA #3 = KOLMANNEKSI UUSIN

KRIITTINEN SÄÄNTÖ #3: "Viimeisin" = TAPAHTUMA #1, "Toiseksi viimeinen" = TAPAHTUMA #2
- Jos kysytään "viimeisin" → käytä TAPAHTUMA #1
- Jos kysytään "toiseksi viimeinen" → käytä TAPAHTUMA #2
- Jos keskustelussa viitataan "sitä edellinen" tai "edellinen" → käytä TAPAHTUMA #2 (toiseksi viimeinen)
- Jos keskustelussa viitataan "sitä seuraava" → käytä TAPAHTUMA #1 (viimeisin)
- Tarkista AINA että päivämäärä on oikein (uusimmat ovat listan alussa)
- Vertaa päivämääriä nykyiseen päivämäärään ({current_date}) varmistaaksesi järjestyksen

================================================================================
MITEN TEHDÄ HAKUJA - ESIMERKKEJÄ
================================================================================

1. JÄRJESTYSPOHJAISET HAKUT (päivämäärän perusteella):
   - "Viimeisin tapahtuma" → Etsi TAPAHTUMA #1 (uusin päivämäärä)
   - "Toiseksi viimeinen" → Etsi TAPAHTUMA #2
   - "Tapahtumat viimeisen kuukauden aikana" → Suodata date-kentän perusteella

2. KAUPPAPOHJAISET HAKUT (merchant-kentän perusteella):
   - "Mitä olen kuluttanut Prismassa?" → Etsi kaikki jossa merchant sisältää "Prisma"
   - "Paljonko olen käyttänyt K-Marketissa?" → Laske summat jossa merchant sisältää "K-Market"
   - Käytä osittaisia osumia: "Prisma" löytää myös "Prisma Kuopio", "Prisma Tampereentie"

3. KATEGORIAPOHJAISET HAKUT (category tai 2nd category -kenttien perusteella):
   - "Paljonko olen käyttänyt ruokakauppaan?" → Etsi category = "Ruokakauppa", laske summat
   - "Mitä olen ostanut Ostokset-kategoriasta?" → Etsi category = "Ostokset", listaa tapahtumat
   - "Paljonko olen käyttänyt Perhe-alakategoriaan?" → Etsi 2nd category = "Perhe", laske summat

4. SUMMAPOHJAISET HAKUT (amount tai adjusted_amount -kenttien perusteella):
   - "Mikä on suurin tapahtuma?" → Etsi suurin adjusted_amount (tai amount)
   - "Tapahtumat yli €100" → Suodata adjusted_amount >= 100
   - Käytä adjusted_amount jos saatavilla, muuten amount

5. AIKAVÄLIPOHJAISET HAKUT (date-kentän perusteella):
   - "Tapahtumat tammikuussa 2025" → Suodata date >= "2025-01-01" AND date < "2025-02-01"
   - "Viimeisen 3 kuukauden tapahtumat" → Laske päivämäärä 3 kuukautta taaksepäin
   - Käytä year ja month -kenttiä jos saatavilla

6. YHDISTETYT HAKUT (useita kenttiä):
   - "Prisma-tapahtumat ruokakauppa-kategoriassa" → merchant sisältää "Prisma" AND category = "Ruokakauppa"
   - "Suuret ostokset (>€50) viime kuussa" → adjusted_amount > 50 AND category = "Ostokset" AND date viime kuusta

================================================================================
ESIMERKKEJÄ KYSYMYKSISTÄ JA VASTAUKSISTA
================================================================================

ESIMERKKI 1 - Viimeisin tapahtuma:
Tapahtumalista:
TAPAHTUMA #1: Päivämäärä: 2025-12-29 | Kauppa: Cursor Ai Powered Ide | Summa: €20.00 | Kategoria: Ostokset
TAPAHTUMA #2: Päivämäärä: 2025-12-15 | Kauppa: K-Market Vuorela | Summa: €14.93 | Kategoria: Ruokakauppa

Kysymys: "Mikä on viimeisin tapahtuma?"
OIKEA VASTAUS: "Viimeisin tapahtuma oli 2025-12-29 Cursor Ai Powered Ide, summa €20.00. Tapahtuma kuului kategoriaan Ostokset."
VÄÄRÄ VASTAUS: "Viimeisin tapahtuma oli 2025-12-15..." (väärä! Käytä #1, ei #2!)

ESIMERKKI 2 - Kauppakohtainen haku:
Kysymys: "Mitä olen kuluttanut Prismassa?"
VASTAUS: "Olet kuluttanut Prismassa yhteensä €450.00 12 tapahtumassa:
- 2025-12-29: Prisma Kuopio, €50.00, Ruokakauppa
- 2025-12-15: Prisma Tampereentie, €30.00, Ruokakauppa
- ... (listaa kaikki Prisma-tapahtumat)"

ESIMERKKI 3 - Kategoriapohjainen haku:
Kysymys: "Paljonko olen käyttänyt ruokakauppaan?"
VASTAUS: "Olet käyttänyt ruokakauppaan yhteensä €2,618.08 156 tapahtumassa. Keskiarvo per tapahtuma on €16.78."

ESIMERKKI 4 - Aikavälipohjainen haku:
Kysymys: "Mitä tapahtumia oli tammikuussa 2025?"
VASTAUS: "Tammikuussa 2025 oli 87 tapahtumaa, yhteensä €1,058.11. Suurimmat kategoriat olivat:
- Ruokakauppa: €450.00
- Ostokset: €300.00
- ..."

================================================================================
OHJEET VASTAUKSIEN MUODOSTAMISEEN
================================================================================

1. Käytä TÄYSIN samaa tietoa kuin tapahtumalistassa:
   - Päivämäärä: käytä täsmälleen samaa muotoa (esim. "2025-12-29")
   - Kauppa: käytä täsmälleen samaa nimeä (esim. "Cursor Ai Powered Ide")
   - Summa: käytä täsmälleen samaa summaa (esim. "€20.00")
   - Kategoria: käytä täsmälleen samaa kategoriaa (esim. "Ostokset")

2. Laske summat oikein:
   - Käytä adjusted_amount jos saatavilla, muuten amount
   - Pyöristä summat kahteen desimaaliin (€XX.XX)
   - Laske keskiarvot, mediaanit, yhteissummat tarvittaessa

3. Ryhmittele tapahtumat:
   - Kategorioittain: groupby('category')
   - Kuukausittain: groupby(['year', 'month'])
   - Kauppakohtaisesti: groupby('merchant')
   - Alakategorioittain: groupby('2nd category')

4. Anna konkreettisia analyyseja:
   - Vertaa kategorioita keskenään
   - Vertaa kuukausia keskenään
   - Etsi säästömahdollisuuksia
   - Anna suosituksia

Anna konkreettisia analyyseja ja suosituksia säästämisestä. Ole ystävällinen ja auttavainen."""

    # Display chat history
    if st.session_state.ai_chat_history:
        st.markdown("### Keskusteluhistoria")
        for msg in st.session_state.ai_chat_history:
            if msg['role'] == 'user':
                with st.chat_message("user"):
                    st.write(msg['content'])
            elif msg['role'] == 'assistant':
                with st.chat_message("assistant"):
                    st.write(msg['content'])
    
    # Chat input
    user_input = st.chat_input("Kysy jotain rahoitustapahtumistasi...")
    
    if user_input:
        # Add user message to history
        st.session_state.ai_chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Check if query is about "latest", "newest", "last" etc. - use deterministic pandas query
        query_lower = user_input.lower()
        is_order_query = any(keyword in query_lower for keyword in [
            'viimeisin', 'uusin', 'viimeinen', 'vika', 'toiseksi viimeinen', 
            'toiseksi uusin', 'kolmanneksi viimeinen', 'kolmanneksi uusin',
            'edellinen', 'seuraava', 'sitä edellinen', 'sitä seuraava',
            'latest', 'newest', 'last', 'second last', 'third last', 'previous', 'next'
        ])
        
        # Handle order-based queries deterministically (without LLM) - fast path
        if is_order_query and not df.empty and 'date' in df.columns:
            try:
                # Ensure dt column exists and sort by it (date + time)
                df_with_dt = ensure_dt(df)
                df_sorted = df_with_dt.sort_values('dt', ascending=False, na_position='last')
                
                # Get deterministic answer without LLM
                answer = handle_order_query(df_sorted, query_lower)
                
                # Add assistant response to history
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': answer
                })
                
                # Rerun to show new messages
                st.rerun()
                return  # Exit early, no LLM call needed
                
            except Exception as e:
                st.warning(f"⚠️ Tapahtumien haku DataFrameesta epäonnistui: {str(e)}")
                # Remove user message if query failed
                if st.session_state.ai_chat_history and st.session_state.ai_chat_history[-1]['role'] == 'user':
                    st.session_state.ai_chat_history.pop()
                return
        
        # Try tools-based approach first (router -> executor -> narrator)
        try:
            result = answer_with_tools(
                df=df,
                user_input=user_input,
                api_key=api_key,
                get_llm_response=get_llm_response,
                router_model="gpt-4o-mini",
                narrator_model=st.session_state.get('ai_model', 'gpt-4o-mini'),
            )
            
            # Show debug info if enabled
            if debug_mode:
                with st.expander("🔍 Debug Info", expanded=True):
                    st.json({
                        "mode": result.get("mode"),
                        "plan": result.get("plan"),
                        "execution_summary": {
                            "tool": result.get("execution", {}).get("tool"),
                            "args": result.get("execution", {}).get("args"),
                            "result_summary": result.get("execution", {}).get("result", {}).get("summary") if result.get("execution", {}).get("result") else None
                        }
                    })
            
            if result["mode"] == "tools" and result.get("answer", "").strip():
                # Tools-based answer succeeded
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': result["answer"]
                })
                st.rerun()
                return  # Exit early, tools handled it
        except Exception as e:
            # If tools fail, fall back to RAG
            if debug_mode:
                st.error(f"⚠️ Työkalujen käyttö epäonnistui: {str(e)}")
            else:
                st.warning(f"⚠️ Työkalujen käyttö epäonnistui: {str(e)}")
        
        # Fallback to RAG/summary flow for semantic questions
        relevant_transactions_text = ""
        
        # Use RAG for semantic queries (if not order-based query)
        if vector_db_exists and 'vector_db_initialized' in st.session_state:
            try:
                relevant_transactions = search_relevant_transactions(
                    user_input, 
                    collection_name, 
                    api_key, 
                    vector_db_path, 
                    top_k=15
                )
                
                if relevant_transactions:
                    # Sort transactions by date (newest first) - parse date properly
                    def parse_date_for_sort(trans):
                        date_str = trans.get('metadata', {}).get('date', '')
                        time_str = trans.get('metadata', {}).get('time', '')
                        try:
                            # Try to parse date string (format: "2025-12-29" or "2025-12-29 00:00:00")
                            from datetime import datetime, timedelta
                            if ' ' in str(date_str):
                                date_str = str(date_str).split(' ')[0]
                            dt = datetime.strptime(str(date_str), '%Y-%m-%d')
                            # Add time if available
                            if time_str:
                                try:
                                    time_parts = str(time_str).split(':')
                                    if len(time_parts) >= 2:
                                        hours = int(time_parts[0])
                                        minutes = int(time_parts[1])
                                        seconds = int(time_parts[2]) if len(time_parts) > 2 else 0
                                        dt += timedelta(hours=hours, minutes=minutes, seconds=seconds)
                                except:
                                    pass
                            return dt
                        except:
                            # If parsing fails, return a very old date so it goes to the end
                            return datetime(1900, 1, 1)
                    
                    sorted_transactions = sorted(
                        relevant_transactions,
                        key=parse_date_for_sort,
                        reverse=True
                    )
                    
                    relevant_transactions_text = "\n\n" + "="*80 + "\n"
                    relevant_transactions_text += "=== RELEVANTIT TAPAHTUMAT (löydetty kysymyksesi perusteella) ===\n"
                    relevant_transactions_text += "KRIITTINEN: Nämä tapahtumat on järjestetty päivämäärän mukaan: UUSIMMAT ENSIN!\n"
                    relevant_transactions_text += "NUMERO 1 = UUSIN TAPAHTUMA, NUMERO 2 = TOISEKSI UUSIN, jne.\n"
                    relevant_transactions_text += "="*80 + "\n\n"
                    relevant_transactions_text += "PAKOLLISTA: Käytä NÄITÄ tapahtumia vastauksessasi! Älä käytä yhteenvetodataa!\n\n"
                    
                    for i, trans in enumerate(sorted_transactions, 1):
                        metadata = trans.get('metadata', {})
                        document = trans.get('document', '')
                        date_str = str(metadata.get('date', ''))
                        # Clean date string (remove time if present)
                        if ' ' in date_str:
                            date_str = date_str.split(' ')[0]
                        
                        relevant_transactions_text += (
                            f"TAPAHTUMA #{i} (uusin={i==1}, toiseksi uusin={i==2}):\n"
                            f"  📅 Päivämäärä: {date_str}\n"
                            f"  🏪 Kauppa: {metadata.get('merchant', '')}\n"
                            f"  💰 Summa: €{metadata.get('amount', 0):.2f}\n"
                            f"  📂 Kategoria: {metadata.get('category', '')}\n"
                            f"  📁 Alakategoria: {metadata.get('subcategory', '')}\n"
                            f"  📄 Täydet tiedot: {document}\n\n"
                        )
            except Exception as e:
                # If RAG fails, continue without it
                st.warning(f"⚠️ Tapahtumien haku epäonnistui: {str(e)}")
        
        # Prepare messages for API
        # If we have transaction list, prioritize it and don't include summary data for order-based queries
        if relevant_transactions_text and is_order_query:
            # For order-based queries, ONLY use transaction list (no summary data to avoid confusion)
            data_context = relevant_transactions_text
        elif relevant_transactions_text:
            # For other queries, include both summary and transaction list
            data_context = f"Tässä on käyttäjän rahoitustapahtumadata:\n\nJSON-muoto:\n{formatted_data['json_summary']}\n\nTekstimuoto:\n{formatted_data['text_summary']}"
            data_context += relevant_transactions_text
        else:
            # No transaction list available, use summary only
            data_context = f"Tässä on käyttäjän rahoitustapahtumadata:\n\nJSON-muoto:\n{formatted_data['json_summary']}\n\nTekstimuoto:\n{formatted_data['text_summary']}"
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'system', 'content': data_context}
        ]
        
        # Add chat history (last 10 messages to avoid token limit)
        for msg in st.session_state.ai_chat_history[-10:]:
            messages.append(msg)
        
        # Get response from LLM
        try:
            with st.spinner("Käsitellään..."):
                # Use gpt-4o-mini as default (gpt-5-nano had issues)
                model = st.session_state.get('ai_model', 'gpt-4o-mini')
                # Debug: show model being used
                st.session_state.debug_model = model
                response = get_llm_response(messages, api_key, model=model)
            
            # Check if response is valid
            if not response or not response.strip():
                st.error("❌ Vastaus oli tyhjä. Yritä uudelleen.")
                # Remove the user message from history if response failed
                if st.session_state.ai_chat_history and st.session_state.ai_chat_history[-1]['role'] == 'user':
                    st.session_state.ai_chat_history.pop()
            else:
                # Add assistant response to history
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': response
                })
                
                # Rerun to show new messages
                st.rerun()
            
        except ImportError as e:
            st.error(f"❌ {str(e)}")
            # Remove the user message from history if import failed
            if st.session_state.ai_chat_history and st.session_state.ai_chat_history[-1]['role'] == 'user':
                st.session_state.ai_chat_history.pop()
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Virhe: {error_msg}")
            # Show debug info
            if 'debug_model' in st.session_state:
                st.caption(f"Käytetty malli: {st.session_state.debug_model}")
            st.info("Yritä uudelleen tai tarkista API-avain.")
            # Remove the user message from history if request failed
            if st.session_state.ai_chat_history and st.session_state.ai_chat_history[-1]['role'] == 'user':
                st.session_state.ai_chat_history.pop()
    
    # Clear history button
    if st.session_state.ai_chat_history:
        if st.button("🗑️ Tyhjennä keskusteluhistoria"):
            st.session_state.ai_chat_history = []
            st.rerun()

