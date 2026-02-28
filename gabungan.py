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

previous_withdraw = {}
previous_deposit = {}
ws_connected = False
reconnect_count = 0

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
    
    withdraw_count = 0
    deposit_count = 0
    
    print("\n📤 WITHDRAW DISABLED:")
    print("-"*70)
    save_to_file('maintenance_log.txt', "\n📤 WITHDRAW DISABLED:")
    save_to_file('maintenance_log.txt', "-"*70)
    
    for coin in currencies:
        currency = coin.get('currency')
        chains = coin.get('chains', [])
        
        for chain in chains:
            chain_name = chain.get('name')
            withdraw_disabled = chain.get('withdraw_disabled', False)
            
            if withdraw_disabled:
                withdraw_count += 1
                line = f"{withdraw_count}. {currency} - {chain_name} | {wib_now}"
                print(line)
                save_to_file('maintenance_log.txt', line)
    
    print(f"\nTotal: {withdraw_count} chains")
    save_to_file('maintenance_log.txt', f"\nTotal: {withdraw_count} chains")
    
    print("\n📥 DEPOSIT DISABLED:")
    print("-"*70)
    save_to_file('maintenance_log.txt', "\n📥 DEPOSIT DISABLED:")
    save_to_file('maintenance_log.txt', "-"*70)
    
    for coin in currencies:
        currency = coin.get('currency')
        chains = coin.get('chains', [])
        
        for chain in chains:
            chain_name = chain.get('name')
            deposit_disabled = chain.get('deposit_disabled', False)
            
            if deposit_disabled:
                deposit_count += 1
                line = f"{deposit_count}. {currency} - {chain_name} | {wib_now}"
                print(line)
                save_to_file('maintenance_log.txt', line)
    
    print(f"\nTotal: {deposit_count} chains")
    print("="*70)
    save_to_file('maintenance_log.txt', f"\nTotal: {deposit_count} chains")
    save_to_file('maintenance_log.txt', f"{'='*70}\n")

def on_message(ws, message):
    global previous_withdraw, previous_deposit
    
    try:
        data = json.loads(message)
        
        if data.get('event') == 'update' and data.get('channel') == 'spot.currency_status':
            result = data.get('result', {})
            currency = result.get('currency', '')
            chains = result.get('chains', [])
            
            for chain in chains:
                chain_name = chain.get('name', '')
                withdraw_disabled = chain.get('withdraw_disabled', False)
                deposit_disabled = chain.get('deposit_disabled', False)
                key = f"{currency}_{chain_name}"
                
                prev_withdraw = previous_withdraw.get(key, None)
                prev_deposit = previous_deposit.get(key, None)
                wib = get_wib_time()
                
                if prev_withdraw == False and withdraw_disabled == True:
                    msg = f"\n🟢 Masuk Withdraw Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                elif prev_withdraw == True and withdraw_disabled == False:
                    msg = f"\n🔴 Keluar Withdraw Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                elif prev_withdraw is None and withdraw_disabled == True:
                    msg = f"\n🟢 Masuk Withdraw Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                if prev_deposit == False and deposit_disabled == True:
                    msg = f"\n🟢 Masuk Deposit Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                elif prev_deposit == True and deposit_disabled == False:
                    msg = f"\n🔴 Keluar Deposit Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                elif prev_deposit is None and deposit_disabled == True:
                    msg = f"\n🟢 Masuk Deposit Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                
                previous_withdraw[key] = withdraw_disabled
                previous_deposit[key] = deposit_disabled
        
    except Exception as e:
        print(f"\n❌ Parse error: {e}")

def on_error(ws, error):
    print(f"\n❌ WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    global ws_connected, reconnect_count
    ws_connected = False
    reconnect_count += 1
    print(f"\n⚠️ WebSocket disconnected (reconnect #{reconnect_count})")

def on_open(ws):
    global ws_connected, reconnect_count
    ws_connected = True
    
    if reconnect_count > 0:
        print(f"✅ Reconnected successfully!")
    else:
        print("✅ WebSocket connected!")
    
    subscribe_message = {
        "time": int(time.time()),
        "channel": "spot.currency_status",
        "event": "subscribe"
    }
    ws.send(json.dumps(subscribe_message))
    print("📡 Subscribed to currency status updates (WITHDRAW & DEPOSIT)")

def start_websocket():
    while True:
        try:
            websocket.enableTrace(False)
            ws = websocket.WebSocketApp(
                "wss://api.gateio.ws/ws/v4/",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            ws.run_forever(ping_interval=20, ping_timeout=10)
            
        except Exception as e:
            print(f"\n❌ WebSocket exception: {e}")
        
        print("🔄 Reconnecting in 5 seconds...")
        time.sleep(5)

def periodic_check():
    global previous_withdraw, previous_deposit, ws_connected
    check_count = 0
    
    while True:
        try:
            time.sleep(30)
            check_count += 1
            
            wib = get_wib_time()
            status = "🟢 Connected" if ws_connected else "🔴 Disconnected"
            total = len(previous_withdraw)
            print(f"\r🔄 {wib} | Check #{check_count} | {status} | Tracking {total} chains", end="", flush=True)
            
        except:
            break

def main():
    global previous_withdraw, previous_deposit
    
    wib_now = get_wib_time()
    
    print("🤖 Gate.io Maintenance Monitor (WITHDRAW & DEPOSIT)")
    print(f"📅 Started: {wib_now}")
    print("="*70)
    
    save_to_file('maintenance_log.txt', f"\n{'='*70}")
    save_to_file('maintenance_log.txt', "🤖 Gate.io Maintenance Monitor (WITHDRAW & DEPOSIT)")
    save_to_file('maintenance_log.txt', f"📅 Started: {wib_now}")
    save_to_file('maintenance_log.txt', f"{'='*70}")
    
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
            previous_withdraw[key] = chain.get('withdraw_disabled', False)
            previous_deposit[key] = chain.get('deposit_disabled', False)
    
    print("\n👀 Starting WebSocket connection...")
    print("="*70)
    
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    periodic_thread = threading.Thread(target=periodic_check, daemon=True)
    periodic_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wib = get_wib_time()
        print(f"\n\n👋 Stopped at {wib}")
        save_to_file('maintenance_log.txt', f"\n👋 Stopped: {wib}")

if __name__ == "__main__":
    main()
