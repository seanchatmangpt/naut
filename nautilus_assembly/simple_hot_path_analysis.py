#!/usr/bin/env python3
"""
Simple Nautilus Hot Path Analysis - Core Objects Only
"""
import time
import numpy as np
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.objects import Price, Quantity

def benchmark_price_operations():
    """Benchmark Price object operations"""
    print("💰 Benchmarking Nautilus Price Operations...")
    
    iterations = 1000000
    prices_raw = np.random.uniform(50000, 51000, iterations)
    
    start_time = time.perf_counter_ns()
    
    for price_raw in prices_raw:
        # Hot path - Price creation and operations
        price = Price.from_str(f"{price_raw:.2f}")
        price_value = float(price)
        
    end_time = time.perf_counter_ns()
    total_time = end_time - start_time
    avg_latency = total_time / iterations
    
    print(f"  Iterations: {iterations:,}")
    print(f"  Average latency: {avg_latency:.1f}ns per operation")
    print(f"  Throughput: {1e9/avg_latency:,.0f} operations/sec")
    
    return avg_latency

def benchmark_quantity_operations():
    """Benchmark Quantity operations"""
    print("\n📏 Benchmarking Nautilus Quantity Operations...")
    
    iterations = 1000000
    quantities_raw = np.random.uniform(0.001, 100.0, iterations)
    
    start_time = time.perf_counter_ns()
    
    for qty_raw in quantities_raw:
        # Hot path - Quantity creation and operations
        qty = Quantity.from_str(f"{qty_raw:.8f}")
        qty_value = float(qty)
        
    end_time = time.perf_counter_ns()
    total_time = end_time - start_time
    avg_latency = total_time / iterations
    
    print(f"  Iterations: {iterations:,}")
    print(f"  Average latency: {avg_latency:.1f}ns per operation")
    print(f"  Throughput: {1e9/avg_latency:,.0f} operations/sec")
    
    return avg_latency

def benchmark_math_operations():
    """Benchmark mathematical operations"""
    print("\n🧮 Benchmarking Math Operations...")
    
    iterations = 10000000
    
    # Prepare test data
    prices = np.random.uniform(50000, 51000, iterations).astype(np.float64)
    quantities = np.random.uniform(0.1, 10.0, iterations).astype(np.float64)
    
    start_time = time.perf_counter_ns()
    
    for i in range(iterations):
        # Hot path - Basic math operations
        notional = prices[i] * quantities[i]
        side_multiplier = 1.0 if i % 2 == 0 else -1.0
        position_delta = notional * side_multiplier
        
    end_time = time.perf_counter_ns()
    total_time = end_time - start_time
    avg_latency = total_time / iterations
    
    print(f"  Iterations: {iterations:,}")
    print(f"  Average latency: {avg_latency:.2f}ns per operation")
    print(f"  Throughput: {1e9/avg_latency:,.0f} operations/sec")
    
    return avg_latency

def benchmark_indicator_simulation():
    """Simulate technical indicator calculations"""
    print("\n📊 Benchmarking Indicator Calculations...")
    
    iterations = 10000000
    prices = np.random.uniform(50000, 51000, iterations).astype(np.float64)
    
    # EMA calculation
    alpha = 0.1
    ema_value = prices[0]
    
    start_time = time.perf_counter_ns()
    
    for price in prices:
        # Hot path - EMA update
        ema_value = alpha * price + (1 - alpha) * ema_value
        
    end_time = time.perf_counter_ns()
    total_time = end_time - start_time
    avg_latency = total_time / iterations
    
    print(f"  Iterations: {iterations:,}")
    print(f"  Average latency: {avg_latency:.2f}ns per update")
    print(f"  Throughput: {1e9/avg_latency:,.0f} updates/sec")
    
    return avg_latency

def main():
    """Run all benchmarks and analysis"""
    print("🔍 NAUTILUS TRADER HOT PATH ANALYSIS")
    print("="*50)
    
    # Run benchmarks
    price_latency = benchmark_price_operations()
    quantity_latency = benchmark_quantity_operations()
    math_latency = benchmark_math_operations()
    indicator_latency = benchmark_indicator_simulation()
    
    # Calculate assembly optimization potential
    print(f"\n🎯 ASSEMBLY OPTIMIZATION POTENTIAL:")
    print("-"*40)
    
    optimizations = {
        'Price operations': {
            'current': price_latency,
            'assembly_target': 5.0,
            'improvement': price_latency / 5.0
        },
        'Quantity operations': {
            'current': quantity_latency,
            'assembly_target': 4.0,
            'improvement': quantity_latency / 4.0
        },
        'Math operations': {
            'current': math_latency,
            'assembly_target': 0.5,
            'improvement': math_latency / 0.5
        },
        'Indicator calculations': {
            'current': indicator_latency,
            'assembly_target': 0.3,
            'improvement': indicator_latency / 0.3
        }
    }
    
    for name, data in optimizations.items():
        print(f"\n{name}:")
        print(f"  Current: {data['current']:.2f}ns")
        print(f"  Assembly target: {data['assembly_target']:.2f}ns")
        print(f"  Improvement: {data['improvement']:.1f}x faster")
    
    # Calculate practical impact
    print(f"\n💰 PRACTICAL TRADING IMPACT:")
    print("-"*30)
    
    # Assume 1M operations per day across all categories
    daily_operations = 1_000_000
    
    total_current_time_us = sum(
        data['current'] * daily_operations / 1000 
        for data in optimizations.values()
    )
    
    total_assembly_time_us = sum(
        data['assembly_target'] * daily_operations / 1000 
        for data in optimizations.values()
    )
    
    daily_savings_us = total_current_time_us - total_assembly_time_us
    
    print(f"Daily time savings: {daily_savings_us:.0f}μs")
    print(f"Additional trading opportunities: ~{daily_savings_us/50:.0f}")
    print(f"Potential daily revenue increase: ${daily_savings_us/50 * 0.5:.0f}")
    
    # Show what we should optimize first
    print(f"\n🏆 OPTIMIZATION PRIORITY:")
    print("-"*25)
    
    priority_list = sorted(
        optimizations.items(),
        key=lambda x: (x[1]['current'] - x[1]['assembly_target']) * daily_operations,
        reverse=True
    )
    
    for i, (name, data) in enumerate(priority_list, 1):
        savings = (data['current'] - data['assembly_target']) * daily_operations / 1000
        print(f"{i}. {name}: {savings:.0f}μs daily savings")

if __name__ == "__main__":
    main()
