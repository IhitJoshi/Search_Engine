"""
Create a sample dataset for testing the search engine
"""

import pandas as pd
import os

def create_sample_dataset():
    """Create a sample stock dataset"""
    
    sample_data = {
        'company_name': [
            'Apple Inc.', 
            'Microsoft Corporation', 
            'Google LLC',
            'Amazon.com Inc.',
            'Tesla Inc.',
            'NVIDIA Corporation',
            'Meta Platforms Inc.',
            'Netflix Inc.',
            'Adobe Inc.',
            'Intel Corporation'
        ],
        'symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'ADBE', 'INTC'],
        'sector': [
            'Technology', 
            'Technology', 
            'Technology', 
            'Consumer Cyclical', 
            'Automotive',
            'Technology',
            'Communication Services',
            'Communication Services',
            'Technology',
            'Technology'
        ],
        'industry': [
            'Consumer Electronics', 
            'Software—Infrastructure', 
            'Internet Content & Information',
            'Internet Retail',
            'Auto Manufacturers',
            'Semiconductors',
            'Internet Content & Information',
            'Entertainment',
            'Software—Infrastructure',
            'Semiconductors'
        ],
        'description': [
            'Apple designs a wide variety of consumer electronic devices, including smartphones, personal computers, tablets, wearables, and accessories.',
            'Microsoft develops and licenses consumer and enterprise software, including Windows operating systems and Office productivity suite.',
            'Google is the largest internet search engine and a dominant player in online advertising and cloud computing.',
            'Amazon is a leading online retailer and cloud service provider with extensive e-commerce operations.',
            'Tesla designs and manufactures electric vehicles, energy storage systems, and solar panels.',
            'NVIDIA is a leading manufacturer of graphics processing units for gaming and professional markets.',
            'Meta operates social networking platforms including Facebook, Instagram, and WhatsApp.',
            'Netflix provides streaming entertainment service with movies, TV shows, and original content.',
            'Adobe provides creative software products for design, photography, video editing, and web development.',
            'Intel designs and manufactures microprocessors and other semiconductor components for computing devices.'
        ],
        'country': ['USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA'],
        'market_cap_billions': [2800, 2100, 1800, 1600, 600, 800, 900, 250, 200, 150]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save to multiple locations for testing
    df.to_csv('data/dataset.csv', index=False)
    df.to_csv('sample_dataset.csv', index=False)
    
    print("Sample dataset created successfully!")
    print(f"Files created:")
    print(f"- data/dataset.csv")
    print(f"- sample_dataset.csv")
    print(f"\nDataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return df

if __name__ == "__main__":
    create_sample_dataset()