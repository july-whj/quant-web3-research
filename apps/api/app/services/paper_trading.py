from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quant_web3.paper_trading import (
    PaperFillEstimate,
    build_grid_levels,
    estimate_cex_limit_fill,
    estimate_cex_market_fill,
    order_touched_by_candle,
    quantize_amount,
)

from ..models import (
    MarketCandle,
    PaperAccount,
    PaperAccountSnapshot,
    PaperBalance,
    PaperBot,
    PaperBotEvent,
    PaperFill,
    PaperLedgerEntry,
    PaperOrder,
    PaperPosition,
    PaperRiskEvent,
)
from ..schemas.paper import (
    PaperAccountCreate,
    PaperAccountResponse,
    PaperBalanceResponse,
    PaperFundsCreate,
    PaperGridCreate,
    PaperPositionResponse,
)


ZERO = Decimal("0")


class PaperTradingError(ValueError):
    pass


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def base_asset(symbol: str) -> str:
    return symbol.split("/", 1)[0]


def owned_account(db: Session, account_id: str, owner_id: str, *, lock: bool = False) -> PaperAccount:
    statement = select(PaperAccount).where(
        PaperAccount.id == account_id,
        PaperAccount.owner_id == owner_id,
    )
    if lock:
        statement = statement.with_for_update()
    account = db.scalar(statement)
    if account is None:
        raise PaperTradingError("模拟账户不存在")
    return account


def latest_candle(db: Session, account: PaperAccount) -> MarketCandle | None:
    return db.scalar(
        select(MarketCandle)
        .where(
            MarketCandle.exchange == account.exchange,
            MarketCandle.symbol == account.symbol,
            MarketCandle.timeframe == "1m",
            MarketCandle.is_closed.is_(True),
        )
        .order_by(MarketCandle.open_time.desc())
        .limit(1)
    )


def require_latest_candle(db: Session, account: PaperAccount) -> MarketCandle:
    candle = latest_candle(db, account)
    if candle is None:
        raise PaperTradingError(
            f"{account.exchange} {account.symbol} 暂无 1m 闭合 K 线，不能模拟成交"
        )
    return candle


def _balance(db: Session, account_id: str, asset: str, *, lock: bool = True) -> PaperBalance:
    statement = select(PaperBalance).where(
        PaperBalance.account_id == account_id,
        PaperBalance.asset == asset,
    )
    if lock:
        statement = statement.with_for_update()
    balance = db.scalar(statement)
    if balance is None:
        balance = PaperBalance(account_id=account_id, asset=asset, available=ZERO, locked=ZERO)
        db.add(balance)
        db.flush()
    return balance


def _position(db: Session, account: PaperAccount, *, lock: bool = True) -> PaperPosition:
    statement = select(PaperPosition).where(
        PaperPosition.account_id == account.id,
        PaperPosition.symbol == account.symbol,
    )
    if lock:
        statement = statement.with_for_update()
    position = db.scalar(statement)
    if position is None:
        position = PaperPosition(
            account_id=account.id,
            symbol=account.symbol,
            quantity=ZERO,
            average_cost=ZERO,
            realized_pnl=ZERO,
        )
        db.add(position)
        db.flush()
    return position


def _ledger(
    db: Session,
    balance: PaperBalance,
    *,
    entry_type: str,
    amount: Decimal,
    reference_type: str | None = None,
    reference_id: str | None = None,
    description: str | None = None,
) -> None:
    db.add(
        PaperLedgerEntry(
            account_id=balance.account_id,
            asset=balance.asset,
            entry_type=entry_type,
            amount=amount,
            available_after=balance.available,
            locked_after=balance.locked,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )
    )


def _risk_rejection(
    db: Session,
    account: PaperAccount,
    *,
    code: str,
    reason: str,
    snapshot: dict[str, object],
) -> None:
    db.add(
        PaperRiskEvent(
            account_id=account.id,
            decision="rejected",
            code=code,
            reason=reason,
            snapshot=snapshot,
        )
    )
    db.flush()
    raise PaperTradingError(reason)


