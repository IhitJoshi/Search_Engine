# Response Synthesizer - Documentation

## Overview

The **Response Synthesizer** is a pure transformation layer that converts ranked stock results into structured, human-readable API responses. It operates deterministically using static token-to-explanation mappings.

## Purpose

### What It Does
- ✅ Transforms BM25-ranked results into JSON-ready responses
- ✅ Maps matched tokens to human-readable explanations
- ✅ Structures data for frontend consumption (Chart.js, React)
- ✅ Provides metadata about the search query

### What It Does NOT Do
- ❌ No data fetching
- ❌ No ranking or scoring
- ❌ No text generation or LLMs
- ❌ No predictions or advice
- ❌ No frontend logic

## Architecture

### Data Flow

```
BM25 Ranker Output
    ↓
[(symbol, score, stock_data_with_tokens), ...]
    ↓
Response Synthesizer
    ↓
{
  metadata: {...},
  results: [
    {
      symbol, rank, score,
      reasons: ["Price is rising", "High trading volume"],
      metrics: {...}
    }
  ]
}
    ↓
JSON API Response
```

### Separation of Concerns

```
┌─────────────────────┐
│  Stock Fetcher      │ → Fetches live data
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Stock Tokenizer    │ → Signals → Tokens
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  BM25 Ranker        │ → Ranks stocks
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Response Synthesizer│ → Formats response  ← YOU ARE HERE
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  API Endpoint       │ → Returns JSON
└─────────────────────┘
```

## Core Components

### 1. Token Explanation Map

**Static dictionary mapping tokens to human-readable text:**

```python
TOKEN_EXPLANATIONS = {
    'price_up': 'Price is rising',
    'volume_high': 'High trading volume',
    'sector_technology': 'Technology sector',
    'rsi_overbought': 'RSI indicates overbought conditions',
    # ... 45+ mappings
}
```

**Why static?**
- Deterministic: Same token = same explanation
- No hallucination: Only factual signal descriptions
- Fast: Simple dictionary lookup
- Testable: Easy to validate

### 2. ResponseSynthesizer Class

**Main class handling response transformation:**

```python
synthesizer = ResponseSynthesizer()
response = synthesizer.synthesize_response(
    query="rising tech stocks",
    ranked_results=[...],
    ranking_method='bm25'
)
```

**Key Methods:**

- `synthesize_response()` - Main entry point
- `_process_single_result()` - Transform one stock result
- `_generate_reasons()` - Map tokens to explanations
- `_get_token_explanation()` - Look up explanation

### 3. Convenience Function

**For quick usage without instantiation:**

```python
from response_synthesizer import synthesize_search_response

response = synthesize_search_response(
    query="high volume",
    ranked_results=ranked_stocks
)
```

## Response Structure

### Complete Response Format

```json
{
  "metadata": {
    "query": "rising tech stocks",
    "timestamp": "2026-02-01T14:30:00.000Z",
    "total_results": 3,
    "ranking_method": "bm25",
    "sector_filter": "Technology"  // optional
  },
  "results": [
    {
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "sector": "Technology",
      "rank": 1,
      "score": 12.4567,
      "reasons": [
        "Bullish price action",
        "Large market capitalization",
        "Price is rising",
        "Technology sector"
      ],
      "metrics": {
        "price": 175.50,
        "volume": 55000000,
        "average_volume": 50000000,
        "market_cap": 2800000000000,
        "change_percent": 2.5,
        "last_updated": "2026-02-01 14:30:00"
      },
      "summary": "Apple Inc. designs, manufactures..."
    }
  ]
}
```

### Response Parts Explained

#### 1. Metadata
- **query**: Original user query
- **timestamp**: When response was generated (ISO 8601)
- **total_results**: Number of stocks returned
- **ranking_method**: Algorithm used ("bm25", "default")
- **Custom fields**: Any additional metadata

#### 2. Results Array
Each result contains:

**Identification**
- `symbol`: Stock ticker (e.g., "AAPL")
- `company_name`: Full company name
- `sector`: Standardized sector

**Ranking Info**
- `rank`: Position in results (1, 2, 3...)
- `score`: BM25 relevance score

**Explanations**
- `reasons`: Array of human-readable strings
  - Derived ONLY from matched tokens
  - No predictions or speculation
  - Sorted alphabetically for consistency

**Current State**
- `metrics`: Live stock data
  - `price`: Current price
  - `volume`: Current trading volume
  - `change_percent`: Price change %
  - `market_cap`: Market capitalization
  - `last_updated`: Timestamp of data

**Context**
- `summary`: Brief company description (optional)

## Usage

### Basic Usage

```python
from response_synthesizer import response_synthesizer

# Input from BM25 ranker
ranked_results = [
    {
        'symbol': 'AAPL',
        'company_name': 'Apple Inc.',
        'price': 175.50,
        'volume': 55000000,
        'change_percent': 2.5,
        '_score': 12.45,
        'tokens': ['price_up', 'sector_technology', 'large_cap']
    }
]

# Synthesize response
response = response_synthesizer.synthesize_response(
    query="rising tech stocks",
    ranked_results=ranked_results,
    ranking_method='bm25'
)

# Use in API
return jsonify(response)
```

### Custom Token Explanations

```python
from response_synthesizer import ResponseSynthesizer

# Add custom explanations
synthesizer = ResponseSynthesizer()
synthesizer.add_token_explanation('custom_signal', 'Custom market signal detected')

response = synthesizer.synthesize_response(...)
```

### With Additional Metadata

