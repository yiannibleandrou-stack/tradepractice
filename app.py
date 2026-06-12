import os
from flask import Flask, request, jsonify

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


app = Flask(__name__)

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

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

    print("Received webhook data:", data, flush=True)

    if not data:
        print("ERROR: No JSON received", flush=True)
        return jsonify({"error": "No JSON received"}), 400

    if data.get("secret") != WEBHOOK_SECRET:
        print("ERROR: Bad webhook secret", flush=True)
        return jsonify({"error": "Unauthorized"}), 401

    symbol = data.get("ticker") or data.get("symbol")
    action = str(data.get("action", "")).lower()
    qty = float(data.get("qty", 1))

    print(f"Parsed order: symbol={symbol}, action={action}, qty={qty}", flush=True)

    if not symbol:
        print("ERROR: Missing ticker/symbol", flush=True)
        return jsonify({"error": "Missing ticker/symbol"}), 400

    if action not in ["buy", "sell"]:
        print("ERROR: Invalid action", flush=True)
        return jsonify({"error": "Action must be buy or sell"}), 400

    side = OrderSide.BUY if action == "buy" else OrderSide.SELL

    try:
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY
        )

        order = trading_client.submit_order(order_data)

        print("ALPACA ORDER SUBMITTED:", order, flush=True)

        return jsonify({
            "status": "order_submitted",
            "symbol": symbol,
            "action": action,
            "qty": qty,
            "alpaca_order_id": str(order.id)
        }), 200

    except Exception as e:
        print("ALPACA ERROR:", str(e), flush=True)
        return jsonify({
            "error": "Alpaca order failed",
            "details": str(e)
        }), 500
