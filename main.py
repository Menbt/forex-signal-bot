import requests
import time
import numpy as np
import MetaTrader5 as mt5

# ตั้งค่าบัญชี MT5
ACCOUNT = 12345678  # ใส่เลขบัญชี MT5
PASSWORD = "yourpassword"  # ใส่รหัสผ่านบัญชี
SERVER = "YourBroker-Server"  # ใส่ชื่อเซิร์ฟเวอร์โบรกเกอร์
SYMBOL = "XAUUSD"
LOT_SIZE = 0.05  # Lot size ตามเป้าหมาย
STOP_LOSS = 10  # Stop Loss 10 pips
TAKE_PROFIT = 20  # Take Profit 20 pips

# ตั้งค่า Telegram Bot API
TELEGRAM_BOT_TOKEN = "HTTP API:8157023046:AAErPaovjPYId1TayDThm1_81NCh3VZpSa0"
TELEGRAM_CHAT_ID = "7841591847"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Message sent to Telegram")
    else:
        print("Failed to send message to Telegram")


def connect_mt5():
    if not mt5.initialize():
        print("MT5 connection failed")
        return False
    if not mt5.login(ACCOUNT, password=PASSWORD, server=SERVER):
        print("Login failed")
        return False
    print("Connected to MT5")
    return True


def fetch_forex_price():
    url = "https://api.forexprovider.com/latest"
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
    trend, overbought, oversold, macd = analyze_market()
    if not trend:
        return None
    
    if price > 2935 and trend == "BULLISH" and not overbought:
        return {"signal": "BUY", "entry": price, "sl": round(price - STOP_LOSS, 2), "tp": round(price + TAKE_PROFIT, 2), "lot": LOT_SIZE}
    elif price < 2930 and trend == "BEARISH" and not oversold:
        return {"signal": "SELL", "entry": price, "sl": round(price + STOP_LOSS, 2), "tp": round(price - TAKE_PROFIT, 2), "lot": LOT_SIZE}
    return None


def place_order(order_type, price, sl, tp, lot):
    order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "Auto Trading Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(order)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")
        send_telegram_message(f"Order failed: {result.comment}")
    else:
        message = f"Order placed: {order_type} at {price}, SL: {sl}, TP: {tp}, Lot: {lot}"
        print(message)
        send_telegram_message(message)


def main():
    if not connect_mt5():
        return
    
    while True:
        price = fetch_forex_price()
        if price:
            signal = generate_signal(price)
            if signal:
                message = f"Signal: {signal['signal']} at {signal['entry']}, SL: {signal['sl']}, TP: {signal['tp']}, Lot: {signal['lot']}"
                print(message)
                send_telegram_message(message)
                place_order(signal['signal'], signal['entry'], signal['sl'], signal['tp'], signal['lot'])
            else:
                print("No trade signal yet.")
        else:
            print("Price data unavailable.")
        
        time.sleep(60)


if __name__ == "__main__":
    main()
