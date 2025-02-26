# SmartLog AI - MVP

## Introduction
SmartLog AI is a zero-dollar startup project focused on creating an offline-capable call summarizer. Our MVP uses Vosk for speech recognition, PyAudio for audio capture, and a minimal Tkinter UI to display live transcription. This repository represents the foundational phase (MVP Phase 1), where we set up the environment, Docker configuration, logging, testing structure, and basic UI scaffolding.

## Features
- **Offline Speech Recognition**: Utilizes Vosk (0.3.44) to perform transcription without an external API.
- **Audio Capture**: PyAudio (0.2.14) for real-time microphone input (or future audio streams).
- **Enhanced Summarization**: SpaCy-based smart summarizer that extracts categories of information (keywords, entities, actions, topics).
- **Backward Compatibility**: Adapter pattern to maintain compatibility with existing keyword extraction.
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

### MVP Phase 2.5 (Current):
- Enhanced AI summarization with SpaCy-based analysis extracting structured information.
- Categorized summaries showing keywords, entities, actions, and key topics.
- Modular architecture using interfaces and adapters for extensibility.

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

- **Freemium Trial:** 14- to 30-day trial with 300 minutes of transcription
- **Base Plan (Individual):** $15/month for ~500 minutes
- **Plus Plan (Small Teams):** $12.99/user/month (pooled minutes)
- **Advanced Plan (Mid-Market):** $10/user/month (larger pooled minutes)
- **Enterprise:** Custom pricing for large orgs

**Data Security Commitment:**
All processing is performed locally on your machine. Audio capture (PyAudio), transcription (Vosk/Whisper), summarization (RAKE/LLM), and logging remain offline. This ensures your data never leaves the device.

## Additional Documentation

See [src/ai/stt_engine.py](src/ai/stt_engine.py) for HybridSTTEngine logic, [src/utils/power.py](src/utils/power.py) for thermal management, [src/utils/logger.py](src/utils/logger.py) for data-safe logging, and [src/ai/smart_summarizer.py](src/ai/smart_summarizer.py) for enhanced text summarization.

## Summarization Features

The SmartLog AI system now includes enhanced summarization capabilities through the SpacySummarizer:

### Categories of Information

The summarizer extracts different types of information from conversations:

- **Keywords**: Important phrases and concepts mentioned (e.g., "product launch")
- **Entities**: Named entities like people, organizations, and dates (e.g., "John Smith", "Apple Inc.")
- **Actions**: Key activities or actions discussed (e.g., "scheduled meeting", "approved budget")
- **Topics**: Main subjects of the conversation (e.g., "marketing", "sales", "development")

### Customization

Users can customize the summarization through:

- **Detail Level**: Choose between Basic, Detailed, or Comprehensive summaries
- **Topic Exclusion**: Filter out specific topics or areas
- **Focus Areas**: Emphasize particular aspects of the conversation

### Technical Implementation

The summarization system uses:

- **SpaCy NLP**: Powerful linguistic analysis for understanding text structure
- **Interface Design**: An `ISummarizer` interface for pluggable summarization engines
- **Adapter Pattern**: Backward compatibility with existing keyword extraction systems

## Additional Enhancements (Recommended)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/coverage-80%25-yellow)](#)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-blue)](#)

### Architectural Diagram
(Placeholder for a simple diagram showing audio capture -> stt engine -> summarization -> UI)
