#!/usr/bin/env python3
"""Append verbatim original Volume-IV plate pages to source-derived reader PDF."""
import argparse
import fitz
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--reader', required=True, type=Path)
p.add_argument('--source', required=True, type=Path)
p.add_argument('--output', required=True, type=Path)
args = p.parse_args()
with fitz.open(args.reader) as d, fitz.open(args.source) as src:
    assert len(src) == 467
    plates = [i for i, page in enumerate(src) if page.get_images(full=True)]
    assert plates == [368, 369, 370, 371, 372], plates
    n = len(d)
    d.insert_pdf(src, from_page=plates[0], to_page=plates[-1], links=False, annots=False)
    m = d.metadata
    m['subject'] = 'Source-derived reader projection + unaltered original Volume IV visual plate pages 369-373; NOT certified theorem proofs'
    d.set_metadata(m)
    d.save(args.output, garbage=4, deflate=True)
    print('Reader pages:', n, 'append original plates:', len(plates), 'total pages:', len(d))
