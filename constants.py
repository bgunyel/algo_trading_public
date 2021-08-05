from typing import Final
from binance_f.model import *

TRADE: Final = 'trade'
BACK_TEST: Final = 'back test'

DATE: Final = 'Date'
OPEN_DATE: Final = 'Open Date'
CLOSE_DATE: Final = 'Close Date'
PRICE: Final = 'Price'
BUDGET: Final = 'Budget'
OPEN_PRICE: Final = 'Open Price'
CLOSE_PRICE: Final = 'Close Price'
TICKER: Final = 'Ticker'
SYMBOL: Final = 'Symbol'
TYPE: Final = 'Type'
SOURCE: Final = 'Source'
CLOSING_SOURCE: Final = 'Closing Source'
AMOUNT: Final = 'Amount'
COMMISSION: Final = 'Commission'
STOP_LOSS: Final = 'StopLoss'

PROFIT_LOSS: Final = 'Profit / Loss'
PROFIT_LOSS_PERCENT: Final = 'Profit / Loss (%)'

EXCHANGE: Final = 'Exchange'
BINANCE: Final = 'Binance'
COINBASE: Final = 'Coinbase'
SPOT: Final = 'Spot'
POLICY: Final = 'Policy'

COMMISSION_RATE: Final = 'Commission Rate'
BASE_CURRENCY: Final = 'Base Currency'
ASSETS: Final = 'Assets'

ORDER_TYPE: Final = 'Order Type'
MARKET_ORDER: Final = 'Market Order'
LIMIT_ORDER: Final = 'Limit Order'

DISTRIBUTION: Final = 'Distribution'
UNIFORM: Final = 'Uniform'
DYNAMIC: Final = 'Dynamic'
COEFFICIENT_VECTOR: Final = 'Coefficient Vector'
IS_IN_POSITION: Final = 'Is In Position'

SUPER_TREND: Final = 'SuperTrend'
MACD: Final = 'MACD'
WAVE_TREND: Final = 'WaveTrend'
MAVILIM_W: Final = 'MavilimW'
MFI: Final = 'MFI'

OPEN_TIME: Final = 'Open Time'
CLOSE_TIME: Final = 'Close Time'

OPEN: Final = 'Open'
HIGH: Final = 'High'
LOW: Final = 'Low'
CLOSE: Final = 'Close'
VOLUME: Final = 'Volume'

QUOTE_ASSET_VOLUME: Final = 'Quote Asset Volume'
NUMBER_OF_TRADES: Final = 'Number of Trades'
TAKER_BUY_BASE_ASSET_VOLUME: Final = 'Taker Buy Base Asset Volume'
TAKER_BUY_QUOTE_ASSET_VOLUME = 'Taker Buy Quote Asset Volume'

LONG: Final = 'LONG'
SHORT: Final = 'SHORT'
NULL: Final = 'NULL'

LONG_ONLY: Final = 'Long Only'
SHORT_ONLY: Final = 'Short Only'
LONG_SHORT: Final = 'Long & Short'

ISOLATED: Final = 'ISOLATED'
CROSSED: Final = 'CROSSED'

m1: Final = '1m'  # 1-minute
m3: Final = '3m'
m5: Final = '5m'
m15: Final = '15m'
m30: Final = '30m'
h1: Final = '1h'  # 1-hour
h2: Final = '2h'
h4: Final = '4h'
h6: Final = '6h'
h8: Final = '8h'
h12: Final = '12h'
d1: Final = '1d'  # 1-day
d3: Final = '3d'
w1: Final = '1w'  # 1-week

USDT: Final = 'USDT'
BTC: Final = 'BTC'

BTCUSDT: Final = 'BTCUSDT'
ETHUSDT: Final = 'ETHUSDT'
XRPUSDT: Final = 'XRPUSDT'
LINKUSDT: Final = 'LINKUSDT'
LTCUSDT: Final = 'LTCUSDT'
XMRUSDT: Final = 'XMRUSDT'
ADAUSDT: Final = 'ADAUSDT'
BNBUSDT: Final = 'BNBUSDT'

DATASET_PATH: Final = '/home/bgunyel/Data/crypto_currency/'
OUTPUT_FOLDER: Final = '/home/bgunyel/Output/algo_trading/'
TRADING_DATA_PATH: Final = '/home/bgunyel/Data/trading_data/'
FUTURES_TRADING_DATA_PATH: Final = '/home/bgunyel/Data/futures_trading_data/'

intervalsMap: Final = {m1: CandlestickInterval.MIN1,
                       m3: CandlestickInterval.MIN3,
                       m5: CandlestickInterval.MIN5,
                       m15: CandlestickInterval.MIN15,
                       m30: CandlestickInterval.MIN30,
                       h1: CandlestickInterval.HOUR1,
                       h2: CandlestickInterval.HOUR2,
                       h4: CandlestickInterval.HOUR4,
                       h6: CandlestickInterval.HOUR6,
                       h8: CandlestickInterval.HOUR8,
                       h12: CandlestickInterval.HOUR12,
                       d1: CandlestickInterval.DAY1,
                       d3: CandlestickInterval.DAY3,
                       w1: CandlestickInterval.WEEK1}

FUTURES_MIN_ORDER_QUANTITIES: Final = {BTCUSDT: 0.001, ETHUSDT: 0.001}