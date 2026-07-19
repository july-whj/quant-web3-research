---
aliases:
  - 第三章 Python与时间序列
tags:
  - 书稿
  - Python
  - Pandas
  - 时间序列
status: 初稿
chapter: 3
---

# 第三章：Python、数据工具与时间序列

## 3.1 从一个计算问题开始

我有技术背景，对 Python 并不陌生。真正开始研究量化交易后，我发现编程面对的第一个问题很具体：怎样把一个金融概念准确地翻译成代码。

假设刚刚完成一笔交易，我想知道自己究竟赚了多少。手工计算一次并不困难：记录本金、卖出金额、手续费和滑点，再按照收益率公式计算即可。

可如果要计算上百笔交易，检查几年的 K 线，或者每天重复更新账户资金，手工计算很快就会变得低效，而且容易出错。

Python 的价值在这时开始显现。它可以保存计算步骤，对不同数据重复执行相同规则，还可以一次处理成千上万个价格和交易记录。

第一次接触编程时，很容易被语法、循环和面向对象这些概念挡在门外。量化计算不必从完整的语法体系开始。先给本金和手续费起一个名字，再写出收益率公式；数据变多后，引入列表和表格；价格按照时间连续出现时，再处理时间序列。每一步都对应一个已经出现的问题。

前两章留下了几个尚未用代码解决的问题：

```text
如何计算真实交易成本？
如何计算收益率和复利？
如何把策略收益和基准放在一起比较？
如何计算超额收益、夏普比率和信息比率？
如何沿着资金曲线计算最大回撤？
分钟、小时和日K线有什么区别？
时间顺序出错为什么会让回测失真？
```

每个问题都按照同一种方式展开：

```text
先理解公式
→ 再手工计算
→ 用 Python 验算
→ 用 Pandas 批量处理
→ 最后把结果画出来
```

这些练习构成了一条最短的量化编程路径。走完这条路径，还不足以独立开发交易系统，但已经能够看懂和修改基础量化代码，分清输入数据、计算步骤与输出结果。

## 3.2 先认识工具：它们分别负责什么

量化研究通常会同时使用多个工具和库。Python 初学者常问：已经有了 Python，为什么还要安装 NumPy、Pandas 和 Matplotlib？

它们是一组分工不同的工具。

| 工具 | 通俗定位 | 在量化中的用途 |
|---|---|---|
| Python | 总指挥和连接器 | 表达规则、组织计算流程 |
| Jupyter Notebook | 可运行的实验笔记本 | 一边写说明，一边运行代码 |
| NumPy | 批量数字计算器 | 快速处理大量数值和数组 |
| Pandas | 可以编程的 Excel | 处理 K 线、时间和表格数据 |
| Matplotlib | 数据画图工具 | 绘制价格、收益和资金曲线 |
| Requests、CCXT | 数据搬运工具 | 从 API 和交易所获取行情 |
| QuantDinger | 量化工作台 | 管理策略、回测、模拟和执行 |

下面的代码使用 Python、NumPy、Pandas 和 Matplotlib。Requests、CCXT 和 QuantDinger 暂不参与计算，它们分别负责数据采集、交易所连接和策略运行。

### 准备一个最小运行环境

先检查本机的 Python 版本：

```bash
python --version
```

独立环境可以避免不同项目的库互相影响：

```bash
cd "05-代码与实验"
python -m venv .venv
```

macOS 或 Linux 激活环境：

```bash
source .venv/bin/activate
```

Windows PowerShell 激活环境：

```powershell
Set-Location "05-代码与实验"
.venv\Scripts\Activate.ps1
```

在独立环境中安装需要的库：

```bash
python -m pip install numpy pandas matplotlib jupyter
```

启动 Jupyter：

```bash
python -m jupyterlab
```

Jupyter 可以把文字、公式、代码和运行结果保存在同一个笔记中。需要长期维护的策略代码通常保存为普通的 `.py` 文件，并使用代码编辑器管理。

## 3.3 变量：给本金、费用和收益贴上名字

第二章记录的那次真实 Web3 操作，正好可以作为第一个 Python 练习。

那次操作资金是 14 USDT，TRON 转账手续费是 1.1476 USDT，币安提现到 BSC 的费用是 0.01 USDT。

