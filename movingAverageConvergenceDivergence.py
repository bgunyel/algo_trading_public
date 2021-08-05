import pandas as pd
import datetime

import indicators
import constants


def dateToStr(date):
    return date.strftime('%Y-%m-%d %H:%M')


def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


class MACD:
    def __init__(self, symbols, intervals):

        self.fastLength = 12
        self.slowLength = 26
        self.signalLength = 9

        self.name = constants.MACD

        self.isObjectReady = False

        self.columns = ['fma', 'sma', 'macd', 'signal']
        self.symbols = symbols
        self.intervals = intervals

        self.macdData = {}

        for symbol in symbols:
            for interval in intervals:
                ticker = symbol + '_' + interval
                self.macdData[ticker] = pd.DataFrame(columns=self.columns)

    def getName(self):
        return self.name

    def computeHistoricalDataNeed(self):
        dataNeed = max([self.fastLength + self.signalLength, self.slowLength + self.signalLength])
        return dataNeed

    def checkDataIntegrity(self):
        pass

    def preProcess(self, ticker, data):

        i = 0
        for idx, row in data.iterrows():

            if i > 0:
                self.process(ticker, row, idx)
            else:
                src = row['Close']
                fma = src  # Fast MA
                sma = src  # Slow MA
                macd = fma - sma
                signal = macd

                self.macdData[ticker].loc[idx, 'fma'] = fma
                self.macdData[ticker].loc[idx, 'sma'] = sma
                self.macdData[ticker].loc[idx, 'macd'] = macd
                self.macdData[ticker].loc[idx, 'signal'] = signal

            i = i + 1

        self.isObjectReady = True

    def process(self, ticker, data, date):
        self.checkDataIntegrity()

        row = self.macdData[ticker].iloc[-1, :]

        src = data['Close']
        fma = indicators.ema(currentValue=src, numPeriods=self.fastLength, prevEMA=row['fma'])  # Fast MA
        sma = indicators.ema(currentValue=src, numPeriods=self.slowLength, prevEMA=row['sma'])  # Slow MA
        macd = fma - sma
        signal = indicators.ema(currentValue=macd, numPeriods=self.signalLength, prevEMA=row['signal'])

        # print(f'Date: {date} MACD: {macd} SIG: {signal} HIST: {macd - signal}')

        self.macdData[ticker].loc[date, 'fma'] = fma
        self.macdData[ticker].loc[date, 'sma'] = sma
        self.macdData[ticker].loc[date, 'macd'] = macd
        self.macdData[ticker].loc[date, 'signal'] = signal

        if self.isObjectReady:  # Delete the oldest row
            self.macdData[ticker].drop(labels=self.macdData[ticker].index[0], axis='index', inplace=True)

    def isUpwardCross(self, ticker):

        row1 = self.macdData[ticker].iloc[-2]
        row2 = self.macdData[ticker].iloc[-1]
        out = False

        if row1['macd'] <= row1['signal'] and row2['macd'] > row2['signal']:
            out = True

        return out

    def isDownwardCross(self, ticker):

        row1 = self.macdData[ticker].iloc[-2]
        row2 = self.macdData[ticker].iloc[-1]
        out = False

        if row1['macd'] >= row1['signal'] and row2['macd'] < row2['signal']:
            out = True

        return out

    def computeSignals(self, ticker, data, date):
        self.process(ticker, data, date)

        signal = {constants.TYPE: constants.NULL,
                  constants.DATE: date,
                  constants.PRICE: data[constants.CLOSE],
                  constants.SYMBOL: ticker.split('_')[0],
                  constants.TICKER: ticker,
                  constants.SOURCE: self.getName()}

        if self.isUpwardCross(ticker=ticker):
            signal[constants.TYPE] = constants.LONG
        elif self.isDownwardCross(ticker=ticker):
            signal[constants.TYPE] = constants.SHORT

        return signal
