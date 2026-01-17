"""Streamlit app for viewing and editing transaction data."""

import sys
import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, date

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import AI Assistant (optional feature)
try:
    from app.ai_assistant import render_ai_assistant_tab
    AI_ASSISTANT_AVAILABLE = True
except ImportError:
    AI_ASSISTANT_AVAILABLE = False

# Try to import LLM client for insights
try:
    from src.llm_client import get_llm_response
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

from src.pipeline import (
    process_new_files,
    detect_new_files,
    process_dataframe
)
from src.config import CATEGORY_EN_TO_FI, GENERAL_2ND_CATEGORIES


# Page configuration
st.set_page_config(
    page_title="Finance Transaction Manager",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'edited' not in st.session_state:
    st.session_state.edited = False
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = None
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load processed data (deprecated - using session state)."""
    return pd.DataFrame()


def refresh_data():
    """Process new files and reload data."""
    with st.spinner("Processing new files..."):
        try:
            df = process_new_files(verbose=False)
            if not df.empty:
                st.session_state.df = df
        except Exception as e:
            st.warning(f"Could not process new files: {e}")
    st.session_state.edited = False
    st.rerun()


def save_changes(df: pd.DataFrame):
    """Save changes to session state."""
    st.session_state.df = df
    st.session_state.edited = False
    st.success("Changes saved to session!")


# Insights helper functions
def calculate_category_changes(df: pd.DataFrame, period_months: int = 1, custom_start: str = None, custom_end: str = None, custom_period1_start: str = None, custom_period1_end: str = None):
    """Calculate category spending changes between time periods.
    
    Args:
        df: DataFrame with transaction data
        period_months: Number of months to compare (1, 3, 6, or None for custom)
        custom_start: Custom start date (YYYY-MM-DD) if period_months is None
        custom_end: Custom end date (YYYY-MM-DD) if period_months is None
    """
    if 'date' not in df.columns or 'category' not in df.columns or 'adjusted_amount' not in df.columns:
        return None
    
    # Get monthly spending by category
    df_temp = df.copy()
    df_temp['month_period'] = df_temp['date'].dt.to_period('M')
    monthly_by_cat = df_temp.groupby(['month_period', 'category'])['adjusted_amount'].sum().reset_index()
    monthly_by_cat['month_period'] = monthly_by_cat['month_period'].astype(str)
    
    # Sort by date
    monthly_by_cat = monthly_by_cat.sort_values('month_period')
    unique_months = sorted(monthly_by_cat['month_period'].unique())
    
    if len(unique_months) < 2:
        return None
    
    # Determine comparison periods
    if custom_start and custom_end:
        # Custom date range (e.g., year-to-year or custom month selection)
        # custom_start/end represent period 2 (previous period)
        period2_start = pd.to_datetime(custom_start)
        period2_end = pd.to_datetime(custom_end)
        
        # Calculate period length
        period_days = (period2_end - period2_start).days
        
        # Get period 2 (previous period, e.g., last year or second selected month)
        period2_df = df_temp[(df_temp['date'] >= period2_start) & (df_temp['date'] <= period2_end)]
        
        # Get period 1 (current period)
        # If custom_period1_start/end are provided, use them (for custom month selection)
        # Otherwise, calculate period 1 from period 2 (for year-to-year)
        if custom_period1_start and custom_period1_end:
            # Custom month selection - use provided period 1 dates
            period1_start = pd.to_datetime(custom_period1_start)
            period1_end = pd.to_datetime(custom_period1_end)
        else:
            # Year-to-year: period 1 is same month in current year
            period1_start = period2_start + pd.DateOffset(years=1)
            period1_end = period2_end + pd.DateOffset(years=1)
        period1_df = df_temp[(df_temp['date'] >= period1_start) & (df_temp['date'] <= period1_end)]
        
        # If period 1 is empty or doesn't exist, try to use last available month
        if period1_df.empty:
            # Use last month as period 1
            last_month_period = unique_months[-1]
            last_month_str = str(last_month_period)
            year, month = map(int, last_month_str.split('-'))
            period1_start = pd.Timestamp(year, month, 1)
            if month == 12:
                period1_end = pd.Timestamp(year, month, 31)
            else:
                period1_end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)
            period1_df = df_temp[(df_temp['date'] >= period1_start) & (df_temp['date'] <= period1_end)]
        
        period1_name = f"{period1_start.strftime('%Y-%m')} - {period1_end.strftime('%Y-%m')}"
        period2_name = f"{period2_start.strftime('%Y-%m')} - {period2_end.strftime('%Y-%m')}"
        
        # Calculate totals for each period
        period1_totals = period1_df.groupby('category')['adjusted_amount'].sum()
        period2_totals = period2_df.groupby('category')['adjusted_amount'].sum()
        
        # Calculate average per category (all time)
        avg_by_cat = df_temp.groupby('category')['adjusted_amount'].sum() / df_temp['month_period'].nunique()
        
    else:
        # Fixed period comparison (1, 3, or 6 months)
        if period_months == 1:
            # Last month vs previous month
            last_month = unique_months[-1]
            prev_month = unique_months[-2]
            period1_months = [last_month]
            period2_months = [prev_month]
            # Convert Period to string format (e.g., "1/2025")
            last_month_str = str(last_month)
            prev_month_str = str(prev_month)
            last_year, last_month_num = map(int, last_month_str.split('-'))
            prev_year, prev_month_num = map(int, prev_month_str.split('-'))
            period1_name = f"{last_month_num}/{last_year}"
            period2_name = f"{prev_month_num}/{prev_year}"
        else:
            # Last N months vs previous N months
            if len(unique_months) < period_months * 2:
                return None
            
            period1_months = unique_months[-period_months:]
            period2_months = unique_months[-(period_months * 2):-period_months]
            # Convert Period objects to string format
            period1_start_str = str(period1_months[0])
            period1_end_str = str(period1_months[-1])
            period2_start_str = str(period2_months[0])
            period2_end_str = str(period2_months[-1])
            
            # Format as "1/2025 - 3/2025"
            p1_start_year, p1_start_month = map(int, period1_start_str.split('-'))
            p1_end_year, p1_end_month = map(int, period1_end_str.split('-'))
            p2_start_year, p2_start_month = map(int, period2_start_str.split('-'))
            p2_end_year, p2_end_month = map(int, period2_end_str.split('-'))
            
            period1_name = f"{p1_start_month}/{p1_start_year} - {p1_end_month}/{p1_end_year}"
            period2_name = f"{p2_start_month}/{p2_start_year} - {p2_end_month}/{p2_end_year}"
        
        # Get spending for each period
        period1_data = monthly_by_cat[monthly_by_cat['month_period'].isin(period1_months)]
        period2_data = monthly_by_cat[monthly_by_cat['month_period'].isin(period2_months)]
        
        period1_totals = period1_data.groupby('category')['adjusted_amount'].sum()
        period2_totals = period2_data.groupby('category')['adjusted_amount'].sum()
        
        # Calculate average per category (all time)
        avg_by_cat = df_temp.groupby('category')['adjusted_amount'].sum() / df_temp['month_period'].nunique()
    
    # Calculate changes
    changes = []
    all_categories = set(avg_by_cat.index) | set(period1_totals.index) | set(period2_totals.index)
    
    for cat in all_categories:
        period1_val = period1_totals.get(cat, 0)
        period2_val = period2_totals.get(cat, 0)
        avg_val = avg_by_cat.get(cat, 0)
        
        if period2_val > 0:
            change_pct = ((period1_val - period2_val) / period2_val) * 100
            change_abs = period1_val - period2_val
        else:
            change_pct = 100 if period1_val > 0 else 0
            change_abs = period1_val
        
        vs_avg_pct = ((period1_val - avg_val) / avg_val * 100) if avg_val > 0 else 0
        
        changes.append({
            'category': cat,
            'period1': period1_val,
            'period2': period2_val,
            'average': avg_val,
            'change_pct': change_pct,
            'change_abs': change_abs,
            'vs_avg_pct': vs_avg_pct
        })
    
    return pd.DataFrame(changes), period1_name, period2_name


def get_top_merchants_by_category(df: pd.DataFrame, category: str, period_months: int = 1, custom_start: str = None, custom_end: str = None, custom_period1_start: str = None, custom_period1_end: str = None, top_n: int = 5):
    """Get top merchants for a category in the comparison period (period 1 - current period)."""
    if 'merchant' not in df.columns or 'category' not in df.columns or 'adjusted_amount' not in df.columns:
        return []
    
    df_temp = df[df['category'] == category].copy()
    
    if df_temp.empty:
        return []
    
    # Filter by period
    if custom_period1_start and custom_period1_end:
        # Custom month selection - use period1 directly
        period1_start = pd.to_datetime(custom_period1_start)
        period1_end = pd.to_datetime(custom_period1_end)
        period_df = df_temp[(df_temp['date'] >= period1_start) & (df_temp['date'] <= period1_end)]
    elif custom_start and custom_end:
        # For year-to-year: custom_start/end is period 2, we need period 1 (current year)
        period2_start = pd.to_datetime(custom_start)
        period2_end = pd.to_datetime(custom_end)
        
        # Period 1 is same period in current year
        period1_start = period2_start + pd.DateOffset(years=1)
        period1_end = period2_end + pd.DateOffset(years=1)
        
        # Use period 1 (current period) for merchant analysis
        period_df = df_temp[(df_temp['date'] >= period1_start) & (df_temp['date'] <= period1_end)]
        
        # If period 1 is empty, use last month
        if period_df.empty:
            df_temp['month_period'] = df_temp['date'].dt.to_period('M')
            unique_months = sorted(df_temp['month_period'].unique())
            if len(unique_months) > 0:
                last_month_period = unique_months[-1]
                # Convert Period to string first
                last_month_str = str(last_month_period)
                year, month = map(int, last_month_str.split('-'))
                period1_start = pd.Timestamp(year, month, 1)
                if month == 12:
                    period1_end = pd.Timestamp(year, month, 31)
                else:
                    period1_end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)
                period_df = df_temp[(df_temp['date'] >= period1_start) & (df_temp['date'] <= period1_end)]
    else:
        # Get last N months
        if period_months is None:
            # If period_months is None, use last month
            period_months = 1
        
        df_temp['month_period'] = df_temp['date'].dt.to_period('M')
        unique_months = sorted(df_temp['month_period'].unique())
        if len(unique_months) < period_months:
            period_df = df_temp
        else:
            period_months_list = unique_months[-period_months:]
            period_df = df_temp[df_temp['month_period'].isin(period_months_list)]
    
    if period_df.empty:
        return []
    
    # Get top merchants
    top_merchants = period_df.groupby('merchant')['adjusted_amount'].sum().sort_values(ascending=False).head(top_n)
    
    return [
        {'merchant': merchant, 'amount': float(amount)}
        for merchant, amount in top_merchants.items()
    ]


def generate_analytics_insights(
    df: pd.DataFrame,
    changes_df: pd.DataFrame,
    opportunities: list,
    high_vs_avg: pd.DataFrame,
    period1_name: str,
    period2_name: str,
    period_months: int = 1,
    custom_start: str = None,
    custom_end: str = None,
    custom_period1_start: str = None,
    custom_period1_end: str = None,
    api_key: str = None
) -> str:
    """
    Generate smart insights summary using LLM for Analytics section.
    
    Args:
        changes_df: DataFrame with category changes
        opportunities: List of savings opportunities
        high_vs_avg: DataFrame with categories vs average
        period1_name: Name of period 1
        period2_name: Name of period 2
        api_key: OpenAI API key
        
    Returns:
        Formatted insights summary or None if error
    """
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        return "Error: OpenAI API key not found. Please set OPENAI_API_KEY in .env file."
    
    # Check if LLM client is available
    if not LLM_AVAILABLE:
        return "Error: LLM client not available. Check imports."
    
    try:
        # Prepare data summary for LLM
        # Top 3 increasing categories
        top_increasing = changes_df.nlargest(3, 'change_pct')
        top_decreasing = changes_df.nsmallest(3, 'change_pct')
        
        # Top savings opportunities
        top_opportunities = sorted(opportunities, key=lambda x: x.get('savings_potential_15', 0), reverse=True)[:3] if opportunities else []
        
        # Categories above average
        top_above_avg = high_vs_avg.head(3) if not high_vs_avg.empty else pd.DataFrame()
        
        # Format data for LLM
        data_summary = f"""VERTAILU: {period1_name} vs {period2_name}

TOP 3 KASVAVAT KATEGORIAT:
"""
        for idx, row in top_increasing.iterrows():
            if row['change_pct'] > 0:
                category = row['category']
                data_summary += f"- {category}: +{row['change_pct']:.1f}% (€{row['period2']:,.2f} → €{row['period1']:,.2f})\n"
                
                # Get top merchants for this category in period1
                top_merchants = get_top_merchants_by_category(
                    df, category, period_months, custom_start, custom_end,
                    custom_period1_start, custom_period1_end, top_n=3
                )
                if top_merchants:
                    merchant_list = ", ".join([f"{m['merchant']} (€{m['amount']:,.2f})" for m in top_merchants])
                    data_summary += f"  → Top merchantit: {merchant_list}\n"
        
        data_summary += "\nTOP 3 LASKEVAT KATEGORIAT:\n"
        for idx, row in top_decreasing.iterrows():
            if row['change_pct'] < 0:
                data_summary += f"- {row['category']}: {row['change_pct']:.1f}% (€{row['period2']:,.2f} → €{row['period1']:,.2f})\n"
        
        if top_opportunities:
            data_summary += "\nTOP SÄÄSTÖMAHDOLLISUUDET:\n"
            for opp in top_opportunities:
                data_summary += f"- {opp['category']}: {opp['title']} - Säästöpotentiaali: €{opp.get('savings_potential_15', 0):,.2f}\n"
        
        if not top_above_avg.empty:
            data_summary += "\nKATEGORIAT KESKIARVON YLÄPUOLELLA:\n"
            for idx, row in top_above_avg.iterrows():
                # Use 'average' column if available, otherwise calculate from period1 and vs_avg_pct
                avg_val = row.get('average', row.get('avg', row['period1'] / (1 + row['vs_avg_pct'] / 100)))
                data_summary += f"- {row['category']}: {row['vs_avg_pct']:.1f}% keskiarvon yläpuolella (€{row['period1']:,.2f} vs €{avg_val:,.2f} keskiarvo)\n"
        
        # LLM prompt
        system_prompt = """Olet talousneuvoja, joka analysoi kulutustottumuksia. 
Luo ytimekäs, toiminnallinen yhteenveto (2-4 lausetta), joka korostaa:
1. Merkittävimmät kulutusmuutokset ja mitkä kaupat/merchantit selittävät nousua
2. Keskeiset säästömahdollisuudet
3. Mielenkiintoinen havainto tarkastelujaksolta

Ole tarkka numeroissa, kategorioissa ja kaupoissa. Mainitse konkreettisesti mitkä merchantit selittävät kulutuksen nousua. Kirjoita suomeksi."""
        
        user_prompt = f"""Analysoi tämä kulutusdata ja anna älykkäitä oivalluksia:

{data_summary}

Anna lyhyt, toiminnallinen yhteenveto suomeksi."""
        
        # Format messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = get_llm_response(
            messages=messages,
            api_key=api_key,
            model="gpt-4o-mini"
        )
        
        # Check if response is valid
        if response and isinstance(response, str) and response.strip():
            return response.strip()
        else:
            return None
    except ImportError as import_err:
        # Import error - OpenAI package not available
        import sys
        python_path = sys.executable
        return f"Error: OpenAI package is not installed in the current Python environment. Python: {python_path}. Install it with: pip install openai. Details: {str(import_err)}"
    except Exception as e:
        # Return error message for debugging
        error_msg = str(e)
        # Check if it's an API error from get_llm_response
        if "OpenAI API error" in error_msg:
            return f"Error: {error_msg}"
        else:
            return f"Error: {error_msg}"


def identify_savings_opportunities(df: pd.DataFrame, changes_df: pd.DataFrame, period_months: int = 1, custom_start: str = None, custom_end: str = None, custom_period1_start: str = None, custom_period1_end: str = None):
    """Identify categories with savings potential."""
    if changes_df is None or changes_df.empty:
        return []
    
    opportunities = []
    seen_categories = set()  # Track categories to avoid duplicates
    
    # High spending categories (above average +30%) - prioritize these
    high_spending = changes_df[changes_df['vs_avg_pct'] > 30].copy()
    for _, row in high_spending.iterrows():
        category = row['category']
        if category not in seen_categories:
            seen_categories.add(category)
            # Calculate savings potential (15% reduction)
            savings_15 = row['period1'] * 0.15
            top_merchants = get_top_merchants_by_category(df, category, period_months, custom_start, custom_end, custom_period1_start, custom_period1_end)
            opportunities.append({
                'type': 'high_spending',
                'category': category,
                'title': 'Exceptionally High Spending',
                'description': f"{category} category is {row['vs_avg_pct']:.0f}% higher than average",
                'current': row['period1'],
                'average': row['average'],
                'vs_avg_pct': row['vs_avg_pct'],
                'savings_potential_15': savings_15,
                'severity': 'high' if row['vs_avg_pct'] > 50 else 'medium',
                'top_merchants': top_merchants
            })
    
    # Rapidly increasing categories (only if not already added as high spending)
    increasing = changes_df[changes_df['change_pct'] > 20].copy()
    for _, row in increasing.iterrows():
        category = row['category']
        if category not in seen_categories:
            seen_categories.add(category)
            savings_15 = row['period1'] * 0.15
            top_merchants = get_top_merchants_by_category(df, category, period_months, custom_start, custom_end, custom_period1_start, custom_period1_end)
            change_abs = row['period1'] - row['period2']
            opportunities.append({
                'type': 'increasing',
                'category': category,
                'title': 'Spending Increased Significantly',
                'description': f"{category} category spending has increased {row['change_pct']:.2f}% from comparison period ({change_abs:,.2f}€)",
                'current': row['period1'],
                'previous': row['period2'],
                'change_pct': row['change_pct'],
                'change_abs': change_abs,
                'average': row['average'],
                'savings_potential_15': savings_15,
                'severity': 'high' if row['change_pct'] > 50 else 'medium',
                'top_merchants': top_merchants
            })
    
    return opportunities


def generate_monthly_summary(df: pd.DataFrame):
    """Generate monthly spending summary."""
    if 'date' not in df.columns or 'adjusted_amount' not in df.columns:
        return None
    
    monthly = df.groupby([df['date'].dt.to_period('M')])['adjusted_amount'].sum().reset_index()
    monthly['date'] = monthly['date'].astype(str)
    monthly = monthly.sort_values('date')
    
    if len(monthly) < 2:
        return None
    
    avg_monthly = monthly['adjusted_amount'].mean()
    last_month_val = monthly['adjusted_amount'].iloc[-1]
    prev_month_val = monthly['adjusted_amount'].iloc[-2]
    highest_month_val = monthly['adjusted_amount'].max()
    lowest_month_val = monthly['adjusted_amount'].min()
    highest_month = monthly.loc[monthly['adjusted_amount'].idxmax(), 'date']
    lowest_month = monthly.loc[monthly['adjusted_amount'].idxmin(), 'date']
    
    change_pct = ((last_month_val - prev_month_val) / prev_month_val * 100) if prev_month_val > 0 else 0
    
    return {
        'last_month': last_month_val,
        'prev_month': prev_month_val,
        'average': avg_monthly,
        'change_pct': change_pct,
        'highest_month': highest_month_val,
        'lowest_month': lowest_month_val,
        'highest_month_name': highest_month,
        'lowest_month_name': lowest_month
    }


# Budget helper functions
def load_budgets() -> dict:
    """Load budgets from session state or return defaults."""
    if 'budgets' not in st.session_state:
        st.session_state.budgets = {}
    return st.session_state.budgets


def save_budgets(budgets: dict):
    """Save budgets to session state."""
    st.session_state.budgets = budgets


def get_budget_vs_actual(df: pd.DataFrame, budgets: dict, month: str = None) -> pd.DataFrame:
    """Calculate budget vs actual spending by category."""
    if 'category' not in df.columns or 'adjusted_amount' not in df.columns:
        return pd.DataFrame()
    
    df_temp = df.copy()
    if month:
        # Filter by month if specified
        df_temp['month_str'] = df_temp['date'].dt.to_period('M').astype(str)
        df_temp = df_temp[df_temp['month_str'] == month]
    
    # Calculate actual spending by category
    actual = df_temp.groupby('category')['adjusted_amount'].sum().reset_index()
    actual.columns = ['category', 'actual']
    
    # Merge with budgets
    budget_df = pd.DataFrame(list(budgets.items()), columns=['category', 'budget'])
    result = budget_df.merge(actual, on='category', how='outer').fillna(0)
    
    # Calculate difference and percentage
    result['difference'] = result['budget'] - result['actual']
    result['percentage'] = (result['actual'] / result['budget'] * 100).replace([float('inf'), float('-inf')], 0)
    result['status'] = result.apply(
        lambda row: 'over' if row['actual'] > row['budget'] else 'under' if row['budget'] > 0 else 'no_budget',
        axis=1
    )
    
    return result.sort_values('actual', ascending=False)


def identify_recurring_expenses(df: pd.DataFrame, months: int = 6, min_count: int = 3) -> pd.DataFrame:
    """Identify recurring expenses based on merchant patterns."""
    if df.empty or 'merchant' not in df.columns or 'date' not in df.columns:
        return pd.DataFrame()
    
    df_temp = df.copy()
    df_temp['date'] = pd.to_datetime(df_temp['date'])
    df_temp['dt'] = df_temp['date']
    if 'time' in df_temp.columns:
        time = pd.to_timedelta(df_temp['time'].astype(str), errors='coerce').fillna(pd.Timedelta(0))
        df_temp['dt'] = df_temp['date'] + time
    
    amount_col = 'adjusted_amount' if 'adjusted_amount' in df_temp.columns else 'amount'
    
    max_dt = df_temp['dt'].max()
    if pd.isna(max_dt):
        return pd.DataFrame()
    
    start = max_dt - pd.DateOffset(months=months)
    sub = df_temp[df_temp['dt'] >= start].copy()
    sub['ym'] = sub['dt'].dt.to_period('M').astype(str)
    
    # Get most common category for each merchant (in case merchant appears in multiple categories)
    merchant_category = sub.groupby('merchant')['category'].apply(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0] if len(x) > 0 else 'Unknown').reset_index()
    merchant_category.columns = ['merchant', 'category']
    
    # Group by merchant
    g = sub.groupby('merchant', dropna=False).agg(
        txn_count=(amount_col, 'count'),
        sum_eur=(amount_col, 'sum'),
        months_active=('ym', 'nunique'),
        avg_per_month=(amount_col, lambda x: x.sum() / sub['ym'].nunique() if sub['ym'].nunique() > 0 else 0)
    ).reset_index()
    
    # Merge with category
    g = g.merge(merchant_category, on='merchant', how='left')
    
    # Filter: at least min_count transactions and active in at least 2 months
    g = g[(g['txn_count'] >= min_count) & (g['months_active'] >= 2)].sort_values(
        'avg_per_month', ascending=False  # Sort by avg_per_month descending
    )
    
    return g[['merchant', 'category', 'txn_count', 'months_active', 'sum_eur', 'avg_per_month']].head(30)


def forecast_spending(df: pd.DataFrame, months_ahead: int = 3) -> pd.DataFrame:
    """Forecast future spending based on historical trends."""
    if df.empty or 'date' not in df.columns or 'adjusted_amount' not in df.columns:
        return pd.DataFrame()
    
    df_temp = df.copy()
    df_temp['date'] = pd.to_datetime(df_temp['date'])
    df_temp['month'] = df_temp['date'].dt.to_period('M')
    
    # Calculate monthly totals
    monthly = df_temp.groupby('month')['adjusted_amount'].sum().reset_index()
    monthly = monthly.sort_values('month')
    
    if len(monthly) < 2:
        return pd.DataFrame()
    
    # Simple linear trend (can be improved with more sophisticated forecasting)
    monthly['month_num'] = range(len(monthly))
    x = monthly['month_num'].values
    y = monthly['adjusted_amount'].values
    
    # Linear regression
    if len(x) > 1:
        slope = (len(x) * (x * y).sum() - x.sum() * y.sum()) / (len(x) * (x * x).sum() - x.sum() * x.sum())
        intercept = y.mean() - slope * x.mean()
        
        # Get last month period to calculate future months
        last_month_period = monthly['month'].iloc[-1]
        last_month_date = last_month_period.to_timestamp()
        
        # Forecast future months with actual month names
        forecasts = []
        for i in range(1, months_ahead + 1):
            forecast_value = intercept + slope * (len(monthly) - 1 + i)
            # Calculate next month date
            next_month_date = last_month_date + pd.DateOffset(months=i)
            next_month_period = pd.Period(next_month_date, freq='M')
            # Format as "MMM YYYY" (e.g., "Jan 2026")
            month_str = next_month_period.strftime('%b %Y')
            
            forecasts.append({
                'month': month_str,
                'month_period': str(next_month_period),
                'amount': max(0, forecast_value)  # Don't allow negative
            })
        
        return pd.DataFrame(forecasts)
    
    return pd.DataFrame()


# Main app
st.title("💰 Finance Transaction Manager")

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    # CSV File Upload
    st.subheader("📤 Upload CSV File")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        key="csv_uploader",
        help="Upload a CSV file to process transactions"
    )
    
    if uploaded_file is not None:
        if st.button("🔄 Process Uploaded File", use_container_width=True, type="primary"):
            try:
                with st.spinner("Processing uploaded CSV file..."):
                    # Read CSV from uploaded file
                    df_uploaded = pd.read_csv(uploaded_file, delimiter=',', quotechar='"', encoding='utf-8')
                    
                    # Strip column names
                    df_uploaded.columns = [col.strip() for col in df_uploaded.columns]
                    
                    # Process through pipeline
                    df_processed = process_dataframe(df_uploaded, start_date='2025-01-01', verbose=False)
                    
                    # Save to session state
                    st.session_state.df = df_processed
                    st.session_state.edited = False
                    
                    st.success(f"✅ Processed {len(df_processed)} transactions!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
    
    st.divider()
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        refresh_data()
    
    st.divider()
    
    # Check for new files
    new_files = detect_new_files()
    if new_files:
        st.warning(f"⚠️ {len(new_files)} new file(s) detected")
        if st.button("Process New Files", use_container_width=True):
            refresh_data()
    else:
        st.success("✅ All files processed")
    
    st.divider()
    
    # Data info
    if not st.session_state.df.empty and len(st.session_state.df) > 0:
        st.metric("Total Transactions", len(st.session_state.df))
        if 'date' in st.session_state.df.columns and not st.session_state.df['date'].empty:
            try:
                date_range = f"{st.session_state.df['date'].min().date()} to {st.session_state.df['date'].max().date()}"
                st.caption(f"Date range: {date_range}")
            except:
                pass
        
        amount_col = 'adjusted_amount' if 'adjusted_amount' in st.session_state.df.columns else 'amount'
        if amount_col in st.session_state.df.columns:
            total_amount = st.session_state.df[amount_col].sum()
            st.metric("Total Amount", f"€{total_amount:,.2f}")

# Load data if not loaded
if st.session_state.df.empty:
    # Try to process default CSV file if it exists
    from src.config import DEFAULT_CSV_PATH
    from src.pipeline import process_file
    if DEFAULT_CSV_PATH and os.path.exists(DEFAULT_CSV_PATH):
        with st.spinner("Processing CSV file..."):
            try:
                st.session_state.df = process_file(DEFAULT_CSV_PATH, start_date='2025-01-01', verbose=False)
                st.success("✅ CSV file processed successfully!")
                st.rerun()
            except Exception as e:
                st.warning(f"Could not process CSV: {e}")

if st.session_state.df.empty:
    st.info("📋 No data found. Please upload a CSV file using the sidebar (📤 Upload CSV File) or process CSV files from the sidebar (🔄 Refresh Data).")
    st.warning("💡 **Tip:** Use the sidebar on the left to upload or process CSV files.")
else:
    df = st.session_state.df.copy()
    
    # Tabs - järjestetty: Dashboard, Analytics, Transactions, Edit Categories, Budget, AI Assistant
    tab_names = ["📊 Dashboard", "📈 Analytics", "📋 Transactions", "✏️ Edit Categories", "💰 Budget"]
    if AI_ASSISTANT_AVAILABLE:
        tab_names.append("🤖 AI Assistant")
    else:
        tab_names.append("🤖 AI (Ei saatavilla)")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_names)
    
    with tab1:
        st.header("Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = df.get('adjusted_amount', df.get('amount', pd.Series([0]))).sum()
            st.metric("Total Spending", f"€{total:,.2f}")
        
        with col2:
            if 'year' in df.columns and 'month' in df.columns:
                if 'adjusted_amount' in df.columns:
                    monthly_sums = df.groupby(['year', 'month'])['adjusted_amount'].sum()
                    avg_monthly = monthly_sums.mean()
                    median_monthly = monthly_sums.median()
                elif 'amount' in df.columns:
                    monthly_sums = df.groupby(['year', 'month'])['amount'].sum()
                    avg_monthly = monthly_sums.mean()
                    median_monthly = monthly_sums.median()
                else:
                    avg_monthly = 0
                    median_monthly = 0
            else:
                # Calculate average monthly without year/month columns
                if 'adjusted_amount' in df.columns:
                    avg_monthly = df['adjusted_amount'].sum() / 12  # Rough estimate
                    median_monthly = df['adjusted_amount'].sum() / 12  # Rough estimate
                elif 'amount' in df.columns:
                    avg_monthly = df['amount'].sum() / 12
                    median_monthly = df['amount'].sum() / 12
                else:
                    avg_monthly = 0
                    median_monthly = 0
            st.metric("Avg Monthly", f"€{avg_monthly:,.2f}")
            st.metric("Median Monthly", f"€{median_monthly:,.2f}")
        
        with col3:
            if 'merchant' in df.columns:
                unique_merchants = df['merchant'].nunique()
            else:
                unique_merchants = 0
            st.metric("Unique Merchants", unique_merchants)
        
        with col4:
            if 'card' in df.columns:
                top_card = df['card'].value_counts().index[0] if not df['card'].value_counts().empty else "N/A"
                st.metric("Top Card", top_card)
        
        st.divider()
        
        # Monthly spending chart with drill-down
        if 'date' in df.columns and 'adjusted_amount' in df.columns:
            monthly = df.groupby([df['date'].dt.to_period('M')])['adjusted_amount'].sum().reset_index()
            monthly['date'] = monthly['date'].astype(str)
            monthly = monthly.sort_values('date')
            
            # Calculate average monthly spending
            avg_monthly_spending = monthly['adjusted_amount'].mean()
            
            # Create interactive bar chart
            fig = px.bar(
                monthly,
                x='date',
                y='adjusted_amount',
                title="📅 Monthly Spending (Select month below to see details)",
                labels={'date': 'Month', 'adjusted_amount': 'Amount (€)'},
                text=[f"€{val:,.0f}" for val in monthly['adjusted_amount']]
            )
            fig.update_traces(
                marker_color='#1f77b4',
                marker_line_color='darkblue',
                marker_line_width=1.5,
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Amount: €%{y:,.2f}<extra></extra>'
            )
            
            # Add average line (dashed, dark gray)
            fig.add_hline(
                y=avg_monthly_spending,
                line_dash="dash",
                line_color="darkgray",
                line_width=2,
                annotation_text=f"Avg: €{avg_monthly_spending:,.2f}",
                annotation_position="right",
                annotation_font_size=12,
                annotation_font_color="darkgray"
            )
            
            fig.update_layout(
                height=500,  # Taller chart
                xaxis_tickangle=-45,
                hovermode='x unified'
            )
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, key="monthly_chart")
            
            # Month selector for drill-down (newest first)
            st.caption("💡 Select a month below to see detailed breakdown")
            month_list = monthly['date'].tolist()
            month_list_reversed = month_list[::-1]  # Reverse to show newest first
            month_options = ['All'] + month_list_reversed
            selected_month_idx = st.selectbox(
                "Select month for details:",
                options=range(len(month_options)),
                format_func=lambda x: month_options[x],
                index=0 if not st.session_state.selected_month else (month_options.index(st.session_state.selected_month) if st.session_state.selected_month in month_options else 0),
                key="month_selector"
            )
            
            if selected_month_idx > 0:
                selected_month_str = month_options[selected_month_idx]
                st.session_state.selected_month = selected_month_str
            else:
                selected_month_str = None
                st.session_state.selected_month = None
            
            # Display monthly breakdown if month is selected
            if selected_month_str:
                st.markdown(f"## 📊 Monthly Summary: {selected_month_str}")
                st.divider()
                
                # Filter data for selected month
                month_df = df[df['date'].dt.to_period('M').astype(str) == selected_month_str]
                
                if not month_df.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        month_total = month_df['adjusted_amount'].sum()
                        st.metric("Month Total", f"€{month_total:,.2f}")
                    with col2:
                        month_count = len(month_df)
                        st.metric("Transactions", month_count)
                    with col3:
                        month_avg = month_df['adjusted_amount'].mean()
                        st.metric("Avg Transaction", f"€{month_avg:,.2f}")
                    
                    # Category breakdown for selected month
                    if 'category' in month_df.columns:
                        st.subheader("By Category")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            month_cat = month_df.groupby('category')['adjusted_amount'].sum().sort_values(ascending=False)
                            if not month_cat.empty:
                                fig_cat = px.pie(
                                    month_cat,
                                    values=month_cat.values,
                                    names=month_cat.index,
                                    title=f"Categories in {selected_month_str}",
                                    hole=0.4
                                )
                                fig_cat.update_traces(
                                    textposition='inside',
                                    textinfo='percent+label',
                                    hovertemplate='<b>%{label}</b><br>Amount: €%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
                                )
                                fig_cat.update_layout(height=500)
                                st.plotly_chart(fig_cat, use_container_width=True)
                        
                        with col2:
                            if '2nd category' in month_df.columns:
                                # Get top subcategories
                                month_subcat = month_df.groupby('2nd category')['adjusted_amount'].sum().sort_values(ascending=False).head(10)
                                if not month_subcat.empty:
                                    # Group by subcategory and merchant for stacked bars
                                    if 'merchant' in month_df.columns:
                                        subcat_merchant = month_df[
                                            month_df['2nd category'].isin(month_subcat.index)
                                        ].groupby(['2nd category', 'merchant'])['adjusted_amount'].sum().reset_index()
                                        
                                        # Create pivot table for stacked bars
                                        pivot_subcat = subcat_merchant.pivot_table(
                                            index='2nd category',
                                            columns='merchant',
                                            values='adjusted_amount',
                                            aggfunc='sum',
                                            fill_value=0
                                        )
                                        
                                        # Reorder rows to match sorted subcategories (largest to smallest)
                                        # month_subcat is already sorted descending, so reindex maintains that order
                                        pivot_subcat = pivot_subcat.reindex(month_subcat.index)
                                        
                                        # Create stacked bar chart
                                        fig_subcat = go.Figure()
                                        
                                        # Add a bar for each merchant
                                        colors = px.colors.qualitative.Set3
                                        for i, merchant in enumerate(pivot_subcat.columns):
                                            fig_subcat.add_trace(go.Bar(
                                                name=merchant,
                                                y=pivot_subcat.index,
                                                x=pivot_subcat[merchant],
                                                orientation='h',
                                                marker_color=colors[i % len(colors)],
                                                hovertemplate=f'<b>{merchant}</b><br>%{{y}}<br>Amount: €%{{x:,.2f}}<extra></extra>'
                                            ))
                                        
                                        # Add text annotations showing total for each subcategory
                                        # Calculate totals for each subcategory
                                        subcat_totals = pivot_subcat.sum(axis=1)
                                        
                                        # Add text annotations
                                        annotations = []
                                        for subcat, total in subcat_totals.items():
                                            annotations.append(dict(
                                                xref='x',
                                                yref='y',
                                                x=total,
                                                y=subcat,
                                                text=f'€{total:,.2f}',
                                                showarrow=False,
                                                xanchor='left',
                                                yanchor='middle',
                                                font=dict(size=11, color='white'),
                                                bgcolor='rgba(0,0,0,0.5)',
                                                bordercolor='rgba(255,255,255,0.3)',
                                                borderwidth=1,
                                                xshift=10
                                            ))
                                        
                                        fig_subcat.update_layout(
                                            title=f"Top Subcategories in {selected_month_str}",
                                            xaxis_title='Amount (€)',
                                            yaxis_title='Subcategory',
                                            yaxis=dict(autorange='reversed'),  # Largest at top
                                            barmode='stack',
                                            height=500,
                                            annotations=annotations,
                                            legend=dict(
                                                orientation="v",
                                                yanchor="top",
                                                y=1,
                                                xanchor="left",
                                                x=1.02
                                            )
                                        )
                                    else:
                                        # Fallback if merchant column doesn't exist
                                        fig_subcat = px.bar(
                                            x=month_subcat.values,
                                            y=month_subcat.index,
                                            orientation='h',
                                            title=f"Top Subcategories in {selected_month_str}",
                                            labels={'x': 'Amount (€)', 'y': 'Subcategory'},
                                            text=[f"€{val:,.2f}" for val in month_subcat.values]
                                        )
                                        fig_subcat.update_traces(textposition='outside')
                                        fig_subcat.update_layout(height=500)
                                    st.plotly_chart(fig_subcat, use_container_width=True)
                    
                    # Top merchants for selected month
                    if 'merchant' in month_df.columns:
                        st.subheader("Top Merchants")
                        top_merchants_month = month_df.groupby('merchant')['adjusted_amount'].sum().sort_values(ascending=False).head(10)
                        if not top_merchants_month.empty:
                            fig_merch = px.bar(
                                x=top_merchants_month.values,
                                y=top_merchants_month.index,
                                orientation='h',
                                title=f"Top 10 Merchants in {selected_month_str}",
                                labels={'x': 'Amount (€)', 'y': 'Merchant'}
                            )
                            fig_merch.update_layout(
                                height=400,
                                yaxis=dict(autorange='reversed')  # Largest at top
                            )
                            st.plotly_chart(fig_merch, use_container_width=True)
                    
                    # Daily spending trend for selected month
                    st.subheader("Daily Spending Trend")
                    daily = month_df.groupby(month_df['date'].dt.date)['adjusted_amount'].sum().reset_index()
                    daily.columns = ['date', 'amount']
                    fig_daily = px.line(
                        daily,
                        x='date',
                        y='amount',
                        title=f"Daily Spending in {selected_month_str}",
                        labels={'date': 'Date', 'amount': 'Amount (€)'},
                        markers=True
                    )
                    fig_daily.update_traces(
                        line_color='#2ca02c',
                        line_width=2,
                        marker_size=8
                    )
                    fig_daily.update_layout(height=300)
                    st.plotly_chart(fig_daily, use_container_width=True)
                    
                    # Clear selection button
                    if st.button("Clear Month Selection"):
                        st.session_state.selected_month = None
                        st.rerun()
        
        # Category breakdown with drill-down
        if 'category' in df.columns and 'adjusted_amount' in df.columns:
            st.markdown("## 💰 Total Spending")
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                category_sum = df.groupby('category')['adjusted_amount'].sum().sort_values(ascending=False)
                if not category_sum.empty:
                    fig = px.pie(
                        values=category_sum.values,
                        names=category_sum.index,
                        title="💰 Total Spending By Category",
                        hole=0.4
                    )
                    fig.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        textfont=dict(size=14),  # Larger text on pie chart
                        hovertemplate='<b>%{label}</b><br>Amount: €%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
                    )
                    fig.update_layout(
                        title_font=dict(size=18)  # Larger chart title
                    )
                    # Remove height to use default size (smaller)
                    st.plotly_chart(fig, use_container_width=True, key="category_chart")
            
            with col2:
                if '2nd category' in df.columns and 'adjusted_amount' in df.columns:
                    subcat_sum = df.groupby('2nd category')['adjusted_amount'].sum().sort_values(ascending=False)
                    if not subcat_sum.empty:
                        fig = px.bar(
                            x=subcat_sum.values,
                            y=subcat_sum.index,
                            orientation='h',
                            title="🏷️ Subcategories",
                            labels={'x': 'Amount (€)', 'y': 'Subcategory'},
                            text=[f"€{val:,.0f}" for val in subcat_sum.values]
                        )
                        fig.update_traces(
                            textposition='outside',
                            textfont=dict(size=14)  # Larger text on bars
                        )
                        fig.update_traces(
                            marker_color='#ff7f0e',
                            hovertemplate='<b>%{y}</b><br>Amount: €%{x:,.2f}<extra></extra>'
                        )
                        fig.update_layout(
                            height=600,  # Taller chart
                            yaxis=dict(
                                autorange='reversed',  # Largest at top
                                tickfont=dict(size=13)  # Larger y-axis labels
                            ),
                            xaxis=dict(
                                title_font=dict(size=14),  # Larger x-axis title
                                tickfont=dict(size=12)  # Larger x-axis labels
                            ),
                            title_font=dict(size=18)  # Larger chart title
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Monthly Average by Subcategory chart (full width, below the two columns)
            if '2nd category' in df.columns and 'adjusted_amount' in df.columns and 'date' in df.columns:
                # Calculate total per subcategory
                subcat_totals = df.groupby('2nd category')['adjusted_amount'].sum()
                
                # Count number of unique months in the data
                num_months = df['date'].dt.to_period('M').nunique()
                if num_months > 0:
                    # Calculate average per subcategory (total / number of months)
                    subcat_avg = (subcat_totals / num_months).sort_values(ascending=False)
                    
                    if not subcat_avg.empty:
                        fig_total = px.bar(
                            x=subcat_avg.values,
                            y=subcat_avg.index,
                            orientation='h',
                            title="💰 Monthly Average by Subcategory",
                            labels={'x': 'Average Amount (€)', 'y': 'Subcategory'},
                            text=[f"€{val:,.0f}" for val in subcat_avg.values]
                        )
                        fig_total.update_traces(
                            textposition='outside',
                            textfont=dict(size=14),  # Larger text on bars
                            marker_color='#2ca02c',
                            hovertemplate='<b>%{y}</b><br>Monthly Avg: €%{x:,.2f}<extra></extra>'
                        )
                        fig_total.update_layout(
                            height=600,
                            yaxis=dict(
                                autorange='reversed',  # Largest at top
                                tickfont=dict(size=13)  # Larger y-axis labels
                            ),
                            xaxis=dict(
                                title_font=dict(size=14),  # Larger x-axis title
                                tickfont=dict(size=12)  # Larger x-axis labels
                            ),
                            title_font=dict(size=18)  # Larger chart title
                        )
                        st.plotly_chart(fig_total, use_container_width=True)
                        
                        # Category selector for drill-down (moved below Monthly Average chart)
                        st.caption("💡 Select a category below to see detailed breakdown")
                        cat_options = ['All'] + sorted(category_sum.index.tolist())
                        selected_cat_idx = st.selectbox(
                            "Select category for details:",
                            options=range(len(cat_options)),
                            format_func=lambda x: cat_options[x],
                            index=0 if not st.session_state.selected_category else (cat_options.index(st.session_state.selected_category) if st.session_state.selected_category in cat_options else 0),
                            key="category_selector"
                        )
                        
                        if selected_cat_idx > 0:
                            st.session_state.selected_category = cat_options[selected_cat_idx]
                        else:
                            st.session_state.selected_category = None
            
            # Show category details if selected
            if st.session_state.selected_category:
                st.subheader(f"📂 Details for: {st.session_state.selected_category}")
                cat_df = df[df['category'] == st.session_state.selected_category]
                
                if not cat_df.empty:
                    # Subcategory pie chart and Top Merchants side by side
                    subcat_col, merch_col = st.columns(2)
                    
                    with subcat_col:
                        # Show subcategory pie chart for selected category
                        if '2nd category' in df.columns:
                            subcat_sum_temp = cat_df.groupby('2nd category')['adjusted_amount'].sum().sort_values(ascending=False)
                            if not subcat_sum_temp.empty:
                                fig_subcat_pie = px.pie(
                                    subcat_sum_temp,
                                    values=subcat_sum_temp.values,
                                    names=subcat_sum_temp.index,
                                    title=f"Subcategories in {st.session_state.selected_category}",
                                    hole=0.4
                                )
                                fig_subcat_pie.update_traces(
                                    textposition='inside',
                                    textinfo='percent+label',
                                    hovertemplate='<b>%{label}</b><br>Amount: €%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
                                )
                                fig_subcat_pie.update_layout(height=600)  # Larger subcategory pie chart
                                st.plotly_chart(fig_subcat_pie, use_container_width=True)
                    
                    with merch_col:
                        # Top merchants in category
                        if 'merchant' in cat_df.columns:
                            top_merchants_cat = cat_df.groupby('merchant')['adjusted_amount'].sum().sort_values(ascending=False).head(10)
                            if not top_merchants_cat.empty:
                                fig_merch_cat = px.bar(
                                    x=top_merchants_cat.values,
                                    y=top_merchants_cat.index,
                                    orientation='h',
                                    title=f"Top 10 Merchants: {st.session_state.selected_category}",
                                    labels={'x': 'Amount (€)', 'y': 'Merchant'}
                                )
                                fig_merch_cat.update_layout(
                                    height=600,
                                    yaxis=dict(autorange='reversed')  # Largest at top
                                )
                                st.plotly_chart(fig_merch_cat, use_container_width=True)
                    
                    # Calculate monthly stats for category
                    if 'date' in cat_df.columns:
                        cat_monthly_sums = cat_df.groupby([cat_df['date'].dt.to_period('M')])['adjusted_amount'].sum()
                        cat_monthly_avg = cat_monthly_sums.mean()
                        cat_monthly_median = cat_monthly_sums.median()
                    else:
                        cat_monthly_avg = 0
                        cat_monthly_median = 0
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        cat_total = cat_df['adjusted_amount'].sum()
                        st.metric("Category Total", f"€{cat_total:,.2f}")
                    with col2:
                        cat_pct = (cat_total / df['adjusted_amount'].sum()) * 100
                        st.metric("% of Total", f"{cat_pct:.1f}%")
                    with col3:
                        cat_count = len(cat_df)
                        st.metric("Transactions", cat_count)
                    with col4:
                        st.metric("Monthly Average", f"€{cat_monthly_avg:,.2f}")
                    with col5:
                        st.metric("Monthly Median", f"€{cat_monthly_median:,.2f}")
                    
                    # Monthly trend for selected category
                    cat_monthly = cat_df.groupby([cat_df['date'].dt.to_period('M')])['adjusted_amount'].sum().reset_index()
                    cat_monthly['date'] = cat_monthly['date'].astype(str)
                    cat_monthly = cat_monthly.sort_values('date')
                    
                    fig_cat_trend = px.line(
                        cat_monthly,
                        x='date',
                        y='adjusted_amount',
                        title=f"Monthly Trend: {st.session_state.selected_category}",
                        labels={'date': 'Month', 'adjusted_amount': 'Amount (€)'},
                        markers=True
                    )
                    fig_cat_trend.update_traces(
                        line_color='#d62728',
                        line_width=3,
                        marker_size=10
                    )
                    fig_cat_trend.update_layout(height=300)
                    st.plotly_chart(fig_cat_trend, use_container_width=True)
                    
                    # Monthly average per subcategory chart
                    if '2nd category' in cat_df.columns and 'date' in cat_df.columns:
                        st.subheader("Monthly Average per Subcategory")
                        # Calculate total per subcategory and divide by number of months
                        subcat_totals = cat_df.groupby('2nd category')['adjusted_amount'].sum()
                        
                        # Count number of unique months in the data
                        num_months = cat_df['date'].dt.to_period('M').nunique()
                        if num_months > 0:
                            # Calculate average per subcategory (total / number of months)
                            subcat_avg = (subcat_totals / num_months).sort_values(ascending=False)
                            
                            if not subcat_avg.empty:
                                fig_subcat_avg = px.bar(
                                    x=subcat_avg.values,
                                    y=subcat_avg.index,
                                    orientation='h',
                                    title=f"Monthly Average per Subcategory: {st.session_state.selected_category}",
                                    labels={'x': 'Average Amount (€)', 'y': 'Subcategory'}
                                )
                                fig_subcat_avg.update_traces(
                                    marker_color='#2ca02c',
                                    hovertemplate='<b>%{y}</b><br>Monthly Avg: €%{x:,.2f}<extra></extra>'
                                )
                                fig_subcat_avg.update_layout(
                                    height=350,
                                    yaxis=dict(autorange='reversed')  # Largest at top
                                )
                                st.plotly_chart(fig_subcat_avg, use_container_width=True)
                    
                    # Monthly Average per Merchant chart (at the bottom of the page)
                    if 'merchant' in cat_df.columns and 'date' in cat_df.columns:
                        # Calculate total per merchant
                        merchant_totals = cat_df.groupby('merchant')['adjusted_amount'].sum()
                        
                        # Count number of unique months in the data
                        num_months_merch = cat_df['date'].dt.to_period('M').nunique()
                        if num_months_merch > 0:
                            # Calculate average per merchant (total / number of months)
                            merchant_avg = (merchant_totals / num_months_merch).sort_values(ascending=False).head(20)
                            
                            if not merchant_avg.empty:
                                fig_merch_avg = px.bar(
                                    x=merchant_avg.values,
                                    y=merchant_avg.index,
                                    orientation='h',
                                    title=f"💰 Monthly Average per Merchant: {st.session_state.selected_category}",
                                    labels={'x': 'Average Amount (€)', 'y': 'Merchant'},
                                    text=[f"€{val:,.0f}" for val in merchant_avg.values]
                                )
                                fig_merch_avg.update_traces(
                                    textposition='outside',
                                    textfont=dict(size=14),  # Larger text on bars
                                    marker_color='#9467bd',
                                    hovertemplate='<b>%{y}</b><br>Monthly Avg: €%{x:,.2f}<extra></extra>'
                                )
                                fig_merch_avg.update_layout(
                                    height=600,
                                    yaxis=dict(
                                        autorange='reversed',  # Largest at top
                                        tickfont=dict(size=13)  # Larger y-axis labels
                                    ),
                                    xaxis=dict(
                                        title_font=dict(size=14),  # Larger x-axis title
                                        tickfont=dict(size=12)  # Larger x-axis labels
                                    ),
                                    title_font=dict(size=18)  # Larger chart title
                                )
                                st.plotly_chart(fig_merch_avg, use_container_width=True)
                    
                    if st.button("Clear Category Selection"):
                        st.session_state.selected_category = None
                        st.rerun()
        
        st.divider()
        
        # Forecast section
        if 'date' in df.columns and 'adjusted_amount' in df.columns:
            st.markdown("#### 📈 Spending Forecast")
            forecast_months = st.slider("Forecast months ahead", 1, 6, 3, key="forecast_months")
            
            forecast_df = forecast_spending(df, months_ahead=forecast_months)
            
            if not forecast_df.empty:
                # Get historical data for comparison
                df_temp = df.copy()
                df_temp['date'] = pd.to_datetime(df_temp['date'])
                df_temp['month'] = df_temp['date'].dt.to_period('M')
                historical = df_temp.groupby('month')['adjusted_amount'].sum().reset_index()
                historical = historical.sort_values('month').tail(6)  # Last 6 months
                
                # Format historical months as "MMM YYYY" (e.g., "Jul 2025")
                historical['month_str'] = historical['month'].apply(lambda p: p.strftime('%b %Y'))
                
                # Create visualization
                fig_forecast = go.Figure()
                
                # Historical data
                fig_forecast.add_trace(go.Scatter(
                    x=historical['month_str'],
                    y=historical['adjusted_amount'],
                    mode='lines+markers',
                    name='Historical',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=8)
                ))
                
                # Forecast data
                fig_forecast.add_trace(go.Scatter(
                    x=forecast_df['month'],
                    y=forecast_df['amount'],
                    mode='lines+markers',
                    name='Forecast',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    marker=dict(size=8, symbol='diamond')
                ))
                
                fig_forecast.update_layout(
                    title="Spending Forecast (Historical vs Projected)",
                    xaxis_title="Month",
                    yaxis_title="Amount (€)",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_historical = historical['adjusted_amount'].mean()
                    st.metric("Avg Historical (6 months)", f"€{avg_historical:,.2f}")
                with col2:
                    avg_forecast = forecast_df['amount'].mean()
                    st.metric("Avg Forecast", f"€{avg_forecast:,.2f}")
                with col3:
                    change_pct = ((avg_forecast - avg_historical) / avg_historical * 100) if avg_historical > 0 else 0
                    st.metric("Projected Change", f"{change_pct:+.1f}%")
            else:
                st.info("Not enough historical data for forecasting. Need at least 2 months of data.")
        
        st.divider()
        
        # Simple pivot table by category (moved to bottom)
        if 'category' in df.columns and 'adjusted_amount' in df.columns and 'month' in df.columns:
            with st.expander("📊 Spending Summary by Category and Month", expanded=False):
                try:
                    # Get year from data (use most common year or first available)
                    if 'year' in df.columns:
                        year = int(df['year'].mode()[0] if not df['year'].mode().empty else df['year'].iloc[0])
                    else:
                        # Fallback to current year or extract from date
                        if 'date' in df.columns:
                            year = int(df['date'].dt.year.mode()[0] if not df['date'].dt.year.mode().empty else df['date'].dt.year.iloc[0])
                        else:
                            year = 2025  # Default
                    
                    # Create simple pivot table by category only
                    pivot_df = df.pivot_table(
                        values='adjusted_amount',
                        index='category',
                        columns='month',
                        aggfunc='sum',
                        fill_value=0
                    )
                    
                    # Sort columns (months 1-12) and rename to include year
                    numeric_cols = [col for col in pivot_df.columns if isinstance(col, (int, float))]
                    if numeric_cols:
                        numeric_cols_sorted = sorted(numeric_cols)
                        other_cols = [col for col in pivot_df.columns if col not in numeric_cols]
                        pivot_df = pivot_df.reindex(columns=numeric_cols_sorted + other_cols)
                        
                        # Rename month columns to include year
                        rename_dict = {col: f"{int(col)}/{year}" for col in numeric_cols_sorted}
                        pivot_df = pivot_df.rename(columns=rename_dict)
                    
                    # Add Grand Total column
                    pivot_df['Grand Total'] = pivot_df.sum(axis=1)
                    
                    # Calculate mean and median per category (excluding Grand Total column)
                    # Month columns are now in format "1/2025", "2/2025" etc.
                    month_only_cols = [col for col in pivot_df.columns if col not in ['Grand Total', 'Mean', 'Median']]
                    pivot_df['Mean'] = pivot_df[month_only_cols].mean(axis=1)
                    pivot_df['Median'] = pivot_df[month_only_cols].median(axis=1)
                    
                    # Add Grand Total row
                    pivot_df.loc['Grand Total'] = pivot_df.sum()
                    # For Grand Total row, calculate mean and median of all months
                    pivot_df.loc['Grand Total', 'Mean'] = pivot_df[month_only_cols].sum().mean()
                    pivot_df.loc['Grand Total', 'Median'] = pivot_df[month_only_cols].sum().median()
                    
                    # Sort by Grand Total (descending)
                    pivot_df_sorted = pivot_df.sort_values('Grand Total', ascending=False)
                    
                    # Move Grand Total to bottom
                    if 'Grand Total' in pivot_df_sorted.index:
                        grand_total_row = pivot_df_sorted.loc[['Grand Total']]
                        pivot_df_sorted = pivot_df_sorted.drop('Grand Total')
                        pivot_df_sorted = pd.concat([pivot_df_sorted, grand_total_row])
                    
                    # Format numbers for display
                    pivot_df_display = pivot_df_sorted.copy()
                    for col in pivot_df_display.columns:
                        if col in ['Mean', 'Median']:
                            pivot_df_display[col] = pivot_df_display[col].apply(
                                lambda x: f"{x:,.2f}" if pd.notna(x) and isinstance(x, (int, float)) else ""
                            )
                        else:
                            pivot_df_display[col] = pivot_df_display[col].apply(
                                lambda x: f"{x:,.2f}" if pd.notna(x) and isinstance(x, (int, float)) and x != 0 else ("0.00" if pd.notna(x) and isinstance(x, (int, float)) else "")
                            )
                    
                    # Display simple table
                    st.dataframe(
                        pivot_df_display,
                        use_container_width=True,
                        height=600
                    )
                    
                    # Download button
                    csv = pivot_df_sorted.to_csv()
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="spending_summary.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.warning(f"Could not create pivot table: {e}")
    
    with tab2:
        st.header("📈 Analytics")
        
        # ========== INSIGHTS SECTION ==========
        st.subheader("💡 Insights")
        st.caption("Automatically generated insights about your spending and savings opportunities")
        
        if 'date' in df.columns and 'category' in df.columns and 'adjusted_amount' in df.columns:
            # Calculate insights (default to 1 month for summary)
            changes_result_default = calculate_category_changes(df, period_months=1)
            monthly_summary = generate_monthly_summary(df)
            
            if changes_result_default and monthly_summary:
                changes_df_default, last_month, prev_month = changes_result_default
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    change_emoji = "📈" if monthly_summary['change_pct'] > 0 else "📉"
                    st.metric(
                        "Last Month",
                        f"€{monthly_summary['last_month']:,.0f}",
                        f"{monthly_summary['change_pct']:+.1f}% vs. previous"
                    )
                with col2:
                    st.metric(
                        "Average",
                        f"€{monthly_summary['average']:,.0f}",
                        f"{((monthly_summary['last_month'] - monthly_summary['average']) / monthly_summary['average'] * 100):+.1f}% vs. last month"
                    )
                with col3:
                    st.metric(
                        "Highest Month",
                        f"€{monthly_summary['highest_month']:,.0f}",
                        monthly_summary['highest_month_name']
                    )
                with col4:
                    st.metric(
                        "Lowest Month",
                        f"€{monthly_summary['lowest_month']:,.0f}",
                        monthly_summary['lowest_month_name']
                    )
                
                st.divider()
                
                # Category trends with period selection
                st.markdown("#### 📈 Category Spending Trends")
                
                # Period selection
                period_option = st.radio(
                    "Select comparison period:",
                    ["Previous Month", "Select Months", "Same Period Last Year"],
                    horizontal=True,
                    key="insights_period"
                )
                
                # Initialize variables
                custom_start = None
                custom_end = None
                custom_period1_start = None
                custom_period1_end = None
                period_months = 1
                year_to_year = False
                
                # Process period selection
                if period_option == "Previous Month":
                    period_months = 1
                elif period_option == "Select Months":
                    # Get available months
                    df_temp = df.copy()
                    df_temp['month_period'] = df_temp['date'].dt.to_period('M')
                    unique_months = sorted(df_temp['month_period'].unique(), reverse=True)  # Newest first
                    
                    # Format months for display (e.g., "1/2025")
                    month_options = []
                    for month_period in unique_months:
                        # Convert Period to string first, then parse
                        month_str = str(month_period)
                        year, month = map(int, month_str.split('-'))
                        month_options.append(f"{month}/{year}")
                    
                    if len(month_options) >= 2:
                        col1, col2 = st.columns(2)
                        with col1:
                            # Get current selection from session state or use default (newest month, index 0)
                            current_month1 = st.session_state.get('analytics_month1_select', month_options[0] if month_options else None)
                            current_index1 = month_options.index(current_month1) if current_month1 in month_options else 0
                            selected_month1 = st.selectbox(
                                "Select first month:",
                                options=month_options,
                                index=current_index1,
                                key="analytics_month1_select"
                            )
                        with col2:
                            # Get current selection from session state or use default (second newest month, index 1)
                            current_month2 = st.session_state.get('analytics_month2_select', month_options[1] if len(month_options) >= 2 else None)
                            current_index2 = month_options.index(current_month2) if current_month2 in month_options else (1 if len(month_options) >= 2 else 0)
                            selected_month2 = st.selectbox(
                                "Select second month:",
                                options=month_options,
                                index=current_index2,
                                key="analytics_month2_select"
                            )
                        
                        # Calculate dates immediately using the selectbox values (like "Same Period Last Year" does)
                        # Use the actual return values from selectboxes, not session_state
                        try:
                            month1_num, year1 = map(int, selected_month1.split('/'))
                            month2_num, year2 = map(int, selected_month2.split('/'))
                            
                            # Calculate period 1 dates (first selected month)
                            period1_start = pd.Timestamp(year1, month1_num, 1)
                            if month1_num == 12:
                                period1_end = pd.Timestamp(year1, month1_num, 31)
                            else:
                                period1_end = pd.Timestamp(year1, month1_num + 1, 1) - pd.Timedelta(days=1)
                            
                            # Calculate period 2 dates (second selected month)
                            period2_start = pd.Timestamp(year2, month2_num, 1)
                            if month2_num == 12:
                                period2_end = pd.Timestamp(year2, month2_num, 31)
                            else:
                                period2_end = pd.Timestamp(year2, month2_num + 1, 1) - pd.Timedelta(days=1)
                            
                            # Store dates for use in calculation below (like "Same Period Last Year")
                            custom_start = str(period2_start.date())
                            custom_end = str(period2_end.date())
                            custom_period1_start = str(period1_start.date())
                            custom_period1_end = str(period1_end.date())
                            period_months = None  # Signal custom dates
                        except (ValueError, KeyError) as e:
                            st.warning(f"Error parsing selected months: {e}")
                            period_months = 1
                    else:
                        st.warning("At least 2 months required for comparison.")
                        period_months = 1
                else:  # Year to Year
                    year_to_year = True
                    # Get last month's date range
                    df_temp = df.copy()
                    df_temp['month_period'] = df_temp['date'].dt.to_period('M')
                    unique_months = sorted(df_temp['month_period'].unique())
                    if len(unique_months) > 0:
                        last_month_period = unique_months[-1]
                        # Convert Period to string first, then parse
                        last_month_str = str(last_month_period)
                        year, month = map(int, last_month_str.split('-'))
                        # Get start and end of last month (period 1 - current)
                        period1_start = pd.Timestamp(year, month, 1)
                        if month == 12:
                            period1_end = pd.Timestamp(year, month, 31)
                        else:
                            period1_end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)
                        
                        # Previous year same period (period 2 - previous year)
                        period2_start = period1_start - pd.DateOffset(years=1)
                        period2_end = period1_end - pd.DateOffset(years=1)
                        
                        # For calculate_category_changes, we pass period 2 dates as custom_start/end
                        # and it will calculate period 1 automatically
                        custom_start = str(period2_start.date())
                        custom_end = str(period2_end.date())
                        period_months = 1  # For merchant calculation
                
                # Recalculate with selected period
                if period_option == "Same Period Last Year":
                    changes_result = calculate_category_changes(df, period_months=None, custom_start=custom_start, custom_end=custom_end)
                elif period_option == "Select Months":
                    # For custom month selection, use the dates calculated above (like "Same Period Last Year")
                    # Debug: check if dates are available
                    if period_months is None and custom_start and custom_end and custom_period1_start and custom_period1_end:
                        changes_result = calculate_category_changes(
                            df, 
                            period_months=None, 
                            custom_start=custom_start, 
                            custom_end=custom_end,
                            custom_period1_start=custom_period1_start,
                            custom_period1_end=custom_period1_end
                        )
                    else:
                        # Debug: show what's missing
                        missing = []
                        if period_months is not None:
                            missing.append(f"period_months={period_months}")
                        if not custom_start:
                            missing.append("custom_start")
                        if not custom_end:
                            missing.append("custom_end")
                        if not custom_period1_start:
                            missing.append("custom_period1_start")
                        if not custom_period1_end:
                            missing.append("custom_period1_end")
                        if missing:
                            st.warning(f"⚠️ Missing values for calculation: {', '.join(missing)}")
                        changes_result = None
                else:
                    changes_result = calculate_category_changes(df, period_months, custom_start, custom_end)
                
                if changes_result:
                    changes_df, period1_name, period2_name = changes_result
                    
                    # Store period names for later use
                    if period_option == "Select Months":
                        # Extract month names from selected months
                        selected_month1 = st.session_state.get('analytics_month1_select', '')
                        selected_month2 = st.session_state.get('analytics_month2_select', '')
                        if selected_month1 and selected_month2:
                            period1_name = selected_month1
                            period2_name = selected_month2
                    
                    st.caption(f"Comparing: {period1_name} vs. {period2_name}")
                    
                    # Top 3 increasing and decreasing
                    top_increasing = changes_df.nlargest(3, 'change_pct')
                    top_decreasing = changes_df.nsmallest(3, 'change_pct')
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🔴 Top 3 Increasing Categories**")
                        if not top_increasing.empty:
                            for idx, row in top_increasing.iterrows():
                                if row['change_pct'] > 0:
                                    st.info(
                                        f"**{row['category']}**: +{row['change_pct']:.2f}% "
                                        f"(€{row['period2']:,.2f} → €{row['period1']:,.2f})"
                                    )
                    
                    with col2:
                        st.markdown("**🟢 Top 3 Decreasing Categories**")
                        if not top_decreasing.empty:
                            for idx, row in top_decreasing.iterrows():
                                if row['change_pct'] < 0:
                                    st.success(
                                        f"**{row['category']}**: {row['change_pct']:.2f}% "
                                        f"(€{row['period2']:,.2f} → €{row['period1']:,.2f})"
                                    )
                    
                    # Category changes chart
                    if not changes_df.empty:
                        # Sort by change percentage
                        chart_df = changes_df.sort_values('change_pct', ascending=False)
                        
                        period_label = "Previous Month" if period_months == 1 else f"Previous {period_months} Months"
                        if year_to_year:
                            period_label = "Same Period Last Year"
                        elif period_option == "Select Months":
                            period_label = f"{period1_name} vs. {period2_name}"
                        
                        # Create custom hover text - simplified: only change % and change €
                        hover_texts = []
                        for idx, row in chart_df.iterrows():
                            change_abs = row['period1'] - row['period2']
                            hover_text = (
                                f"<b>{row['category']}</b><br>"
                                f"Change: {row['change_pct']:.2f}%<br>"
                                f"Change: €{change_abs:,.2f}"
                            )
                            hover_texts.append(hover_text)
                        
                        fig_changes = px.bar(
                            chart_df,
                            x='change_pct',
                            y='category',
                            orientation='h',
                            title=f"Category Change from Comparison Period (%) - {period_label}",
                            labels={'change_pct': 'Change (%)', 'category': 'Category'},
                            color='change_pct',
                            color_continuous_scale=['#2ca02c', '#ff7f0e', '#d62728'],
                            text=[f"{val:+.0f}%" for val in chart_df['change_pct']]
                        )
                        fig_changes.update_traces(
                            textposition='outside',
                            hovertemplate='%{customdata}<extra></extra>',
                            customdata=hover_texts
                        )
                        fig_changes.update_layout(height=400)
                        st.plotly_chart(fig_changes, use_container_width=True)
                        
                        # Waterfall chart
                        st.markdown("#### 💧 Waterfall Chart: Spending Change by Category")
                        
                        # Prepare data for waterfall chart - sort by period2 for better visualization
                        waterfall_df = chart_df.sort_values('period2', ascending=True).copy()
                        waterfall_df['change'] = waterfall_df['period1'] - waterfall_df['period2']
                        
                        # Create waterfall chart using go.Figure
                        fig_waterfall = go.Figure()
                        
                        categories = waterfall_df['category'].tolist()
                        period2_values = waterfall_df['period2'].tolist()
                        period1_values = waterfall_df['period1'].tolist()
                        changes = waterfall_df['change'].tolist()
                        
                        # Calculate cumulative positions for waterfall effect
                        # Starting from 0, each category builds on the previous
                        cumulative_start = 0
                        cumulative_end = 0
                        
                        # Add starting total (sum of all period2)
                        total_start = sum(period2_values)
                        total_end = sum(period1_values)
                        total_change = total_end - total_start
                        
                        # Add initial bar (total start)
                        fig_waterfall.add_trace(go.Bar(
                            name='Starting Value (Total)',
                            x=['Starting Value'],
                            y=[total_start],
                            marker_color='lightblue',
                            text=[f"€{total_start:,.0f}"],
                            textposition='outside',
                            hovertemplate='<b>Starting Value</b><br>Total: €%{y:,.2f}<extra></extra>'
                        ))
                        
                        # Add change bars for each category
                        positive_changes = []
                        negative_changes = []
                        positive_categories = []
                        negative_categories = []
                        positive_base = []
                        negative_base = []
                        
                        for cat, change, period2, period1 in zip(categories, changes, period2_values, period1_values):
                            if change >= 0:
                                positive_changes.append(change)
                                positive_categories.append(cat)
                                positive_base.append(total_start)
                                total_start += change
                            else:
                                negative_changes.append(change)
                                negative_categories.append(cat)
                                negative_base.append(total_start + change)
                                total_start += change
                        
                        # Add positive changes
                        if positive_changes:
                            fig_waterfall.add_trace(go.Bar(
                                name='Increase',
                                x=positive_categories,
                                y=positive_changes,
                                marker_color='green',
                                base=positive_base,
                                text=[f"+€{val:,.0f}" for val in positive_changes],
                                textposition='outside',
                                hovertemplate='<b>%{x}</b><br>Increase: +€%{y:,.2f}<br>Starting Value: €%{base:,.2f}<extra></extra>'
                            ))
                        
                        # Add negative changes
                        if negative_changes:
                            fig_waterfall.add_trace(go.Bar(
                                name='Decrease',
                                x=negative_categories,
                                y=negative_changes,
                                marker_color='red',
                                base=negative_base,
                                text=[f"€{val:,.0f}" for val in negative_changes],
                                textposition='outside',
                                hovertemplate='<b>%{x}</b><br>Decrease: €%{y:,.2f}<br>Starting Value: €%{base:,.2f}<extra></extra>'
                            ))
                        
                        # Add final total
                        fig_waterfall.add_trace(go.Bar(
                            name='Ending Value (Total)',
                            x=['Ending Value'],
                            y=[total_end],
                            marker_color='lightcoral',
                            base=[sum(period2_values)],
                            text=[f"€{total_end:,.0f}"],
                            textposition='outside',
                            hovertemplate='<b>Ending Value</b><br>Total: €%{y:,.2f}<extra></extra>'
                        ))
                        
                        fig_waterfall.update_layout(
                            title=f"Waterfall: Spending Change by Category - {period_label}",
                            barmode='overlay',
                            height=700,
                            xaxis_title="Category",
                            yaxis_title="Spending (€)",
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig_waterfall, use_container_width=True)
                else:
                    st.warning("Insufficient data for selected period.")
                
                st.divider()
                
                # AI-Powered Insights (on-demand generation)
                st.markdown("#### 🤖 AI-Powered Insights")
                with st.expander("💡 Generate Smart Insights", expanded=False):
                    api_key = os.getenv('OPENAI_API_KEY')
                    # Check if API key and LLM are available
                    if not api_key:
                        st.warning("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
                    elif not LLM_AVAILABLE:
                        st.warning("⚠️ LLM client not available. Check that src.llm_client can be imported.")
                    elif api_key and LLM_AVAILABLE:
                        if changes_result:
                            # Button to generate insights
                            if st.button("🚀 Generate Insights", use_container_width=True, type="primary"):
                                with st.spinner("🤖 Generating insights (this may take 10-30 seconds)..."):
                                    changes_df_insights, period1_name_insights, period2_name_insights = changes_result
                                    
                                    # Get opportunities and high vs avg for the selected period
                                    custom_period1_start_insights = None
                                    custom_period1_end_insights = None
                                    if period_option == "Select Months" and custom_start and custom_end:
                                        selected_month1 = st.session_state.get('analytics_month1_select', '')
                                        if selected_month1:
                                            month1_num, year1 = map(int, selected_month1.split('/'))
                                            period1_start = pd.Timestamp(year1, month1_num, 1)
                                            if month1_num == 12:
                                                period1_end = pd.Timestamp(year1, month1_num, 31)
                                            else:
                                                period1_end = pd.Timestamp(year1, month1_num + 1, 1) - pd.Timedelta(days=1)
                                            custom_period1_start_insights = str(period1_start.date())
                                            custom_period1_end_insights = str(period1_end.date())
                                    
                                    opportunities_insights = identify_savings_opportunities(
                                        df, changes_df_insights, period_months, custom_start, custom_end,
                                        custom_period1_start_insights, custom_period1_end_insights
                                    )
                                    high_vs_avg_insights = changes_df_insights[changes_df_insights['vs_avg_pct'] > 20].sort_values('vs_avg_pct', ascending=False)
                                    
                                    # Generate insights
                                    try:
                                        insights = generate_analytics_insights(
                                            df,
                                            changes_df_insights,
                                            opportunities_insights,
                                            high_vs_avg_insights,
                                            period1_name_insights,
                                            period2_name_insights,
                                            period_months,
                                            custom_start,
                                            custom_end,
                                            custom_period1_start_insights,
                                            custom_period1_end_insights,
                                            api_key
                                        )
                                        
                                        if insights and not insights.startswith("Error:") and insights.strip():
                                            st.session_state['analytics_insights'] = insights
                                            st.session_state['analytics_insights_period'] = f"{period1_name_insights} vs {period2_name_insights}"
                                            st.success("✅ Insights generated successfully!")
                                        else:
                                            error_msg = insights if insights and insights.startswith("Error:") else "Unknown error - check API key and OpenAI package installation"
                                            st.error(f"❌ Failed to generate insights: {error_msg}")
                                            # Show debug info
                                            with st.expander("🔍 Debug Info"):
                                                import sys
                                                st.write(f"**Python executable:** {sys.executable}")
                                                st.write(f"**API Key present:** {bool(api_key)}")
                                                st.write(f"**LLM Available:** {LLM_AVAILABLE}")
                                                st.write(f"**Insights value:** {repr(insights)}")
                                                try:
                                                    from openai import OpenAI
                                                    import openai
                                                    st.write(f"✅ OpenAI package is importable (version: {openai.__version__})")
                                                except ImportError as e:
                                                    st.write(f"❌ OpenAI package import failed: {e}")
                                                    st.write(f"**Python path:** {sys.path[:3]}")
                                    except Exception as e:
                                        st.error(f"❌ Error generating insights: {str(e)}")
                                        import traceback
                                        with st.expander("🔍 Debug Details"):
                                            st.code(traceback.format_exc())
                                
                                # Rerun to show the insights
                                st.rerun()
                            
                            # Display stored insights if available
                            if 'analytics_insights' in st.session_state and 'analytics_insights_period' in st.session_state:
                                st.markdown(f"**Period:** {st.session_state['analytics_insights_period']}")
                                st.markdown("---")
                                st.markdown(st.session_state['analytics_insights'])
                                if st.button("🗑️ Clear Insights", use_container_width=True):
                                    del st.session_state['analytics_insights']
                                    del st.session_state['analytics_insights_period']
                                    st.rerun()
                            else:
                                st.info("💡 Click 'Generate Insights' to create a smart summary based on the selected period above.")
                        else:
                            st.warning("⚠️ No data available for the selected period.")
                    else:
                        if not api_key:
                            st.info("💡 Configure OpenAI API key in .env file to enable AI-powered insights.")
                        else:
                            st.info("💡 LLM client not available.")
                
                st.divider()
                
                # Savings opportunities
                st.markdown("#### 💰 Savings Opportunities")
                
                # Use the same period as selected for trends
                if changes_result:
                    changes_df_for_opps, _, _ = changes_result
                    # Get custom period1 dates if available (for custom month selection)
                    custom_period1_start = None
                    custom_period1_end = None
                    if period_option == "Select Months" and custom_start and custom_end:
                        selected_month1 = st.session_state.get('analytics_month1_select', '')
                        if selected_month1:
                            month1_num, year1 = map(int, selected_month1.split('/'))
                            period1_start = pd.Timestamp(year1, month1_num, 1)
                            if month1_num == 12:
                                period1_end = pd.Timestamp(year1, month1_num, 31)
                            else:
                                period1_end = pd.Timestamp(year1, month1_num + 1, 1) - pd.Timedelta(days=1)
                            custom_period1_start = str(period1_start.date())
                            custom_period1_end = str(period1_end.date())
                    
                    opportunities = identify_savings_opportunities(
                        df, changes_df_for_opps, period_months, custom_start, custom_end,
                        custom_period1_start, custom_period1_end
                    )
                    
                    if opportunities:
                        # Sort by savings potential
                        opportunities_sorted = sorted(opportunities, key=lambda x: x.get('savings_potential_15', 0), reverse=True)
                        
                        for opp in opportunities_sorted[:5]:  # Show top 5
                            # Severity color logic:
                            # - 🔴 high: vs_avg_pct > 50% OR change_pct > 50%
                            # - 🟡 medium: vs_avg_pct 30-50% OR change_pct 20-50%
                            severity_color = {
                                'high': '🔴',
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(opp['severity'], '⚪')
                            
                            with st.expander(f"{severity_color} {opp['title']}: {opp['category']}", expanded=False):
                                # Get additional info from changes_df
                                cat_info = None
                                period1_name_display = "Selected Period"
                                period2_name_display = "Comparison Period"
                                
                                if changes_result:
                                    changes_df_info, period1_name_result, period2_name_result = changes_result
                                    cat_info = changes_df_info[changes_df_info['category'] == opp['category']]
                                    # Use period names from result if available
                                    if period1_name_result and period2_name_result:
                                        period1_name_display = period1_name_result
                                        period2_name_display = period2_name_result
                                
                                # Get period names for display if custom month selection
                                if period_option == "Select Months":
                                    selected_month1 = st.session_state.get('analytics_month1_select', '')
                                    selected_month2 = st.session_state.get('analytics_month2_select', '')
                                    if selected_month1 and selected_month2:
                                        period1_name_display = selected_month1
                                        period2_name_display = selected_month2
                                
                                # Calculate differences
                                diff_previous = None
                                diff_previous_pct = None
                                diff_average = None
                                diff_average_pct = None
                                
                                if 'current' in opp:
                                    if cat_info is not None and not cat_info.empty:
                                        diff_previous = opp['current'] - cat_info.iloc[0]['period2']
                                        if cat_info.iloc[0]['period2'] > 0:
                                            diff_previous_pct = (diff_previous / cat_info.iloc[0]['period2'] * 100)
                                        diff_average = opp['current'] - cat_info.iloc[0]['average']
                                        if cat_info.iloc[0]['average'] > 0:
                                            diff_average_pct = (diff_average / cat_info.iloc[0]['average'] * 100)
                                    elif 'previous' in opp:
                                        diff_previous = opp['current'] - opp['previous']
                                        if opp['previous'] > 0:
                                            diff_previous_pct = (diff_previous / opp['previous'] * 100)
                                    if 'average' in opp:
                                        diff_average = opp['current'] - opp['average']
                                        if opp['average'] > 0:
                                            diff_average_pct = (diff_average / opp['average'] * 100)
                                
                                # Display description with change info
                                if 'change_pct' in opp and 'change_abs' in opp:
                                    st.markdown(f"**{opp['category']} category spending has increased {opp['change_pct']:.2f}% from comparison period ({opp['change_abs']:,.2f}€)**")
                                else:
                                    st.markdown(f"**{opp['description']}**")
                                
                                # First row: Selected Period - Comparison Period - Difference€ (percentage)
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    if 'current' in opp:
                                        st.metric(period1_name_display, f"€{opp['current']:,.2f}")
                                with col2:
                                    if cat_info is not None and not cat_info.empty:
                                        st.metric(period2_name_display, f"€{cat_info.iloc[0]['period2']:,.2f}")
                                    elif 'previous' in opp:
                                        st.metric(period2_name_display, f"€{opp['previous']:,.2f}")
                                with col3:
                                    if diff_previous is not None:
                                        pct_text = f"({diff_previous_pct:+.2f}%)" if diff_previous_pct is not None else ""
                                        st.metric("Difference", f"€{diff_previous:,.2f} {pct_text}")
                                
                                # Second row: Selected Period - Average - Difference€ (percentage)
                                col4, col5, col6 = st.columns(3)
                                with col4:
                                    if 'current' in opp:
                                        st.metric(period1_name_display, f"€{opp['current']:,.2f}")
                                with col5:
                                    if cat_info is not None and not cat_info.empty:
                                        st.metric("Average", f"€{cat_info.iloc[0]['average']:,.2f}")
                                    elif 'average' in opp:
                                        st.metric("Average", f"€{opp['average']:,.2f}")
                                with col6:
                                    if diff_average is not None:
                                        pct_text = f"({diff_average_pct:+.2f}%)" if diff_average_pct is not None else ""
                                        st.metric("Difference", f"€{diff_average:,.2f} {pct_text}")
                                
                                # Savings potential
                                if 'savings_potential_15' in opp:
                                    st.metric(
                                        "Savings Potential (15% reduction)",
                                        f"€{opp['savings_potential_15']:,.2f}/month"
                                    )
                                
                                # Top 5 merchants
                                if 'top_merchants' in opp and opp['top_merchants']:
                                    st.markdown("**🏪 Top 5 Merchants (explaining spending):**")
                                    merchant_df = pd.DataFrame(opp['top_merchants'])
                                    if opp['current'] > 0:
                                        merchant_df['% of category'] = (merchant_df['amount'] / opp['current'] * 100).round(1)
                                    else:
                                        merchant_df['% of category'] = 0.0
                                    
                                    for idx, merchant_row in merchant_df.iterrows():
                                        merchant_name = merchant_row['merchant']
                                        st.markdown(
                                            f"  • {merchant_name}: "
                                            f"€{merchant_row['amount']:,.2f} ({merchant_row['% of category']:.1f}%)"
                                        )
                                
                                if 'savings_potential_15' in opp and opp['savings_potential_15'] > 0:
                                    st.info(
                                        f"💡 **Recommendation**: If you reduce {opp['category']} category by 15%, "
                                        f"you'll save approximately €{opp['savings_potential_15']:,.2f}/month"
                                    )
                    else:
                        st.info("No significant savings opportunities detected.")
                else:
                    st.warning("Insufficient data for savings opportunities analysis.")
                
                st.divider()
                
                # Highest vs average categories
                st.markdown("#### 📊 Categories vs. Average")
                if changes_result:
                    changes_df_for_avg, _, _ = changes_result
                    high_vs_avg = changes_df_for_avg[changes_df_for_avg['vs_avg_pct'] > 20].sort_values('vs_avg_pct', ascending=False)
                    
                    if not high_vs_avg.empty:
                        st.markdown("**Categories where spending is significantly higher than average:**")
                        for idx, row in high_vs_avg.head(5).iterrows():
                            st.warning(
                                f"**{row['category']}**: €{row['period1']:,.2f} "
                                f"({row['vs_avg_pct']:+.0f}% vs. average €{row['average']:,.2f})"
                            )
                    else:
                        st.success("All categories are close to average.")
        
        st.divider()
        
        # ========== RECURRING EXPENSES SECTION ==========
        st.markdown("#### 🔄 Recurring Expenses")
        st.caption("Identify subscriptions and recurring payments")
        
        if 'merchant' in df.columns and 'date' in df.columns:
            col1, col2 = st.columns(2)
            with col1:
                recurring_months = st.slider("Analysis period (months)", 3, 12, 6, key="recurring_months")
            with col2:
                min_transactions = st.slider("Minimum transactions", 2, 10, 3, key="min_transactions")
            
            recurring_df = identify_recurring_expenses(df, months=recurring_months, min_count=min_transactions)
            
            if not recurring_df.empty:
                # Category filter
                if 'category' in recurring_df.columns:
                    categories = ['All'] + sorted(recurring_df['category'].unique().tolist())
                    selected_category = st.selectbox(
                        "Filter by Category:",
                        options=categories,
                        key="recurring_category_filter"
                    )
                    
                    # Filter by category if not "All"
                    if selected_category != 'All':
                        recurring_df_filtered = recurring_df[recurring_df['category'] == selected_category].copy()
                    else:
                        recurring_df_filtered = recurring_df.copy()
                else:
                    recurring_df_filtered = recurring_df.copy()
                    selected_category = 'All'
                
                # Summary metrics (based on filtered data)
                total_recurring = recurring_df_filtered['sum_eur'].sum()
                monthly_recurring = recurring_df_filtered['avg_per_month'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Recurring Expenses", f"€{total_recurring:,.2f}")
                with col2:
                    st.metric("Monthly Average", f"€{monthly_recurring:,.2f}")
                with col3:
                    st.metric("Number of Recurring Items", len(recurring_df_filtered))
                
                # Display table
                display_recurring = recurring_df_filtered.copy()
                if 'category' in display_recurring.columns:
                    display_recurring.columns = ['Merchant', 'Category', 'Transactions', 'Months Active', 'Total (€)', 'Avg/Month (€)']
                else:
                    display_recurring.columns = ['Merchant', 'Transactions', 'Months Active', 'Total (€)', 'Avg/Month (€)']
                display_recurring['Total (€)'] = display_recurring['Total (€)'].apply(lambda x: f"€{x:,.2f}")
                display_recurring['Avg/Month (€)'] = display_recurring['Avg/Month (€)'].apply(lambda x: f"€{x:,.2f}")
                
                st.dataframe(
                    display_recurring,
                    use_container_width=True,
                    height=400
                )
                
                # Visualization - Top 15 sorted by avg_per_month descending
                top_15 = recurring_df_filtered.head(15).sort_values('avg_per_month', ascending=False)
                
                if not top_15.empty:
                    # Create color mapping by category if available
                    if 'category' in top_15.columns:
                        unique_categories = top_15['category'].unique()
                        colors = px.colors.qualitative.Set3
                        color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(unique_categories)}
                        top_15['color'] = top_15['category'].map(color_map)
                    else:
                        color_map = None
                    
                    fig_recurring = px.bar(
                        top_15,
                        x='merchant',
                        y='avg_per_month',
                        color='category' if 'category' in top_15.columns else None,
                        title="Top 15 Recurring Expenses (Monthly Average)" + (f" - {selected_category}" if selected_category != 'All' else ""),
                        labels={'merchant': 'Merchant', 'avg_per_month': 'Average per Month (€)', 'category': 'Category'},
                        color_discrete_map=color_map if color_map else None
                    )
                    fig_recurring.update_layout(
                        height=400,
                        xaxis_tickangle=-45,
                        xaxis={'categoryorder': 'total descending'}  # Sort by value descending
                    )
                    st.plotly_chart(fig_recurring, use_container_width=True)
                else:
                    st.info("No data to display after filtering.")
            else:
                st.info("No recurring expenses identified. Try adjusting the analysis period or minimum transactions.")
        
        # ========== EXISTING ANALYTICS SECTIONS ==========
        st.divider()
        
        # Time series analysis with multiple views
        if 'date' in df.columns and 'adjusted_amount' in df.columns:
            st.subheader("Time Series Analysis")
            
            # View selector
            view_option = st.radio(
                "Select View:",
                ["Weekly", "Monthly", "Daily"],
                horizontal=True,
                key="time_view"
            )
            
            if view_option == "Weekly":
                df_temp = df.copy()
                df_temp['week'] = df_temp['date'].dt.to_period('W')
                time_data = df_temp.groupby('week')['adjusted_amount'].sum().reset_index()
                time_data['week'] = time_data['week'].astype(str)
                time_col = 'week'
                title = "Weekly Spending Trend"
            elif view_option == "Monthly":
                time_data = df.groupby([df['date'].dt.to_period('M')])['adjusted_amount'].sum().reset_index()
                time_data['date'] = time_data['date'].astype(str)
                time_col = 'date'
                title = "Monthly Spending Trend"
            else:  # Daily
                time_data = df.groupby(df['date'].dt.date)['adjusted_amount'].sum().reset_index()
                time_data.columns = ['date', 'adjusted_amount']
                time_col = 'date'
                title = "Daily Spending Trend"
            
            time_data = time_data.sort_values(time_col)
            
            # Create interactive line chart with moving average
            fig = go.Figure()
            
            # Main line
            fig.add_trace(go.Scatter(
                x=time_data[time_col],
                y=time_data['adjusted_amount'],
                mode='lines+markers',
                name='Spending',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Amount: €%{y:,.2f}<extra></extra>'
            ))
            
            # Moving average
            if view_option == "Daily" and len(time_data) > 7:
                time_data['ma'] = time_data['adjusted_amount'].rolling(window=7, center=True).mean()
                fig.add_trace(go.Scatter(
                    x=time_data[time_col],
                    y=time_data['ma'],
                    mode='lines',
                    name='7-Day Moving Average',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    hovertemplate='<b>%{x}</b><br>MA: €%{y:,.2f}<extra></extra>'
                ))
            elif view_option == "Monthly" and len(time_data) > 3:
                time_data['ma'] = time_data['adjusted_amount'].rolling(window=3, center=True).mean()
                fig.add_trace(go.Scatter(
                    x=time_data[time_col],
                    y=time_data['ma'],
                    mode='lines',
                    name='3-Month Moving Average',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    hovertemplate='<b>%{x}</b><br>MA: €%{y:,.2f}<extra></extra>'
                ))
            
            fig.update_layout(
                title=title,
                xaxis_title=view_option,
                yaxis_title='Amount (€)',
                height=400,
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Category comparison over time
        if 'category' in df.columns and 'date' in df.columns and 'adjusted_amount' in df.columns:
            st.subheader("Category Trends Over Time")
            
            # Select categories to compare
            categories_to_compare = st.multiselect(
                "Select categories to compare:",
                options=sorted(df['category'].unique()),
                default=sorted(df['category'].unique())[:5] if len(df['category'].unique()) >= 5 else sorted(df['category'].unique()),
                key="cat_compare"
            )
            
            if categories_to_compare:
                cat_df = df[df['category'].isin(categories_to_compare)].copy()
                cat_trends = cat_df.groupby([
                    cat_df['date'].dt.to_period('M'),
                    'category'
                ])['adjusted_amount'].sum().reset_index()
                cat_trends['date'] = cat_trends['date'].astype(str)
                cat_trends = cat_trends.sort_values('date')
                
                fig_cat_trends = px.line(
                    cat_trends,
                    x='date',
                    y='adjusted_amount',
                    color='category',
                    title="Category Spending Trends",
                    labels={'date': 'Month', 'adjusted_amount': 'Amount (€)', 'category': 'Category'},
                    markers=True
                )
                fig_cat_trends.update_layout(height=400)
                st.plotly_chart(fig_cat_trends, use_container_width=True)
        
        # Top merchants with more details
        if 'merchant' in df.columns and 'adjusted_amount' in df.columns:
            st.subheader("Top Merchants Analysis")
            
            top_n = st.slider("Number of merchants to show:", 5, 30, 15, key="top_merchants")
            top_merchants = df.groupby('merchant')['adjusted_amount'].sum().sort_values(ascending=False).head(top_n)
            
            if not top_merchants.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = px.bar(
                        x=top_merchants.values,
                        y=top_merchants.index,
                        orientation='h',
                        title=f"Top {top_n} Merchants by Spending",
                        labels={'x': 'Amount (€)', 'y': 'Merchant'},
                        text=[f"€{val:,.0f}" for val in top_merchants.values]
                    )
                    fig.update_traces(
                        marker_color='#2ca02c',
                        hovertemplate='<b>%{y}</b><br>Amount: €%{x:,.2f}<extra></extra>'
                    )
                    fig.update_layout(height=max(400, top_n * 25))
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.metric("Total", f"€{top_merchants.sum():,.2f}")
                    st.metric("Average", f"€{top_merchants.mean():,.2f}")
                    st.metric("Median", f"€{top_merchants.median():,.2f}")
                    
                    # Percentage of total
                    pct_of_total = (top_merchants.sum() / df['adjusted_amount'].sum()) * 100
                    st.metric("% of Total", f"{pct_of_total:.1f}%")
    
    with tab3:
        st.header("Transaction Table")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'category' in df.columns:
                categories = ['All'] + sorted(df['category'].unique().tolist())
                selected_category = st.selectbox("Category", categories)
                if selected_category != 'All':
                    df = df[df['category'] == selected_category]
        
        with col2:
            if 'merchant' in df.columns:
                search_merchant = st.text_input("Search Merchant", "")
                if search_merchant:
                    df = df[df['merchant'].str.contains(search_merchant, case=False, na=False)]
        
        with col3:
            if 'date' in df.columns and not df.empty:
                # Check if dates are valid (not NaT)
                min_date = df['date'].min()
                max_date = df['date'].max()
                
                # Only show date input if we have valid dates
                if pd.notna(min_date) and pd.notna(max_date):
                    try:
                        date_range = st.date_input(
                            "Date Range",
                            value=(min_date.date(), max_date.date()),
                            min_value=min_date.date(),
                            max_value=max_date.date()
                        )
                        if len(date_range) == 2:
                            df = df[(df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])]
                    except (ValueError, AttributeError):
                        # If date conversion fails, skip date filtering
                        st.info("⚠️ Päivämääräsuodatus ei saatavilla")
                else:
                    st.info("⚠️ Päivämäärätiedot puuttuvat")
        
        # Display table
        display_cols = ['date', 'merchant', 'amount', 'adjusted_amount', 'cost_allocation', 'category', '2nd category', 'notes', 'card']
        display_cols = [col for col in display_cols if col in df.columns]
        
        if display_cols:
            # Sort by date if available, otherwise by first column
            sort_col = 'date' if 'date' in display_cols else display_cols[0]
            display_df = df[display_cols].sort_values(sort_col, ascending=False).copy()
            
            # Rename columns to Title Case
            column_rename_map = {
                'date': 'Date',
                'merchant': 'Merchant',
                'amount': 'Amount',
                'adjusted_amount': 'Adjusted Amount',
                'cost_allocation': 'Cost Allocation',
                'category': 'Category',
                '2nd category': 'Subcategory',
                'notes': 'Notes',
                'card': 'Card'
            }
            display_df = display_df.rename(columns=column_rename_map)
            
            # Format Amount and Adjusted Amount as euros
            if 'Amount' in display_df.columns:
                display_df['Amount'] = display_df['Amount'].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) and isinstance(x, (int, float)) else x)
            if 'Adjusted Amount' in display_df.columns:
                display_df['Adjusted Amount'] = display_df['Adjusted Amount'].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) and isinstance(x, (int, float)) else x)
            
            # Format Cost Allocation as percentage without decimals
            if 'Cost Allocation' in display_df.columns:
                display_df['Cost Allocation'] = (display_df['Cost Allocation'] * 100).astype(int).astype(str) + '%'
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=600
            )
        else:
            st.info("No columns available to display")
    
    with tab4:
        st.header("Edit Categories")
        st.info("Select transactions to edit their categories and notes.")
        
        # Get unique categories for dropdown
        if 'category' in df.columns:
            categories = sorted(df['category'].unique().tolist())
            
            # Select transaction to edit
            transaction_options = [
                f"{row['date'].strftime('%Y-%m-%d')} | {row['merchant']} | €{row.get('amount', 0):.2f}"
                for idx, row in df.iterrows()
            ]
            
            selected_idx = st.selectbox(
                "Select Transaction",
                options=range(len(transaction_options)),
                format_func=lambda x: transaction_options[x]
            )
            
            if selected_idx is not None:
                selected_row = df.iloc[selected_idx]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Current Values")
                    st.write(f"**Date:** {selected_row['date']}")
                    st.write(f"**Merchant:** {selected_row['merchant']}")
                    st.write(f"**Amount:** €{selected_row.get('amount', 0):.2f}")
                    st.write(f"**Category:** {selected_row.get('category', 'N/A')}")
                    st.write(f"**2nd Category:** {selected_row.get('2nd category', 'N/A')}")
                    st.write(f"**Notes:** {selected_row.get('notes', 'N/A')}")
                
                with col2:
                    st.subheader("Edit Values")
                    
                    new_category = st.selectbox(
                        "Category",
                        options=categories,
                        index=categories.index(selected_row['category']) if selected_row.get('category') in categories else 0
                    )
                    
                    # Get subcategories for selected category
                    subcategories = [''] + GENERAL_2ND_CATEGORIES
                    if new_category in GENERAL_2ND_CATEGORIES:
                        subcategories = ['Yleinen']
                    else:
                        # Add common subcategories
                        subcategories = ['', 'Henkilökohtainen', 'Perhe', 'Yleinen']
                    
                    current_2nd = selected_row.get('2nd category', '')
                    if current_2nd not in subcategories:
                        subcategories.insert(0, current_2nd)
                    
                    new_2nd_category = st.selectbox(
                        "2nd Category",
                        options=subcategories,
                        index=subcategories.index(current_2nd) if current_2nd in subcategories else 0
                    )
                    
                    new_notes = st.text_input(
                        "Notes",
                        value=str(selected_row.get('notes', ''))
                    )
                    
                    if st.button("💾 Save Changes", use_container_width=True):
                        # Extract cost allocation from notes
                        from src.cost_allocator import extract_cost_allocation
                        allocation, cleaned_notes = extract_cost_allocation(new_notes)
                        
                        # Update dataframe
                        idx = df.index[selected_idx]
                        df.loc[idx, 'category'] = new_category
                        df.loc[idx, '2nd category'] = new_2nd_category
                        df.loc[idx, 'notes'] = cleaned_notes
                        
                        # Ensure cost_allocation and adjusted_amount columns exist
                        if 'cost_allocation' not in df.columns:
                            df['cost_allocation'] = 1.0
                        if 'adjusted_amount' not in df.columns:
                            df['adjusted_amount'] = df['amount']
                        
                        df.loc[idx, 'cost_allocation'] = allocation
                        df.loc[idx, 'adjusted_amount'] = df.loc[idx, 'amount'] * allocation
                        
                        st.session_state.df = df
                        st.session_state.edited = True
                        st.success("Changes saved to session!")
                        st.rerun()
        
        # Save all changes button
        if st.session_state.edited:
            st.divider()
            if st.button("💾 Save All Changes to Excel", type="primary", use_container_width=True):
                save_changes(st.session_state.df)
    
    with tab5:
        st.header("💰 Budget")
        
        budgets = load_budgets()
        
        # Budget setup section
        st.subheader("Set Monthly Budgets")
        st.caption("Set monthly spending limits for each category")
        
        if 'category' in df.columns:
            categories = sorted(df['category'].unique().tolist())
            
            # Create budget inputs
            budget_inputs = {}
            col1, col2 = st.columns(2)
            
            for i, category in enumerate(categories):
                col = col1 if i % 2 == 0 else col2
                with col:
                    current_budget = budgets.get(category, 0.0)
                    budget_inputs[category] = st.number_input(
                        f"{category}",
                        min_value=0.0,
                        value=float(current_budget),
                        step=50.0,
                        key=f"budget_{category}"
                    )
            
            # Save budgets button
            if st.button("💾 Save Budgets", type="primary", use_container_width=True):
                save_budgets(budget_inputs)
                st.success("Budgets saved!")
                st.rerun()
        
        st.divider()
        
        # Budget vs Actual section
        st.subheader("Budget vs Actual")
        st.caption("Compare your spending against your budgets")
        
        if budgets and 'category' in df.columns and 'adjusted_amount' in df.columns:
            # Month selector
            if 'date' in df.columns:
                df_temp = df.copy()
                df_temp['date'] = pd.to_datetime(df_temp['date'])
                df_temp['month_str'] = df_temp['date'].dt.to_period('M').astype(str)
                available_months = sorted(df_temp['month_str'].unique(), reverse=True)
                
                if available_months:
                    selected_month = st.selectbox(
                        "Select month to analyze:",
                        options=["All Time"] + available_months,
                        key="budget_month_selector"
                    )
                    
                    month_filter = None if selected_month == "All Time" else selected_month
                    budget_vs_actual = get_budget_vs_actual(df, budgets, month=month_filter)
                    
                    if not budget_vs_actual.empty:
                        # Filter out categories with no budget
                        budget_vs_actual = budget_vs_actual[budget_vs_actual['budget'] > 0]
                        
                        if not budget_vs_actual.empty:
                            # Summary metrics
                            total_budget = budget_vs_actual['budget'].sum()
                            total_actual = budget_vs_actual['actual'].sum()
                            total_diff = total_budget - total_actual
                            total_pct = (total_actual / total_budget * 100) if total_budget > 0 else 0
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Budget", f"€{total_budget:,.2f}")
                            with col2:
                                st.metric("Total Actual", f"€{total_actual:,.2f}")
                            with col3:
                                st.metric("Remaining", f"€{total_diff:,.2f}", delta=f"{total_pct:.1f}%")
                            with col4:
                                over_budget = len(budget_vs_actual[budget_vs_actual['status'] == 'over'])
                                st.metric("Over Budget", f"{over_budget} categories")
                            
                            # Alerts for over-budget categories
                            over_budget_df = budget_vs_actual[budget_vs_actual['status'] == 'over']
                            if not over_budget_df.empty:
                                st.warning(f"⚠️ {len(over_budget_df)} category/categories over budget:")
                                for _, row in over_budget_df.iterrows():
                                    over_amount = row['actual'] - row['budget']
                                    over_pct = (over_amount / row['budget'] * 100) if row['budget'] > 0 else 0
                                    st.error(
                                        f"**{row['category']}**: €{row['actual']:,.2f} / €{row['budget']:,.2f} "
                                        f"(€{over_amount:,.2f} over, {over_pct:.1f}%)"
                                    )
                            
                            # Visualization
                            fig_budget = go.Figure()
                            
                            # Budget bars
                            fig_budget.add_trace(go.Bar(
                                name='Budget',
                                x=budget_vs_actual['category'],
                                y=budget_vs_actual['budget'],
                                marker_color='#2ca02c',
                                text=[f"€{val:,.0f}" for val in budget_vs_actual['budget']],
                                textposition='outside'
                            ))
                            
                            # Actual bars
                            fig_budget.add_trace(go.Bar(
                                name='Actual',
                                x=budget_vs_actual['category'],
                                y=budget_vs_actual['actual'],
                                marker_color=budget_vs_actual['status'].map({
                                    'over': '#d62728',
                                    'under': '#1f77b4',
                                    'no_budget': '#7f7f7f'
                                }),
                                text=[f"€{val:,.0f}" for val in budget_vs_actual['actual']],
                                textposition='outside'
                            ))
                            
                            fig_budget.update_layout(
                                title="Budget vs Actual Spending",
                                xaxis_title="Category",
                                yaxis_title="Amount (€)",
                                height=500,
                                barmode='group',
                                xaxis_tickangle=-45
                            )
                            
                            st.plotly_chart(fig_budget, use_container_width=True)
                            
                            # Detailed table
                            display_budget = budget_vs_actual.copy()
                            display_budget['budget'] = display_budget['budget'].apply(lambda x: f"€{x:,.2f}")
                            display_budget['actual'] = display_budget['actual'].apply(lambda x: f"€{x:,.2f}")
                            display_budget['difference'] = display_budget['difference'].apply(lambda x: f"€{x:,.2f}")
                            display_budget['percentage'] = display_budget['percentage'].apply(lambda x: f"{x:.1f}%")
                            display_budget['status'] = display_budget['status'].map({
                                'over': '🔴 Over',
                                'under': '🟢 Under',
                                'no_budget': '⚪ No Budget'
                            })
                            display_budget.columns = ['Category', 'Budget', 'Actual', 'Difference', 'Percentage', 'Status']
                            
                            st.dataframe(
                                display_budget,
                                use_container_width=True,
                                height=400
                            )
                        else:
                            st.info("No budgets set for any categories. Set budgets above to see comparisons.")
                    else:
                        st.info("No budget data available for selected period.")
                else:
                    st.info("No date data available for month filtering.")
            else:
                st.info("Date column not available for month filtering.")
        else:
            if not budgets:
                st.info("No budgets set yet. Set budgets above to start tracking.")
            else:
                st.info("Category or amount data not available.")
    
    with tab6:
        if AI_ASSISTANT_AVAILABLE:
            render_ai_assistant_tab(df)
        else:
            st.info("AI Assistant -ominaisuus ei ole saatavilla. Asenna openai-paketti: `pip install openai`")

