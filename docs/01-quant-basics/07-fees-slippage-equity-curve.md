---
aliases:
  - 第七章 加入手续费滑点与资金曲线
tags:
  - 书稿
  - 回测
  - 手续费
  - 滑点
  - 资金曲线
status: 初稿
chapter: 7
---

# 第七章：加入手续费、滑点与资金曲线

## 7.1 没有成本的回测只是第一版

第六章完成了第一次回测。那次回测已经能回答几个基础问题：策略有没有跑赢 BTC 买入持有，最大回撤有没有改善，买入和卖出次数是多少。

但它还有一个明显缺口：没有交易成本。

真实交易不是在一个干净的数学世界里发生的。每次买入和卖出，都可能产生手续费；真实成交价格也可能比回测里假设的价格更差。第六章的结果只能算“无成本版本”。它适合理解流程，不适合作为最终判断。

本章要把两个成本加进来：

```text
手续费：交易所或协议收取的费用
滑点：预期成交价和实际成交价之间的不利差异
```

加入成本以后，策略收益通常会变差。交易次数越多，影响越明显。

这不是坏事。回测的目的不是让曲线好看，而是让结果更接近真实交易。

## 7.2 手续费是什么

手续费是交易发生时支付给交易平台或协议的费用。

在中心化交易所里，现货交易通常会区分 maker 和 taker。

maker 是挂单提供流动性。例如我挂一个限价买单，等待别人卖给我。这个订单进入订单簿，增加了市场可交易深度。

taker 是吃单拿走流动性。例如我直接用市价单买入，立即吃掉订单簿里别人挂出的卖单。

很多交易所的 maker 费率和 taker 费率不同。taker 通常更贵，因为它立即消耗了订单簿里的流动性。

在本书当前阶段，策略只做日线现货回测，不模拟复杂挂单队列。因此，第一次加入手续费时，可以先按 taker 费率估算。这更保守，也更容易理解。

如果未来策略明确使用限价挂单，并且能够合理模拟是否成交，再考虑 maker 费率。

## 7.3 手续费从哪里获取

手续费不是固定不变的数字。不同交易所、不同账户等级、不同交易对、是否使用平台币抵扣，都可能影响费率。

获取手续费通常有四种方式。

### 第一种：查看交易所费率页面

这是最直接的方法。

比如 Binance、OKX 等交易所都有公开的费率页面。页面会列出普通用户、不同 VIP 等级、maker 和 taker 的费率。

这种方式适合学习阶段。缺点是它需要人工查看，而且费率可能随着时间变化。

所以，书稿和代码里不要把某个交易所当前费率当成永久事实。更好的写法是：

```text
本次回测假设 taker 手续费为 0.1%
真实费率以交易所当前费率页面或账户实际费率为准
```

### 第二种：用 CCXT 读取市场费率

CCXT 的市场信息里可能包含 maker 和 taker 费率。

示例代码：

```python
import ccxt

exchange = ccxt.binance({
    "enableRateLimit": True,
})

markets = exchange.load_markets()
market = markets["BTC/USDT"]

print("maker:", market.get("maker"))
print("taker:", market.get("taker"))
```

如果交易所支持统一手续费接口，也可以尝试：

```python
fee = exchange.fetch_trading_fee("BTC/USDT")
print(fee)
```

但这类接口并不是所有交易所都支持，有些还需要 API Key。CCXT 文档也提醒过，交易费率信息可能不完整或不稳定。

所以，CCXT 读取到的费率可以作为参考，但回测报告里仍然要写明：

```text
手续费来源：交易所费率页 / CCXT 市场信息 / 账户实际成交记录
```

### 第三种：读取真实成交记录

如果已经有真实交易记录，最准确的方式是看成交明细。

真实成交记录通常会包含：

```text
成交时间
交易对
买卖方向
成交价格
成交数量
手续费金额
手续费币种
```

这是复盘实盘交易时最可靠的数据。

但本书当前阶段还不做真实自动交易，所以暂时不用账户私有接口读取成交记录。学习阶段先用公开行情和假设费率完成回测。

### 第四种：Web3 链上交易的费用

如果是在 DEX 或链上执行交易，成本结构会更复杂。

它可能包括：

```text
Gas
协议费
LP 手续费
滑点
MEV 或三明治攻击造成的额外损失
跨链费用
```

这些内容后面进入 DEX 和链上策略时再展开。本章只处理中心化交易所现货 K 线回测中的交易手续费和滑点。

## 7.4 滑点是什么

滑点是预期成交价和实际成交价之间的差异。

假设 BTC 当前看起来是 70000 USDT，我的回测也按 70000 USDT 买入。但真实交易时，由于订单簿深度、市场波动、下单延迟等原因，实际成交均价可能是 70035 USDT。

