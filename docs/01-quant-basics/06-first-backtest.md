---
aliases:
  - 第六章 完成第一次回测
tags:
  - 书稿
  - 回测
  - 双均线策略
  - BTC
  - 策略评估
status: 初稿
chapter: 6
---

# 第六章：完成第一次回测

## 6.1 回测不是证明策略能赚钱

第五章已经把 BTC 现货双均线策略写成了信号。我们知道了哪一天出现买入信号，哪一天出现卖出信号，也知道了如何把信号向后移动，避免在回测里使用未来信息。

现在可以进入回测。

回测，就是把一套交易规则放回历史数据中运行，观察如果过去按这套规则交易，账户会怎样变化。

这句话里有两个重点。

第一，回测使用的是历史数据。它只能说明策略在过去这段数据中的表现，不能证明未来一定会重复。

第二，回测运行的是规则。规则越清楚，回测越容易复现；规则越模糊，回测就越容易变成事后解释。

回测不是用来给策略盖章的。它更像一次压力测试：先看看策略在历史中有没有明显问题，是否比基准更好，过程中最大回撤有多大，交易次数是否过多，结果是否只是偶然。

一个策略如果连回测都经不起检查，就没有必要直接进入实盘。

## 6.2 为什么回测重要

回测的价值，不只是算出一个收益率。

它至少能帮助我完成几件事。

### 把想法变成可验证的规则

“趋势向上就买入”是一句判断。

“MA20 上穿 MA60 后，下一根 K 线开盘持有 BTC；MA20 下穿 MA60 后，下一根 K 线开盘空仓”才是规则。

只有规则足够清楚，代码才能执行，别人也才能复现。

### 在投入真实资金前发现错误

很多错误不需要等到实盘才暴露。

比如信号是不是提前使用了当天收盘价，买入和卖出有没有重复触发，账户是否在空仓时还计算了 BTC 收益，最大回撤是不是算错了。这些问题都可以在回测阶段发现。

### 观察收益背后的过程

只看最终收益是不够的。一个策略最后赚了 20%，中途可能回撤 50%；另一个策略最后只赚 12%，但中途最大回撤只有 8%。

回测能看到资金曲线，也能看到最难熬的时候。

### 和基准比较

第二章已经讲过，收益率必须有参照物。

BTC 双均线策略至少要和 BTC 买入持有比较。如果一套策略没有降低回撤，也没有提高收益，却增加了交易次数和手续费，那么它未必比简单持有更有价值。

## 6.3 第一次回测先做简化版

真正严谨的回测系统会考虑很多细节：手续费、滑点、订单成交方式、最小下单数量、交易所精度、资金占用、异常 K 线、网络延迟。

这些内容都重要，但不适合一次塞进第一个回测。

本章先做简化版。

假设如下：

| 项目 | 本章处理方式 |
|---|---|
| 交易对象 | BTC/USDT |
| 数据周期 | 1d |
| 交易方向 | 只做现货多头 |
| 信号来源 | MA20 与 MA60 交叉 |
| 成交假设 | 当天收盘后得到信号，下一天开盘调整仓位 |
| 仓位 | 满仓 BTC 或空仓 USDT |
| 初始资金 | 1000 USDT |
| 手续费 | 暂不计入 |
| 滑点 | 暂不计入 |
| 基准 | BTC 买入持有 |

这不是最终版本。

本章故意不加入手续费和滑点，是为了先把回测主流程跑通。第七章会把成本加进去。到那时，很多看起来不错的收益会变得更接近真实。

## 6.4 回测需要注意什么

第一次回测最容易犯的错误，不是公式复杂，而是假设没有写清楚。

### 不要使用未来函数

未来函数是回测中最危险的问题之一。

如果当天收盘后才能知道的均线信号，却假设自己已经在当天收盘价完成交易，这就是使用了未来信息。

本章采用更保守的方式：

```text
当天收盘后计算信号
下一天开盘调整仓位
之后计算下一段收益
```

