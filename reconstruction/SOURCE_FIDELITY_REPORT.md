# Source-fidelity audit · 2026-10-31

Scope: independent local **binary identity**, **lossless registry recovery**, **dependency-graph topology**, and **rendered PDF text** checks. This is **not** external mathematical peer review.

| Source | Actual pages | SHA-256 verified against source/manifest |
|---|---:|---|
| Unified Edition v1.1 | 467 A4 | `b0f3ba069c3ea03c53a7df6d6f315c49239a7cb08eed175ef63997344821878e` |
| §-LANG PDF v1.1 | 437 A4 | `456fe8352d25de698673eb68441ae29237d6a45dc5c684c1769f8b7763ce7946` |
| §-LANG complete text source (separately held) | n/a | `3b74c95f6fbb94ad9b0ca4fc2fbbfaa808aa939dc1f769eada5d0382324b77f6` |
| Recovered original registry | 5,000 records | `e63df14867bb38614deff42517d6e45e9ad11bd3b03dfd51607efa6390bb7cad` |

**Exact reconstruction:** 5,000/5,000 Base64 source witnesses decoded and each record SHA-256 verified. Concatenated JSON lines with LF and final LF match the overall source registry hash. All recovered IDs are unique and numbered 1–5000.

**Independent graph audit:** 6,924 hard edges; 0 dangling dependencies; 1 root (`S26-N-00000001`); 1 weakly connected component; no directed cycles; no unknown dependency types.

**Evidence classification:** `A=2268`, `M=2364`, `S=365`, `H=3`, `P=0`. There remain 399 + 398 + 399 = **1,196** `A` records without explicit assumptions metadata in Volumes I, II and III.

**PDF cross-check:** 5,000/5,000 §-LANG claim IDs, titles, hard-dependency lists and statuses agree with the recovered registry. After NFKC and whitespace normalization, statement text agrees for 4,995/5,000. All five exceptions concern the visually absent isomorphism glyph `≅`, which is correctly present in the source registry:

| ID | Unified page | §-LANG page |
|---|---:|---:|
| `S26-T-00003109` | 300 | 259 |
| `S26-T-00003256` | 311 | 270 |
| `S26-T-00003311` | 315 | 274 |
| `S26-T-00003510` | 330 | 290 |
| `S26-D-00003916` | 360 | 322 |

**Generated reader projection:** a 635-page typeset edition plus unchanged original Volume IV visual plates (published source PDF pp. 369–373), totaling **640 pages**. QA found 5,000 unique sequential record headings, **5,000/5,000 statements reproduced after NFKC + whitespace normalization**, **5,000/5,000 evidence labels**, **5,000/5,000 hard-dependency lists**, no missing source mathematical Unicode glyphs, and zero out-of-page text spans in a full geometry scan. These tests establish rendered-text fidelity, not theorem validity. The generated PDF remains an **unreviewed editorial artifact**, not a replacement edition.

**Remaining obligations:** review complete record metadata before publishing the reconstructed JSONL, preserve further historical corrections, verify mathematics theorem-by-theorem, and perform full visual QA. Structural agreement is not proof correctness.

**Local output SHA-256 (draft artifacts, not released PDFs):**

- Complete 635-page source-derived reader: `3b4a30f5dd862f14e3274c73f66d394da888cdfa427309c9c2047d3ec53e5a1e`
- Reader plus five original visual-plate pages, 640 pages: `12029dc2b4a0d31246d4cb78e46e75906dead4a1921556495131edfb05c1f4d5`
