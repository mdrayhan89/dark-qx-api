import os
import json
import threading
import websocket
from flask import Flask, jsonify, request
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
    # ব্রোকারের মেসেজ ৪২ দিয়ে শুরু হলে তা ডাটা হিসেবে গণ্য হয়
    if message.startswith('42'):
        try:
            # এখানে ব্রোকার থেকে আসা লাইভ ডাটা হ্যান্ডেল করার লজিক
            # আপনার রিকোয়েস্ট অনুযায়ী স্যাম্পল ডাটা ফরম্যাট রাখা হলো
            now = datetime.now()
            candle = {
                "id": str(len(live_candles) + 1),
                "pair": "USDBDT_otc",
                "timeframe": "M1",
                "candle_time": now.strftime("%Y-%m-%d %H:%M:00"),
                "open": "128.223", 
                "high": "128.237",
                "low": "128.217",
                "close": "128.233",
                "volume": "48",
                "color": "green",
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            live_candles.insert(0, candle)
            
            # মেমোরি ফ্রি রাখতে সর্বোচ্চ ৫০০ ডাটা রাখা হবে
            if len(live_candles) > 500:
                live_candles.pop()
        except Exception as e:
            print(f"Data Processing Error: {e}")

def run_ws():
    # লেটেস্ট হোস্ট ইউআরএল
    ws_url = "wss://ws2.market-qx.trade/socket.io/?EIO=3&transport=websocket"
    
    # আপনার দেওয়া অরিজিনাল কুকি
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
        on_open=lambda ws: print("### Connection Established ###"),
        on_error=lambda ws, err: print(f"### Connection Error: {err} ###")
    )
    ws.run_forever()

@app.route('/Qx/Qx.php')
def get_api():
    # নির্দিষ্ট পেয়ার ফিল্টার করার অপশন (যেমন: ?pair=USDBDT_otc)
    target_pair = request.args.get('pair')
    if target_pair:
        filtered = [c for c in live_candles if c['pair'].lower() == target_pair.lower()]
        return jsonify({
            **OWNER_INFO,
            "success": True,
            "count": len(filtered),
            "data": filtered
        })
    
    # কোনো পেয়ার না দিলে সব ডাটা দেখাবে
    return jsonify({
        **OWNER_INFO,
        "success": True,
        "count": len(live_candles),
        "data": live_candles
    })

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে ডাটা কালেকশন শুরু
    threading.Thread(target=run_ws, daemon=True).start()
    
    # Render-এর জন্য ডাইনামিক পোর্ট
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
