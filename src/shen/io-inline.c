/* Minimal byte-stream boundary. Language values and evaluation remain in Koka. */
#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include <limits.h>
static FILE *shen_streams[4096];
static int32_t shen_stream_ids[4096];
static FILE *shen_stream(int32_t n) {
  if (n==0) return stdin;
  if (n==1) return stdout;
  if (n==2) return stderr;
  if(n<3) return NULL;
  int32_t slot=n % 4096;
  return slot>=3 && shen_stream_ids[slot]==n ? shen_streams[slot] : NULL;
}
static int32_t shen_stream_open(kk_string_t name, bool writing, kk_context_t *ctx) {
  int32_t n=3;
  while(n<4096 && (shen_streams[n] || shen_stream_ids[n]>INT32_MAX-4096)) n++;
  FILE *f = n<4096 ? fopen(kk_string_cbuf_borrow(name,NULL,ctx),writing ? "wb" : "rb") : NULL;
  kk_string_drop(name,ctx);
  if(!f) return -1;
  shen_streams[n]=f;
  shen_stream_ids[n] = shen_stream_ids[n]==0 ? n : shen_stream_ids[n]+4096;
  return shen_stream_ids[n];
}
static int32_t shen_stream_read(int32_t id, kk_context_t *ctx) {
  (void)ctx; FILE *f=shen_stream(id); if(!f) return -2;
  int c=fgetc(f); return c==EOF ? (ferror(f) ? -2 : -1) : c;
}
static int32_t shen_stream_write(int32_t id,int32_t byte,kk_context_t *ctx) {
  (void)ctx; FILE *f=shen_stream(id);
  if(!f || byte<0 || byte>255 || fputc(byte,f)==EOF) return -1;
  if(id==1 || id==2) fflush(f);
  return byte;
}
static int32_t shen_stream_close(int32_t id,kk_context_t *ctx) {
  (void)ctx; FILE *f=shen_stream(id); if(!f) return -1;
  if(id<3) return 0;
  shen_streams[id % 4096]=NULL; return fclose(f);
}
static double shen_clock_time(bool run,kk_context_t *ctx) {
  (void)ctx; return run ? (double)clock()/CLOCKS_PER_SEC : (double)time(NULL);
}
static kk_unit_t shen_process_exit(int32_t code,kk_context_t *ctx) {
  (void)ctx; exit(code); return kk_Unit;
}

static bool shen_stdin_eof(kk_context_t *ctx) { (void)ctx; return feof(stdin)!=0; }
