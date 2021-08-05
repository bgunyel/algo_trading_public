import pandas as pd
from PIL.ImageChops import constant
import math

import constants


def getOppositePositionType(positionType):
    oppositeType = constants.NULL
    if positionType == constants.LONG:
        oppositeType = constants.SHORT
    elif positionType == constants.SHORT:
        oppositeType = constants.LONG

    return oppositeType


def calculateProfitLoss(trade, price):
    out = 0
    positionType = trade[constants.TYPE]

    if positionType == constants.SHORT:
        out = (trade[constants.OPEN_PRICE] - price) * trade[constants.AMOUNT] - trade[constants.COMMISSION]
    elif positionType == constants.LONG:
        out = (price - trade[constants.OPEN_PRICE]) * trade[constants.AMOUNT] - trade[constants.COMMISSION]

    return out


class Wallet:
    def __init__(self, symbol, cash, policyType, algorithmCoefficients):
        self.symbol = symbol
        self.cash = cash
        self.policyType = policyType
        self.tradeList = []
        self.algorithmCoefficients = algorithmCoefficients
        self.algorithmOccupied = {}
        self.credit = {}

        for idx in algorithmCoefficients.keys():
            self.algorithmOccupied[idx] = False
            self.credit[idx] = 0

    def getSymbol(self):
        return self.symbol

    def getCashInfo(self):
        return self.cash

    def getOpenPositionsList(self):
        openPositionsList = [trade for trade in self.tradeList if trade['isOpen']]

        # for trade in self.tradeList:
        #     if trade['isOpen']:
        #         openPositionsList.append(trade)

        return openPositionsList

    def openPosition(self, positionType, positionSource, date, budget, price, amount, commission):
        self.tradeList.append(dict([(constants.OPEN_DATE, date),
                                    (constants.SYMBOL, self.symbol),
                                    (constants.TYPE, positionType),
                                    (constants.SOURCE, positionSource),
                                    (constants.BUDGET, budget),
                                    (constants.OPEN_PRICE, price),
                                    (constants.AMOUNT, amount),
                                    (constants.COMMISSION, commission),
                                    ('isOpen', True)]))
        self.algorithmOccupied[positionSource] = True

        if positionType == constants.LONG:
            totalCost = price * amount + commission
            self.cash -= totalCost
        elif positionType == constants.SHORT:
            self.cash -= budget  # For position opening (from cash-to-credit)
            self.credit[
                positionSource] = budget + price * amount - commission  # (price*amount-commission) via short-selling

    def closePosition(self, trade, date, price, commission, closingSource):
        positionType = trade[constants.TYPE]
        positionSource = trade[constants.SOURCE]
        amount = trade[constants.AMOUNT]

        trade['isOpen'] = False
        trade[constants.CLOSE_DATE] = date
        trade[constants.CLOSING_SOURCE] = closingSource
        trade[constants.CLOSE_PRICE] = price
        trade[constants.COMMISSION] += commission

        self.algorithmOccupied[positionSource] = False

        if positionType == constants.SHORT:  # Closing a SHORT Position
            totalCost = price * amount + commission
            self.credit[positionSource] -= totalCost
            self.cash += self.credit[positionSource]
            self.credit[positionSource] = 0

        elif positionType == constants.LONG:  # Closing a LONG Position
            totalGain = price * amount - commission
            self.cash += totalGain

        trade[constants.PROFIT_LOSS] = calculateProfitLoss(trade=trade, price=price)
        trade[constants.PROFIT_LOSS_PERCENT] = 100 * trade[constants.PROFIT_LOSS] / trade[constants.BUDGET]

    def stopLoss(self, positionType, positionSource, date, price, commission):

        for trade in self.tradeList:
            if trade['isOpen'] and trade[constants.TYPE] == positionType and trade[constants.SOURCE] == positionSource:
                self.closePosition(trade=trade, date=date, price=price, commission=commission,
                                   closingSource=constants.STOP_LOSS)
                break

    def implementSignal(self, signalType, signalSource, date, budget, price, amount, commission):

        oppositeType = getOppositePositionType(signalType)

        for trade in self.tradeList:
            if trade['isOpen'] and trade[constants.TYPE] == oppositeType and trade[constants.SOURCE] == signalSource:
                self.closePosition(trade=trade, date=date, price=price, commission=commission,
                                   closingSource=signalSource)
                break

        else:  # Else of for loop
            if self.policyType == constants.SHORT_ONLY and signalType == constants.SHORT:
                self.openPosition(signalType, signalSource, date, budget, price, amount, commission)
            elif self.policyType == constants.LONG_ONLY and signalType == constants.LONG:
                self.openPosition(signalType, signalSource, date, budget, price, amount, commission)

    def getClosingPositionQuantity(self, positionType, positionSource):

        oppositeType = getOppositePositionType(positionType)

        quantity = -1

        for trade in self.tradeList:
            if trade['isOpen'] and trade[constants.TYPE] == oppositeType and trade[constants.SOURCE] == positionSource:
                quantity = trade[constants.AMOUNT]
                break

        return quantity

    def getOpeningPositionBudget(self, positionSource):

        budget = -1

        if not self.algorithmOccupied[positionSource]:
            activeCoefficients = [v for k, v in self.algorithmCoefficients.items() if
                                  self.algorithmOccupied[k] == False]
            effectiveCoefficient = self.algorithmCoefficients[positionSource] / sum(activeCoefficients)
            budget = self.cash * effectiveCoefficient

        return budget

    def getTradeTable(self):
        tradeTable = pd.DataFrame(self.tradeList)
        return tradeTable


