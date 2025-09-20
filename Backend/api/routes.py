from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from model.food_alternative_model import FoodAlternativeModel
from model.waste_prediction_model import WastePredictionModel
from fastapi import Body
from fastapi.responses import JSONResponse
import datetime
import logging
from supabase_client import supabase
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, List
import logging

router = APIRouter()

logger = logging.getLogger("uvicorn.error")

# Load the food alternative model
food_model = FoodAlternativeModel('database/nutrition_data.csv')

# Load the waste prediction model
try:
    waste_prediction_model = WastePredictionModel('best_lasso_model.joblib', 'lasso_preprocessor.joblib')
    if not hasattr(waste_prediction_model, 'lasso_model_path'):
        raise ValueError("Model initialization failed - missing lasso_model_path")
except Exception as e:
    logger.error(f"Failed to initialize waste prediction model: {e}")
    waste_prediction_model = None  # We'll handle this case in the endpoints

logger = logging.getLogger("uvicorn.error")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class FoodRequest(BaseModel):
    food_name: str

class MenuRequest(BaseModel):
    menu: List[str]

# User models
class UserSignup(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: EmailStr

# Food wastage data model
class WastageRecord(BaseModel):
    user_id: str
    date: Optional[str] = None  # ISO date string
    food_item: str
    quantity: float  # e.g. in kg or units
    notes: Optional[str] = None

# Authentication endpoints
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserSignup):
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })
        if response.get("error"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response["error"]["message"])
        return {"message": "User signed up successfully. Please check your email to confirm."}
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        if response.get("error"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=response["error"]["message"])
        access_token = response.get("data", {}).get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Dependency to get current user from token
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        user_data = supabase.auth.get_user(token)
        if user_data.get("error"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        user_info = user_data.get("data", {}).get("user")
        if not user_info:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return User(id=user_info["id"], email=user_info["email"])
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

# Food wastage data endpoints
@router.post("/wastage")
def add_wastage_record(record: WastageRecord, current_user: User = Depends(get_current_user)):
    try:
        data = record.dict()
        data["user_id"] = current_user.id  # Override user_id with authenticated user
        response = supabase.table("wastage_records").insert(data).execute()
        if response.get("error"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response["error"]["message"])
        return {"message": "Wastage record added successfully"}
    except Exception as e:
        logger.error(f"Add wastage record error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/wastage")
def get_wastage_records(current_user: User = Depends(get_current_user)):
    try:
        response = supabase.table("wastage_records").select("*").eq("user_id", current_user.id).execute()
        if response.get("error"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response["error"]["message"])
        return {"wastage_records": response.get("data", [])}
    except Exception as e:
        logger.error(f"Get wastage records error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/wastage/analysis")
def get_wastage_analysis(current_user: User = Depends(get_current_user)):
    try:
        # Basic example analysis: total quantity wasted per food item
        response = supabase.table("wastage_records").select("food_item, quantity").eq("user_id", current_user.id).execute()
        if response.get("error"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response["error"]["message"])
        data = response.get("data", [])
        analysis = {}
        for record in data:
            food_item = record["food_item"]
            quantity = record["quantity"]
            analysis[food_item] = analysis.get(food_item, 0) + quantity
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Wastage analysis error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Existing food alternatives endpoints
@router.post('/food-alternatives')
def get_food_alternatives(request: FoodRequest):
    if not request.food_name or not request.food_name.strip():
        raise HTTPException(status_code=422, detail="Food name must not be empty")
    try:
        result = food_model.find_alternatives(request.food_name)
        if not result or "alternatives" not in result or not result["alternatives"]:
            raise HTTPException(status_code=404, detail="Food not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_food_alternatives: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post('/menu-alternatives')
def get_menu_alternatives(request: MenuRequest):
    try:
        menu_alternatives = []
        for food_name in request.menu:
            result = food_model.find_alternatives(food_name)
            if result and "alternatives" in result and result["alternatives"]:
                menu_alternatives.append({
                    "input_food": result["input_food"],
                    "input_food_nutrients": result["input_food_nutrients"],
                    "nutrients_message": result["nutrients_message"],
                    "alternatives": result["alternatives"]
                })
            else:
                menu_alternatives.append({
                    "input_food": food_name,
                    "error": "Food not found"
                })
        return {"menu_alternatives": menu_alternatives}
    except Exception as e:
        logger.error(f"Error in get_menu_alternatives: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post('/waste-prediction')
def waste_prediction(
    user_id: str = Body(...),
    recent_waste: list = Body(...),
    menu_items: list = Body(...),
    day_of_week: int = Body(...)
):
    """
    Predict waste quantity based on recent waste, menu items, and day of week.
    """
    try:
        # Input validation
        if not isinstance(recent_waste, list):
            raise HTTPException(status_code=422, detail="recent_waste must be a list")
            
        if not isinstance(menu_items, list):
            raise HTTPException(status_code=422, detail="menu_items must be a list")
            
        if not isinstance(day_of_week, int) or day_of_week < 0 or day_of_week > 6:
            raise HTTPException(status_code=422, detail="day_of_week must be an integer between 0 and 6 inclusive")
            
        # Get prediction from the model
        prediction_result = waste_prediction_model.get_prediction_and_analysis(
            user_id, recent_waste, menu_items, day_of_week
        )
        
        return prediction_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in waste prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
