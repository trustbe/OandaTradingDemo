"""
ClickHouse Sentiment Data Fetcher

This module fetches market sentiment data from ClickHouse database.
It supports any data source (XM, FXBlue, etc.) and trading symbol combination
by dynamically querying tables named st_{source}_{symbol}.

The sentiment ratio is calculated as: 50 - AVG(longval)
- Positive values indicate clients are net short (contrarian signal to go LONG)
- Negative values indicate clients are net long (contrarian signal to go SHORT)
"""

import requests
import json
import os
from config import CLICKHOUSE_URL, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD

# Allow environment variables to override configuration file settings
# This is useful for production deployments with external secret management
CLICKHOUSE_URL = os.getenv("CLICKHOUSE_URL", CLICKHOUSE_URL)
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", CLICKHOUSE_USER)
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", CLICKHOUSE_PASSWORD)


def get_last_sentiment(source="xm", symbol="xauusd", timeframe=480):
    """
    Fetch the average client sentiment from ClickHouse for any source/symbol combination.

    This function queries ClickHouse tables following the naming convention: st_{source}_{symbol}
    For example: st_xm_xauusd, st_fxblue_eurusd, etc.

    Args:
        source (str): Data provider name (e.g., "xm" for XM.com broker data,
                     "fxblue" for FXBlue sentiment data). Must match the table
                     name prefix in ClickHouse database.
        symbol (str): Trading instrument (e.g., "xauusd" for Gold, "eurusd" for EUR/USD).
                     Underscores and hyphens are automatically removed for table lookup.
        timeframe (int): Lookback period in minutes for sentiment averaging.
                        Common values: 480 (8 hours), 720 (12 hours), 1440 (24 hours).

    Returns:
        float: Rounded client ratio (sentiment value) or None if error occurs.
               Positive = clients net short, Negative = clients net long.
    """
    # Normalize symbol to lowercase and remove special characters for ClickHouse table name
    # Example: "XAU_USD" or "XAU-USD" becomes "xauusd"
    symbol = symbol.lower().replace('_', '').replace('-', '')

    # Build dynamic table name following convention: st_{source}_{symbol}
    # Example: source="xm", symbol="xauusd" → "default.st_xm_xauusd"
    table_name = f"default.st_{source}_{symbol}"

    # Calculate client ratio: 50 - AVG(longval)
    # If 60% are long, longval=60, so client_ratio = 50 - 60 = -10 (net long)
    # If 40% are long, longval=40, so client_ratio = 50 - 40 = +10 (net short)
    query = f"""
    SELECT ROUND(50 - AVG(longval), 1) AS client_ratio
    FROM {table_name}
    WHERE stamp >= now() - INTERVAL {timeframe} MINUTE
    FORMAT JSONEachRow;
    """

    print(f"Querying table: {table_name} with {timeframe} minute lookback")

    try:
        # Execute query with 10-second timeout to prevent hanging
        response = requests.post(
            CLICKHOUSE_URL,
            params={
                "user": CLICKHOUSE_USER,
                "password": CLICKHOUSE_PASSWORD,
                "query": query,
            },
            timeout=10,
        )
        response.raise_for_status()  # Raise exception for HTTP errors

        # Parse response - ClickHouse returns JSONEachRow format (one JSON per line)
        lines = response.text.strip().splitlines()
        if not lines:
            return None  # No data available

        data = json.loads(lines[0])
        return float(data["client_ratio"]) if data.get("client_ratio") is not None else None

    except requests.exceptions.RequestException as e:
        print(f"[HTTP error] {e}")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"[Parse error] {e}")
    except Exception as e:
        print(f"[Unexpected error] {e}")

    return None


if __name__ == "__main__":
    # Test with different sources and symbols
    test_cases = [
        ("xm", "xauusd", 480),
        ("fxblue", "xauusd", 480),
        ("xm", "eurusd", 1440),
    ]

    for src, sym, tf in test_cases:
        result = get_last_sentiment(src, sym, tf)
        if result is not None:
            print(f"{src.upper()} {sym.upper()} ({tf}min avg) client ratio: {result}")
        else:
            print(f"{src.upper()} {sym.upper()}: No data found or error occurred.")
