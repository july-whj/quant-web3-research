---
aliases:
  - Web3量化交易入门大纲
  - 写书大纲
tags:
  - 学习路线
  - 量化交易
  - Web3
status: 进行中
---

# 从零开始学 Web3 量化交易

项目定位：**开源 Web3 量化交易研究系统**

暂定书名：**《从零开始学 Web3 量化交易：Python、回测、链上数据与模拟盘实践》**

开源目标：用书稿讲清楚概念，用代码跑通实验，最终形成一套可复现、可扩展的 Web3 量化交易研究系统。

## 项目定位

- [ ] 顶层路线：[项目定位与开源路线](00-project-positioning.md)

## 第一部分：交易与量化基础

- [ ] 第 1 章：[什么是量化交易](01-quant-basics/01-what-is-quant-trading.md)
- [ ] 第 2 章：[收益率、回撤、复利与风险](01-quant-basics/02-return-drawdown-compounding-risk.md)
- [ ] 第 3 章：[Python 与时间序列](01-quant-basics/03-python-and-time-series.md)
- [ ] 第 4 章：[获取第一份 BTC 行情数据](01-quant-basics/04-get-first-btc-market-data.md)
- [ ] 第 5 章：[BTC 现货双均线策略](01-quant-basics/05-btc-spot-ma-cross-strategy.md)
- [ ] 第 6 章：[完成第一次回测](01-quant-basics/06-first-backtest.md)
- [ ] 第 7 章：[加入手续费、滑点与资金曲线](01-quant-basics/07-fees-slippage-equity-curve.md)
- [ ] 第 8 章：[识别未来函数、幸存者偏差和过拟合](01-quant-basics/08-lookahead-survivorship-overfitting.md)

### 里程碑 M1

独立完成一个只做现货多头的 BTC 双均线策略，并能解释收益率、最大回撤和交易成本。

## 第二部分：Web3 基础

- [ ] 第二部分总大纲：[Web3 基础大纲](02-web3-basics/README.md)
- [ ] 第 9 章：[区块链、区块、交易与共识](02-web3-basics/09-blockchain-block-transaction-consensus.md)
- [ ] 第 10 章：[账户、钱包、私钥和助记词](02-web3-basics/10-account-wallet-private-key-seed-phrase.md)
- [ ] 第 11 章：[BTC、ETH、稳定币与 Token 标准](02-web3-basics/11-btc-eth-stablecoin-token-standard.md)
- [ ] 第 12 章：[CEX 与 DEX](02-web3-basics/12-cex-and-dex.md)
- [ ] 第 13 章：[公链、Chain ID、Gas 与确认](02-web3-basics/13-chain-id-gas-confirmation.md)
- [ ] 第 14 章：[智能合约、RPC 节点与区块浏览器](02-web3-basics/14-contract-rpc-explorer.md)
- [ ] 第 15 章：[预言机、跨链桥与链上安全](02-web3-basics/15-oracle-bridge-security.md)

### 里程碑 M2

能安全创建测试钱包，读取一笔链上交易，并解释 Gas、确认、Token 合约和授权的含义。

## 第三部分： Web3 量化实践

- [ ] 第三部分总大纲：[系统实践大纲](03-system-practice/README.md)
- [x] 第 16 章：[开源系统的整体架构与目录设计](03-system-practice/16-open-source-system-architecture.md)
- [x] 第 17 章：[CEX 行情数据模块：K 线、成交与订单簿](03-system-practice/17-cex-market-data-module.md)
- [ ] 第 18 章：链上数据模块：区块、交易、回执与事件日志
- [ ] 第 19 章：数据标准化与指标模块：时间序列、Token 与资金流
- [ ] 第 20 章：策略模块：规则、参数、信号与配置文件
- [ ] 第 21 章：回测引擎模块：成交、成本、资金曲线与报告
- [ ] 第 22 章：模拟盘模块：虚拟账户、订单、持仓与风控
- [ ] 第 23 章：监控与复盘模块：告警、日志、看板与开源发布

### 里程碑 M3

完成一套最小可运行的开源研究系统：能拉取数据、运行策略、完成回测、输出报告，并支持模拟盘记录，不涉及真实资金自动交易。

## 第四部分：风险、产品化与真实运行边界

- [ ] 第 24 章：风险系统：仓位、波动率、最大亏损与风控规则
- [ ] 第 25 章：密钥与权限安全：API Key、私钥、授权和白名单
- [ ] 第 26 章：真实执行边界：CEX API、DEX 交易与失败订单
- [ ] 第 27 章：任务调度、日志、告警与故障恢复
- [ ] 第 28 章：样本外验证、参数稳定性与策略验收
- [ ] 第 29 章：Web 平台原型：策略配置、回测看板与模拟盘
- [ ] 第 30 章：开源项目发布：README、许可证、贡献指南与风险声明
- [ ] 第 31 章：托管版与商业化边界：卖服务，不卖收益承诺
- [ ] 第 32 章：失败实验、常见误区与下一阶段路线

### 里程碑 M4

形成一套可复现的开源研究闭环，并把书稿、代码、示例、测试和风险声明整理成可以公开发布的项目。

## 推荐学习顺序

```text
市场与 Python 基础
→ CEX 公开行情
→ BTC 现货策略回测
→ 手续费、滑点与风险控制
→ Web3 与链上数据基础
→ 开源系统架构
→ 数据模块
→ 策略模块
→ 回测引擎
→ 模拟盘
→ 监控与复盘
→ 测试网和模拟盘
→ Web 平台原型
```

## 每章完成标准

- [ ] 能用自己的话解释核心概念
- [ ] 有一个能够运行或复查的例子
- [ ] 写明数据来源、时间范围和参数
- [ ] 写明手续费、Gas、滑点等成本
- [ ] 记录错误、修正过程和局限性
- [ ] 区分事实、推测与实验结论
- [ ] 列出资料来源
- [ ] 对应一个系统模块或可运行实验
- [ ] 能说明该模块输入、处理过程和输出

## 暂不纳入入门阶段

- 杠杆和合约实盘
- 高频交易与抢跑程序
- 新币自动交易
- 策略订阅和自动跟单
- 用户资产托管
- 默认开启实盘交易
- 复杂期权定价与随机微积分
- 使用深度学习直接预测价格
- 未经验证的套利机器人
