## 2024-05-23 - Busy-Wait Elimination in Workers
**Learning:** Found `ASRWorker` and `MTWorker` using `while True: time.sleep(0.001)` to poll queues. This is a classic busy-wait pattern that burns CPU cycles unnecessarily.
**Action:** Replaced busy-waits with `threading.Condition`. Threads now `wait()` efficiently and are `notify()`'d when data arrives. Always check for tight `sleep()` loops in worker threads.
