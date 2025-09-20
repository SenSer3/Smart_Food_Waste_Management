import os
from fastapi import FastAPI
import joblib
from api.routes import router as api_router
from model.food_alternative_model import FoodAlternativeModel

app = FastAPI()

# Load existing lasso model
lasso_model_path = 'model/best_lasso_model.pkl'
lasso_model = joblib.load(lasso_model_path)

# Load food alternative model
food_alternative_model = FoodAlternativeModel('database/nutrition_data.csv')

# Include API routes
app.include_router(api_router)

# You can add endpoints here to use lasso_model and food_alternative_model as needed

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
