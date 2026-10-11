module shen/io
import std/num/int32
extern import { c file "io-inline.c" }
pub extern stream-open(name:string,writing:bool): console int32 { c inline "shen_stream_open(#1,#2,kk_context())" }
pub extern stream-read(id:int32): console int32 { c inline "shen_stream_read(#1,kk_context())" }
pub extern stream-write(id:int32,byte:int32): console int32 { c inline "shen_stream_write(#1,#2,kk_context())" }
pub extern stream-close(id:int32): console int32 { c inline "shen_stream_close(#1,kk_context())" }
pub extern clock-time(run:bool): console float64 { c inline "shen_clock_time(#1,kk_context())" }
pub extern process-exit(code:int32): console () { c inline "shen_process_exit(#1,kk_context())" }

pub extern stdin-eof(): console bool { c inline "shen_stdin_eof(kk_context())" }
