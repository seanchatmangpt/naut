// nautilus_assembly/src/risk_engine.s
// Ultra-fast risk validation engine
.section __TEXT,__text
.global _nautilus_validate_order_batch
.align 4

// Args: x0=orders*, x1=positions*, x2=limits*, x3=count
// Returns: x0=bitmask of valid orders
_nautilus_validate_order_batch:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    
    mov x4, #0              // Result bitmask
    mov x5, #0              // Counter
    
validation_loop:
    cmp x5, x3
    b.ge validation_done
    
    // Load order data (symbol_id, quantity, price)
    lsl x6, x5, #4          // order_size = 16 bytes
    add x7, x0, x6
    
    ldr w8, [x7]            // symbol_id
    ldr w9, [x7, #4]        // quantity
    ldr w10, [x7, #8]       // price
    
    // Load current position for this symbol
    lsl x11, x8, #3         // position_size = 8 bytes
    add x12, x1, x11
    ldr w13, [x12]          // current_position
    
    // Calculate new position
    add w14, w13, w9        // new_position = current + order_quantity
    
    // Load position limit
    ldr w15, [x2]           // max_position_size
    
    // Check position limit
    cmp w14, w15
    b.gt order_invalid
    neg w16, w15
    cmp w14, w16
    b.lt order_invalid
    
    // Check price limits
    ldr w16, [x2, #4]       // min_price
    ldr w17, [x2, #8]       // max_price
    
    cmp w10, w16
    b.lt order_invalid
    cmp w10, w17
    b.gt order_invalid
    
order_valid:
    mov x6, #1
    lsl x6, x6, x5          // Create bit mask for this position
    orr x4, x4, x6          // Set bit in result
    
order_invalid:
    add x5, x5, #1
    b validation_loop
    
validation_done:
    mov x0, x4              // Return bitmask
    ldp x29, x30, [sp], #16
    ret

.global _nautilus_calculate_portfolio_var
.align 4

// Args: x0=positions*, x1=correlations*, x2=volatilities*, x3=count
// Returns: x0=portfolio_var (as scaled integer)
_nautilus_calculate_portfolio_var:
    stp x29, x30, [sp, #-32]!
    stp x19, x20, [sp, #16]
    mov x29, sp
    
    mov x19, x3             // count
    fmov s16, #0.0          // portfolio_variance = 0
    
    // Calculate variance = sum(w_i * w_j * cov_ij)
    mov x4, #0              // i counter
    
outer_variance_loop:
    cmp x4, x19
    b.ge variance_calculation_done
    
    // Load position i
    lsl x5, x4, #3          // position offset
    ldr s0, [x0, x5]        // weight_i
    ldr s1, [x2, x5]        // volatility_i
    
    mov x6, #0              // j counter
    
inner_variance_loop:
    cmp x6, x19
    b.ge inner_loop_done
    
    // Load position j
    lsl x7, x6, #3
    ldr s2, [x0, x7]        // weight_j
    ldr s3, [x2, x7]        // volatility_j
    
    // Calculate correlation index: i * count + j
    mul x8, x4, x19
    add x8, x8, x6
    lsl x8, x8, #2          // correlation offset (4 bytes each)
    ldr s4, [x1, x8]        // correlation_ij
    
    // Calculate covariance: vol_i * vol_j * correlation_ij
    fmul s5, s1, s3         // vol_i * vol_j
    fmul s5, s5, s4         // * correlation_ij
    
    // Add to portfolio variance: weight_i * weight_j * covariance_ij
    fmul s6, s0, s2         // weight_i * weight_j
    fmul s6, s6, s5         // * covariance_ij
    fadd s16, s16, s6       // Add to portfolio variance
    
    add x6, x6, #1
    b inner_variance_loop
    
inner_loop_done:
    add x4, x4, #1
    b outer_variance_loop
    
variance_calculation_done:
    // Take square root to get portfolio volatility
    fsqrt s16, s16
    
    // Scale and convert to integer for return
    fmov s17, #100000000.0  // Scale factor
    fmul s16, s16, s17
    fcvtzs x0, s16          // Convert to integer
    
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
