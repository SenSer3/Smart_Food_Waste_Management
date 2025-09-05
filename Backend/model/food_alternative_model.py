import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import difflib
import logging

class FoodAlternativeModel:
    def __init__(self, nutrition_data_path):
        self.logger = logging.getLogger("uvicorn.error")
        self.nutrition_data = pd.read_csv(nutrition_data_path, encoding='latin1')
        # Save original columns for nutrient names before renaming
        original_cols = list(self.nutrition_data.columns)
        # Fix malformed header: rename second column to 'food_name'
        cols = list(self.nutrition_data.columns)
        if len(cols) > 1:
            cols[1] = 'food_name'
            self.nutrition_data.columns = cols
        self.food_names = self.nutrition_data['food_name'].values
        # Select nutritional columns for similarity comparison
        self.nutrition_features = self.nutrition_data.drop(columns=['food_code', 'food_name'])
        # Store nutrient names from original columns excluding 'food_code' and the second column (food_name)
        self.nutrient_names = [col for col in original_cols if col not in ['food_code', original_cols[1]]]
        # Convert all nutrition feature columns to numeric, coercing errors to NaN
        self.nutrition_features = self.nutrition_features.apply(pd.to_numeric, errors='coerce')
        # Fill NaN values with column mean
        self.nutrition_features = self.nutrition_features.fillna(self.nutrition_features.mean())
        # For columns that still have NaNs (all values NaN), fill with zeros
        self.nutrition_features = self.nutrition_features.fillna(0)
        # Log NaN counts after filling
        nan_counts = self.nutrition_features.isna().sum().sum()
        if nan_counts > 0:
            self.logger.error(f"NaN values remain in nutrition_features after fillna: {nan_counts}")

        # Log min and max values for each column before normalization
        min_vals = self.nutrition_features.min()
        max_vals = self.nutrition_features.max()
        for col in self.nutrition_features.columns:
            self.logger.info(f"Column '{col}': min={min_vals[col]}, max={max_vals[col]}")

        # Avoid division by zero in normalization
        denom = max_vals - min_vals
        denom[denom == 0] = 1  # replace 0 with 1 to avoid NaNs

        # Normalize nutritional features for better similarity comparison
        self.normalized_features = (self.nutrition_features - min_vals) / denom

        # Log NaN counts after normalization
        nan_counts_norm = self.normalized_features.isna().sum().sum()
        if nan_counts_norm > 0:
            self.logger.error(f"NaN values remain in normalized_features after normalization: {nan_counts_norm}")

    def find_closest_food_name(self, food_name):
        # Use difflib to find closest match ignoring case
        food_names_lower = [name.lower() for name in self.food_names]
        matches = difflib.get_close_matches(food_name.lower(), food_names_lower, n=1, cutoff=0.6)
        if matches:
            # Return the original food name with correct case
            idx = food_names_lower.index(matches[0])
            return self.food_names[idx]
        else:
            return None

    def find_alternatives(self, food_name, top_n=5):
        closest_name = self.find_closest_food_name(food_name)
        if not closest_name:
            return {}  # Food not found
        indices = np.where(self.food_names == closest_name)[0]
        idx = indices[0]
        # Compute cosine similarity between the input food and all others
        input_vector = self.normalized_features.iloc[idx].values.reshape(1, -1)

        # Check for NaNs or infinite values and replace with zeros before logging
        if np.isnan(input_vector).any() or np.isinf(input_vector).any():
            self.logger.error(f"Input vector for food '{closest_name}' contains NaN or infinite values. Replacing with zeros.")
            input_vector = np.nan_to_num(input_vector)

        # Log input_vector values after cleaning
        self.logger.info(f"Input vector for food '{closest_name}': {input_vector}")

        # Clean normalized_features to replace NaNs or infinite values with zeros before similarity computation
        if self.normalized_features.isna().any().any() or np.isinf(self.normalized_features.values).any():
            self.logger.error("Normalized features contain NaN or infinite values. Replacing with zeros.")
            self.normalized_features = self.normalized_features.fillna(0)
            self.normalized_features = self.normalized_features.replace([np.inf, -np.inf], 0)

        similarities = cosine_similarity(input_vector, self.normalized_features)[0]
        # Get indices of top_n most similar foods excluding the input food itself
        similar_indices = similarities.argsort()[::-1][1:top_n+1]
        # Prepare alternatives list with similarity as percentage string
        alternatives = [{"food_name": self.food_names[i], "similarity": f"{similarities[i]*100:.2f}%"} for i in similar_indices]

        # Get nutrient values for input food as percentages (0-100), rounded to 2 decimals
        input_nutrients = (self.normalized_features.iloc[idx] * 100).round(2)
        input_nutrients_dict = input_nutrients.to_dict()

        # Replace keys in input_nutrients_dict with nutrient names
        input_nutrients_named = {}
        for i, key in enumerate(input_nutrients_dict.keys()):
            nutrient_name = self.nutrient_names[i] if i < len(self.nutrient_names) else key
            input_nutrients_named[nutrient_name] = input_nutrients_dict[key]

        # Prepare a text message listing major nutrients considered (top 5 by value)
        sorted_nutrients = input_nutrients.sort_values(ascending=False)
        major_nutrients = sorted_nutrients.head(5).index.tolist()
        # Replace major nutrient keys with names
        major_nutrients_named = [self.nutrient_names[i] if i < len(self.nutrient_names) else n for i, n in enumerate(major_nutrients)]
        major_nutrients_str = ", ".join(major_nutrients_named)
        nutrients_message = f"Major nutrients considered: {major_nutrients_str}"

        return {
            "input_food": closest_name,
            "input_food_nutrients": input_nutrients_named,
            "nutrients_message": nutrients_message,
            "alternatives": alternatives
        }
