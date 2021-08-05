import os
import pandas as pd
import numpy as np
import datetime
import time
import collections
import pytz
from binance.client import Client

from os import listdir
from os.path import isfile, join
import json

import constants


def dateToStr(date):
    return date.strftime('%Y-%m-%d %H:%M')


def strToDate(dateStr):
    temp = datetime.datetime.strptime(dateStr, '%Y-%m-%d %H:%M')
    out = datetime.datetime(year=temp.year, month=temp.month, day=temp.day, hour=temp.hour, minute=temp.minute,
                            tzinfo=datetime.timezone.utc)
    return out


def getApiCredentials():
    filePath = '/home/bgunyel/Documents/Technical/bnc.txt'
    f = open(filePath, "r")
    lines = f.read().splitlines()
    api_key = lines[0]
    api_secret = lines[1]
    f.close()

    return api_key, api_secret


def printServerTime(client):
    time_server = time.gmtime(client.get_server_time()['serverTime'] / 1000)  # convert to UTC
    time_local = time.localtime(int(time.time()))  # convert to Local Time
    print(
        f'Server Time: {time_server.tm_year}-{time_server.tm_mon:02d}-{time_server.tm_mday:02d} {time_server.tm_hour:02d}:{time_server.tm_min:02d}:{time_server.tm_sec:02d}')
    print(
        f'Local Time: {time_local.tm_year}-{time_local.tm_mon}-{time_local.tm_mday} {time_local.tm_hour}:{time_local.tm_min:02d}:{time_local.tm_sec:02d}')


def downloadToDataFrame(client, ticker, interval, timestamp):
    bars = client.get_historical_klines(ticker, interval, timestamp, limit=1000)
    df = pd.DataFrame(data=bars, columns=[constants.OPEN_TIME, constants.OPEN, constants.HIGH, constants.LOW,
                                          constants.CLOSE, constants.VOLUME, constants.CLOSE_TIME,
                                          constants.QUOTE_ASSET_VOLUME, constants.NUMBER_OF_TRADES,
                                          constants.TAKER_BUY_BASE_ASSET_VOLUME,
                                          constants.TAKER_BUY_QUOTE_ASSET_VOLUME, 'Ignore'])

    df[constants.DATE] = np.nan
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]

    for index, row in df.iterrows():
        dateString = dateToStr(
            datetime.datetime.fromtimestamp(row[constants.OPEN_TIME] / 1000, datetime.timezone.utc))
        df.loc[index, constants.DATE] = dateString
        print(dateString)

    df.drop(columns=[constants.OPEN_TIME, constants.CLOSE_TIME, 'Ignore'], inplace=True)

    return df


def updateExistingCsv(client, ticker, interval, csvFilePath, numberOfDataLinesFile):
    with open(numberOfDataLinesFile) as f:
        numberOfDataLines = json.load(f)

    lastRow = pd.read_csv(filepath_or_buffer=csvFilePath, skiprows=range(1, numberOfDataLines[ticker + '_' + interval]))
    lastTimeStamp = int(strToDate(lastRow.iloc[-1, :][constants.DATE]).timestamp() * 1000)

    # lastTimeStamp = int(strToDate(df[constants.DATE][-1]).timestamp() * 1000)
    # lastTimeStamp = int(df.iloc[-1, 1])
    df2 = downloadToDataFrame(client, ticker, interval, lastTimeStamp)

    if len(df2.index > 1):
        numberOfRows = df2.shape[0]
        df2.drop(numberOfRows - 1).drop(0).to_csv(path_or_buf=csvFilePath, mode='a', index=False, header=False)
        numberOfDataLines[ticker + '_' + interval] = numberOfDataLines[ticker + '_' + interval] + df2.shape[0] - 2

        with open(numberOfDataLinesFile, 'w') as json_file:
            json.dump(numberOfDataLines, json_file)


