
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


@app.route("/ctrader-ssl-test")
def ctrader_ssl_test():
    import socket
    import ssl

    try:
        context = ssl.create_default_context()

        with socket.create_connection(
            ("demo.ctraderapi.com", 5035),
            timeout=10
        ) as sock:
            with context.wrap_socket(
                sock,
                server_hostname="demo.ctraderapi.com"
            ) as ssock:
                return jsonify({
                    "status": "ok",
                    "message": "cTrader SSL/TLS 連線成功",
                    "tls_version": ssock.version()
                })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


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
        print(result.stdout, flush=True)
        print(result.stderr, flush=True)
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

@app.route("/ctrader-credential-test")
def ctrader_credential_test():
    try:
        client_id = os.environ.get("CTRADER_CLIENT_ID")
        client_secret = os.environ.get("CTRADER_CLIENT_SECRET")
        refresh_token = os.environ.get("CTRADER_REFRESH_TOKEN")

        if not client_id or not client_secret or not refresh_token:
            return jsonify({
                "status": "error",
                "message": "Missing cTrader environment variables"
            }), 500

        response = requests.post(
            "https://openapi.ctrader.com/apps/token",
            params={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret
            },
            timeout=15
        )

        data = response.json()

        if response.ok and "accessToken" in data:
            return jsonify({
                "status": "ok",
                "message": "cTrader credentials accepted"
            })

        return jsonify({
            "status": "error",
            "http_status": response.status_code,
            "ctrader_response": data
        }), response.status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@app.route("/gold-test")
def gold_test():
    try:
        api_key = os.environ.get("TWELVE_DATA_API_KEY")

        if not api_key:
            return jsonify({
                "status": "error",
                "message": "TWELVE_DATA_API_KEY missing"
            }), 500

        response = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": "XAU/USD",
                "interval": "1min",
                "outputsize": 5,
                "apikey": api_key
            },
            timeout=15
        )

        data = response.json()

        if "values" not in data:
            return jsonify({
                "status": "error",
                "response": data
            }), 500

        latest = data["values"][0]

        return jsonify({
            "status": "ok",
            "symbol": "XAU/USD",
            "datetime": latest["datetime"],
            "open": latest["open"],
            "high": latest["high"],
            "low": latest["low"],
            "close": latest["close"]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/gold-mtf")
def gold_mtf():
    try:
        api_key = os.environ.get("TWELVE_DATA_API_KEY")

        if not api_key:
            return jsonify({
                "status": "error",
                "message": "TWELVE_DATA_API_KEY missing"
            }), 500

        intervals = {
            "M5": "5min",
            "M15": "15min",
            "H1": "1h"
        }

        result = {}

        for label, interval in intervals.items():
            response = requests.get(
                "https://api.twelvedata.com/time_series",
                params={
                    "symbol": "XAU/USD",
                    "interval": interval,
                    "outputsize": 100,
                    "apikey": api_key
                },
                timeout=15
            )

            data = response.json()

            if "values" not in data:
                return jsonify({
                    "status": "error",
                    "timeframe": label,
                    "response": data
                }), 500

            candles = []

            for item in reversed(data["values"]):
                candles.append({
                    "datetime": item["datetime"],
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"])
                })

            result[label] = candles

        return jsonify({
            "status": "ok",
            "symbol": "XAU/USD",
            "timeframes": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
def calc_ema(values, period):
    multiplier = 2 / (period + 1)
    ema = values[0]

    for value in values[1:]:
        ema = (value - ema) * multiplier + ema

    return ema


def calc_rsi(values, period=14):
    if len(values) < period + 1:
        return 50

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_atr(candles, period=14):
    true_ranges = []

    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        previous_close = candles[i - 1]["close"]

        true_range = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )

        true_ranges.append(true_range)

    if not true_ranges:
        return 0

    return sum(true_ranges[-period:]) / min(period, len(true_ranges))


def analyse_timeframe(candles):
    closes = [candle["close"] for candle in candles]

    price = closes[-1]
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    rsi = calc_rsi(closes)

    score = 0

    if price > ema9:
        score += 1
    else:
        score -= 1

    if ema9 > ema21:
        score += 1
    else:
        score -= 1

    if rsi >= 55:
        score += 1
    elif rsi <= 45:
        score -= 1

    if score >= 2:
        signal = "BUY"
    elif score <= -2:
        signal = "SELL"
    else:
        signal = "WAIT"

    return {
        "signal": signal,
        "score": score,
        "price": round(price, 2),
        "ema9": round(ema9, 2),
        "ema21": round(ema21, 2),
        "rsi": round(rsi, 2)
    }


@app.route("/gold-signal")
def gold_signal():
    try:
        api_key = os.environ.get("TWELVE_DATA_API_KEY")

        intervals = {
            "M5": "5min",
            "M15": "15min",
            "H1": "1h"
        }

        analyses = {}

        for label, interval in intervals.items():
            response = requests.get(
                "https://api.twelvedata.com/time_series",
                params={
                    "symbol": "XAU/USD",
                    "interval": interval,
                    "outputsize": 100,
                    "apikey": api_key
                },
                timeout=15
            )

            data = response.json()

            if "values" not in data:
                return jsonify({
                    "status": "error",
                    "timeframe": label,
                    "response": data
                }), 500

            candles = []

            for item in reversed(data["values"]):
                candles.append({
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"])
                })
             analyses[label] = analyse_timeframe(candles)
             analyses[label]["atr"] = round(calc_atr(candles), 2)

        current_price = analyses["M5"]["price"]

        weighted_score = (
            analyses["M5"]["score"] +
            analyses["M15"]["score"] * 2 +
            analyses["H1"]["score"] * 3
        )

        if weighted_score >= 6:
            final_signal = "BUY"
        elif weighted_score <= -6:
            final_signal = "SELL"
        else:
            final_signal = "WAIT"

        confidence = min(
            100,
            round(abs(weighted_score) / 18 * 100)
        )
        atr = analyses["M15"]["atr"]
        entry = current_price

        if final_signal == "BUY":
            stop_loss = entry - (atr * 1.5)
            tp1 = entry + (atr * 1.0)
            tp2 = entry + (atr * 2.0)
            tp3 = entry + (atr * 3.0)

        elif final_signal == "SELL":
            stop_loss = entry + (atr * 1.5)
            tp1 = entry - (atr * 1.0)
            tp2 = entry - (atr * 2.0)
            tp3 = entry - (atr * 3.0)

        else:
            stop_loss = None
            tp1 = None
            tp2 = None
            tp3 = None
        return jsonify({
            "status": "ok",
            "symbol": "XAU/USD",
            "price": current_price,
            "signal": final_signal,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2) if stop_loss is not None else None,
            "tp1": round(tp1, 2) if tp1 is not None else None,
            "tp2": round(tp2, 2) if tp2 is not None else None,
            "tp3": round(tp3, 2) if tp3 is not None else None,
            "confidence": confidence,
            "timeframes": analyses
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
if __name__ == "__main__":
            app.run(host="0.0.0.0", port=10000)
    
