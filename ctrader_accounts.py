import os
import json
import time

from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAApplicationAuthRes,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetAccountListByAccessTokenRes,
    ProtoOAAccountAuthReq,
    ProtoOAAccountAuthRes,
    ProtoOASymbolsListReq,
    ProtoOASymbolsListRes,
    ProtoOASubscribeSpotsReq,
    ProtoOASpotEvent,
    ProtoOAGetTrendbarsReq,
    ProtoOAGetTrendbarsRes,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
from twisted.internet import reactor


CLIENT_ID = os.environ.get("CTRADER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CTRADER_CLIENT_SECRET")
ACCESS_TOKEN = os.environ.get("CTRADER_ACCESS_TOKEN")


client = Client(
    EndPoints.PROTOBUF_DEMO_HOST,
    EndPoints.PROTOBUF_PORT,
    TcpProtocol
)

finished = False



def stop_with(data):
    global finished
    finished = True

    print(json.dumps(data, ensure_ascii=False), flush=True)

    if reactor.running:
        reactor.stop()


def on_error(failure):
    print("CTRADER SEND ERROR:", repr(failure.value), flush=True)
    print(failure.getTraceback(), flush=True)
    
    stop_with({
        "status": "error",
        "message": str(failure)
    })
def connected(client):
        print("CONNECTED CALLBACK FIRED", flush=True)
    
        request = ProtoOAApplicationAuthReq()
        request.clientId = CLIENT_ID
        request.clientSecret = CLIENT_SECRET
  
        print("SENDING APPLICATION AUTH", flush=True)
 
    
        deferred = client.send(request)
        deferred.addErrback(on_error)
    

def disconnected(client, reason):
    return

    


def on_message(client, message):
    extracted = Protobuf.extract(message)

    print(
        "cTrader message:",
        message.payloadType,
        flush=True
    )
    if message.payloadType == ProtoOAApplicationAuthRes().payloadType:
        print("cTrader Application Auth OK", flush=True)

        account_request = ProtoOAGetAccountListByAccessTokenReq()
        account_request.accessToken = ACCESS_TOKEN

        deferred = client.send(account_request)
        deferred.addErrback(on_error)



    if message.payloadType == ProtoOAGetAccountListByAccessTokenRes().payloadType:

        response = Protobuf.extract(message)

        accounts = []

        for account in response.ctidTraderAccount:
            accounts.append({
                "ctidTraderAccountId": account.ctidTraderAccountId,
                "traderLogin": account.traderLogin,
                "isLive": account.isLive,
                "broker": getattr(account, "brokerTitleShort", "")
            })

        selected_account = response.ctidTraderAccount[0]

        auth_request = ProtoOAAccountAuthReq()
        auth_request.ctidTraderAccountId = selected_account.ctidTraderAccountId
        auth_request.accessToken = ACCESS_TOKEN

        deferred = client.send(auth_request)
        deferred.addErrback(on_error)
        
    if message.payloadType == ProtoOAAccountAuthRes().payloadType:
        response = Protobuf.extract(message)

        symbols_request = ProtoOASymbolsListReq()
        symbols_request.ctidTraderAccountId = response.ctidTraderAccountId
        symbols_request.includeArchivedSymbols = False

        deferred = client.send(symbols_request)
        deferred.addErrback(on_error)
        
    if message.payloadType == ProtoOASymbolsListRes().payloadType:
        response = Protobuf.extract(message)

        xauusd = []

        for symbol in response.symbol:
            symbol_name = getattr(symbol, "symbolName", "")
            if "XAUUSD" in symbol_name.upper():
                xauusd.append({
                    "symbolId": symbol.symbolId,
                    "symbolName": symbol_name
                })
            if not xauusd:
                xauusd = [{"symbolId": 41, "symbolName": "XAUUSD"}]
            if xauusd:
                spot_request = ProtoOASubscribeSpotsReq()
                spot_request.ctidTraderAccountId = response.ctidTraderAccountId
                spot_request.symbolId.append(xauusd[0]["symbolId"])

                deferred = client.send(spot_request)
                deferred.addErrback(on_error)

                trend_request = ProtoOAGetTrendbarsReq()
                trend_request.ctidTraderAccountId = response.ctidTraderAccountId
                trend_request.symbolId = xauusd[0]["symbolId"]
                trend_request.period = ProtoOATrendbarPeriod.Value("M5")
                trend_request.count = 100
                trend_request.toTimestamp = int(time.time() * 1000)
                trend_request.fromTimestamp = int((time.time() - 2 * 24 * 60 * 60) * 1000)

                deferred = client.send(trend_request)
                deferred.addErrback(on_error)

        
            else:
                stop_with({
                   "status": "error",
                   "stage": "symbols",
                   "message": "XAUUSD not found"
                }) 
    if message.payloadType == ProtoOASpotEvent().payloadType:
        spot = Protobuf.extract(message)

        bid = spot.bid / 100000 if getattr(spot, "bid", 0) else None
        ask = spot.ask / 100000 if getattr(spot, "ask", 0) else None
    if message.payloadType == ProtoOAGetTrendbarsRes().payloadType:
        response = Protobuf.extract(message)

        bars = []

        for bar in response.trendbar:
            low = bar.low / 100000
            open_price = (bar.low + bar.deltaOpen) / 100000
            high = (bar.low + bar.deltaHigh) / 100000
            close = (bar.low + bar.deltaClose) / 100000

            bars.append({
                "timestamp": bar.utcTimestampInMinutes,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close
            })
        closes = [bar["close"] for bar in bars]

        def ema(values, period):
            multiplier = 2 / (period + 1)
            result = values[0]

            for value in values[1:]:
                result = (value - result) * multiplier + result

            return round(result, 2)

        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        ema50 = ema(closes, 50)

        if ema9 > ema21 > ema50:
            signal = "LONG"
        elif ema9 < ema21 < ema50:
            signal = "SHORT"
        else:
            signal = "WAIT"
        stop_with({
            "status": "ok",
            "stage": "signal",
            "timeframe": "M5",
            "count": len(bars),
            "ema9": ema9,
            "ema21": ema21,
            "ema50": ema50,
            "signal": signal,
            "lastClose": bars[-1]["close"],
            "bars": bars[-5:]
        })

if not CLIENT_ID or not CLIENT_SECRET or not ACCESS_TOKEN:
    stop_with({
        "status": "error",
        "message": "Missing cTrader environment variables"
    })
else:
    client.setConnectedCallback(connected)
    client.setDisconnectedCallback(disconnected)
    client.setMessageReceivedCallback(on_message)

    client.startService()

    reactor.callLater(
        15,
        lambda: stop_with({
            "status": "error",
            "message": "cTrader connection timeout"
        })
    )

    reactor.run()
