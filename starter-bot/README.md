# Yes or No Lab starter bot

A first trading bot for spot bitcoin that you can read in one sitting. One settings file, four strategies, pretend money.

**It does not place real orders.** It replays recent prices or watches the live price and keeps a pretend account, so you can see what a strategy would have done before you risk anything.

## Run it

You need Python 3.11 or newer. Nothing else to install, and no exchange account.

```
python3 bot.py
```

It prints a report and writes every trade to `trades.csv`.

## Change it

Open `config.toml`. That file is the control room: which strategy to use, its numbers, the fee, the stop loss, and whether to replay history (`backtest`) or watch the live price (`paper`). Change a number, save, run again. You never need to edit `bot.py`.

## Read the report honestly

- **"Just holding bitcoin" is the number to beat.** A bot that loses less than holding in a falling month has not made money.
- **Count the round trips.** Three trades prove nothing. Thirty is a bare minimum.
- **Never set the fee to zero.** Most strategies that look good with no fee lose with a real one.
- **A good result on one month is where testing starts.** Try other bar sizes and wait for new data before believing it.

## Important

This is teaching code from Yes or No Lab, published by Coding Friend LLC. It is provided "as is" with no warranty, under the MIT license in `LICENSE`. It is not financial advice and it is not a recommendation to buy or sell anything. The settings in `config.toml` are examples for learning, not suggestions. Trading can lose money, including all of it. If you change this code to place real orders, you do so entirely at your own risk.
