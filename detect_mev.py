import requests
import psycopg2
import os
import time
from dotenv import load_dotenv

load_dotenv()

ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"

# Known DEX router addresses only — real sandwiches happen on DEXes
DEX_ROUTERS = {
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap V2
    "0xe592427a0aece92de3edee1f18e0157c05861564",  # Uniswap V3
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f",  # Sushiswap
    "0x1111111254eeb25477b68fb85ed929f73a960582",  # 1inch V5
    "0x881d40237659c251811cec9c364ef91dc08d300c",  # Metamask swap
}

def rpc(method, params):
    r = requests.post(ALCHEMY_URL, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    })
    return r.json().get('result')

def get_latest_block():
    return int(rpc("eth_blockNumber", []), 16)

def get_block_transactions(block_number):
    block = rpc("eth_getBlockByNumber", [hex(block_number), True])
    if not block:
        return [], 0
    return block.get('transactions', []), int(block.get('timestamp', '0x0'), 16)

def get_db():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=os.getenv("SUPABASE_PORT"),
        dbname=os.getenv("SUPABASE_DB"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD")
    )

def detect_sandwiches(transactions):
    sandwiches = []

    # Only keep DEX transactions
    dex_txs = []
    for i, tx in enumerate(transactions):
        to = (tx.get('to') or '').lower()
        if to in DEX_ROUTERS:
            dex_txs.append((i, tx))

    if len(dex_txs) < 3:
        return sandwiches

    # Group by sender
    sender_map = {}
    for pos, tx in dex_txs:
        sender = (tx.get('from') or '').lower()
        if sender not in sender_map:
            sender_map[sender] = []
        sender_map[sender].append((pos, tx))

    # Find sandwich patterns
    for sender, tx_list in sender_map.items():
        if len(tx_list) < 2:
            continue

        for a in range(len(tx_list)):
            for b in range(a + 1, len(tx_list)):
                pos_i, frontrun = tx_list[a]
                pos_k, backrun = tx_list[b]

                # Must be within 5 positions of each other
                if pos_k - pos_i > 10 or pos_k - pos_i < 2:
                    continue

                frontrun_to = (frontrun.get('to') or '').lower()
                backrun_to = (backrun.get('to') or '').lower()

                if frontrun_to != backrun_to:
                    continue

                frontrun_gas = int(frontrun.get('gasPrice') or '0x0', 16)
                backrun_gas = int(backrun.get('gasPrice') or '0x0', 16)

                # Look for victim between them
                for j in range(pos_i + 1, pos_k):
                    victim = transactions[j]
                    victim_sender = (victim.get('from') or '').lower()
                    victim_to = (victim.get('to') or '').lower()
                    victim_gas = int(victim.get('gasPrice') or '0x0', 16)

                    if victim_to != frontrun_to:
                        continue
                    if victim_sender == sender:
                        continue

                    # Key check: frontrun gas > victim gas (bot jumped ahead)
                    if frontrun_gas <= victim_gas:
                        continue

                    # Key check: backrun gas <= victim gas (bot followed behind)
                    if backrun_gas > victim_gas:
                        continue

                    sandwiches.append({
                        'frontrun_tx': frontrun.get('hash'),
                        'victim_tx': victim.get('hash'),
                        'backrun_tx': backrun.get('hash'),
                        'bot_address': sender,
                        'victim_address': victim_sender,
                        'token_address': frontrun_to,
                        'extracted_eth': (frontrun_gas - backrun_gas) / 1e18,
                    })

    return sandwiches

def save_sandwiches(sandwiches, block_number, block_timestamp):
    if not sandwiches:
        return 0

    conn = get_db()
    cursor = conn.cursor()
    saved = 0

    for s in sandwiches:
        try:
            cursor.execute("""
                INSERT INTO mev_sandwiches
                (block_number, block_timestamp, frontrun_tx, victim_tx, backrun_tx,
                 bot_address, victim_address, token_address, extracted_eth)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                block_number, block_timestamp,
                s['frontrun_tx'], s['victim_tx'], s['backrun_tx'],
                s['bot_address'], s['victim_address'],
                s['token_address'], s['extracted_eth']
            ))
            if cursor.rowcount == 1:
                saved += 1
        except Exception as e:
            print(f"Error saving: {e}")

    conn.commit()
    conn.close()
    return saved

print("MEV Sandwich Detector started")
last_block = get_latest_block() - 1

while True:
    try:
        latest = get_latest_block()

        for block_num in range(last_block, min(latest + 1, last_block + 3)):
            print(f"Scanning block {block_num}...")
            txs, timestamp = get_block_transactions(block_num)
            print(f"  {len(txs)} transactions found")

            if txs:
                sandwiches = detect_sandwiches(txs)
                print(f"  {len(sandwiches)} sandwich patterns detected")

                if sandwiches:
                    saved = save_sandwiches(sandwiches, block_num, timestamp)
                    print(f"  {saved} new sandwiches saved")

        last_block = min(latest + 1, last_block + 3)
        print("Waiting 30 seconds...")
        time.sleep(30)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)