import os
import json

from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAApplicationAuthRes,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetAccountListByAccessTokenRes,
)
from twisted.internet import reactor


CLIENT_ID = os.environ.get("CTRADER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CTRADER_CLIENT_SECRET")
ACCESS_TOKEN = os.environ.get("CTRADER_ACCESS_TOKEN")


client = Client(
    "demo.ctraderapi.com",
    5035,
    TcpProtocol
)



def stop_with(data):
    print(json.dumps(data, ensure_ascii=False))

    if reactor.running:
        reactor.stop()


def on_error(failure):
    stop_with({
        "status": "error",
        "message": str(failure)
    })


def connected(client):
    request = ProtoOAApplicationAuthReq()
    request.clientId = CLIENT_ID
    request.clientSecret = CLIENT_SECRET

    deferred = client.send(request)
    deferred.addErrback(on_error)


def disconnected(client, reason):
    pass


def on_message(client, message):

    if message.payloadType == ProtoOAApplicationAuthRes().payloadType:

        request = ProtoOAGetAccountListByAccessTokenReq()
        request.accessToken = ACCESS_TOKEN

        deferred = client.send(request)
        deferred.addErrback(on_error)

    elif message.payloadType == ProtoOAGetAccountListByAccessTokenRes().payloadType:

        response = Protobuf.extract(message)

        accounts = []

        for account in response.ctidTraderAccount:
            accounts.append({
                "ctidTraderAccountId": account.ctidTraderAccountId,
                "traderLogin": account.traderLogin,
                "isLive": account.isLive,
                "broker": account.brokerTitleShort
            })

        stop_with({
            "status": "ok",
            "accounts": accounts
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
