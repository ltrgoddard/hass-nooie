ARG BUILD_FROM=python:3.12-alpine
FROM ${BUILD_FROM}

ARG BUILD_ARCH=amd64
# How nooie-proxy is installed. It is its own package on PyPI, pinned here so
# an add-on build is reproducible; point this at a git URL to test a branch.
ARG NOOIE_PKG="nooie-proxy==0.1.0"

# aiortc reads crc32c only for SCTP, which a receive-only call never opens,
# and google-crc32c has no musl wheel. Its pure-python fallback therefore
# costs nothing here, but it warns once per camera process. Keep that one
# warning out of the add-on log; every other warning still shows.
ENV PYTHONWARNINGS="ignore::RuntimeWarning:google_crc32c"

RUN apk add --no-cache ca-certificates \
    && pip install --no-cache-dir --no-compile "${NOOIE_PKG}" \
    && case "${BUILD_ARCH}" in \
        amd64)   GO2RTC_ARCH=amd64 ;; \
        aarch64) GO2RTC_ARCH=arm64 ;; \
        *) echo "unsupported architecture: ${BUILD_ARCH}" >&2; exit 1 ;; \
       esac \
    && wget -qO /usr/local/bin/go2rtc \
        "https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_${GO2RTC_ARCH}" \
    && chmod +x /usr/local/bin/go2rtc \
    # nothing installs at runtime, so pip and the bytecode cache are weight.
    && pip uninstall -y pip setuptools wheel >/dev/null 2>&1 || true \
    && find /usr/local/lib/python3.12 -name '__pycache__' -type d -prune -exec rm -rf {} + \
    && rm -rf /root/.cache

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
