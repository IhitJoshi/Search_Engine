# BM25-Based Stock Ranking System

## Overview

This is a **real-time stock search and ranking system** using BM25 algorithm on **tokenized stock snapshots**. Unlike traditional document search, this system treats each stock's market state as a "document" composed of symbolic tokens representing market signals.

## Core Concept

### NOT Document Retrieval
- ❌ No text documents or articles
- ❌ No semantic embeddings or LLMs
- ❌ No long-term document storage
- ✅ Real-time stock market data
- ✅ Symbolic token generation from signals
- ✅ BM25 ranking on ephemeral snapshots

### How It Works

```
Stock Data → Tokenization → BM25 Ranking → Top-K Results
    ↓            ↓              ↓              ↓
{price: +2.5%} ["price_up",   Score each    Return
{volume: +180%} "volume_high", stock by      ranked
{sector: "Tech"} "sector_tech"] relevance    symbols
```

## Architecture

### 1. **Stock Tokenizer** (`stock_tokenizer.py`)
Converts real-time stock snapshots into symbolic tokens.

**Example:**
```python
Input: {
    symbol: "AAPL",
    price_change: +2.5%,
    volume: 55M (vs avg 50M),
    sector: "Technology",
    market_cap: 2.8T
}

Output Tokens: [
    "price_up", "rising", "bullish",
    "volume_high", "active",
    "sector_technology", "technology",
    "large_cap", "mega_cap", "blue_chip",
    "aapl", "apple"
]
```

**Signal Categories:**
- **Price Movement**: `price_up`, `price_down`, `price_strong_up`, `bullish`, `bearish`
- **Volume**: `volume_high`, `volume_very_high`, `active`, `low_activity`
- **Market Cap**: `large_cap`, `mid_cap`, `small_cap`, `blue_chip`
- **Sector**: `sector_technology`, `sector_financial_services`, etc.
- **Technical**: `rsi_overbought`, `above_50ma`, `high_volatility`
- **Identity**: Company name tokens, ticker symbol

### 2. **Query Tokenizer** (`stock_tokenizer.py`)
Maps natural language queries to the same token space.

**Example:**
```python
Query: "rising tech stocks with high volume"

Tokens: [
    "price_up", "rising", "bullish",
    "sector_technology", "technology",
    "volume_high", "volume_very_high", "active"
]
```

**Keyword Mapping:**
- "rising" → `["price_up", "rising", "bullish"]`
- "tech" → `["sector_technology", "technology"]`
- "high volume" → `["volume_high", "volume_very_high"]`
- "large cap" → `["large_cap", "blue_chip"]`

### 3. **BM25 Ranker** (`bm25_stock_ranker.py`)
Ranks stocks using BM25 algorithm on tokenized snapshots.

**BM25 Formula:**
```
score = Σ IDF(qi) × (f(qi,D) × (k1 + 1)) / (f(qi,D) + k1 × (1 - b + b × |D|/avgdl))
```

Where:
- `qi`: Query token
- `f(qi,D)`: Frequency of token in stock snapshot
- `|D|`: Number of tokens in snapshot
- `avgdl`: Average snapshot length
- `IDF`: Inverse document frequency (rarity)
- `k1 = 1.5`: Term frequency saturation (default)
- `b = 0.75`: Length normalization (default)

**Why BM25?**
- ✅ Handles term frequency saturation
- ✅ Document length normalization
- ✅ Fast and deterministic
- ✅ No training required
- ✅ Production-proven (used in Elasticsearch, etc.)

### 4. **API Integration** (`api.py`)
Clean integration into Flask API with clear separation of concerns.

**Request Flow:**
```
1. User sends query: "rising tech stocks"
2. Fetch live stock data from database
3. Apply sector filters (optional)
4. Tokenize query: ["price_up", "sector_technology"]
5. Tokenize all stocks
6. Rank with BM25
7. Return top-K results with scores
```

## Parameters

### BM25 Parameters
- **k1** (default: 1.5): Controls term frequency saturation
  - Lower (1.2): Less emphasis on repeated tokens
  - Higher (2.0): More emphasis on repeated tokens
  - **Recommendation**: 1.5 for stock signals

- **b** (default: 0.75): Controls length normalization
  - 0: No normalization
  - 1: Full normalization
  - **Recommendation**: 0.75 for moderate normalization

### Tokenizer Thresholds
Can be tuned in `StockTokenizer.__init__()`:
- `price_up_threshold = 0.5%`: Minimum for "rising"
- `price_strong_up = 2.0%`: Threshold for "strong_up"
- `volume_high_threshold = 50%`: Volume spike threshold
- `rsi_overbought = 70`: RSI overbought level
- `large_cap = 200B`: Large cap threshold

## API Usage

### Search Endpoint
```bash
POST /api/search
Content-Type: application/json

{
  "query": "rising tech stocks with high volume",
  "sector": "Technology",  # optional
  "limit": 10              # optional
}
```

