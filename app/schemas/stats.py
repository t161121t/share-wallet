# app/schemas/stats.py

from datetime import date
from typing import List

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """
    期間指定用（from/to）
    - クエリパラメータで使うときは個別に受け取ることが多いが、
      サービス層に渡すときにまとめて使えるよう定義しておく。
    """
    from_date: date = Field(..., alias="from", description="開始日")
    to_date: date = Field(..., alias="to", description="終了日")

    class Config:
        # Pydantic v1: allow_population_by_field_name = True
        # Pydantic v2: use 'model_config' だが FastAPI は基本的に両対応してくれる
        allow_population_by_field_name = True


class UserTotal(BaseModel):
    """
    ユーザーごとの合計出金
    """
    user_id: int = Field(..., description="ユーザーID")
    total_amount: int = Field(..., description="期間内の合計出金額（1円単位）")


class CategoryTotal(BaseModel):
    """
    カテゴリごとの合計出金
    """
    category_id: int = Field(..., description="カテゴリID")
    category_name: str = Field(..., description="カテゴリ名")
    total_amount: int = Field(..., description="期間内の合計出金額（1円単位）")


class SummaryResponse(BaseModel):
    """
    ② 二人の出金合計（全体・人別・カテゴリ別）レスポンス
    - GET /stats/summary
    """
    from_date: date = Field(..., description="集計開始日")
    to_date: date = Field(..., description="集計終了日")
    total_amount: int = Field(..., description="期間内の総出金額")
    by_user: List[UserTotal] = Field(..., description="ユーザー別の合計出金")
    by_category: List[CategoryTotal] = Field(..., description="カテゴリ別の合計出金")


class UserTotalsResponse(BaseModel):
    """
    ③ 個人の出金合計（全ユーザー分の一覧）
    - GET /stats/users
    """
    from_date: date = Field(..., description="集計開始日")
    to_date: date = Field(..., description="集計終了日")
    users: List[UserTotal] = Field(..., description="ユーザーごとの合計出金（多い順など）")


class UserCategoryBreakdownResponse(BaseModel):
    """
    ③ 個人のカテゴリ内訳
    - GET /stats/users/{user_id}/categories
    """
    user_id: int = Field(..., description="対象ユーザーID")
    from_date: date = Field(..., description="集計開始日")
    to_date: date = Field(..., description="集計終了日")
    categories: List[CategoryTotal] = Field(
        ..., description="そのユーザーのカテゴリ別合計出金"
    )
