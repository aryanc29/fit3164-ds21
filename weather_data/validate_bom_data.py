"""
BOM Data Validation Script
Quick validation of CSV file structure and sample data quality
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_csv_file(file_path: Path):
    """Validate a single CSV file"""
    print(f"\n📁 Analyzing: {file_path.name}")
    print("-" * 50)
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        encoding_used = None
        
        for encoding in encodings:
            try:
                # Try to read first few lines with this encoding
                test_df = pd.read_csv(file_path, encoding=encoding, nrows=1)
                encoding_used = encoding
                print(f"✅ Using encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if not encoding_used:
            print("❌ Could not determine file encoding")
            return False
        
        # Try to read with different skip rows to find data start
        skip_rows = 8  # Default for BOM files
        for test_skip in [8, 9, 10, 11, 12]:
            try:
                df = pd.read_csv(file_path, encoding=encoding_used, skiprows=test_skip, nrows=5)
                if 'Date' in df.columns or 'Station Name' in df.columns:
                    skip_rows = test_skip
                    print(f"✅ Data starts at line {skip_rows + 1}")
                    break
            except:
                continue
        
        # Read full file with detected encoding and skip
        df = pd.read_csv(file_path, encoding=encoding_used, skiprows=skip_rows)
        
        print(f"📊 Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"🏷️  Columns: {list(df.columns)}")
        
        # Check for expected columns
        expected_columns = ['Date', 'Station Name']
        weather_columns = ['Evapotranspiration', 'Rain', 'Temperature', 'Humidity', 'Wind', 'Solar']
        
        has_date = any('Date' in col for col in df.columns)
        has_station = any('Station' in col for col in df.columns)
        has_weather = any(any(w in col for w in weather_columns) for col in df.columns)
        
        print(f"✅ Has Date column: {has_date}")
        print(f"✅ Has Station column: {has_station}")
        print(f"✅ Has Weather data: {has_weather}")
        
        # Sample data
        if len(df) > 0:
            print("\n📋 Sample data (first 3 rows):")
            print(df.head(3).to_string(index=False))
            
            # Check for missing data
            missing_counts = df.isnull().sum()
            if missing_counts.sum() > 0:
                print(f"\n⚠️  Missing data summary:")
                for col, count in missing_counts.items():
                    if count > 0:
                        percentage = (count / len(df)) * 100
                        print(f"   {col}: {count} ({percentage:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def main():
    """Main validation function"""
    data_dir = Path("./data/bom_data")
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Get all CSV files
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in {data_dir}")
        return
    
    print(f"🔍 Found {len(csv_files)} CSV files")
    
    # Validate a sample of files
    sample_files = csv_files[:5]  # First 5 files
    
    print("="*60)
    print("BOM DATA VALIDATION REPORT")
    print("="*60)
    
    successful = 0
    for file_path in sample_files:
        if validate_csv_file(file_path):
            successful += 1
    
    print("\n" + "="*60)
    print(f"SUMMARY: {successful}/{len(sample_files)} files validated successfully")
    print("="*60)
    
    if successful == len(sample_files):
        print("✅ All sample files look good! Ready for ingestion.")
    else:
        print("⚠️  Some files have issues. Check validation output above.")

if __name__ == "__main__":
    main()
