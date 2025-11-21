# app/routers/stats.py

from datetime import date
from typing import Dict, List, Tuple

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.transaction import Transaction, TransactionSplit
from app.schemas import (
    SummaryResponse,
    UserTotalsResponse,
    UserCategoryBreakdownResponse,
    UserTotal,
    CategoryTotal,
)

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)


# 期間フィルター共通関数
def _filter_by_period(db: Session, from_date: date, to_date: date):
    return (
        db.query(Transaction)
        .filter(Transaction.used_date >= from_date)
        .filter(Transaction.used_date <= to_date)
        .all()
    )


# -------------------------------
# ② /stats/summary
# -------------------------------
@router.get(
    "/summary",
    response_model=SummaryResponse,
)
def get_summary(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    """
    二人の出金合計（期間内の全体・人別・カテゴリ別）
    """
    tx_list = _filter_by_period(db, from_date, to_date)

    # -------- 全体の合計 --------
    total_amount = sum(tx.total_amount for tx in tx_list)

    # -------- 人別の合計 --------
    user_totals: Dict[int, int] = {}

    for tx in tx_list:
        splits = db.query(TransactionSplit).filter(
            TransactionSplit.transaction_id == tx.id
        ).all()

        for s in splits:
            user_totals[s.user_id] = user_totals.get(s.user_id, 0) + s.amount

    by_user = [
        UserTotal(user_id=user_id, total_amount=amount)
        for user_id, amount in user_totals.items()
    ]

    # -------- カテゴリ別の合計 --------
    category_totals: Dict[Tuple[int, str], int] = {}

    for tx in tx_list:
        key = (tx.category_id, f"Category {tx.category_id}")  # MVPは仮名
        category_totals[key] = category_totals.get(key, 0) + tx.total_amount

    by_category = [
        CategoryTotal(
            category_id=cat_id,
            category_name=cat_name,
            total_amount=amount,
        )
        for (cat_id, cat_name), amount in category_totals.items()
    ]

    return SummaryResponse(
        from_date=from_date,
        to_date=to_date,
        total_amount=total_amount,
        by_user=by_user,
        by_category=by_category,
    )


# -------------------------------
# ③ /stats/users
# -------------------------------
@router.get(
    "/users",
    response_model=UserTotalsResponse,
)
def get_user_totals(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    """
    個人の出金合計（全ユーザー分）
    """
    tx_list = _filter_by_period(db, from_date, to_date)

    user_totals: Dict[int, int] = {}

    for tx in tx_list:
        splits = db.query(TransactionSplit).filter(
            TransactionSplit.transaction_id == tx.id
        ).all()

        for s in splits:
            user_totals[s.user_id] = user_totals.get(s.user_id, 0) + s.amount

    # 金額が大きい順にソート
    sorted_items = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)

    users = [
        UserTotal(user_id=user_id, total_amount=amount)
        for user_id, amount in sorted_items
    ]

    return UserTotalsResponse(
        from_date=from_date,
        to_date=to_date,
        users=users,
    )


# -------------------------------
# ③ /stats/users/{user_id}/categories
# -------------------------------
@router.get(
    "/users/{user_id}/categories",
    response_model=UserCategoryBreakdownResponse,
)
def get_user_category_breakdown(
    user_id: int,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    """
    個人のカテゴリ別内訳
    """
    tx_list = _filter_by_period(db, from_date, to_date)

    category_totals: Dict[Tuple[int, str], int] = {}

    for tx in tx_list:
        splits = db.query(TransactionSplit).filter(
            TransactionSplit.transaction_id == tx.id
        ).all()

        for s in splits:
            if s.user_id != user_id:
                continue

            key = (tx.category_id, f"Category {tx.category_id}")  # MVPのカテゴリ名
            category_totals[key] = category_totals.get(key, 0) + s.amount

    categories = [
        CategoryTotal(
            category_id=cat_id,
            category_name=cat_name,
            total_amount=amount,
        )
        for (cat_id, cat_name), amount in category_totals.items()
    ]

    return UserCategoryBreakdownResponse(
        user_id=user_id,
        from_date=from_date,
        to_date=to_date,
        categories=categories,
    )
