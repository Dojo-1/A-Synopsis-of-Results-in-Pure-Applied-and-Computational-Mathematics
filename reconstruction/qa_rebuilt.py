#!/usr/bin/env python3
"""Mechanical QA for a source-derived reader edition; does not audit theorem truth."""
import argparse, hashlib, json, re, unicodedata
from pathlib import Path
import fitz

ID = re.compile(r'(?m)^\s*(S26-[A-Z]-\d{8})\s*\|\s*')
REF = re.compile(r'S26-[A-Z]-\d{8}')


def norm(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', s)).strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--registry', required=True, type=Path)
    p.add_argument('--reader', required=True, type=Path)
    p.add_argument('--report', required=True, type=Path)
    a = p.parse_args()
    records = [json.loads(x) for x in a.registry.read_text(encoding='utf8').splitlines() if x]
    assert len(records) == 5000
    d = fitz.open(a.reader)
    texts, images, out_of_bounds = [], [], []
    for i, page in enumerate(d, 1):
        texts.append(page.get_text('text', sort=True))
        if page.get_images(full=True):
            images.append(i)
        for block in page.get_text('dict').get('blocks', []):
            for line in block.get('lines', []):
                for span in line.get('spans', []):
                    x0, y0, x1, y1 = span['bbox']
                    if x0 < -.1 or y0 < -.1 or x1 > page.rect.width + .1 or y1 > page.rect.height + .1:
                        out_of_bounds.append({'page': i, 'bbox': span['bbox'], 'text': span.get('text', '')[:80]})
    joined = '\n'.join(texts)
    heads = list(ID.finditer(joined))
    exact_sequence = [m.group(1) for m in heads] == [r['id'] for r in records]
    statement_fail, status_fail, dep_fail = [], [], []
    if len(heads) == 5000:
        for i, r in enumerate(records):
            body = joined[heads[i].end():heads[i + 1].start() if i + 1 < len(heads) else len(joined)]
            if norm(r['statement']) not in norm(body):
                statement_fail.append(r['id'])
            if not re.search(r'(?m)^\s*Evidence:\s*' + re.escape(r['evidence']['status']) + r'\b', body):
                status_fail.append(r['id'])
            expected = [x['id'] for x in r['dependencies'] if x['type'] == 'hard']
            m = re.search(r'Hard:\s*(.*?)(?=\n\s*(?:Assumptions:|Correction on record:|S26-[A-Z]-\d{8}\s*\|)|\Z)', body, re.S)
            actual = REF.findall(m.group(1)) if m else []
            if expected != actual:
                dep_fail.append(r['id'])
    source_chars = set(''.join(r['statement'] for r in records))
    observed_chars = set(joined)
    missing = sorted(c for c in source_chars if ord(c) > 127 and c not in observed_chars)
    original_glyph_count = sum(r['statement'].count('≅') for r in records)
    output_glyph_count = joined.count('≅')
    result = {
        'scope': 'rendered-text and page-geometry QA; NOT mathematical proof verification',
        'registry_sha256': hashlib.sha256(a.registry.read_bytes()).hexdigest(),
        'reader_sha256': hashlib.sha256(a.reader.read_bytes()).hexdigest(),
        'pages': len(d),
        'record_heading_count': len(heads),
        'exact_canonical_order': exact_sequence,
        'statement_matches': 5000 - len(statement_fail),
        'statement_mismatch_ids': statement_fail,
        'evidence_status_matches': 5000 - len(status_fail),
        'evidence_status_mismatch_ids': status_fail,
        'hard_dependency_list_matches': 5000 - len(dep_fail),
        'hard_dependency_mismatch_ids': dep_fail,
        'source_statement_isomorphism_glyphs': original_glyph_count,
        'extracted_pdf_isomorphism_glyphs_including_cover': output_glyph_count,
        'missing_source_unicode_codepoints': [f'U+{ord(c):04X}' for c in missing],
        'out_of_page_text_spans': out_of_bounds,
        'embedded_image_pages': images,
    }
    passed = (exact_sequence and len(heads) == 5000 and not statement_fail and
              not status_fail and not dep_fail and not missing and not out_of_bounds)
    result['mechanical_pass'] = passed
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
