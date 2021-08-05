import pandas as pd
import os

from binance.client import Client

import constants


class Broker:
    def __init__(self, symbols, intervals, datasetPath, operationMode, tradeStartDate):
        self.operationMode = operationMode
        self.symbols = symbols
        self.intervals = intervals
        self.datasetPath = datasetPath
        self.tradeStartDate = tradeStartDate

        self.clients = {}

        if operationMode == constants.TRADE:
            df = pd.read_excel(os.path.join(constants.TRADING_DATA_PATH, 'users.xlsx'), engine='openpyxl')

            for idx, row in df.iterrows():
                self.clients[row['Account Name']] = Client(row['Code-1'], row['Code-2'])

    def getAccountBalance(self, accountId):
        info = self.clients[accountId].get_account()
        balance = {}

        for item in info['balances']:
            asset = item['asset']
            symbol = asset + 'USDT'
            if symbol in self.symbols or symbol == 'BNBUSDT':
                balance[symbol] = float(item['free'])
            elif asset == 'USDT':
                balance[asset] = float(item['free'])

        return balance

    def getTotalAccountValue(self, accountId):
        balance = self.getAccountBalance(accountId=accountId)

        totalValue = 0
        for key in balance.keys():
            if key == 'USDT':
                totalValue += balance[key]
            else:
                price = float(self.clients[accountId].get_symbol_ticker(symbol=key)['price'])
                totalValue += price * balance[key]

        return totalValue

    # Example:
    # BTCUSDT --> symbol
    # 4h --> interval
    # BTCUSDT_4h --> ticker

    def setOrder(self, accountID, symbol, ticker, date, quantity, budget, signalType):

        realizationPrice = -1

        amount = -1
        commission = -1
        commissionAsset = 'USDT'

        if self.operationMode == constants.BACK_TEST:
            commissionRate = 0.00075
            data = self.simulationChartList[ticker]['data']
            price = data.loc[date, constants.CLOSE]
            realizationPrice = price

            if signalType == constants.LONG:
                if budget > 0:
                    temp = budget / (1 + commissionRate)
                    amount = temp / price
                    commission = budget - temp
                elif quantity > 0:
                    amount = quantity
                    commission = amount * price * commissionRate
                else:
                    pass
            elif signalType == constants.SHORT:
                if budget > 0:
                    temp = budget / (1 + commissionRate)
                    amount = temp / price
                    commission = budget - temp
                elif quantity > 0:
                    amount = quantity
                    commission = quantity * price * commissionRate
                else:
                    pass

        elif self.operationMode == constants.TRADE:

            price = float(self.clients[accountID].get_symbol_ticker(symbol=symbol)['price'])

            if signalType == constants.LONG:
                if budget > 0:  # Opening LONG
                    amount = budget / price
                    order = self.clients[accountID].order_market_buy(symbol=symbol, quantity=amount)
                    realizationPrice = float(order['fills'][0]['price'])
                    commission = float(order['fills'][0]['commission'])
                    commissionAsset = float(order['fills'][0]['commissionAsset'])

                elif quantity > 0:  # Closing SHORT
                    pass
                else:
                    pass
            elif signalType == constants.SHORT:
                if budget > 0:  # Opening SHORT
                    pass
                elif quantity > 0:  # Closing LONG
                    amount = quantity
                    order = self.clients[accountID].order_market_sell(symbol=symbol, quantity=amount)
                    realizationPrice = float(order['fills'][0]['price'])
                    commission = float(order['fills'][0]['commission'])
                    commissionAsset = float(order['fills'][0]['commissionAsset'])
                else:
                    pass
        else:
            pass  # TODO: This should be an error-case

        return realizationPrice, amount, commission, commissionAsset
