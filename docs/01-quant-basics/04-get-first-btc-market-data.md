---
aliases:
  - 第四章 获取第一份BTC行情数据
tags:
  - 书稿
  - BTC
  - 行情数据
  - CCXT
  - Pandas
status: 初稿
chapter: 4
---

# 第四章：获取第一份 BTC 行情数据

## 4.1 为什么第一份数据选择 BTC

前几章一直在使用手工构造的数据：几笔资金变化、几行 K 线、几组收益率。它们适合理解公式，却还不是市场本身。

从这一章开始，数据来自真实市场。

第一份数据选择 BTC，不是因为 BTC 最容易赚钱，也不是因为后面的策略一定要只交易 BTC。原因更基础：BTC 是加密市场中最重要、最容易获得数据、最适合作为入门基准的资产。

对很多 Web3 交易者来说，BTC 像一支市场温度计。市场风险偏好升高时，BTC 往往最先被观察；市场恐慌时，BTC 也通常是判断大盘状态的核心资产之一。虽然不同赛道会有各自的行情，比如 DeFi、Layer2、AI、Meme 或稳定币相关资产，但 BTC 的走势仍然会影响很多人的仓位和情绪。

第二章讲过基准。判断一套 Web3 策略是否有价值，不能只看它有没有赚钱，还要看它和谁比较。如果一个策略长期跑不赢 BTC 买入持有，同时又承担了更高的回撤和交易成本，那么它的复杂度就需要被重新审视。

因此，本章先获取 BTC 数据。不是为了立刻预测它，而是为了建立一条最小的数据处理路径：

```text
获取真实行情
→ 转成 Pandas 表格
→ 统一时间和字段
→ 保存到本地
→ 画图检查
→ 计算基础指标
```

这条路径跑通以后，后面换成 ETH、BNB、SOL，或者换成其他交易所数据，方法才有扩展的基础。

## 4.2 BTC、Web3 和加密市场的关系

BTC 是最早被广泛采用的加密资产。比特币白皮书把它描述为一种点对点电子现金系统，重点是让两个参与者可以在没有传统金融中介的情况下完成价值转移。

今天讨论 Web3 时，经常会同时提到以太坊、智能合约、DeFi、NFT、DAO、链上身份和各种应用协议。这些内容很多并不发生在 Bitcoin 网络上。Bitcoin 网络本身更专注于 BTC 的发行、转账、区块确认和网络安全；以太坊等公链则扩展出了更复杂的链上应用生态。

所以，BTC 不等于整个 Web3。

但从交易和市场观察的角度看，BTC 仍然是绕不开的资产。很多行情软件、交易所首页、研究报告和市场复盘，都会先看 BTC 的价格、涨跌幅、成交量和波动情况。对初学者来说，从 BTC 开始有三个好处。

第一，数据容易获得。主流交易所几乎都提供 BTC 交易对，K 线数据格式也比较标准。

第二，流动性较好。流动性越好的资产，价格异常和数据断点通常越少，适合作为第一份数据练习。

第三，适合作为基准。后面研究策略时，可以先问一个朴素的问题：这套策略是否比简单持有 BTC 更有价值？

本章只使用 BTC 的交易所行情数据，不涉及真实下单，也不使用 API Key。

## 4.3 什么是行情数据

行情数据不是只有一个价格。

打开交易所或行情软件时，最容易看到的是 BTC 当前价格。但量化研究需要的是一段时间内连续、结构化的数据。最常见的是 K 线，也就是 OHLCV 数据。

一根 K 线通常包含六个字段：

| 字段 | 含义 |
|---|---|
| timestamp | 这根 K 线对应的时间 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |

如果是一根日线 K 线，它表示一天内的开盘价、最高价、最低价、收盘价和成交量。如果是一根小时线 K 线，它表示这一小时内的同一组数据。

第三章已经讲过时间序列。现在可以把手工示例换成真实市场数据。这里有一个小变化：真实数据不会因为我们需要它而变得干净。它可能有缺失，可能时间没有完全对齐，也可能不同来源之间存在差异。

所以，获取数据只是第一步。拿到数据后，还要检查字段、时间、周期和来源。

