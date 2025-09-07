from typing import Union, List, Dict
from fastapi import FastAPI, HTTPException
import pandas as pd
import joblib
from pydantic import BaseModel

app = FastAPI()

# Load the model and preprocessor at startup
try:
    preprocessor = joblib.load('lasso_preprocessor.joblib')
    model = joblib.load('best_lasso_model.joblib')
except FileNotFoundError:
    raise RuntimeError("Model or preprocessor files not found. Please train the model first.")

class PredictionInput(BaseModel):
    data: List[Dict[str, Union[str, int, float]]]

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/predict")
def predict_waste(input_data: PredictionInput):
    """
    Predict food waste based on input features.
    Expects a list of dictionaries, each representing a row of features.
    Handles any number of features by filling missing ones with defaults.
    """
    try:
        # Convert input to DataFrame
        df = pd.DataFrame(input_data.data)

        # Get expected columns
        expected_num_cols = preprocessor.named_transformers_['num'].feature_names_in_
        expected_cat_cols = preprocessor.named_transformers_['cat'].feature_names_in_

        # Fill missing columns
        for col in expected_num_cols:
            if col not in df.columns:
                df[col] = 0

        for col in expected_cat_cols:
            if col not in df.columns:
                df[col] = 'unknown'

        # Order columns
        all_expected_cols = list(expected_num_cols) + list(expected_cat_cols)
        df = df[all_expected_cols]

        # Preprocess and predict
        X_processed = preprocessor.transform(df)
        predictions = model.predict(X_processed)

        # Return predictions
        return {"predictions": predictions.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

@app.post("/logs")
def post_logs():
    pass

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
