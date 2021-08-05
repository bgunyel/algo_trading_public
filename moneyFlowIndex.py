import pandas as pd
import datetime

import indicators
import constants


def dateToStr(date):
    return date.strftime('%Y-%m-%d %H:%M')


def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


class MoneyFlowIndex:
    def __init__(self, symbols, intervals):
        self.length = 14
        self.fastLength = 3
        self.slowLength = 6

        self.name = constants.MFI

        self.isObjectReady = False

        self.columns = ['ap', 'pmf', 'nmf', 'mfi', 'fma', 'sma']
        self.symbols = symbols
        self.intervals = intervals

        self.mfiData = {}

        for symbol in symbols:
            for interval in intervals:
                ticker = symbol + '_' + interval
                self.mfiData[ticker] = pd.DataFrame(columns=self.columns)


    def getName(self):
        return self.name

    def computeHistoricalDataNeed(self):
        dataNeed = self.length + 1
        return dataNeed

    def checkDataIntegrity(self):
        pass

    def preProcess(self, ticker, data):

        i = 0
        for idx, row in data.iterrows():

            if i > 0:
                self.process(ticker, row, idx)
            else:
                ap = (data.loc[idx, constants.HIGH] + data.loc[idx, constants.LOW] + data.loc[idx, constants.CLOSE]) / 3
                pmf = 0
                nmf = 0
                mfi = 50
                fma = mfi
                sma = mfi

                self.mfiData[ticker].loc[idx, 'ap'] = ap
                self.mfiData[ticker].loc[idx, 'pmf'] = pmf
                self.mfiData[ticker].loc[idx, 'nmf'] = nmf
                self.mfiData[ticker].loc[idx, 'mfi'] = mfi
                self.mfiData[ticker].loc[idx, 'fma'] = fma
                self.mfiData[ticker].loc[idx, 'sma'] = sma

            i = i + 1

        self.isObjectReady = True

    def process(self, ticker, data, date):

        row = self.mfiData[ticker].iloc[-1, :]

        ap = (data[constants.HIGH] + data[constants.LOW] + data[constants.CLOSE]) / 3

        pmf = 0
        nmf = 0

        if ap - row['ap'] > 0:
            pmf = data[constants.VOLUME] * ap
        else:
            nmf = data[constants.VOLUME] * ap

        self.mfiData[ticker].loc[date, 'ap'] = ap
        self.mfiData[ticker].loc[date, 'pmf'] = pmf
        self.mfiData[ticker].loc[date, 'nmf'] = nmf

        numElem = min(self.length, self.mfiData[ticker].shape[0])

        total_pmf = self.mfiData[ticker].tail(numElem)['pmf'].sum()
        total_nmf = self.mfiData[ticker].tail(numElem)['nmf'].sum()
        mfi = 100

        if total_nmf != 0:
            mfi = 100 - (100 / (1 + total_pmf / total_nmf))

        self.mfiData[ticker].loc[date, 'mfi'] = mfi

        fma = indicators.ema(currentValue=mfi, numPeriods=self.fastLength, prevEMA=row['fma'])
        sma = indicators.ema(currentValue=mfi, numPeriods=self.slowLength, prevEMA=row['sma'])

        self.mfiData[ticker].loc[date, 'fma'] = fma
        self.mfiData[ticker].loc[date, 'sma'] = sma

        if self.isObjectReady:  # Delete the oldest row
            self.mfiData[ticker].drop(labels=self.mfiData[ticker].index[0], axis='index', inplace=True)

    def isUpwardCross(self, ticker):

        row1 = self.mfiData[ticker].iloc[-2]
        row2 = self.mfiData[ticker].iloc[-1]
        out = False

        if row1['fma'] <= row1['sma'] and row2['fma'] > row2['sma']:
            out = True

        return out

    def isDownwardCross(self, ticker):

        row1 = self.mfiData[ticker].iloc[-2]
        row2 = self.mfiData[ticker].iloc[-1]
        out = False

        if row1['fma'] >= row1['sma'] and row2['fma'] < row2['sma']:
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
