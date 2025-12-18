## 2024-05-23 - Busy-Wait Elimination
**Learning:** Found workers (`ASRWorker`, `MTWorker`) using `time.sleep(0.001)` loops to check for data. This consumed unnecessary CPU cycles and context switches (verified ~18k checks/sec idle).
**Action:** Replaced busy-waiting with `threading.Condition`. This is a classic pattern: `with cv: while not predicate: cv.wait()`. Ensure all producers call `cv.notify()`.
