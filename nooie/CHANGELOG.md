# Changelog

## 0.1.1

- The add-on image is 177 MB, from 305 MB. It builds on Alpine, and it keeps
  neither pip nor the bytecode cache, which a running add-on does not use.

## 0.1.0

- First release. The add-on runs one preloaded nooie-proxy process for each
  camera, and go2rtc serves each stream as RTSP, WebRTC, and HLS. The add-on
  installs the proxy from PyPI. The proxy has its own repository,
  [nooie-proxy](https://github.com/ltrgoddard/nooie-proxy).
