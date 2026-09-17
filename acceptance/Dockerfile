# Public multi-toolchain acceptance environment used for candidate verification.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      bash coreutils ca-certificates git make build-essential \
      python3 nodejs npm golang-go rustc cargo openjdk-21-jdk-headless \
 && npm install -g typescript@5.6.3 \
 && npm cache clean --force \
 && rm -rf /var/lib/apt/lists/* \
 && for tool in bash git make gcc g++ python3 node npm tsc go rustc cargo javac java; do \
      command -v "$tool" >/dev/null || exit 1; \
    done

ENV HOME=/tmp \
    GOCACHE=/tmp/gocache \
    GOPATH=/tmp/gopath \
    GOFLAGS=-mod=mod \
    CARGO_HOME=/tmp/cargo \
    npm_config_cache=/tmp/npm

WORKDIR /work
USER 65534:65534
CMD ["bash"]