def create_account(
    db: Session,
    *,
    owner_id: str,
    payload: PaperAccountCreate,
) -> PaperAccount:
    account = PaperAccount(
        owner_id=owner_id,
        name=payload.name,
        exchange=payload.exchange,
        symbol="BTC/USDT",
        base_currency="USDT",
        fee_rate=payload.fee_rate,
        slippage_rate=payload.slippage_rate,
        max_position_pct=payload.max_position_pct,
        max_order_notional=payload.max_order_notional,
    )
    db.add(account)
    db.flush()
    quote = PaperBalance(
        account_id=account.id,
        asset="USDT",
        available=payload.initial_funds,
        locked=ZERO,
    )
    base = PaperBalance(account_id=account.id, asset="BTC", available=ZERO, locked=ZERO)
    db.add_all([quote, base])
    db.flush()
    _ledger(
        db,
        quote,
        entry_type="paper_funds_deposit",
        amount=payload.initial_funds,
        reference_type="account",
        reference_id=account.id,
        description="Initial paper funds",
    )
    _position(db, account)
    return account


def add_paper_funds(
    db: Session,
    *,
    account: PaperAccount,
    payload: PaperFundsCreate,
) -> None:
    if account.status != "active":
        raise PaperTradingError("只有正常状态的模拟账户可以增加资金")
    quote = _balance(db, account.id, account.base_currency)
    quote.available += payload.amount
    _ledger(
        db,
        quote,
        entry_type="paper_funds_deposit",
        amount=payload.amount,
        reference_type="account",
        reference_id=account.id,
        description=payload.note or "Paper funds deposit",
    )


def _account_equity(
    db: Session,
    account: PaperAccount,
    mark_price: Decimal,
) -> Decimal:
    quote = _balance(db, account.id, account.base_currency, lock=False)
    base = _balance(db, account.id, base_asset(account.symbol), lock=False)
    return quote.available + quote.locked + (base.available + base.locked) * mark_price


def _validate_order_risk(
    db: Session,
    account: PaperAccount,
    *,
    side: str,
    quantity: Decimal,
    price: Decimal,
) -> None:
    if account.status != "active":
        _risk_rejection(
            db,
            account,
            code="account_not_active",
            reason="模拟账户当前不可交易",
            snapshot={"status": account.status},
        )
    notional = price * quantity
    if notional > account.max_order_notional:
        _risk_rejection(
            db,
            account,
            code="max_order_notional",
            reason="订单金额超过账户单笔上限",
            snapshot={"notional": str(notional), "limit": str(account.max_order_notional)},
        )
    if side == "buy":
        position = _position(db, account, lock=False)
        equity = _account_equity(db, account, price)
        post_value = (position.quantity + quantity) * price
        if equity <= 0 or post_value / equity > account.max_position_pct:
            _risk_rejection(
                db,
                account,
                code="max_position_pct",
                reason="买入后持仓比例将超过账户限制",
                snapshot={
                    "post_position_value": str(post_value),
                    "equity": str(equity),
                    "limit": str(account.max_position_pct),
                },
            )


def _reserve_limit_order(
    db: Session,
    account: PaperAccount,
    order: PaperOrder,
) -> None:
    assert order.limit_price is not None
    if order.side == "buy":
        balance = _balance(db, account.id, account.base_currency)
        required = quantize_amount(
            order.limit_price * order.quantity * (Decimal("1") + account.fee_rate)
        )
        asset = account.base_currency
    else:
        asset = base_asset(account.symbol)
        balance = _balance(db, account.id, asset)
        required = order.quantity
    if balance.available < required:
        _risk_rejection(
            db,
            account,
            code="insufficient_balance",
            reason=f"可用 {asset} 余额不足",
            snapshot={"required": str(required), "available": str(balance.available)},
        )
    balance.available -= required
    balance.locked += required
    order.reserved_asset = asset
    order.reserved_amount = required
    order.status = "open"
    _ledger(
        db,
        balance,
        entry_type="order_lock",
        amount=-required,
        reference_type="order",
        reference_id=order.id,
        description="Funds locked for limit order",
    )


def _release_reservation(db: Session, order: PaperOrder, *, entry_type: str) -> None:
    if not order.reserved_asset or order.reserved_amount <= 0:
        return
    balance = _balance(db, order.account_id, order.reserved_asset)
    released = min(balance.locked, order.reserved_amount)
    balance.locked -= released
    balance.available += released
    order.reserved_amount = ZERO
    _ledger(
        db,
        balance,
        entry_type=entry_type,
        amount=released,
        reference_type="order",
        reference_id=order.id,
        description="Order reservation released",
    )