```python
principal = 14
tron_fee = 1.1476
bsc_fee = 0.01

total_fee = tron_fee + bsc_fee
fee_rate = total_fee / principal

print(f"总费用：{total_fee:.4f} USDT")
print(f"费用占比：{fee_rate:.2%}")
```

运行结果：

```text
总费用：1.1576 USDT
费用占比：8.27%
```

这里的 `principal`、`tron_fee` 和 `bsc_fee` 都是变量。

变量像一个带名字的盒子。盒子保存数值，名字说明这个数值在现实中代表什么。

如果代码直接写成：

```python
(1.1476 + 0.01) / 14
```

计算机仍然可以得到答案，但每个数字的含义已经变得模糊。变量既保存数据，也让计算过程保持可读。

这段代码用到了四种基础数据类型：

```python
principal = 14                 # int：整数
fee = 1.1576                   # float：小数
symbol = "BNB/USDT"           # str：文本
paper_only = True              # bool：真或假
```

## 3.4 列表和字典：保存一组数据

单个变量只能保存一个值。记录账户连续几天的资金变化时，可以使用列表：

```python
equity_curve = [1000, 1100, 1050, 1300, 900, 1000]
```

列表像一排有顺序的抽屉。第一个值代表最早的资金，最后一个值代表最新资金。

时间顺序非常重要。下面两组数字包含相同的金额，但顺序不同：

```python
curve_a = [1000, 1300, 900]
curve_b = [1000, 900, 1300]
```

两者的最终金额不同，过程中经历的最大回撤也不同。因此，量化数据不能只保存数值，还要保存它发生的时间。

字典则适合保存带名称的一组信息：

```python
trade = {
    "symbol": "BNB/USDT",
    "principal": 14,
    "entry_price": 605,
    "total_fee": 1.1576,
}
```

字典中的每一项都是“名称和数值”的组合。创建 Pandas 表格时，列名和数据经常使用这种结构表达。

## 3.5 函数：把金融公式变成可以重复使用的工具

第二章使用了最简单的收益率公式：

```text
收益率 =（结束资金 - 初始资金）÷ 初始资金
```

把它写成 Python：

```python
initial_money = 1000
final_money = 1100

return_rate = (final_money - initial_money) / initial_money

print(f"收益率：{return_rate:.2%}")
```

反复计算同一个指标时，可以把公式封装成函数：

```python
def calculate_return(initial_money, final_money):
    return (final_money - initial_money) / initial_money


result = calculate_return(1000, 1100)
print(f"收益率：{result:.2%}")
```

函数像一台小机器。数据进入函数，经过固定步骤处理后返回结果。

加入交易成本后，函数需要再接收一个参数：

```python
def calculate_net_return(initial_money, final_money, total_cost=0):
    net_profit = final_money - initial_money - total_cost
    return net_profit / initial_money


result = calculate_net_return(
    initial_money=1000,
    final_money=1080,
    total_cost=10,
)

print(f"净收益率：{result:.2%}")
```

输出结果是：

```text
净收益率：7.00%
```

`total_cost=0` 表示没有传入成本时按 0 计算。这个默认值让同一个函数可以处理不同情况。

## 3.6 NumPy：一次计算很多个数字

普通 Python 足以完成单次收益计算。但量化研究面对的往往是几千甚至几百万个价格和收益率。

NumPy 的主要作用，是使用数组批量处理数值。

```python
import numpy as np

period_returns = np.array([0.02, -0.01, 0.03, -0.02])

total_return = np.prod(1 + period_returns) - 1

print(f"累计收益率：{total_return:.2%}")
```

这里不能简单地把 2%、-1%、3% 和 -2% 直接相加，因为每一期收益都作用在上一期结束后的资金上。

```text
累计收益率
= (1 + 2%) × (1 - 1%) × (1 + 3%) × (1 - 2%) - 1
```

NumPy负责批量数值计算，Pandas则在这些数值上继续增加时间、列名和缺失值处理能力。

## 3.7 Pandas：把数据放进一张可编程的表格

Pandas中最常见的两个数据结构是：

- `Series`：一列带索引的数据。
- `DataFrame`：多列组成的一张表格。

