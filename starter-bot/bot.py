#!/usr/bin/env python3
"""Starter bot from Yes or No Lab (Coding Friend LLC).

A teaching bot for spot bitcoin. It reads config.toml, pulls public prices from Kraken (no account, no key),
and either replays recent history ("backtest") or watches the live price and pretends to trade ("paper").

IT DOES NOT PLACE REAL ORDERS. There is no code in this file that can.

NO WARRANTY. This software is provided "as is" for education only. It is not financial advice. Trading can lose
money, including all of it. You alone are responsible for what you do with this code. See LICENSE and README.
"""
import csv, json, sys, time, tomllib, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
CFG = tomllib.loads((HERE / "config.toml").read_text())


# ---------- prices ----------
def candles(pair, minutes):
    """Up to 720 most recent bars from Kraken's public API: (time, open, high, low, close)."""
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={minutes}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "yesornolab-starter-bot"}), timeout=30) as r:
        data = json.load(r)
    if data.get("error"):
        sys.exit(f"Kraken refused the request: {data['error']}. Check [market] pair and candle_minutes in config.toml.")
    rows = next(v for k, v in data["result"].items() if k != "last")
    return [(int(t), float(o), float(h), float(l), float(c)) for t, o, h, l, c, *_ in rows[:-1]]   # drop the unfinished bar


# ---------- indicators (plain Python so you can read them) ----------
def average(xs):
    return sum(xs) / len(xs)

def rsi(closes, n):
    gains = [max(b - a, 0) for a, b in zip(closes[-n - 1:], closes[-n:])]
    losses = [max(a - b, 0) for a, b in zip(closes[-n - 1:], closes[-n:])]
    if sum(losses) == 0:
        return 100.0
    return 100 - 100 / (1 + sum(gains) / sum(losses))


# ---------- strategies: each answers "buy", "sell" or "wait" using only bars it has already seen ----------
def decide(bars, holding):
    name = CFG["strategy"]["use"]; p = CFG["strategy"][name]
    closes = [b[4] for b in bars]; price = closes[-1]
    if name == "momentum":
        if len(closes) <= p["lookback_bars"]: return "wait"
        change = (price / closes[-1 - p["lookback_bars"]] - 1) * 100
        if not holding and change >= p["buy_when_up_percent"]: return "buy"
        if holding and change <= -p["sell_when_down_percent"]: return "sell"
    elif name == "ma_cross":
        if len(closes) <= p["slow_bars"]: return "wait"
        fast, slow = average(closes[-p["fast_bars"]:]), average(closes[-p["slow_bars"]:])
        if not holding and fast > slow: return "buy"
        if holding and fast < slow: return "sell"
    elif name == "rsi_dip":
        if len(closes) <= p["rsi_bars"]: return "wait"
        r = rsi(closes, p["rsi_bars"])
        if not holding and r < p["buy_below"]: return "buy"
        if holding and r > p["sell_above"]: return "sell"
    elif name == "breakout":
        need = max(p["high_bars"], p["exit_low_bars"])
        if len(bars) <= need: return "wait"
        if not holding and price > max(b[2] for b in bars[-1 - p["high_bars"]:-1]): return "buy"
        if holding and price < min(b[3] for b in bars[-1 - p["exit_low_bars"]:-1]): return "sell"
    else:
        sys.exit(f"config.toml says [strategy] use = \"{name}\". Pick one of: momentum, ma_cross, rsi_dip, breakout.")
    return "wait"


# ---------- the pretend account ----------
class Account:
    def __init__(self):
        a = CFG["account"]
        self.cash, self.coins, self.entry, self.fee = float(a["starting_cash"]), 0.0, 0.0, a["fee_percent"] / 100
        self.fees_paid, self.trades, self.day_count = 0.0, [], {}

    def value(self, price):
        return self.cash + self.coins * price

    def buy(self, t, price, why):
        day = time.strftime("%Y-%m-%d", time.gmtime(t))
        if self.day_count.get(day, 0) >= CFG["safety"]["max_trades_per_day"]: return
        spend = self.cash * CFG["account"]["trade_percent"] / 100
        if spend < 1: return
        fee = spend * self.fee
        self.coins += (spend - fee) / price; self.cash -= spend; self.fees_paid += fee; self.entry = price
        self.day_count[day] = self.day_count.get(day, 0) + 1
        self.trades.append(dict(time=t, side="buy", price=price, why=why, value=round(self.value(price), 2)))

    def sell(self, t, price, why):
        if self.coins <= 0: return
        gross = self.coins * price; fee = gross * self.fee
        self.cash += gross - fee; self.fees_paid += fee; self.coins = 0.0
        self.trades.append(dict(time=t, side="sell", price=price, why=why, value=round(self.cash, 2),
                                result_percent=round((price * (1 - self.fee) / (self.entry / (1 - self.fee)) - 1) * 100, 2)))


