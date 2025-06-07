#ifndef OPTIMIZED_CORE_H
#define OPTIMIZED_CORE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Assembly functions
uint64_t fast_order_book_update(uint64_t price, uint64_t quantity, uint64_t side);
uint64_t fast_array_sum(float* array, uint64_t count);
void fast_memory_copy(void* dst, void* src, uint64_t bytes);

// EMA update in assembly
float fast_ema_update(float new_price, float prev_ema, float alpha);

#ifdef __cplusplus
}
#endif

#endif
