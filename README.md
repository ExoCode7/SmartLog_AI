# SmartLog AI - MVP

## Introduction
SmartLog AI is a zero-dollar startup project focused on creating an offline-capable call summarizer. Our MVP uses Vosk for speech recognition, PyAudio for audio capture, and a minimal Tkinter UI to display live transcription. This repository represents the foundational phase (MVP Phase 1), where we set up the environment, Docker configuration, logging, testing structure, and basic UI scaffolding.

## Features
- **Offline Speech Recognition**: Utilizes Vosk (0.3.44) to perform transcription without an external API.
- **Audio Capture**: PyAudio (0.2.14) for real-time microphone input (or future audio streams).
- **Minimal UI**: Tkinter for a lightweight GUI, with plans to integrate 21st.dev for a modern interface later.
- **Docker**: A Dockerfile pinned to python:3.9-slim, installing Miniconda for environment consistency.
- **Pre-commit Hooks**: Bandit for security checks, Black for formatting, Flake8 for linting, and housekeeping hooks (trailing-whitespace, end-of-file-fixer).
- **Testing**: Pytest structure ready for unit tests, located in the `tests/` directory.

## Requirements
- **Miniconda** or **Anaconda** (Python 3.9)
- **Git** for version control
- (Optional) **Docker** if you plan to build a containerized version

### Apple Silicon Note
If you're on an M1/M2 Mac, install PortAudio (`brew install portaudio`) before creating the environment, so PyAudio can compile correctly.

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ExoCode7/SmartLogAI-MVP.git
   cd SmartLogAI-MVP
   ```

2. **Create and activate the Conda environment**:
   ```bash
   conda env create -f conda.yml
   conda activate smartlog-ai-mvp
   ```
   This installs Python 3.9, tk, and uses pip to install vosk, pyaudio, and pre-commit.

3. **Pre-commit hooks**:
   ```bash
   pre-commit install
   pre-commit run --all-files
   ```
   Ensures code formatting and security checks on each commit.

4. **Export environment (optional)**:
   ```bash
   conda env export --from-history > environment.yml
   conda list --explicit > spec-file.txt
   ```
   Some teams prefer to keep these in .gitignore.

## Usage
Currently, MVP Phase 1 only sets up the environment. To run any future code (e.g., main_mvp.py), you would:

```bash
python src/main_mvp.py
```
(Or the final entrypoint once implemented.)

**Docker usage (optional)**:
```bash
docker build -t smartlogai:latest .
docker run -it smartlogai:latest
```
Adjust as needed for your development workflow.

## Troubleshooting
- **PackagesNotFoundError**: If you see this for pyaudio or vosk, ensure they're in the pip: subsection of conda.yml.
- **PortAudio compilation issues (M1/M2 Macs)**: Run `brew install portaudio` before creating the environment.
- **Pre-commit not found**: Make sure you installed pre-commit==3.3.3 via pip in conda.yml, or run `pip install pre-commit`.
- **Trailing-whitespace or end-of-file-fixer "failures"**: These hooks auto-fix formatting issues, so just re-add and commit the changed files.

## Roadmap
### MVP Phase 1:
- Environment, Dockerfile, pre-commit, logging, testing scaffold, UI directory.

### MVP Phase 2:
- Basic AI summarization (keyword extraction) linked to the transcription pipeline.

### MVP Phase 3:
- Minimal Tkinter UI for real-time transcription display and summarized keywords.

### MVP Phase 4:
- Testing, feedback, bug fixes, and refinement before broader release.

## Acknowledgments
- Vosk contributors for offline speech recognition.
- PortAudio and PyAudio for enabling cross-platform audio capture.
- 21st.dev for future UI expansions and design inspiration.
- Bandit, Black, and Flake8 for code quality and security.
- The open-source community for making zero-dollar startups possible.

## Pricing Model and Roadmap Overview

Our pricing model is designed to scale with your needs while ensuring complete data security through 100% local processing. Our tiers include:

- **Freemium Trial:** A 14- to 30-day trial with 300 minutes of transcription, allowing you to experience the core functionality without any commitment.
- **Base Plan (Individual):** $15 per user per month for approximately 500 minutes of transcription. Overage fees apply at $0.25 per additional minute.
- **Plus Plan (Small Teams):** $12.99 per user per month for teams up to 10 members, with a pooled allocation of around 3,000 minutes. Overage fees are $0.20 per extra minute.
- **Advanced Plan (Mid-Market Teams):** $10 per user per month for teams with 11-25 users, with a pooled allocation of 7,500–10,000 minutes. Overage fees are $0.15 per extra minute.
- **Enterprise Plan (Large Organizations):** Custom pricing for 25+ users, including unlimited or high-volume usage bundles, advanced integrations, dedicated support, and additional features.

**Data Security Commitment:**
All processing is performed locally on your machine. Audio capture (via PyAudio), transcription (via Vosk/Whisper), summarization (via RAKE or locally-run LLMs), and even logging are designed to ensure that no data is transmitted externally. This local-first approach guarantees the highest level of data security and privacy for business consumers.

This roadmap and pricing model are continuously refined based on user feedback and market trends.
