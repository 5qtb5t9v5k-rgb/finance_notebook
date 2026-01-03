"""Vector store module for RAG implementation using ChromaDB."""

import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
import os


def initialize_vector_store(db_path: str):
    """
    Initialize Chroma vector database.
    
    Args:
        db_path: Path to the database directory
        
    Returns:
        Chroma client and collection
    """
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        raise ImportError(
            "ChromaDB package is not installed. Install it with: pip install chromadb"
        )
    
    # Create directory if it doesn't exist
    Path(db_path).mkdir(parents=True, exist_ok=True)
    
    # Initialize Chroma client (persistent mode)
    client = chromadb.PersistentClient(path=db_path)
    
    # Get or create collection
    collection_name = "transactions"
    try:
        collection = client.get_collection(name=collection_name)
    except:
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Transaction data for RAG"}
        )
    
    return client, collection


def create_embeddings(texts: List[str], api_key: str) -> List[List[float]]:
    """
    Create embeddings using OpenAI API.
    
    Args:
        texts: List of text strings to embed
        api_key: OpenAI API key
        
    Returns:
        List of embedding vectors
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )
    
    if not api_key:
        raise ValueError("API key is required")
    
    if not texts:
        return []
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Use text-embedding-3-small (cheap and fast)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        
        return [item.embedding for item in response.data]
        
    except Exception as e:
        raise Exception(f"Error creating embeddings: {str(e)}")


def store_transactions(
    df: pd.DataFrame, 
    collection_name: str, 
    api_key: str, 
    db_path: str,
    clear_existing: bool = True
):
    """
    Store transactions in vector database.
    
    Args:
        df: DataFrame with transaction data
        collection_name: Name of the collection
        api_key: OpenAI API key
        db_path: Path to the database directory
        clear_existing: If True, clear existing collection before adding new transactions
    """
    if df.empty:
        return
    
    # Initialize vector store
    client, collection = initialize_vector_store(db_path)
    
    # Clear existing collection if requested
    if clear_existing:
        try:
            # Get all existing IDs and delete them
            existing_data = collection.get()
            if existing_data and 'ids' in existing_data and existing_data['ids']:
                collection.delete(ids=existing_data['ids'])
        except Exception as e:
            # If collection is empty or doesn't exist, that's fine
            pass
    
    # Format transactions for embedding
    from src.data_formatter import format_transactions_for_embedding
    transaction_texts = format_transactions_for_embedding(df)
    
    # Create embeddings
    embeddings = create_embeddings(transaction_texts, api_key)
    
    # Prepare metadata and create unique IDs
    amount_col = 'adjusted_amount' if 'adjusted_amount' in df.columns else 'amount'
    
    ids = []
    metadatas = []
    
    for idx, row in df.iterrows():
        # Create unique ID from transaction data (date + merchant + amount + time if available)
        date_str = str(row.get('date', ''))
        merchant_str = str(row.get('merchant', ''))
        amount_val = float(row.get(amount_col, 0))
        time_str = str(row.get('time', '')) if 'time' in df.columns else ''
        
        # Create unique ID: hash of date + merchant + amount + time
        import hashlib
        unique_string = f"{date_str}|{merchant_str}|{amount_val}|{time_str}|{idx}"
        unique_id = hashlib.md5(unique_string.encode()).hexdigest()
        ids.append(unique_id)
        
        metadata = {
            'date': date_str,
            'merchant': merchant_str,
            'amount': amount_val,
            'category': str(row.get('category', '')),
            'subcategory': str(row.get('2nd category', '')),
            'index': int(idx)  # Store original index for reference
        }
        metadatas.append(metadata)
    
    # Store in Chroma
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=transaction_texts,
        metadatas=metadatas
    )


def search_relevant_transactions(
    query: str, 
    collection_name: str, 
    api_key: str, 
    db_path: str, 
    top_k: int = 10
) -> List[Dict]:
    """
    Search for relevant transactions using vector similarity.
    
    Args:
        query: User's question/query
        collection_name: Name of the collection
        api_key: OpenAI API key
        db_path: Path to the database directory
        top_k: Number of results to return
        
    Returns:
        List of relevant transactions with metadata
    """
    # Initialize vector store
    client, collection = initialize_vector_store(db_path)
    
    # Create query embedding
    query_embeddings = create_embeddings([query], api_key)
    
    if not query_embeddings:
        return []
    
    # Search in Chroma
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=top_k
    )
    
    # Format results
    relevant_transactions = []
    if results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            transaction = {
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            }
            relevant_transactions.append(transaction)
    
    return relevant_transactions

