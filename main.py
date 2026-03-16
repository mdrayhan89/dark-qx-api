import os
import json
import threading
import websocket
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# আপনার ব্র্যান্ডিং তথ্য
OWNER_INFO = {
    "Owner_Developer": "DARK-X-RAYHAN",
    "Telegram": "@mdrayhan85",
    "Channel": "https://t.me/mdrayhan85"
}

# গ্লোবাল ডাটা স্টোরেজ
live_candles = []

def on_message(ws, message):
    global live_candles
    try:
        # কোট্যাক্স থেকে আসা ডাটা প্রসেসিং (এখানে লজিক ইমপ্লিমেন্ট করতে হবে)
        # নমুনা হিসেবে আপনার ফরম্যাটে একটি ডাটা জেনারেট হচ্ছে
        now = datetime.now()
        new_candle = {
            "id": str(len(live_candles) + 1),
            "pair": "USDBDT_otc",
            "timeframe": "M1",
            "candle_time": now.strftime("%Y-%m-%d %H:%M:00"),
            "open": "128.223", 
            "high": "128.237",
            "low": "128.217",
            "close": "128.233",
            "volume": "48",
            "color": "doji",
            "created_at": now.strftime("%Y-%m-%d %H:%M:00")
        }
        live_candles.insert(0, new_candle)
        if len(live_candles) > 500: live_candles.pop()
    except Exception as e:
        print(f"Error: {e}")

def run_ws():
    # এখানে আপনার সংগৃহীত কোট্যাক্স টোকেনটি বসাতে হবে (Headers-এ)
    ws_url = "wss://ws.qxbroker.com/socket.io/?EIO=3&transport=websocket"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message)
    ws.run_forever()

@app.route('/Qx/Qx.php')
def get_api():
    return jsonify({
        **OWNER_INFO,
        "success": True,
        "count": len(live_candles),
        "data": live_candles
    })

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে ডাটা কালেকশন শুরু
    threading.Thread(target=run_ws, daemon=True).start()
    # Render-এর জন্য পোর্ট সেটআপ
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
