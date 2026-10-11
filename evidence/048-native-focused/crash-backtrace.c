/* Diagnostic only: loaded explicitly for the failing generated-code probe. */
#include <execinfo.h>
#include <signal.h>
#include <unistd.h>
static void report_crash(int sig) {
  void *frames[40]; int n=backtrace(frames,40);
  backtrace_symbols_fd(frames,n,2); _exit(128+sig);
}
__attribute__((constructor)) static void install_handler(void) { signal(SIGSEGV,report_crash); }
