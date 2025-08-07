# after Debian 13 (trixie) is released, this can be removed in favor of the libjbig2enc-dev package
FROM debian:bookworm-slim AS jbig2enc-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential autoconf automake libtool \
    libleptonica-dev \
    zlib1g-dev \
    libffi-dev \
    ca-certificates \
    curl \
    git \
    libcairo2-dev \
    pkg-config

WORKDIR /opt

RUN git clone --depth 1 https://github.com/agl/jbig2enc && \
    cd jbig2enc && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install

# The actual image to be used
FROM python:3.11-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libdjvulibre-dev \
    libtiff-dev \
    libjpeg-dev \
    ghostscript \
    poppler-utils \
    libleptonica-dev \
    # libjbig2enc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=jbig2enc-builder /usr/local/lib/ /usr/local/lib/
COPY --from=jbig2enc-builder /usr/local/bin/ /usr/local/bin/

RUN pip install --no-cache-dir poetry ocrmypdf

WORKDIR /app
COPY . .

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

RUN mkdir /files

WORKDIR /files

ENTRYPOINT ["python", "-m", "dpsprep"]
