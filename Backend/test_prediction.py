import pandas as pd
from predict_waste import predict_waste

# Test with 4 features
print("Testing with 4 features:")
data_4 = pd.DataFrame({
    'meals_served': [100, 200],
    'kitchen_staff': [5, 10],
    'temperature_C': [25.0, 30.0],
    'humidity_percent': [50.0, 60.0]
})
predictions_4 = predict_waste(data_4)
print("Predictions:", predictions_4)

# Test with 5 features
print("\nTesting with 5 features:")
data_5 = pd.DataFrame({
    'meals_served': [150, 250],
    'kitchen_staff': [7, 12],
    'temperature_C': [22.0, 28.0],
    'humidity_percent': [55.0, 65.0],
    'day_of_week': [1, 3]
})
predictions_5 = predict_waste(data_5)
print("Predictions:", predictions_5)

# Test with 6 features
print("\nTesting with 6 features:")
data_6 = pd.DataFrame({
    'meals_served': [120, 180],
    'kitchen_staff': [6, 9],
    'temperature_C': [24.0, 26.0],
    'humidity_percent': [52.0, 58.0],
    'day_of_week': [2, 4],
    'special_event': [0, 1]
})
predictions_6 = predict_waste(data_6)
print("Predictions:", predictions_6)

print("\nAll tests completed successfully!")
