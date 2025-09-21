import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
# import matplotlib.pyplot as plt  # Visualization disabled
# import seaborn as sns  # Visualization disabled
# import base64  # Visualization disabled
# from io import BytesIO  # Visualization disabled
from fastapi import HTTPException
# from Backend.supabase_client import supabase
import logging
import sys
import os

logger = logging.getLogger("uvicorn.error")

class WastePredictionModel:
    def __init__(self, model_path='best_lasso_model.joblib', preprocessor_path='lasso_preprocessor.joblib'):
        """
        Initialize the WastePredictionModel.
        
        Args:
            model_path (str): Path to the trained model file
            preprocessor_path (str): Path to the preprocessor file
        """
        # Always define all class attributes first - before any possible exceptions
        self.logger = logger
        # Initialize model-related attributes
        self.lasso_model_path = model_path  # Store the model path
        self.preprocessor_path = preprocessor_path  # Store the preprocessor path
        self.lasso_model = None
        self.preprocessor = None
        
        # Define feature-related attributes (excluding date to avoid preprocessing issues)
        self.feature_columns = [
            'ID', 'meals_served', 'kitchen_staff', 'temperature_C',
            'humidity_percent', 'day_of_week', 'special_event', 'past_waste_kg',
            'staff_experience', 'waste_category'
        ]
        self.numeric_features = [
            'ID', 'meals_served', 'kitchen_staff', 'temperature_C',
            'humidity_percent', 'day_of_week', 'special_event', 'past_waste_kg'
        ]
        self.categorical_features = ['staff_experience', 'waste_category']
        
        try:
            # Get base directory and construct paths
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Build full paths while preserving the original paths
            model_full_path = os.path.join(base_dir, self.lasso_model_path)
            preprocessor_full_path = os.path.join(base_dir, self.preprocessor_path)
            
            # Update paths to full paths after confirming originals are saved
            self.lasso_model_path = model_full_path
            self.preprocessor_path = preprocessor_full_path
            
            # Validate file existence
            if not os.path.exists(self.lasso_model_path):
                raise FileNotFoundError(f"Model file not found: {self.lasso_model_path}")
            if not os.path.exists(self.preprocessor_path):
                raise FileNotFoundError(f"Preprocessor file not found: {self.preprocessor_path}")
            
            # Load model and preprocessor
            try:
                self.logger.info(f"Attempting to load model from: {self.lasso_model_path}")
                self.lasso_model = joblib.load(self.lasso_model_path)
                self.logger.info("Successfully loaded LASSO model")
                
                self.logger.info(f"Attempting to load preprocessor from: {self.preprocessor_path}")
                self.preprocessor = joblib.load(self.preprocessor_path)
                self.logger.info("Successfully loaded preprocessor")
                
                # Verify the model and preprocessor are valid
                if not hasattr(self.lasso_model, 'predict'):
                    raise ValueError("Loaded model does not have 'predict' method")
                if not hasattr(self.preprocessor, 'transform'):
                    raise ValueError("Loaded preprocessor does not have 'transform' method")
                    
            except Exception as e:
                self.logger.error(f"Failed to load model files: {str(e)}")
                raise ValueError(f"Failed to load model files: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error initializing WastePredictionModel: {str(e)}")
            raise ValueError(f"Failed to initialize model: {str(e)}")

    def prepare_features(self, recent_waste, menu_items, day_of_week):
        """
        Prepare features matching the training data columns for flexible prediction.
        Maps API input to expected model features.
        """
        features = {}

        # Map API input to training features (excluding date)
        features['ID'] = int(0)  # Default ID
        features['meals_served'] = float(len(menu_items) * 100 if menu_items else 100)  # Estimate based on menu items
        features['kitchen_staff'] = float(10)  # Default value
        features['temperature_C'] = float(25.0)  # Default value
        features['humidity_percent'] = float(60.0)  # Default value
        features['day_of_week'] = int(day_of_week)
        features['special_event'] = int(0)  # Default: no special event
        features['past_waste_kg'] = float(sum([record.get('quantity', 0) for record in recent_waste]) if recent_waste else 0)
        features['staff_experience'] = str('intermediate')  # Default experience level
        features['waste_category'] = str('mixed')  # Default category

        # Convert to DataFrame and ensure all required columns are present
        feature_df = pd.DataFrame([features])
        
        # Ensure all expected features are present
        for col in self.feature_columns:
            if col not in feature_df.columns:
                if col in self.numeric_features:
                    feature_df[col] = 0
                else:
                    feature_df[col] = 'unknown'
                    
        # Convert numeric features to float
        for col in self.numeric_features:
            feature_df[col] = feature_df[col].astype(float)
            
        # Convert categorical features to string
        for col in self.categorical_features:
            feature_df[col] = feature_df[col].astype(str)
            
        # Reorder columns to match training data
        feature_df = feature_df[self.feature_columns]

        # Fill NaN values with 0 and replace infinities
        feature_df = feature_df.fillna(0).replace([np.inf, -np.inf], 0)

        self.logger.info(f"Prepared features matching training data: {list(features.keys())}")
        self.logger.info(f"Feature DataFrame dtypes:\n{feature_df.dtypes}")
        return feature_df

    def predict_waste(self, recent_waste, menu_items, day_of_week):
        """
        Make prediction using the loaded lasso model.
        
        Args:
            recent_waste (list): List of recent waste records
            menu_items (list): List of menu items
            day_of_week (int): Day of the week (0-6)
            
        Returns:
            dict: Contains prediction value and analysis
        """
        # Prepare features from input
        features = self.prepare_features(recent_waste, menu_items, day_of_week)
        try:
            # Ensure features are properly formatted
            if not isinstance(features, pd.DataFrame):
                features = pd.DataFrame([features]) if isinstance(features, dict) else pd.DataFrame(features)
            
            # Ensure all required columns are present
            for col in self.feature_columns:
                if col not in features.columns:
                    if col in self.numeric_features:
                        features[col] = 0
                    else:
                        features[col] = 'unknown'
            
            # Convert numeric features to float
            for col in self.numeric_features:
                features[col] = features[col].astype(float)
            
            # Convert categorical features to string
            for col in self.categorical_features:
                features[col] = features[col].astype(str)
            
            # Reorder columns to match training data
            features = features[self.feature_columns]
            
            # Apply preprocessing
            preprocessed_features = self.preprocessor.transform(features)
            
            # Make prediction
            prediction = self.lasso_model.predict(preprocessed_features)
            
            # Ensure non-negative prediction and round to 2 decimal places
            predicted_value = max(0.0, float(prediction[0]))
            return round(predicted_value, 2)
            
        except Exception as e:
            self.logger.error(f"Error in predict_waste: {str(e)}")
            raise ValueError(f"Failed to make prediction: {str(e)}")

    def get_prediction_and_analysis(self, user_id, recent_waste, menu_items, day_of_week):
        """
        Get waste prediction and analysis based on input parameters.
        
        Args:
            user_id (str): User identifier
            recent_waste (list): List of recent waste records
            menu_items (list): List of menu items
            day_of_week (int): Day of the week (0-6)
            
        Returns:
            dict: Prediction results, analysis, and visualizations
        """
        try:
            # Input validation
            if not isinstance(day_of_week, (int, float)) or day_of_week < 0 or day_of_week > 6:
                raise ValueError("day_of_week must be an integer between 0 and 6")
                
            # Prepare features and make prediction
            features = self.prepare_features(recent_waste, menu_items, day_of_week)
            preprocessed_features = self.preprocessor.transform(features)
            
            # Get raw prediction
            prediction = self.lasso_model.predict(preprocessed_features)
            predicted_waste = max(0.0, float(prediction[0]))
            
            # Calculate recent waste statistics
            total_recent_waste = sum(record.get('quantity', 0) for record in recent_waste) if recent_waste else 0
            avg_recent_waste = total_recent_waste / len(recent_waste) if recent_waste else 0
            
            # Get historical analysis
            historical_data = self.get_historical_data(user_id)
            historical_analysis = self.analyze_trends(historical_data)
            
            # Generate visualizations
            visualizations = self.generate_visualizations(historical_analysis)
            
            # Prepare comprehensive response
            return {
                "prediction": {
                    "predicted_waste_kg": round(predicted_waste, 2),
                    "confidence_level": "medium"  # Could be enhanced based on model metrics
                },
                "analysis": {
                    "recent_waste_total_kg": round(float(total_recent_waste), 2),
                    "recent_waste_average_kg": round(float(avg_recent_waste), 2),
                    "menu_item_count": len(menu_items),
                    "day_of_week": int(day_of_week),
                    "trend": "increasing" if predicted_waste > avg_recent_waste else "decreasing",
                    "historical": historical_analysis
                },
                "visualizations": visualizations
            }
        except Exception as e:
            self.logger.error(f"Error in get_prediction_and_analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

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

        # Debug: print keys before conversion
        print(f"Weekly waste keys before: {list(weekly_waste.keys())}")
        print(f"Weekly waste keys types before: {[type(k) for k in weekly_waste.keys()]}")

        # Convert weekly_waste to dict with string keys
        weekly_waste_dict = {str(k): v for k, v in weekly_waste.items()}
        waste_by_item_dict = waste_by_item.to_dict()
        high_waste_items_dict = high_waste_items

        # Debug: print types of keys
        print(f"Weekly waste keys types: {[type(k) for k in weekly_waste_dict.keys()]}")
        print(f"Waste by item keys types: {[type(k) for k in waste_by_item_dict.keys()]}")
        print(f"High waste items keys types: {[type(k) for k in high_waste_items_dict.keys()]}")

        # Debug: print the dicts
        print(f"Weekly waste dict: {weekly_waste_dict}")
        print(f"Waste by item dict: {waste_by_item_dict}")
        print(f"High waste items dict: {high_waste_items_dict}")

        # Check for Timestamp in values
        def check_for_timestamp(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    check_for_timestamp(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_for_timestamp(v, f"{path}[{i}]")
            elif hasattr(obj, '__class__') and 'Timestamp' in str(obj.__class__):
                print(f"Found Timestamp at {path}: {obj}")

        check_for_timestamp(weekly_waste_dict, "weekly_waste_dict")
        check_for_timestamp(waste_by_item_dict, "waste_by_item_dict")
        check_for_timestamp(high_waste_items_dict, "high_waste_items_dict")

        return {
            'weekly_waste': weekly_waste_dict,
            'waste_by_item': waste_by_item_dict,
            'high_waste_items': high_waste_items_dict
        }

    def generate_visualizations(self, analysis_data):
        """Generate visualizations for waste analysis"""
        # Temporarily returning empty dict while visualizations are disabled
        return {}
        
        # # Set style for better-looking plots
        # # plt.style.use('seaborn-v0_8')  # Using the updated seaborn style name - commented out
        
        # # Line chart for weekly waste
        # if 'weekly_waste' in analysis_data:
        #     plt.figure(figsize=(10, 6))
        #     series = pd.Series(analysis_data['weekly_waste'])
        #     ax = series.plot(kind='line', marker='o', linewidth=2)
        #     plt.title('Weekly Waste Trend Analysis', fontsize=14, pad=20)
        #     plt.xlabel('Week', fontsize=12)
        #     plt.ylabel('Waste Quantity (kg)', fontsize=12)
        #     plt.grid(True, linestyle='--', alpha=0.7)
            
        #     # Add value labels on points
        #     for i, v in enumerate(series):
        #         ax.text(i, v, f'{v:.1f}', ha='center', va='bottom')
                
        #     plt.tight_layout()
        #     buf = BytesIO()
        #     plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        #     buf.seek(0)
        #     images['weekly_trend'] = base64.b64encode(buf.read()).decode('utf-8')
        #     plt.close()

        # # Bar chart for waste by item
        # if 'waste_by_item' in analysis_data:
        #     plt.figure(figsize=(10, 6))
        #     series = pd.Series(analysis_data['waste_by_item'])
        #     ax = series.plot(kind='bar', color='skyblue')
        #     plt.title('Waste Analysis by Food Item', fontsize=14, pad=20)
        #     plt.xlabel('Food Item', fontsize=12)
        #     plt.ylabel('Total Waste Quantity (kg)', fontsize=12)
        #     plt.xticks(rotation=45, ha='right')
        #     plt.grid(True, axis='y', linestyle='--', alpha=0.7)
            
        #     # Add value labels on bars
        #     for i, v in enumerate(series):
        #         ax.text(i, v, f'{v:.1f}', ha='center', va='bottom')
                
        #     plt.tight_layout()
        #     buf = BytesIO()
        #     plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        #     buf.seek(0)
        #     images['waste_by_item'] = base64.b64encode(buf.read()).decode('utf-8')
        #     plt.close()

        # return images


