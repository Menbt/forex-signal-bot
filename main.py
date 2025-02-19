import requests
import time
import talib
import numpy as np

# ตัวแปรเก็บราคาย้อนหลัง
prices = []

# ดึงราคาจาก API
def fetch_forex_price():
    url = "https://api.forexprovider.com/latest"
    response = requests.get(url)
    data = response.json()
    return data["XAUUSD"]  # ราคาทองคำ (XAU/USD)

# คำนวณแนวรับแนวต้าน
def calculate_support_resistance(prices):
    if len(prices) < 20:
        return None, None
    support = min(prices[-20:])
    resistance = max(prices[-20:])
    return support, resistance

# วิเคราะห์สัญญาณซื้อขาย
def generate_signal(prices):
    if len(prices) < 21:
        return None
    
    price = prices[-1]
    close_prices = np.array(prices, dtype=float)
    
    # คำนวณ EMA
    ema_9 = talib.EMA(close_prices, timeperiod=9)
    ema_21 = talib.EMA(close_prices, timeperiod=21)
    
    # คำนวณ RSI
    rsi = talib.RSI(close_prices, timeperiod=14)
    
    # คำนวณ MACD
    macd, signal, _ = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
    
    # คำนวณแนวรับแนวต้าน
    support, resistance = calculate_support_resistance(prices)
    
    sl = 5  # Stop Loss 5 pips
    tp = 10 # Take Profit 10 pips
    
    # เงื่อนไขเข้า Buy
    if ema_9[-1] > ema_21[-1] and macd[-1] > signal[-1] and rsi[-1] > 50 and price > resistance:
        return {
            "signal": "BUY",
            "entry": price,
            "sl": round(price - sl, 2),
            "tp": round(price + tp, 2)
        }
    
    # เงื่อนไขเข้า Sell
    elif ema_9[-1] < ema_21[-1] and macd[-1] < signal[-1] and rsi[-1] < 50 and price < support:
        return {
            "signal": "SELL",
            "entry": price,
            "sl": round(price + sl, 2),
            "tp": round(price - tp, 2)
        }
    
    return None

# ฟังก์ชันหลัก
def main():
    global prices
    while True:
        price = fetch_forex_price()
        prices.append(price)
        
        if len(prices) > 50:
            prices.pop(0)  # เก็บแค่ 50 แท่งล่าสุด
        
        signal = generate_signal(prices)
        
        if signal:
            print(f"Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}")
        else:
            print("No trade signal yet.")
        
        time.sleep(60)  # รอ 1 นาที

if __name__ == "__main__":
    main()
