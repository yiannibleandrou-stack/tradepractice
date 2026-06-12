import os
from flask import Flask, request, jsonify

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


app = Flask(__name__)

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise RuntimeError("Missing Alpaca API keys.")

if not WEBHOOK_SECRET:
    raise RuntimeError("Missing WEBHOOK_SECRET.")

trading_client = TradingClient(
    api_key=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
    paper=True
)


@app.get("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "TradingView to Alpaca webhook is running."
    })


@app.post("/webhook")
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    if data.get("secret") != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    symbol = data.get("ticker") or data.get("symbol")
    action = str(data.get("action", "")).lower()
    qty = float(data.get("qty", 1))

    if not symbol:
        return jsonify({"error": "Missing ticker/symbol"}), 400

    if action not in ["buy", "sell"]:
        return jsonify({"error": "Action must be buy or sell"}), 400

    if qty <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400

    side = OrderSide.BUY if action == "buy" else OrderSide.SELL

    order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY
    )

    order = trading_client.submit_order(order_data)

    return jsonify({
        "status": "order_submitted",
        "symbol": symbol,
        "action": action,
        "qty": qty,
        "alpaca_order_id": str(order.id)
    })
