# Usage Examples

This document provides detailed examples for using the OandaTrading system with various configurations.

## Basic Trading Scenarios

### 1. Gold (XAUUSD) Trading with XM Data

Standard configuration for trading gold:

```bash
python3 oanda_trade_avg.py \
    --account 101-001-123456-001 \
    --symbol XAUUSD \
    --source xm \
    --timeframe 1440 \
    --units 100
```

This will:
- Use XM sentiment data for Gold
- Look back 1440 minutes (24 hours)
- Use ±1% treshold for trading signals
- Trade 100 units (0.01 lot)

### 2. EUR/USD with Custom Threshold

More conservative approach with wider treshold:

```bash
python3 oanda_trade_avg.py \
    --account 101-001-123456-001 \
    --symbol EURUSD \
    --source fxblue \
    --timeframe 1440 \
    --units 10000 \
    --treshold 10.0
```

This configuration:
- Uses 24-hour sentiment average (timeframe 1440 minutes)
- Requires ±10% sentiment extreme to trigger trades
- More conservative, fewer trades
- Suitable for volatile market conditions

### 3. Aggressive Scalping Setup

For more frequent trading with tighter parameters:

```bash
python3 oanda_trade_avg.py \
    --account 101-001-123456-001 \
    --symbol GBPUSD \
    --source xm \
    --timeframe 240 \
    --units 5000 \
    --treshold 3.0
```

Features:
- 4-hour sentiment lookback (timeframe 240 minutes)
- ±3% treshold for quicker signals
- More frequent position changes
- Higher risk/reward profile

### 4. Multiple Pairs Management

Run multiple instances for different pairs:

```bash
# Terminal 1 - Gold
python3 oanda_trade_avg.py --account 101-001-123456-001 --symbol XAUUSD --source xm --timeframe 1440 --units 100

# Terminal 2 - EUR/USD
python3 oanda_trade_avg.py --account 101-001-123456-001 --symbol EURUSD --source xm --timeframe 1440 --units 10000

# Terminal 3 - GBP/USD
python3 oanda_trade_avg.py --account 101-001-123456-001 --symbol GBPUSD --source fxblue --timeframe 1440 --units 5000
```

## Sentiment Testing Examples

### Check Current Sentiment

Test sentiment data without trading:

```python
# In Python interactive mode
from sentiment_fetcher_clickhouse import get_last_sentiment

# Check Gold sentiment (8-hour average)
xau_sentiment = get_last_sentiment(source="xm", symbol="xauusd", timeframe=480)
print(f"XAU/USD sentiment: {xau_sentiment}")

# Check EUR/USD sentiment (24-hour average)
eur_sentiment = get_last_sentiment(source="fxblue", symbol="eurusd", timeframe=1440)
print(f"EUR/USD sentiment: {eur_sentiment}")
```

### Batch Sentiment Check Script

Create `check_all_sentiments.py`:

```python
from sentiment_fetcher_clickhouse import get_last_sentiment

pairs = [
    ("xm", "xauusd", 480),
    ("xm", "eurusd", 1440),
    ("fxblue", "gbpusd", 720),
    ("xm", "usdjpy", 480),
]

for source, symbol, timeframe in pairs:
    sentiment = get_last_sentiment(source, symbol, timeframe)
    if sentiment is not None:
        action = "SHORT" if sentiment < -5 else "LONG" if sentiment > 5 else "NEUTRAL"
        print(f"{symbol.upper():8} ({source:6}): {sentiment:6.1f} -> {action}")
    else:
        print(f"{symbol.upper():8} ({source:6}): No data")
```

## Automation Examples

### 1. Simple Cron Job

Run every 4 hours during market hours:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
# With 60 second timeout to prevent hanging
0 */4 * * * cd /home/user/OandaTradingDemo && timeout 60 python3 oanda_trade_avg.py --account 101-001-123456-001 --symbol XAUUSD --source xm --timeframe 1440 --units 100 >> /var/log/trading.log 2>&1
```

### 2. Advanced Scheduling with Multiple Pairs

Create `run_all_pairs.sh`:

```bash
#!/bin/bash

ACCOUNT="101-001-123456-001"
LOG_DIR="/var/log/oanda_trading"
SCRIPT_DIR="/home/user/OandaTradingDemo"

# Ensure log directory exists
mkdir -p $LOG_DIR

# Run each pair
cd $SCRIPT_DIR

echo "$(date): Starting trading cycle" >> $LOG_DIR/main.log

# Gold - Conservative (with 60s timeout)
timeout 60 python3 oanda_trade_avg.py \
    --account $ACCOUNT \
    --symbol XAUUSD \
    --source xm \
    --timeframe 720 \
    --units 100 \
    --treshold 7.5 >> $LOG_DIR/xauusd.log 2>&1

sleep 5

# EUR/USD - Standard (with 60s timeout)
timeout 60 python3 oanda_trade_avg.py \
    --account $ACCOUNT \
    --symbol EURUSD \
    --source fxblue \
    --timeframe 480 \
    --units 10000 \
    --treshold 5.0 >> $LOG_DIR/eurusd.log 2>&1

sleep 5

# GBP/USD - Aggressive (with 60s timeout)
timeout 60 python3 oanda_trade_avg.py \
    --account $ACCOUNT \
    --symbol GBPUSD \
    --source xm \
    --timeframe 240 \
    --units 5000 \
    --treshold 3.0 >> $LOG_DIR/gbpusd.log 2>&1

