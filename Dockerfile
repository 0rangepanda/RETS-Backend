FROM debian:9.5
MAINTAINER Jay Luo <jayluo9410@gmail.com>

# Install libRETS and python binding
WORKDIR /librets
ADD ./libRETS/ /librets/

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    autoconf \
    swig \
    libboost-dev \
    libboost-filesystem-dev \
    libcurl4-openssl-dev \
    libexpat-dev \
    default-jdk \
    && ./autogen.sh \
    && ./configure \
    --enable-depends \
    --enable-shared_dependencies \
    && make \
    && make install \
    && rm -rf /var/lib/apt/lists/*

# Create the group and user to be used in this container (read-only)
WORKDIR /home/flask/app/backend

RUN groupadd flaskgroup && useradd -m -g flaskgroup -s /bin/bash flask \
    && chown -R flask:flaskgroup /home/flask

# Install the package dependencies
COPY ./backend/requirements.txt /home/flask/app/backend/
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY ./backend/ /home/flask/app/backend/


# After installing everthing, switch to right user
USER flask
