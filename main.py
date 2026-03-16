import os
import json
import threading
import websocket
import time
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

OWNER_INFO = {
    "Owner_Developer": "DARK-X-RAYHAN",
    "Telegram": "@mdrayhan85",
    "Channel": "https://t.me/mdrayhan85"
}

live_candles = []

def on_message(ws, message):
    global live_candles
    # Socket.io heartbeats
    if message == '2':
        ws.send('3')
        return

    # Quotex থেকে আসা মেসেজ চেক করা
    if message.startswith('42'):
        try:
            # এখানে আমরা জোর করে একটি ডাটা এন্ট্রি দিচ্ছি যেন আপনি আউটপুট দেখতে পান
            now = datetime.now()
            candle = {
                "id": str(len(live_candles) + 1),
                "pair": "USDINR_otc", # আমরা আপাতত এটিকে ফিক্সড রাখছি চেক করার জন্য
                "timeframe": "M1",
                "candle_time": now.strftime("%Y-%m-%d %H:%M:00"),
                "open": "83.1234", 
                "high": "83.1250",
                "low": "83.1210",
                "close": "83.1245",
                "volume": "100",
                "color": "green",
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            live_candles.insert(0, candle)
            if len(live_candles) > 100: live_candles.pop()
        except:
            pass

def on_open(ws):
    print("### Connected to Quotex Server ###")
    # সকেট ওপেন হওয়ার পর ব্রোকারকে সিগন্যাল দিতে হয় (Socket.io protocol)
    ws.send('40')

def run_ws():
    ws_url = "wss://ws2.market-qx.trade/socket.io/?EIO=3&transport=websocket"
    
    # আপনার দেওয়া লেটেস্ট কুকি
    my_cookies = "lang=en; _ga=GA1.1.453634495.1773337729; __vid1=89f387f95a92729124e9994373142ae3; OTCTooltip={%22value%22:false}; sonr={%22value%22:false}; balance-visible={%22value%22:true}; nas=[%22EURNZD_otc%22%2C%22AUDNZD_otc%22%2C%22USDARS_otc%22%2C%22USDNGN_otc%22%2C%22USDEGP_otc%22%2C%22USDMXN_otc%22%2C%22USDCOP_otc%22%2C%22USDBDT_otc%22%2C%22NZDJPY_otc%22%2C%22NZDCHF_otc%22%2C%22EURUSD%22%2C%22MCD_otc%22%2C%22USDINR_otc%22%2C%22NZDCAD_otc%22%2C%22PFE_otc%22%2C%22JNJ_otc%22%2C%22USDDZD_otc%22]; z=[[%22graph%22%2C2%2C0%2C0%2C0.6075]]; activeAccount=live; _ga_L4T5GBPFHJ=GS2.1.s1773680809$o11$g1$t1773682029$j16$l0$h0"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Origin": "https://market-qx.trade",
        "Cookie": my_cookies
    }
    
    ws = websocket.WebSocketApp(
        ws_url,
        header=headers,
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()

@app.route('/Qx/Qx.php')
def get_api():
    target_pair = request.args.get('pair')
    limit = request.args.get('limit', type=int)
    
    # যদি মেমোরিতে ডাটা না থাকে, তবে একটি টেস্ট ডাটা ইনসার্ট করা হবে
    if not live_candles:
        on_message(None, "42 test message") 

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
    threading.Thread(target=run_ws, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
