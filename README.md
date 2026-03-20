# Flowl

> **Advanced Overlay Natural Language Processing Real-Time Speech Translator**

> **Work in Progress** — This project is under active development. Features, APIs, and configurations are subject to change.

---

## Overview

**Flowl** is a Windows desktop application that provides real-time speech translation rendered as a transparent always-on-top overlay. It is designed to be used alongside any application — games, video calls, lectures, or media — without interrupting your workflow.

Speech is captured from your microphone, recognised using offline ASR models (Vosk), translated using local NLP transformer models (Helsinki-NLP via HuggingFace Transformers), and rendered live as floating text directly over your desktop.

---

## Requirements

- **Python** 3.10+
- **Windows** 10/11 (transparent frameless overlay requires Windows compositor)
- **Vosk models** — downloaded separately and configured in Advanced Settings
- **GPU optional** — MT runs on CPU by default; GPU acceleration available via PyTorch

## License

MIT © thaisya
