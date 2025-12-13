## 2024-05-23 - [Busy Wait Optimization]
**Learning:** Replaced `time.sleep(0.001)` busy loops with `threading.Condition` in worker threads.
**Action:** Always verify if polling loops can be replaced by event-driven synchronization (Condition, Event, Queue) to save CPU cycles.