## 4.4 BTC 行情数据可以从哪里来

BTC 数据有很多来源。初学时不需要全部使用，但要先知道它们的区别。

### 交易所数据

交易所数据来自真实交易市场。常见来源包括 Binance、OKX、Coinbase、Bybit、Kraken 等。

这类数据可以回答：

```text
BTC/USDT 在某个交易所的成交价格是多少？
某个时间段内开盘、最高、最低、收盘分别是多少？
这一段时间成交了多少 BTC？
```

交易所数据最适合做交易策略和回测。因为如果策略将来要在交易所执行，回测时就应该尽量使用接近交易执行场所的数据。

但交易所之间的数据不一定完全一致。Binance 的 BTC/USDT、OKX 的 BTC/USDT、Coinbase 的 BTC/USD，价格可能非常接近，但不会每一秒都完全一样。成交量差异更明显，因为每个交易所的用户、流动性和交易结构都不同。

### 行情聚合平台

行情聚合平台会从多个市场收集数据，再进行展示或加工。常见平台包括 CoinGecko、CoinMarketCap、TradingView、Yahoo Finance 等。

这类平台适合看大盘、做展示、做粗粒度研究。它们通常使用方便，图表也清楚。但聚合数据可能经过计算，不一定等同于某个具体交易所的可成交价格。

如果只是写一篇市场复盘，聚合平台很方便。如果要做交易策略回测，就需要更谨慎地记录数据来源和计算方式。

### 链上节点数据

链上节点数据来自区块链本身。以 Bitcoin Core 节点为例，它可以读取区块、交易、区块高度、交易输出、确认数等信息。

这类数据回答的是另一类问题：

```text
某个区块里有哪些交易？
一笔交易是否已经确认？
某段时间链上转账活跃不活跃？
手续费水平是否升高？
```

它和交易所 K 线不是同一种数据。

可以简单区分：

```text
交易所数据：BTC 多少钱、成交了多少
链上数据：Bitcoin 网络里发生了哪些区块和交易事件
```

链上数据可以辅助理解市场。例如交易所流入流出、大额转账、矿工行为和链上手续费变化，都可能和市场情绪有关。但链上节点不会直接告诉我 Binance 上 BTC/USDT 的一分钟 K 线。

### 专业链上数据平台

专业链上数据平台会把原始链上数据进一步整理成指标。常见平台包括 Glassnode、CryptoQuant、Coinglass、Dune、Nansen 等。

这些平台可能提供交易所净流入、长期持有者变化、稳定币供应、合约持仓、资金费率、大户地址变化等指标。它们对后续研究很有价值，但不适合作为第一份入门数据。

本章的目标更简单：先拿到一份 BTC/USDT K 线，并能在本地保存、读取和检查。

## 4.5 第一份数据应该选哪种来源

本章使用 CCXT 获取交易所公开 K 线数据。

本章选择：

```text
数据类型：交易所公开 K 线
交易对：BTC/USDT
周期：1d（日线）
工具：CCXT
权限：不需要 API Key
```

CCXT 是一个统一的加密货币交易所 API 库。它把很多交易所的接口封装成相似的方法。这样做的好处是，今天可以用 Binance，后面也可以比较容易地切换到 OKX、Kraken 或其他交易所。

第一份数据不追求最全，而是追求可理解、可重复、可验证。

日线比分钟线更适合作为第一份数据。分钟线数量多，容易遇到接口分页、请求限制和缺失处理。日线数据少一些，适合先把流程跑通。

这章的代码只读取公开行情，不读取账户，不创建订单，不需要填写 API Key。这样可以先把数据学习和交易权限隔离开。

## 4.6 安装 CCXT

如果已经在第三章创建了虚拟环境，可以继续使用同一个环境。

进入代码实验目录：

```bash
cd "05-代码与实验"
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

安装 CCXT：

```bash
python -m pip install ccxt
```

如果使用项目里的 `requirements.txt`，可以执行：

```bash
python -m pip install -r requirements.txt
```

启动 Jupyter：

```bash
python -m jupyterlab
```

本章建议新建一个笔记：

```text
notebooks/chapter04/btc_market_data.ipynb
```

如果暂时不创建 notebook，也可以在 Jupyter 中先新建一个临时文件，确认代码能跑通后再整理。

## 4.7 用 CCXT 获取 BTC K 线

先写最小代码。

```python
import ccxt

