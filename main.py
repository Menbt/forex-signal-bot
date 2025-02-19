import pandas as pd
import requests

# ตั้งค่า API ดึงข้อมูลราคาจริง (อาจใช้ Binance, Forex API)
API_URL = "https://api.forexprovider.com"  # <-- เปลี่ยนเป็น API จริง

def get_price():
    """ ดึงราคาล่าสุดจาก API """
    response = requests.get(API_URL)
    data = response.json()
    return data["price"]

def calculate_ema(data, period):
    """ คำนวณ EMA (Exponential Moving Average) """
    return data.ewm(span=period, adjust=False).mean()

def generate_signal():
    """ ตรวจสอบสัญญาณ Buy/Sell """
    prices = pd.Series([get_price() for _ in range(100)])  # จำลองราคา 100 จุด
    ema10 = calculate_ema(prices, 10)
    ema50 = calculate_ema(prices, 50)
    ema200 = calculate_ema(prices, 200)

    if ema10.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]:
        return "📈 Buy Signal"
    elif ema10.iloc[-1] < ema50.iloc[-1] < ema200.iloc[-1]:
        return "📉 Sell Signal"
    return "⏳ No Clear Signal"

# แสดงผล
if __name__ == "__main__":
    signal = generate_signal()
    print(f"🔔 Forex Signal: {signal}")