先创建一张简单的K线表：

```python
import pandas as pd

data = {
    "timestamp": [
        "2026-01-01 00:00:00",
        "2026-01-01 01:00:00",
        "2026-01-01 02:00:00",
        "2026-01-01 03:00:00",
    ],
    "open": [100, 103, 101, 106],
    "high": [105, 104, 108, 109],
    "low": [99, 100, 100, 105],
    "close": [103, 101, 106, 108],
    "volume": [12, 8, 15, 10],
}

df = pd.DataFrame(data)

print(df)
```

`DataFrame`是一张可以编程处理的表格。每一行代表一个时间点，每一列代表一种数据。

当前的 `timestamp` 还只是文本，必须先转换成时间类型。

## 3.8 时间才是K线真正的坐标轴

量化交易的数据都有明确的时间顺序。价格、成交量、账户资金和交易记录发生在不同时间，先后关系会直接影响计算结果。

先把时间列转换成 Pandas 能够识别的时间类型，并统一使用 UTC：

```python
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
df = df.set_index("timestamp")
df = df.sort_index()

print(df)
```

这几行分别完成了：

```text
pd.to_datetime()：把文本转换成时间
utc=True：将时间明确为 UTC
set_index()：使用时间作为表格索引
sort_index()：按照时间从早到晚排序
```

使用时间索引后，Pandas才知道哪一行是上一小时、哪一行是下一小时，也才能正确进行周期转换、滚动计算和收益率计算。

### 为什么统一使用 UTC

加密货币全天候交易，不同交易所、钱包和数据源可能使用不同的时区。如果一部分数据使用北京时间，另一部分使用 UTC，同一个时间可能被错误地当成两个不同时间点。

原始数据统一保存为 UTC，展示时再转换到北京时间，通常更容易管理：

```python
beijing_index = df.index.tz_convert("Asia/Shanghai")
```

## 3.9 分钟、小时、日线到底有什么区别

一根K线代表一段时间内的市场变化。

```text
1分钟K线：记录这一分钟内的开、高、低、收和成交量
1小时K线：记录这一小时内的数据
日K线：记录一天内的数据
周K线：记录一周内的数据
```

相同策略使用不同K线周期，结果可能完全不同。

- 分钟线包含更多细节，交易信号也更多。
- 日线过滤了很多短期波动，交易次数通常更少。
- 周线变化更慢，更适合观察长期趋势。

周期越短，并不代表信息一定越有价值。短周期通常还意味着更多噪声、更高交易频率和更明显的手续费影响。

因此，每次回测都必须记录：

```text
交易对：BTC/USDT
数据周期：1小时
回测区间：2024-01-01至2025-12-31
时区：UTC
```

只说“策略收益率是20%”，缺少周期和时间范围，就无法判断这个结果代表什么。

## 3.10 小周期怎样合成大周期K线

把小时K线转换成日K线，不能简单计算所有价格的平均值。

正确的OHLCV聚合规则是：

```text
开盘价：这一天第一根K线的开盘价
最高价：这一天所有K线中的最高价
最低价：这一天所有K线中的最低价
收盘价：这一天最后一根K线的收盘价
成交量：这一天所有K线成交量之和
```

使用刚才创建的小时数据：

```python
daily = df.resample(
    "1D",
    label="left",
    closed="left",
).agg({
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum",
})

daily = daily.dropna(subset=["open", "close"])

print(daily)
```

得到的日K线是：

| 时间 | open | high | low | close | volume |
|---|---:|---:|---:|---:|---:|
| 2026-01-01 UTC | 100 | 109 | 99 | 108 | 45 |

`resample("1D")`表示按照一天重新分组。`label`和`closed`决定每个时间区间怎样标记、边界数据属于哪一组。这些参数在日线切分、交易所K线时间和策略信号对齐时非常重要。

## 3.11 沿着时间计算收益率和复利

有了按时间排列的收盘价，就可以计算每一期收益率：

```python
df["return"] = df["close"].pct_change(fill_method=None)

print(df[["close", "return"]])
```

`pct_change()`默认用当前值和上一行比较：

```text
本期收益率 =（本期收盘价 - 上期收盘价）÷ 上期收盘价
```

