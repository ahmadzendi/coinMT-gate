import urllib.request
import json
import time
from datetime import datetime, timezone, timedelta

def get_wib_time():
    wib = timezone(timedelta(hours=7))
    return datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S WIB')

def check_maintenance():
    url = "https://api.gateio.ws/api/v4/spot/currencies"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except:
        return None

def save_to_file(filename, content):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(content + '\n')

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

def main():
    wib_now = get_wib_time()
    
    print("🤖 Gate.io Withdraw Maintenance Monitor")
    print(f"📅 Started: {wib_now}")
    print("="*70)
    
    save_to_file('maintenance_log.txt', f"\n{'='*70}")
    save_to_file('maintenance_log.txt', "🤖 Gate.io Withdraw Maintenance Monitor")
    save_to_file('maintenance_log.txt', f"Started: {wib_now}")
    
    print("📡 Fetching initial data...")
    currencies = check_maintenance()
    
    if not currencies:
        print("❌ Failed to fetch data.")
        return
    
    show_current_maintenance(currencies)
    
    print("👀 Monitoring...")
    print("="*70)
    
    previous = {}
    for coin in currencies:
        currency = coin.get('currency')
        for chain in coin.get('chains', []):
            key = f"{currency}_{chain.get('name')}"
            previous[key] = chain.get('withdraw_disabled', False)
    
    check_count = 0
    
    while True:
        try:
            currencies = check_maintenance()
            
            if not currencies:
                time.sleep(0.1)
                continue
            
            current = {}
            
            for coin in currencies:
                currency = coin.get('currency')
                chains = coin.get('chains', [])
                
                for chain in chains:
                    chain_name = chain.get('name')
                    withdraw_disabled = chain.get('withdraw_disabled', False)
                    key = f"{currency}_{chain_name}"
                    current[key] = withdraw_disabled
                    
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
                    
                    elif prev_status is None and withdraw_disabled == True:
                        wib = get_wib_time()
                        msg = f"\n🟢 Masuk Maintenance\n   Coin  : {currency}\n   Chain : {chain_name}\n   Time  : {wib}"
                        print(msg)
                        save_to_file('maintenance_log.txt', msg)
                        save_to_file('changes_log.txt', msg)
            
            previous = current
            check_count += 1
            print(f"\r⚡ {get_wib_time()} | Check #{check_count} | {len(current)} chains", end="", flush=True)
            
            time.sleep(0.01)
            
        except KeyboardInterrupt:
            print(f"\n\n👋 Stopped at {get_wib_time()}")
            save_to_file('maintenance_log.txt', f"\n👋 Stopped: {get_wib_time()}")
            break
        except Exception as e:
            print(f"\n❌ {e}")
            time.sleep(0.1)

if __name__ == "__main__":
    main()
