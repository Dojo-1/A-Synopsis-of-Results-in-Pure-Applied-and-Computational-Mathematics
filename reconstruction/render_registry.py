#!/usr/bin/env python3
"""Generate a readable PDF projection from the byte-exact reviewed registry.

Does not assert theorem validity. Source JSONL remains the authority for all fields,
including details not included in the reader projection. Never overwrite v1.1 PDFs.
"""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, PageBreak, Flowable, HRFlowable

FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
font = FONT_DIR / 'DejaVuSans.ttf'
bold = FONT_DIR / 'DejaVuSans-Bold.ttf'
if not font.exists():
    raise FileNotFoundError('Required TTF not available; configure a Unicode math-capable TTF instead')
pdfmetrics.registerFont(TTFont('DejaVuReader', str(font)))
pdfmetrics.registerFont(TTFont('DejaVuReaderBold', str(bold)))
pdfmetrics.registerFontFamily('DejaVuReader', normal='DejaVuReader', bold='DejaVuReaderBold')
NAVY = colors.HexColor('#19364e')
SLATE = colors.HexColor('#5c6d7c')
MUTED = colors.HexColor('#a7b1b9')


def st(name, size, leading=None, bold=False, color=colors.black, spaceAfter=4, alignment=TA_LEFT):
    return ParagraphStyle(name, fontName='DejaVuReaderBold' if bold else 'DejaVuReader',
                          fontSize=size, leading=leading or size * 1.44,
                          textColor=color, spaceAfter=spaceAfter, alignment=alignment,
                          allowWidows=0, allowOrphans=0)


ST = {
    'cover': st('cover', 18, 26, True, NAVY, 18),
    'subtitle': st('subtitle', 11, 18, False, SLATE, 13),
    'body': st('body', 9.2, 13.6, False, colors.HexColor('#232f35'), 7),
    'section': st('section', 14, 21, True, NAVY, 10),
    'heading': st('heading', 9.6, 14.3, True, NAVY, 5),
    'meta': st('meta', 7.9, 11.5, False, SLATE, 5),
    'note': st('note', 8.3, 12.1, False, SLATE, 6),
}
VOLUMES = [
    ('0', 'Foundations, Language, Registry and Epistemic Protocol'),
    ('I', 'Number, Algebra and Discrete Structure'),
    ('II', 'Analysis'),
    ('III', 'Geometry and Topology'),
    ('IV', 'p-adic Hypercomplex Hyperdimensional Continuum'),
]