def _apply_fill(
    db: Session,
    *,
    account: PaperAccount,
    order: PaperOrder,
    estimate: PaperFillEstimate,
    market_time: datetime,
) -> PaperFill:
    _release_reservation(db, order, entry_type="order_fill_unlock")
    quote = _balance(db, account.id, account.base_currency)
    base = _balance(db, account.id, base_asset(account.symbol))
    position = _position(db, account)

    if estimate.side == "buy":
        required = estimate.quote_amount + estimate.fee_amount
        if quote.available < required:
            raise PaperTradingError("成交时可用 USDT 余额不足")
        old_cost = position.quantity * position.average_cost
        quote.available -= estimate.quote_amount
        _ledger(
            db,
            quote,
            entry_type="trade_spend",
            amount=-estimate.quote_amount,
            reference_type="order",
            reference_id=order.id,
        )
        quote.available -= estimate.fee_amount
        _ledger(
            db,
            quote,
            entry_type="trading_fee",
            amount=-estimate.fee_amount,
            reference_type="order",
            reference_id=order.id,
        )
        base.available += estimate.quantity
        _ledger(
            db,
            base,
            entry_type="trade_receive",
            amount=estimate.quantity,
            reference_type="order",
            reference_id=order.id,
        )
        position.quantity += estimate.quantity
        position.average_cost = (old_cost + estimate.quote_amount + estimate.fee_amount) / (
            position.quantity
        )
    else:
        if base.available < estimate.quantity:
            raise PaperTradingError("成交时可用 BTC 余额不足")
        base.available -= estimate.quantity
        _ledger(
            db,
            base,
            entry_type="trade_spend",
            amount=-estimate.quantity,
            reference_type="order",
            reference_id=order.id,
        )
        quote.available += estimate.quote_amount
        _ledger(
            db,
            quote,
            entry_type="trade_receive",
            amount=estimate.quote_amount,
            reference_type="order",
            reference_id=order.id,
        )
        quote.available -= estimate.fee_amount
        _ledger(
            db,
            quote,
            entry_type="trading_fee",
            amount=-estimate.fee_amount,
            reference_type="order",
            reference_id=order.id,
        )
        realized_delta = (
            (estimate.execution_price - position.average_cost) * estimate.quantity
            - estimate.fee_amount
        )
        position.realized_pnl += realized_delta
        if order.bot_id:
            bot = db.get(PaperBot, order.bot_id)
            if bot is not None:
                bot.realized_profit += realized_delta
        position.quantity -= estimate.quantity
        if position.quantity <= 0:
            position.quantity = ZERO
            position.average_cost = ZERO

    order.status = "filled"
    order.filled_quantity = estimate.quantity
    order.average_price = estimate.execution_price
    order.fee_amount = estimate.fee_amount
    order.slippage_amount = estimate.slippage_amount
    order.gas_amount = estimate.gas_amount
    order.filled_at = as_utc(market_time)
    fill = PaperFill(
        order_id=order.id,
        account_id=account.id,
        side=estimate.side,
        reference_price=estimate.reference_price,
        execution_price=estimate.execution_price,
        quantity=estimate.quantity,
        quote_amount=estimate.quote_amount,
        fee_amount=estimate.fee_amount,
        slippage_amount=estimate.slippage_amount,
        gas_amount=estimate.gas_amount,
        market_time=as_utc(market_time),
        cost_snapshot={
            "venue_type": "cex",
            "exchange": account.exchange,
            "fee_rate": str(account.fee_rate),
            "slippage_rate": str(account.slippage_rate),
            "gas_applied": False,
        },
    )
    db.add(fill)
    db.flush()
    _record_snapshot(db, account, estimate.execution_price, market_time)
    return fill


def _record_snapshot(
    db: Session,
    account: PaperAccount,
    mark_price: Decimal,
    market_time: datetime,
) -> None:
    quote = _balance(db, account.id, account.base_currency, lock=False)
    base = _balance(db, account.id, base_asset(account.symbol), lock=False)
    position = _position(db, account, lock=False)
    base_quantity = base.available + base.locked
    unrealized = (mark_price - position.average_cost) * position.quantity
    db.add(
        PaperAccountSnapshot(
            account_id=account.id,
            market_time=as_utc(market_time),
            quote_balance=quote.available + quote.locked,
            base_quantity=base_quantity,
            mark_price=mark_price,
            equity=quote.available + quote.locked + base_quantity * mark_price,
            realized_pnl=position.realized_pnl,
            unrealized_pnl=unrealized,
        )
    )


