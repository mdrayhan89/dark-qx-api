import os
import json
import threading
import websocket
import time
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# ব্র্যান্ডিং তথ্য
OWNER_INFO = {
    "Owner_Developer": "DARK-X-RAYHAN",
    "Telegram": "@mdrayhan85",
    "Channel": "https://t.me/mdrayhan85"
}

# গ্লোবাল ডাটা স্টোরেজ
live_candles = []

def on_message(ws, message):
    global live_candles
    
    # Socket.io heartbeats (কানেকশন সচল রাখতে)
    if message == '2':
        ws.send('3')
        return

    # Quotex থেকে আসা ডাটা প্রসেস করা
    if message.startswith('42'):
        try:
            # সকেট মেসেজ থেকে JSON ডাটা আলাদা করা
            data_json = json.loads(message[2:])
            
            # যদি এটি ক্যান্ডেল ডাটা হয়
            if data_json[0] == 'candles':
                candles_list = data_json[1]
                for item in candles_list:
                    now = datetime.now()
                    candle = {
                        "id": str(len(live_candles) + 1),
                        "pair": "USDINR_otc",
                        "timeframe": "M1",
                        "candle_time": datetime.fromtimestamp(item.get('time', time.time())).strftime("%Y-%m-%d %H:%M:00"),
                        "open": str(item.get('open')), 
                        "high": str(item.get('high')),
                        "low": str(item.get('low')),
                        "close": str(item.get('close')),
                        "volume": str(item.get('volume', 0)),
                        "color": "green" if float(item.get('close', 0)) >= float(item.get('open', 0)) else "red",
                        "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    live_candles.insert(0, candle)
            
            # মেমোরি কন্ট্রোল (সর্বোচ্চ ৫০০ ডাটা রাখবে)
            if len(live_candles) > 500:
                live_candles = live_candles[:500]
                
        except Exception as e:
            # ডাটা প্রসেসিংয়ে ভুল হলে প্রিন্ট করবে
            print(f"Error parsing message: {e}")

def on_open(ws):
    print("### Connected to Quotex Server ###")
    # সকেট প্রোটোকল অনুযায়ী স্টার্ট সিগন্যাল
    ws.send('40')

def run_ws():
    ws_url = "wss://ws2.market-qx.trade/socket.io/?EIO=3&transport=websocket"
    
    # আপনার ভেরিফাইড কুকি
    my_cookies = "lang=en; _ga=GA1.1.453634495.1773337729; __vid1=89f387f95a92729124e9994373142ae3; OTCTooltip={%22value%22:false}; sonr={%22value%22:false}; balance-visible={%22value%22:true}; nas=[%22EURNZD_otc%22%2C%22AUDNZD_otc%22%2C%22USDARS_otc%22%2C%22USDNGN_otc%22%2C%22USDEGP_otc%22%2C%22USDMXN_otc%22%2C%22USDCOP_otc%22%2C%22USDBDT_otc%22%2C%22NZDJPY_otc%22%2C%22NZDCHF_otc%22%2C%22EURUSD%22%2C%22MCD_otc%22%2C%22USDINR_otc%22%2C%22NZDCAD_otc%22%2C%22PFE_otc%22%2C%22JNJ_otc%22%2C%22USDDZD_otc%22]; z=[[%22graph%22%2C2%2C0%2C0%2C0.6075]]; activeAccount=live; _ga_L4T5GBPFHJ=GS2.1.s1773680809$o11$g1$t1773682029$j16$l0$h0"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Origin": "https://market-qx.trade",
        "Cookie": my_cookies
    }
    
    while True: # ডিসকানেক্ট হলে অটোমেটিক রিকানেক্ট করার জন্য
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                header=headers,
                on_message=on_message,
                on_open=on_open
            )
            ws.run_forever()
        except:
            time.sleep(5)

@app.route('/Qx/Qx.php')
def get_api():
    target_pair = request.args.get('pair')
    limit = request.args.get('limit', type=int)
    
    # সকেট কানেক্ট হওয়ার আগ পর্যন্ত যদি ডাটা না থাকে, তবে একটি টেস্ট মেসেজ দেখাবে
    if not live_candles:
        test_now = datetime.now()
        test_candle = {
            "id": "0",
            "pair": "Waiting for Server...",
            "candle_time": test_now.strftime("%H:%M:%S"),
            "status": "Connecting to WebSocket"
        }
        return jsonify({**OWNER_INFO, "success": True, "count": 0, "data": [test_candle]})

    data_to_show = live_candles
    
    if target_pair:
        data_to_show = [c for c in live_candles if c['pair'].lower() == target_pair.lower()]
    
    if limit:
        data_to_show = data_to_show[:limit]
    
    return jsonify({
        **OWNER_INFO,
        "success": True,
        "count": len(data_to_show),
        "data": data_to_show
    })

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ড থ্রেডে সকেট চালানো
    threading.Thread(target=run_ws, daemon=True).start()
    
    # Render এর জন্য পোর্ট কনফিগারেশন
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
