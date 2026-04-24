# Fabri-Form

**A digital pipeline for collaborative pattern cutting.**
Stage 01 of a staged research project.

Yu Ting Liao · MA Computational Arts · Goldsmiths, University of London · 2026

---

## What this is

Fabri-Form accepts a hand-drawn sketch, routes it through a multimodal
language model (Claude Sonnet, via the Anthropic API), derives a set of
garment parameters, and draws a printable 1:1 pattern in the browser.
It is a translation tool between the sensitivity of design and the
physical act of pattern tracing.

## Architecture

- **`index.html`** — the front-end interface. Pure HTML / CSS / JS,
  no build step. Hosted on GitHub Pages.
- **`proxy.py`** — a small Python proxy that forwards browser requests
  to the Anthropic API, attaches the API key server-side, and returns
  results with permissive CORS headers. Hosted on Render.
- **Fallback paths** — if the proxy is unreachable, the front-end falls
  back to a set of preset sketches with ground-truth parameters and a
  pixel-level heuristic that runs entirely in the browser.

## Run locally

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 proxy.py
# then open index.html in a browser
```

## Cloud deployment

The proxy is configured for Render via `render.yaml`. The API key is
read from the `ANTHROPIC_API_KEY` environment variable and is never
stored in the source.

---

## Submission

This repository is part of the MA Computational Arts Individual Research
Project submission. The accompanying written submission, poster, and
process video are submitted separately through the Goldsmiths VLE.
