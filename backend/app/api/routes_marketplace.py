from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..db.database import get_db
from ..db.models import (
    User, SellerProfile, BuyerProfile, GigCategory, Gig, Project, 
    ProjectMilestone, Proposal, Order, Review, Wallet, Transaction, 
    Dispute, Coupon, MarketplaceAnalytics
)
from ..services.marketplace_ai_service import marketplace_ai

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

# --- Schemas ---

class GigCreate(BaseModel):
    seller_id: str
    category_id: str
    title: str
    description: str
    price: float
    delivery_days: int
    revisions: int = 0

class ProjectCreate(BaseModel):
    buyer_id: str
    title: str
    description: str
    budget: float
    deadline: datetime
    skills_required: str

class OrderCreate(BaseModel):
    buyer_id: str
    seller_id: str
    gig_id: Optional[str] = None
    project_id: Optional[str] = None
    amount: float

class ReviewCreate(BaseModel):
    order_id: str
    reviewer_id: str
    reviewee_id: str
    rating: int
    comment: str

# --- Endpoints ---

@router.post("/gigs", status_code=status.HTTP_201_CREATED)
def create_gig(gig_data: GigCreate, db: Session = Depends(get_db)):
    db_gig = Gig(**gig_data.model_dump())
    db.add(db_gig)
    db.commit()
    db.refresh(db_gig)
    return db_gig

@router.get("/gigs")
def search_gigs(category: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, db: Session = Depends(get_db)):
    query = db.query(Gig).filter(Gig.is_active == True)
    if category:
        query = query.join(GigCategory).filter(GigCategory.name == category)
    if min_price is not None:
        query = query.filter(Gig.price >= min_price)
    if max_price is not None:
        query = query.filter(Gig.price <= max_price)
    return query.all()

@router.post("/projects", status_code=status.HTTP_201_CREATED)
def post_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    db_proj = Project(**project_data.model_dump())
    db.add(db_proj)
    db.commit()
    db.refresh(db_proj)
    return db_proj

@router.get("/projects")
def get_open_projects(db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.status == "Open").all()

@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(**order_data.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/orders/{user_id}")
def get_user_orders(user_id: str, db: Session = Depends(get_db)):
    orders_as_buyer = db.query(Order).filter(Order.buyer_id == user_id).all()
    orders_as_seller = db.query(Order).filter(Order.seller_id == user_id).all()
    return {"buying": orders_as_buyer, "selling": orders_as_seller}

@router.post("/reviews", status_code=status.HTTP_201_CREATED)
def submit_review(review_data: ReviewCreate, db: Session = Depends(get_db)):
    db_review = Review(**review_data.model_dump())
    db.add(db_review)
    
    # Update seller rating (simplified)
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == review_data.reviewee_id).first()
    if seller:
        seller.total_reviews += 1
        seller.rating = ((seller.rating * (seller.total_reviews - 1)) + review_data.rating) / seller.total_reviews
        
    db.commit()
    db.refresh(db_review)
    return db_review

# --- AI Endpoints ---

@router.post("/ai/recommend-gigs")
def recommend_gigs_api(user_skills: str, db: Session = Depends(get_db)):
    available_gigs = [
        {"id": g.id, "title": g.title, "description": g.description, "price": g.price} 
        for g in db.query(Gig).filter(Gig.is_active == True).limit(50).all()
    ]
    recommended = marketplace_ai.recommend_gigs(user_skills, available_gigs)
    return recommended[:10]

@router.post("/ai/suggest-price")
def suggest_price_api(category: str, skills: str, experience_level: str):
    return marketplace_ai.suggest_pricing(category, skills, experience_level)

@router.get("/analytics")
def get_marketplace_analytics(db: Session = Depends(get_db)):
    total_gigs = db.query(Gig).count()
    total_orders = db.query(Order).count()
    total_projects = db.query(Project).count()
    return {
        "total_gigs": total_gigs,
        "total_orders": total_orders,
        "total_projects": total_projects,
        "status": "Healthy"
    }
