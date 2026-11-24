# Yes or No Lab bots

Teaching bots from [Yes or No Lab](https://yesornolab.substack.com), a newsletter that tests trading ideas and publishes the result either way.

Every bot here is small enough to read in one sitting, keeps all of its settings in one file, and runs on pretend money. None of them can place a real order.

| Bot | What it is |
|---|---|
| [starter-bot](starter-bot/) | A first spot-bitcoin bot. One settings file, four strategies (momentum, moving-average cross, buy-the-dip, breakout), a history replay and a live practice mode. Plain Python, nothing to install, no exchange account. |

## Why these exist

Most "trading bot" pitches show a line going up and hide the code. These do the opposite. You get the code, and the report it prints tells you how the strategy really did, including against simply holding.

When we ran all four starter strategies on 27 days of hourly prices in November 2026, every one of them lost money. They are here to learn from, not to get rich with.

## Important

This is teaching code published by Coding Friend LLC. It is provided "as is" with no warranty, under the MIT license in [LICENSE](LICENSE). It is not financial advice and not a recommendation to buy or sell anything. The example settings are for learning, not suggestions. Trading can lose money, including all of it. If you change this code to place real orders, you do so entirely at your own risk.
