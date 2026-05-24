# Crypto Trading Signals Bot

A Python market-scanning bot that watches 100+ USDT futures pairs and pushes actionable RSI-based entry signals to Telegram in real time.

## What it does

- **Scans 100+ top crypto pairs** (BTC, ETH, SOL, ARB, OP, SUI, INJ, TIA, PEPE, …) on a configurable interval
- **RSI-based entry filter** — flags pairs in a tunable oversold-to-momentum band (default RSI 35–60)
- **Exit signals** when RSI crosses an upper threshold (default 70)
- **Volume-spike detection** — alerts when a pair's volume jumps above a configurable multiple of its average
- **Macro guard** — fires an emergency alert if BTC drops more than the configured crash threshold (default −5%)
- **Telegram delivery** — formatted message per signal, including suggested leverage
- **Schedulable** via `schedule` package; runs continuously or on cron

## Tech

| Layer    | Library                          |
|----------|----------------------------------|
| Exchange | [ccxt](https://github.com/ccxt/ccxt) (unified exchange API) |
| Indicators | `pandas`, `pandas-ta`           |
| Delivery | Telegram Bot API (`requests`)    |
| Scheduling | `schedule`                     |

## Configuration

Edit the constants at the top of `bot.py`:

```python
TELEGRAM_TOKEN          = "<your bot token>"
TELEGRAM_CHAT_ID        = "<your chat id>"
RSI_ENTRY_MIN           = 35
RSI_ENTRY_MAX           = 60
RSI_EXIT                = 70
SCAN_INTERVAL_MINUTES   = 15
BTC_CRASH_THRESHOLD     = -5.0
VOLUME_SPIKE_MULTIPLIER = 2.0
```

## Run

```bash
pip install ccxt pandas pandas-ta requests schedule
python bot.py
```

## Disclaimer

This bot generates **informational signals only**. It does not execute trades. Crypto markets are high-risk; do your own research before acting on any signal.