第一行没有上一期数据，因此收益率会显示为空值 `NaN`。这不是错误，而是表示当前没有足够信息完成计算。

接着计算累计收益率：

```python
df["growth"] = (1 + df["return"].fillna(0)).cumprod()
df["cumulative_return"] = df["growth"] - 1

print(df[["close", "return", "cumulative_return"]])
```

这里的 `cumprod()` 是连续累乘。它把每一期收益按照时间顺序连接起来，正好对应第二章的复利计算。

这里的 `fillna(0)`只把第一期无法计算的收益视为0，方便从初始资金开始累计。真实K线中间出现缺失值时，不能不加判断地全部填成0。

### 为什么时间周期必须写清楚

一分钟收益率、小时收益率和每日收益率不是同一个指标。年化收益率也必须根据数据频率计算。

加密货币通常全天候交易，日线一年约有365期；传统证券市场还需要考虑交易日和休市。把一天的偶然高收益直接乘以365，通常会严重夸大结果。

在入门阶段，与其急着计算年化收益率，不如先同时记录累计收益率、实际起止日期和K线周期。

## 3.12 把策略收益和基准放在同一张表里

第二章加入了基准和超额收益。这个概念用手工计算并不难：策略收益率减去基准收益率即可。

真正容易出错的地方，是时间对齐。

策略收益和基准收益必须发生在同一段时间里，才能直接比较。不能拿策略的小时收益去比较 BTC 的日收益，也不能拿 2026 年 1 月的策略结果去比较 2026 年 2 月的市场表现。

先创建一张简化的收益率表：

```python
import pandas as pd

returns = pd.DataFrame(
    {
        "strategy_return": [0.00, 0.015, -0.005, 0.020, -0.010, 0.012],
        "benchmark_return": [0.00, 0.020, -0.015, 0.030, -0.020, 0.018],
    },
    index=pd.date_range(
        "2026-01-01",
        periods=6,
        freq="1D",
        tz="UTC",
    ),
)

print(returns)
```

这里的 `strategy_return` 是策略每天的收益率，`benchmark_return` 是基准每天的收益率。两列使用同一个时间索引，表示它们在同一批日期上比较。

计算策略和基准的累计收益：

```python
returns["strategy_growth"] = (1 + returns["strategy_return"]).cumprod()
returns["benchmark_growth"] = (1 + returns["benchmark_return"]).cumprod()

returns["strategy_cumulative_return"] = returns["strategy_growth"] - 1
returns["benchmark_cumulative_return"] = returns["benchmark_growth"] - 1

final_strategy_return = returns["strategy_cumulative_return"].iloc[-1]
final_benchmark_return = returns["benchmark_cumulative_return"].iloc[-1]
final_excess_return = final_strategy_return - final_benchmark_return

print(f"策略累计收益率：{final_strategy_return:.2%}")
print(f"基准累计收益率：{final_benchmark_return:.2%}")
print(f"最终超额收益：{final_excess_return:.2%}")
```

运行结果：

```text
策略累计收益率：3.21%
基准累计收益率：3.24%
最终超额收益：-0.03%
```

这段代码的核心不是公式有多复杂，而是把策略和基准放进同一张时间表。只要时间索引对齐，后面的比较才有意义。

如果只关心每一期是否跑赢基准，可以直接计算逐期超额收益：

```python
returns["active_return"] = (
    returns["strategy_return"] - returns["benchmark_return"]
)

print(returns[[
    "strategy_return",
    "benchmark_return",
    "active_return",
]])
```

`active_return` 为正，说明这一期策略跑赢基准；为负，说明这一期落后基准。

第二章还提到了夏普比率和信息比率。入门阶段可以先写成两个小函数：

```python
def calculate_sharpe_ratio(period_returns, risk_free_rate=0):
    excess_return = period_returns - risk_free_rate
    return excess_return.mean() / excess_return.std(ddof=1)


def calculate_information_ratio(strategy_returns, benchmark_returns):
    active_return = strategy_returns - benchmark_returns
    return active_return.mean() / active_return.std(ddof=1)


sharpe_ratio = calculate_sharpe_ratio(returns["strategy_return"])
information_ratio = calculate_information_ratio(
    returns["strategy_return"],
    returns["benchmark_return"],
)

print(f"夏普比率：{sharpe_ratio:.2f}")
print(f"信息比率：{information_ratio:.2f}")
```