这 35 USDT 的差异，就是买入时的不利滑点。

买入时：

```text
买入滑点 =（实际成交价 - 参考价格）÷ 参考价格
```

卖出时：

```text
卖出滑点 =（参考价格 - 实际成交价）÷ 参考价格
```

这两个公式都把“不利方向”的差异记为成本。

滑点和手续费不同。手续费通常可以提前查到大致费率，滑点只有在真实成交后才完全确定。

回测时只能估算滑点。

## 7.5 滑点从哪里获取

滑点没有一个固定页面可以查询。它依赖交易当时的市场状态和订单大小。

常见估算方式有三种。

### 第一种：用固定滑点假设

这是入门回测最常用的方法。

例如：

```text
每次交易假设滑点为 0.05%
```

如果策略交易次数不多、资产流动性较好、下单金额很小，这个简化可以先接受。

缺点也明显：它不能反映不同市场状态下的真实流动性。市场剧烈波动时，滑点可能远高于平时。

### 第二种：用订单簿估算

订单簿可以看到当前市场上买一价、卖一价，以及不同价格档位上的挂单数量。

用 CCXT 可以读取公开订单簿：

```python
order_book = exchange.fetch_order_book(
    "BTC/USDT",
    limit=20,
)

best_bid = order_book["bids"][0][0]
best_ask = order_book["asks"][0][0]
mid_price = (best_bid + best_ask) / 2

spread_rate = (best_ask - best_bid) / mid_price

print(f"买一价：{best_bid}")
print(f"卖一价：{best_ask}")
print(f"价差比例：{spread_rate:.4%}")
```

买卖价差可以看作最基础的即时交易成本之一。市价买入通常要吃卖一价，市价卖出通常要吃买一价。

如果订单金额较大，还会吃掉多个档位。此时需要根据订单簿逐档计算平均成交价。

示例：估算用 1000 USDT 市价买入 BTC 的平均成交价。

```python
def estimate_market_buy_price(asks, quote_amount):
    remaining_quote = quote_amount
    base_bought = 0
    quote_spent = 0

    for level in asks:
        price, amount = level[:2]

        level_quote = price * amount
        spend = min(remaining_quote, level_quote)

        base_bought += spend / price
        quote_spent += spend
        remaining_quote -= spend

        if remaining_quote <= 0:
            break

    if remaining_quote > 0:
        return None

    return quote_spent / base_bought


quote_amount = 1000
average_buy_price = estimate_market_buy_price(
    order_book["asks"],
    quote_amount,
)

buy_slippage = (
    average_buy_price - mid_price
) / mid_price

print(f"估算买入均价：{average_buy_price}")
print(f"估算买入滑点：{buy_slippage:.4%}")
```

这里没有写成 `for price, amount in asks`，是因为不同交易所返回的订单簿档位格式不一定完全相同。有些交易所只返回 `[price, amount]`，有些可能返回 `[price, amount, 其他字段]`。使用 `level[:2]` 只取价格和数量，可以避免因为额外字段导致解包报错。

这仍然只是估算。订单簿是瞬时快照，真实下单时市场可能已经变化。

### 第三种：用真实成交记录反推

真实交易完成后，可以用实际成交均价和下单前参考价格计算滑点。

例如，下单前参考价是 70000 USDT，实际买入均价是 70035 USDT：

```text
买入滑点 = (70035 - 70000) ÷ 70000
         = 0.05%
```

这是复盘实盘交易时最有价值的方法。

但它需要真实成交数据。入门阶段先不依赖这一步。

## 7.6 第一次成本模型：手续费 + 固定滑点

本章先使用最小成本模型。

假设：

```text
taker 手续费：0.10%
单次滑点：0.05%
单次交易总成本：0.15%
```

写成代码：

```python
fee_rate = 0.001
slippage_rate = 0.0005

single_trade_cost_rate = fee_rate + slippage_rate
```

这里的数字只是示例，不是交易建议。真实回测应根据交易所费率、账户等级、交易对流动性和订单大小调整。

因为本章策略只有两种状态：满仓 BTC 或空仓 USDT，所以每次买入或卖出都可以看作对整个账户做一次换仓。每次仓位从 0 变成 1，或者从 1 变成 0，就扣一次成本。

## 7.7 在回测中识别交易发生的时刻

第六章已经生成了 `position`。

`position` 表示当前 K 线开始时的持仓：

```text
0：空仓
1：持有 BTC
```

交易发生在 `position` 发生变化的时候。

```python
backtest["trade"] = (
    backtest["position"]
    .diff()
    .abs()
    .fillna(backtest["position"])
)

print(backtest["trade"].value_counts())
```