def place_order(
    db: Session,
    *,
    account: PaperAccount,
    side: str,
    order_type: str,
    quantity: Decimal,
    limit_price: Decimal | None = None,
    client_order_id: str | None = None,
    bot_id: str | None = None,
    grid_level: int | None = None,
    paired_level: int | None = None,
) -> PaperOrder:
    candle = require_latest_candle(db, account)
    mark_price = Decimal(candle.close)
    client_id = client_order_id or f"paper-{uuid.uuid4().hex}"
    existing = db.scalar(
        select(PaperOrder).where(
            PaperOrder.account_id == account.id,
            PaperOrder.client_order_id == client_id,
        )
    )
    if existing is not None:
        return existing
    validation_price = limit_price or mark_price
    _validate_order_risk(
        db,
        account,
        side=side,
        quantity=quantity,
        price=validation_price,
    )
    order = PaperOrder(
        account_id=account.id,
        bot_id=bot_id,
        client_order_id=client_id,
        exchange=account.exchange,
        symbol=account.symbol,
        side=side,
        order_type=order_type,
        status="pending",
        quantity=quantize_amount(quantity),
        limit_price=limit_price,
        filled_quantity=ZERO,
        fee_amount=ZERO,
        slippage_amount=ZERO,
        gas_amount=ZERO,
        reserved_amount=ZERO,
        grid_level=grid_level,
        paired_level=paired_level,
    )
    db.add(order)
    db.flush()

    if order_type == "market":
        estimate = estimate_cex_market_fill(
            side=side,
            reference_price=mark_price,
            quantity=order.quantity,
            fee_rate=account.fee_rate,
            slippage_rate=account.slippage_rate,
        )
        _apply_fill(
            db,
            account=account,
            order=order,
            estimate=estimate,
            market_time=candle.close_time,
        )
        return order

    if limit_price is None:
        raise PaperTradingError("限价单必须提供价格")
    marketable = (side == "buy" and limit_price >= mark_price) or (
        side == "sell" and limit_price <= mark_price
    )
    if marketable:
        estimate = estimate_cex_market_fill(
            side=side,
            reference_price=mark_price,
            quantity=order.quantity,
            fee_rate=account.fee_rate,
            slippage_rate=account.slippage_rate,
        )
        within_limit = (side == "buy" and estimate.execution_price <= limit_price) or (
            side == "sell" and estimate.execution_price >= limit_price
        )
        if within_limit:
            _apply_fill(
                db,
                account=account,
                order=order,
                estimate=estimate,
                market_time=candle.close_time,
            )
            return order
    _reserve_limit_order(db, account, order)
    return order


def cancel_order(db: Session, *, account: PaperAccount, order_id: str) -> PaperOrder:
    order = db.scalar(
        select(PaperOrder)
        .where(PaperOrder.id == order_id, PaperOrder.account_id == account.id)
        .with_for_update()
    )
    if order is None:
        raise PaperTradingError("模拟订单不存在")
    if order.status != "open":
        raise PaperTradingError("只有未成交订单可以撤销")
    _release_reservation(db, order, entry_type="order_cancel_unlock")
    order.status = "cancelled"
    order.cancelled_at = datetime.now(UTC)
    return order


def process_open_orders(db: Session, account: PaperAccount) -> int:
    orders = list(
        db.scalars(
            select(PaperOrder)
            .where(PaperOrder.account_id == account.id, PaperOrder.status == "open")
            .order_by(PaperOrder.created_at.asc())
            .with_for_update()
        ).all()
    )
    if not orders:
        return 0

    # Replaying every closed candle since the oldest open order prevents a short
    # engine outage from hiding a price touch that happened while the worker was
    # stopped. Orders are still filled at most once because their status changes
    # inside the same transaction.
    oldest_order_time = min(as_utc(order.created_at) for order in orders)
    candles = list(
        db.scalars(
            select(MarketCandle)
            .where(
                MarketCandle.exchange == account.exchange,
                MarketCandle.symbol == account.symbol,
                MarketCandle.timeframe == "1m",
                MarketCandle.is_closed.is_(True),
                MarketCandle.close_time >= oldest_order_time,
            )
            .order_by(MarketCandle.close_time.asc())
        ).all()
    )
    if not candles:
        return 0

    filled = 0
    for order in orders:
        if order.bot_id:
            bot = db.get(PaperBot, order.bot_id)
            if bot is None or bot.status != "running":
                continue
        assert order.limit_price is not None
        candle = next(
            (
                candidate
                for candidate in candles
                if as_utc(candidate.close_time) >= as_utc(order.created_at)
                and order_touched_by_candle(
                    side=order.side,
                    limit_price=order.limit_price,
                    candle_low=Decimal(candidate.low),
                    candle_high=Decimal(candidate.high),
                )
            ),
            None,
        )
        if candle is None:
            continue
        estimate = estimate_cex_limit_fill(
            side=order.side,
            limit_price=order.limit_price,
            quantity=order.quantity,
            fee_rate=account.fee_rate,
        )
        _apply_fill(
            db,
            account=account,
            order=order,
            estimate=estimate,
            market_time=candle.close_time,
        )
        filled += 1
        if order.bot_id:
            _place_grid_counter_order(db, account, order)
    return filled


