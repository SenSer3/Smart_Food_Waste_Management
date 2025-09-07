import pandas as pd
import joblib
import numpy as np

def predict_waste(input_data, model_path='best_lasso_model.joblib', preprocessor_path='lasso_preprocessor.joblib'):
    """
    Predict food waste using the trained Lasso model and preprocessing pipeline.
    This function can handle any number of features by filling missing columns with defaults.

    Parameters:
    - input_data: pandas DataFrame with features for prediction.
    - model_path: Path to the saved Lasso model.
    - preprocessor_path: Path to the saved preprocessing pipeline.

    Returns:
    - predictions: Array of predicted food waste values.
    """
    # Load the preprocessor and model
    preprocessor = joblib.load(preprocessor_path)
    model = joblib.load(model_path)

    # Get the expected columns from the preprocessor
    expected_num_cols = preprocessor.named_transformers_['num'].feature_names_in_
    expected_cat_cols = preprocessor.named_transformers_['cat'].feature_names_in_

    # Fill missing columns with defaults
    for col in expected_num_cols:
        if col not in input_data.columns:
            input_data[col] = 0  # Default for numerical

    for col in expected_cat_cols:
        if col not in input_data.columns:
            input_data[col] = 'unknown'  # Default for categorical

    # Ensure columns are in the correct order
    all_expected_cols = list(expected_num_cols) + list(expected_cat_cols)
    input_data = input_data[all_expected_cols]

    # Preprocess the input data
    try:
        X_processed = preprocessor.transform(input_data)
    except Exception as e:
        raise ValueError(f"Error in preprocessing: {e}")

    # Make predictions
    predictions = model.predict(X_processed)

    return predictions

if __name__ == "__main__":
    # Example usage: Load test data and predict
    test_df = pd.read_csv('DataSet/test.csv')
    print(test_df)
    # Assuming test.csv has the same structure as train.csv without the target
    # For demo, drop 'food_waste_kg' if present, but test.csv might not have it
    if 'food_waste_kg' in test_df.columns:
        test_df = test_df.drop(columns=['food_waste_kg'])

    predictions = predict_waste(test_df)
    print("Predictions:", predictions[:10])  # Show first 10 predictions
