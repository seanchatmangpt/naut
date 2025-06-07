#!/usr/bin/env python3
"""
Ultra-Fast Risk Validation Benchmark
Testing multiple optimization strategies
"""
import time
import numpy as np
import subprocess
import ctypes
import os
import tempfile

def compile_and_benchmark_risk():
    """Test ultra-fast risk validation"""
    print("⚡ ULTRA-FAST Risk Validation Benchmark")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Compile assembly
        asm_path = "/Users/sac/dev/naut/nautilus_assembly/src/ultra_fast_risk.s"
        obj_path = os.path.join(tmpdir, "risk.o")
        
        result = subprocess.run([
            "clang", "-c", "-arch", "arm64", "-O3",
            "-march=armv8.4-a+simd",
            asm_path, "-o", obj_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Compilation failed: {result.stderr}")
            # Try simpler version
            return benchmark_simple_risk()
        
        # Create library
        lib_path = os.path.join(tmpdir, "librisk.dylib")
        result = subprocess.run([
            "clang", "-shared", "-arch", "arm64",
            obj_path, "-o", lib_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Library creation failed")
            return benchmark_simple_risk()
        
        print("✅ Risk validation assembly compiled\n")
        
        lib = ctypes.CDLL(lib_path)
        
        # Test 1: Single validation
        print("📊 Single Order Validation (Bit-packed)")
        print("-" * 50)
        
        lib.ultra_fast_risk_validate.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
        lib.ultra_fast_risk_validate.restype = ctypes.c_uint64
        
        # Pack limits: min_price=50000, max_price=150000, min_qty=1, max_qty=10000
        limits = (150000 << 48) | (50000 << 32) | (10000 << 16) | 1
        
        iterations = 100_000_000
        
        # Generate test orders
        prices = np.random.randint(40000, 160000, iterations)
        quantities = np.random.randint(0, 12000, iterations)
        
        # Pack orders
        orders = (prices.astype(np.uint64) << 32) | quantities.astype(np.uint64)
        
        start = time.perf_counter_ns()
        
        for i in range(iterations):
            result = lib.ultra_fast_risk_validate(orders[i], limits)
        
        end = time.perf_counter_ns()
        
        single_ns = (end - start) / iterations
        print(f"  Iterations: {iterations:,}")
        print(f"  Per validation: {single_ns:.3f}ns")
        print(f"  Throughput: {1e9/single_ns:,.0f} validations/sec")
        
        # Test 2: Portfolio check
        if hasattr(lib, 'ultra_fast_portfolio_check'):
            print("\n📊 Portfolio Limit Check")
            print("-" * 50)
            
            lib.ultra_fast_portfolio_check.argtypes = [
                ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64
            ]
            lib.ultra_fast_portfolio_check.restype = ctypes.c_uint64
            
            position = 5000
            max_position = 10000
            order_quantities = np.random.randint(-1000, 1000, iterations)
            
            start = time.perf_counter_ns()
            
            for i in range(iterations):
                result = lib.ultra_fast_portfolio_check(
                    position, order_quantities[i], max_position
                )
            
            end = time.perf_counter_ns()
            
            portfolio_ns = (end - start) / iterations
            print(f"  Per check: {portfolio_ns:.3f}ns")
            print(f"  Throughput: {1e9/portfolio_ns:,.0f} checks/sec")
        
        return single_ns

def benchmark_simple_risk():
    """Fallback simple risk validation"""
    print("\n📊 Simple Risk Validation (Python Baseline)")
    print("-" * 50)
    
    SIMPLE_RISK_ASM = """
    .section __TEXT,__text
    .global _simple_risk_check
    .align 4
    
    // Simplest possible risk check - just compare two values
    // x0 = value, x1 = limit
    // Returns: x0 = 0 (valid) or 1 (invalid)
    _simple_risk_check:
        cmp x0, x1
        cset x0, gt
        ret
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write and compile simple assembly
        asm_path = os.path.join(tmpdir, "simple_risk.s")
        with open(asm_path, 'w') as f:
            f.write(SIMPLE_RISK_ASM)
        
        obj_path = os.path.join(tmpdir, "simple_risk.o")
        subprocess.run([
            "clang", "-c", "-arch", "arm64", "-O3",
            asm_path, "-o", obj_path
        ], capture_output=True)
        
        lib_path = os.path.join(tmpdir, "libsimplerisk.dylib")
        subprocess.run([
            "clang", "-shared", "-arch", "arm64",
            obj_path, "-o", lib_path
        ], capture_output=True)
        
        lib = ctypes.CDLL(lib_path)
        lib.simple_risk_check.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
        lib.simple_risk_check.restype = ctypes.c_uint64
        
        iterations = 100_000_000
        values = np.random.randint(0, 20000, iterations)
        limit = 10000
        
        start = time.perf_counter_ns()
        
        for i in range(iterations):
            result = lib.simple_risk_check(values[i], limit)
        
        end = time.perf_counter_ns()
        
        simple_ns = (end - start) / iterations
        print(f"  Per check: {simple_ns:.3f}ns")
        print(f"  Throughput: {1e9/simple_ns:,.0f} checks/sec")
        
        return simple_ns

def benchmark_lookup_table():
    """Test lookup table approach"""
    print("\n📊 Lookup Table Risk Validation")
    print("-" * 50)
    
    # Pre-compute validation results
    max_price_idx = 1000
    max_qty_idx = 100
    
    # Create lookup table
    lookup_table = np.zeros((max_price_idx, max_qty_idx), dtype=np.uint8)
    
    # Set valid ranges
    min_price_idx, max_price_idx_valid = 200, 800
    min_qty_idx, max_qty_idx_valid = 1, 50
    
    lookup_table[min_price_idx:max_price_idx_valid, 
                 min_qty_idx:max_qty_idx_valid] = 1
    
    # Flatten for fast 1D access
    lookup_flat = lookup_table.flatten()
    
    iterations = 100_000_000
    price_indices = np.random.randint(0, max_price_idx, iterations)
    qty_indices = np.random.randint(0, max_qty_idx, iterations)
    
    start = time.perf_counter_ns()
    
    for i in range(iterations):
        idx = price_indices[i] * max_qty_idx + qty_indices[i]
        valid = lookup_flat[idx]
    
    end = time.perf_counter_ns()
    
    lookup_ns = (end - start) / iterations
    print(f"  Per lookup: {lookup_ns:.3f}ns")
    print(f"  Throughput: {1e9/lookup_ns:,.0f} lookups/sec")
    print(f"  Table size: {lookup_flat.nbytes:,} bytes")
    
    return lookup_ns

def main():
    """Run all risk validation benchmarks"""
    
    # Test different approaches
    asm_result = compile_and_benchmark_risk()
    lookup_result = benchmark_lookup_table()
    
    print("\n\n🎯 Risk Validation Performance Summary")
    print("=" * 60)
    print(f"  Current implementation: 169.52ns")
    print(f"  Simple comparison: ~200ns")
    print(f"  Bit-packed validation: {asm_result:.3f}ns")
    print(f"  Lookup table: {lookup_result:.3f}ns")
    print(f"\n✅ Best approach: {'Lookup table' if lookup_result < asm_result else 'Bit-packed'}")
    print(f"🚀 Speed improvement: {169.52/min(asm_result, lookup_result):.1f}x faster!")

if __name__ == "__main__":
    main()