echo "$(date): Trading cycle completed" >> $LOG_DIR/main.log
```

Make it executable and add to cron:

```bash
chmod +x run_all_pairs.sh
crontab -e
# Add: 0 */2 * * * /home/user/OandaTradingDemo/run_all_pairs.sh
```

### 3. Python Scheduler

Create `automated_trader.py` for continuous operation:

```python
import schedule
import time
import subprocess
from datetime import datetime

def run_trading(symbol, source, units, treshold, timeframe):
    \"\"\"Execute trading for a specific symbol\"\"\"
    cmd = [
        "python3", "oanda_trade_avg.py",
        "--account", "101-001-123456-001",
        "--symbol", symbol,
        "--source", source,
        "--timeframe", str(timeframe),
        "--units", str(units),
        "--treshold", str(treshold)
    ]

    print(f"{datetime.now()}: Running {symbol}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")

# Schedule different pairs at different intervals
schedule.every(4).hours.do(lambda: run_trading("XAUUSD", "xm", 100, 5.0, 480))
schedule.every(2).hours.do(lambda: run_trading("EURUSD", "fxblue", 10000, 7.5, 720))
schedule.every(6).hours.do(lambda: run_trading("GBPUSD", "xm", 5000, 10.0, 1440))

print("Automated trader started. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Risk Management Examples

### 1. Position Size Calculation

Calculate position size based on account balance:

```python
def calculate_position_size(account_balance, risk_percent, stop_loss_pips, pip_value):
    \"\"\"
    Calculate safe position size

    Args:
        account_balance: Account balance in USD
        risk_percent: Risk per trade (e.g., 0.01 for 1%)
        stop_loss_pips: Stop loss distance in pips
        pip_value: Value per pip per unit
    \"\"\"
    risk_amount = account_balance * risk_percent
    position_size = risk_amount / (stop_loss_pips * pip_value)
    return int(position_size)

# Example: $10,000 account, 1% risk, 50 pip stop
balance = 10000
risk = 0.01
stop_pips = 50
pip_value_eurusd = 0.0001  # For 1 unit

units = calculate_position_size(balance, risk, stop_pips, pip_value_eurusd)
print(f"Safe position size: {units} units")
```

### 2. Maximum Exposure Limit

Wrapper script to limit total exposure:

```python
import oandapyV20 as opy
import oandapyV20.endpoints.accounts as accounts
from config import OANDA_API_TOKEN

def get_current_exposure(account_id):
    \"\"\"Get current total exposure\"\"\"
    client = opy.API(access_token=OANDA_API_TOKEN)
    r = accounts.AccountDetails(accountID=account_id)
    response = client.request(r)

    positions = response.get('account', {}).get('positions', [])
    total_units = sum(abs(float(p.get('long', {}).get('units', 0)) +
                          float(p.get('short', {}).get('units', 0)))
                     for p in positions)
    return total_units

# Check before trading
MAX_EXPOSURE = 50000  # Maximum total units
current = get_current_exposure("101-001-123456-001")

if current < MAX_EXPOSURE:
    # Safe to trade
    print("Proceeding with trade")
else:
    print(f"Maximum exposure reached: {current}/{MAX_EXPOSURE}")
```

## Monitoring and Alerts

### Email Alert System

```python
import smtplib
from email.mime.text import MIMEText

def send_trade_alert(subject, message):
    \"\"\"Send email alert for trades\"\"\"
    sender = "your-email@gmail.com"
    recipient = "alert-email@gmail.com"
    password = "your-app-password"

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)

# Use in trading script
sentiment = get_last_sentiment("xm", "xauusd", 480)
if abs(sentiment) > 20:  # Extreme sentiment
    send_trade_alert(
        "Extreme Sentiment Alert",
        f"XAU/USD sentiment at {sentiment}. Trade executed."
    )
```

## Backtesting Example

Simple backtesting framework:

```python
import pandas as pd
from datetime import datetime, timedelta

def backtest_strategy(symbol, source, treshold, timeframe, days_back=30):
    \"\"\"Simple backtest of the strategy\"\"\"

    results = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # This would need actual historical data
    # Placeholder for demonstration

    print(f"Backtesting {symbol} with treshold={treshold}, lookback={timeframe}min")
    print(f"Period: {start_date} to {end_date}")

    # Add your backtesting logic here
    # Query historical sentiment data
    # Simulate trades based on strategy
    # Calculate returns

    return results

# Run backtest
backtest_strategy("xauusd", "xm", treshold=1.0, timeframe=480, days_back=30)
```

## Troubleshooting Examples

### Debug Mode Script

```python
# debug_trader.py
import sys
from sentiment_fetcher_clickhouse import get_last_sentiment
from oanda_trade_avg import OandaTrader

def debug_trading(account, symbol, source):
    print("=== DEBUG MODE ===")

    # Test sentiment fetch
    print(f"\\n1. Testing sentiment fetch for {symbol} from {source}")
    sentiment = get_last_sentiment(source, symbol.lower(), 480)
    print(f"   Sentiment value: {sentiment}")

    if sentiment is None:
        print("   ERROR: Could not fetch sentiment")
        return

    # Test Oanda connection
    print(f"\\n2. Testing Oanda connection")
    try:
        trader = OandaTrader(account)
        count = trader.get_orders_count(symbol)
        print(f"   Active orders: {count}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # Test trading logic
    print(f"\\n3. Trading decision")
    if sentiment < -5:
        print(f"   Signal: SHORT (sentiment {sentiment} < -5)")
    elif sentiment > 5:
        print(f"   Signal: LONG (sentiment {sentiment} > 5)")
    else:
        print(f"   Signal: NEUTRAL (sentiment {sentiment} between -5 and 5)")

    print("\\n=== END DEBUG ===")

# Usage
debug_trading("101-001-123456-001", "XAUUSD", "xm")
```