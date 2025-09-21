import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt  # Visualization disabled
import joblib

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_squared_error, r2_score

def train_flexible_lasso_model(data_path='DataSet/train.csv', save_path='best_lasso_model.joblib', preprocessor_path='lasso_preprocessor.joblib'):
    """
    Train a flexible Lasso model that can handle any number of features.
    The model uses a preprocessing pipeline that dynamically identifies numerical and categorical columns.
    """
    # Step 1: Load and clean data
    df = pd.read_csv(data_path)
    df.dropna(inplace=True)
    
    # Drop the date column since it's not needed for predictions
    df = df.drop(columns=['date'], errors='ignore')

    # Step 2: Separate features and target
    X = df.drop(columns=['food_waste_kg'], axis=1)
    y = df['food_waste_kg']

    # Step 3: Identify column types dynamically
    numerical_columns = X.select_dtypes(include=['int64', 'float64']).columns
    categorical_columns = X.select_dtypes(include=['object']).columns

    # Step 4: Define pipelines for numerical and categorical features
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy='median')),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("one_hot", OneHotEncoder(handle_unknown='ignore')),
        ("scaler", StandardScaler(with_mean=False))
    ])

    preprocessor = ColumnTransformer([
        ("num", num_pipeline, numerical_columns),
        ("cat", cat_pipeline, categorical_columns)
    ])

    # Step 5: Preprocess features
    X_processed = preprocessor.fit_transform(X)

    # Step 6: Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, random_state=42)

    # Step 7: Define Lasso model with higher max_iter for convergence
    lasso = Lasso(max_iter=10000)

    # Step 8: Hyperparameter tuning with GridSearchCV
    param_grid = {
        'alpha': np.logspace(-4, 2, 100)  # 0.0001 to 100
    }

    grid_search = GridSearchCV(estimator=lasso, param_grid={'alpha': param_grid['alpha']},
                               scoring='neg_mean_squared_error', cv=5, n_jobs=-1)

    grid_search.fit(X_train, y_train)

    # Step 9: Best model
    best_lasso = grid_search.best_estimator_
    print("✅ Best alpha:", grid_search.best_params_['alpha'])

    # Step 10: Predict and evaluate
    y_pred = best_lasso.predict(X_test)
    y_test = y_test.reset_index(drop=True)

    # Step 11: Create result DataFrame
    pred_df = pd.DataFrame({
        'Actual Value': y_test,
        'Predicted Value': y_pred,
        'Difference': y_test - y_pred
    })

    # Step 12: Evaluation metrics
    print("MSE:", mean_squared_error(y_test, y_pred))
    print("R2 Score:", r2_score(y_test, y_pred))

    # Step 13: Save the preprocessing pipeline and model for reuse
    joblib.dump(preprocessor, preprocessor_path)
    joblib.dump(best_lasso, save_path)
    print(f"Model saved to {save_path}")
    print(f"Preprocessor saved to {preprocessor_path}")

    # Step 14: Show results
    print(pred_df.head())

    # Step 15: Plot alpha vs MSE - Visualization disabled
    # alphas = param_grid['alpha']
    # mse_scores = -grid_search.cv_results_['mean_test_score']

    # plt.figure(figsize=(8, 5))
    # plt.plot(alphas, mse_scores, marker='o')
    # plt.xscale('log')
    # plt.xlabel('Alpha')
    # plt.ylabel('Negative Mean Squared Error')
    # plt.title('Alpha vs MSE (Cross-validation)')
    # plt.grid(True)
    # plt.show()

if __name__ == "__main__":
    train_flexible_lasso_model()
