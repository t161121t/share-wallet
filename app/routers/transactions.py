# app/routers/transactions.py

from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import (
    TransactionCreate,
    TransactionDetail,
    TransactionSplitItem,
    CategoryInfo,
    APIError,
)

from app.models.transaction import Transaction, TransactionSplit

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
)


@router.post(
    "",
    response_model=TransactionDetail,
    responses={400: {"model": APIError}},
)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    """
    ① 出金登録（Supabase / PostgreSQL 版）
    """
    # ① 内訳合計チェック
    splits_sum = sum(split.amount for split in payload.splits)
    if splits_sum != payload.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "合計不一致",
                "message": "内訳の合計と合計金額が一致していません",
            },
        )

    # ② トランザクションを INSERT
    db_tx = Transaction(
        category_id=payload.category_id,
        total_amount=payload.total_amount,
        used_date=payload.used_date,
        name=payload.name,
        memo=payload.memo,
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)

    # ③ splits も INSERT
    for s in payload.splits:
        db_split = TransactionSplit(
            transaction_id=db_tx.id,
            user_id=s.user_id,
            amount=s.amount,
        )
        db.add(db_split)
    db.commit()

    # ④ レスポンス整形（カテゴリ名は MVP では仮）
    category = CategoryInfo(id=payload.category_id, name=f"Category {payload.category_id}")

    return TransactionDetail(
        id=db_tx.id,
        category_id=db_tx.category_id,
        total_amount=db_tx.total_amount,
        used_date=db_tx.used_date,
        name=db_tx.name,
        memo=db_tx.memo,
        category=category,
        splits=payload.splits,
        created_at=db_tx.created_at,
        updated_at=db_tx.updated_at,
    )


@router.get(
    "",
    response_model=List[TransactionDetail],
)
def list_transactions(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    category_id: Optional[int] = None,
    user_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    ④ 出金履歴一覧（Supabase / PostgreSQL）
    """
    q = db.query(Transaction)

    # 期間
    if from_date:
        q = q.filter(Transaction.used_date >= from_date)
    if to_date:
        q = q.filter(Transaction.used_date <= to_date)

    # カテゴリ
    if category_id:
        q = q.filter(Transaction.category_id == category_id)

    # キーワード
    if keyword:
        keyword = f"%{keyword}%"
        q = q.filter(
            (Transaction.name.ilike(keyword)) |
            (Transaction.memo.ilike(keyword))
        )

    tx_list = q.all()

    results = []

    for tx in tx_list:
        splits = db.query(TransactionSplit).filter(
            TransactionSplit.transaction_id == tx.id
        ).all()

        split_items = [
            TransactionSplitItem(
                user_id=s.user_id,
                amount=s.amount,
            )
            for s in splits
        ]

        # user_id フィルタ
        if user_id is not None:
            if all(s.user_id != user_id for s in split_items):
                continue

        category = CategoryInfo(id=tx.category_id, name=f"Category {tx.category_id}")

        results.append(
            TransactionDetail(
                id=tx.id,
                category_id=tx.category_id,
                total_amount=tx.total_amount,
                used_date=tx.used_date,
                name=tx.name,
                memo=tx.memo,
                category=category,
                splits=split_items,
                created_at=tx.created_at,
                updated_at=tx.updated_at,
            )
        )

    return results


@router.get(
    "/{transaction_id}",
    response_model=TransactionDetail,
)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    ④ 出金詳細（Supabase / PostgreSQL）
    """
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not tx:
        raise HTTPException(status_code=404, detail="取引が見つかりません")

    splits = db.query(TransactionSplit).filter(
        TransactionSplit.transaction_id == tx.id
    ).all()

    split_items = [
        TransactionSplitItem(user_id=s.user_id, amount=s.amount)
        for s in splits
    ]

    category = CategoryInfo(id=tx.category_id, name=f"Category {tx.category_id}")

    return TransactionDetail(
        id=tx.id,
        category_id=tx.category_id,
        total_amount=tx.total_amount,
        used_date=tx.used_date,
        name=tx.name,
        memo=tx.memo,
        category=category,
        splits=split_items,
        created_at=tx.created_at,
        updated_at=tx.updated_at,
    )
