import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from pathlib import Path
from typing import List, Tuple
import pytz

class SyntheticOrderBookGenerator:
    def __init__(
        self,
        symbol: str = "BTCUSDT",
        start_price: float = 20000.0,
        volatility: float = 0.02,
        num_levels: int = 20,
        base_volume: float = 1.0,
        update_frequency_ms: int = 100,
        start_time: datetime = None,
        duration_hours: int = 24,
    ):
        self.symbol = symbol
        self.start_price = start_price
        self.volatility = volatility
        self.num_levels = num_levels
        self.base_volume = base_volume
        self.update_frequency_ms = update_frequency_ms
        self.start_time = start_time or datetime(2022, 11, 1, tzinfo=pytz.UTC)
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        
        # Initialize order book state
        self.current_price = start_price
        self.bids: List[Tuple[float, float]] = []  # (price, quantity)
        self.asks: List[Tuple[float, float]] = []  # (price, quantity)
        
    def _generate_level_volumes(self, is_bid: bool) -> List[float]:
        """Generate realistic volume distribution for order book levels."""
        volumes = []
        for i in range(self.num_levels):
            # Exponential decay of volumes as we move away from mid price
            decay = np.exp(-0.5 * i)
            # Add some randomness
            volume = self.base_volume * decay * (0.8 + 0.4 * random.random())
            volumes.append(volume)
        return volumes

    def _generate_snapshot(self) -> pd.DataFrame:
        """Generate initial order book snapshot."""
        # Generate bid prices (below current price)
        bid_prices = [self.current_price * (1 - 0.0001 * i) for i in range(1, self.num_levels + 1)]
        bid_volumes = self._generate_level_volumes(is_bid=True)
        
        # Generate ask prices (above current price)
        ask_prices = [self.current_price * (1 + 0.0001 * i) for i in range(1, self.num_levels + 1)]
        ask_volumes = self._generate_level_volumes(is_bid=False)
        
        # Create snapshot data
        data = []
        timestamp = int(self.start_time.timestamp() * 1000)
        
        # Add bids
        for price, volume in zip(bid_prices, bid_volumes):
            data.append({
                'timestamp': timestamp,
                'symbol': self.symbol,
                'side': 'bids',
                'price': price,
                'quantity': volume,
                'update_id': 0,
            })
            
        # Add asks
        for price, volume in zip(ask_prices, ask_volumes):
            data.append({
                'timestamp': timestamp,
                'symbol': self.symbol,
                'side': 'asks',
                'price': price,
                'quantity': volume,
                'update_id': 0,
            })
            
        return pd.DataFrame(data)

    def _generate_updates(self) -> pd.DataFrame:
        """Generate order book updates."""
        data = []
        current_time = self.start_time
        update_id = 1
        
        while current_time < self.end_time:
            # Random walk for price
            price_change = self.current_price * self.volatility * np.random.normal(0, 1) * np.sqrt(self.update_frequency_ms / 1000)
            self.current_price += price_change
            
            # Decide if we're updating bids or asks
            side = random.choice(['bids', 'asks'])
            
            # Generate new price and quantity
            if side == 'bids':
                price = self.current_price * (1 - 0.0001 * random.randint(1, self.num_levels))
            else:
                price = self.current_price * (1 + 0.0001 * random.randint(1, self.num_levels))
                
            quantity = self.base_volume * random.random()
            
            # Randomly decide if this is an update or deletion
            if random.random() < 0.1:  # 10% chance of deletion
                quantity = 0
                
            data.append({
                'timestamp': int(current_time.timestamp() * 1000),
                'symbol': self.symbol,
                'side': side,
                'price': price,
                'quantity': quantity,
                'update_id': update_id,
            })
            
            current_time += timedelta(milliseconds=self.update_frequency_ms)
            update_id += 1
            
        return pd.DataFrame(data)

    def generate_data(self, output_dir: str = "data"):
        """Generate and save both snapshot and update files."""
        output_path = Path(output_dir) / "Binance"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate and save snapshot
        snapshot_df = self._generate_snapshot()
        snapshot_file = output_path / f"{self.symbol}_T_DEPTH_{self.start_time.strftime('%Y-%m-%d')}_depth_snap.csv"
        snapshot_df.to_csv(snapshot_file, index=False)
        print(f"Generated snapshot file: {snapshot_file}")
        
        # Generate and save updates
        updates_df = self._generate_updates()
        updates_file = output_path / f"{self.symbol}_T_DEPTH_{self.start_time.strftime('%Y-%m-%d')}_depth_update.csv"
        updates_df.to_csv(updates_file, index=False)
        print(f"Generated updates file: {updates_file}")

if __name__ == "__main__":
    # Create data directory in user's home directory
    data_dir = str(Path.home() / "Downloads" / "Data")
    
    # Generate synthetic data
    generator = SyntheticOrderBookGenerator(
        symbol="BTCUSDT",
        start_price=20000.0,
        volatility=0.02,
        num_levels=20,
        base_volume=1.0,
        update_frequency_ms=100,
        start_time=datetime(2022, 11, 1, tzinfo=pytz.UTC),
        duration_hours=24,
    )
    
    generator.generate_data(data_dir) 