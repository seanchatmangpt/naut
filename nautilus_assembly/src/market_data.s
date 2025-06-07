// nautilus_assembly/src/market_data.s
// SIMD-accelerated market data processing for M3 Max
.section __TEXT,__text
.global _nautilus_process_tick_batch
.align 4

// Args: x0=input_ticks*, x1=output_events*, x2=count, x3=instrument_id
// Processes Nautilus tick data in SIMD batches
_nautilus_process_tick_batch:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    
    // Load instrument ID into vector register for broadcasting
    dup v16.2d, x3
    
    // Process 2 ticks at a time (each tick is 32 bytes)
    mov x4, #2
    udiv x5, x2, x4              // iterations = count / 2
    
tick_vector_loop:
    cbz x5, remaining_ticks
    
    // Load 2 ticks worth of data (64 bytes total)
    ld1 {v0.2d, v1.2d}, [x0], #32    // First tick: price, qty
    ld1 {v2.2d, v3.2d}, [x0], #32    // Second tick: price, qty
    
    // Pack prices and quantities
    zip1 v4.2d, v0.2d, v2.2d         // prices: [price1, price2]
    zip1 v5.2d, v1.2d, v3.2d         // quantities: [qty1, qty2]
    
    // Apply Nautilus precision scaling (multiply by 1e8 for precision)
    fmov v6.2d, #100000000.0
    fmul v4.2d, v4.2d, v6.2d
    fmul v5.2d, v5.2d, v6.2d
    
    // Convert to integers for Nautilus internal format
    fcvtzs v7.2d, v4.2d
    fcvtzs v8.2d, v5.2d
    
    // Store processed tick events
    st1 {v16.2d}, [x1], #16          // instrument_ids
    st1 {v7.2d}, [x1], #16           // scaled_prices  
    st1 {v8.2d}, [x1], #16           // scaled_quantities
    
    sub x5, x5, #1
    b tick_vector_loop
    
remaining_ticks:
    // Handle remaining single tick
    and x4, x2, #1
    cbz x4, tick_processing_done
    
    ldr d0, [x0], #8             // price
    ldr d1, [x0], #8             // quantity
    
    fmov d2, #100000000.0
    fmul d0, d0, d2
    fmul d1, d1, d2
    fcvtzs d0, d0
    fcvtzs d1, d1
    
    str x3, [x1], #8             // instrument_id
    str d0, [x1], #8             // scaled_price
    str d1, [x1], #8             // scaled_quantity
    
tick_processing_done:
    ldp x29, x30, [sp], #16
    ret

.global _nautilus_calculate_ohlc_vectorized
.align 4

// Args: x0=ticks*, x1=ohlc_output*, x2=count, x3=window_size
// Calculate OHLC bars using SIMD processing
_nautilus_calculate_ohlc_vectorized:
    stp x29, x30, [sp, #-32]!
    stp x19, x20, [sp, #16]
    mov x29, sp
    
    mov x19, x3                  // window_size
    mov x20, #0                  // current_tick_index
    
ohlc_window_loop:
    cmp x20, x2
    b.ge ohlc_complete
    
    // Calculate remaining ticks in current window
    add x4, x20, x19             // end_index = current + window_size
    cmp x4, x2
    csel x4, x2, x4, gt          // min(end_index, total_count)
    sub x5, x4, x20              // ticks_in_window = end_index - current
    
    // Load first tick as initial OHLC values
    lsl x6, x20, #3              // offset = current_tick_index * 8
    ldr d0, [x0, x6]             // open = first_price
    fmov d1, d0                  // high = first_price
    fmov d2, d0                  // low = first_price
    fmov d3, d0                  // close = first_price
    
    add x20, x20, #1             // Move to next tick
    sub x5, x5, #1               // Decrement remaining count
    
    // Process remaining ticks in window using SIMD where possible
    mov x7, #4                   // Process 4 at a time
    udiv x8, x5, x7              // simd_iterations
    
ohlc_simd_loop:
    cbz x8, ohlc_remaining_in_window
    
    // Load 4 prices
    lsl x6, x20, #3
    ld1 {v4.4s}, [x0, x6]
    
    // Update high (find max)
    fmaxv s5, v4.4s              // Find max in vector
    fmax s1, s1, s5              // Update overall high
    
    // Update low (find min)
    fminv s6, v4.4s              // Find min in vector
    fmin s2, s2, s6              // Update overall low
    
    // Close is the last price in this batch
    mov v3.s[0], v4.s[3]
    
    add x20, x20, #4
    sub x8, x8, #1
    b ohlc_simd_loop
    
ohlc_remaining_in_window:
    // Handle remaining ticks (< 4)
    and x6, x5, #3
    
ohlc_scalar_loop:
    cbz x6, ohlc_window_complete
    
    lsl x7, x20, #3
    ldr s7, [x0, x7]             // Load price
    
    fmax s1, s1, s7              // Update high
    fmin s2, s2, s7              // Update low
    fmov s3, s7                  // Update close
    
    add x20, x20, #1
    sub x6, x6, #1
    b ohlc_scalar_loop
    
ohlc_window_complete:
    // Store OHLC values
    st1 {v0.s}[0], [x1], #4      // Store open
    st1 {v1.s}[0], [x1], #4      // Store high
    st1 {v2.s}[0], [x1], #4      // Store low
    st1 {v3.s}[0], [x1], #4      // Store close
    
    b ohlc_window_loop
    
ohlc_complete:
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