def create_grid_bot(
    db: Session,
    *,
    account: PaperAccount,
    payload: PaperGridCreate,
) -> PaperBot:
    levels = build_grid_levels(
        payload.lower_price,
        payload.upper_price,
        payload.grid_count,
        payload.grid_mode,
    )
    bot = PaperBot(
        account_id=account.id,
        name=payload.name,
        status="draft",
        lower_price=payload.lower_price,
        upper_price=payload.upper_price,
        grid_count=payload.grid_count,
        grid_mode=payload.grid_mode,
        investment=payload.investment,
        parameters={
            "levels": [{"index": level.index, "price": str(level.price)} for level in levels]
        },
        realized_profit=ZERO,
    )
    db.add(bot)
    db.flush()
    db.add(
        PaperBotEvent(
            bot_id=bot.id,
            event_type="created",
            message="Grid bot created",
            payload=bot.parameters,
        )
    )
    return bot


def start_grid_bot(db: Session, *, account: PaperAccount, bot: PaperBot) -> PaperBot:
    if bot.status == "paused":
        bot.status = "running"
        db.add(
            PaperBotEvent(
                bot_id=bot.id,
                event_type="resumed",
                message="Grid bot resumed",
                payload={},
            )
        )
        return bot
    if bot.status != "draft":
        raise PaperTradingError("只有草稿或暂停状态的网格可以启动")
    candle = require_latest_candle(db, account)
    mark = Decimal(candle.close)
    if not bot.lower_price < mark < bot.upper_price:
        raise PaperTradingError("当前价格必须位于网格价格范围内")
    quote = _balance(db, account.id, account.base_currency)
    if quote.available < bot.investment:
        raise PaperTradingError("可用 USDT 不足以启动网格")

    levels = build_grid_levels(bot.lower_price, bot.upper_price, bot.grid_count, bot.grid_mode)
    lower = [level for level in levels if level.price < mark]
    upper = [level for level in levels if level.price > mark]
    cost_buffer = Decimal("1") + account.fee_rate + account.slippage_rate
    per_grid = bot.investment / Decimal(bot.grid_count) / cost_buffer

    upper_quantities = {
        level.index: quantize_amount(per_grid / level.price) for level in upper
    }
    if upper_quantities:
        initial_quantity = sum(upper_quantities.values(), start=ZERO)
        place_order(
            db,
            account=account,
            side="buy",
            order_type="market",
            quantity=initial_quantity,
            client_order_id=f"grid-{bot.id}-inventory",
            bot_id=bot.id,
        )
    for level in lower:
        quantity = per_grid / (level.price * (Decimal("1") + account.fee_rate))
        place_order(
            db,
            account=account,
            side="buy",
            order_type="limit",
            quantity=quantity,
            limit_price=level.price,
            client_order_id=f"grid-{bot.id}-initial-buy-{level.index}",
            bot_id=bot.id,
            grid_level=level.index,
            paired_level=level.index + 1,
        )
    for level in upper:
        quantity = upper_quantities[level.index]
        place_order(
            db,
            account=account,
            side="sell",
            order_type="limit",
            quantity=quantity,
            limit_price=level.price,
            client_order_id=f"grid-{bot.id}-initial-sell-{level.index}",
            bot_id=bot.id,
            grid_level=level.index,
            paired_level=level.index - 1,
        )
    bot.status = "running"
    bot.started_at = datetime.now(UTC)
    db.add(
        PaperBotEvent(
            bot_id=bot.id,
            event_type="started",
            message="Grid bot started",
            payload={"mark_price": str(mark), "order_count": len(lower) + len(upper)},
        )
    )
    return bot


