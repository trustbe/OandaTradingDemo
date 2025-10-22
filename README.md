# OandaTradingDemo

Automated trading system for Oanda platform using sentiment analysis from ClickHouse database. The system implements a contrarian trading strategy based on market sentiment data.

## Features

- **Dynamic Symbol Support**: Trade any currency pair or instrument available in your ClickHouse database
- **Configurable Parameters**: Adjustable threshold levels and lookback periods
- **Contrarian Strategy**: Automatically trades against extreme market sentiment
- **Position Management**: Intelligent position handling with automatic closing of opposing trades
- **Multi-Source Support**: Works with any sentiment data provider (XM, FXBlue, etc.)

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   ClickHouse DB     │────>│ Sentiment Fetcher│────>│  Trading Logic  │
│  (Sentiment Data)   │     │    (Averaging)   │     │   (Threshold)   │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
                                                              │
                                                              ▼
                                                      ┌─────────────────┐
                                                      │   Oanda API     │
                                                      │ (Execute Trades)│
                                                      └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.6+
- Oanda trading account
- Access to ClickHouse database with sentiment data

### Setup

1. Clone the repository:
```bash
git clone https://github.com/trustbe/OandaTradingDemo.git
cd OandaTradingDemo
```

2. Install dependencies:
```bash
pip install oandapyV20 requests
```

3. Configure credentials:
```bash
# Copy the example config
cp config.example.py config.py

# Edit config.py with your actual credentials
nano config.py
```

Update the following in `config.py`:
- `OANDA_API_TOKEN`: Your Oanda API token
- `CLICKHOUSE_URL`: Your ClickHouse server URL
- `CLICKHOUSE_USER`: Your ClickHouse username
- `CLICKHOUSE_PASSWORD`: Your ClickHouse password

## Usage

### Basic Usage

```bash
python3 oanda_trade_avg.py \
    --account YOUR_ACCOUNT_ID \
    --symbol XAUUSD \
    --source xm \
    --timeframe 1440 \
    --units 1000
```

### Advanced Usage with Custom Parameters

```bash
python3 oanda_trade_avg.py \
    --account YOUR_ACCOUNT_ID \
    --symbol EURUSD \
    --source fxblue \
    --timeframe 720 \
    --units 10000 \
    --threshold 7.5
```

### Command Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--account` | Yes | - | Oanda account ID |
| `--symbol` | Yes | - | Trading symbol (e.g., EURUSD, XAUUSD) |
| `--source` | Yes | - | Data source (e.g., xm, fxblue) |
| `--timeframe` | Yes | - | Lookback period in minutes for sentiment averaging (e.g., 480, 720, 1440) |
| `--units` | Yes | - | Number of units to trade |
| `--threshold` | No | 5.0 | Threshold for trading signals |

## Trading Logic

The system implements a contrarian trading strategy:

1. **Fetch Sentiment**: Retrieves average client sentiment over the specified period
2. **Calculate Signal**: Computes `50 - AVG(longval)` to get the contrarian ratio
3. **Execute Trades**:
   - If ratio < -threshold: Market is heavily long → Open SHORT position
   - If ratio > +threshold: Market is heavily short → Open LONG position
   - If -threshold ≤ ratio ≤ +threshold: Neutral zone → Close all positions

### Example Scenarios

- Sentiment shows 70% of clients are long (ratio = -20):
  - System closes any existing long positions
  - Opens a short position (trading against the crowd)

- Sentiment shows 30% of clients are long (ratio = +20):
  - System closes any existing short positions
  - Opens a long position (trading against the crowd)

- Sentiment shows 48% of clients are long (ratio = +2):
  - Within neutral zone (assuming threshold = 5)
  - System closes all positions and waits

## Database Structure

The system expects ClickHouse tables following this naming convention:
```
st_{source}_{symbol}
```

Example table names:
- `st_xm_xauusd` - XM data for Gold
- `st_fxblue_eurusd` - FXBlue data for EUR/USD
- `st_xm_gbpusd` - XM data for GBP/USD

Required table structure:
```sql
CREATE TABLE st_source_symbol (
    stamp DateTime,
    longval Float32
)
```

## Testing Sentiment Data

You can test the sentiment fetcher independently:

```bash
# Test sentiment data retrieval
python3 sentiment_fetcher_clickhouse.py
```

This will fetch and display sentiment data for various configured pairs.

## Security Considerations

- **Never commit `config.py`** to public repositories
- Use environment variables for credentials in production
- Regularly rotate API tokens
- Monitor account activity for unauthorized trades

### Using Environment Variables

The system supports environment variable overrides:

```bash
export CLICKHOUSE_USER="your_user"
export CLICKHOUSE_PASSWORD="your_password"
export CLICKHOUSE_URL="http://your-server:8123"
```

## Automation

### Using Cron (Linux/Mac)

Add to crontab for automated execution:

```bash
# Run every 4 hours
0 */4 * * * cd /path/to/OandaTradingDemo && python3 oanda_trade_avg.py --account ACCOUNT --symbol XAUUSD --source xm --timeframe 1440 --units 1000 >> trading.log 2>&1
```

### Using Task Scheduler (Windows)

Create a batch file `run_trader.bat`:
```batch
cd C:\path\to\OandaTradingDemo
python oanda_trade_avg.py --account ACCOUNT --symbol XAUUSD --source xm --timeframe 1440 --units 1000
```

Schedule it using Windows Task Scheduler.

## Monitoring

Monitor your trades through:
- Oanda web platform: https://www.oanda.com
- Oanda mobile app
- Log files from the script output

## Troubleshooting

### Common Issues

1. **"No sentiment data found"**
   - Check ClickHouse connection
   - Verify table name exists: `st_{source}_{symbol}`
   - Ensure data exists for the specified lookback period

2. **"Invalid sentiment data (longPercentage is 0)"**
   - No data returned from query
   - Check if table has recent data

3. **Connection errors**
   - Verify network connectivity
   - Check firewall rules
   - Confirm API credentials are valid

### Debug Mode

Run with verbose output:
```bash
python3 -u oanda_trade_avg.py --account ACCOUNT --symbol XAUUSD --source xm --timeframe 1440 --units 1000
```

## Risk Warning

⚠️ **IMPORTANT**: Trading foreign exchange on margin carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to trade foreign exchange, you should carefully consider your investment objectives, level of experience, and risk appetite.

## License

This project is for educational purposes. Use at your own risk.

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation above

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Disclaimer

This software is provided "as is" without warranty of any kind. The authors are not responsible for any trading losses incurred using this system.