# app/schemas/transaction.py

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, conint, validator


class TransactionSplitItem(BaseModel):
    """
    割り勘内訳の1行分
    - user_id: 負担するユーザーID
    - amount: そのユーザーの負担金額（1円単位、正の整数）
    """
    user_id: int = Field(..., description="負担するユーザーのID")
    amount: conint(gt=0) = Field(..., description="そのユーザーの負担金額（1円単位）")


class TransactionBase(BaseModel):
    """
    取引の共通フィールド（リクエスト/レスポンス両方で使う）
    """
    category_id: int = Field(..., description="カテゴリID")
    total_amount: conint(gt=0) = Field(..., description="合計金額（1円単位、正の整数）")
    used_date: date = Field(..., description="使用日（例: 2025-10-15）")
    name: str = Field(..., description="取引の名前（例: スーパーでの買い物）")
    memo: Optional[str] = Field(None, description="メモ（任意）")


class TransactionCreate(TransactionBase):
    """
    ① 出金登録のリクエストボディ

    - 内訳（splits）の合計 ＝ total_amount のチェックは
      サービス層（もしくはルーター側）で行う想定。
      ここでは「重複ユーザー」のみ schema レベルでチェック。
    """
    splits: List[TransactionSplitItem] = Field(
        ..., description="割り勘内訳（ユーザーごとの負担金額）"
    )

    @validator("splits")
    def check_unique_user_ids(cls, splits: List["TransactionSplitItem"]):
        """
        同じ取引内で同一ユーザーIDが複数指定されていないかチェック。
        （仕様: 同じ取引内で同じユーザーIDを重複させない）
        """
        user_ids = [s.user_id for s in splits]
        if len(user_ids) != len(set(user_ids)):
            # ここで ValueError を投げると FastAPI が 422 Unprocessable Entity を返す
            raise ValueError("同一ユーザーが複数回指定されています")
        return splits


class CategoryInfo(BaseModel):
    """
    レスポンス用のカテゴリ情報
    """
    id: int
    name: str


class TransactionDetail(TransactionBase):
    """
    1件分の取引詳細（レスポンス用）
    - ④ 履歴一覧・詳細どちらでも使える形
    """
    id: int = Field(..., description="取引ID")
    category: CategoryInfo = Field(..., description="カテゴリ情報")
    splits: List[TransactionSplitItem] = Field(..., description="割り勘内訳")
    created_at: datetime = Field(..., description="登録日時")
    updated_at: datetime = Field(..., description="更新日時")


class APIError(BaseModel):
    """
    エラー用の共通レスポンス
    例:
      - error: "合計不一致"
        message: "内訳の合計と合計金額が一致していません"
      - error: "重複内訳"
        message: "同一ユーザーが複数回指定されています"
    """
    error: str = Field(..., description="エラー名（例: 合計不一致, 重複内訳）")
    message: str = Field(..., description="エラーの説明メッセージ")