运行结果：

```text
夏普比率：0.44
信息比率：-0.02
```

这两个结果还没有年化。年化需要知道数据频率，例如日线、小时线或分钟线。加密货币日线通常可以按一年 365 期估算，传统证券市场常按一年约 252 个交易日估算。现在先保留未年化结果，避免在样本很短时被夸大的数字误导。

夏普比率使用策略收益和无风险收益比较，信息比率使用策略收益和基准收益比较。代码上看，只是减去的对象不同；金融含义上，一个关心承担波动是否值得，另一个关心是否稳定跑赢基准。

## 3.13 沿着资金曲线计算最大回撤

现在使用第二章练习中的账户资金：

```python
import pandas as pd

equity = pd.Series(
    [1000, 1100, 1050, 1300, 900, 1000],
    index=pd.date_range(
        "2026-01-01",
        periods=6,
        freq="1D",
        tz="UTC",
    ),
    name="equity",
)
```

计算每个时间点之前出现过的最高资金：

```python
historical_peak = equity.cummax()
```

计算当前资金相对历史最高点的回撤：

```python
drawdown = equity / historical_peak - 1
```

找到最严重的一次回撤：

```python
max_drawdown = drawdown.min()
trough_time = drawdown.idxmin()
peak_time = equity.loc[:trough_time].idxmax()

print(f"最大回撤：{max_drawdown:.2%}")
print(f"回撤高点：{peak_time}")
print(f"回撤低点：{trough_time}")
```

结果是：

```text
最大回撤：-30.77%
回撤高点：2026-01-04
回撤低点：2026-01-05
```

因为资金从1300元跌到900元：

```text
(900 - 1300) ÷ 1300 ≈ -30.77%
```

### 为什么数据频率会影响最大回撤

如果只保存每日收盘资金，盘中发生的大幅下跌可能不会出现在数据中。使用小时或分钟数据，可能会看到更深的盘中回撤。

所以最大回撤必须和数据频率一起说明：

```text
基于日线收盘资金计算的最大回撤：-20%
基于分钟账户权益计算的最大回撤：-27%
```

两者都可能计算正确，只是观察精度不同。

## 3.14 把资金曲线和回撤画出来

数字可以准确表达结果，图表则更容易展示过程。

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(
    2,
    1,
    figsize=(10, 7),
    sharex=True,
)

equity.plot(ax=axes[0], label="Equity")
historical_peak.plot(
    ax=axes[0],
    label="Historical Peak",
    linestyle="--",
)
axes[0].set_title("Equity Curve")
axes[0].set_ylabel("Account Value")
axes[0].legend()

drawdown.plot(ax=axes[1], color="red")
axes[1].fill_between(
    drawdown.index,
    drawdown.values,
    0,
    color="red",
    alpha=0.2,
)
axes[1].set_title("Drawdown")
axes[1].set_ylabel("Drawdown")

plt.tight_layout()
plt.show()
```

第一张图展示账户资金和历史高点，第二张图展示资金从高点跌下来的比例。最大回撤发生的位置和后续恢复过程都可以从图中看到。
![时间序列示例](../assets/Pasted%20image%2020260622204725.png)
示例的图表标题使用英文，以避免本地环境缺少中文字体时出现方框。配置中文字体后，可以将标题改成中文。

## 3.15 时间数据中的四类常见问题

### 时间没有排序

如果K线顺序混乱，`pct_change()`会把错误的两根K线放在一起比较。

```python
df = df.sort_index()
```

### 出现重复时间

同一个时间点出现两条K线，可能导致重复计算。

```python
duplicate_count = df.index.duplicated().sum()
print(f"重复时间数量：{duplicate_count}")
```

处理重复数据前，需要先查明原因，不能默认随便删除一条。

### 中间缺少K线

生成理论上应当存在的时间索引，即可检查缺失时间：

```python
expected_index = pd.date_range(
    start=df.index.min(),
    end=df.index.max(),
    freq="1h",
    tz="UTC",
)

