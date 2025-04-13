FROM python:3.9-bookworm

RUN apt-get update && apt-get install -y \
    libdjvulibre-dev \
    libtiff-dev \
    libjpeg-dev \
    ghostscript \
    poppler-utils \
    # Jbig2enc build requirements below
    git autotools-dev automake libtool libleptonica-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# add Jbig2enc, after debian 13 is released, this can be removed (libjbig2enc-dev will be available)
WORKDIR /opt
RUN git clone https://github.com/agl/jbig2enc

WORKDIR /opt/jbig2enc 
RUN ./autogen.sh && ./configure && make install

# Continue with environment setup 
RUN pip install poetry
RUN pip install ocrmypdf

WORKDIR /app
COPY . /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

RUN mkdir /files

WORKDIR /files

ENTRYPOINT ["python", "-m", "dpsprep"]
