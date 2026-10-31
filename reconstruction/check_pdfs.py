#!/usr/bin/env python3
"""Cross-check recovered Synopsis JSONL with both published PDF reading surfaces.

Source text in PDFs is not a substitute for original typed data. This reports
extraction agreement and page pointers, not universal semantic identity.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path
import fitz

ID_RE = r'S26-[A-Z]-\d{8}'
MAIN_RE = re.compile(r'(?m)^\s*(' + ID_RE + r')\s+-\s+([^\n]+)')
LANG_RE = re.compile(r'(?m)^\s*§CLAIM\[(' + ID_RE + r')\|([A-Z])\|([AMHSPR])\|([^\]]+)\]([^\n]*)')
DEP_RE = re.compile(ID_RE)
FIELD_RE = re.compile(r'(?m)^\s*§([A-Z_]+)\s*:=\s*')
PDF_EXPECTED = {
    'unified': ('b0f3ba069c3ea03c53a7df6d6f315c49239a7cb08eed175ef63997344821878e', 467),
    'slang': ('456fe8352d25de698673eb68441ae29237d6a45dc5c684c1769f8b7763ce7946', 437),
}


def norm(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', s)).strip()


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def split_fields(segment):
    matches = list(FIELD_RE.finditer(segment))
    result = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(segment)
        block = segment[m.end():end]
        block = re.sub(r'(?m)^\s*Synopsis 2026\s+-\s+§-LANG s1 Translation.*$', '', block)
        block = re.sub(r'(?m)^\s*§PACK Synopsis_.*$', '', block)
        block = re.sub(r'(?m)^\s*(volume|canonical_range)\s*:=.*$', '', block)
        result[m.group(1)] = norm(block)
    return result


def run(registry, unified, slang, out):
    records = [json.loads(x) for x in registry.read_text('utf8').splitlines() if x]
    byid = {r['id']: r for r in records}
    pdfs, texts = {}, {}
    for label, path in [('unified', unified), ('slang', slang)]:
        doc = fitz.open(path)
        expected_hash, expected_pages = PDF_EXPECTED[label]
        digest = sha(path)
        pdfs[label] = {
            'filename': path.name, 'sha256': digest,
            'sha256_matches_manifest': digest == expected_hash,
            'pages': len(doc), 'pages_match_manifest': len(doc) == expected_pages,
            'a4_pages': sum(abs(p.rect.width - 595.276) < 2 and abs(p.rect.height - 841.89) < 2 for p in doc),
        }
        texts[label] = [p.get_text('text', sort=True) for p in doc]
        doc.close()
        if digest != expected_hash or pdfs[label]['pages'] != expected_pages:
            raise ValueError(label + ' source PDF identity mismatch')
    main = defaultdict(list)
    for pno, s in enumerate(texts['unified'], 1):
        for m in MAIN_RE.finditer(s):
            main[m.group(1)].append({'page': pno, 'title': norm(m.group(2))})
    slang_all = '\n'.join(texts['slang'])
    lang_m = list(LANG_RE.finditer(slang_all))
    slang_items = {}
    counts = Counter()
    mismatch = []
    ids = []
    for i, m in enumerate(lang_m):
        id, cls, status, chart = m.group(1, 2, 3, 4)
        ids.append(id)
        counts[status] += 1
        start = m.end()
        end = lang_m[i + 1].start() if i + 1 < len(lang_m) else len(slang_all)
        body = slang_all[start:end]
        pre_title = body.split('§FORM :=', 1)[0]
        title = norm(m.group(5) + ' ' + pre_title)
        fields = split_fields(body)
        r = byid[id]
        expected_dep = [d['id'] for d in r['dependencies'] if d['type'] == 'hard']
        actual_dep = DEP_RE.findall(fields.get('DEP_HARD', ''))
        field_eq = norm(fields.get('FORM', '')) == norm(r['statement'])
        item = {
            'id': id, 'status_pdf': status,
            'status_registry': r['evidence']['status'],
            'statement_nfkc_whitespace_exact': field_eq,
            'hard_dependencies_exact': actual_dep == expected_dep,
            'title_exact': title == norm(r['title'])
        }
        if (status != r['evidence']['status'] or cls != r['class'] or
            actual_dep != expected_dep or not field_eq or not item['title_exact']):
            mismatch.append({
                **item, 'registry_statement': r['statement'][:250],
                'pdf_form': fields.get('FORM', '')[:250],
                'registry_title': r['title'][:110], 'pdf_title': title[:110],
                'registry_deps': expected_dep[:8], 'pdf_deps': actual_dep[:8]
            })
        slang_items[id] = item
    offsets = []
    off = 0
    for s in texts['slang']:
        offsets.append((off, off + len(s)))
        off += len(s) + 1
    starts = [x[0] for x in offsets]
    crosswalk, title_bad, no_main = [], [], []
    for r in records:
        rid = r['id']
        candidates = main.get(rid, [])
        wanted = norm(r['title'])
        candidates_match = [x for x in candidates if wanted.startswith(x['title']) or x['title'].startswith(wanted)]
        canonical = candidates_match[-1] if candidates_match else (candidates[-1] if candidates else None)
        if not canonical:
            no_main.append(rid)
        elif not candidates_match:
            title_bad.append({'id': rid, 'actual': canonical['title'], 'expected': wanted})
        lm = lang_m[len(crosswalk)]
        page = bisect_right(starts, lm.start())
        crosswalk.append({
            'id': rid,
            'volume': '0' if len(crosswalk) < 1000 else ['I', 'II', 'III', 'IV'][(len(crosswalk) - 1000) // 1000],
            'status': r['evidence']['status'], 'title': r['title'],
            'unified_page': canonical['page'] if canonical else None,
            'slang_page': page,
            'statement_sha256': hashlib.sha256(r['statement'].encode('utf8')).hexdigest(),
            'source_pdf_field_status': slang_items[rid]
        })
    counts2 = {k: sum(bool(x[k]) for x in slang_items.values())
               for k in ('statement_nfkc_whitespace_exact', 'hard_dependencies_exact', 'title_exact')}
    summary = {
        'scope': 'PDF identity checks and source-to-rendered-text comparisons; not proof verification',
        'pdfs': pdfs, 'registry_records': len(records),
        'slang_claim_markers': len(lang_m),
        'slang_ids_in_registry_sequence': ids == [x['id'] for x in records],
        'slang_evidence_counts': dict(sorted(counts.items())),
        'slang_field_exact_matches': counts2,
        'slang_mismatch_count': len(mismatch),
        'unified_unique_canonical_ids': sum(bool(main.get(r['id'])) for r in records),
        'unified_title_mismatches': len(title_bad),
        'unified_missing_ids': no_main,
        'unified_duplicate_heading_occurrences': sum(max(0, len(x) - 1) for x in main.values()),
        'limitations': 'PDF text extraction can lose typographic mathematics, ligatures, fractions, tables, images and Unicode distinctions. Visual sampling and exact registry witness remain required.'
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / 'pdf_crosscheck.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    (out / 'pdf_text_mismatches_sample.json').write_text(json.dumps(mismatch[:80], indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    (out / 'pdf_heading_mismatches_sample.json').write_text(json.dumps(title_bad[:50], indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    with (out / 'page_crosswalk.jsonl').open('w', encoding='utf8') as f:
        for item in crosswalk:
            f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')
    return summary


def main():
    p = argparse.ArgumentParser()
    for a in ('registry', 'unified', 'slang', 'out'):
        p.add_argument('--' + a, type=Path, required=True)
    kw = vars(p.parse_args())
    print(json.dumps(run(**kw), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
