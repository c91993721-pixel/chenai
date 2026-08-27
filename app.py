from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>XAUUSD AI Signal</title>
    </head>
    <body style="font-family:Arial;padding:30px;background:#111;color:white;">
        <h1>🥇 XAUUSD AI Trading Signal</h1>
        <p>系統已成功上線</p>
        <hr>
        <h2>交易訊號系統</h2>
        <p>商品：XAUUSD</p>
        <p>狀態：等待市場資料</p>
        <p>訊號：WAIT</p>
        <p>方向：--</p>
        <p>進場價：--</p>
        <p>止損 SL：--</p>
        <p>止盈 TP：--</p>
    </body>
    </html>
    """

@app.route("/api/signal")
def signal():
    return jsonify({
        "symbol": "XAUUSD",
        "signal": "WAIT",
        "entry": None,
        "stop_loss": None,
        "take_profit": None,
        "time": datetime.utcnow().isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
