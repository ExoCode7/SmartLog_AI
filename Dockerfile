FROM python:3.9-slim

WORKDIR /app

COPY conda.yml environment.yml spec-file.txt ./

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    sh miniconda.sh -b -p /miniconda && \
    rm miniconda.sh
ENV PATH="/miniconda/bin:${PATH}"

RUN conda env create -f conda.yml

COPY . /app

# We'll define the final entrypoint in later phases, e.g.,
# CMD ["python", "src/main_mvp.py"]
