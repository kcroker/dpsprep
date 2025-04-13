FROM python:3.9-bookworm

RUN apt-get update && apt-get install -y \
    libdjvulibre-dev \
    libtiff-dev \
    libjpeg-dev \
    ghostscript \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry
RUN pip install ocrmypdf

WORKDIR /app
COPY . /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

RUN mkdir /files

WORKDIR /files

ENTRYPOINT ["python", "-m", "dpsprep"]
