# Prerequisites — Installation Guide

Read this file when `acli --version` or `mdadf --version` fails (tool not found).

## acli

- macOS: `brew install atlassian-labs/tap/acli`
- Linux/Windows: download from https://developer.atlassian.com/cloud/acli/guides/install-acli/
- After install, authenticate with `acli auth login`

## mdadf

Download the binary for your platform from https://github.com/chenhunghan/mdadf/releases/latest and place it on your PATH:

- macOS (Apple Silicon): `curl -L -o mdadf.tar.gz https://github.com/chenhunghan/mdadf/releases/latest/download/mdadf-darwin-arm64.tar.gz && tar xzf mdadf.tar.gz && mv mdadf /usr/local/bin/`
- macOS (Intel): replace `darwin-arm64` with `darwin-x64`
- Linux (x86_64): replace with `linux-x64`
- Windows: download `mdadf-windows-x64.zip` from the releases page and add to PATH
- If sudo is needed: install to `$HOME/.local/bin` and ensure it is on PATH.

If either tool cannot be installed (e.g. no network access), tell the user exactly what commands to run and stop.