missing_times = expected_index.difference(df.index)
print(missing_times)
```

缺失K线可能来自网络、交易所接口或市场停牌。是否填充以及怎样填充，取决于数据来源和策略，不能一律把缺失价格填成0。

### 使用尚未结束的K线

当前小时或当天还没有结束时，这根K线的最高价、最低价、收盘价和成交量都可能继续变化。使用未完成K线生成信号，会导致回测和实盘结果不一致。

## 3.16 未来函数：时间关系写错了

假设策略规定：当收盘价高于3期均线时持有资产。

```python
df["ma3"] = df["close"].rolling(3).mean()
df["signal"] = df["close"] > df["ma3"]
```

这段代码在当前K线收盘后才能知道信号结果。如果回测同时假设自己已经按照当前收盘价提前成交，就使用了当时尚未完全获得的信息。

最简单的处理方式之一，是把信号向后移动一期：

```python
df["position"] = df["signal"].shift(
    1,
    fill_value=False,
)
```

它表示：这一期收盘后得到的信号，从下一期开始执行。

这不能解决所有成交时点问题，但先把信息产生时间和成交时间错开了：

> 每一个信号都必须说明，我在什么时间获得了这条信息，又能在什么时间以什么价格成交。

未来函数往往不是公式写错，而是时间关系写错。

## 3.17 我算对了吗：用Python检查第二章练习

先手工完成第二章练习，再运行 Python 比较答案。这里的代码用于验算，不代替公式推导。

### 练习一：净收益率

题目：本金1000元，卖出后得到1080元，买卖手续费共8元，滑点损失2元。

```python
principal = 1000
final_money = 1080
fee = 8
slippage = 2

net_profit = final_money - principal - fee - slippage
net_return = net_profit / principal

print(f"净收益：{net_profit:.2f} 元")
print(f"净收益率：{net_return:.2%}")
```

正确结果：

```text
净收益：70.00 元
净收益率：7.00%
```

### 练习二：最大回撤

题目：账户资金依次为：

```text
1000 → 1100 → 1050 → 1300 → 900 → 1000
```

```python
equity = pd.Series([1000, 1100, 1050, 1300, 900, 1000])
peak = equity.cummax()
drawdown = equity / peak - 1

print(f"最大回撤：{drawdown.min():.2%}")
```

正确结果：

```text
最大回撤：-30.77%
```

### 练习三：单利和复利

题目：本金1000元，每期增长5%，连续6期。

```python
principal = 1000
return_rate = 0.05
periods = 6

simple_result = principal * (1 + return_rate * periods)
compound_result = principal * (1 + return_rate) ** periods

print(f"单利结果：{simple_result:.2f} 元")
print(f"复利结果：{compound_result:.2f} 元")
```

正确结果：

```text
单利结果：1300.00 元
复利结果：1340.10 元
```

### 练习四：把风险边界变成参数

这道题没有统一答案。下面的数字只是代码示例，不是推荐的交易标准。

```python
learning_capital = 1000

max_total_loss_rate = 0.10
max_trade_loss_rate = 0.01
drawdown_warning_rate = 0.08

max_total_loss = learning_capital * max_total_loss_rate
max_trade_loss = learning_capital * max_trade_loss_rate
drawdown_warning = learning_capital * drawdown_warning_rate

print(f"学习资金：{learning_capital:.2f} 元")
print(f"最大总亏损：{max_total_loss:.2f} 元")
print(f"单笔最大亏损：{max_trade_loss:.2f} 元")
print(f"回撤预警金额：{drawdown_warning:.2f} 元")
```

将示例数字改成自己能够理解和承担的范围，并写下选择这些数字的理由。

### 练习五：和买入持有比较

题目第一段：某个策略一年收益率为18%，同一时期 BTC 买入持有收益率为25%。

```python
strategy_return = 0.18
benchmark_return = 0.25

excess_return = strategy_return - benchmark_return

print(f"超额收益：{excess_return:.2%}")
print(f"是否跑赢基准：{excess_return > 0}")
```

正确结果：

```text
超额收益：-7.00%
是否跑赢基准：False
```

策略虽然赚了18%，但落后 BTC 买入持有7个百分点。

题目第二段：另一个年份，策略收益率为 -6%，BTC 买入持有收益率为 -28%。

```python
strategy_return = -0.06
benchmark_return = -0.28

