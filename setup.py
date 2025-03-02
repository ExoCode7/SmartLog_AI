from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smartlog-ai",
    version="0.1.0",
    author="ExoCode7",
    description="Offline-capable audio summarizer with NLP-powered analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smartlog-ai",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/smartlog-ai/issues",
        "Documentation": "https://github.com/yourusername/smartlog-ai#readme",
    },
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "vosk==0.3.44",
        "openai-whisper==20240930",
        "pyaudio==0.2.14",
        "psutil==5.9.5",
        "spacy==3.7.2",
        "torch==2.2.2",
        "numpy==1.24.3",
        "tiktoken==0.9.0",
        "packaging==23.2",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-mock==3.10.0",
            "black==24.3.0",
            "flake8==6.0.0",
            "flake8-pyproject==1.2.3",
            "bandit==1.7.5",
            "pre-commit==3.3.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "smartlog=src.main_mvp:main",
        ],
    },
)
