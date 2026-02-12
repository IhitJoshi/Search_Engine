"""
Quick setup script for local development
Creates necessary databases and files
"""

import sqlite3
import pandas as pd
import os
import sys

def create_stocks_database():
    """Create stocks.db with sample data"""
    print("📦 Creating stocks.db database...")
    
    conn = sqlite3.connect('stocks.db')
    cursor = conn.cursor()
    
    # Create stocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            sector TEXT,
            price REAL,
            volume INTEGER,
            average_volume INTEGER,
            market_cap REAL,
            change_percent REAL,
            summary TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample stocks
    sample_stocks = [
        ('AAPL', 'Apple Inc.', 'Technology', 175.43, 50000000, 45000000, 2750000000000, 1.25, 
         'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company is known for iPhone, iPad, Mac, Apple Watch, and AirPods.'),
        
        ('MSFT', 'Microsoft Corporation', 'Technology', 378.91, 25000000, 23000000, 2820000000000, 0.85,
         'Microsoft Corporation develops, licenses, and supports software products, services, and devices worldwide. Known for Windows OS, Office suite, Azure cloud services, and LinkedIn.'),
        
        ('GOOGL', 'Alphabet Inc.', 'Technology', 141.80, 20000000, 18000000, 1750000000000, -0.45,
         'Alphabet Inc. offers various products and platforms including Google Search, Android, Chrome, YouTube, Google Cloud, and hardware products like Pixel phones.'),
        
        ('AMZN', 'Amazon.com Inc.', 'Consumer Cyclical', 178.25, 45000000, 42000000, 1830000000000, 1.75,
         'Amazon.com Inc. engages in retail sale of consumer products and cloud computing services. Amazon Web Services (AWS) provides cloud infrastructure services.'),
        
        ('TSLA', 'Tesla Inc.', 'Automotive', 248.50, 95000000, 88000000, 790000000000, 3.20,
         'Tesla Inc. designs, develops, manufactures, and sells electric vehicles, energy generation and storage systems. Known for Model S, Model 3, Model X, and Model Y.'),
        
        ('NVDA', 'NVIDIA Corporation', 'Technology', 875.28, 35000000, 32000000, 2160000000000, 2.10,
         'NVIDIA Corporation provides graphics and compute solutions. Specializes in GPUs for gaming, data centers, and artificial intelligence applications.'),
        
        ('META', 'Meta Platforms Inc.', 'Technology', 484.03, 18000000, 16000000, 1230000000000, -1.25,
         'Meta Platforms Inc. engages in social media and metaverse. Products include Facebook, Instagram, WhatsApp, and Messenger platforms.'),
        
        ('JPM', 'JPMorgan Chase & Co.', 'Financial Services', 185.92, 8000000, 7500000, 540000000000, 0.65,
         'JPMorgan Chase & Co. operates as a financial services company. Provides investment banking, financial services for consumers and businesses, and asset management.'),
        
        ('V', 'Visa Inc.', 'Financial Services', 276.54, 6000000, 5800000, 580000000000, 0.45,
         'Visa Inc. operates a retail electronic payments network worldwide. Facilitates digital payments between consumers, merchants, financial institutions, and government entities.'),
        
        ('WMT', 'Walmart Inc.', 'Consumer Defensive', 168.37, 7000000, 6500000, 460000000000, -0.30,
         'Walmart Inc. operates retail stores, supercenters, and e-commerce platforms. Offers groceries, electronics, home goods, and pharmacy services.'),
        
        ('JNJ', 'Johnson & Johnson', 'Healthcare', 158.72, 5000000, 4800000, 390000000000, 0.15,
         'Johnson & Johnson researches, develops, manufactures, and sells healthcare products. Focuses on pharmaceuticals, medical devices, and consumer health products.'),
        
        ('PG', 'Procter & Gamble Co.', 'Consumer Defensive', 162.45, 5500000, 5200000, 385000000000, 0.25,
         'Procter & Gamble Co. provides consumer packaged goods. Products include beauty, grooming, health care, fabric care, and home care products.'),
        
        ('DIS', 'The Walt Disney Company', 'Communication Services', 112.85, 9000000, 8500000, 205000000000, 1.95,
         'The Walt Disney Company operates entertainment and media businesses. Segments include streaming (Disney+), theme parks, studio entertainment, and consumer products.'),
        
        ('NFLX', 'Netflix Inc.', 'Communication Services', 485.20, 4000000, 3800000, 210000000000, -0.85,
         'Netflix Inc. provides entertainment services. Streaming platform offers TV series, films, and games across various genres and languages.'),
        
        ('BA', 'The Boeing Company', 'Industrials', 184.32, 6500000, 6200000, 112000000000, 1.45,
         'The Boeing Company designs, develops, manufactures, and sells commercial jetliners, defense systems, and space vehicles worldwide.')
    ]
    
    for stock in sample_stocks:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO stocks 
                (symbol, company_name, sector, price, volume, average_volume, market_cap, change_percent, summary, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', stock)
        except Exception as e:
            print(f"Error inserting {stock[0]}: {e}")
    
    conn.commit()
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM stocks')
    count = cursor.fetchone()[0]
    print(f"✅ Created stocks.db with {count} stocks")
    
    conn.close()


def create_dataset_csv():
    """Create dataset.csv from stocks.db"""
    print("\n📄 Creating dataset.csv...")
    
    conn = sqlite3.connect('stocks.db')
    df = pd.read_sql_query('SELECT * FROM stocks', conn)
    conn.close()
    
    # Save to data directory
    os.makedirs('data', exist_ok=True)
    csv_path = os.path.join('data', 'dataset.csv')
    df.to_csv(csv_path, index=False)
    
    print(f"✅ Created {csv_path} with {len(df)} stocks")


def main():
    """Run setup"""
    print("="*60)
    print("🚀 Setting up Stock Search Engine - Local Development")
    print("="*60)
    
    # Change to backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"\n📁 Working directory: {os.getcwd()}\n")
    
    try:
        # Create databases
        create_stocks_database()
        create_dataset_csv()
        
        print("\n" + "="*60)
        print("✅ Setup Complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Activate your virtual environment:")
        print("   .\\venv\\Scripts\\activate")
        print("\n2. Install dependencies (if not done):")
        print("   pip install -r requirements.txt")
        print("   python -m spacy download en_core_web_sm")
        print("\n3. Run the backend server:")
        print("   python api.py")
        print("\n4. Backend will be available at: http://localhost:5000")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
