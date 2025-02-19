import requests
import time
import numpy as np

def fetch_forex_price():
    url = "https://api.forexprovider.com/latest"
    response = requests.get(url)
    data = response.json()
    return data["XAUUSD"]  # ดึงราคาทองคำ (XAU/USD)

def analyze_market():
    prices = [fetch_forex_price() for _ in range(10)]
    ema_short = np.mean(prices[-5:])
    ema_long = np.mean(prices)
    rsi = 100 - (100 / (1 + (np.mean(prices[-5:]) / np.mean(prices[-10:]))))
    
    trend = "BULLISH" if ema_short > ema_long else "BEARISH"
    overbought = rsi > 70
    oversold = rsi < 30
    
    return trend, overbought, oversold

def generate_signal(price):
    sl = 10  # Stop Loss 10 pips
    tp = 20  # Take Profit 20 pips
    lot_size = 0.05  # Lot size ตามเป้าหมาย
    trend, overbought, oversold = analyze_market()
    
    if price > 2935 and trend == "BULLISH" and not overbought:
        return {
            "signal": "BUY",
            "entry": price,
            "sl": round(price - sl, 2),
            "tp": round(price + tp, 2),
            "lot": lot_size
        }
    elif price < 2930 and trend == "BEARISH" and not oversold:
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
