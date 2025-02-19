import requests
import time
import numpy as np

def fetch_forex_price():
    url = "https://api.forexprovider.com/latest"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # เช็ค HTTP Error เช่น 404, 500
        if response.text.strip():  # ตรวจสอบว่า Response ไม่ใช่ค่าว่าง
            data = response.json()  # แปลง JSON
            return data.get("XAUUSD", None)  # ตรวจสอบว่ามี Key "XAUUSD" หรือไม่
        else:
            print("Empty response from API.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        print("Error decoding JSON. Response may not be in JSON format.")
        print(f"Response: {response.text}")
        return None

# ทดสอบการดึงข้อมูล
price = fetch_forex_price()
print(f"Forex Price: {price}")

def analyze_market():
    prices = [fetch_forex_price() for _ in range(10)]
    ema_short = np.mean(prices[-5:])
    ema_long = np.mean(prices)
    rsi = 100 - (100 / (1 + (np.mean(prices[-5:]) / np.mean(prices[-10:]))))
    macd = ema_short - ema_long
    trend = "BULLISH" if ema_short > ema_long else "BEARISH"
    overbought = rsi > 70
    oversold = rsi < 30
    return trend, overbought, oversold, macd

def generate_signal(price):
    sl = 10  # Stop Loss 10 pips
    tp = 20  # Take Profit 20 pips
    lot_size = 0.05  # Lot size ตามเป้าหมาย
    trend, overbought, oversold, macd = analyze_market()
    alert_threshold = 2  # แจ้งเตือนล่วงหน้าเมื่อเข้าใกล้ระดับ

    if 2935 - alert_threshold < price < 2935 and trend == "BULLISH" and not overbought:
        print(f"[ALERT] Price approaching BUY entry zone: {price}")
    elif 2930 + alert_threshold > price > 2930 and trend == "BEARISH" and not oversold:
        print(f"[ALERT] Price approaching SELL entry zone: {price}")
    
    if price > 2935 and trend == "BULLISH" and not overbought and macd > 0:
        return {
            "signal": "BUY",
            "entry": price,
            "sl": round(price - sl, 2),
            "tp": round(price + tp, 2),
            "lot": lot_size
        }
    elif price < 2930 and trend == "BEARISH" and not oversold and macd < 0:
        return {
            "signal": "SELL",
            "entry": price,
            "sl": round(price + sl, 2),
            "tp": round(price - tp, 2),
            "lot": lot_size
        }
    else:
        return None

def main():
    while True:
        price = fetch_forex_price()
        signal = generate_signal(price)
        
        if signal:
            print(f"Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}, Lot: {signal['lot']}")
        else:
            print("No trade signal yet.")
        
        time.sleep(60)  # รอ 1 นาที

if __name__ == "__main__":
    main()
