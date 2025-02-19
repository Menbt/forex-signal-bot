import requests
import numpy as np
from flask import Flask, jsonify
import time

app = Flask(__name__)

# ตั้งค่า Telegram Bot API
TELEGRAM_BOT_TOKEN = "8157023046:AAErPaovjPYId1TayDThm1_81NCh3VZpSa0"
TELEGRAM_CHAT_ID = "7841591847"

# ตั้งค่า API ของ GoldAPI.io
GOLD_API_KEY = "goldapi-3w2fcsm7bictes-io"
GOLD_API_URL = "https://www.goldapi.io/api/XAU/USD"

# เวลาที่ดึงข้อมูลล่าสุด
last_fetched_time = time.time()

# ฟังก์ชันการส่งข้อความผ่าน Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=data)

# ฟังก์ชันดึงข้อมูลราคาจาก API
def fetch_forex_price():
    global last_fetched_time
    current_time = time.time()
    # ตรวจสอบว่าเวลาผ่านไปมากกว่า 6 นาที (360 วินาที) แล้วหรือยัง
    if current_time - last_fetched_time > 360:
        headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
        response = requests.get(GOLD_API_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            last_fetched_time = current_time  # อัปเดตเวลาที่ดึงข้อมูลล่าสุด
            return data.get("price", None)
    else:
        return None  # ถ้าผ่านไปไม่ถึง 6 นาที จะไม่ดึงข้อมูลใหม่

# ฟังก์ชันคำนวณ Fibonacci retracement
def fibonacci_retracement(prices):
    high = max(prices)
    low = min(prices)
    diff = high - low
    levels = {
        "level_0": high,
        "level_23.6": high - 0.236 * diff,
        "level_38.2": high - 0.382 * diff,
        "level_50": high - 0.5 * diff,
        "level_61.8": high - 0.618 * diff,
        "level_100": low
    }
    return levels

# ฟังก์ชันการคำนวณ EMA
def calculate_ema(prices, period):
    return np.mean(prices[-period:])

# ฟังก์ชันการคำนวณ RSI
def calculate_rsi(prices, period=14):
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ฟังก์ชันการสร้างสัญญาณการเทรด
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

    # Fibonacci Levels for trade decision
    fib_levels = fibonacci_retracement(prices)

    # วิเคราะห์ราคาตาม Fibonacci
    if price > fib_levels['level_61.8'] and trend == "BULLISH" and not overbought:
        signal = {"signal": "BUY", "entry": price, "sl": round(price - STOP_LOSS, 2), "tp": round(price + TAKE_PROFIT, 2), "lot": LOT_SIZE}
    elif price < fib_levels['level_23.6'] and trend == "BEARISH" and not oversold:
        signal = {"signal": "SELL", "entry": price, "sl": round(price + STOP_LOSS, 2), "tp": round(price - TAKE_PROFIT, 2), "lot": LOT_SIZE}
    else:
        send_telegram_message("No trade signal yet. Price is not suitable for entry.")
        return {"message": "No trade signal yet"}

    send_telegram_message(f"Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}, Lot: {signal['lot']}")
    return signal

# ฟังก์ชันการวิเคราะห์ตลาด (Trend, RSI, MACD)
def analyze_market(prices):
    if len(prices) < 10:
        return None, None, None, None

    ema_short = calculate_ema(prices, 5)
    ema_long = calculate_ema(prices, 50)
    rsi = calculate_rsi(prices)
    macd = ema_short - ema_long

    trend = "BULLISH" if ema_short > ema_long else "BEARISH"
    overbought = rsi > 70
    oversold = rsi < 30

    return trend, overbought, oversold, macd

# Route สำหรับเทรด
@app.route('/trade', methods=['GET'])
def trade():
    return jsonify(generate_signal())

@app.route('/')
def home():
    return "Forex Signal Bot is Running!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
