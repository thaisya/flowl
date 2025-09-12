"""Thread-safe queues for audio data and ASR/MT events.

Note: This file contains unused queue definitions. The actual queues are created
in FlowlApp.__init__() and passed to workers. These global definitions are
kept for potential future use or can be removed if not needed.
Note: Soon will be changed to another buffering logic
"""

import queue

# These queues are currently unused - FlowlApp creates its own queues
# Keeping them here for potential future use or reference
audio_q = queue.Queue(maxsize=100)
"""Raw audio chunks captured by PyAudio callback."""

events_q = queue.Queue(maxsize=200)
"""Events emitted by ASR (partial/final) consumed by the MT thread."""