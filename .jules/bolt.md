## 2024-11-20 - Worker Thread Busy-Wait Removal
**Learning:** Python worker threads using `while True: sleep(0.001)` for queue polling cause significant CPU waste (approx 1000 wakeups/sec per worker) even when idle.
**Action:** Replace `threading.Lock` + busy-wait with `threading.Condition` + `wait()`. This eliminates CPU usage when queues are empty and improves responsiveness.
