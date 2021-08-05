import time
import datetime
import pandas as pd
import os

import constants

import trader
import broker
import dataProvider


def dateToStr(date):
    return date.strftime('%Y-%m-%d')


def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y-%m-%d')


def main(name):
    print(name)

    backTestStartDate = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=0)  # 2018-06-01
    backTestEndDate = datetime.datetime(year=2021, month=2, day=23, hour=0, minute=0)  # 2021-02-23  # TODO

    # symbols = [constants.BTCUSDT, constants.ETHUSDT, constants.XRPUSDT, constants.LINKUSDT, constants.LTCUSDT,
    #           constants.XMRUSDT, constants.ADAUSDT]

    symbols = [constants.BTCUSDT, constants.ETHUSDT, constants.XRPUSDT, constants.LTCUSDT, constants.ADAUSDT]

    intervals = [constants.h4]

    dp = dataProvider.DataProvider(symbols=symbols, intervals=intervals, datasetPath=constants.DATASET_PATH,
                                   operationMode=constants.BACK_TEST, tradeStartDate=backTestStartDate,
                                   tradeEndDate=backTestEndDate)
    tr = trader.Trader(symbols=symbols, intervals=intervals, datasetPath=constants.DATASET_PATH,
                       operationMode=constants.BACK_TEST, tradeStartDate=backTestStartDate)
    br = broker.Broker(symbols=symbols, intervals=intervals, datasetPath=constants.DATASET_PATH,
                       operationMode=constants.BACK_TEST, tradeStartDate=backTestStartDate)
    tr.setBroker(br)

    ###
    # RUN THE SIMULATION #
    ###

    priceTimes = dp.getPriceTimesList()

    for i in range(0, len(priceTimes)):
        priceTime = priceTimes[i]
        print(priceTime)
        candles = dp.getCandles(priceTime)
        tr.process(candles, priceTime)

    tradeTables = tr.getTradeTables()

    params = dict([('Start Date', dateToStr(backTestStartDate)),
                   ('End Date', dateToStr(backTestEndDate))])
    parametersTable = pd.DataFrame(data=params, index=[0])
    parametersTable = parametersTable.T

    timeStr = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M')
    xlsFilePath = os.path.join(constants.OUTPUT_FOLDER, 'trade_table_' + timeStr + '.xlsx')
    excelWriter = pd.ExcelWriter(xlsFilePath)
    parametersTable.to_excel(excelWriter, 'Parameters')

    accountNames = tr.getAccountNames()

    for accountId in accountNames:
        tradeTables[accountId].to_excel(excelWriter, accountId)
    excelWriter.save()

    dummy = -32


if __name__ == '__main__':
    start_time = time.time()
    main('Crypto-currency Backtest')
    end_time = time.time()
    elapsed_time = end_time - start_time
    print('Start Time: ', datetime.datetime.fromtimestamp(start_time))
    print('End Time: ', datetime.datetime.fromtimestamp(end_time))
    print(f'Time Elapsed: {elapsed_time:.2f} seconds')
