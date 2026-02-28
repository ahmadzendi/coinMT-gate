import json
import time
from datetime import datetime, timezone, timedelta
import websocket
import threading
import urllib.request

def get_wib_time():
    wib = timezone(timedelta(hours=7))
    return datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S WIB')

def save_to_file(filename, content):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(content + '\n')

previous = {}

def check_maintenance_rest():
    url = "https://api.gateio.ws/api/v4/spot/currencies"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except:
        return None

def show_current_maintenance(currencies):
    wib_now = get_wib_time()
    
    print(f"\n🔴 CURRENT MAINTENANCE ({wib_now}):")
    print("="*70)
    
    save_to_file('maintenance_log.txt', f"\n{'='*70}")
    save_to_file('maintenance_log.txt', f"📅 {wib_now}")
    save_to_file('maintenance_log.txt', f"🔴 CURRENT MAINTENANCE:")
    save_to_file('maintenance_log.txt', f"{'='*70}")
    
    count = 0
    for coin in currencies:
        currency = coin.get('currency')
        chains = coin.get('chains', [])
        
        for chain in chains:
            chain_name = chain.get('name')
            withdraw_disabled = chain.get('withdraw_disabled', False)
            
            if withdraw_disabled:
                count += 1
                line = f"{count}. {currency} - {chain_name} | {wib_now}"
                print(line)
                save_to_file('maintenance_log.txt', line)
    
    print("="*70)
    print(f"Total: {count} chains in maintenance\n")
    
    save_to_file('maintenance_log.txt', f"{'='*70}")
    save_to_file('maintenance_log.txt', f"Total: {count} chains in maintenance\n")

def on_message(ws, message):
    global previous
    
    try:
        data = json.loads(message)
        
        if data.get('event') == 'update' and data.get('channel') == 'spot.currency_status':
            result = data.get('result', {})
            currency = result.get('currency', '')
            chains = result.get('chains', [])
            
            for chain in chains:
                chain_name = chain.get('name', '')
                withdraw_disabled = chain.get('withdraw_disabled', False)
                key = f"{currency}_{chain_name}"
                
                prev_status = previous.get(key, None)
                
                if prev_status == False and withdraw_disabled == True:
                    wib = get_wib_time()
                    msg = f"\n🟢 Masuk Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                elif prev_status == True and withdraw_disabled == False:
                    wib = get_wib_time()
                    msg = f"\n🔴 Keluar Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                previous[key] = withdraw_disabled
        
    except Exception as e:
        print(f"❌ Parse error: {e}")

def on_error(ws, error):
    print(f"❌ WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"\n⚠️ WebSocket closed: {close_status_code}")
    for i in range(3):
        print(f"🔄 Reconnecting... ({i+1}/3)")
        time.sleep(5)
        start_websocket()

def on_open(ws):
    print("✅ WebSocket connected!")
    
    subscribe_message = {
        "time": int(time.time()),
        "channel": "spot.currency_status",
        "event": "subscribe"
    }
    ws.send(json.dumps(subscribe_message))
    print("📡 Subscribed to currency status updates")

def start_websocket():
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://api.gateio.ws/ws/v4/",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    ws.run_forever()

def periodic_check():
    global previous
    check_count = 0
    
    while True:
        try:
            time.sleep(30)
            check_count += 1
            print(f"\r🔄 Periodic check #{check_count} | Tracking {len(previous)} chains", end="", flush=True)
        except:
            break

def main():
    global previous
    
    wib_now = get_wib_time()
    
    print("🤖 Gate.io Withdraw Maintenance Monitor (WebSocket Real-Time)")
    print(f"📅 Started: {wib_now}")
    print("="*70)
    
    save_to_file('maintenance_log.txt', f"\n{'='*70}")
    save_to_file('maintenance_log.txt', "🤖 Gate.io Withdraw Maintenance Monitor (WebSocket)")
    save_to_file('maintenance_log.txt', f"Started: {wib_now}")
    
    print("📡 Fetching initial data via REST API...")
    currencies = check_maintenance_rest()
    
    if not currencies:
        print("❌ Failed to fetch initial data.")
        return
    
    show_current_maintenance(currencies)
    
    for coin in currencies:
        currency = coin.get('currency')
        for chain in coin.get('chains', []):
            key = f"{currency}_{chain.get('name')}"
            previous[key] = chain.get('withdraw_disabled', False)
    
    print("👀 Starting WebSocket connection...")
    print("="*70)
    
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    periodic_thread = threading.Thread(target=periodic_check, daemon=True)
    periodic_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n👋 Stopped at {get_wib_time()}")
        save_to_file('maintenance_log.txt', f"\n👋 Stopped: {get_wib_time()}")

if __name__ == "__main__":
    main()
