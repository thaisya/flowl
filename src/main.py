from audio import threads

def main():
    workers_init()
    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Manual exit")
    finally:
        shutdown()

def shutdown():
    stream.stop_stream()
    stream.close()
    audio_q.put(None)
    events_q.put(("final", "exit"))
    t_asr.join(timeout=1.0)
    t_mt.join(timeout=1.0)
    p.terminate()

if __name__ == "__main__":
    main()