如果 `trade` 等于 1，说明当天开盘发生了一次买入或卖出。

如果 `trade` 等于 0，说明当天没有交易。

对于本章这种“满仓或空仓”的策略，`trade` 只会是 0 或 1。以后如果加入半仓、三成仓，`trade` 就可以表示仓位变化比例。

## 7.8 把成本加入策略收益

第六章中的无成本策略收益是：

```python
backtest["strategy_return"] = (
    backtest["position"] * backtest["open_to_next_open_return"]
)
```

加入成本后，先计算成本：

```python
backtest["cost_rate"] = (
    backtest["trade"] * single_trade_cost_rate
)
```

再计算扣除成本后的策略收益：

```python
backtest["strategy_return_with_cost"] = (
    backtest["position"] * backtest["open_to_next_open_return"]
    - backtest["cost_rate"]
)
```

这里的含义是：

```text
持仓收益 = position × BTC 开盘到下一日开盘收益
交易成本 = trade × 单次交易成本率
扣成本后收益 = 持仓收益 - 交易成本
```

如果当天没有交易，`cost_rate` 为 0。

如果当天发生买入或卖出，`cost_rate` 为 0.15%。

这个模型仍然是简化模型，但它已经比无成本回测更接近真实。

## 7.9 重新计算资金曲线

设初始资金仍然是 1000 USDT。

```python
initial_cash = 1000
```

无成本策略资金曲线：

```python
backtest["strategy_equity_no_cost"] = (
    initial_cash
    * (1 + backtest["strategy_return"]).cumprod()
)
```

有成本策略资金曲线：

```python
backtest["strategy_equity_with_cost"] = (
    initial_cash
    * (1 + backtest["strategy_return_with_cost"]).cumprod()
)
```

买入持有资金曲线保持不变：

```python
backtest["benchmark_equity"] = (
    initial_cash
    * (1 + backtest["benchmark_return"]).cumprod()
)
```

计算最终收益：

```python
strategy_return_no_cost = (
    backtest["strategy_equity_no_cost"].iloc[-1]
    / initial_cash
    - 1
)

strategy_return_with_cost = (
    backtest["strategy_equity_with_cost"].iloc[-1]
    / initial_cash
    - 1
)

benchmark_return = (
    backtest["benchmark_equity"].iloc[-1]
    / initial_cash
    - 1
)

print(f"策略收益率（无成本）：{strategy_return_no_cost:.2%}")
print(f"策略收益率（含成本）：{strategy_return_with_cost:.2%}")
print(f"买入持有收益率：{benchmark_return:.2%}")
```

如果交易次数不多，成本影响可能不大。如果交易次数很多，成本会明显拖累收益。

这也是为什么短线策略必须更重视手续费和滑点。

## 7.10 重新计算最大回撤

继续使用第二、三章中的回撤函数：

```python
def calculate_drawdown(equity_curve):
    historical_peak = equity_curve.cummax()
    drawdown = equity_curve / historical_peak - 1
    return drawdown
```

分别计算无成本和有成本回撤：

```python
backtest["drawdown_no_cost"] = calculate_drawdown(
    backtest["strategy_equity_no_cost"]
)

backtest["drawdown_with_cost"] = calculate_drawdown(
    backtest["strategy_equity_with_cost"]
)

backtest["benchmark_drawdown"] = calculate_drawdown(
    backtest["benchmark_equity"]
)

print(f"策略最大回撤（无成本）：{backtest['drawdown_no_cost'].min():.2%}")
print(f"策略最大回撤（含成本）：{backtest['drawdown_with_cost'].min():.2%}")
print(f"买入持有最大回撤：{backtest['benchmark_drawdown'].min():.2%}")
```

成本不只影响最终收益，也可能影响最大回撤。尤其当策略频繁交易时，连续小额成本会持续压低资金曲线。

## 7.11 画出三条资金曲线

把无成本策略、有成本策略和买入持有放在同一张图里。

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(
    figsize=(12, 6),
)

backtest["strategy_equity_no_cost"].plot(
    ax=ax,
    label="MA Strategy No Cost",
)

backtest["strategy_equity_with_cost"].plot(
    ax=ax,
    label="MA Strategy With Cost",
)

backtest["benchmark_equity"].plot(
    ax=ax,
    label="Buy and Hold",
    linestyle="--",
)

ax.set_title("Cost Impact on Equity Curve")
ax.set_ylabel("Equity")
ax.grid(True)
ax.legend()

