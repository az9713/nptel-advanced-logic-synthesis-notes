# Advanced Logic Synthesis

Open the [GitHub Pages reader](https://az9713.github.io/nptel-advanced-logic-synthesis-notes/), [recording map](https://az9713.github.io/nptel-advanced-logic-synthesis-notes/source-map.html), or [computational laboratory](https://az9713.github.io/nptel-advanced-logic-synthesis-notes/laboratory.html). These independent study notes cover Dhiraj Taneja's 34-recording IIT Madras course in 11 chapters. Each chapter is available in HTML and Markdown. [NPTEL course](https://nptel.ac.in/courses/117106109) · [Official syllabus](https://archive.nptel.ac.in/content/syllabus_pdf/117106109.pdf)

The [inventory](lecture-inventory.csv) records the English track used for each recording, its endpoint, and its SHA-256 digest. Recordings 22, 24, and 31 use local speech recognition after YouTube rate-limited their English captions. Technical spellings and equations in the notes follow the circuit derivations and cited primary references.

The worked execution slice and numerical inputs are original teaching examples. The course's Design Compiler, PrimeTime, and Formality demonstrations provide the procedural context. The executable checks use Python, ngspice, and Yosys. The source review used transcript cues, including speech recognition from the three fallback audio tracks. Slide frames and commercial tool sessions were outside the verification.

## Rebuild and verify

Run `python -m pip install -r requirements.txt` and `python tools/build.py` from this directory. The reader uses a bundled MathJax distribution under the [Apache License](assets/mathjax-LICENSE), so its equations render offline. Recording links open the original videos online.

`python tools/figures.py` regenerates the two model plots with Matplotlib.

Run `python code/lab.py all` for the deterministic numerical checks. See [the laboratory instructions](code/README.md) for the ngspice and Yosys examples.

Run `python tools/check.py` for source and link validation. Add `--browser "C:/Program Files/Google/Chrome/Application/chrome.exe"` with Playwright installed to test desktop and mobile rendering.

## Verification results

- The 34 transcript endpoints are within 13 seconds of the playlist durations. The inventory validator checked each transcript hash and the 87 timestamp pointers.
- The 14 reader pages loaded at 1440 px and 390 px with network access to external assets disabled. Chapter navigation, local links, and equation rendering passed.
- All ten Python lab checks passed. Separate ngspice measurements reproduced the RC crossing and slew. Yosys proved the eight matched result bits and the reset base case for the mapped slice, proved the selector relocation, and confirmed the injected mismatch.
