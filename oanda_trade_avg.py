#!/usr/bin/env python3
import os
import sys
import argparse
import oandapyV20 as opy
from oandapyV20.contrib.requests import MarketOrderRequest, TradeCloseRequest
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
from sentiment_fetcher_clickhouse import get_last_sentiment
from config import OANDA_API_TOKEN

class OandaTrader:
	def __init__(self, account_id, api_token=None):
		"""Initialize Oanda trader with account details."""
		self.account_id = account_id
		self.client = opy.API(access_token=api_token or OANDA_API_TOKEN)

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
	parser.add_argument('--symbol', required=True, help='Trading symbol (e.g., EURUSD, XAUUSD)')
	parser.add_argument('--source', required=True, help='Trading source (e.g., xm, fxblue)')
	parser.add_argument('--timeframe', required=True, type=int, help='Lookback period in minutes for sentiment averaging (e.g., 480, 1440)')
	parser.add_argument('--units', required=True, type=int, help='Number of units to trade')
	parser.add_argument('--treshold', type=float, default=1.0, help='Treshold for trading signals (default: 1.0)')
	
	args = parser.parse_args()

	# Initialize trader
	trader = OandaTrader(args.account)

	# Get sentiment data
	# Normalize symbol for ClickHouse table lookup
	symbol_for_db = args.symbol.replace('_', '').replace('-', '')
	sentiment_data = get_last_sentiment(source=args.source, symbol=symbol_for_db, timeframe=args.timeframe)
	if not sentiment_data:
		print("Error: Could not fetch sentiment data")
		sys.exit(1)

	if sentiment_data == 0:
		print("Error: Invalid sentiment data (longPercentage is 0)")
		sys.exit(1)

	long_percentage = round(sentiment_data)

	print(f"Symbol: {args.symbol}, Long Percentage: {long_percentage}, Treshold: ±{args.treshold}, Timeframe: {args.timeframe} min")

	# Trading logic with configurable treshold
	command = "_"
	if long_percentage < -args.treshold:
		# Close all long positions before going short
		trader.close_all_orders(args.symbol, "LONG")
		command = "SELL"
	elif long_percentage > args.treshold:
		# Close all short positions before going long
		trader.close_all_orders(args.symbol, "SHORT")
		command = "BUY"
	else:
		trader.close_all_orders(args.symbol, "LONG")
		trader.close_all_orders(args.symbol, "SHORT")

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

