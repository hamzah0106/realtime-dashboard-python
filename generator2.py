import pandas as pd
import random
import time

# Function to generate random data for symbols (X, Y, Z) and their values
def generate_data():
    # List of symbols
    symbols = ['X', 'Y', 'Z']
    
    # Generate random percentage values for Value1 to Value6
    data = {
        "Symbol": symbols,
        "Value1": [f"{random.randint(5, 15)}%" for _ in symbols],
        "Value2": [f"{random.randint(5, 15)}%" for _ in symbols],
        "Value3": [f"{random.randint(-10, 20)}%" for _ in symbols],
        "Value4": [f"{random.randint(-10, 20)}%" for _ in symbols],
        "Value5": [f"{random.randint(-5, 15)}%" for _ in symbols],
        "Value6": [f"{random.randint(5, 25)}%" for _ in symbols],
    }
    
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(data)
    return df

# Function to overwrite the CSV file with new data
def overwrite_csv(csv_file_path):
    # Generate new data
    new_data = generate_data()
    
    # Write the new data to the CSV file, overwriting the existing data
    new_data.to_csv(csv_file_path, index=False)
    
    print(f"Data updated and saved to {csv_file_path}")

# Main loop to periodically update and overwrite the CSV file every specified interval
def process_csv(csv_file_path, update_interval):
    while True:
        # Overwrite the CSV file with new data
        overwrite_csv(csv_file_path)
        
        # Wait for the specified update interval (in seconds) before generating new data
        time.sleep(update_interval)

# Specify the path to your CSV file
csv_file_path = 'scenario2.csv'  # Replace with your actual CSV file path

# Initial update interval (10 seconds)
update_interval = 10  # Can be changed dynamically

# Run the data generation and file overwriting function
process_csv(csv_file_path, update_interval)