def convertParquetToCsv(parquetFilePath, csvFilePath, numberOfDataLinesFile, ticker, interval):
    if False:
        df = pd.read_parquet(parquetFilePath)
        df.rename(columns={'open': constants.OPEN, 'high': constants.HIGH, 'low': constants.LOW,
                           'close': constants.CLOSE, 'volume': constants.VOLUME,
                           'quote_asset_volume': constants.QUOTE_ASSET_VOLUME,
                           'number_of_trades': constants.NUMBER_OF_TRADES,
                           'taker_buy_base_asset_volume': constants.TAKER_BUY_BASE_ASSET_VOLUME,
                           'taker_buy_quote_asset_volume': constants.TAKER_BUY_QUOTE_ASSET_VOLUME},
                  inplace=True)
        df.rename(dateToStr, axis='index', inplace=True)
        df.reset_index(inplace=True)
        df.rename(columns={'open_time': constants.DATE}, inplace=True)
        df.to_csv(path_or_buf=csvFilePath, mode='w', index=False, header=False)

        with open(numberOfDataLinesFile) as f:
            numberOfDataLines = json.load(f)

        numberOfDataLines[ticker + '_' + interval] = df.shape[0]

        with open(numberOfDataLinesFile, 'w') as json_file:
            json.dump(numberOfDataLines, json_file)


def getHistoricalData(client, ticker, interval):
    datasetFolder = '/home/bgunyel/Data/crypto_currency/'
    archiveFolder = datasetFolder + 'archive/'
    numberOfDataLinesFile = datasetFolder + 'number_of_data_lines.json'
    csvFilePath = datasetFolder + ticker + '_' + interval + '.csv'

    print('Updating ' + ticker + '_' + interval)

    if os.path.exists(csvFilePath):
        updateExistingCsv(client, ticker, interval, csvFilePath, numberOfDataLinesFile)
    else:

        if interval == '1m':  # Go to the archive
            fileList = listdir(archiveFolder)

            for f in fileList:
                if isfile(join(archiveFolder, f)):
                    filename, file_extension = os.path.splitext(f)
                    temp = filename.replace('-', '')

                    if temp == ticker:
                        convertParquetToCsv(join(archiveFolder, f), csvFilePath, numberOfDataLinesFile, ticker,
                                            interval)
                        updateExistingCsv(client, ticker, interval, csvFilePath, numberOfDataLinesFile)
                        dummy = -32

        else:
            timestamp = client._get_earliest_valid_timestamp(ticker, interval)
            df = downloadToDataFrame(client, ticker, interval, timestamp)
            numberOfRows = df.shape[0]
            df.drop(numberOfRows - 1).to_csv(path_or_buf=csvFilePath, index=False)

            with open(numberOfDataLinesFile) as f:
                numberOfDataLines = json.load(f)

            numberOfDataLines[ticker + '_' + interval] = df.shape[0] - 1

            with open(numberOfDataLinesFile, 'w') as json_file:
                json.dump(numberOfDataLines, json_file)

        dummy = -32


def updatePastData(tickers, intervals):
    api_key, api_secret = getApiCredentials()
    client = Client(api_key, api_secret)

    printServerTime(client)

    for ticker in tickers:
        for interval in intervals:
            getHistoricalData(client, ticker, interval)


def getPastDataForTrader(tickers, intervals, operationStartDates, historicalDataNeed, timeDeltas, client):

    for ticker in tickers:
        for interval in intervals:

            timeStamp = int((operationStartDates[interval] - historicalDataNeed * timeDeltas[interval]).timestamp() * 1000)

            csvFilePath = os.path.join(constants.TRADING_DATA_PATH, ticker + '_' + interval + '.csv')
            if os.path.exists(csvFilePath):
                os.remove(csvFilePath)
            df = downloadToDataFrame(client, ticker, interval, timeStamp)
            numberOfRows = df.shape[0]
            df.drop(numberOfRows - 1).to_csv(path_or_buf=csvFilePath, index=False)


def main(name):
    print(name)  # Press Ctrl+F8 to toggle the breakpoint.

    # valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    tickers = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LINKUSDT', 'LTCUSDT', 'XMRUSDT', 'ADAUSDT', 'BNBUSDT']
    # tickers = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
    intervals = ['4h', '1h', '30m']

    updatePastData(tickers=tickers, intervals=intervals)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('UPDATE HISTORICAL DATA')