class Book(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if getattr(flowable, '_volume_bookmark', None):
            name, title = flowable._volume_bookmark
            self.canv.bookmarkPage(name)
            self.canv.addOutlineEntry(title, name, level=0)


def par(s, which):
    s = escape(str(s)).replace('\n', ' ')
    return Paragraph(s, ST[which])


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(MUTED)
    canvas.setLineWidth(.3)
    canvas.line(21 * mm, 18 * mm, width - 21 * mm, 18 * mm)
    canvas.setFillColor(SLATE)
    canvas.setFont('DejaVuReader', 7.0)
    canvas.drawString(21 * mm, 13.8 * mm,
                      'RECONSTRUCTED READER PROJECTION · SOURCE JSONL IS AUTHORITATIVE')
    canvas.drawRightString(width - 21 * mm, 13.8 * mm, str(doc.page))
    canvas.restoreState()


def build(registry: Path, out: Path, ids=None):
    data = registry.read_bytes()
    records = [json.loads(x) for x in data.splitlines() if x]
    assert len(records) == 5000
    all_ids = {r['id'] for r in records}
    if ids is not None:
        chosen = set(ids)
        assert chosen <= all_ids, chosen - all_ids
        records = [r for r in records if r['id'] in chosen]
    doc = Book(str(out), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
               topMargin=24 * mm, bottomMargin=22 * mm,
               title='A Synopsis of Results in Pure, Applied and Computational Mathematics | reconstructed reader projection',
               author='Jesús Vilela Jato',
               subject='Source-derived review edition, mathematical claim statuses preserved')
    story = [
        Spacer(1, 23 * mm),
        par('A Synopsis of Results in Pure, Applied and Computational Mathematics', 'cover'),
        par('Source-preserving reader projection · 2026 · Reconstruction pilot' if ids is not None
            else 'Source-preserving reader projection · 2026 · Complete records', 'subtitle'),
        HRFlowable(width='100%', thickness=.6, color=MUTED),
        Spacer(1, 10 * mm),
        par('This is a new typesetting of canonical records recovered from the exact v1.1 §-LANG source witness. It is not the original PDF, not a proof audit, and not a claim that the statements have been independently established.', 'body'),
        par('Record identifiers, statements and evidence classes come from the byte-for-byte recovered JSONL registry. The full source JSONL preserves provenance, correction history, relations and other fields that may be summarized or omitted here.', 'body'),
        par('Registry SHA-256: ' + hashlib.sha256(data).hexdigest(), 'meta'),
        par('Evidence: A (assumed/accepted under scope) · M (bounded measurement) · H (hypothesis) · S (semantic/architectural) · P (independently proved at precise scope, none in this edition).', 'note'),
        par('Glyph correction: this PDF embeds a Unicode mathematical font and keeps ≅ where present in the exact source, repairing the five isomorphism glyph omissions observed in the 2026 v1.1 PDFs.', 'note'),
        PageBreak(),
    ]
    last_vol = None
    for r in records:
        n = int(r['id'].split('-')[-1])
        vol = '0' if n <= 1000 else ['I', 'II', 'III', 'IV'][(n - 1001) // 1000]
        if vol != last_vol:
            heading = par('VOLUME ' + vol + ' · ' + dict(VOLUMES)[vol], 'section')
            heading._volume_bookmark = ('volume_' + vol, 'Volume ' + vol)
            if last_vol is not None:
                story.append(PageBreak())
            story.extend([heading, HRFlowable(width='100%', thickness=.45, color=MUTED), Spacer(1, 5 * mm)])
            last_vol = vol
        stat = r['evidence']['status']
        headline = f'{r["id"]}   |   {r["title"]}'
        comps = [par(headline, 'heading'), par(r['statement'], 'body')]
        hard = [x['id'] for x in r['dependencies'] if x['type'] == 'hard']
        soft = [x['id'] for x in r['dependencies'] if x['type'] == 'soft']
        elems = [f'Evidence: {stat}']
        if hard:
            elems.append('Hard: ' + ', '.join(hard))
        if soft:
            elems.append('Soft: ' + ', '.join(soft))
        comps.append(par(' · '.join(elems), 'meta'))
        assumptions = r.get('assumptions', [])
        if assumptions:
            comps.append(par('Assumptions: ' + ' | '.join(assumptions), 'note'))
        correction = r.get('correction_history') or []
        if any('Peer-review' in str(x.get('change', '')) for x in correction):
            comps.append(par('Correction on record: ' + ' | '.join(
                x.get('change', '') for x in correction if 'Peer-review' in x.get('change', '')), 'note'))
        comps.append(Spacer(1, 2.5 * mm))
        story.append(KeepTogether(comps))
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return len(records)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--pilot', action='store_true')
    args = p.parse_args()
    ids = None
    if args.pilot:
        selected = [1, 9, 500, 1000, 1001, 1150, 2000, 2001, 2158, 2262,
                    3000, 3001, 3053, 3109, 3256, 3311, 3510, 3916, 4000,
                    4001, 4062, 4341, 4999, 5000]
        ids = {f'S26-{next(r["class"] for r in (json.loads(x) for x in args.registry.read_text().splitlines()) if int(r["id"].split("-")[-1]) == n)}-{n:08d}' for n in selected}
    n = build(args.registry, args.output, ids)
    print(f'Wrote {n} record projections to {args.output}')


if __name__ == '__main__':
    main()
