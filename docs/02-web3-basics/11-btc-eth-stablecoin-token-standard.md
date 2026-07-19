---
aliases:
  - 第十一章 BTC ETH 稳定币与 Token 标准
tags:
  - 书稿
  - Web3
  - Token
status: 初稿
chapter: 11
---

# 第十一章：BTC、ETH、稳定币与 Token 标准

Web3 市场里，很多资产都显示成一个交易符号：BTC、ETH、USDT、USDC、WETH、DAI、UNI。

交易界面把它们放在同一类列表里，但底层并不相同。

有的是某条链的原生资产，有的是智能合约 Token，有的是稳定币，有的是封装资产，有的是 NFT 或多资产标准下的资产。

做量化研究时，不能只记录资产符号。符号相同，不代表链相同、合约相同、风险相同。

## 11.1 原生资产和 Token 的区别

原生资产是某条链自身的资产。

例如：

```text
Bitcoin 网络的 BTC
Ethereum 主网的 ETH
BNB Chain 的 BNB
Polygon 的 POL / MATIC 历史资产体系
```

原生资产通常用于支付该链上的交易费用。

Token 则通常是部署在某条链上的智能合约资产。比如以太坊上的 USDT、USDC、UNI，大多是 ERC-20 Token。

可以这样理解：

```text
链：运行环境
原生资产：这条链自己的燃料和资产
Token：部署在链上的合约资产
```

这个区别会影响交易成本。你可能有很多 USDT，但如果没有该链的原生 Gas 资产，就无法转出这笔 USDT。

## 11.2 BTC：比特币网络的原生资产

BTC 是比特币网络的原生资产。

比特币网络的设计重点是点对点电子现金、交易验证和防止双花。它没有以太坊那样的通用智能合约账户模型。

BTC 常被市场当作加密资产的核心参考资产。很多交易者观察 BTC 趋势来判断整体风险偏好。

但要注意，交易所账户里的 BTC、比特币主网上的 BTC、其他链上的封装 BTC，不是同一个层面的东西。

例如 WBTC 是以太坊等链上的封装 BTC。它的价格通常跟随 BTC，但它还包含托管、铸造、赎回、合约和链上流动性风险。

做数据分析时，至少区分：

```text
比特币主网 BTC
CEX 账户余额中的 BTC
其他链上的封装 BTC
永续合约或期货中的 BTC 敞口
```

同样叫 BTC，数据来源和风险边界可能完全不同。

## 11.3 ETH：资产，也是执行成本

ETH 是以太坊主网的原生资产。

它有两个角色。

第一，ETH 是可交易资产。

第二，ETH 是以太坊上支付 Gas 的资产。

用户转账、授权、调用合约、部署合约，都需要消耗 Gas。Gas 费用通常用 ETH 支付。

这使 ETH 和普通 ERC-20 Token 不同。

如果地址里只有 USDT，没有 ETH，就可能无法把 USDT 转走。因为 USDT 转账本身是一笔合约调用，也需要 ETH 支付 Gas。

其他链也有类似规则。BNB Chain 需要 BNB，Polygon 需要对应原生 Gas 资产，Arbitrum 上的 Gas 也用 ETH 计价。

量化策略如果涉及链上执行，就必须记录“交易资产”和“Gas 资产”两类余额。

## 11.4 稳定币是什么

稳定币通常试图让价格接近某种法币，最常见的是美元。

交易中常见稳定币包括 USDT、USDC、DAI 等。

稳定币的主要作用是：

```text
交易计价
资金暂存
跨平台结算
链上协议抵押或借贷
策略收益统计
```

稳定币让交易者不必每次都回到法币账户，也方便在 CEX、DEX、借贷协议和跨链桥之间移动资金。

但稳定币不等于没有风险。

常见风险包括：

```text
发行方信用风险
储备资产风险
脱锚风险
合约风险
冻结或黑名单风险
所在链的安全风险
流动性不足风险
```

如果回测默认 1 USDT 永远等于 1 美元，这是一种简化假设。

对普通 BTC/USDT 日线回测，这个假设通常影响不大。对稳定币套利、跨链资金搬运、DeFi 借贷和低收益策略，稳定币偏离会直接影响结果。

## 11.5 同一个稳定币可以在多条链上存在

USDT 可以存在于以太坊、Tron、BNB Chain 等多条链。

这些 USDT 价格接近，符号相同，但转账网络、合约地址、手续费和确认规则不同。

转账时必须同时确认：

```text
资产符号
所在链
合约地址
充值网络
提现网络
手续费
到账确认数
```

把以太坊 USDT 转到只支持 Tron USDT 的地址，可能导致资产无法到账。

对程序化数据来说，资产标识不能只写 `USDT`。至少要写：

```text
chain
chain_id
token_symbol
contract_address
decimals
```

否则后续聚合数据时，很容易把不同链上的资产混在一起。

## 11.6 ERC-20：同质化 Token 标准

ERC-20 是以太坊生态中最常见的同质化 Token 标准。

同质化的意思是：同一种 Token 的每一单位可以互相替代。1 个 USDC 和另 1 个 USDC 没有编号差异。

ERC-20 合约通常提供这些能力：

```text
查询总供应量
查询地址余额
转账
授权第三方地址使用 Token
查询授权额度
```

