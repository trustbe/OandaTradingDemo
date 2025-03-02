import requests

def get_last_sentiment(symbol="XAUUSD", source="xm", timeframe=1440):
    """
    Fetch the last sentiment data for a given symbol from the API.
    
    Args:
        symbol (str): The trading symbol (default is "XAUUSD").
        source (str): The source of the sentiment data (default is "xm").
        timeframe (int): The timeframe for the sentiment data (default is 1440 minutes).
    
    Returns:
        str: The response text from the API.
    """
    # Normalize symbol
    if symbol == 'SPX500_USD':
        symbol = 'US500'
    symbol = symbol.lower()
    
    # Build the API URL
    url = f"https://data.fxbold.com/api/get_sentiment_history?symbol={symbol.upper()}&source={source}&timeframe={timeframe}"
    print(f"Requesting data from URL: {url}")
    
    try:
        # Make the request
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx
        return float(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sentiment data: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    result = get_last_sentiment("SPX500_USD")
    if result:
        print(f"Latest sentiment data: {result}")
    else:
        print("No sentiment data found or an error occurred.")