这不代表它已经完全接近实盘，但比“看到当天收盘信号，又在当天收盘成交”更诚实。

### 数据周期必须一致

日线策略就使用日线信号和日线收益。

不能用日线信号去套分钟级成交假设，也不能用不同交易所的数据混在一起比较。数据来源、交易对、周期和时区，都必须记录下来。

### 成本暂时不计入，但不能忘记

本章暂不计算手续费和滑点，只是为了降低复杂度。它不代表交易没有成本。

如果一个策略在不计成本时只是略微跑赢基准，那么加入手续费后很可能变成落后。

### 不要只看最终收益

策略评价至少要同时看：

- 策略累计收益率
- BTC 买入持有收益率
- 最大回撤
- 交易次数
- 资金曲线是否稳定
- 策略是否长期空仓

如果只看一个最终收益数字，很容易误判策略。

### 不要为了结果反复调参数

MA20 和 MA60 只是第一组参数。看到回测结果不好后，很容易改成 MA10/MA30、MA15/MA45、MA5/MA120，一直调到历史表现最好。

这就是过拟合的入口。

参数可以研究，但不能为了让过去的曲线好看而无限试。

## 6.5 读取 BTC 数据并重新生成信号

第六章可以直接接着第五章的 notebook 做，也可以新建一个 notebook。

建议新建：

```text
notebooks/chapter06/first_backtest.ipynb
```

先读取第 4 章保存的数据：

```python
import pandas as pd

file_path = "data/btc_usdt_1d.csv"

df = pd.read_csv(
    file_path,
    parse_dates=["timestamp"],
    index_col="timestamp",
)

df = df.sort_index()

print(df.head())
print(df.tail())
```

重新计算 MA20 和 MA60：

```python
df["ma20"] = df["close"].rolling(window=20).mean()
df["ma60"] = df["close"].rolling(window=60).mean()
df["trend_up"] = df["ma20"] > df["ma60"]
```

生成严格的买入和卖出信号：

```python
previous_ma20 = df["ma20"].shift(1)
previous_ma60 = df["ma60"].shift(1)

df["buy_signal"] = (
    (previous_ma20 <= previous_ma60)
    & (df["ma20"] > df["ma60"])
)

df["sell_signal"] = (
    (previous_ma20 >= previous_ma60)
    & (df["ma20"] < df["ma60"])
)
```

接着把信号转换成持仓：

```python
df["target_position"] = pd.Series(
    index=df.index,
    dtype="float",
)

df.loc[df["buy_signal"], "target_position"] = 1
df.loc[df["sell_signal"], "target_position"] = 0

df["position"] = (
    df["target_position"]
    .ffill()
    .fillna(0)
    .shift(1, fill_value=0)
    .astype(int)
)

print(df[["buy_signal", "sell_signal", "position"]].tail())
```

这里的 `position` 表示这一根 K 线开始时持有的仓位。1 表示持有 BTC，0 表示空仓。

## 6.6 计算策略收益

本章采用“下一天开盘调整仓位”的简化假设。

如果今天开盘时持有 BTC，那么从今天开盘到明天开盘之间，账户承受 BTC 的价格变化。如果今天开盘时空仓，那么这段时间收益记为 0。

先计算 BTC 从今天开盘到明天开盘的收益率：

```python
df["open_to_next_open_return"] = (
    df["open"].shift(-1) / df["open"] - 1
)
```

再计算策略收益：

```python
df["strategy_return"] = (
    df["position"] * df["open_to_next_open_return"]
)
```

BTC 买入持有基准的收益，就是同一段时间内一直持有 BTC：

```python
df["benchmark_return"] = df["open_to_next_open_return"]
```

最后一行没有下一天开盘价，因此无法计算下一段收益。可以把它去掉：

```python
backtest = df.dropna(
    subset=["open_to_next_open_return"]
).copy()
```

为了避免均线还没有形成时参与统计，可以从 MA60 有效之后开始观察：

