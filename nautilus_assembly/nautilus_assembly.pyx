# nautilus_assembly/nautilus_assembly.pyx
# Cython bindings for ARM64 assembly engine
from libc.stdint cimport uint64_t, int32_t, uintptr_t
from libc.stdlib cimport malloc, free
import numpy as np
cimport numpy as cnp

cdef extern from "assembly_engine.h":
    int32_t nautilus_update_l2_level(
        void* order_book,
        int32_t side,
        uint64_t price_raw,
        uint64_t quantity_raw,
        int32_t action
    ) nogil
    
    void nautilus_process_tick_batch(
        void* input_ticks,
        void* output_events,
        uint64_t count,
        uint64_t instrument_id
    ) nogil
    
    void nautilus_calculate_ema_vectorized(
        float* prices,
        float* output,
        uint64_t count,
        float alpha
    ) nogil
    
    void nautilus_calculate_rsi_vectorized(
        float* prices,
        float* rsi_output,
        uint64_t count,
        uint64_t period
    ) nogil
    
    uint64_t nautilus_validate_order_batch(
        void* orders,
        void* positions,
        void* limits,
        uint64_t count
    ) nogil

cdef class AssemblyOrderBookEngine:
    """Ultra-fast order book engine using ARM64 assembly"""
    
    cdef void* _book_ptr
    cdef uint64_t _instrument_id
    
    def __init__(self, book_ptr, instrument_id):
        self._book_ptr = <void*><uintptr_t>book_ptr
        self._instrument_id = instrument_id
    
    cpdef bint update_level(
        self,
        int side,
        double price,
        double quantity,
        int action
    ):
        """Update order book level using assembly engine"""
        cdef uint64_t price_raw = <uint64_t>(price * 1e8)
        cdef uint64_t qty_raw = <uint64_t>(quantity * 1e8)
        
        cdef int32_t flags
        with nogil:
            flags = nautilus_update_l2_level(
                self._book_ptr,
                side,
                price_raw,
                qty_raw,
                action
            )
        
        return (flags & 0x2) != 0  # Return True if top of book changed

cdef class AssemblyMarketDataProcessor:
    """SIMD-accelerated market data processing"""
    
    cdef uint64_t _instrument_id
    
    def __init__(self, instrument_id):
        self._instrument_id = instrument_id
    
    def process_ticks(self, ticks):
        """Process batch of ticks using SIMD assembly"""
        cdef uint64_t count = len(ticks)
        if count == 0:
            return []
        
        # Use malloc instead of aligned_alloc for compatibility
        cdef void* input_buffer = malloc(count * 32)
        cdef void* output_buffer = malloc(count * 48)
        
        if input_buffer == NULL or output_buffer == NULL:
            if input_buffer != NULL:
                free(input_buffer)
            if output_buffer != NULL:
                free(output_buffer)
            raise MemoryError("Failed to allocate memory")
        
        # Copy tick data to input buffer
        self._copy_ticks_to_buffer(ticks, input_buffer)
        
        # Process using assembly
        with nogil:
            nautilus_process_tick_batch(
                input_buffer,
                output_buffer,
                count,
                self._instrument_id
            )
        
        # Convert results back to Python objects
        result = self._convert_from_buffer(output_buffer, count)
        
        free(input_buffer)
        free(output_buffer)
        return result
    
    cdef void _copy_ticks_to_buffer(self, ticks, void* buffer):
        """Copy tick data to C buffer"""
        cdef float* float_buffer = <float*>buffer
        cdef int i
        
        for i, tick in enumerate(ticks):
            float_buffer[i * 4] = float(tick.get('price', 0.0))
            float_buffer[i * 4 + 1] = float(tick.get('quantity', 0.0))
            float_buffer[i * 4 + 2] = float(tick.get('timestamp', 0.0))
            float_buffer[i * 4 + 3] = 0.0  # padding
    
    cdef list _convert_from_buffer(self, void* buffer, uint64_t count):
        """Convert C buffer back to Python objects"""
        result = []
        cdef float* float_buffer = <float*>buffer
        cdef int i
        
        for i in range(count):
            result.append({
                'instrument_id': self._instrument_id,
                'price': float_buffer[i * 3],
                'quantity': float_buffer[i * 3 + 1],
                'scaled_price': int(float_buffer[i * 3 + 2])
            })
        
        return result

