
from flask import Flask, jsonify, redirect, request
from datetime import datetime
import random
import os
import requests
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from twisted.internet import reactor
app = Flask(__name__)

CTRADER_CLIENT_ID = os.environ.get("CTRADER_CLIENT_ID")
CTRADER_CLIENT_SECRET = os.environ.get("CTRADER_CLIENT_SECRET")
CTRADER_REDIRECT_URI = "https://chenai-qry4.onrender.com/callback"
CTRADER_ACCESS_TOKEN = os.environ.get("CTRADER_ACCESS_TOKEN")
CTRADER_REFRESH_TOKEN = os.environ.get("CTRADER_REFRESH_TOKEN")
@app.route("/ctrader-test")
def ctrader_test():
    try:
        sdk_loaded = all([
            Client,
            Protobuf,
            TcpProtocol,
            EndPoints
        ])

        return jsonify({
            "status": "ok",
            "token_loaded": bool(CTRADER_ACCESS_TOKEN),
            "sdk_loaded": bool(sdk_loaded),
            "message": "cTrader SDK 與 Access Token 均已載入"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/ctrader-account-info")
def ctrader_account_info():
    return jsonify({
        "status": "ready",
        "access_token_loaded": bool(CTRADER_ACCESS_TOKEN),
        "client_id_loaded": bool(CTRADER_CLIENT_ID),
        "client_secret_loaded": bool(CTRADER_CLIENT_SECRET),
        "next_step": "connect_account_list"
  })
    })


@app.route("/ctrader-port-test")
def ctrader_port_test():
    import socket

    try:
        sock = socket.create_connection(
            ("demo.ctraderapi.com", 5035),
            timeout=10
        )
        sock.close()

        return jsonify({
            "status": "ok",
            "message": "Render 可以連線 cTrader 5035"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/ctrader-accounts")
def ctrader_accounts():
@app.route("/ctrader-accounts")
def ctrader_accounts():
    try:
        import subprocess
        import sys
        import json

        result = subprocess.run(
            [sys.executable, "ctrader_accounts.py"],
            capture_output=True,
            text=True,
            timeout=20
        )

        output = result.stdout.strip()

        if not output:
            return jsonify({
                "status": "error",
                "message": result.stderr.strip() or "沒有收到 cTrader 回應"
            }), 500

        # ctrader_accounts.py 最後一行會輸出 JSON
        last_line = output.splitlines()[-1]

        return jsonify(json.loads(last_line))

    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "cTrader 連線逾時"
        }), 504

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
def get_signal():
    # 目前先使用模擬行情測試訊號系統
    price = round(random.uniform(4300, 4500), 2)

    # 示範訊號邏輯
    if price < 4360:
        signal = "BUY"
        direction = "做多"
        sl = round(price - 10, 2)
        tp = round(price + 20, 2)

    elif price > 4440:
        signal = "SELL"
        direction = "做空"
        sl = round(price + 10, 2)
        tp = round(price - 20, 2)

    else:
        signal = "WAIT"
        direction = "等待"
        sl = "--"
        tp = "--"

    return {
        "symbol": "XAUUSD",
        "signal": signal,
        "direction": direction,
        "entry": price,
        "sl": sl,
        "tp": tp,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
@app.route("/login")
def ctrader_login():
    auth_url = (
        "https://id.ctrader.com/my/settings/openapi/grantingaccess/"
        f"?client_id={CTRADER_CLIENT_ID}"
        f"&redirect_uri={CTRADER_REDIRECT_URI}"
        "&scope=trading"
        "&product=web"
    )
    return redirect(auth_url)


@app.route("/callback")
def ctrader_callback():
    code = request.args.get("code")

    if not code:
        return "cTrader 授權失敗：沒有收到 authorization code", 400

    token_url = "https://openapi.ctrader.com/apps/token"

    params = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": CTRADER_REDIRECT_URI,
        "client_id": CTRADER_CLIENT_ID,
        "client_secret": CTRADER_CLIENT_SECRET
    }

    response = requests.get(token_url, params=params, timeout=20)

    if response.status_code != 200:
        return f"cTrader Token 取得失敗：{response.text}", 400

    token_data = response.json()

    return jsonify({
        "status": "connected",
        "message": "cTrader 授權成功",
        "expires_in": token_data.get("expiresIn")
    })

@app.route("/")
def home():
    data = get_signal()

    if data["signal"] == "BUY":
        signal_color = "#00d084"
    elif data["signal"] == "SELL":
        signal_color = "#ff4d4f"
    else:
        signal_color = "#f5c542"

    return f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="30">

        <title>XAUUSD AI Signal</title>

        <style>
            body {{
                background:#0d0f12;
                color:white;
                font-family:Arial,sans-serif;
                margin:0;
                padding:30px 20px;
            }}

            .container {{
                max-width:600px;
                margin:auto;
            }}

            h1 {{
                font-size:36px;
            }}

            .status {{
                color:#9da5b4;
            }}

            .card {{
                background:#171a1f;
                border-radius:18px;
                padding:25px;
                margin-top:25px;
            }}

            .signal {{
                font-size:42px;
                font-weight:bold;
                color:{signal_color};
            }}

            .row {{
                display:flex;
                justify-content:space-between;
                padding:13px 0;
                border-bottom:1px solid #292d34;
                font-size:18px;
            }}

            .warning {{
                color:#8d96a5;
                font-size:13px;
                margin-top:25px;
                line-height:1.6;
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <h1>🥇 XAUUSD AI Signal</h1>

            <p class="status">
                黃金交易訊號監控系統
            </p>

            <div class="card">

                <div class="signal">
                    {data["signal"]}
                </div>

                <div class="row">
                    <span>商品</span>
                    <strong>{data["symbol"]}</strong>
                </div>

                <div class="row">
                    <span>方向</span>
                    <strong>{data["direction"]}</strong>
                </div>

                <div class="row">
                    <span>進場價</span>
                    <strong>{data["entry"]}</strong>
                </div>

                <div class="row">
                    <span>止損 SL</span>
                    <strong>{data["sl"]}</strong>
                </div>

                <div class="row">
                    <span>止盈 TP</span>
                    <strong>{data["tp"]}</strong>
                </div>

                <div class="row">
                    <span>更新時間</span>
                    <strong>{data["time"]}</strong>
                </div>

            </div>

            <p class="warning">
                ⚠️ 目前為系統功能測試版本，價格為模擬資料，
                尚未連接即時 XAUUSD 行情，請勿依此訊號進行真實交易。
            </p>

        </div>
    </body>
    </html>
    """


@app.route("/api/signal")
def signal():
    return jsonify(get_signal())


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "XAUUSD AI Signal"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