```python
backtest = backtest.loc[
    backtest["ma60"].notna()
].copy()
```

这一步让策略和基准在同一个有效区间内比较。

## 6.7 计算资金曲线

假设初始资金为 1000 USDT。

```python
initial_cash = 1000
```

策略资金曲线：

```python
backtest["strategy_equity"] = (
    initial_cash
    * (1 + backtest["strategy_return"]).cumprod()
)
```

BTC 买入持有资金曲线：

```python
backtest["benchmark_equity"] = (
    initial_cash
    * (1 + backtest["benchmark_return"]).cumprod()
)
```

查看最后几行：

```python
print(backtest[[
    "strategy_return",
    "benchmark_return",
    "strategy_equity",
    "benchmark_equity",
]].tail())
```

资金曲线比最终收益更重要。最终收益只告诉我终点，资金曲线会告诉我中间经历了什么。

## 6.8 计算累计收益率和最大回撤

累计收益率：

```python
strategy_total_return = (
    backtest["strategy_equity"].iloc[-1] / initial_cash - 1
)

benchmark_total_return = (
    backtest["benchmark_equity"].iloc[-1] / initial_cash - 1
)

print(f"策略累计收益率：{strategy_total_return:.2%}")
print(f"买入持有收益率：{benchmark_total_return:.2%}")
```

最大回撤可以写成一个函数：

```python
def calculate_drawdown(equity_curve):
    historical_peak = equity_curve.cummax()
    drawdown = equity_curve / historical_peak - 1
    return drawdown
```

分别计算策略和基准的回撤：

```python
backtest["strategy_drawdown"] = calculate_drawdown(
    backtest["strategy_equity"]
)

backtest["benchmark_drawdown"] = calculate_drawdown(
    backtest["benchmark_equity"]
)

strategy_max_drawdown = backtest["strategy_drawdown"].min()
benchmark_max_drawdown = backtest["benchmark_drawdown"].min()

print(f"策略最大回撤：{strategy_max_drawdown:.2%}")
print(f"买入持有最大回撤：{benchmark_max_drawdown:.2%}")
```

还可以统计交易次数：

```python
buy_count = backtest["buy_signal"].sum()
sell_count = backtest["sell_signal"].sum()
trade_count = buy_count + sell_count

print(f"买入次数：{buy_count}")
print(f"卖出次数：{sell_count}")
print(f"交易信号总数：{trade_count}")
```

交易次数现在还没有成本影响。第七章加入手续费和滑点后，交易次数会变得更重要。

## 6.9 如果策略资金曲线一直是 1000

第一次运行回测时，可能会看到这样的结果：

```text
strategy_return 一直是 0
strategy_equity 一直是 1000
benchmark_equity 却在上下变化
```

这通常不是收益公式错了，而是策略一直没有持仓。

可以先检查持仓分布：

```python
print(backtest["position"].value_counts())
```

如果只看到：

```text
0    ...
```

说明整个有效回测区间里，策略都处于空仓状态。因为：

```text
strategy_return = position × open_to_next_open_return
```

当 `position` 一直是 0 时，策略收益自然一直是 0，资金也会一直停留在初始资金。

再检查买入和卖出信号数量：

```python
print("买入次数：", backtest["buy_signal"].sum())
print("卖出次数：", backtest["sell_signal"].sum())
```

如果买入次数为 0，通常有两种原因。

第一，数据太短。第 4 章如果只获取了 100 根日线，MA60 形成后只剩 40 根左右的有效数据，可能根本没有出现真正的 MA20 上穿 MA60。

第二，回测开始时 MA20 已经在 MA60 上方。严格金叉规则不会把“刚开始观察时已经处在多头状态”当成买入信号。它只会在样本内部真正发生上穿时买入。

这时有两个处理方式。

第一种，保留严格规则，接受策略在这段样本中没有交易。这样更适合训练“事件信号”的概念。

第二种，扩大数据范围。比如第 4 章获取数据时使用：

```python
limit = 1000
```