excess_return_down_year = strategy_return - benchmark_return

print(f"超额收益：{excess_return_down_year:.2%}")
print(f"是否跑赢基准：{excess_return_down_year > 0}")
```

正确结果：

```text
超额收益：22.00%
是否跑赢基准：True
```

这一次策略仍然亏钱，但比直接持有 BTC 少亏了22个百分点。它是否值得继续研究，还要看回撤、交易成本、样本数量和策略逻辑，但不能只因为结果为负就直接否定。

### 练习六：辨别收益质量

题目中的两个策略如下：

```python
strategies = pd.DataFrame(
    {
        "annual_return": [0.30, 0.16],
        "max_drawdown": [-0.55, -0.12],
        "sharpe_ratio": [0.7, 1.4],
    },
    index=["A", "B"],
)

strategies["return_to_drawdown"] = (
    strategies["annual_return"] / strategies["max_drawdown"].abs()
)

print(strategies)
```

运行后可以看到，策略 A 的年化收益率更高，但最大回撤达到 -55%，夏普比率也更低。策略 B 的年化收益率不如 A，但回撤小得多，夏普比率更高。

如果只是做小资金模拟盘观察，我会先选择 B。代码不能替我做最终判断，但它能把几个指标放在同一张表里，避免只盯着最高收益率。

### 用 `assert` 让程序自动检查答案

`assert`可以理解为程序中的检查题。如果条件不成立，程序就会报错。

```python
assert round(net_profit, 2) == 70.00
assert round(net_return, 4) == 0.07
assert round(compound_result, 2) == 1340.10
assert round(excess_return, 2) == -0.07
assert round(excess_return_down_year, 2) == 0.22
```

如果检查条件本身写错，程序仍然可能把错误答案当成正确答案。Python只会执行规则，不会替人判断金融逻辑是否合理。

## 3.18 本章实践：建立量化计算笔记

新建一个名为 `quant_basics.ipynb` 的 Jupyter 笔记，依次完成：

1. 输入初始资金和最终资金。
2. 输入手续费、滑点和Gas。
3. 计算净收益与净收益率。
4. 输入每期收益率，计算累计收益。
5. 输入一条带时间的资金曲线。
6. 计算历史最高点、当前回撤和最大回撤。
7. 绘制资金曲线和回撤图。
8. 输入策略收益率和基准收益率，计算超额收益。
9. 计算夏普比率和信息比率。
10. 修改数据周期，观察结果如何变化。

这份笔记不连接交易所，也不涉及真实资金。它把前两章的金融概念转换成一套能够运行、修改和重复验证的代码。

## 本章小结

Python在量化研究中的第一项工作，是准确表达公式、重复计算并保存研究过程。自动下单只是它的用途之一。

NumPy负责批量处理数值，Pandas负责把数值、时间和列名组织成表格，Matplotlib负责把资金变化画出来。

时间序列是K线和回测的基础。收益率、复利、最大回撤、基准比较和交易信号，都依赖正确的时间顺序和数据周期。同一个策略换成分钟线、小时线或日线，结果可能完全不同。

因此，每次量化实验都必须记录数据周期、起止时间、时区、缺失数据处理方式、基准选择和信号执行时间。

量化代码要算对公式，也要把每一条信息放在它实际能够被获得的时间点上。

下一章将开始获取第一份真实的BTC行情数据，把本章使用的示例表格替换成来自市场的K线。

## 延伸阅读与资料来源

- [Python 官方教程](https://docs.python.org/3/tutorial/)
- [NumPy：Absolute Basics for Beginners](https://numpy.org/doc/stable/user/absolute_beginners.html)
- [Pandas 官方文档](https://pandas.pydata.org/docs/)
- [Pandas：时间序列与日期功能](https://pandas.pydata.org/docs/user_guide/timeseries.html)
- [Pandas：Series.pct_change](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.pct_change.html)
- [Matplotlib：Quick Start Guide](https://matplotlib.org/stable/users/explain/quick_start.html)
