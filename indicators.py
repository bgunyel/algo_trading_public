def ema(currentValue, numPeriods, prevEMA):
    alpha = 2 / (numPeriods + 1)
    currentEMA = alpha * currentValue + (1 - alpha) * prevEMA
    return currentEMA


def rma(currentValue, numPeriods, prevRMA):
    alpha = 1 / numPeriods
    currentRMA = alpha * currentValue + (1 - alpha) * prevRMA
    return currentRMA


def trueRange(currentHigh, currentLow, previousClose):

    tr1 = abs(currentHigh - currentLow)
    tr2 = abs(currentHigh - previousClose)
    tr3 = abs(currentLow - previousClose)

    return max(tr1, tr2, tr3)


def atr(currentHigh, currentLow, previousClose, numPeriods, prevATR):

    tr = trueRange(currentHigh=currentHigh, currentLow=currentLow, previousClose=previousClose)
    out = rma(currentValue=tr, numPeriods=numPeriods, prevRMA=prevATR)
    return out