cdef class AssemblySignalEngine:
    """High-performance technical indicator calculations"""
    
    def calculate_ema(self, cnp.ndarray[float, ndim=1] prices, float alpha):
        """Calculate EMA using vectorized assembly"""
        cdef uint64_t count = prices.shape[0]
        cdef cnp.ndarray[float, ndim=1] output = np.zeros(count, dtype=np.float32)
        
        with nogil:
            nautilus_calculate_ema_vectorized(
                &prices[0],
                &output[0],
                count,
                alpha
            )
        
        return output
    
    def calculate_rsi(self, cnp.ndarray[float, ndim=1] prices, int period):
        """Calculate RSI using vectorized assembly"""
        cdef uint64_t count = prices.shape[0]
        cdef cnp.ndarray[float, ndim=1] output = np.zeros(count, dtype=np.float32)
        
        with nogil:
            nautilus_calculate_rsi_vectorized(
                &prices[0],
                &output[0],
                count,
                period
            )
        
        return output

cdef class AssemblyRiskEngine:
    """Ultra-fast risk validation engine"""
    
    def validate_order_batch(self, orders, positions, limits):
        """Validate batch of orders using assembly"""
        cdef uint64_t count = len(orders)
        if count == 0:
            return []
        
        # Use malloc instead of aligned_alloc
        cdef void* order_buffer = malloc(count * 16)
        cdef void* position_buffer = malloc(len(positions) * 8)
        cdef void* limits_buffer = malloc(12)  # 3 limits * 4 bytes
        
        if order_buffer == NULL or position_buffer == NULL or limits_buffer == NULL:
            if order_buffer != NULL:
                free(order_buffer)
            if position_buffer != NULL:
                free(position_buffer)
            if limits_buffer != NULL:
                free(limits_buffer)
            raise MemoryError("Failed to allocate memory")
        
        # Copy data to buffers
        self._copy_orders_to_buffer(orders, order_buffer)
        self._copy_positions_to_buffer(positions, position_buffer)
        self._copy_limits_to_buffer(limits, limits_buffer)
        
        cdef uint64_t result_mask
        with nogil:
            result_mask = nautilus_validate_order_batch(
                order_buffer,
                position_buffer,
                limits_buffer,
                count
            )
        
        # Convert bitmask to list of booleans
        result = []
        for i in range(count):
            result.append((result_mask & (1 << i)) != 0)
        
        free(order_buffer)
        free(position_buffer)
        free(limits_buffer)
        return result
    
    cdef void _copy_orders_to_buffer(self, orders, void* buffer):
        """Copy order data to C buffer"""
        cdef int* int_buffer = <int*>buffer
        cdef int i
        
        for i, order in enumerate(orders):
            int_buffer[i * 4] = int(order.get('symbol_id', 0))
            int_buffer[i * 4 + 1] = int(order.get('quantity', 0))
            int_buffer[i * 4 + 2] = int(order.get('price', 0) * 100)  # scaled price
            int_buffer[i * 4 + 3] = 0  # padding
    
    cdef void _copy_positions_to_buffer(self, positions, void* buffer):
        """Copy position data to C buffer"""
        cdef int* int_buffer = <int*>buffer
        cdef int i = 0
        
        for symbol_id, position in positions.items():
            int_buffer[i * 2] = int(symbol_id)
            int_buffer[i * 2 + 1] = int(position)
            i += 1
    
    cdef void _copy_limits_to_buffer(self, limits, void* buffer):
        """Copy limits data to C buffer"""
        cdef int* int_buffer = <int*>buffer
        
        int_buffer[0] = int(limits.get('max_position_size', 1000))
        int_buffer[1] = int(limits.get('min_price', 0) * 100)  # scaled
        int_buffer[2] = int(limits.get('max_price', 1000000) * 100)  # scaled
