"""
Main Application Entry Point - Stock Search Engine
Coordinates data loading, indexing, and serves as the main orchestrator
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
import pandas as pd

from preprocessing import load_dataset, tokenize_all_columns
from search import BM25Search
from stock_fetcher import create_table as create_stocks_table
from database import init_db as init_users_db

# Setup logging with ASCII-only characters for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class StockSearchApp:
    """
    Main application class that orchestrates the stock search engine
    """
    
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.search_engine = BM25Search()
        self.index_data: Optional[Dict[str, Any]] = None
        
    def initialize_databases(self):
        """Initialize all required databases"""
        logger.info("Initializing databases...")
        try:
            # Initialize users database
            init_users_db()
            logger.info("[SUCCESS] Users database initialized")
            
            # Initialize stocks database
            create_stocks_table()
            logger.info("[SUCCESS] Stocks database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            raise
    
    def load_and_preprocess_data(self, dataset_path: str = None):
        """
        Load and preprocess the dataset
        
        Args:
            dataset_path: Optional custom path to dataset file
        """
        logger.info("Loading and preprocessing dataset...")
        
        try:
            # If no path provided, try multiple possible locations
            if dataset_path is None:
                possible_paths = [
                    os.path.join("data", "dataset.csv"),
                    os.path.join("..", "data", "dataset.csv"),
                    "dataset.csv",
                    os.path.join(os.path.dirname(__file__), "..", "data", "dataset.csv")
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        dataset_path = path
                        break
                else:
                    # If no dataset found, create a sample one
                    logger.warning("No dataset file found. Creating sample dataset...")
                    self._create_sample_dataset()
                    dataset_path = "sample_dataset.csv"
            
            # Load dataset
            self.df = load_dataset(dataset_path)
            
            # Show dataset info
            logger.info(f"Dataset shape: {self.df.shape}")
            logger.info(f"Dataset columns: {list(self.df.columns)}")
            
            # Display sample data
            if not self.df.empty:
                logger.info("First 3 rows of dataset:")
                for col in self.df.columns:
                    if col != 'tokens':  # Don't show tokens in preview
                        sample_values = self.df[col].head(3).tolist()
                        logger.info(f"  {col}: {sample_values}")
            
            # Tokenize all columns
            self.df = tokenize_all_columns(self.df)
            
            # Show tokenization results
            if 'tokens' in self.df.columns:
                logger.info("Tokenization sample:")
                for i, tokens in enumerate(self.df['tokens'].head(2)):
                    logger.info(f"  Document {i}: {tokens[:10]}...")  # First 10 tokens
            
            logger.info("[SUCCESS] Dataset loaded and preprocessed successfully")
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    def _create_sample_dataset(self):
        """Create a sample dataset for testing"""
        sample_data = {
            'company_name': [
                'Apple Inc.', 
                'Microsoft Corporation', 
                'Google LLC',
                'Amazon.com Inc.',
                'Tesla Inc.'
            ],
            'symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
            'sector': ['Technology', 'Technology', 'Technology', 'Consumer Cyclical', 'Automotive'],
            'industry': [
                'Consumer Electronics', 
                'Software—Infrastructure', 
                'Internet Content & Information',
                'Internet Retail',
                'Auto Manufacturers'
            ],
            'description': [
                'Apple designs a wide variety of consumer electronic devices, including smartphones, personal computers, tablets, wearables, and accessories.',
                'Microsoft develops and licenses consumer and enterprise software, including Windows operating systems and Office productivity suite.',
                'Google is the largest internet search engine and a dominant player in online advertising and cloud computing.',
                'Amazon is a leading online retailer and cloud service provider with extensive e-commerce operations.',
                'Tesla designs and manufactures electric vehicles, energy storage systems, and solar panels.'
            ],
            'country': ['USA', 'USA', 'USA', 'USA', 'USA']
        }
        
        df = pd.DataFrame(sample_data)
        df.to_csv('sample_dataset.csv', index=False)
        logger.info("Sample dataset created: sample_dataset.csv")
    
    def initialize_search_engine(self):
        """Initialize the search engine with preprocessed data"""
        logger.info("Initializing search engine...")
        
        if self.df is None:
            raise ValueError("Data not loaded. Call load_and_preprocess_data() first.")
        
        try:
            # Build search index directly from DataFrame
            self.search_engine.build_index(self.df)
            logger.info("[SUCCESS] Search engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize search engine: {e}")
            raise
    
    def search(self, query: str, top_n: int = 10):
        """
        Perform a search query
        
        Args:
            query: Search query string
            top_n: Number of top results to return
            
        Returns:
            List of search results
        """
        if self.search_engine.inverted_index is None:
            raise ValueError("Search engine not initialized")
        
        logger.info(f"Searching for: '{query}'")
        return self.search_engine.search(query, self.df, top_n)
    
    def get_app_info(self) -> Dict[str, Any]:
        """Get application information"""
        return {
            'status': 'ready' if self.df is not None else 'initializing',
            'documents': len(self.df) if self.df is not None else 0,
            'search_terms': len(self.search_engine.inverted_index) if self.search_engine.inverted_index else 0,
            'dataset_columns': list(self.df.columns) if self.df is not None else []
        }
    
    def run_test_search(self):
        """Run test searches to verify functionality"""
        if self.df is None or self.search_engine.inverted_index is None:
            logger.warning("Cannot run test search - app not fully initialized")
            return
        
        test_queries = [
            "technology",
            "apple",
            "software",
            "internet"
        ]
        
        logger.info("=" * 50)
        logger.info("RUNNING TEST SEARCHES")
        logger.info("=" * 50)
        
        for query in test_queries:
            try:
                results = self.search(query, top_n=3)
                logger.info(f"Query: '{query}' -> Found {len(results)} results")
                
                for i, (doc_idx, score) in enumerate(results, 1):
                    # Create preview
                    preview = ""
                    for col in self.df.columns:
                        if col != 'tokens' and pd.notna(self.df.iloc[doc_idx][col]):
                            preview += str(self.df.iloc[doc_idx][col]) + " "
                    preview = preview.strip()[:100] + "..." if len(preview) > 100 else preview
                    
                    logger.info(f"  {i}. Doc {doc_idx} (Score: {score:.4f})")
                    logger.info(f"     Preview: {preview}")
                    
            except Exception as e:
                logger.error(f"Test search failed for '{query}': {e}")

def main():
    """Main application entry point"""
    logger.info("=" * 60)
    logger.info("STOCK SEARCH ENGINE - APPLICATION STARTUP")
    logger.info("=" * 60)
    
    app = StockSearchApp()
    
    try:
        # Step 1: Initialize databases
        app.initialize_databases()
        
        # Step 2: Load and preprocess data
        app.load_and_preprocess_data()
        
        # Step 3: Initialize search engine
        app.initialize_search_engine()
        
        # Step 4: Display application info
        app_info = app.get_app_info()
        logger.info("=" * 50)
        logger.info("APPLICATION INFORMATION")
        logger.info("=" * 50)
        for key, value in app_info.items():
            logger.info(f"  {key}: {value}")
        
        # Step 5: Run test searches
        app.run_test_search()
        
        logger.info("=" * 60)
        logger.info("[SUCCESS] APPLICATION STARTUP COMPLETED")
        logger.info("=" * 60)
        
        return app
        
    except Exception as e:
        logger.error(f"[ERROR] Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the application
    main()