class CommissionsWallet:
    def __init__(self, cash):
        self.cash = cash

    def receivePayment(self, payment):
        self.cash += payment

    def makePayment(self, payment):
        self.cash -= payment

    def getCashInfo(self):
        return self.cash


class Account:

    def __init__(self, symbols, exchange, accountType, policyType, baseCurrency, stopLossLevel, algorithmCoefficients,
                 budget=0, commissionRate=0.00075, isActive=False):
        self.symbols = symbols
        self.exchange = exchange
        self.accountType = accountType
        self.policyType = policyType
        self.baseCurrency = baseCurrency
        self.budget = budget
        self.commissionRate = commissionRate
        self.stopLossLevel = stopLossLevel
        self.algorithmsCoefficients = algorithmCoefficients  # Dictionary
        self.isActive = isActive

        self.wallets = {}
        for symbol in self.symbols:
            cash = self.budget / len(self.symbols)
            self.wallets[symbol] = Wallet(symbol=symbol, cash=cash, policyType=policyType,
                                          algorithmCoefficients=algorithmCoefficients)

    def getAccountType(self):
        return self.accountType

    def getPolicyType(self):
        return self.policyType

    def getStopLossLevel(self):
        return self.stopLossLevel

    def getOpenPositionsList(self, symbol):
        return self.wallets[symbol].getOpenPositionsList()

    def implementSignal(self, symbol, signalType, signalSource, date, budget, price, amount, commission):
        self.wallets[symbol].implementSignal(signalType, signalSource, date, budget, price, amount, commission)

    def stopLoss(self, symbol, positionType, positionSource, date, price, commission):
        self.wallets[symbol].stopLoss(positionType=positionType, positionSource=positionSource, date=date, price=price,
                                      commission=commission)

    def getClosingPositionQuantity(self, symbol, positionType, positionSource):
        return self.wallets[symbol].getClosingPositionQuantity(positionType=positionType, positionSource=positionSource)

    def getOpeningPositionBudget(self, symbol, positionSource):
        return self.wallets[symbol].getOpeningPositionBudget(positionSource=positionSource)

    def getTradeTable(self):
        tradeTable = pd.DataFrame()

        for symbol in self.symbols:
            table = self.wallets[symbol].getTradeTable()
            tradeTable = tradeTable.append(table)
        return tradeTable

    def setActiveStatus(self, isActive):
        self.isActive = isActive

    def getActiveStatus(self):
        return self.isActive

    def setSymbols(self, symbols):
        self.symbols = symbols

    def getSymbols(self):
        return self.symbols