def step(acct, bars):
    """One bar of thinking: safety rules first, then the strategy."""
    t, price = bars[-1][0], bars[-1][4]; s = CFG["safety"]
    if acct.coins > 0:
        move = (price / acct.entry - 1) * 100
        if s["stop_loss_percent"] and move <= -s["stop_loss_percent"]: return acct.sell(t, price, "stop loss")
        if s["take_profit_percent"] and move >= s["take_profit_percent"]: return acct.sell(t, price, "take profit")
    action = decide(bars, acct.coins > 0)
    if action == "buy": acct.buy(t, price, CFG["strategy"]["use"])
    if action == "sell": acct.sell(t, price, CFG["strategy"]["use"])


def report(acct, bars, start_index):
    first, last = bars[start_index][4], bars[-1][4]; start = CFG["account"]["starting_cash"]
    end = acct.value(last); sells = [x for x in acct.trades if x["side"] == "sell"]; wins = [x for x in sells if x["result_percent"] > 0]
    peak, worst = start, 0.0
    for x in acct.trades:
        peak = max(peak, x["value"]); worst = min(worst, x["value"] / peak - 1)
    days = (bars[-1][0] - bars[start_index][0]) / 86400
    lines = [
        f"Strategy: {CFG['strategy']['use']}   Market: {CFG['market']['pair']}   Bars: {CFG['market']['candle_minutes']} min   Period: {days:.0f} days",
        f"Started with:        ${start:,.2f}",
        f"Ended with:          ${end:,.2f}   ({(end / start - 1) * 100:+.1f}%)",
        f"Just holding bitcoin: {(last / first - 1) * 100:+.1f}%   <- the number to beat",
        f"Round trips:         {len(sells)}   won {len(wins)}, lost {len(sells) - len(wins)}",
        f"Fees paid:           ${acct.fees_paid:,.2f}",
        f"Worst drop from a high point: {worst * 100:.1f}%",
    ]
    if len(sells) < 30:
        lines.append(f"Careful: {len(sells)} round trips is far too few to trust. Thirty is a bare minimum; hundreds is better.")
    return "\n".join(lines)


def save_trades(acct):
    with open(HERE / "trades.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["time", "side", "price", "why", "value", "result_percent"]); w.writeheader()
        for x in acct.trades:
            w.writerow(dict(x, time=time.strftime("%Y-%m-%d %H:%M", time.gmtime(x["time"]))))


def backtest():
    bars = candles(CFG["market"]["pair"], CFG["market"]["candle_minutes"]); acct = Account(); warmup = 60
    if len(bars) < warmup + 50: sys.exit("Kraken returned too little history for this bar size. Try candle_minutes = 60.")
    for i in range(warmup, len(bars)):
        step(acct, bars[:i + 1])
    save_trades(acct); print(report(acct, bars, warmup)); print("Every trade is in trades.csv.")


def paper():
    minutes = CFG["market"]["candle_minutes"]; acct = Account(); seen = 0
    print(f"Paper trading {CFG['market']['pair']} on {minutes}-minute bars with pretend money. Ctrl+C to stop.")
    while True:
        try:
            bars = candles(CFG["market"]["pair"], minutes)
        except Exception as e:
            print(f"Could not reach Kraken ({e}). Trying again in a minute."); time.sleep(60); continue
        if bars[-1][0] != seen:
            seen = bars[-1][0]; before = len(acct.trades); step(acct, bars); price = bars[-1][4]
            what = f"{acct.trades[-1]['side'].upper()} ({acct.trades[-1]['why']})" if len(acct.trades) > before else "no trade"
            print(f"{time.strftime('%Y-%m-%d %H:%M', time.gmtime(seen))} UTC  price ${price:,.0f}  {what}  account ${acct.value(price):,.2f}")
            save_trades(acct)
        time.sleep(min(60, minutes * 15))


if __name__ == "__main__":
    mode = CFG["mode"]["run"]
    if mode == "backtest": backtest()
    elif mode == "paper": paper()
    else: sys.exit(f'config.toml says [mode] run = "{mode}". Use "backtest" or "paper".')