exchange = ccxt.binance({
    "enableRateLimit": True,
})

symbol = "BTC/USDT"
timeframe = "1d"
limit = 1000

ohlcv = exchange.fetch_ohlcv(
    symbol=symbol,
    timeframe=timeframe,
    limit=limit,
)

print(type(ohlcv))
print(len(ohlcv))
print(ohlcv[0])
```

`exchange = ccxt.binance()` 表示创建一个 Binance 交易所对象。`enableRateLimit=True` 表示让 CCXT 尽量遵守交易所请求频率限制，避免短时间内请求过快。

`fetch_ohlcv()` 用来获取 K 线。这里的三个参数分别是：

| 参数 | 含义 |
|---|---|
| symbol | 交易对，例如 BTC/USDT |
| timeframe | K 线周期，例如 1d、1h、15m |
| limit | 返回多少根 K 线 |

CCXT 返回的数据是一组列表。每一行通常是：

```text
[
    timestamp,
    open,
    high,
    low,
    close,
    volume
]
```

其中 `timestamp` 是毫秒级 UTC 时间戳。它还不是人能直接阅读的时间，需要转换。

这里把 `limit` 设置为 1000，是为了给后面的 MA20/MA60 策略留下足够长的观察区间。如果只获取 100 根日线，前 59 根还无法计算 MA60，真正参与回测的数据只剩 40 根左右，很容易出现没有任何买入信号的情况。

如果 Binance 在当前网络环境下不可访问，可以改用其他 CCXT 支持的交易所，例如：

```python
exchange = ccxt.okx({
    "enableRateLimit": True,
})
```

不同交易所支持的交易对不完全一样。如果 `BTC/USDT` 不存在，需要查看该交易所支持的市场，或者换成交易所实际支持的交易对。

## 4.8 把 CCXT 数据转换成 Pandas 表格

列表适合传输，不适合分析。接下来把它转成 Pandas DataFrame。

```python
import pandas as pd

columns = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

df = pd.DataFrame(ohlcv, columns=columns)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    unit="ms",
    utc=True,
)

df = df.set_index("timestamp")
df = df.sort_index()

print(df.head())
print(df.tail())
```

这段代码做了几件事。

第一，把原始列表放进 DataFrame。

第二，给每一列起清楚的名字。

第三，把毫秒时间戳转换成 UTC 时间。

第四，把时间设置为索引，并按时间排序。

处理完以后，表格应该类似这样：

| timestamp | open | high | low | close | volume |
|---|---:|---:|---:|---:|---:|
| 2026-03-15 00:00:00+00:00 | ... | ... | ... | ... | ... |
| 2026-03-16 00:00:00+00:00 | ... | ... | ... | ... | ... |

行情数据中的价格和成交量必须是数字。可以检查字段类型：

```python
print(df.dtypes)
```

如果某些字段是 `object`，说明它可能还保留为文本。可以统一转换：

```python
numeric_columns = ["open", "high", "low", "close", "volume"]
df[numeric_columns] = df[numeric_columns].astype(float)

print(df.dtypes)
```

## 4.9 检查这份数据是否可用

拿到数据后，不要马上计算策略。先做几项检查。

### 检查时间范围

```python
print("开始时间：", df.index.min())
print("结束时间：", df.index.max())
print("数据行数：", len(df))
```

这一步确认数据覆盖了哪一段时间。

### 检查时间顺序

```python
print("时间是否递增：", df.index.is_monotonic_increasing)
```

如果结果是 `False`，说明数据没有按时间从早到晚排列，需要重新排序。

### 检查重复时间

```python
duplicate_count = df.index.duplicated().sum()
print("重复时间数量：", duplicate_count)
```

K 线数据通常不应该出现重复时间。如果有重复，需要先查原因。

### 检查缺失值

```python
print(df.isna().sum())
```

如果 open、high、low、close 或 volume 有缺失，需要判断是接口问题、交易所问题，还是数据转换过程中出现了错误。

### 检查价格关系

一根正常 K 线应该满足：

```text
最高价 >= 开盘价、收盘价、最低价
最低价 <= 开盘价、收盘价、最高价
```

可以用代码检查：

```python
invalid_price_rows = df[
    (df["high"] < df[["open", "close", "low"]].max(axis=1))
    | (df["low"] > df[["open", "close", "high"]].min(axis=1))
]

