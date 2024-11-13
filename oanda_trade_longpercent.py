#!/usr/bin/env python3
import os
import sys
import argparse
import oandapyV20 as opy
from oandapyV20.contrib.requests import MarketOrderRequest, TradeCloseRequest
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
from sentiment_xm_fetcher import get_last_sentiment

class OandaTrader:
    def __init__(self, account_id, api_token='25ebfb9ee277e219b95233d58cdc8140-bec4d827bcf87c80e5e529b6dc772f55'):
        """Initialize Oanda trader with account details."""
        self.account_id = account_id
        self.client = opy.API(access_token=api_token)

    @staticmethod
    def get_oanda_symbol(symbol):
        """Convert symbol format to Oanda format (e.g., 'EURUSD' to 'EUR_USD')."""
        if symbol == 'SPX500_USD': return symbol
        return f"{symbol[0:3]}_{symbol[3:]}"

    def get_orders_count(self, symbol):
        """Get count of open orders for a specific symbol."""
        count = 0
        r = trades.OpenTrades(accountID=self.account_id)
        self.client.request(r)
        
        for trade in r.response['trades']:
            if trade['instrument'] == self.get_oanda_symbol(symbol):
                count += 1
        return count

    def order_send(self, symbol, units):
        """Send a market order."""
        mo = MarketOrderRequest(
            instrument=self.get_oanda_symbol(symbol),
            units=units
        )
        r = orders.OrderCreate(self.account_id, data=mo.data)
        response = self.client.request(r)
        print(f"Order response: {response}")
        return response

    def close_all_orders(self, symbol, direction=None):
        """
        Close all orders for a symbol.
        If direction is provided, only close orders in that direction.
        If direction is None, close all orders regardless of direction.
        """
        if self.get_orders_count(symbol) == 0:
            print("No active orders to close")
            return

        r = trades.OpenTrades(accountID=self.account_id)
        self.client.request(r)
        
        for trade in r.response['trades']:
            trade_id = trade['id']
            initial_units = float(trade['initialUnits'])
            
            if trade['instrument'] == self.get_oanda_symbol(symbol):
                should_close = False
                if direction is None:
                    should_close = True
                elif direction == 'LONG' and initial_units > 0:
                    should_close = True
                elif direction == 'SHORT' and initial_units < 0:
                    should_close = True

                if should_close:
                    print(f"Closing trade: {trade}")
                    order = TradeCloseRequest()
                    tr = trades.TradeClose(self.account_id, tradeID=trade_id, data=order.data)
                    response = self.client.request(tr)
                    print(f"Close response: {response}")

def main():
    """Main function to handle the trading logic."""
    parser = argparse.ArgumentParser(description='Oanda Trading Script based on XM Sentiment')
    parser.add_argument('--account', required=True, help='Oanda account ID')
    parser.add_argument('--symbol', required=True, help='Trading symbol (e.g., EURUSD)')
    parser.add_argument('--units', required=True, type=int, help='Number of units to trade')
    parser.add_argument('--longcross', type=int, default=0, help='Long crossing threshold (default: 0)')
    
    args = parser.parse_args()

    # Initialize trader
    trader = OandaTrader(args.account)

    # Get sentiment data
    sentiment_data = get_last_sentiment(args.symbol)
    if not sentiment_data:
        print("Error: Could not fetch sentiment data")
        sys.exit(1)

    long_percentage = float(sentiment_data['longPercentage'])*100

    if long_percentage == 0:
        print("Error: Invalid sentiment data (longPercentage is 0)")
        sys.exit(1)

    print(f"Symbol: {args.symbol}, Long Percentage: {long_percentage}")

    # Trading logic
    command = "_"
    if long_percentage > 50 + args.longcross:
        # Close all long positions before going short
        trader.close_all_orders(args.symbol, "LONG")
        command = "SELL"
    elif long_percentage < 50 - args.longcross:
        # Close all short positions before going long
        trader.close_all_orders(args.symbol, "SHORT")
        command = "BUY"

    # Execute trades based on command
    if command == "SELL" and trader.get_orders_count(args.symbol) == 0:
        print("Opening SHORT position")
        trader.order_send(args.symbol, -1 * args.units)
    elif command == "BUY" and trader.get_orders_count(args.symbol) == 0:
        print("Opening LONG position")
        trader.order_send(args.symbol, args.units)
    elif command == "_" and trader.get_orders_count(args.symbol) != 0:
        print("Closing ALL positions")
        trader.close_all_orders(args.symbol)  # Close all positions regardless of direction

if __name__ == '__main__':
    main()

