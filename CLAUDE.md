# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated trading system that executes trades on the Oanda platform based on market sentiment data. The system fetches sentiment data from external sources (XM or FXBlue) and makes trading decisions based on client positioning ratios.

## Architecture

### Core Components

1. **oanda_trade_avg.py**: Main trading script that coordinates the entire trading flow
   - Connects to Oanda API for trade execution
   - Implements trading logic based on sentiment thresholds (±5%)
   - Manages position opening/closing based on market sentiment

2. **sentiment_fetcher_xauusd.py**: Primary sentiment data fetcher
   - Connects to ClickHouse database at super.fxbold.com
   - Retrieves 24-hour average client sentiment for XAUUSD
   - Supports both XM and FXBlue data sources

3. **sentiment_fetcher.py**: Alternative sentiment fetcher (appears to be legacy)
   - Uses FXBold API for sentiment history
   - Supports multiple symbols and timeframes

### Trading Logic Flow

1. Fetch sentiment data from ClickHouse (24h average)
2. Calculate client ratio: `50 - AVG(longval)`
3. Execute trades based on thresholds:
   - Ratio < -5: Close longs, open short position
   - Ratio > 5: Close shorts, open long position
   - -5 ≤ Ratio ≤ 5: Close all positions

## Development Commands

### Running the Trading Script
```bash
python3 oanda_trade_avg.py --account <ACCOUNT_ID> --symbol <SYMBOL> --source <xm|fxblue> --timeframe <MINUTES> --units <TRADE_SIZE>
```

### Testing Sentiment Fetchers
```bash
# Test XAU/USD sentiment fetcher
python3 sentiment_fetcher_xauusd.py

# Test generic sentiment fetcher
python3 sentiment_fetcher.py
```

## Dependencies

Required Python packages:
- oandapyV20 (Oanda API client)
- requests (HTTP client)

## API Endpoints

- **Oanda API**: Uses oandapyV20 library with API token authentication
- **ClickHouse**: http://super.fxbold.com:8123 (requires credentials)
- **FXBold API**: https://data.fxbold.com/api/get_sentiment_history

## Important Notes

- The system uses a 480-minute (8-hour) window for sentiment averaging in ClickHouse queries
- API credentials are embedded in code - consider using environment variables for production
- The main script expects sentiment_fetcher_xauusd to be available as an import