
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

# Virtual portfolio only. No exchange account or trading API.
STARTING_CASH = 1000.0
STATE_FILE = Path("paper_state.json")
COINS = {"bitcoin": "BTC", "ethereum": "ETH"}

def get_prices():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum&vs_currencies=usd"
    )
    request = Request(url, headers={"User-Agent": "CryptoPaperBot/1.0"})
    with urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    return {coin: float(data[coin]["usd"]) for coin in COINS}

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "cash": STARTING_CASH,
        "coins": {"bitcoin": 0.0, "ethereum": 0.0},
        "last_prices": {},
        "trades": [],
        "starting_value": STARTING_CASH,
    }

def run():
    state = load_state()
    prices = get_prices()
    now = datetime.now(timezone.utc).isoformat()

    # Simple demonstration strategy:
    # Buy a small virtual amount after a 1% price drop from the last check.
    # Sell a small holding after a 1% rise from the last check.
    # This is a toy strategy, not a validated profitable AI.
    for coin, symbol in COINS.items():
        price = prices[coin]
        previous = state["last_prices"].get(coin)
        action = "HOLD"

        if previous:
            change = (price - previous) / previous
            if change <= -0.01 and state["cash"] >= 50:
                amount_usd = 50.0
                state["coins"][coin] += amount_usd / price
                state["cash"] -= amount_usd
                action = "PAPER BUY $50"
            elif change >= 0.01 and state["coins"][coin] * price >= 50:
                amount_usd = min(50.0, state["coins"][coin] * price)
                state["coins"][coin] -= amount_usd / price
                state["cash"] += amount_usd
                action = f"PAPER SELL ${amount_usd:.2f}"

        state["last_prices"][coin] = price
        state["trades"].append({
            "time": now, "coin": symbol, "price_usd": price,
            "action": action
        })
        print(f"{symbol}: ${price:,.2f} | {action}")

    holdings = sum(
        state["coins"][coin] * prices[coin] for coin in COINS
    )
    total = state["cash"] + holdings
    state["last_run"] = now
    state["last_total_usd"] = round(total, 2)
    state["trades"] = state["trades"][-500:]
    STATE_FILE.write_text(json.dumps(state, indent=2))

    print(f"Virtual cash: ${state['cash']:.2f}")
    print(f"Holdings:     ${holdings:.2f}")
    print(f"Total value:  ${total:.2f}")
    print(f"P/L:          ${total - STARTING_CASH:+.2f}")

if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"Run failed: {exc}")
        raise
