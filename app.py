from flask import Flask, jsonify
from datetime import datetime
import random

app = Flask(__name__)

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
