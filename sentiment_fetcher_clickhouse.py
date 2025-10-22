import requests
import json
import os
from config import CLICKHOUSE_URL, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD

# Allow environment variables to override config
CLICKHOUSE_URL = os.getenv("CLICKHOUSE_URL", CLICKHOUSE_URL)
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", CLICKHOUSE_USER)
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", CLICKHOUSE_PASSWORD)


def get_last_sentiment(source="xm", symbol="xauusd", timeframe=480):
    """
    Fetch the average client sentiment from ClickHouse for any source/symbol combination.

    Args:
        source (str): Data source (e.g., "xm", "fxblue", etc.)
        symbol (str): Trading symbol (e.g., "xauusd", "eurusd", etc.)
        timeframe (int): Lookback period in minutes for averaging

    Returns:
        float: Rounded client ratio or None if error.
    """
    # Normalize symbol to lowercase for table name
    symbol = symbol.lower().replace('_', '').replace('-', '')

    # Build dynamic table name
    table_name = f"default.st_{source}_{symbol}"

    query = f"""
    SELECT ROUND(50 - AVG(longval), 1) AS client_ratio
    FROM {table_name}
    WHERE stamp >= now() - INTERVAL {timeframe} MINUTE
    FORMAT JSONEachRow;
    """

    print(f"Querying table: {table_name} with {timeframe} minute lookback")

    try:
        response = requests.post(
            CLICKHOUSE_URL,
            params={
                "user": CLICKHOUSE_USER,
                "password": CLICKHOUSE_PASSWORD,
                "query": query,
            },
            timeout=10,
        )
        response.raise_for_status()

        lines = response.text.strip().splitlines()
        if not lines:
            return None

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
