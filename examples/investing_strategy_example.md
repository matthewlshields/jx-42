# Trend Following Strategy Definition (Example)

- Universe: large cap equities + index ETFs
- Signal: price above N-day moving average AND breakout over M-day high
- Entry: next day open (draft only)
- Exit: cross below moving average OR trailing stop
- Risk: max 1% portfolio risk per position; max 3 open positions; kill-switch at 10% drawdown
