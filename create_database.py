import pandas as pd
import sqlite3
import re
import os

print("--- Starting ETL (Extract, Transform, Load) Process ---")

# Define file names
crop_csv = "ICRISAT-District Level Data.csv"
rainfall_csv = "Monthly District Avg RainFall 1901 - 2017.csv"
db_name = "samarth.db"

# Check if source files exist
if not os.path.exists(crop_csv) or not os.path.exists(rainfall_csv):
    print(f"Error: Make sure both '{crop_csv}' and '{rainfall_csv}' are in the same directory as this script.")
    exit()

try:
    # --- EXTRACT ---
    print(f"Extracting data from '{crop_csv}' and '{rainfall_csv}'...")
    crop_df = pd.read_csv(crop_csv)
    rainfall_df = pd.read_csv(rainfall_csv)

    # --- TRANSFORM (Rainfall Data) ---
    print("Transforming Rainfall Data...")
    
    # Select the correct columns identified from our earlier debugging
    clean_rainfall_df = rainfall_df[['State', 'District', 'Year', 'final_annual']].copy()
    
    # Rename columns to a standard format
    clean_rainfall_df.rename(columns={
        'State': 'State_Name',
        'District': 'District_Name',
        'Year': 'Year',
        'final_annual': 'Annual_Rainfall_mm'
    }, inplace=True)
    
    # Standardize text data for matching (uppercase, strip whitespace)
    clean_rainfall_df['State_Name'] = clean_rainfall_df['State_Name'].str.strip().str.upper()
    clean_rainfall_df['District_Name'] = clean_rainfall_df['District_Name'].str.strip().str.upper()
    
    print("Rainfall data transformed successfully.")

    # --- TRANSFORM (Crop Data) ---
    print("Transforming Crop Data (Melting from wide to long format)...")
    
    # 1. Identify ID columns (what defines a unique row)
    id_vars = ['State Name', 'Dist Name', 'Year']
    
    # 2. Identify all 'PRODUCTION' columns to be melted
    production_cols = [col for col in crop_df.columns if 'PRODUCTION' in col]
    
    # 3. Use 'pd.melt' to transform from wide to long format
    # This is crucial for making the data queryable
    clean_crop_df = pd.melt(crop_df, 
                            id_vars=id_vars, 
                            value_vars=production_cols, 
                            var_name='Crop_Name', 
                            value_name='Production_Tonnes')
    
    # 4. Clean the new 'Crop_Name' column
    # Removes " PRODUCTION (...)" suffix and extra spaces
    clean_crop_df['Crop_Name'] = clean_crop_df['Crop_Name'].str.replace(r' PRODUCTION \(.*\)', '', regex=True).str.strip().str.upper()

    # 5. Rename and standardize ID columns to match the rainfall data
    clean_crop_df.rename(columns={
        'State Name': 'State_Name', 
        'Dist Name': 'District_Name'
    }, inplace=True)
    clean_crop_df['State_Name'] = clean_crop_df['State_Name'].str.strip().str.upper()
    clean_crop_df['District_Name'] = clean_crop_df['District_Name'].str.strip().str.upper()

    # 6. Drop rows where production is zero or NaN (not useful for analysis)
    clean_crop_df = clean_crop_df[clean_crop_df['Production_Tonnes'] > 0].dropna()

    print("Crop data transformed successfully.")

    # --- LOAD ---
    print(f"Loading transformed data into SQLite database '{db_name}'...")
    
    # Connect to (and create) the SQLite database
    conn = sqlite3.connect(db_name)
    
    # Load the DataFrames into SQL tables
    # 'if_exists='replace'' means the script can be re-run without errors
    clean_crop_df.to_sql('crop_production', conn, if_exists='replace', index=False)
    print("- Created 'crop_production' table.")
    
    clean_rainfall_df.to_sql('rainfall', conn, if_exists='replace', index=False)
    print("- Created 'rainfall' table.")
    
    # Clean up and close the connection
    conn.commit()
    conn.close()
    
    print(f"\n--- ETL Process Complete ---")
    print(f"Database '{db_name}' is ready for Stage 2.")

except FileNotFoundError:
    print(f"Error: One or more CSV files not found. Please check the file names.")
except pd.errors.EmptyDataError:
    print("Error: One of the CSV files is empty.")
except KeyError as e:
    print(f"KeyError: {e}. A required column name was not found in one of the CSVs. Please check the files.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

