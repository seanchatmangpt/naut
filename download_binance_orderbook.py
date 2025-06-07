import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import requests
import gzip
import io

def download_binance_orderbook(symbol: str, date: str, output_dir: str):
    """
    Download Binance orderbook data for a specific date using their official AWS S3 data.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        date: Date in YYYY-MM-DD format
        output_dir: Directory to save the files
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir).expanduser() / "Data" / "Binance"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convert date to Binance's format (YYYY-MM-DD)
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    date_str = date_obj.strftime("%Y-%m-%d")
    
    # Base URL for Binance's AWS S3 data
    base_url = "https://data.binance.vision/data/spot/daily/depth"
    
    # File patterns for the data we need
    files = [
        f"{symbol}-depth-snapshots-{date_str}.zip",  # Orderbook snapshots
        f"{symbol}-depth-{date_str}.zip",  # Orderbook updates
    ]
    
    for file in files:
        url = f"{base_url}/{symbol}/{file}"
        print(f"\nDownloading {file}...")
        
        try:
            # Download the file
            response = requests.get(url)
            response.raise_for_status()
            
            # Save the file
            file_path = output_path / file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Successfully downloaded {file}")
            
            # Process the file based on its type
            if "snapshots" in file:
                # Process snapshots
                df = pd.read_csv(file_path, compression='zip')
                output_file = output_path / f"{symbol}_T_DEPTH_{date}_depth_snap.csv"
                df.to_csv(output_file, index=False)
                print(f"Processed snapshots saved to {output_file}")
            else:
                # Process updates
                df = pd.read_csv(file_path, compression='zip')
                output_file = output_path / f"{symbol}_T_DEPTH_{date}_depth_update.csv"
                df.to_csv(output_file, index=False)
                print(f"Processed updates saved to {output_file}")
            
            # Clean up the zip file
            os.remove(file_path)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"File not found: {file}")
            else:
                print(f"Error downloading {file}: {e}")
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    print(f"\nDownload complete! Files saved to {output_path}")

if __name__ == "__main__":
    # Download BTCUSDT orderbook data for November 1st, 2022
    download_binance_orderbook(
        symbol="BTCUSDT",
        date="2022-11-01",
        output_dir="~/Downloads"
    ) 