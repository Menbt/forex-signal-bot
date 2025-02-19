import requests
import numpy as np
from flask import Flask, jsonify

app = Flask(__name__)

# ตั้งค่า Telegram Bot API
TELEGRAM_BOT_TOKEN = "8157023046:AAErPaovjPYId1TayDThm1_81NCh3VZpSa0"
TELEGRAM_CHAT_ID = "7841591847"

# ตั้งค่า API ของ GoldAPI.io
GOLD_API_KEY = "your_goldapi_key"
GOLD_API_URL = "https://www.goldapi.io/api/XAU/USD"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=data)

def fetch_forex_price():
    headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
    response = requests.get(GOLD_API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("price", None)
    return None

def analyze_market(prices):
    if len(prices) < 10:
        return None, None, None, None

    ema_short = np.mean(prices[-5:])
    ema_long = np.mean(prices)
    rsi = 100 - (100 / (1 + (np.mean(prices[-5:]) / np.mean(prices[-10:]))))
    macd = ema_short - ema_long

    trend = "BULLISH" if ema_short > ema_long else "BEARISH"
    overbought = rsi > 70
    oversold = rsi < 30

    return trend, overbought, oversold, macd

def generate_signal():
    price = fetch_forex_price()
    if not price:
        return {"error": "Price data unavailable"}

    prices = [price] * 10  # จำลองราคาย้อนหลัง
    trend, overbought, oversold, macd = analyze_market(prices)

    if not trend:
        return {"message": "Not enough data for analysis"}

    STOP_LOSS = 10
    TAKE_PROFIT = 20
    LOT_SIZE = 0.05

    if price > 2935 and trend == "BULLISH" and not overbought:
        signal = {"signal": "BUY", "entry": price, "sl": round(price - STOP_LOSS, 2), "tp": round(price + TAKE_PROFIT, 2), "lot": LOT_SIZE}
    elif price < 2930 and trend == "BEARISH" and not oversold:
        signal = {"signal": "SELL", "entry": price, "sl": round(price + STOP_LOSS, 2), "tp": round(price - TAKE_PROFIT, 2), "lot": LOT_SIZE}
    else:
        return {"message": "No trade signal yet"}

    send_telegram_message(f"Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}, Lot: {signal['lot']}")
    return signal

@app.route('/trade', methods=['GET'])
def trade():
    return jsonify(generate_signal())

@app.route('/')
def home():
    return "Forex Signal Bot is Running!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