```python
response = response_synthesizer.synthesize_response(
    query="tech stocks",
    ranked_results=results,
    ranking_method='bm25',
    metadata={
        'sector_filter': 'Technology',
        'user_id': 'user123',
        'request_id': 'req-456'
    }
)
```

## Token → Explanation Examples

### Price Signals
| Token | Explanation |
|-------|-------------|
| `price_up` | Price is rising |
| `price_strong_up` | Strong upward price movement |
| `bullish` | Bullish price action |
| `falling` | Downward price trend detected |

### Volume Signals
| Token | Explanation |
|-------|-------------|
| `volume_high` | High trading volume |
| `volume_very_high` | Unusually high trading volume |
| `active` | Active trading activity |

### Market Cap
| Token | Explanation |
|-------|-------------|
| `large_cap` | Large market capitalization |
| `blue_chip` | Blue chip stock |
| `small_cap` | Small market capitalization |

### Sectors
| Token | Explanation |
|-------|-------------|
| `sector_technology` | Technology sector |
| `sector_financial_services` | Financial services sector |
| `sector_*` | [Dynamic] * sector |

### Technical Indicators
| Token | Explanation |
|-------|-------------|
| `rsi_overbought` | RSI indicates overbought conditions |
| `above_50ma` | Price above 50-day moving average |
| `high_volatility` | High volatility |

## Integration with API

### In api.py

```python
from response_synthesizer import response_synthesizer

@app.route('/api/search', methods=['POST'])
def search():
    # ... fetch data, rank with BM25 ...
    
    # Convert ranker output to synthesizer input
    formatted_results = []
    for symbol, score, stock_data in ranked_results:
        result = {**stock_data, '_score': score}
        formatted_results.append(result)
    
    # Synthesize response
    response = response_synthesizer.synthesize_response(
        query=query,
        ranked_results=formatted_results,
        ranking_method='bm25'
    )
    
    return jsonify(response)
```

## Testing

### Run Test Suite

```bash
cd backend
python test_response_synthesizer.py
```

### Test Coverage

1. **Token Explanation Mappings**
   - Validates all common tokens have explanations
   - Tests dynamic pattern matching (sector_*)

2. **Response Structure**
   - Validates metadata fields
   - Validates result fields
   - Validates metrics structure

3. **Reasons Generation**
   - Tests token-to-explanation conversion
   - Validates deduplication
   - Tests sorting

4. **Edge Cases**
   - Empty results
   - Empty token lists
   - Unknown tokens
   - Dynamic sector tokens

5. **Full Integration**
   - End-to-end transformation
   - Realistic data scenarios

### Expected Output

```
============================================================
TEST SUMMARY
============================================================
  ✓ PASS: Token Explanations
  ✓ PASS: Response Structure
  ✓ PASS: Reasons Generation
  ✓ PASS: Edge Cases
  ✓ PASS: Full Integration

============================================================
✓ ALL TESTS PASSED
============================================================
```

## Design Principles

### 1. Determinism
- Same input = same output
- No randomness
- No external dependencies
- Fully testable

### 2. Separation of Concerns
- Only handles response formatting
- No data fetching
- No ranking logic
- No frontend assumptions

### 3. Explainability
- Clear token mappings
- Human-readable reasons
- Traceable explanations
- No black boxes

### 4. Maintainability
- Simple dictionary lookups
- Clear function boundaries
- Comprehensive tests
- Well-documented

## Frontend Consumption

### Display Reasons

```javascript
// React component
{result.reasons.map(reason => (
  <li key={reason}>{reason}</li>
))}
```

### Use Metrics for Charts

```javascript
// Chart.js
const chartData = {
  labels: results.map(r => r.symbol),
  datasets: [{
    label: 'Price',
    data: results.map(r => r.metrics.price)
  }]
};
```

### Show Rank & Score

```javascript
// Display ranking
<span>#{result.rank} (score: {result.score})</span>
```

## Performance

- **Token lookup**: O(1) dictionary access
- **Reason generation**: O(n) where n = number of tokens
- **Response synthesis**: O(m) where m = number of results
- **Total time**: <1ms for typical queries

## Error Handling

### Empty Results
```python
# Returns valid structure with 0 results
response = {
  'metadata': {'total_results': 0, ...},
  'results': []
}
```

### Unknown Tokens
```python
# Silently ignores unknown tokens
tokens = ['price_up', 'unknown_xyz']
reasons = ['Price is rising']  # only known tokens
```

### Missing Fields
```python
# Gracefully handles None values
'price': stock_data.get('price')  # None if missing
```

## Extending

### Add New Token Explanation

```python
# In TOKEN_EXPLANATIONS dictionary
TOKEN_EXPLANATIONS['new_signal'] = 'New signal description'
```

### Add Dynamic Pattern

```python
# In _get_token_explanation() method
if token.startswith('indicator_'):
    indicator_name = token.replace('indicator_', '').upper()
    return f"{indicator_name} indicator signal"
```

### Custom Synthesizer

```python
custom_explanations = {
    'custom_token': 'Custom explanation'
}
synthesizer = ResponseSynthesizer(token_explanations=custom_explanations)
```

## Summary

The Response Synthesizer is a **pure, deterministic transformation layer** that:

✅ Converts ranked data → structured responses  
✅ Maps tokens → human-readable explanations  
✅ Provides metadata for frontend  
✅ Maintains separation of concerns  
✅ Operates without side effects  
✅ Is fully testable and maintainable  

**Status**: Production-ready ✅
