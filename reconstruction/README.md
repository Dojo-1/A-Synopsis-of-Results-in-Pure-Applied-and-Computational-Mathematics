# Reconstruction pilot · source first

**Status:** source fidelity verified locally on 2026-10-31; publication review required before releasing reconstructed sources or replacing any PDF.

This directory documents a controlled reconstruction of the *2026 Unified Edition v1.1*. The published PDFs in `editions/` are **immutable references** for this work. None has been replaced.

## What was actually recovered

The original companion file `Synopsis_2026_Volumes_0-IV_Peer_Reviewed_sLANG_S1_v1.1.lang` (held separately from this repository) contains 5,000 `source_b64` witnesses and 5,000 record-level `source_sha256` digests. Decode each witness, verify its digest, concatenate its original serialized JSON lines in canonical order with LF line endings and a final LF, and verify the overall digest:

```text
e63df14867bb38614deff42517d6e45e9ad11bd3b03dfd51607efa6390bb7cad
```

This reconstruction **matched byte-for-byte**. The resulting `REGISTRY_00000001_00005000_REVIEWED.jsonl` is the exact original serialized registry; it was **not** inferred or rewritten from extracted PDF paragraphs.

The source `.lang` and recovered JSONL have **not** been added to the public repository. Their publication, including embedded provenance and correction metadata, is a separate decision.

## Structural and PDF checks

See [the measured audit](SOURCE_FIDELITY_REPORT.md). The independent checks found 5,000 sequential records, 6,924 hard dependencies, one root, one weakly connected component, zero cycles, zero dangling hard references, and the original evidence distribution (`A=2268 · M=2364 · S=365 · H=3 · P=0`). These are **structural facts about the recovered snapshot**, not independently proved mathematics.

The two published PDF SHA-256 hashes and the page counts (467 / 437) matched their manifest. In the §-LANG PDF, all 5,000 claim IDs, statuses, titles, and hard-dependency lists were recovered. **Five** rendered statement texts omit the `≅` isomorphism character; the exact JSONL witness correctly retains it.

## Local reproduction

Use [`recover_registry.py`](recover_registry.py) with the original complete `.lang` source:

```sh
python3 reconstruction/recover_registry.py \
  --lang /path/to/Synopsis_2026_Volumes_0-IV_Peer_Reviewed_sLANG_S1_v1.1.lang \
  --output /path/to/recovered/
sha256sum /path/to/recovered/REGISTRY_00000001_00005000_REVIEWED.jsonl
```

This decoder uses only the Python standard library, fails closed on a mismatch, and reports the recovered graph and evidence distribution. Keep the output outside the public repository until its full provenance has been reviewed.

A separate local rendering experiment produced a **640-page reader projection** (635 typeset pages plus the five original Volume IV visual-plate facsimiles). It preserves every canonical record and uses a font covering the source’s mathematical glyphs, but is **not** a page-identical facsimile and does not replace v1.1.

## Rebuild and compare the PDF reading surfaces

With the exact recovered JSONL and both original v1.1 PDFs available locally:

```sh
python3 -m pip install -r reconstruction/requirements.txt

python3 reconstruction/check_pdfs.py \
  --registry /path/to/recovered/REGISTRY_00000001_00005000_REVIEWED.jsonl \
  --unified /path/to/Synopsis_2026_Volumes_0-IV_Peer_Reviewed_Consolidated_v1.1.pdf \
  --slang /path/to/Synopsis_2026_Volumes_0-IV_sLANG_S1_Translated_Peer_Reviewed_v1.1.pdf \
  --out /path/to/audit-output/

python3 reconstruction/render_registry.py \
  --registry /path/to/recovered/REGISTRY_00000001_00005000_REVIEWED.jsonl \
  --output /path/to/Synopsis_Reconstructed_Reader_Edition_v0.1.pdf

python3 reconstruction/append_plates.py \
  --reader /path/to/Synopsis_Reconstructed_Reader_Edition_v0.1.pdf \
  --source /path/to/Synopsis_2026_Volumes_0-IV_Peer_Reviewed_Consolidated_v1.1.pdf \
  --output /path/to/Synopsis_Reconstructed_Reader_With_Source_Plates_v0.1.pdf
```

Then mechanically verify the full regenerated reader (including the five appended source plates):

```sh
python3 reconstruction/qa_rebuilt.py \
  --registry /path/to/recovered/REGISTRY_00000001_00005000_REVIEWED.jsonl \
  --reader /path/to/Synopsis_Reconstructed_Reader_With_Source_Plates_v0.1.pdf \
  --report /path/to/rebuilt_pdf_QA.json
```

The locally validated 640-page output achieved **5,000/5,000** exact record headings, statements (after Unicode NFKC and whitespace normalization), evidence labels and hard-dependency lists, with zero out-of-bounds text spans and five preserved source-plate pages.

`render_registry.py` currently uses installed DejaVu Sans TrueType files at `/usr/share/fonts/truetype/dejavu/`. The typography is a new **editorial projection**, not the original A4 page breaks. It includes record IDs, titles, statements, status, typed dependencies, explicit assumptions, and peer-review corrections; the JSONL retains **all** fields.

These scripts and their documented outputs were exercised locally on the source files. They are not yet integrated as a CI job because the exact reversible `.lang` source is not distributed in this repository.

## Integrity boundaries

- Original `editions/` PDFs remain the historical references.
- Byte-exact registry recovery **does not** establish truth of `A` claims or a general theorem from an `M` fixture.
- Missing assumptions metadata on 1,196 `A` records in Volumes I–III remains unresolved.
- An exact registry-to-§-LANG witness round trip is different from equivalence of mathematical interpretations.
- Independent mathematical refereeing and comprehensive formula layout review are outstanding.

Further edits should remain on review branches until provenance, glyphs, cross-edition completeness, rendering and distribution permissions have been checked.