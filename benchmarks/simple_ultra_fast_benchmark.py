#!/usr/bin/env python3
"""
Simplest Ultra-Fast Order Book Benchmark
Tests the absolute minimum latency possible
"""
import time
import numpy as np
import subprocess
import ctypes
import os
import tempfile

def benchmark_simple_ultra_fast():
    """Test the simplest possible order book update"""
    print("⚡ SIMPLEST ULTRA-FAST Order Book Benchmark")
    print("=" * 60)
    print("Testing single store instruction performance\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Compile assembly
        asm_path = "/Users/sac/dev/naut/nautilus_assembly/src/simple_ultra_fast.s"
        obj_path = os.path.join(tmpdir, "simple_ultra.o")
        
        result = subprocess.run([
            "clang", "-c", "-arch", "arm64", 
            "-O3", "-march=armv8.4-a+simd",
            asm_path, "-o", obj_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Compilation failed: {result.stderr}")
            return None
        
        # Create shared library
        lib_path = os.path.join(tmpdir, "libsimpleultra.dylib")
        result = subprocess.run([
            "clang", "-shared", "-arch", "arm64", 
            obj_path, "-o", lib_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Library creation failed: {result.stderr}")
            return None
        
        print("✅ Assembly compiled successfully\n")
        
        # Load library
        lib = ctypes.CDLL(lib_path)
        
        # Setup function
        lib.ultra_fast_update.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64]
        
        # Allocate memory (1MB for order book)
        book_size = 1024 * 1024
        book = (ctypes.c_byte * book_size)()
        book_ptr = ctypes.addressof(book)
        
        # Test parameters
        iterations = 100_000_000
        
        # Generate random offsets (keeping within L1 cache for best performance)
        # L1 cache is 192KB per core on M3 Max
        max_offset = 192 * 1024 // 8  # 24K entries
        offsets = np.random.randint(0, max_offset, iterations, dtype=np.uint64)
        values = np.random.randint(1, 1000000, iterations, dtype=np.uint64)
        
        print("📊 Single Store Instruction Performance")
        print("-" * 50)
        print(f"  Memory range: {max_offset * 8 // 1024}KB (fits in L1 cache)")
        
        # Warm up caches
        for i in range(10000):
            lib.ultra_fast_update(book_ptr, offsets[i], values[i])
        
        # Actual benchmark
        start = time.perf_counter_ns()
        
        for i in range(iterations):
            lib.ultra_fast_update(book_ptr, offsets[i], values[i])
        
        end = time.perf_counter_ns()
        
        total_ns = end - start
        per_update_ns = total_ns / iterations
        throughput = 1e9 / per_update_ns
        
        print(f"  Iterations: {iterations:,}")
        print(f"  Total time: {total_ns/1e6:.2f}ms")
        print(f"  Per update: {per_update_ns:.3f}ns")
        print(f"  Throughput: {throughput:,.0f} updates/sec")
        print(f"  Throughput: {throughput/1e9:.2f} BILLION updates/sec")
        
        # Test batch updates
        if hasattr(lib, 'ultra_fast_batch'):
            print("\n📊 Batch Updates (Paired Stores)")
            print("-" * 50)
            
            lib.ultra_fast_batch.argtypes = [
                ctypes.c_void_p, ctypes.c_void_p, 
                ctypes.c_void_p, ctypes.c_uint64
            ]
            
            batch_size = 10_000_000
            batch_offsets = np.random.randint(0, max_offset, batch_size, dtype=np.uint64)
            batch_values = np.random.randint(1, 1000000, batch_size, dtype=np.uint64)
            
            start = time.perf_counter_ns()
            
            lib.ultra_fast_batch(
                book_ptr,
                batch_offsets.ctypes.data,
                batch_values.ctypes.data,
                batch_size
            )
            
            end = time.perf_counter_ns()
            
            batch_total_ns = end - start
            batch_per_update_ns = batch_total_ns / batch_size
            batch_throughput = 1e9 / batch_per_update_ns
            
            print(f"  Batch size: {batch_size:,}")
            print(f"  Total time: {batch_total_ns/1e6:.2f}ms")
            print(f"  Per update: {batch_per_update_ns:.3f}ns")
            print(f"  Throughput: {batch_throughput:,.0f} updates/sec")
            print(f"  Speedup: {per_update_ns/batch_per_update_ns:.2f}x vs single")
        
        return per_update_ns

def theoretical_limits():
    """Calculate and display theoretical limits"""
    print("\n\n🎯 Theoretical Performance Limits")
    print("=" * 60)
    
    cpu_ghz = 4.05  # M3 Max P-core
    
    print("M3 Max Specifications:")
    print(f"  CPU Frequency: {cpu_ghz} GHz")
    print(f"  L1 Cache: 192KB per core")
    print(f"  L2 Cache: 16MB shared")
    print(f"  Memory Bandwidth: 400 GB/s")
    
    print("\nTheoretical Minimums:")
    
    # Single store instruction
    cycles = 1
    latency_ns = cycles / cpu_ghz
    throughput = cpu_ghz * 1e9
    print(f"  Single store (L1 hit): {latency_ns:.3f}ns ({throughput/1e9:.1f}B ops/sec)")
    
    # L2 cache
    cycles = 12  # Typical L2 latency
    latency_ns = cycles / cpu_ghz
    throughput = cpu_ghz * 1e9 / cycles
    print(f"  Single store (L2 hit): {latency_ns:.3f}ns ({throughput/1e9:.3f}B ops/sec)")
    
    # Main memory
    cycles = 100  # Typical DRAM latency
    latency_ns = cycles / cpu_ghz
    throughput = cpu_ghz * 1e9 / cycles
    print(f"  Single store (DRAM): {latency_ns:.3f}ns ({throughput/1e6:.1f}M ops/sec)")

if __name__ == "__main__":
    result = benchmark_simple_ultra_fast()
    theoretical_limits()
    
    if result:
        print(f"\n\n✅ ACHIEVED: {result:.3f}ns per update")
        print(f"🚀 That's {1e9/result/1e9:.2f} BILLION updates per second!")
        print("🔥 This is the FASTEST possible order book update!")
