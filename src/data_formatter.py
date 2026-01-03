"""Data formatter for LLM analysis - formats transaction data for OpenAI API."""

import pandas as pd
import json
from typing import Dict, Any, List


def format_data_for_llm(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Format transaction data for LLM analysis.
    
    Creates both JSON and text summaries of the data for LLM consumption.
    
    Args:
        df: DataFrame with transaction data
        
    Returns:
        Dictionary with 'json_summary' and 'text_summary' keys
    """
    if df.empty:
        return {
            'json_summary': {},
            'text_summary': 'Ei tapahtumadataa saatavilla.'
        }
    
    # Use adjusted_amount if available, otherwise amount
    amount_col = 'adjusted_amount' if 'adjusted_amount' in df.columns else 'amount'
    
    # JSON Summary
    json_summary = {}
    
    # Basic statistics
    total_spending = df[amount_col].sum()
    total_transactions = len(df)
    date_range = {
        'start': str(df['date'].min()) if 'date' in df.columns else None,
        'end': str(df['date'].max()) if 'date' in df.columns else None
    }
    
    json_summary['overview'] = {
        'total_spending': float(total_spending),
        'total_transactions': total_transactions,
        'date_range': date_range
    }
    
    # Spending by category
    if 'category' in df.columns:
        category_totals = df.groupby('category')[amount_col].sum().sort_values(ascending=False)
        json_summary['by_category'] = {
            cat: float(amount) for cat, amount in category_totals.items()
        }
    
    # Spending by month
    if 'year' in df.columns and 'month' in df.columns:
        monthly_totals = df.groupby(['year', 'month'])[amount_col].sum()
        json_summary['by_month'] = {
            f"{int(year)}-{int(month):02d}": float(amount) 
            for (year, month), amount in monthly_totals.items()
        }
    
    # Spending by subcategory (2nd category)
    if '2nd category' in df.columns:
        subcat_totals = df.groupby(['category', '2nd category'])[amount_col].sum().sort_values(ascending=False)
        json_summary['by_subcategory'] = {
            f"{cat} - {subcat}": float(amount)
            for (cat, subcat), amount in subcat_totals.head(20).items()  # Top 20
        }
    
    # Top merchants
    if 'merchant' in df.columns:
        merchant_totals = df.groupby('merchant')[amount_col].sum().sort_values(ascending=False)
        json_summary['top_merchants'] = {
            merchant: float(amount)
            for merchant, amount in merchant_totals.head(20).items()  # Top 20
        }
    
    # Average monthly spending
    if 'year' in df.columns and 'month' in df.columns:
        monthly_sums = df.groupby(['year', 'month'])[amount_col].sum()
        json_summary['statistics'] = {
            'average_monthly': float(monthly_sums.mean()) if len(monthly_sums) > 0 else 0.0,
            'median_monthly': float(monthly_sums.median()) if len(monthly_sums) > 0 else 0.0,
            'highest_month': {
                'month': str(monthly_sums.idxmax()) if len(monthly_sums) > 0 else None,
                'amount': float(monthly_sums.max()) if len(monthly_sums) > 0 else 0.0
            },
            'lowest_month': {
                'month': str(monthly_sums.idxmin()) if len(monthly_sums) > 0 else None,
                'amount': float(monthly_sums.min()) if len(monthly_sums) > 0 else 0.0
            }
        }
    
    # Text Summary
    text_lines = []
    text_lines.append("=== RAHOITUSTAPAHTUMIEN YHTEENVETO ===\n")
    
    text_lines.append(f"Yhteensä kulutettu: €{total_spending:,.2f}")
    text_lines.append(f"Tapahtumia yhteensä: {total_transactions}")
    if date_range['start'] and date_range['end']:
        text_lines.append(f"Aikaväli: {date_range['start']} - {date_range['end']}\n")
    
    if 'by_category' in json_summary:
        text_lines.append("\n=== KULUTUS KATEGORIOITTAIN ===")
        for cat, amount in list(json_summary['by_category'].items())[:10]:  # Top 10
            pct = (amount / total_spending * 100) if total_spending > 0 else 0
            text_lines.append(f"- {cat}: €{amount:,.2f} ({pct:.1f}%)")
    
    if 'by_month' in json_summary:
        text_lines.append("\n=== KULUTUS KUUKAUSITTAIN ===")
        for month, amount in list(json_summary['by_month'].items())[-6:]:  # Last 6 months
            text_lines.append(f"- {month}: €{amount:,.2f}")
    
    if 'statistics' in json_summary:
        stats = json_summary['statistics']
        text_lines.append("\n=== TILASTOT ===")
        text_lines.append(f"Keskiarvo kuukaudessa: €{stats['average_monthly']:,.2f}")
        text_lines.append(f"Mediaani kuukaudessa: €{stats['median_monthly']:,.2f}")
        if stats['highest_month']['month']:
            text_lines.append(f"Korkein kuukausi: {stats['highest_month']['month']} (€{stats['highest_month']['amount']:,.2f})")
        if stats['lowest_month']['month']:
            text_lines.append(f"Alin kuukausi: {stats['lowest_month']['month']} (€{stats['lowest_month']['amount']:,.2f})")
    
    if 'top_merchants' in json_summary:
        text_lines.append("\n=== TOP 10 MERCHANTIT ===")
        for merchant, amount in list(json_summary['top_merchants'].items())[:10]:
            text_lines.append(f"- {merchant}: €{amount:,.2f}")
    
    text_summary = "\n".join(text_lines)
    
    return {
        'json_summary': json_summary,
        'text_summary': text_summary
    }


def format_transactions_for_embedding(df: pd.DataFrame) -> List[str]:
    """
    Format transactions as text strings for embedding.
    
    Args:
        df: DataFrame with transaction data
        
    Returns:
        List of formatted transaction strings
    """
    if df.empty:
        return []
    
    # Use adjusted_amount if available, otherwise amount
    amount_col = 'adjusted_amount' if 'adjusted_amount' in df.columns else 'amount'
    
    transaction_texts = []
    
    for idx, row in df.iterrows():
        date = str(row.get('date', '')) if 'date' in df.columns else ''
        merchant = str(row.get('merchant', '')) if 'merchant' in df.columns else ''
        amount = float(row.get(amount_col, 0))
        category = str(row.get('category', '')) if 'category' in df.columns else ''
        subcategory = str(row.get('2nd category', '')) if '2nd category' in df.columns else ''
        
        # Format: "2025-01-01 Prisma €50.00 Ruokakauppa Yleinen"
        transaction_text = f"{date} {merchant} €{amount:.2f} {category} {subcategory}".strip()
        transaction_texts.append(transaction_text)
    
    return transaction_texts

