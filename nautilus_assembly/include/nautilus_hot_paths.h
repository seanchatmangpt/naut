#ifndef NAUTILUS_HOT_PATHS_H
#define NAUTILUS_HOT_PATHS_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Assembly-optimized hot path functions for Nautilus Trader

// Price operations
uint64_t fast_price_operations(uint64_t price_int, uint64_t operation_type);

// Quantity operations  
uint64_t fast_quantity_operations(uint64_t quantity_int, uint64_t operation_type);

// Math operations (SIMD optimized)
uint64_t fast_math_operations(float* prices, float* quantities, uint64_t count);

// EMA calculation (SIMD optimized)
float fast_ema_calculation(float* prices, uint64_t count, float alpha);

// Batch operations
uint64_t fast_batch_operations(uint64_t operation_type, void* data_ptr, uint64_t count);

#ifdef __cplusplus
}
#endif

#endif // NAUTILUS_HOT_PATHS_H
