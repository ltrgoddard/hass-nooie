ARG BUILD_FROM=python:3.12-slim-bookworm
FROM ${BUILD_FROM}

ARG BUILD_ARCH=amd64
# How nooie-proxy is installed. It is its own package on PyPI, pinned here so
# an add-on build is reproducible; point this at a git URL to test a branch.
ARG NOOIE_PKG="nooie-proxy==0.1.0"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "${NOOIE_PKG}" \
    && case "${BUILD_ARCH}" in \
        amd64)   GO2RTC_ARCH=amd64 ;; \
        aarch64) GO2RTC_ARCH=arm64 ;; \
        *) echo "unsupported architecture: ${BUILD_ARCH}" >&2; exit 1 ;; \
       esac \
    && curl -fsSL -o /usr/local/bin/go2rtc \
        "https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_${GO2RTC_ARCH}" \
    && chmod +x /usr/local/bin/go2rtc

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
