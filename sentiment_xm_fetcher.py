from pymongo import MongoClient
from typing import Optional, Dict, Any

def get_last_sentiment(symbol: str = "US500") -> Optional[Dict[Any, Any]]:
    """
    Fetch the last sentiment record for a given symbol from MongoDB.
    
    Args:
        symbol (str): Trading symbol, defaults to "US500"
        
    Returns:
        Optional[Dict]: The last sentiment record or None if no records found
        
    Raises:
        Exception: If there's an error connecting to MongoDB or querying the data
    """
    try:
        # Normalize symbol
        if symbol == 'SPX500_USD':
            symbol = 'US500'
        symbol = symbol.lower()
        
        # MongoDB connection details
        MONGO_URI = 'mongodb+srv://mongo:Mongo3421@serverlessinstance0.8i8oho8.mongodb.net/forexbold?retryWrites=true&w=majority'
        DATABASE_NAME = 'forexbold'
        COLLECTION_NAME = f'sentiment_xm_{symbol}'
        
        # Create MongoDB client and connect
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Fetch the last record by timestamp
        last_record = collection.find_one(sort=[('stamp', -1)])
        
        return last_record
        
    except Exception as e:
        print(f"Error fetching sentiment data: {str(e)}")
        return None
        
    finally:
        if 'client' in locals():
            client.close()

# Example usage:
if __name__ == "__main__":
    result = get_last_sentiment("SPX500_USD")
    if result:
        print(f"Latest sentiment data: {result}")
    else:
        print("No sentiment data found or error occurred")