plt.show()
```

![手续费与滑点实验结果](../assets/Pasted%20image%2020260623162858.png)
这张图能直接看出成本对策略的侵蚀。

如果两条策略曲线几乎重合，说明当前交易次数少，成本影响暂时不大。

如果有成本曲线明显低于无成本曲线，说明策略对成本敏感。后面就要重点检查交易频率、手续费假设和滑点假设。

## 7.12 交易次数怎样影响成本

成本和交易次数直接相关。

统计交易次数：

```python
trade_count = backtest["trade"].sum()

total_cost_rate_simple = trade_count * single_trade_cost_rate

print(f"交易次数：{trade_count:.0f}")
print(f"单次交易成本率：{single_trade_cost_rate:.2%}")
print(f"简单累计成本率估算：{total_cost_rate_simple:.2%}")
```

这里的“简单累计成本率估算”不是最终收益扣减值，因为真实资金曲线会复利变化。但它能帮助读者形成直觉：

```text
交易越多，成本越重
单次成本越高，策略越难盈利
```

假设单次交易成本为 0.15%：

| 交易次数 | 简单累计成本率 |
|---:|---:|
| 6 | 0.90% |
| 20 | 3.00% |
| 100 | 15.00% |
| 300 | 45.00% |

这也是为什么很多看起来聪明的短线策略，加入成本后会失效。

## 7.13 重新解读第六章的 300 天样本

第六章记录过一次 300 天样本回测：

| 指标 | 双均线策略 | BTC 买入持有 |
|---|---:|---:|
| 累计收益率 | -19.56% | -42.65% |
| 最大回撤 | -24.24% | -46.85% |

交易次数：

```text
买入次数：3
卖出次数：3
总交易次数：6
```

如果本章先使用：

```text
手续费：0.10%
滑点：0.05%
单次交易成本：0.15%
```

那么 6 次交易的简单累计成本率约为：

```text
6 × 0.15% = 0.90%
```

这说明，在这次 300 天样本里，交易次数不多，成本不会完全改变结论，但会让策略收益进一步下降。

无成本版本中，策略相对买入持有少亏 23.09 个百分点。加入成本后，这个优势会缩小，但只要成本影响小于 23.09 个百分点，策略仍然会在这段样本中跑赢买入持有。

这不是策略长期有效的证明，只是对本次样本的更真实解释。

## 7.14 本章实践

本章实践目标：把手续费和滑点加入第六章回测。

建议完成以下步骤：

1. 复制第六章 notebook，另存为 `notebooks/chapter07/backtest_with_cost.ipynb`。
2. 设置手续费假设，例如 `fee_rate = 0.001`。
3. 设置滑点假设，例如 `slippage_rate = 0.0005`。
4. 用 `position.diff().abs()` 识别交易发生的时间。
5. 计算每次交易成本。
6. 计算扣成本后的策略收益率。
7. 生成无成本和有成本两条策略资金曲线。
8. 重新计算收益率和最大回撤。
9. 画出无成本策略、有成本策略和买入持有三条曲线。
10. 写下成本假设来源。

如果有条件，可以再做一个敏感性测试：

```python
for cost_rate in [0.0005, 0.001, 0.002, 0.005]:
    equity = initial_cash * (
        1 + backtest["strategy_return"]
        - backtest["trade"] * cost_rate
    ).cumprod()

    total_return = equity.iloc[-1] / initial_cash - 1
    print(f"单次成本 {cost_rate:.2%}，策略收益 {total_return:.2%}")
```

这段代码可以观察：当成本变高时，策略是否仍然有优势。

## 本章小结

手续费可以从交易所费率页面、CCXT 市场信息、交易所手续费接口或真实成交记录中获取。学习阶段可以先使用公开费率和保守假设，实盘复盘时应优先使用真实成交记录。

滑点无法像手续费一样直接查到。它可以通过固定假设、订单簿估算或真实成交价反推。回测中的滑点永远只是近似值。

本章使用“手续费 + 固定滑点”的简化成本模型，把交易成本加入策略收益。这个模型不完美，但已经能让回测从“理想结果”向“更接近真实”前进一步。

交易次数越多，成本越重要。第六章的双均线策略在 300 天样本中只交易 6 次，成本影响相对有限；如果换成高频或短线策略，成本可能直接决定策略是否还能成立。

下一章将进入回测常见陷阱：未来函数、幸存者偏差和参数过拟合。它们不会像手续费一样直接显示在账户里，但对回测结果的破坏更隐蔽。

## 延伸阅读与资料来源

- [CCXT Manual：Fees](https://github.com/ccxt/ccxt/wiki/manual#fees)
- [CCXT Manual：fetchOrderBook](https://github.com/ccxt/ccxt/wiki/manual)
- [Binance：Spot Trading Fee Rate](https://www.binance.com/en/fee/trading)
- [OKX：Trading Fee](https://www.okx.com/fees)
