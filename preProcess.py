import datetime
import pandas as pd

import constants


def dateToStr(date):
    return date.strftime('%Y-%m-%d %H:%M')


def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y-%m-%d %H:%M')


def prepareTimeDeltas():
    # valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    timeDeltas = {constants.m1: datetime.timedelta(minutes=1),
                  constants.m3: datetime.timedelta(minutes=3),
                  constants.m5: datetime.timedelta(minutes=5),
                  constants.m15: datetime.timedelta(minutes=15),
                  constants.m30: datetime.timedelta(minutes=30),
                  constants.h1: datetime.timedelta(hours=1),
                  constants.h2: datetime.timedelta(hours=2),
                  constants.h4: datetime.timedelta(hours=4),
                  constants.h6: datetime.timedelta(hours=6),
                  constants.h8: datetime.timedelta(hours=8),
                  constants.h12: datetime.timedelta(hours=12),
                  constants.d1: datetime.timedelta(days=1),
                  constants.d3: datetime.timedelta(days=3),
                  constants.w1: datetime.timedelta(weeks=1)}

    return timeDeltas


def computeOperationStartDates(operationNowDate, intervals, timeDeltas):

    origin = datetime.datetime(year=operationNowDate.year, month=operationNowDate.month, day=operationNowDate.day,
                               hour=0, minute=0, tzinfo=operationNowDate.tzinfo)
    operationStartDates = {}

    for interval in intervals:
        timeDelta = timeDeltas[interval]
        t = origin

        while t < operationNowDate:
            t = t + timeDelta

        operationStartDates[interval] = t

    return operationStartDates


def prepareHistoricalCharts(symbols, intervals, operationStartDates, historicalDataNeed, datasetPath):
    beginDates = {}  # Holds the begin dates for different bar intervals to ensure sufficient data for the simulation
    timeDeltas = prepareTimeDeltas()

    for interval in intervals:
        beginDates[interval] = operationStartDates[interval] - timeDeltas[interval] * historicalDataNeed

    tickersList = []
    chartList = {}
    priceTimes = []

    for symbol in symbols:
        for interval in intervals:
            ticker = symbol + '_' + interval
            tickersList.append(ticker)

            filePath = datasetPath + ticker + '.csv'
            df = pd.read_csv(filePath)
            df.set_index('Date', inplace=True)

            data = df.loc[dateToStr(beginDates[interval]):dateToStr(operationStartDates[interval] - timeDeltas[interval]), :]

            if data[pd.isnull(data).any(axis=1)].size > 0:
                # print(ticker)
                # print(data[pd.isnull(data).any(axis=1)])
                data.dropna(axis=0, how='any', inplace=True)

            chartList[ticker] = {'data': data}

            priceTimes.extend(data.index)
            temp = set(priceTimes)
            priceTimes = list(temp)

    priceTimes.sort()

    return chartList


def prepareSimulationCharts(symbols, intervals, simulationStartDate, simulationEndDate, datasetPath):
    tickersList = []
    chartList = {}
    priceTimes = []

    for symbol in symbols:
        for interval in intervals:
            ticker = symbol + '_' + interval
            tickersList.append(ticker)

            filePath = datasetPath + ticker + '.csv'
            df = pd.read_csv(filePath)
            df.set_index('Date', inplace=True)

            data = df.loc[dateToStr(simulationStartDate):dateToStr(simulationEndDate), :]

            if data[pd.isnull(data).any(axis=1)].size > 0:
                # print(ticker)
                # print(data[pd.isnull(data).any(axis=1)])
                data.dropna(axis=0, how='any', inplace=True)

            chartList[ticker] = {'data': data}

            priceTimes.extend(data.index)
            temp = set(priceTimes)
            priceTimes = list(temp)

    priceTimes.sort()

    return chartList, priceTimes
