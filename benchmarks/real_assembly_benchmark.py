#!/usr/bin/env python3
"""
Real Assembly Performance Benchmark
Tests actual ARM64 assembly implementations
"""
import time
import numpy as np
import ctypes
import os
import subprocess
import tempfile

class AssemblyBenchmark:
    def __init__(self):
        self.lib = None
        self.compile_assembly()
    
    def compile_assembly(self):
        """Compile the assembly files into a shared library"""
        print("🔨 Compiling ARM64 Assembly...")
        
        assembly_files = [
            "nautilus_assembly/src/order_book.s",
            "nautilus_assembly/src/signals.s",
            "nautilus_assembly/src/market_data.s",
            "nautilus_assembly/src/risk_engine.s"
        ]
        
        # Create temporary directory for build
        with tempfile.TemporaryDirectory() as tmpdir:
            # Compile each assembly file
            obj_files = []
            for asm_file in assembly_files:
                if os.path.exists(asm_file):
                    obj_file = os.path.join(tmpdir, os.path.basename(asm_file).replace('.s', '.o'))
                    cmd = ['clang', '-c', asm_file, '-o', obj_file, '-arch', 'arm64']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        obj_files.append(obj_file)
                        print(f"  ✓ Compiled {os.path.basename(asm_file)}")
                    else:
                        print(f"  ✗ Failed to compile {asm_file}: {result.stderr}")
            
            if obj_files:
                # Link into shared library
                lib_path = os.path.join(os.getcwd(), 'nautilus_assembly.dylib')
                cmd = ['clang', '-shared', '-arch', 'arm64'] + obj_files + ['-o', lib_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Assembly library created: {lib_path}")
                    self.lib = ctypes.CDLL(lib_path)
                    self.setup_functions()
                else:
                    print(f"❌ Failed to create library: {result.stderr}")
    
    def setup_functions(self):
        """Setup function signatures for assembly functions"""
        if not self.lib:
            return
        
        # Order book functions
        if hasattr(self.lib, '_nautilus_update_l2_level'):
            self.lib._nautilus_update_l2_level.argtypes = [
                ctypes.c_void_p,  # order_book*
                ctypes.c_int,     # side
                ctypes.c_double,  # price
                ctypes.c_double,  # quantity
                ctypes.c_int      # action
            ]
            self.lib._nautilus_update_l2_level.restype = ctypes.c_int
        
        # Signal functions
        if hasattr(self.lib, '_nautilus_calculate_ema_vectorized'):
            self.lib._nautilus_calculate_ema_vectorized.argtypes = [
                ctypes.c_void_p,  # prices*
                ctypes.c_void_p,  # output*
                ctypes.c_size_t,  # count
                ctypes.c_float    # alpha
            ]
    
    def benchmark_order_book_assembly(self, iterations=1000000):
        """Benchmark real assembly order book updates"""
        if not self.lib or not hasattr(self.lib, '_nautilus_update_l2_level'):
            print("⚠️  Order book assembly not available")
            return
        
        print("\n📊 Real Assembly Order Book Benchmark")
        print("=" * 50)
        
        # Create mock order book structure
        order_book_size = 1024  # Allocate space for order book
        order_book = (ctypes.c_byte * order_book_size)()
        
        # Warm up
        for _ in range(1000):
            self.lib._nautilus_update_l2_level(
                ctypes.addressof(order_book),
                0,  # bid side
                99.50,
                100.0,
                0   # update action
            )
        
        # Benchmark
        start = time.perf_counter_ns()
        
        for i in range(iterations):
            price = 99.0 + (i % 100) * 0.01
            self.lib._nautilus_update_l2_level(
                ctypes.addressof(order_book),
                i % 2,  # alternate bid/ask
                price,
                100.0 + i % 10,
                0       # update action
            )
        
        end = time.perf_counter_ns()
        
        total_ns = end - start
        per_update_ns = total_ns / iterations
        throughput = 1e9 / per_update_ns
        
        print(f"  Iterations: {iterations:,}")
        print(f"  Total time: {total_ns/1e6:.2f}ms")
        print(f"  Per update: {per_update_ns:.1f}ns")
        print(f"  Throughput: {throughput:,.0f} updates/sec")
        
        return per_update_ns
    
    def benchmark_signal_assembly(self, size=100000):
        """Benchmark real assembly signal calculations"""
        if not self.lib or not hasattr(self.lib, '_nautilus_calculate_ema_vectorized'):
            print("⚠️  Signal assembly not available")
            return
        
        print("\n📈 Real Assembly Signal Calculation Benchmark")
        print("=" * 50)
        
        # Create test data
        prices = np.random.uniform(95.0, 105.0, size).astype(np.float32)
        output = np.zeros(size, dtype=np.float32)
        
        # Benchmark EMA calculation
        alpha = 0.1
        
        # Warm up
        self.lib._nautilus_calculate_ema_vectorized(
            prices.ctypes.data_as(ctypes.c_void_p),
            output.ctypes.data_as(ctypes.c_void_p),
            100,
            ctypes.c_float(alpha)
        )
        
        # Actual benchmark
        start = time.perf_counter_ns()
        
        self.lib._nautilus_calculate_ema_vectorized(
            prices.ctypes.data_as(ctypes.c_void_p),
            output.ctypes.data_as(ctypes.c_void_p),
            size,
            ctypes.c_float(alpha)
        )
        
        end = time.perf_counter_ns()
        
        total_ns = end - start
        total_ms = total_ns / 1e6
        per_point_ns = total_ns / size
        throughput = 1e9 / per_point_ns
        
        print(f"  Data points: {size:,}")
        print(f"  Total time: {total_ms:.2f}ms")
        print(f"  Per point: {per_point_ns:.1f}ns")
        print(f"  Throughput: {throughput:,.0f} points/sec")
        
        return per_point_ns

def main():
    print("🚀 NautilusTrader Real ARM64 Assembly Benchmark")
    print("=" * 60)
    
    # Check if we're on ARM64
    import platform
    if platform.machine() != 'arm64':
        print("❌ This benchmark requires ARM64 architecture")
        return
    
    benchmark = AssemblyBenchmark()
    
    if benchmark.lib:
        # Run benchmarks
        order_book_latency = benchmark.benchmark_order_book_assembly()
        signal_latency = benchmark.benchmark_signal_assembly()
        
        print("\n🎯 Summary:")
        print(f"  Order Book: {order_book_latency:.1f}ns per update")
        print(f"  Signal Calc: {signal_latency:.1f}ns per point")
    else:
        print("\n❌ Failed to compile assembly. Running Python fallback benchmark...")
        
        # Fallback to Python benchmark
        print("\n📊 Python Baseline (for comparison)")
        
        # Simple order book simulation
        order_book = {'bids': [], 'asks': []}
        start = time.perf_counter_ns()
        
        for i in range(1000000):
            price = 99.0 + (i % 100) * 0.01
            side = 'bids' if i % 2 == 0 else 'asks'
            order_book[side].append((price, 100.0))
            if len(order_book[side]) > 100:
                order_book[side].pop(0)
        
        end = time.perf_counter_ns()
        python_ob_latency = (end - start) / 1000000
        
        print(f"  Order Book (Python): {python_ob_latency:.1f}ns per update")
        
        # EMA calculation
        prices = np.random.uniform(95.0, 105.0, 100000).astype(np.float32)
        alpha = 0.1
        
        start = time.perf_counter_ns()
        
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        end = time.perf_counter_ns()
        python_ema_latency = (end - start) / 100000
        
        print(f"  EMA Calc (Python): {python_ema_latency:.1f}ns per point")

if __name__ == "__main__":
    main()
