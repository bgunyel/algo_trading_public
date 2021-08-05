import pandas as pd
import os

import strategyHandler
import preProcess
import constants
import account


class Trader:

    def __init__(self, symbols, intervals, datasetPath, operationMode, tradeStartDate, br):

        self.stopLossThreshold = 0.05

        self.setBroker(br)

        self.accounts = {}
        self.symbols = symbols
        self.intervals = intervals
        self.datasetPath = datasetPath

        self.tickers = []
        self.prepareTickersList()

        self.indicatorProportions = {}
        self.setIndicatorProportions()

        self.operationMode = operationMode
        self.tradeStartDate = tradeStartDate

        self.createAccounts()

        self.sh = strategyHandler.StrategyHandler(symbols=symbols, intervals=intervals)

        timeDeltas = preProcess.prepareTimeDeltas()
        operationStartDates = preProcess.computeOperationStartDates(operationNowDate=tradeStartDate,
                                                                    intervals=self.intervals, timeDeltas=timeDeltas)
        historicalDataNeed = self.sh.computeHistoricalDataNeed()
        historicalChartList = preProcess.prepareHistoricalCharts(symbols=symbols, intervals=intervals,
                                                                 operationStartDates=operationStartDates,
                                                                 historicalDataNeed=historicalDataNeed,
                                                                 datasetPath=datasetPath)

        self.sh.preProcess(historicalChartList)

    def getTradeTables(self):
        tradeTables = {}
        for accountID in self.accounts.keys():
            tradeTables[accountID] = self.accounts[accountID].getTradeTable()
        return tradeTables

    def setBroker(self, br):
        self.br = br

    def setIndicatorProportions(self):
        self.indicatorProportions[constants.SUPER_TREND] = 0.275
        self.indicatorProportions['MavilimW_3_5'] = 0.275  # TODO: Must be automated
        self.indicatorProportions[constants.WAVE_TREND] = 0.15
        self.indicatorProportions[constants.MACD] = 0.15
        self.indicatorProportions[constants.MFI] = 0.15

    def prepareTickersList(self):
        for symbol in self.symbols:
            for interval in self.intervals:
                ticker = symbol + '_' + interval
                self.tickers.append(ticker)

    def createAccounts(self):

        if self.operationMode == constants.BACK_TEST:
            self.accounts['account-1'] = account.Account(symbols=self.symbols, exchange=constants.BINANCE,
                                                         accountType=constants.SPOT, policyType=constants.LONG_ONLY,
                                                         baseCurrency=constants.USDT,
                                                         budget=5000, commissionRate=0.00075,
                                                         stopLossLevel=0.05,
                                                         algorithmCoefficients=self.indicatorProportions)
            self.accounts['account-2'] = account.Account(symbols=self.symbols, exchange=constants.BINANCE,
                                                         accountType=constants.SPOT, policyType=constants.SHORT_ONLY,
                                                         baseCurrency=constants.USDT,
                                                         budget=5000, commissionRate=0.00075,
                                                         stopLossLevel=0.05,
                                                         algorithmCoefficients=self.indicatorProportions)
        elif self.operationMode == constants.TRADE:
            df = pd.read_excel(os.path.join(constants.TRADING_DATA_PATH, 'users.xlsx'), engine='openpyxl')

            for idx, row in df.iterrows():
                accountId = row['Account Name']
                self.accounts[accountId] = account.Account(symbols=self.symbols,
                                                           exchange=row[constants.EXCHANGE],
                                                           accountType=row[constants.TYPE],
                                                           policyType=row[constants.POLICY],
                                                           baseCurrency=row[constants.BASE_CURRENCY],
                                                           stopLossLevel=0.05,
                                                           algorithmCoefficients=self.indicatorProportions)
                totalAccountValue = self.br.getTotalTradeValue(accountId)

                if totalAccountValue < 200:
                    self.accounts[accountId].setActiveStatus(False)
                else:
                    self.accounts[accountId].setActiveStatus(True)
                    symbols = self.symbols[:2]
                    for i in range(len(self.symbols) - 2):
                        if totalAccountValue > (i + 1) * 1000:
                            symbols.append(self.symbols[i + 2])
                    self.accounts[accountId].setSymbols(symbols)

        else:
            pass

    def getAccountNames(self):
        return self.accounts.keys()

    def arrangeSpotOrder(self, accountID, symbol, signalType, signalSource):

        budget = -1
        quantity = -1

        policyType = self.accounts[accountID].getPolicyType()

        if policyType == constants.LONG_ONLY:
            if signalType == constants.LONG:
                budget = self.accounts[accountID].getOpeningPositionBudget(symbol, signalSource)
            elif signalType == constants.SHORT:
                quantity = self.accounts[accountID].getClosingPositionQuantity(symbol, signalType, signalSource)
        elif policyType == constants.SHORT_ONLY:
            if signalType == constants.SHORT:
                budget = self.accounts[accountID].getOpeningPositionBudget(symbol, signalSource)
            elif signalType == constants.LONG:
                quantity = self.accounts[accountID].getClosingPositionQuantity(symbol, signalType, signalSource)
        elif policyType == constants.LONG_SHORT:
            pass
        else:
            pass

        return budget, quantity

    def adjustAccount(self, accountID, symbol, price, quantity, commission, signalType):

        baseCurrency = self.accounts[accountID][constants.BASE_CURRENCY]

        if signalType == constants.LONG:
            totalCost = price * quantity + commission
            self.accounts[accountID][baseCurrency] -= totalCost
            self.accounts[accountID][constants.ASSETS][symbol] += quantity

        elif signalType == constants.SHORT:
            totalGain = price * quantity - commission
            self.accounts[accountID][baseCurrency] += totalGain
            self.accounts[accountID][constants.ASSETS][symbol] -= quantity

        else:
            pass

    def sendOrders(self, signals):

        for index, signal in signals.iterrows():
            symbol = signal[constants.SYMBOL]
            ticker = signal[constants.TICKER]
            date = signal[constants.DATE]
            signalSource = signal[constants.SOURCE]
            signalType = signal[constants.TYPE]

            for accountID in self.accounts.keys():

                if symbol in self.accounts[accountID].getSymbols() and self.accounts[accountID].getActiveStatus() == True:

                    if self.accounts[accountID].getAccountType() == constants.SPOT:
                        budget, quantity = self.arrangeSpotOrder(accountID=accountID, symbol=symbol,
                                                                 signalType=signalType,
                                                                 signalSource=signalSource)

                        price, amount, commission, commissionAsset = self.br.setOrder(accountID=accountID,
                                                                                      symbol=symbol, ticker=ticker,
                                                                                      date=date, quantity=quantity,
                                                                                      budget=budget,
                                                                                      signalType=signalType)

                        if price > 0 and amount > 0 and commission > 0:
                            self.accounts[accountID].implementSignal(symbol=symbol, signalType=signalType,
                                                                     signalSource=signalSource, date=date,
                                                                     budget=budget,
                                                                     price=price, amount=amount, commission=commission)

    def checkStopLoss(self, ticker, candle, date):

        symbol = ticker.split('_')[0]

        for accountID in self.accounts.keys():
            openPositionsList = self.accounts[accountID].getOpenPositionsList(symbol=symbol)

            if len(openPositionsList) > 0:
                stopLossLevel = self.accounts[accountID].getStopLossLevel()
                price = candle[constants.CLOSE]

                for pos in openPositionsList:
                    profitLoss = account.calculateProfitLoss(trade=pos, price=price)
                    percentProfitLoss = profitLoss / pos[constants.BUDGET]
                    closingSignalType = account.getOppositePositionType(pos[constants.TYPE])

                    if percentProfitLoss <= -abs(stopLossLevel):
                        budget = -1
                        realizationPrice, amount, commission = self.br.setOrder(symbol=symbol, ticker=ticker, date=date,
                                                                                quantity=pos[constants.AMOUNT],
                                                                                budget=budget,
                                                                                signalType=closingSignalType)

                        if realizationPrice > 0 and amount > 0 and commission > 0:
                            self.accounts[accountID].stopLoss(symbol=symbol, positionType=pos[constants.TYPE],
                                                              positionSource=pos[constants.SOURCE], date=date,
                                                              price=realizationPrice, commission=commission)

    def process(self, candles, date):

        for ticker in self.tickers:
            if candles[ticker].shape[0] > 0:
                self.checkStopLoss(ticker, candles[ticker], date)

                signals = self.sh.process(ticker, candles[ticker], date)

                if signals.shape[0] > 0:
                    self.sendOrders(signals=signals)

            else:
                print(f'No candle received! -- {ticker}')

        dummy = -32
