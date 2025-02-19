import requests
import time

def fetch_forex_price():
    url = "https://api.forexprovider.com/latest"
    response = requests.get(url)
    data = response.json()
    return data["XAUUSD"]  # ดึงราคาทองคำ (XAU/USD)

def generate_signal(price):
    sl = 5  # Stop Loss 5 pips
    tp = 10 # Take Profit 10 pips
    buffer = 2  # แจ้งเตือนล่วงหน้าก่อนถึงราคาเข้าออเดอร์ 2 pips
    
    if price >= 2935 - buffer and price < 2935:  # แจ้งเตือนก่อนเข้า Buy
        print("⚠️ Price approaching BUY entry at 2935")
    elif price <= 2930 + buffer and price > 2930:  # แจ้งเตือนก่อนเข้า Sell
        print("⚠️ Price approaching SELL entry at 2930")
    
    if price > 2935:  # เงื่อนไขเข้า Buy
        return {
            "signal": "BUY",
            "entry": price,
            "sl": round(price - sl, 2),
            "tp": round(price + tp, 2)
        }
    elif price < 2930:  # เงื่อนไขเข้า Sell
        return {
            "signal": "SELL",
            "entry": price,
            "sl": round(price + sl, 2),
            "tp": round(price - tp, 2)
        }
    else:
        return None  # ยังไม่มีสัญญาณ

def main():
    while True:
        price = fetch_forex_price()
        generate_signal(price)  # เรียกใช้เพื่อให้แจ้งเตือนล่วงหน้าด้วย
        signal = generate_signal(price)
        
        if signal:
            print(f"✅ Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}")
        else:
            print("No trade signal yet.")
        
        time.sleep(60)  # รอ 1 นาที

if __name__ == "__main__":
    main()