class BinanceFuturesAccount:

    def __init__(self, client, symbols, leverage, marginType, policyType, stopLossLevel, algorithmCoefficients,
                 isActive=False):

        self.client = client

        self.symbols = symbols
        self.leverage = leverage
        self.marginType = marginType
        self.policyType = policyType
        self.stopLossLevel = stopLossLevel
        self.algorithmsCoefficients = algorithmCoefficients  # Dictionary
        self.isActive = isActive
        self.commissionRate = 0.00036

        info = self.client.get_symbol_info(symbol=constants.BNBUSDT)
        self.minLotSizes = {constants.BNBUSDT: float(info['filters'][2]['minQty'])}
        self.symbolPrecisions = {constants.BNBUSDT: int(math.log10(1.0 / self.minLotSizes[constants.BNBUSDT]))}
        self.minOrderSizes = {constants.BNBUSDT: float(info['filters'][3]['minNotional'])}

        self.setMarginType()

        commissionsBudget = max(self.getTotalTradeValue() * self.commissionRate * 2, self.minOrderSizes[constants.BNBUSDT] * 1.25)
        self.commissionsWallet = CommissionsWallet(cash=commissionsBudget)
        budget = self.getAssetBalance(constants.USDT) - commissionsBudget
        self.checkBNB()

        self.wallets = {}
        for symbol in self.symbols:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            cash = budget / len(self.symbols)
            self.wallets[symbol] = Wallet(symbol=symbol, cash=cash, policyType=policyType,
                                          algorithmCoefficients=algorithmCoefficients)

    def getAccountType(self):
        return self.accountType

    def getPolicyType(self):
        return self.policyType

    def getStopLossLevel(self):
        return self.stopLossLevel

    def getOpenPositionsList(self, symbol):
        return self.wallets[symbol].getOpenPositionsList()

    def setMarginType(self):
        info = self.client.futures_position_information()

        for item in info:
            symbol = item['symbol']
            if symbol in self.symbols:
                marginType = item['marginType']
                if marginType != 'isolated':
                    self.client.futures_change_margin_type(symbol=symbol, marginType=constants.ISOLATED)

    def implementSignal(self, symbol, signalType, signalSource, date, price):
        minAcceptableRatio = 0.90
        quantity = 0
        budget = 0
        commission = 0

        if self.policyType == constants.LONG_ONLY:
            if signalType == constants.LONG:
                budget = self.getOpeningPositionBudget(symbol=symbol, positionSource=signalSource)
                leveragedBudget = budget * self.leverage
                quantity = leveragedBudget / price
                minOrderQuantity = constants.FUTURES_MIN_ORDER_QUANTITIES[symbol]
                ratio = quantity / minOrderQuantity
                coefficient = math.floor(ratio)
                remainder = ratio - coefficient
                walletCash = self.wallets[symbol].getCashInfo()

                if remainder >= minAcceptableRatio and walletCash > budget / (minAcceptableRatio - 0.05) * (
                        1 + self.commissionRate):
                    coefficient = coefficient + 1
                quantity = coefficient * minOrderQuantity

            elif signalType == constants.SHORT:
                quantity = self.getClosingPositionQuantity(symbol=symbol, positionType=signalType)

        elif self.policyType == constants.SHORT_ONLY:
            if signalType == constants.LONG:
                quantity = self.getClosingPositionQuantity(symbol=symbol, positionType=signalType)
            elif signalType == constants.SHORT:
                budget = self.getOpeningPositionBudget(symbol=symbol, positionSource=signalSource)
                leveragedBudget = budget * self.leverage

        self.client.futures_create_order(symbol=symbol, side=orderSide, quantity=quantity)
        self.wallets[symbol].implementSignal(signalType, signalSource, date, budget, price, amount=quantity,
                                             commission=commission)

    def stopLoss(self, symbol, positionType, positionSource, date, price, commission):
        self.wallets[symbol].stopLoss(positionType=positionType, positionSource=positionSource, date=date, price=price,
                                      commission=commission)

    def getClosingPositionQuantity(self, symbol, positionType, positionSource):
        return self.wallets[symbol].getClosingPositionQuantity(positionType=positionType, positionSource=positionSource)

    def getOpeningPositionBudget(self, symbol, positionSource):
        return self.wallets[symbol].getOpeningPositionBudget(positionSource=positionSource)

    def getTradeTable(self):
        tradeTable = pd.DataFrame()

        for symbol in self.symbols:
            table = self.wallets[symbol].getTradeTable()
            tradeTable = tradeTable.append(table)
        return tradeTable

    def setActiveStatus(self, isActive):
        self.isActive = isActive

    def getActiveStatus(self):
        return self.isActive

    def setSymbols(self, symbols):
        self.symbols = symbols

    def getSymbols(self):
        return self.symbols

    def getAssetBalance(self, asset):
        info = self.client.futures_account_balance()
        out = 0

        for item in info:
            if asset == item['asset']:
                out = float(item['balance'])
                break

        return out

    def getTotalPositionsValue(self):
        info = self.client.futures_position_information()

        value = 0
        margin = 0
        for item in info:
            symbol = item['symbol']
            if symbol in self.symbols:
                quantity = abs(float(item['positionAmt']))
                markPrice = float(item['markPrice'])
                value += quantity * markPrice
                margin += float(item['isolatedMargin'])

        return value, margin

    def getTotalTradeValue(self):
        cash = self.getAssetBalance('USDT')
        positionValue, totalMargin = self.getTotalPositionsValue()
        info = self.client.futures_position_information()
        out = (cash - totalMargin) * self.leverage + positionValue
        return out

    def checkBNB(self):
        price = float(self.client.get_symbol_ticker(symbol=constants.BNBUSDT)['price'])
        bnb = self.getAssetBalance('BNB') * price
        requiredBNB = self.getTotalTradeValue() * self.commissionRate * 1.25  # in USDT

        if bnb < requiredBNB:

            try:
                diffBNB = requiredBNB - bnb

                budget = max(self.minOrderSizes[constants.BNBUSDT], diffBNB)
                safetyBudget = round(1.15 * budget, 2)  # How much to be transferred to Spot for the purchase

                if self.commissionsWallet.getCashInfo() >= budget:
                    self.client.futures_account_transfer(asset=constants.USDT, amount=safetyBudget, type=2)
                    self.commissionsWallet.makePayment(payment=budget)
                    order = self.client.order_market_buy(symbol='BNBUSDT', quoteOrderQty=safetyBudget)
                    bnbTransfer = float(self.client.get_asset_balance(asset='BNB')['free'])
                    self.client.futures_account_transfer(asset='BNB', amount=bnbTransfer, type=1)
                else:
                    print('COMMISSIONS WALLET IS POOR !')

            except Exception as e:
                print("BNB could NOT be purchased - {}".format(e))
