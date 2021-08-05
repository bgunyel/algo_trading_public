import pandas as pd

import constants
import preProcess
import datetime

import updateHistoricalData


class DataProvider:
    def __init__(self, symbols, intervals, datasetPath, operationMode,
                 tradeStartDate=datetime.datetime(year=1881, month=5, day=19),
                 tradeEndDate=datetime.datetime(year=1881, month=5, day=19)):
        self.operationMode = operationMode
        self.symbols = symbols
        self.intervals = intervals
        self.datasetPath = datasetPath
        self.tradeStartDate = tradeStartDate  # This date is utilized only in back-test mode
        self.tradeEndDate = tradeEndDate  # This date is utilized only in back-test mode

        self.tickers = []
        self.prepareTickersList()

        self.client = 0

        if operationMode == constants.BACK_TEST:
            self.simulationChartList, self.priceTimes = preProcess.prepareSimulationCharts(
                symbols=symbols,
                intervals=intervals,
                simulationStartDate=tradeStartDate,
                simulationEndDate=tradeEndDate,
                datasetPath=datasetPath)
        elif operationMode == constants.TRADE:
            updateHistoricalData.updatePastData(self.symbols, self.intervals)

    def setClient(self, client):
        self.client = client

    def prepareTickersList(self):
        for symbol in self.symbols:
            for interval in self.intervals:
                ticker = symbol + '_' + interval
                self.tickers.append(ticker)

    def getPriceTimesList(self):
        out = []
        if self.operationMode == constants.BACK_TEST:
            out = self.priceTimes
        return out

    def getCandleInfo(self, ticker, date):

        columns = [constants.DATE, constants.OPEN, constants.HIGH, constants.LOW, constants.CLOSE, constants.VOLUME,
                   constants.QUOTE_ASSET_VOLUME, constants.NUMBER_OF_TRADES, constants.TAKER_BUY_BASE_ASSET_VOLUME,
                   constants.TAKER_BUY_QUOTE_ASSET_VOLUME]
        out = pd.DataFrame(columns=columns)

        if self.operationMode == constants.BACK_TEST:
            chart = self.simulationChartList[ticker]
            data = chart['data']

            if date in data.index:
                out = data.loc[date]

        elif self.operationMode == constants.TRADE:
            pass
        else:
            pass  # TODO This should be an error-reporting case

        return out

    def getCandles(self, date):
        candles = {}
        for ticker in self.tickers:
            candles[ticker] = self.getCandleInfo(ticker, date)

        return candles
