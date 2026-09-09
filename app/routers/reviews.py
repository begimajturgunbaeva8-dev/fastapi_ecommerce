from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.db_depends import get_async_db
from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel
from app.schemas import ReviewCreate, ReviewOut
from app.auth import get_current_user  

router = APIRouter(tags=["reviews"])


# --- Функция автоматического пересчета рейтинга товара ---
async def update_product_rating(db: AsyncSession, product_id: int):
    # Используем func.avg для подсчета среднего значения grade среди АКТИВНЫХ отзывов
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    
    # Получаем объект товара из базы и обновляем поле rating
    product = await db.get(ProductModel, product_id)
    if product:
        product.rating = round(float(avg_rating), 2)
        await db.commit()


# 1. GET /reviews/ — Получение всех активных отзывов
@router.get("/reviews/", response_model=List[ReviewOut])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(ReviewModel).where(ReviewModel.is_active == True))
    return result.scalars().all()


# 2. GET /products/{product_id}/reviews/ — Получение отзывов о конкретном товаре
@router.get("/products/{product_id}/reviews/", response_model=List[ReviewOut])
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    # Проверяем, существует ли активный товар
    product = await db.get(ProductModel, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
        
    result = await db.execute(
        select(ReviewModel).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    return result.scalars().all()


# 3. POST /reviews/ — Добавление отзыва (Только для роли "buyer")
@router.post("/reviews/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Проверка роли
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Forbidden: Only buyers can leave reviews")
        
    # Проверка существования и активности товара
    product = await db.get(ProductModel, body.product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    # Создание отзыва
    new_review = ReviewModel(
        user_id=current_user.id,
        product_id=body.product_id,
        comment=body.comment,
        grade=body.grade
    )
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    # Пересчитываем рейтинг товара
    await update_product_rating(db, body.product_id)
    
    return new_review


# 4. DELETE /reviews/{review_id} — Мягкое удаление отзыва (Только для роли "admin")
@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Проверка роли
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Only admins can delete reviews")

    # Поиск активного отзыва
    result = await db.execute(select(ReviewModel).where(ReviewModel.id == review_id, ReviewModel.is_active == True))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Мягкое удаление
    review.is_active = False
    await db.commit()

    # Пересчет рейтинга товара уже БЕЗ удаленного отзыва
    await update_product_rating(db, review.product_id)

    return {"message": "Review deleted"}