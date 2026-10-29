# Sample Data

Ready-to-upload files for trying out EthiViz without needing your own dataset yet.
Use the **Upload Your Data** option in the sidebar (not "Use Sample Data" — that
button is currently wired to a single hardcoded example and doesn't support
image uploads; see note below) and pick a file from here.

## text/

Three files, each demonstrating a different supported upload format
(`ALLOWED_EXTENSIONS_TEXT` in `Scripts/api_server.py`: csv, xlsx, xls, json, txt):

- **mixed_bias_examples.csv** — 20 short statements spanning all 7 lenses
  (Western, Ubuntu, Confucian, Islamic, Buddhist, Hindu, Indigenous), mixing
  clean and clearly biased examples so you can see both ends of the score
  range. Same `text,bias_level,category,notes` schema as the curated
  per-tradition sets in `ethiviz/sample_data/` (those are the files behind the
  built-in "Use Sample Data" button today, and are worth a look for deeper,
  tradition-specific examples).
- **product_reviews.txt** — plain newline-delimited text, one review per line.
- **job_postings.json** — a JSON list of `{"text": ...}` objects.

Select "Text" (or "Text & Image") as the analysis type and upload one of these.

## images/

Three synthetic, programmatically generated PNGs (`gradient_sample.png`,
`geometric_pattern_sample.png`, `color_swatch_sample.png`) — colors and
shapes only, no people. They're here so you can exercise the full upload →
detection → 7-lens scoring → dashboard pipeline end-to-end without sourcing
real photos yourself.

**They contain no faces**, so face count and skin-tone detection will
correctly report zero/empty for all three — that's expected, not a bug. To
see real face/skin-tone/cultural-element detection results, upload your own
photos instead (and make sure vision extras are installed — see
`bash start_ethiviz.sh --with-vision`).

## Regenerating the images

Run `python3 sample_data/images/generate_samples.py` (uses Pillow, already a
project dependency) to regenerate or tweak these placeholder images.
