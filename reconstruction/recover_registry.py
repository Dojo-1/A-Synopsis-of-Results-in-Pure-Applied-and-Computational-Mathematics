#!/usr/bin/env python3
"""Recover and audit Synopsis JSONL from an exact §-LANG source witness.

Standard-library only, fail closed. The recovered serialized registry is
byte-identical when its global SHA-256 matches the declared source digest.
Graph checks do NOT certify mathematical theorem truth.
"""
import argparse
import base64
from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path
import re

SHA_RE = re.compile(r'^  source_sha256 = "([a-f0-9]{64})"\s*$', re.M)
B64_RE = re.compile(r'^  source_b64 = "([A-Za-z0-9+/=]+)"\s*$', re.M)
GLOBAL_RE = re.compile(r'^  source_registry_sha256 = "([a-f0-9]{64})"\s*$', re.M)
ENTRY_RE = re.compile(r'^§\|LANG\|SYNOPSIS_ENTRY\{$', re.M)
ID_RE = re.compile(r'^S26-([A-Z])-([0-9]{8})$)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(records, expected_hash, source_hash, witnesses):
    ids = [r['id'] for r in records]
    assert len(ids) == 5000 and len(set(ids)) == 5000
    assert [int(ID_RE.fullmatch(x).group(2)) for x in ids] == list(range(1, 5001))
    for r in records:
        m = ID_RE.fullmatch(r['id'])
        assert m and m.group(1) == r['class'], r['id']
        assert isinstance(r['statement'], str) and r['statement'].strip(), r['id']
        assert isinstance(r.get('title'), str) and r['title'].strip(), r['id']
    idset = set(ids)
    hard = []
    unknown_deps = []
    dangling = []
    parents = {r['id']: r['id'] for r in records}

    def find(x):
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parents[a] = b

    incoming = Counter()
    successors = defaultdict(list)
    for r in records:
        for dep in r['dependencies']:
            target, t = dep['id'], dep['type']
            if target not in idset:
                dangling.append((r['id'], target, t))
            if t == 'hard':
                hard.append((target, r['id']))
                incoming[r['id']] += 1
                successors[target].append(r['id'])
                if target in idset:
                    union(r['id'], target)
            elif t not in {'soft', 'hard'}:
                unknown_deps.append((r['id'], target, t))
    assert not dangling, dangling[:5]
    roots = [r['id'] for r in records if incoming[r['id']] == 0]
    q = deque(roots)
    indeg = incoming.copy()
    visited = 0
    while q:
        u = q.popleft()
        visited += 1
        for v in successors[u]:
            indeg[v] -= 1
            if not indeg[v]:
                q.append(v)
    cyclic = visited != len(records)
    components = len({find(r['id']) for r in records})
    evidence = Counter(r['evidence']['status'] for r in records)
    a_empty = Counter()
    for n, r in enumerate(records, 1):
        if r['evidence']['status'] == 'A' and not r['assumptions']:
            vol = '0' if n <= 1000 else ['I', 'II', 'III', 'IV'][(n - 1001) // 1000]
            a_empty[vol] += 1
    result = {
        'authority': 'byte-exact source JSONL recovery; structural audit only; NOT mathematical theorem verification',
        'source_slang_sha256': source_hash,
        'expected_registry_sha256': expected_hash,
        'recovered_registry_sha256': expected_hash,
        'registry_records': len(records),
        'base64_witnesses_verified': witnesses,
        'ids_unique_and_sequential': True,
        'hard_dependencies_count': len(hard),
        'dangling_dependencies': len(dangling),
        'unknown_dependency_types': unknown_deps,
        'hard_graph_roots': roots,
        'hard_graph_weak_components': components,
        'hard_graph_acyclic': not cyclic,
        'evidence_counts': dict(sorted(evidence.items())),
        'a_records_without_explicit_assumptions_by_volume': dict(sorted(a_empty.items())),
        'conditional_review': 'Counts and topology certify this registry snapshot only; A/M/S/H do not become P.'
    }
    assert len(hard) == 6924, len(hard)
    assert roots == ['S26-N-00000001'], roots
    assert components == 1 and not cyclic
    assert evidence == {'A': 2268, 'M': 2364, 'S': 365, 'H': 3}
    return result


def recover(lang: Path, output: Path):
    source = lang.read_bytes()
    text = source.decode('utf-8')
    expected = GLOBAL_RE.search(text)
    if not expected:
        raise ValueError('Source registry SHA-256 header absent')
    expected = expected.group(1)
    blobs = B64_RE.findall(text)
    line_hashes = SHA_RE.findall(text)
    entry_headers = ENTRY_RE.findall(text)
    if (len(blobs), len(line_hashes), len(entry_headers)) != (5000, 5000, 5000):
        raise ValueError('Witness/header count discrepancy')
    lines = []
    for n, (b64, digest) in enumerate(zip(blobs, line_hashes), 1):
        decoded = base64.b64decode(b64, validate=True)
        if b'\n' in decoded or b'\r' in decoded:
            raise ValueError(f'Embedded newline in witness {n}')
        if sha(decoded) != digest:
            raise ValueError(f'Witness SHA mismatch at {n}')
        lines.append(decoded)
    raw = b'\n'.join(lines) + b'\n'
    if sha(raw) != expected:
        raise ValueError('Global registry digest mismatch; no output written')
    records = [json.loads(line) for line in lines]
    result = audit(records, expected, sha(source), len(lines))
    output.mkdir(parents=True, exist_ok=True)
    registry_path = output / 'REGISTRY_00000001_00005000_REVIEWED.jsonl'
    report_path = output / 'SOURCE_RECOVERY_AUDIT.json'
    registry_path.write_bytes(raw)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return result, registry_path, report_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result, registry, report = recover(args.lang, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print('Registry: ', registry)
    print('Audit: ', report)


if __name__ == '__main__':
    main()