print("价格关系异常行数：", len(invalid_price_rows))
```

这类检查看起来基础，但很重要。很多回测问题不是策略逻辑错了，而是数据一开始就没有被检查。

## 4.10 保存第一份 BTC 数据

如果每次练习都重新请求交易所接口，会遇到几个问题。

第一，接口可能临时失败。

第二，交易所可能有请求频率限制。

第三，不同时间请求到的数据范围可能不同。

第四，无法确认后续实验使用的是不是同一份数据。

因此，拿到第一份数据后，应当保存到本地。

```python
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

file_path = data_dir / "btc_usdt_1d.csv"
df.to_csv(file_path)

print(file_path)
```

保存后再读取一次，确认文件可以被重新使用：

```python
df_saved = pd.read_csv(
    file_path,
    parse_dates=["timestamp"],
    index_col="timestamp",
)

print(df_saved.head())
print(df_saved.dtypes)
```

这里有一个细节：`to_csv()` 保存时间索引时，默认会把索引列名一起写进去。如果前面索引名称是 `timestamp`，读取时就可以用 `parse_dates=["timestamp"]` 和 `index_col="timestamp"` 重新恢复时间索引。

如果读取时报错，先检查 CSV 第一行的列名。不要急着改策略代码。

## 4.11 画出 BTC 收盘价曲线

数据能够保存和读取以后，可以画出第一张真实市场图。

```python
import matplotlib.pyplot as plt

ax = df["close"].plot(
    figsize=(12, 6),
    title="BTC/USDT Close Price - 1D",
)

ax.set_xlabel("Time")
ax.set_ylabel("Price")
ax.grid(True)

plt.show()
```

![BTC 行情数据示例](../assets/Pasted%20image%2020260623135230.png)
这张图只画收盘价。它的作用不是预测涨跌，而是确认三件事：

```text
时间顺序是否正确
价格是否大致连续
数据是否能被正常读取和展示
```

图表标题暂时使用英文，是为了避免本地环境缺少中文字体时出现乱码。后面如果配置好中文字体，可以改成中文标题。

## 4.12 用第二、三章的方法检查 BTC 数据

现在可以把前几章的知识用到真实 BTC 数据上。

先计算每日收益率：

```python
df["return"] = df["close"].pct_change(fill_method=None)

print(df[["close", "return"]].tail())
```

再计算累计收益率，也就是从第一天买入并持有到最后一天的收益变化：

```python
df["growth"] = (1 + df["return"].fillna(0)).cumprod()
df["cumulative_return"] = df["growth"] - 1

final_return = df["cumulative_return"].iloc[-1]

print(f"BTC 买入持有收益率：{final_return:.2%}")
```

接着计算最大回撤。

这里把初始资金设为 1，只观察 BTC 买入持有的资金曲线：

```python
equity = df["growth"]
historical_peak = equity.cummax()
drawdown = equity / historical_peak - 1

max_drawdown = drawdown.min()
trough_time = drawdown.idxmin()
peak_time = equity.loc[:trough_time].idxmax()

print(f"最大回撤：{max_drawdown:.2%}")
print(f"回撤高点：{peak_time}")
print(f"回撤低点：{trough_time}")
```

最后把资金曲线和回撤画出来：

```python
fig, axes = plt.subplots(
    2,
    1,
    figsize=(12, 8),
    sharex=True,
)

equity.plot(
    ax=axes[0],
    label="Buy and Hold Equity",
)

historical_peak.plot(
    ax=axes[0],
    linestyle="--",
    label="Historical Peak",
)

axes[0].set_title("BTC/USDT Buy and Hold Equity")
axes[0].set_ylabel("Equity")
axes[0].legend()
axes[0].grid(True)

