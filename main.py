import requests
import time
import numpy as np

def fetch_forex_price():
    url = "https://api.forexprovider.com/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        price = data.get("XAUUSD", None)  # ดึงราคาทองคำ
        if price is None:
            print("Warning: API did not return a valid price.")
        return price
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        print("Error decoding JSON response.")
        return None

def analyze_market():
    prices = [fetch_forex_price() for _ in range(10)]
    prices = [p for p in prices if p is not None]  # กรองค่า None ออก

    if len(prices) < 5:
        print("Error: Not enough valid prices to calculate indicators.")
        return None, None, None

    ema_short = np.mean(prices[-5:])
    ema_long = np.mean(prices)
    rsi = 100 - (100 / (1 + (np.mean(prices[-5:]) / np.mean(prices[-10:]))))
    
    trend = "BULLISH" if ema_short > ema_long else "BEARISH"
    overbought = rsi > 70
    oversold = rsi < 30
    
    return trend, overbought, oversold

def generate_signal(price):
    if price is None:
        print("Warning: No valid price received, skipping signal generation.")
        return None
    
    trend, overbought, oversold = analyze_market()
    
    if trend is None:
        print("Warning: No valid trend detected, skipping trade signal.")
        return None
    
    sl = 10  # Stop Loss 10 pips
    tp = 20  # Take Profit 20 pips
    lot_size = 0.05  # Lot size ตามเป้าหมาย
    
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