这样 MA20/MA60 有更长的历史区间，出现完整买入和卖出信号的概率更高。

不要为了让策略产生交易而随便修改参数。先确认数据长度、信号数量和持仓状态，再决定是否继续。

## 6.10 把策略和基准画在一起

数字需要看，图也需要看。

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(
    2,
    1,
    figsize=(12, 8),
    sharex=True,
)

backtest["strategy_equity"].plot(
    ax=axes[0],
    label="MA Strategy",
)

backtest["benchmark_equity"].plot(
    ax=axes[0],
    label="Buy and Hold",
    linestyle="--",
)

axes[0].set_title("Strategy vs Buy and Hold")
axes[0].set_ylabel("Equity")
axes[0].grid(True)
axes[0].legend()

backtest["strategy_drawdown"].plot(
    ax=axes[1],
    label="MA Strategy Drawdown",
)

backtest["benchmark_drawdown"].plot(
    ax=axes[1],
    label="Buy and Hold Drawdown",
    linestyle="--",
)

axes[1].set_title("Drawdown Comparison")
axes[1].set_ylabel("Drawdown")
axes[1].grid(True)
axes[1].legend()

plt.tight_layout()
plt.show()
```

第一张图比较策略资金曲线和买入持有资金曲线。第二张图比较两者的回撤。

如果策略收益更低，但回撤也明显更小，它未必没有价值。

如果策略收益更低，回撤也没有改善，交易次数还很多，那它大概率不值得继续投入精力。

如果策略收益更高，但中间回撤极大，也不能只看最终数字就认为它更好。

## 6.11 读懂第一次回测结果

回测跑完后，不要急着下结论。

先按顺序问几个问题。

第一，策略是否跑赢买入持有？

```text
策略累计收益率 - 买入持有收益率 = 超额收益
```

如果超额收益为负，说明策略没有跑赢基准。

第二，策略最大回撤是否更小？

双均线策略有时跑不赢大牛市，因为它会在趋势确认后才入场。但它可能在某些下跌阶段减少持仓，从而降低回撤。是否真的降低，要看数据。

第三，交易次数是否过多？

本章暂不计成本。交易次数越多，第七章加入成本后受到的影响越大。

第四，策略是否长时间空仓？

如果策略大部分时间都空仓，那么收益和风险都会降低。它看起来回撤小，可能只是因为没有参与市场。

第五，结果是否依赖少数几次交易？

如果一套策略大部分收益来自一两次偶然大涨，稳定性就需要继续验证。

第一次回测的目标不是找到完美策略，而是学会读懂结果。

### 本次 300 天样本的回测记录

本章使用约 300 天 BTC/USDT 日线数据，对 MA20/MA60 双均线策略做了一次简化回测。交易假设仍然是：收盘后生成信号，下一日开盘调整仓位；暂不计入手续费和滑点。

回测结果如下：

| 指标 | 双均线策略 | BTC 买入持有 |
|---|---:|---:|
| 累计收益率 | -19.56% | -42.65% |
| 最大回撤 | -24.24% | -46.85% |

交易次数：

```text
买入次数：3
卖出次数：3
```

从这组结果看，双均线策略没有实现盈利，账户仍然亏损 19.56%。但相对于 BTC 买入持有，它少亏了 23.09 个百分点：

```text
超额收益 = -19.56% - (-42.65%)
         = 23.09%
