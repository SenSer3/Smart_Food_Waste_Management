# Smart Food Waste Management Backend - Project Overview

## 📁 Project Structure

```
Backend/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── supabase_client.py              # Supabase database client
├── .env                            # Environment variables (API keys)
├── .venv/                          # Virtual environment
├── __pycache__/                    # Python cache files
├── api/
│   └── routes.py                   # API endpoints and routes
├── database/
│   └── nutrition_data.csv          # Nutrition data for alternatives
├── model/
│   ├── best_lasso_model.pkl        # Trained waste prediction model
│   ├── food_alternative_model.py   # Food alternatives logic
│   └── waste_prediction_model.py   # Waste prediction and analysis
├── schemas/
│   └── input_schema.py             # Pydantic data models
└── test_all_endpoints_updated.py   # Comprehensive API testing
```

## 🚀 Key Features

### 1. **User Authentication**
- User signup and login via Supabase Auth
- JWT token-based authentication
- Secure user sessions

### 2. **Food Waste Tracking**
- Add waste records with food item, quantity, date, notes
- View personal waste history
- Basic waste analysis (total waste per food item)

### 3. **Food Alternatives**
- Find nutrient-similar food alternatives
- Menu-based alternative suggestions
- Cosine similarity based on nutrition data

### 4. **Waste Prediction & Analysis**
- Predict future waste using trained Lasso model
- Historical trend analysis (weekly waste, high-waste items)
- Pictorial visualizations (charts as base64 images)
- Optimized feature engineering (~50 features vs 700+)

## 🔗 API Endpoints

### Base URL: `http://localhost:8002`

### Authentication Endpoints
```
POST /signup
- Body: {"email": "user@example.com", "password": "password123"}
- Response: {"message": "User signed up successfully"}

POST /login
- Body: {"username": "user@example.com", "password": "password123"}
- Response: {"access_token": "jwt_token", "token_type": "bearer"}
```

### Waste Management Endpoints (Require Authentication)
```
POST /wastage
- Headers: {"Authorization": "Bearer <token>"}
- Body: {
    "user_id": "user123",
    "date": "2024-01-01",
    "food_item": "chicken",
    "quantity": 2.5,
    "notes": "Leftover from lunch"
  }

GET /wastage
- Headers: {"Authorization": "Bearer <token>"}
- Response: {"wastage_records": [...]}

GET /wastage/analysis
- Headers: {"Authorization": "Bearer <token>"}
- Response: {"analysis": {"apple": 5.0, "banana": 3.2}}
```

### Food Alternatives Endpoints
```
POST /food-alternatives
- Body: {"food_name": "apple"}
- Response: {
    "input_food": "apple",
    "input_food_nutrients": {...},
    "nutrients_message": "Major nutrients: ...",
    "alternatives": [{"food_name": "pear", "similarity": "85.2%"}]
  }

POST /menu-alternatives
- Body: {"menu": ["chicken", "rice", "broccoli"]}
- Response: {"menu_alternatives": [...]}
```

### Waste Prediction & Analysis Endpoints
```
POST /waste-prediction
- Body: {
    "user_id": "user123",
    "recent_waste": [{"quantity": 2.5}, {"quantity": 1.8}],
    "menu_items": ["chicken", "rice", "broccoli"],
    "day_of_week": 2
  }
- Response: {
    "prediction": 4.2,
    "analysis": {
      "weekly_waste": {...},
      "waste_by_item": {...},
      "high_waste_items": {...}
    },
    "visualizations": {
      "weekly_trend": "base64_image_data",
      "waste_by_item": "base64_image_data"
    }
  }
```

## 🗄️ Database Schema (Supabase)

### Tables
- **wastage_records**
  - user_id (string)
  - date (ISO date string)
  - food_item (string)
  - quantity (float)
  - notes (string, optional)

## 🧪 Testing

### Automated Testing
```bash
# Run comprehensive endpoint tests
python Backend/test_all_endpoints_updated.py
```

### Manual Testing
```bash
# Start the server
python Backend/main.py

# Server runs on http://localhost:8002
# Use tools like Postman, curl, or the test script
```

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- Supabase account and project
- Virtual environment

### Installation
```bash
cd Backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Setup
1. Copy `.env` and update Supabase credentials
2. Ensure nutrition_data.csv is in database/ folder
3. Ensure best_lasso_model.pkl is in model/ folder

### Running the Application
```bash
python main.py
```

## 📊 Data Flow

1. **User Authentication**: Frontend → Supabase Auth → JWT Token
2. **Waste Tracking**: Frontend → API → Supabase Database
3. **Food Alternatives**: Frontend → API → Nutrition Data Processing
4. **Waste Prediction**: Frontend → API → ML Model → Analysis → Visualizations

## 🔒 Security Features

- JWT token authentication
- User-specific data isolation
- Input validation with Pydantic
- Error handling and logging
- Supabase RLS (Row Level Security) recommended

## 📈 Performance Optimizations

- Optimized waste prediction model (50 features vs 700+)
- Efficient database queries
- Base64 image encoding for visualizations
- Asynchronous processing where applicable

## 🔄 Integration with Frontend

### Authentication Flow
1. User signs up/logs in via frontend
2. Frontend receives JWT token
3. Include token in Authorization header for protected endpoints

### Data Formats
- All responses in JSON format
- Images returned as base64-encoded strings
- Dates in ISO format
- Quantities as floats

### Error Handling
- HTTP status codes (200, 400, 401, 500)
- Descriptive error messages
- Consistent response structure

## 🚀 Deployment Considerations

- Environment variables for production
- Database connection pooling
- API rate limiting
- Monitoring and logging
- HTTPS in production
- CORS configuration for frontend domains

## 📞 Support

For frontend integration questions:
- Refer to this documentation
- Use the test script to understand API responses
- Check server logs for debugging
- Ensure proper authentication headers

---

**Last Updated**: January 2024
**API Version**: v1.0
**Server Port**: 8002
