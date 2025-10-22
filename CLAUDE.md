# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated trading system that executes trades on the Oanda platform based on market sentiment data. The system fetches sentiment data from external sources (XM or FXBlue) and makes trading decisions based on client positioning ratios.

## Architecture

### Core Components

1. **oanda_trade_avg.py**: Main trading script that coordinates the entire trading flow
   - Connects to Oanda API for trade execution
   - Implements trading logic based on sentiment tresholds (±1%)
   - Manages position opening/closing based on market sentiment

2. **sentiment_fetcher_clickhouse.py**: ClickHouse sentiment data fetcher
   - Connects to ClickHouse database at super.fxbold.com
   - Dynamically queries any st_{source}_{symbol} table
   - Supports configurable lookback periods (timeframe in minutes)
   - Works with any data source (XM, FXBlue, etc.)

3. **config.py**: Configuration file
   - Stores Oanda API credentials
   - Stores ClickHouse connection details
   - Gitignored for security

### Trading Logic Flow

1. Fetch sentiment data from ClickHouse (configurable timeframe)
2. Calculate client ratio: `50 - AVG(longval)`
3. Execute trades based on configurable treshold (default ±5):
   - Ratio < -treshold: Close longs, open short position
   - Ratio > +treshold: Close shorts, open long position
   - Within treshold range: Close all positions

## Development Commands

### Running the Trading Script
```bash
python3 oanda_trade_avg.py --account <ACCOUNT_ID> --symbol <SYMBOL> --source <xm|fxblue> --timeframe <MINUTES> --units <TRADE_SIZE> [--treshold <VALUE>]
```

### Testing Sentiment Fetcher
```bash
# Test sentiment fetcher with various sources/symbols
python3 sentiment_fetcher_clickhouse.py
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

- The timeframe parameter controls the lookback period for sentiment averaging in ClickHouse queries
- API credentials are stored in config.py (gitignored for security)
- The system supports any source/symbol combination via dynamic table names: st_{source}_{symbol}
- Threshold and timeframe are fully configurable via command-line arguments