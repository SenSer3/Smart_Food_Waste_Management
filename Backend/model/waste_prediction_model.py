import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
# from Backend.supabase_client import supabase
import logging

logger = logging.getLogger("uvicorn.error")

class WastePredictionModel:
    def __init__(self, lasso_model_path, preprocessor_path='lasso_preprocessor.joblib'):
        self.lasso_model = joblib.load(lasso_model_path)
        self.preprocessor = joblib.load(preprocessor_path)
        self.logger = logger

    def prepare_features(self, recent_waste, menu_items, day_of_week):
        """
        Prepare optimized features - reduced from 700+ to ~50 meaningful features.
        Focuses on quality over quantity for better performance.
        """
        features = {}

        # Basic features from input
        features['recent_waste_quantity'] = sum([record['quantity'] for record in recent_waste]) if recent_waste else 0
        features['num_menu_items'] = len(menu_items) if menu_items else 0
        features['day_of_week'] = day_of_week

        # Day of week one-hot encoding (7 features)
        for i in range(7):
            features[f'day_of_week_{i}'] = 1 if day_of_week == i else 0

        # Reduced menu item features - only essential foods (12 features)
        essential_foods = [
            'chicken', 'beef', 'fish', 'rice', 'bread', 'potato',
            'tomato', 'onion', 'carrot', 'milk', 'cheese', 'eggs'
        ]

        # One-hot encoding for essential menu items
        for food in essential_foods:
            features[f'menu_{food}'] = 1 if food in [item.lower() for item in menu_items] else 0

        # Recent waste features - simplified (4 features)
        if recent_waste:
            quantities = [r['quantity'] for r in recent_waste]
            features['recent_waste_count'] = len(recent_waste)
            features['recent_waste_avg'] = np.mean(quantities)
            features['recent_waste_max'] = max(quantities)
            features['recent_waste_std'] = np.std(quantities) if len(quantities) > 1 else 0
        else:
            features['recent_waste_count'] = 0
            features['recent_waste_avg'] = 0
            features['recent_waste_max'] = 0
            features['recent_waste_std'] = 0

        # Menu diversity features (4 features)
        if menu_items:
            features['menu_unique_items'] = len(set(menu_items))
            features['menu_has_protein'] = 1 if any(item.lower() in ['chicken', 'beef', 'fish', 'eggs'] for item in menu_items) else 0
            features['menu_has_veg'] = 1 if any(item.lower() in ['potato', 'tomato', 'onion', 'carrot'] for item in menu_items) else 0
            features['menu_has_dairy'] = 1 if any(item.lower() in ['milk', 'cheese'] for item in menu_items) else 0
        else:
            features['menu_unique_items'] = 0
            features['menu_has_protein'] = 0
            features['menu_has_veg'] = 0
            features['menu_has_dairy'] = 0

        # Time-based features (4 features)
        current_hour = datetime.now().hour
        features['hour_of_day'] = current_hour
        features['is_breakfast_time'] = 1 if 6 <= current_hour <= 10 else 0
        features['is_lunch_time'] = 1 if 11 <= current_hour <= 15 else 0
        features['is_dinner_time'] = 1 if 17 <= current_hour <= 21 else 0

        # Key interaction features (2 features)
        features['waste_quantity_x_num_items'] = features['recent_waste_quantity'] * features['num_menu_items']
        features['waste_per_item'] = features['recent_waste_quantity'] / max(features['num_menu_items'], 1)

        # Convert to DataFrame
        feature_df = pd.DataFrame([features])

        self.logger.info(f"Prepared {len(features)} optimized features for prediction")
        return feature_df

    def predict_waste(self, features):
        """
        Make prediction using the flexible lasso model that can handle any number of features.
        This function fills missing columns with defaults to match the trained model's expectations.
        """
        # Get the expected columns from the preprocessor
        expected_num_cols = self.preprocessor.named_transformers_['num'].feature_names_in_
        expected_cat_cols = self.preprocessor.named_transformers_['cat'].feature_names_in_

        # Fill missing columns with defaults
        for col in expected_num_cols:
            if col not in features.columns:
                features[col] = 0  # Default for numerical

        for col in expected_cat_cols:
            if col not in features.columns:
                features[col] = 'unknown'  # Default for categorical

        # Ensure columns are in the correct order
        all_expected_cols = list(expected_num_cols) + list(expected_cat_cols)
        features = features[all_expected_cols]

        # Preprocess the input data
        try:
            X_processed = self.preprocessor.transform(features)
        except Exception as e:
            self.logger.error(f"Error in preprocessing: {e}")
            raise ValueError(f"Error in preprocessing: {e}")

        # Make predictions
        predictions = self.lasso_model.predict(X_processed)
        return predictions[0]

    def get_historical_data(self, user_id, days=30):
        # Supabase commented out - returning mock data for testing
        # end_date = datetime.now()
        # start_date = end_date - timedelta(days=days)
        # response = supabase.table("wastage_records").select("*").eq("user_id", user_id).gte("date", start_date.isoformat()).execute()
        # if response.get("error"):
        #     self.logger.error(f"Error fetching historical data: {response['error']}")
        #     return []
        # return response.get("data", [])

        # Mock data for testing
        mock_data = [
            {"date": "2024-01-01", "food_item": "chicken", "quantity": 2.5},
            {"date": "2024-01-02", "food_item": "rice", "quantity": 1.0},
            {"date": "2024-01-03", "food_item": "chicken", "quantity": 3.0},
            {"date": "2024-01-04", "food_item": "potato", "quantity": 1.5},
        ]
        return mock_data

    def analyze_trends(self, historical_data):
        # Analyze trends from historical data
        df = pd.DataFrame(historical_data)
        if df.empty:
            return {"error": "No historical data available"}

        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # Total waste over time (weekly)
        weekly_waste = df.resample('W').sum()['quantity']
        # Waste by food item
        waste_by_item = df.groupby('food_item')['quantity'].sum().sort_values(ascending=False)
        # High-waste items (top 5)
        high_waste_items = waste_by_item.head(5).to_dict()

        return {
            'weekly_waste': weekly_waste.to_dict(),
            'waste_by_item': waste_by_item.to_dict(),
            'high_waste_items': high_waste_items
        }

    def generate_visualizations(self, analysis_data):
        # Generate charts
        images = {}
        # Line chart for weekly waste
        if 'weekly_waste' in analysis_data:
            plt.figure(figsize=(8, 4))
            pd.Series(analysis_data['weekly_waste']).plot(kind='line')
            plt.title('Weekly Waste Trend')
            plt.xlabel('Week')
            plt.ylabel('Waste Quantity')
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            images['weekly_trend'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

        # Bar chart for waste by item
        if 'waste_by_item' in analysis_data:
            plt.figure(figsize=(8, 4))
            pd.Series(analysis_data['waste_by_item']).plot(kind='bar')
            plt.title('Waste by Food Item')
            plt.xlabel('Food Item')
            plt.ylabel('Waste Quantity')
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            images['waste_by_item'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

        return images

    def get_prediction_and_analysis(self, user_id, recent_waste, menu_items, day_of_week):
        # Prepare features
        features = self.prepare_features(recent_waste, menu_items, day_of_week)
        # Predict
        prediction = self.predict_waste(features)
        # Get historical data and analyze
        historical_data = self.get_historical_data(user_id)
        analysis = self.analyze_trends(historical_data)
        # Generate visualizations
        visualizations = self.generate_visualizations(analysis)

        return {
            'prediction': prediction,
            'analysis': analysis,
            'visualizations': visualizations
        }
