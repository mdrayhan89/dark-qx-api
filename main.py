import os
import json
import threading
import websocket
import time
from flask import Flask, jsonify, request
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# আপনার ইমেইল ও পাসওয়ার্ড এখানে সেট করবেন
EMAIL = os.environ.get("EMAIL", "trrayhan786@gmail.com")
PASSWORD = os.environ.get("PASSWORD", "Mdrayhan@655")

OWNER_INFO = {
    "Owner_Developer": "DARK-X-RAYHAN",
    "Telegram": "@mdrayhan85",
    "Channel": "https://t.me/mdrayhan85"
}

live_candles = []
current_cookies = ""

def get_cookies():
    global current_cookies
    print("### Selenium লগইন শুরু হচ্ছে... ###")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://qxbroker.com/en/sign-in")
        time.sleep(5)
        
        driver.find_element("name", "email").send_keys(EMAIL)
        driver.find_element("name", "password").send_keys(PASSWORD)
        driver.find_element("xpath", "//button[@type='submit']").click()
        
        time.sleep(10)
        cookies = driver.get_cookies()
        current_cookies = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        driver.quit()
        print("### সেশন সাকসেসফুল! ###")
    except Exception as e:
        print(f"Login Error: {e}")

def on_message(ws, message):
    global live_candles
    if message == '2': ws.send('3') # Heartbeat
    if message.startswith('42'):
        try:
            res = json.loads(message[2:])
            if res[0] == 'candles':
                for item in res[1]:
                    # আপনার চাওয়া বিস্তারিত আউটপুট ফরম্যাট
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
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    live_candles.insert(0, candle)
            if len(live_candles) > 100: live_candles = live_candles[:100]
        except: pass

def run_ws():
    global current_cookies
    while True:
        if not current_cookies: get_cookies()
        try:
            ws_url = "wss://ws2.market-qx.trade/socket.io/?EIO=3&transport=websocket"
            ws = websocket.WebSocketApp(
                ws_url,
                header={"Cookie": current_cookies, "Origin": "https://market-qx.trade"},
                on_message=on_message,
                on_open=lambda ws: ws.send('42["subscribe_symbol",{"name":"USDINR_otc","period":60}]')
            )
            ws.run_forever()
        except:
            current_cookies = "" # পুনরায় লগইন করার জন্য কুকি ক্লিয়ার করা
            time.sleep(5)

@app.route('/Qx/Qx.php')
def get_api():
    limit = request.args.get('limit', type=int, default=10)
    if not live_candles:
        return jsonify({**OWNER_INFO, "success": True, "status": "Connecting to WebSocket..."})
    return jsonify({**OWNER_INFO, "success": True, "count": len(live_candles[:limit]), "data": live_candles[:limit]})

if __name__ == "__main__":
    threading.Thread(target=run_ws, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
