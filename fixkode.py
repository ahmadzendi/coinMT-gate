import json
import time
from datetime import datetime, timezone, timedelta
import websocket
import threading
import urllib.request

# ==================== KONFIGURASI TELEGRAM ====================
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
# ==============================================================

def get_wib_time():
    wib = timezone(timedelta(hours=7))
    return datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S WIB')

def save_to_file(filename, content):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(content + '\n')

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return True
    except Exception as e:
        print(f"\n❌ Telegram error: {e}")
        return False

def send_telegram_to(chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return True
    except:
        return False

def send_long_message(chat_id, header, coins_list):
    wib = get_wib_time()
    
    if not coins_list:
        msg = f"{header}\n📅 {wib}\n\n✅ Tidak ada coin dalam maintenance"
        send_telegram_to(chat_id, msg)
        return
    
    chunk_size = 50
    total_coins = len(coins_list)
    total_pages = (total_coins + chunk_size - 1) // chunk_size
    
    # Kirim header di pesan pertama
    first_msg = f"{header}\n📅 {wib}\n📊 Total: {total_coins} chains\n\n"
    
    for i, (coin, coin_time) in enumerate(coins_list[:chunk_size], 1):
        first_msg += f"{i}. {coin} | {coin_time}\n"
    
    send_telegram_to(chat_id, first_msg)
    
    # Kirim sisa halaman tanpa header
    for page in range(1, total_pages):
        time.sleep(0.5)
        
        start = page * chunk_size
        end = min(start + chunk_size, total_coins)
        
        msg = ""
        for i, (coin, coin_time) in enumerate(coins_list[start:end], start + 1):
            msg += f"{i}. {coin} | {coin_time}\n"
        
        send_telegram_to(chat_id, msg)

def get_telegram_updates(offset=None):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=1"
        if offset:
            url += f"&offset={offset}"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            return data.get('result', [])
    except:
        return []

previous_withdraw = {}
previous_deposit = {}
withdraw_times = {}
deposit_times = {}
ws_connected = False
reconnect_count = 0

def check_maintenance_rest():
    url = "https://api.gateio.ws/api/v4/spot/currencies"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    for attempt in range(5):
        try:
            print(f"\r📡 Fetching data... (attempt {attempt+1}/5)", end="", flush=True)
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
                print("\r✅ Data received!                         ")
                return json.loads(data)
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
            return "exit"
        except Exception as e:
            print(f"\r⚠️ Attempt {attempt+1} failed: {str(e)[:40]}")
            if attempt < 4:
                print(f"🔄 Retrying in 3 seconds...")
                time.sleep(3)
    
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
                key = f"{currency}_{chain_name}"
                withdraw_times[key] = wib_now
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
                key = f"{currency}_{chain_name}"
                deposit_times[key] = wib_now
                line = f"{deposit_count}. {currency} - {chain_name} | {wib_now}"
                print(line)
                save_to_file('maintenance_log.txt', line)
    
    print(f"\nTotal: {deposit_count} chains")
    print("="*70)
    save_to_file('maintenance_log.txt', f"\nTotal: {deposit_count} chains")
    save_to_file('maintenance_log.txt', f"{'='*70}\n")

def get_withdraw_list():
    coins = []
    
    for key, disabled in previous_withdraw.items():
        if disabled:
            currency, chain = key.rsplit('_', 1)
            coin_time = withdraw_times.get(key, "Unknown")
            coins.append((f"{currency} - {chain}", coin_time))
    
    return coins

def get_deposit_list():
    coins = []
    
    for key, disabled in previous_deposit.items():
        if disabled:
            currency, chain = key.rsplit('_', 1)
            coin_time = deposit_times.get(key, "Unknown")
            coins.append((f"{currency} - {chain}", coin_time))
    
    return coins

def telegram_handler():
    print("📱 Telegram handler started")
    last_update_id = None
    
    while True:
        try:
            updates = get_telegram_updates(last_update_id)
            
            for update in updates:
                last_update_id = update['update_id'] + 1
                
                message = update.get('message', {})
                text = message.get('text', '')
                chat_id = message.get('chat', {}).get('id')
                
                if not text or not chat_id:
                    continue
                
                if text == '/start':
                    reply = "🤖 <b>Gate.io Maintenance Bot</b>\n\n"
                    reply += "📋 <b>Commands:</b>\n"
                    reply += "/withdraw - List withdraw maintenance\n"
                    reply += "/deposit - List deposit maintenance\n"
                    reply += "/status - Bot status"
                    send_telegram_to(chat_id, reply)
                
                elif text == '/withdraw':
                    coins = get_withdraw_list()
                    send_long_message(chat_id, "📤 <b>WITHDRAW MAINTENANCE</b>", coins)
                
                elif text == '/deposit':
                    coins = get_deposit_list()
                    send_long_message(chat_id, "📥 <b>DEPOSIT MAINTENANCE</b>", coins)
                
                elif text == '/status':
                    wib = get_wib_time()
                    status = "🟢 Connected" if ws_connected else "🔴 Disconnected"
                    
                    withdraw_count = sum(1 for v in previous_withdraw.values() if v)
                    deposit_count = sum(1 for v in previous_deposit.values() if v)
                    
                    reply = f"📊 <b>BOT STATUS</b>\n\n"
                    reply += f"📅 Time: {wib}\n"
                    reply += f"🔌 WebSocket: {status}\n"
                    reply += f"🔄 Reconnects: {reconnect_count}\n"
                    reply += f"📤 Withdraw Disabled: {withdraw_count} chains\n"
                    reply += f"📥 Deposit Disabled: {deposit_count} chains\n"
                    reply += f"📊 Total Tracking: {len(previous_withdraw)} chains"
                    send_telegram_to(chat_id, reply)
            
            time.sleep(1)
            
        except Exception as e:
            time.sleep(3)

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
                    withdraw_times[key] = wib
                    msg = f"\n🟢 Masuk Withdraw Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                    
                    tg_msg = f"🟢 <b>Masuk Withdraw Maintenance</b>\n\n"
                    tg_msg += f"💰 Coin  : <b>{currency}</b>\n"
                    tg_msg += f"🔗 Chain : <b>{chain_name}</b>\n"
                    tg_msg += f"📅 Time  : {wib}"
                    send_telegram(tg_msg)
                
                elif prev_withdraw == True and withdraw_disabled == False:
                    if key in withdraw_times:
                        del withdraw_times[key]
                    msg = f"\n🔴 Keluar Withdraw Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                    
                    tg_msg = f"🔴 <b>Keluar Withdraw Maintenance</b>\n\n"
                    tg_msg += f"💰 Coin  : <b>{currency}</b>\n"
                    tg_msg += f"🔗 Chain : <b>{chain_name}</b>\n"
                    tg_msg += f"📅 Time  : {wib}"
                    send_telegram(tg_msg)
                
                elif prev_withdraw is None and withdraw_disabled == True:
                    withdraw_times[key] = wib
                    msg = f"\n🟢 Masuk Withdraw Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                    
                    tg_msg = f"🟢 <b>Masuk Withdraw Maintenance</b>\n\n"
                    tg_msg += f"💰 Coin  : <b>{currency}</b>\n"
                    tg_msg += f"🔗 Chain : <b>{chain_name}</b>\n"
                    tg_msg += f"📅 Time  : {wib}"
                    send_telegram(tg_msg)
                
                if prev_deposit == False and deposit_disabled == True:
                    deposit_times[key] = wib
                    msg = f"\n🟢 Masuk Deposit Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                    
                    tg_msg = f"🟢 <b>Masuk Deposit Maintenance</b>\n\n"
                    tg_msg += f"💰 Coin  : <b>{currency}</b>\n"
                    tg_msg += f"🔗 Chain : <b>{chain_name}</b>\n"
                    tg_msg += f"📅 Time  : {wib}"
                    send_telegram(tg_msg)
                
                elif prev_deposit == True and deposit_disabled == False:
                    if key in deposit_times:
                        del deposit_times[key]
                    msg = f"\n🔴 Keluar Deposit Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                    
                    tg_msg = f"🔴 <b>Keluar Deposit Maintenance</b>\n\n"
                    tg_msg += f"💰 Coin  : <b>{currency}</b>\n"
                    tg_msg += f"🔗 Chain : <b>{chain_name}</b>\n"
                    tg_msg += f"📅 Time  : {wib}"
                    send_telegram(tg_msg)
                
                elif prev_deposit is None and deposit_disabled == True:
                    deposit_times[key] = wib
                    msg = f"\n🟢 Masuk Deposit Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                    print(msg)
                    save_to_file('maintenance_log.txt', msg)
                    save_to_file('changes_log.txt', msg)
                    
                    tg_msg = f"🟢 <b>Masuk Deposit Maintenance</b>\n\n"
                    tg_msg += f"💰 Coin  : <b>{currency}</b>\n"
                    tg_msg += f"🔗 Chain : <b>{chain_name}</b>\n"
                    tg_msg += f"📅 Time  : {wib}"
                    send_telegram(tg_msg)
                
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
    
    currencies = check_maintenance_rest()
    
    if currencies == "exit":
        return
    
    while not currencies:
        print("❌ Failed to fetch data. Retrying in 5 seconds...")
        try:
            time.sleep(5)
            currencies = check_maintenance_rest()
            if currencies == "exit":
                return
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
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
    
    tg_thread = threading.Thread(target=telegram_handler, daemon=True)
    tg_thread.start()
    
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    periodic_thread = threading.Thread(target=periodic_check, daemon=True)
    periodic_thread.start()
    
    startup_msg = f"🤖 <b>Bot Started</b>\n\n"
    startup_msg += f"📅 {wib_now}\n"
    startup_msg += f"📤 Withdraw Tracking: {len(previous_withdraw)} chains\n"
    startup_msg += f"📥 Deposit Tracking: {len(previous_deposit)} chains"
    send_telegram(startup_msg)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wib = get_wib_time()
        print(f"\n\n👋 Stopped at {wib}")
        save_to_file('maintenance_log.txt', f"\n👋 Stopped: {wib}")
        send_telegram(f"🛑 <b>Bot Stopped</b>\n\n📅 {wib}")

if __name__ == "__main__":
    main()