### Response
```json
{
  "query": "rising tech stocks with high volume",
  "sector": "Technology",
  "total_results": 3,
  "ranking_method": "bm25",
  "results": [
    {
      "symbol": "NVDA",
      "company_name": "NVIDIA Corporation",
      "sector": "Technology",
      "price": 495.00,
      "volume": 45000000,
      "change_percent": 3.8,
      "_rank": 1,
      "_score": 12.4567
    },
    ...
  ]
}
```

## Files

### Core Implementation
- **`stock_tokenizer.py`**: Stock and query tokenization
- **`bm25_stock_ranker.py`**: BM25 ranking engine
- **`api.py`**: Flask API integration
- **`app.py`**: Stock fetcher and database manager
- **`test_bm25_ranker.py`**: Test suite

### Supporting Files
- **`search.py`**: Legacy BM25 (kept for backward compatibility)
- **`preprocessing.py`**: Text preprocessing utilities
- **`database.py`**: Database utilities

## Testing

Run the test suite:
```bash
cd backend
python test_bm25_ranker.py
```

**Tests Include:**
1. Stock tokenization validation
2. Query tokenization validation
3. BM25 ranking with various queries
4. Edge case handling (empty queries, no matches, etc.)

## Workflow Example

### 1. Start Backend Server
```bash
cd backend
python api.py
```

### 2. Stock Data Auto-Fetch
Background thread fetches live data every 60 seconds for 48 stocks:
- Technology: AAPL, MSFT, NVDA, etc.
- Finance: JPM, BAC, V, MA, etc.
- Energy: XOM, CVX, BP, etc.
- Healthcare: JNJ, PFE, MRK, etc.
- Automotive: TSLA, NIO, RIVN, etc.

### 3. Search Flow
```
User Query → Query Tokenization
    ↓
Fetch Live Stock Data from DB
    ↓
Stock Tokenization (all stocks)
    ↓
BM25 Ranking
    ↓
Return Top-K Results
```

## Example Queries

| Query | Intent | Expected Tokens |
|-------|--------|-----------------|
| "rising tech stocks" | Bullish tech | `price_up`, `sector_technology` |
| "high volume stocks" | Active trading | `volume_high`, `active` |
| "large cap financials" | Big banks | `large_cap`, `sector_financial_services` |
| "falling energy stocks" | Bearish energy | `price_down`, `sector_energy` |
| "apple" | Specific company | `aapl`, `apple` |
| "stocks with momentum" | Strong movers | `price_strong_up`, `volume_high` |

## Performance

- **Tokenization**: ~0.1ms per stock
- **BM25 Ranking**: ~1-2ms for 50 stocks
- **Total Query Time**: <50ms (including DB fetch)

## Advantages

✅ **Fast**: In-memory computation, no external APIs  
✅ **Deterministic**: Same query = same results  
✅ **Explainable**: Clear token matching, no black box  
✅ **Scalable**: Handles 100s of stocks easily  
✅ **Real-time**: Works with streaming/live data  
✅ **No Training**: No ML models to train or maintain  
✅ **Production-Ready**: Battle-tested algorithm (BM25)  

## Limitations

⚠️ **No Semantic Understanding**: "profitable" won't match unless mapped  
⚠️ **Token Mapping Required**: Must maintain keyword → token mappings  
⚠️ **Fixed Thresholds**: Price/volume thresholds may need tuning  
⚠️ **English Only**: Query tokenizer assumes English keywords  

## Extending the System

### Add New Signal
1. Extract signal in `StockTokenizer.tokenize_stock()`
2. Generate tokens based on thresholds
3. Update `QueryTokenizer.keyword_map` if needed

Example - Adding P/E Ratio:
```python
# In StockTokenizer
pe_ratio = stock_data.get('pe_ratio')
if pe_ratio:
    if pe_ratio < 15:
        tokens.append('low_pe')
    elif pe_ratio > 30:
        tokens.append('high_pe')

# In QueryTokenizer
'undervalued': ['low_pe'],
'expensive': ['high_pe'],
```

### Tune BM25 Parameters
```python
# More emphasis on term frequency
stock_ranker = create_ranker(k1=2.0, b=0.75)

# Less length normalization
stock_ranker = create_ranker(k1=1.5, b=0.5)
```

## Best Practices

1. **Keep Tokens Consistent**: Query tokens must match stock tokens
2. **Use Descriptive Token Names**: `price_strong_up` > `psu`
3. **Log Token Generation**: Debug token mismatches easily
4. **Monitor Score Distribution**: Ensure meaningful score differences
5. **Validate Thresholds**: Adjust based on market conditions

## Troubleshooting

### No Results Returned
- Check if query tokens are generated
- Verify stock data is being fetched
- Ensure token mappings are correct
- Look at `_score` values in response

### Poor Ranking Quality
- Review token generation for stocks
- Adjust BM25 parameters (k1, b)
- Tune tokenizer thresholds
- Add more specific keywords to query tokenizer

### Slow Performance
- Reduce number of stocks being ranked
- Check database query performance
- Profile tokenization step

## Credits

**Algorithm**: BM25 (Robertson & Walker, 1994)  
**Implementation**: Custom for real-time stock ranking  
**Backend**: Python + Flask + SQLite  
**Data Source**: yfinance (Yahoo Finance)  

---

**Questions?** Review the code comments - they explain WHY, not just WHAT.
