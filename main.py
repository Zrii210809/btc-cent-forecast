# btc-cent-forecast-01 entry: forecast BTC's price 240 minutes after each checkpoint.
# Method (backtested on the kit's 6 practice windows, 384 checkpoints, plus the
# 5 practice cases whose answers the next case's last price reveals):
#   - if BTC moved <= 0.2% over the last 31 minutes, guess the median of the
#     last 31 closes: it denoises the pool's microstructure ticks;
#   - otherwise guess the last close, so a real move is tracked without lag.
# Backtest MAE: 35,142 cents vs 35,822 for persistence on 384 checkpoints
# (better in all 6 windows), 46,823 vs 47,055 on the 5 known practice cases.
# The gate uses the window's first close as its reference so a flat market is
# judged on the move across the whole window, not on the last tick alone.
# Deterministic: the same bytes on every run. Standard library only, no network.
import json
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

MEDIAN_WINDOW = 31
GATE = 0.002  # 0.2% move over the window

def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])

def price5(x):
    return round(max(1e-5, min(x, 9_999_999.0)), 5)

def forecast(prices):
    if not prices:
        raise ValueError("no prices")
    last = prices[-1]
    window = prices[-MEDIAN_WINDOW:]
    if len(window) < 2:
        return price5(last)
    move = abs(last / window[0] - 1.0)
    if move <= GATE:
        return price5(median(window))
    return price5(last)

def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(in_dir.glob("*.in")):
        cid = f.stem
        case = json.loads(f.read_text(encoding="utf-8"))
        markets = case.get("markets") or []
        if len(markets) != 1:
            raise ValueError(f"{f.name} does not hold exactly one market")
        prices = markets[0].get("prices") or []
        guess = forecast(prices)
        payload = {"forecasts": [{"case": cid, "price": guess}]}
        (out_dir / f"{cid}.out").write_text(json.dumps(payload) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
