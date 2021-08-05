import pandas as pd
import datetime

import moneyFlowIndex
import movingAverageConvergenceDivergence


def dateToStr(date):
    return date.strftime('%Y-%m-%d %H:%M')


def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


class StrategyHandler:

    def __init__(self, symbols, intervals):

        self.columns = ['ticker', 'type', 'price', 'amount']

        self.symbols = symbols
        self.intervals = intervals

        self.strategyData = {}

        for symbol in symbols:
            for interval in intervals:
                ticker = symbol + '_' + interval
                self.strategyData[ticker] = pd.DataFrame(columns=self.columns)

        self.mfi = moneyFlowIndex.MoneyFlowIndex(symbols, intervals)  # Create MoneyFlowIndex Object
        self.macd = movingAverageConvergenceDivergence.MACD(symbols, intervals)  # Create MACD Object

    def computeHistoricalDataNeed(self):
        dataNeed = max([self.mfi.computeHistoricalDataNeed(),
                        self.macd.computeHistoricalDataNeed()])
        return dataNeed

    def preProcess(self, historicalChartList):

        for symbol in self.symbols:
            for interval in self.intervals:
                ticker = symbol + '_' + interval

                chart = historicalChartList[ticker]
                data = chart['data']

                self.mfi.preProcess(ticker, data)
                self.macd.preProcess(ticker, data)


    def process(self, ticker, data, date):
        signals = pd.DataFrame(columns=['Type', 'Date', 'Price', 'Ticker'])

        signals = signals.append(self.mfi.computeSignals(ticker=ticker, data=data, date=date), ignore_index=True)
        signals = signals.append(self.macd.computeSignals(ticker=ticker, data=data, date=date), ignore_index=True)
        return signals[signals['Type'] != 'NULL']

    def getActiveIndicatorNames(self):
        names = [self.mfi.getName(), self.macd.getName()]
        return names