```

最大回撤也从买入持有的 -46.85% 降低到 -24.24%。这说明在这段样本中，策略确实减少了下跌行情中的持仓暴露，起到了一定的回撤控制作用。

但这个结果不能直接证明策略长期有效。

第一，样本只有约 300 天，时间不够长。

第二，本章还没有计入手续费和滑点。

第三，这段行情本身偏下跌，趋势过滤策略在这种市场里更容易表现出“少亏”的效果。如果换成快速上涨行情，双均线策略可能因为入场滞后而跑输买入持有。

因此，这次回测更准确的结论是：

> 在当前 300 天样本中，MA20/MA60 双均线策略没有赚钱，但相比 BTC 买入持有明显降低了亏损和最大回撤。下一步需要加入手续费和滑点，并用更长时间区间继续验证。

## 6.12 本章回测的局限

本章回测只是第一版。它有明确局限。

第一，没有手续费。

每一次买入和卖出都应该付出成本。本章暂时忽略了它。

第二，没有滑点。

真实成交价格可能和开盘价不同。资金越大、流动性越差，滑点越明显。

第三，没有考虑最小交易数量和交易精度。

交易所通常有最小下单金额、数量精度和价格精度。

第四，没有处理异常数据。

如果某一天 K 线异常，回测结果可能被扭曲。

第五，只测试了一组参数。

MA20/MA60 只是一个起点。它是否稳定，需要后续用更多时间区间和参数组合检查。

第六，历史表现不代表未来。

市场环境会变。过去有效的趋势策略，未来可能失效。

这些局限不是为了否定回测，而是为了提醒自己：回测结果必须带着假设阅读。

## 6.13 回测记录应该写什么

每一次回测都应该留下记录。否则，几天后很难说清自己到底测了什么。

一份最小回测记录至少包括：

```text
策略名称：BTC 现货 MA20/MA60 双均线策略
数据来源：第 4 章保存的 BTC/USDT 日线数据
交易所：例如 Binance via CCXT
交易对：BTC/USDT
数据周期：1d
回测区间：开始日期至结束日期
初始资金：1000 USDT
成交假设：收盘后生成信号，下一日开盘调整仓位
手续费：未计入
滑点：未计入
基准：BTC 买入持有
策略收益率：
基准收益率：
策略最大回撤：
基准最大回撤：
交易次数：
主要观察：
```

这些记录看起来繁琐，但它们会防止后续复盘时只记得结论，忘记条件。

## 6.14 本章实践

本章实践目标：完成第一次可复查的策略回测。

建议完成以下步骤：

1. 新建 `notebooks/chapter06/first_backtest.ipynb`。
2. 读取 `data/btc_usdt_1d.csv`。
3. 计算 MA20、MA60、买入信号和卖出信号。
4. 根据买卖信号生成 `position`。
5. 使用下一日开盘价计算收益。
6. 生成策略资金曲线。
7. 生成 BTC 买入持有资金曲线。
8. 计算策略收益率和买入持有收益率。
9. 计算策略最大回撤和买入持有最大回撤。
10. 统计买入次数、卖出次数和交易信号总数。
11. 画出资金曲线和回撤对比图。
12. 写一份回测记录。

如果结果看起来异常，不要先调参数。先检查数据、信号、持仓和收益计算。

## 本章小结

回测是把交易规则放回历史数据中运行，观察策略过去会怎样表现。它不能证明未来一定赚钱，但可以在真实资金投入前发现很多问题。

第一次回测应该尽量简单。本章只做 BTC 现货多头双均线策略，不计手续费和滑点，使用收盘后信号、下一日开盘调整仓位的假设。

回测结果必须和基准比较。双均线策略如果不能跑赢 BTC 买入持有，也没有改善最大回撤，就需要重新审视策略价值。

本章 300 天样本中，双均线策略亏损 19.56%，BTC 买入持有亏损 42.65%；策略最大回撤为 -24.24%，买入持有最大回撤为 -46.85%。这说明策略在该样本中没有盈利，但减少了亏损和回撤。

回测最重要的不是漂亮收益率，而是可复查。数据来源、参数、交易假设、成本处理和结果指标，都要写清楚。

下一章将把手续费和滑点加入回测。到那时，策略收益会更接近真实交易结果。

## 延伸阅读与资料来源

- [Pandas：Series.cumprod](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.cumprod.html)
- [Pandas：Series.cummax](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.cummax.html)
- [Pandas：DataFrame.shift](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.shift.html)
- [Investopedia：Backtesting](https://www.investopedia.com/terms/b/backtesting.asp)
