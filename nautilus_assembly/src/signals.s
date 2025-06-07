// nautilus_assembly/src/signals.s
// High-performance signal calculation engine
.section __TEXT,__text
.global _nautilus_calculate_ema_vectorized
.align 4

// Args: x0=prices*, x1=output*, x2=count, x3=alpha (as float in s0)
_nautilus_calculate_ema_vectorized:
    stp x29, x30, [sp, #-32]!
    stp x19, x20, [sp, #16]
    mov x29, sp
    
    // Load alpha into all lanes of vector register
    dup v16.4s, v0.s[0]     // v0.s[0] contains alpha parameter
    
    // Calculate (1 - alpha)
    fmov v17.4s, #1.0
    fsub v17.4s, v17.4s, v16.4s
    
    // Initialize EMA with first price
    ldr s18, [x0]           // Current EMA value
    str s18, [x1]           // Store first value
    
    add x0, x0, #4          // Move to second price
    add x1, x1, #4          // Move to second output
    sub x2, x2, #1          // Decrement count
    
    // Process 4 values at a time
    mov x4, #4
    udiv x5, x2, x4         // iterations = (count-1) / 4
    
ema_vector_loop:
    cbz x5, ema_remaining
    
    // Load 4 prices
    ld1 {v0.4s}, [x0], #16
    
    // Duplicate current EMA to all lanes
    dup v1.4s, v18.s[0]
    
    // EMA calculation: alpha * price + (1-alpha) * prev_ema
    fmul v2.4s, v16.4s, v0.4s       // alpha * price
    fmul v3.4s, v17.4s, v1.4s       // (1-alpha) * prev_ema
    fadd v4.4s, v2.4s, v3.4s        // new EMA values
    
    // Store results
    st1 {v4.4s}, [x1], #16
    
    // Update EMA for next iteration (use last calculated value)
    mov v18.s[0], v4.s[3]
    
    sub x5, x5, #1
    b ema_vector_loop
    
ema_remaining:
    // Handle remaining elements
    and x4, x2, #3
    
ema_scalar_loop:
    cbz x4, ema_done
    
    ldr s0, [x0], #4        // Load price
    
    fmul s1, s16, s0        // alpha * price
    fmul s2, s17, s18       // (1-alpha) * prev_ema
    fadd s18, s1, s2        // new EMA
    
    str s18, [x1], #4       // Store result
    
    sub x4, x4, #1
    b ema_scalar_loop
    
ema_done:
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret

.global _nautilus_calculate_rsi_vectorized
.align 4

// Args: x0=prices*, x1=rsi_output*, x2=count, x3=period
_nautilus_calculate_rsi_vectorized:
    stp x29, x30, [sp, #-64]!
    stp x19, x20, [sp, #48]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #16]
    mov x29, sp
    
    mov x19, x3             // period
    fmov s20, #0.0          // avg_gain
    fmov s21, #0.0          // avg_loss
    
    // Calculate initial gains and losses
    mov x20, #1             // Start from second price
    
initial_period_loop:
    cmp x20, x19
    b.gt initial_calculation_done
    
    // Calculate price change
    sub x21, x20, #1
    lsl x22, x20, #2        // current price offset
    lsl x23, x21, #2        // previous price offset
    
    ldr s0, [x0, x22]       // current price
    ldr s1, [x0, x23]       // previous price
    fsub s2, s0, s1         // change = current - previous
    
    // Separate gains and losses
    fcmp s2, #0.0
    b.lt add_loss
    
add_gain:
    fadd s20, s20, s2       // Add to avg_gain
    b next_initial_iteration
    
add_loss:
    fneg s3, s2             // Convert to positive
    fadd s21, s21, s3       // Add to avg_loss
    
next_initial_iteration:
    add x20, x20, #1
    b initial_period_loop
    
initial_calculation_done:
    // Calculate initial averages
    scvtf s24, x19          // Convert period to float
    fdiv s20, s20, s24      // avg_gain = total_gain / period
    fdiv s21, s21, s24      // avg_loss = total_loss / period
    
    // Calculate RSI for remaining periods
    mov x20, x19            // Start from period+1
    
rsi_calculation_loop:
    cmp x20, x2
    b.ge rsi_complete
    
    // Calculate current change
    sub x21, x20, #1
    lsl x22, x20, #2
    lsl x23, x21, #2
    
    ldr s0, [x0, x22]       // current price
    ldr s1, [x0, x23]       // previous price
    fsub s2, s0, s1         // change
    
    // Update smoothed averages using Wilder's method
    // avg_gain = ((period-1) * avg_gain + current_gain) / period
    // avg_loss = ((period-1) * avg_loss + current_loss) / period
    
    fmov s3, #0.0           // current_gain
    fmov s4, #0.0           // current_loss
    
    fcmp s2, #0.0
    b.lt update_loss
    
update_gain:
    fmov s3, s2             // current_gain = change
    b calculate_smoothed_averages
    
update_loss:
    fneg s4, s2             // current_loss = -change
    
calculate_smoothed_averages:
    // Smoothed average calculation
    sub x21, x19, #1        // period - 1
    scvtf s5, x21           // Convert to float
    scvtf s6, x19           // period as float
    
    fmul s7, s5, s20        // (period-1) * avg_gain
    fadd s7, s7, s3         // + current_gain
    fdiv s20, s7, s6        // / period
    
    fmul s8, s5, s21        // (period-1) * avg_loss
    fadd s8, s8, s4         // + current_loss
    fdiv s21, s8, s6        // / period
    
    // Calculate RSI = 100 - (100 / (1 + RS))
    // where RS = avg_gain / avg_loss
    fcmp s21, #0.0
    b.eq rsi_no_loss
    
    fdiv s9, s20, s21       // RS = avg_gain / avg_loss
    fmov s10, #1.0
    fadd s11, s10, s9       // 1 + RS
    fmov s12, #100.0
    fdiv s13, s12, s11      // 100 / (1 + RS)
    fsub s14, s12, s13      // 100 - (100 / (1 + RS))
    b store_rsi
    
rsi_no_loss:
    fmov s14, #100.0        // RSI = 100 when no losses
    
store_rsi:
    lsl x22, x20, #2
    str s14, [x1, x22]      // Store RSI value
    
    add x20, x20, #1
    b rsi_calculation_loop
    
rsi_complete:
    ldp x23, x24, [sp, #16]
    ldp x21, x22, [sp, #32]
    ldp x19, x20, [sp, #48]
    ldp x29, x30, [sp], #64
    ret
