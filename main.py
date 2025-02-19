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
GOLD_API_URL = "https://www.goldapi.io/api/XAU/USD/history"

# ตัวแปรสำหรับควบคุมการดึงข้อมูลจาก API
last_request_time = 0  # เวลาเมื่อครั้งสุดท้ายที่ดึงข้อมูล
request_count = 0  # จำนวนครั้งที่เรียก API ใน 1 ชั่วโมง
MAX_REQUESTS_PER_HOUR = 10  # จำกัดการเรียก API 10 ครั้งต่อชั่วโมง
TIME_FRAME = 3600  # 1 ชั่วโมงในหน่วยวินาที

# ตัวแปรสำหรับส่งข้อความทุกๆ 10 นาที
last_signal_time = 0  # เวลาที่ส่งสัญญาณหรือข้อความล่าสุด
SIGNAL_INTERVAL = 600  # 10 นาที (600 วินาที)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=data)

def fetch_forex_price_history():
    global last_request_time, request_count

    # ตรวจสอบเวลาปัจจุบัน
    current_time = time.time()

    # หากเวลาผ่านไปเกิน 1 ชั่วโมง (3600 วินาที) หลังจากดึงข้อมูลครั้งล่าสุด
    if current_time - last_request_time > TIME_FRAME:
        # รีเซ็ตการนับจำนวนครั้ง
        request_count = 0
        last_request_time = current_time

    # หากจำนวนครั้งที่เรียก API น้อยกว่า 10 ครั้งใน 1 ชั่วโมง
    if request_count < MAX_REQUESTS_PER_HOUR:
        headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
        params = {
            "limit": 200,  # ดึงข้อมูลราคาย้อนหลัง 200 จุด
            "interval": "6m"  # ระยะเวลา 6 นาทีต่อบาร์
        }
        response = requests.get(GOLD_API_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            prices = [item["close"] for item in data["prices"]]
            request_count += 1  # เพิ่มจำนวนครั้งที่เรียก API
            return prices
        else:
            # ส่งข้อความแจ้งเตือนกรณี API ไม่ตอบกลับ
            send_telegram_message("Error: Failed to fetch data from API")
            return None
    else:
        # ส่งข้อความแจ้งเตือนกรณีเกินจำนวนครั้งที่ดึงข้อมูล
        send_telegram_message("API request limit exceeded. Please wait for the next hour.")
        return {"error": "API request limit exceeded. Please wait for the next hour."}

def calculate_support_resistance(prices):
    # คำนวณระดับแนวรับ (Support) และแนวต้าน (Resistance) จากข้อมูลราคาย้อนหลัง
    high = max(prices[-50:])  # ระดับราคาสูงสุดใน 50 จุดล่าสุด
    low = min(prices[-50:])   # ระดับราคาต่ำสุดใน 50 จุดล่าสุด
    range_ = high - low       # ช่วงของราคาที่เคลื่อนไหว

    support = low + range_ * 0.382  # ใช้ Fibonacci retracement 38.2% สำหรับแนวรับ
    resistance = high - range_ * 0.382  # ใช้ Fibonacci retracement 38.2% สำหรับแนวต้าน

    return support, resistance

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
    if isinstance(prices, dict) and "error" in prices:
        return prices  # ส่งข้อความเมื่อเกินจำนวนครั้งที่ดึงข้อมูล

    if not prices:
        return {"error": "Price data unavailable"}

    trend, long_term_trend, super_long_term_trend, overbought, oversold, macd = analyze_market(prices)
    support, resistance = calculate_support_resistance(prices)  # คำนวณระดับแนวรับและแนวต้าน

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
    if price > resistance and trend == "BULLISH" and long_term_trend == "BULLISH" and super_long_term_trend == "BULLISH" and not overbought:
        # ถ้าอยู่ในกรอบบนสุดของตลาด ให้ตั้ง TP เป็น 100 จุด
        take_profit = round(price + 100, 2) if price > resistance else round(price + points_needed_for_target_profit, 2)
        stop_loss = round(price - STOP_LOSS, 2)
        signal = {"signal": "BUY", "entry": price, "sl": stop_loss, "tp": take_profit, "lot": LOT_SIZE}
    
    # กรณีขาย
    elif price < support and trend == "BEARISH" and long_term_trend == "BEARISH" and super_long_term_trend == "BEARISH" and not oversold:
        # ถ้าอยู่ในกรอบล่างสุดของตลาด ให้ตั้ง TP เป็น 100 จุด
        take_profit = round(price - 100, 2) if price < support else round(price - points_needed_for_target_profit, 2)
        stop_loss = round(price + STOP_LOSS, 2)
        signal = {"signal": "SELL", "entry": price, "sl": stop_loss, "tp": take_profit, "lot": LOT_SIZE}
    
    else:
        # ส่งข้อความทุก 10 นาทีกรณีไม่มีสัญญาณ
        current_time = time.time()
        global last_signal_time
        
        if current_time - last_signal_time >= SIGNAL_INTERVAL:
            reason = "No trade signal: Conditions not met or market is not favorable."
            send_telegram_message(f"Reminder: No signal to enter trade at {price}. Reason: {reason}")
            last_signal_time = current_time  # อัปเดตเวลาที่ส่งข้อความ
        
        return {"message": "No trade signal yet"}

    send_telegram_message(f"Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}, Lot: {signal['lot']}")
    last_signal_time = time.time()  # อัปเดตเวลาส่งสัญญาณ
    return signal

@app.route('/trade', methods=['GET'])
def trade():
    return jsonify(generate_signal())

@app.route('/')
def home():
    return "Forex Signal Bot is Running!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
