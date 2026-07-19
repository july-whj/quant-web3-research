# Quant Web3 Research

<p align="center">
  <img src="docs/assets/logo-primary.png" alt="Quant Web3 Research Logo" width="180">
</p>

一个面向初学者的 Web3 量化交易研究项目。这里同时保存书稿、Notebook 和可复用的 Python 模块，用同一份代码解释行情获取、策略信号、回测、交易成本、风险指标与链上数据。

项目目前处于早期阶段。默认用途是学习、研究和模拟交易，不会自动连接真实账户下单，也不提供收益承诺。

## 现在有什么

- `docs/`：第 1—15 章书稿，以及后续系统实践路线。
- `notebooks/`：收益率、复利、时间序列、BTC 行情、双均线、回测和交易成本实验。
- `src/quant_web3/`：行情、链上 RPC、指标、策略、回测与风险计算的基础模块。
- `examples/`：可以从命令行运行的最小示例。
- `tests/`：对核心计算和防未来函数规则的自动检查。
- `apps/web/`：React、TypeScript、Vite 与 Tailwind CSS 研究工作区。
- `apps/api/`：FastAPI、MySQL 8.x、钱包签名登录与研究接口。
- `apps/worker/`：通过 Redis/RQ 执行耗时回测任务。

## 快速开始

需要 Python 3.10 或更高版本。

```bash
cd quant-web3-research
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

运行不需要联网的双均线回测示例：

```bash
python examples/backtest_ma_cross.py
```

启动 Notebook：

```bash
jupyter lab
```

### 启动 Web 研究系统

复制本地配置，并先启动 MySQL 8.x 与 Redis：

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d mysql redis
python scripts/init_db.py
```

分别启动 API 和前端：

```bash
./scripts/run_api.sh
```

```bash
cd apps/web
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`。本地默认使用同步回测模式，不需要单独启动 Worker。需要验证完整队列时，把 `.env` 中的 `JOB_MODE` 改为 `rq`，然后运行：

```bash
./scripts/run_worker.sh
```

也可以一次启动整套容器，完成后访问 `http://localhost:8080`：

```bash
docker compose -f infra/docker-compose.yml up --build
```

获取交易所公开 K 线需要联网：

```bash
python examples/fetch_cex_ohlcv.py --exchange binance --symbol BTC/USDT --timeframe 1d --limit 100
```

## 项目结构

```text
quant-web3-research/
├── apps/web/             # React 研究工作区
├── apps/api/             # FastAPI 接口与数据库模型
├── apps/worker/          # Redis/RQ 回测任务
├── docs/                 # 书稿和研究说明
├── notebooks/            # 按章节组织的实验
├── src/quant_web3/       # 可复用 Python 包
├── examples/             # 命令行示例
├── configs/              # 数据、策略和回测配置
├── data/                 # 本地数据与报告，默认不提交
├── tests/                # 自动测试
├── infra/                # MySQL、Redis 与容器编排
└── scripts/              # 常用开发命令
```

系统各模块的职责、钱包登录边界和数据存储原则见 [系统架构说明](docs/architecture/system-architecture.md)。

## 阅读路线

从 [前言](docs/00-preface.md) 和 [学习路线](docs/00-roadmap.md) 开始。量化基础在 `docs/01-quant-basics/`，Web3 基础在 `docs/02-web3-basics/`。第 16—23 章会随着系统模块实现逐步补全，当前计划见 [系统实践大纲](docs/03-system-practice/README.md)。

## 安全边界

- 研究结果不等于未来收益，回测也不能证明策略可以稳定赚钱。
- 默认只读取公开数据。项目不会要求助记词或私钥。
- API Key 只能通过本地环境变量提供，禁止提交 `.env`、密钥文件或真实账户信息。
- 在接入实盘前，应先完成单元测试、历史回测和模拟交易，并设置仓位、止损、单日亏损与异常停机规则。

完整说明见 [DISCLAIMER.md](DISCLAIMER.md) 和 [SECURITY.md](SECURITY.md)。

## 路线图

当前目标是完成一个能被读者检查的研究闭环：获取数据，生成信号，执行回测，扣除成本，计算回撤，输出报告。之后再加入链上事件数据、模拟交易、风险控制和监控。

项目采用 MIT License。提交问题或代码前，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