def _place_grid_counter_order(
    db: Session,
    account: PaperAccount,
    filled_order: PaperOrder,
) -> None:
    bot = db.get(PaperBot, filled_order.bot_id)
    if bot is None or bot.status != "running" or filled_order.paired_level is None:
        return
    levels = build_grid_levels(bot.lower_price, bot.upper_price, bot.grid_count, bot.grid_mode)
    target = next((level for level in levels if level.index == filled_order.paired_level), None)
    if target is None:
        return
    side = "sell" if filled_order.side == "buy" else "buy"
    paired_level = target.index - 1 if side == "sell" else target.index + 1
    try:
        place_order(
            db,
            account=account,
            side=side,
            order_type="limit",
            quantity=filled_order.quantity,
            limit_price=target.price,
            client_order_id=f"grid-{bot.id}-pair-{filled_order.id}",
            bot_id=bot.id,
            grid_level=target.index,
            paired_level=paired_level,
        )
    except PaperTradingError as exc:
        bot.status = "error"
        db.add(
            PaperBotEvent(
                bot_id=bot.id,
                event_type="error",
                message=str(exc),
                payload={"filled_order_id": filled_order.id},
            )
        )


def change_grid_bot_status(
    db: Session,
    *,
    account: PaperAccount,
    bot: PaperBot,
    action: str,
) -> PaperBot:
    if bot.account_id != account.id:
        raise PaperTradingError("网格机器人不存在")
    if action == "start":
        return start_grid_bot(db, account=account, bot=bot)
    if action == "pause":
        if bot.status != "running":
            raise PaperTradingError("只有运行中的网格可以暂停")
        bot.status = "paused"
    elif action == "stop":
        if bot.status not in {"running", "paused", "error"}:
            raise PaperTradingError("当前网格不能停止")
        for order in db.scalars(
            select(PaperOrder).where(
                PaperOrder.bot_id == bot.id,
                PaperOrder.status == "open",
            )
        ):
            cancel_order(db, account=account, order_id=order.id)
        bot.status = "stopped"
        bot.stopped_at = datetime.now(UTC)
    else:
        raise PaperTradingError("不支持的网格操作")
    db.add(
        PaperBotEvent(
            bot_id=bot.id,
            event_type=action,
            message=f"Grid bot {action}",
            payload={},
        )
    )
    return bot


def account_response(db: Session, account: PaperAccount) -> PaperAccountResponse:
    candle = latest_candle(db, account)
    mark = Decimal(candle.close) if candle else ZERO
    balances = list(
        db.scalars(
            select(PaperBalance)
            .where(PaperBalance.account_id == account.id)
            .order_by(PaperBalance.asset.asc())
        ).all()
    )
    position = _position(db, account, lock=False)
    market_value = position.quantity * mark
    unrealized = (mark - position.average_cost) * position.quantity if mark else ZERO
    equity = sum((item.available + item.locked for item in balances if item.asset == "USDT"), ZERO)
    equity += sum((item.available + item.locked for item in balances if item.asset == "BTC"), ZERO) * mark
    total_fees = db.scalar(
        select(func.coalesce(func.sum(-PaperLedgerEntry.amount), 0)).where(
            PaperLedgerEntry.account_id == account.id,
            PaperLedgerEntry.entry_type == "trading_fee",
        )
    ) or ZERO
    total_gas = db.scalar(
        select(func.coalesce(func.sum(-PaperLedgerEntry.amount), 0)).where(
            PaperLedgerEntry.account_id == account.id,
            PaperLedgerEntry.entry_type == "gas_fee",
        )
    ) or ZERO
    return PaperAccountResponse(
        id=account.id,
        name=account.name,
        exchange=account.exchange,
        symbol=account.symbol,
        status=account.status,
        fee_rate=account.fee_rate,
        slippage_rate=account.slippage_rate,
        max_position_pct=account.max_position_pct,
        max_order_notional=account.max_order_notional,
        balances=[
            PaperBalanceResponse(
                asset=item.asset,
                available=item.available,
                locked=item.locked,
            )
            for item in balances
        ],
        position=PaperPositionResponse(
            symbol=account.symbol,
            quantity=position.quantity,
            average_cost=position.average_cost,
            mark_price=mark,
            market_value=market_value,
            realized_pnl=position.realized_pnl,
            unrealized_pnl=unrealized,
        ),
        equity=equity,
        total_fees=Decimal(total_fees),
        total_gas=Decimal(total_gas),
        created_at=account.created_at,
    )


def process_all_paper_accounts(db: Session) -> int:
    accounts = list(
        db.scalars(
            select(PaperAccount)
            .where(PaperAccount.status == "active")
            .order_by(PaperAccount.id.asc())
        ).all()
    )
    return sum(process_open_orders(db, account) for account in accounts)
