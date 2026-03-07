# python-automation-bot

# 🚀 CRYPTO ALERT BOT — SETUP GUIDE

## Step 1: Python Libraries Install Karo
```
pip install ccxt pandas pandas-ta requests schedule
```

## Step 2: bot.py mein apni settings dalo
```python
TELEGRAM_TOKEN = "Apna token yahan"     # BotFather se mila
TELEGRAM_CHAT_ID = "Apna chat ID"        # @userinfobot se mila
BINANCE_API_KEY = "Apni API key"         # Binance se mili
BINANCE_SECRET = "Apna secret"           # Binance se mila
```

## Step 3: Bot Run Karo
```
python bot.py
```

## ✅ Bot Kya Karega:
- Har 15 minute mein 50 top coins scan karega
- RSI 15m + 1H + 4H check karega
- EMA 20/50 analysis karega
- Volume filter lagayega
- Score 60+ pe Telegram alert bhejega
- RSI 70+ pe exit alert bhejega

## ⚠️ Important:
- Binance API mein sirf READ permission do
- Kabhi withdrawal permission mat do
- Bot sirf alerts bhejta hai, trade nahi karta