几个方法尤其重要：

| 方法 | 含义 |
|---|---|
| `balanceOf` | 查询某个地址余额 |
| `transfer` | 从自己地址转出 Token |
| `approve` | 授权某个地址或合约使用 Token |
| `allowance` | 查询授权额度 |
| `transferFrom` | 被授权方从某地址转出 Token |

DEX 交易中常见流程是：

```text
用户先 approve 路由合约
路由合约再通过 transferFrom 转走用户 Token
合约完成兑换
用户收到另一种 Token
```

所以，ERC-20 的授权机制既是交易基础，也是安全风险来源。

## 11.7 decimals、symbol 和合约地址

分析 Token 时，不能只看 `symbol`。

`symbol` 只是符号，不保证唯一。任何人都可以部署一个符号相同的假 Token。

真正要确认的是合约地址。

还要确认 `decimals`，也就是 Token 精度。

链上原始数量通常是整数。钱包和区块浏览器会根据 decimals 把整数转换成人类可读数量。

例如：

```text
原始数量：1000000
decimals：6
实际显示：1.000000
```

如果 decimals 是 18，同样的 `1000000` 就是非常小的一部分 Token。

做量化数据清洗时，decimals 错了，收益、成交量、资金流都会错。

因此，Token 元数据至少要包括：

```text
chain
contract_address
symbol
name
decimals
是否为官方合约
是否有多个链版本
```

## 11.8 ERC-721 与 ERC-1155

ERC-721 常用于 NFT。

非同质化的意思是：每个 Token 都有独立编号。一个 NFT 和另一个 NFT 不完全等价。

ERC-1155 可以在同一个合约中管理多类资产，既可以表示同质化资产，也可以表示非同质化资产或半同质化资产。

本书主要研究交易、资金流、DEX、稳定币和 ERC-20 Token。NFT 和 ERC-1155 不会成为前期重点。

但读者至少要知道：区块浏览器里的 Token 记录不一定都是 ERC-20。不同标准的数据结构和事件解析方式不同。

## 11.9 Wrapped Token 和跨链资产

Wrapped Token 可以理解为某种资产在另一套环境中的映射。

最常见例子是 WETH。

ETH 是以太坊原生资产，不完全符合 ERC-20 标准。为了让 ETH 更方便地和 ERC-20 协议交互，用户可以把 ETH 包装成 WETH。WETH 是 ERC-20 Token，可以进入许多 DeFi 合约。

WBTC 则是 BTC 在其他链上的封装表示。它通常涉及托管或跨链机制。

Wrapped Token 的重点不是名字，而是兑换关系和风险来源。

需要问：

```text
原资产是什么？
封装资产在哪条链？
谁负责托管或铸造？
如何赎回？
是否有足够流动性？
是否存在脱锚风险？
```

回测中如果把 WBTC 完全等同于 BTC，也要写明这是一种简化。

## 11.10 对量化研究的影响

资产分类错误，会直接影响策略结果。

常见错误包括：

- 把不同链上的 USDT 合并统计。
- 把假 Token 当成官方 Token。
- 忽略 decimals，导致成交量放大或缩小。
- 把 WETH 当作 ETH，却忘记兑换和合约风险。
- 把稳定币当作无风险美元。
- 只看 Token 符号，不记录合约地址。

后续建立数据表时，建议把资产标识设计成组合字段，而不是单独一个 symbol：

```text
chain_id
chain_name
contract_address
native_or_token
symbol
decimals
```

原生资产没有 Token 合约地址，可以用固定规则标记，例如 `native`。

## 本章实践

选择三个资产，分别记录它们的信息：

```text
资产 1：BTC
所在环境：Bitcoin 主网 / CEX / 封装资产
是否原生资产：
是否有合约地址：
主要风险：

资产 2：ETH 或 WETH
所在链：
是否用于支付 Gas：
如果是 WETH，合约地址：
decimals：

资产 3：USDT 或 USDC
所在链：
合约地址：
decimals：
是否有其他链版本：
是否存在冻结、脱锚或合约风险：
```

重点不是收集越多越好，而是训练自己不要只看资产符号。

## 本章小结

BTC、ETH、稳定币和 Token 都可以交易，但底层含义不同。

BTC 是比特币网络的原生资产。ETH 是以太坊的原生资产，也是支付 Gas 的资产。稳定币常用于计价和结算，但仍有发行、储备、脱锚、冻结和合约风险。

ERC-20 让同质化 Token 有统一接口，授权机制让 DEX 交易成为可能，也带来风险。

对 Web3 量化研究来说，资产标识必须包含链、合约地址和精度。只记录 symbol，不够。

## 延伸阅读与资料来源

- [Bitcoin Whitepaper](https://bitcoin.org/bitcoin.pdf)
- [Ethereum.org：What is ether?](https://ethereum.org/eth/)
- [Ethereum Developers Docs：ERC-20 Token Standard](https://ethereum.org/developers/docs/standards/tokens/erc-20/)
- [Ethereum Developers Docs：ERC-721](https://ethereum.org/developers/docs/standards/tokens/erc-721/)
- [Ethereum Developers Docs：ERC-1155](https://ethereum.org/developers/docs/standards/tokens/erc-1155/)