drawdown.plot(
    ax=axes[1],
    color="red",
)

axes[1].fill_between(
    drawdown.index,
    drawdown.values,
    0,
    color="red",
    alpha=0.2,
)

axes[1].set_title("BTC/USDT Drawdown")
axes[1].set_ylabel("Drawdown")
axes[1].grid(True)

plt.tight_layout()
plt.show()
```

![BTC K 线示例](../assets/Pasted%20image%2020260623135259.png)
这一步很关键。BTC 买入持有本身就是一个基准。后面写双均线策略时，策略收益、最大回撤和交易次数都要和这个基准放在一起看。

如果策略没有明显改善收益或回撤，只是让交易次数变多、手续费变高，那么它并不一定比简单持有更好。

## 4.13 不同数据源为什么可能不一样

当开始比较不同平台的数据时，很容易发现一个现象：BTC 的价格看起来差不多，但细节并不完全一样。

这不是异常。常见原因有几个。

第一，交易所不同。Binance、OKX、Coinbase 的用户、订单簿和流动性不同，同一时刻的成交价可能略有差异。

第二，交易对不同。BTC/USDT、BTC/USDC、BTC/USD 使用的报价资产不同。稳定币本身也可能出现轻微偏离。

第三，K 线切分时间不同。日线如果按 UTC 切分，和按北京时间切分，开盘价、收盘价和最高最低价都可能不同。

第四，成交量口径不同。有些平台显示基础资产成交量，有些平台显示报价资产成交额，有些聚合平台会合并多个市场。

第五，数据源可能经过加工。聚合平台为了展示大盘价格，可能使用加权平均或其他计算方式。

因此，每次实验都要记录：

```text
数据来源：Binance via CCXT
交易对：BTC/USDT
周期：1d
时间范围：开始时间至结束时间
时区：UTC
获取时间：实际运行代码的时间
```

没有数据来源记录的回测，很难复现。

## 4.14 本章实践

本章实践的目标，是把第一份 BTC 行情数据保存到本地，并完成一次基础检查。

建议在 `05-代码与实验` 中完成以下步骤：

1. 新建 `notebooks/chapter04/btc_market_data.ipynb`。
2. 使用 CCXT 创建交易所对象。
3. 获取 BTC/USDT 日线 K 线。
4. 转成 Pandas DataFrame。
5. 将 timestamp 转成 UTC 时间索引。
6. 检查时间范围、重复时间、缺失值和价格关系。
7. 保存为 `data/btc_usdt_1d.csv`。
8. 重新读取 CSV。
9. 画出 BTC 收盘价曲线。
10. 计算买入持有收益率和最大回撤。
11. 记录数据来源、交易对、周期、时间范围和时区。

完成这些步骤后，才算真正拿到了第一份可使用的数据。

## 本章小结

BTC 是学习 Web3 量化交易时最适合先使用的资产之一。它数据充足，流动性较好，也常被用作加密市场的重要基准。

行情数据和链上数据不是一回事。交易所 K 线记录的是价格和成交量，链上节点数据记录的是区块和交易事件。两者都重要，但本章先处理 K 线。

CCXT 让不同交易所的数据获取方式更统一。使用它获取 BTC/USDT 日线，可以把重点放在数据结构、时间索引、保存和检查上，而不是一开始就陷入不同交易所 API 的细节。

从这一章开始，后面的策略研究会建立在真实市场数据上。策略是否有效，先取决于数据是否可靠。

下一章将使用这份 BTC 数据，编写第一个只做现货多头的双均线策略。

## 延伸阅读与资料来源

- [Bitcoin 白皮书：Bitcoin: A Peer-to-Peer Electronic Cash System](https://bitcoin.org/bitcoin.pdf)
- [CCXT 官方文档](https://docs.ccxt.com/)
- [CCXT Manual：OHLCV Candlestick Charts](https://github.com/ccxt/ccxt/wiki/manual#ohlcv-candlestick-charts)
- [Binance Spot API：Kline/Candlestick data](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#klinecandlestick-data)
- [Bitcoin Core RPC：getblock](https://developer.bitcoin.org/reference/rpc/getblock.html)
