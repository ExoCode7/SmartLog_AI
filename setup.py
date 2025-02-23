from setuptools import setup, find_packages

setup(
    name="smartlog-ai",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "vosk==0.3.44",
        "pyaudio==0.2.14",
        "rake-nltk==1.0.6",
        "psutil==5.9.5",
        # Add other pinned dependencies from requirements.txt as needed
    ],
)
