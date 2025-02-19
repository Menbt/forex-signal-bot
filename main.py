import requests
import time
import numpy as np

# ตั้งค่า Telegram Bot API
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Message sent to Telegram")
    else:
        print("Failed to send message to Telegram")

def fetch_forex_price():
    url = "https://api.forexprovider.com/latest"  # เปลี่ยนเป็น API ที่ใช้งานได้จริง
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("XAUUSD", None)
    else:
        print("Failed to fetch price")
        return None

def analyze_market():
    prices = []
    for _ in range(10):
        price = fetch_forex_price()
        if price:
            prices.append(price)
        time.sleep(1)
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

def generate_signal(price):
    STOP_LOSS = 10
    TAKE_PROFIT = 20
    LOT_SIZE = 0.05
    
    trend, overbought, oversold, macd = analyze_market()
    if not trend:
        return None
    
    if price > 2935 and trend == "BULLISH" and not overbought:
        return {"signal": "BUY", "entry": price, "sl": round(price - STOP_LOSS, 2), "tp": round(price + TAKE_PROFIT, 2), "lot": LOT_SIZE}
    elif price < 2930 and trend == "BEARISH" and not oversold:
        return {"signal": "SELL", "entry": price, "sl": round(price + STOP_LOSS, 2), "tp": round(price - TAKE_PROFIT, 2), "lot": LOT_SIZE}
    return None

def main():
    while True:
        price = fetch_forex_price()
        if price:
            signal = generate_signal(price)
            if signal:
                message = f"Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}, Lot: {signal['lot']}"
                print(message)
                send_telegram_message(message)
            else:
                print("No trade signal yet.")
        else:
            print("Price data unavailable.")
        
        time.sleep(60)

if __name__ == "__main__":
    main()
