#ifndef ASSEMBLY_ENGINE_H
#define ASSEMBLY_ENGINE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Order book functions
int32_t nautilus_update_l2_level(
    void* order_book,
    int32_t side,
    uint64_t price_raw,
    uint64_t quantity_raw,
    int32_t action
);

void nautilus_get_best_bid_ask(
    void* order_book,
    uint64_t* best_bid,
    uint64_t* best_ask
);

// Market data processing
void nautilus_process_tick_batch(
    void* input_ticks,
    void* output_events,
    uint64_t count,
    uint64_t instrument_id
);

void nautilus_calculate_ohlc_vectorized(
    float* ticks,
    float* ohlc_output,
    uint64_t count,
    uint64_t window_size
);

// Signal calculations
void nautilus_calculate_ema_vectorized(
    float* prices,
    float* output,
    uint64_t count,
    float alpha
);

void nautilus_calculate_rsi_vectorized(
    float* prices,
    float* rsi_output,
    uint64_t count,
    uint64_t period
);

// Risk management
uint64_t nautilus_validate_order_batch(
    void* orders,
    void* positions,
    void* limits,
    uint64_t count
);

uint64_t nautilus_calculate_portfolio_var(
    float* positions,
    float* correlations,
    float* volatilities,
    uint64_t count
);

#ifdef __cplusplus
}
#endif

#endif // ASSEMBLY_ENGINE_H
