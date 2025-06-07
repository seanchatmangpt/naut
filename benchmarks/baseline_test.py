#!/usr/bin/env python3
"""
Simplified performance test for basic loop operations on M3 Max
This tests the fundamental performance characteristics without assembly
"""
import time
import numpy as np
import statistics


def test_basic_loop_performance():
    """Test basic loop performance to establish baseline"""
    print("🔥 M3 Max Basic Loop Performance Test")
    print("=" * 50)
    
    # Test 1: Simple counter loop
    iterations = 1_000_000_000
    start_time = time.perf_counter_ns()
    
    total = 0
    for i in range(iterations):
        total += i
    
    end_time = time.perf_counter_ns()
    loop_time_ns = end_time - start_time
    per_iteration_ns = loop_time_ns / iterations
    
    print(f"\n📊 Simple Counter Loop:")
    print(f"  Iterations: {iterations:,}")
    print(f"  Total time: {loop_time_ns/1e9:.3f}s")
    print(f"  Per iteration: {per_iteration_ns:.3f}ns")
    print(f"  Throughput: {1e9/per_iteration_ns:,.0f} ops/sec")
    print(f"  Result: {total}")
    
    return per_iteration_ns


def test_numpy_vectorized_operations():
    """Test NumPy vectorized operations"""
    print(f"\n🧮 NumPy Vectorized Operations:")
    
    # Test array operations
    size = 10_000_000
    arr1 = np.random.uniform(0, 100, size).astype(np.float32)
    arr2 = np.random.uniform(0, 100, size).astype(np.float32)
    
    # Addition
    start_time = time.perf_counter_ns()
    result = arr1 + arr2
    end_time = time.perf_counter_ns()
    add_time = end_time - start_time
    
    # Multiplication
    start_time = time.perf_counter_ns()
    result = arr1 * arr2
    end_time = time.perf_counter_ns()
    mul_time = end_time - start_time
    
    # EMA-like calculation
    start_time = time.perf_counter_ns()
    alpha = 0.1
    ema = np.zeros_like(arr1)
    ema[0] = arr1[0]
    for i in range(1, len(arr1)):
        ema[i] = alpha * arr1[i] + (1 - alpha) * ema[i-1]
    end_time = time.perf_counter_ns()
    ema_time = end_time - start_time
    
    print(f"  Array size: {size:,} elements")
    print(f"  Addition: {add_time/1e6:.2f}ms ({size*1e9/add_time:,.0f} ops/sec)")
    print(f"  Multiplication: {mul_time/1e6:.2f}ms ({size*1e9/mul_time:,.0f} ops/sec)")
    print(f"  EMA calculation: {ema_time/1e6:.2f}ms ({size*1e9/ema_time:,.0f} ops/sec)")


def test_memory_bandwidth():
    """Test memory bandwidth characteristics"""
    print(f"\n💾 Memory Bandwidth Test:")
    
    # Test different array sizes to see cache effects
    sizes = [1000, 10000, 100000, 1000000, 10000000]
    
    for size in sizes:
        arr = np.random.uniform(0, 100, size).astype(np.float32)
        
        # Sequential read test
        iterations = max(1, 10000000 // size)
        start_time = time.perf_counter_ns()
        
        for _ in range(iterations):
            total = np.sum(arr)
        
        end_time = time.perf_counter_ns()
        time_per_op = (end_time - start_time) / iterations
        bandwidth_gb_s = (size * 4 * 1e9) / (time_per_op * 1e9)  # 4 bytes per float32
        
        print(f"  Size: {size:>8,} elements | Time: {time_per_op/1e3:>6.1f}μs | Bandwidth: {bandwidth_gb_s:>5.1f} GB/s")


def test_order_book_simulation():
    """Simulate order book operations without assembly"""
    print(f"\n📊 Order Book Simulation (Python):")
    
    # Simulate a simple order book with price levels
    class SimpleOrderBook:
        def __init__(self):
            self.bids = {}  # price -> quantity
            self.asks = {}  # price -> quantity
            
        def update_level(self, side, price, quantity):
            book = self.bids if side == 0 else self.asks
            if quantity > 0:
                book[price] = quantity
            elif price in book:
                del book[price]
    
    book = SimpleOrderBook()
    
    # Generate random updates
    num_updates = 1_000_000
    updates = []
    for i in range(num_updates):
        updates.append((
            i % 2,  # side
            100.0 + (i % 1000) / 100.0,  # price
            1000.0 + (i % 5000)  # quantity
        ))
    
    # Warm up
    for _ in range(1000):
        book.update_level(0, 100.50, 1000.0)
    
    # Benchmark
    start_time = time.perf_counter_ns()
    
    for side, price, quantity in updates:
        book.update_level(side, price, quantity)
    
    end_time = time.perf_counter_ns()
    total_time = end_time - start_time
    per_update_ns = total_time / num_updates
    
    print(f"  Updates: {num_updates:,}")
    print(f"  Total time: {total_time/1e6:.2f}ms")
    print(f"  Per update: {per_update_ns:.1f}ns")
    print(f"  Throughput: {1e9/per_update_ns:,.0f} updates/sec")
    print(f"  Bid levels: {len(book.bids)}")
    print(f"  Ask levels: {len(book.asks)}")


def test_latency_distribution():
    """Test latency distribution for small operations"""
    print(f"\n📈 Latency Distribution Analysis:")
    
    # Test simple arithmetic operations
    latencies = []
    iterations = 10000
    
    for _ in range(iterations):
        start = time.perf_counter_ns()
        result = 123.456 * 789.012 + 456.789
        end = time.perf_counter_ns()
        latencies.append(end - start)
    
    latencies.sort()
    
    print(f"  Operation: floating point arithmetic")
    print(f"  Samples: {iterations:,}")
    print(f"  P50:  {latencies[iterations//2]:.1f}ns")
    print(f"  P95:  {latencies[int(iterations*0.95)]:.1f}ns")
    print(f"  P99:  {latencies[int(iterations*0.99)]:.1f}ns")
    print(f"  P99.9: {latencies[int(iterations*0.999)]:.1f}ns")
    print(f"  Min:  {min(latencies):.1f}ns")
    print(f"  Max:  {max(latencies):.1f}ns")


def main():
    """Run all performance tests"""
    print("🚀 M3 Max Performance Baseline Tests")
    print("=====================================")
    
    # Get system info
    import platform
    import sys
    
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")
    print(f"Python: {sys.version}")
    print(f"NumPy: {np.__version__}")
    
    # Run tests
    basic_perf = test_basic_loop_performance()
    test_numpy_vectorized_operations()
    test_memory_bandwidth()
    test_order_book_simulation()
    test_latency_distribution()
    
    print(f"\n🎯 Performance Summary:")
    print(f"  Basic loop: {basic_perf:.3f}ns per iteration")
    print(f"  Expected assembly improvement: 5-15x faster")
    print(f"  Target assembly performance: {basic_perf/10:.3f}ns per iteration")
    
    print(f"\n✅ Baseline testing complete!")
    print(f"🔧 Assembly engine would provide significant speedups")


if __name__ == "__main__":
    main()
