import requests
import numpy as np
from flask import Flask, jsonify

app = Flask(__name__)

# ตั้งค่า Telegram Bot API
TELEGRAM_BOT_TOKEN = "8157023046:AAErPaovjPYId1TayDThm1_81NCh3VZpSa0"
TELEGRAM_CHAT_ID = "7841591847"

# ตั้งค่า API ของ GoldAPI.io
GOLD_API_KEY = "goldapi-3w2fcsm7bictes-io"
GOLD_API_URL = "https://www.goldapi.io/api/XAU/USD/history"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=data)

def fetch_forex_price_history():
    headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
    params = {
        "limit": 200,  # ดึงข้อมูลราคาย้อนหลัง 200 จุด
        "interval": "1h"  # ระยะเวลา 1 ชั่วโมงต่อบาร์
    }
    response = requests.get(GOLD_API_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        prices = [item["close"] for item in data["prices"]]
        return prices
    return None

def analyze_market(prices):
    if len(prices) < 200:
        return None, None, None, None, None, None

    ema_short = np.mean(prices[-5:])  # EMA 5
    ema_medium = np.mean(prices[-10:])  # EMA 10
    ema_long = np.mean(prices[-50:])  # EMA 50
    ema_longest = np.mean(prices[-200:])  # EMA 200

    rsi = 100 - (100 / (1 + (np.mean(prices[-5:]) / np.mean(prices[-10:]))))
    macd = ema_short - ema_medium

    trend = "BULLISH" if ema_short > ema_medium else "BEARISH"
    long_term_trend = "BULLISH" if ema_short > ema_long else "BEARISH"
    super_long_term_trend = "BULLISH" if ema_short > ema_longest else "BEARISH"
    
    overbought = rsi > 70
    oversold = rsi < 30

    return trend, long_term_trend, super_long_term_trend, overbought, oversold, macd

def generate_signal():
    prices = fetch_forex_price_history()
    if not prices:
        return {"error": "Price data unavailable"}

    trend, long_term_trend, super_long_term_trend, overbought, oversold, macd = analyze_market(prices)

    if not trend:
        return {"message": "Not enough data for analysis"}

    price = prices[-1]  # ใช้ราคาล่าสุดจากข้อมูลราคาที่ดึงมา
    STOP_LOSS = 10  # ค่า Stop Loss 10 จุด
    LOT_SIZE = 0.05  # ขนาดล็อต

    # เป้าหมายกำไร 2000 บาทต่อวัน
    target_profit_per_trade = 2000
    profit_per_pip = 0.05 * 10  # สมมุติว่า 1 จุดทำกำไร 0.5 USD

    # คำนวณจำนวนจุดที่ต้องการเพื่อให้ได้กำไร 2,000 บาท
    points_needed_for_target_profit = target_profit_per_trade / profit_per_pip

    # กรณีซื้อ
    if price > 2935 and trend == "BULLISH" and long_term_trend == "BULLISH" and super_long_term_trend == "BULLISH" and not overbought:
        # ถ้าอยู่ในกรอบบนสุดของตลาด ให้ตั้ง TP เป็น 100 จุด
        take_profit = round(price + 100, 2) if price > 2950 else round(price + points_needed_for_target_profit, 2)
        stop_loss = round(price - STOP_LOSS, 2)
        signal = {"signal": "BUY", "entry": price, "sl": stop_loss, "tp": take_profit, "lot": LOT_SIZE}
    
    # กรณีขาย
    elif price < 2930 and trend == "BEARISH" and long_term_trend == "BEARISH" and super_long_term_trend == "BEARISH" and not oversold:
        # ถ้าอยู่ในกรอบล่างสุดของตลาด ให้ตั้ง TP เป็น 100 จุด
        take_profit = round(price - 100, 2) if price < 2900 else round(price - points_needed_for_target_profit, 2)
        stop_loss = round(price + STOP_LOSS, 2)
        signal = {"signal": "SELL", "entry": price, "sl": stop_loss, "tp": take_profit, "lot": LOT_SIZE}
    
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
