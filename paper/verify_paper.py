"""Read-only checks for either the published manuscript or a fresh TeX build."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import pymupdf

PAPER = Path(__file__).resolve().parent


def verify(pdf, log=None, private_terms=()):
    with pymupdf.open(pdf) as doc:
        assert 6 <= len(doc) <= 20, 'Unexpected manuscript page count'
        text = '\n'.join(page.get_text() for page in doc)
        assert '参考文献' in text and 'AI' in text
        assert all(f'[{number}]' in text for number in range(1, 8)), 'Missing reference entries'
        assert not re.search(r'\[\s*\?\s*\]', text), 'Unresolved citation marker'
        assert '19,365' in text and '98,648' in text, 'Table 5 lost conditional sample sizes'
        normalized = re.sub(r'\s+', '', text)
        assert '概率公式的构建由作者负责' in normalized, 'Latest disclosure is missing'
        assert not re.search(r'(?<!\d)\d{12}(?!\d)', text), 'Possible student identifier'
        assert doc.metadata.get('author', '') in ('', 'Anonymous', '匿名作者')
        assert doc.embfile_count() == 0, 'Unreviewed embedded file'
        surfaces = [text, json.dumps(doc.metadata, ensure_ascii=False), doc.get_xml_metadata()]
        for term in private_terms:
            assert not any(term in value for value in surfaces), 'Private term found in PDF'
        fonts = {font[0] for page in doc for font in page.get_fonts()}
        assert all(doc.extract_font(xref)[3] for xref in fonts), 'Unembedded font'
        for page in doc:
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    for span in line['spans']:
                        box = pymupdf.Rect(span['bbox'])
                        assert box.x0 >= -1 and box.y0 >= -1
                        assert box.x1 <= page.rect.width + 1 and box.y1 <= page.rect.height + 1
        result = {'pages': len(doc), 'table5_sample_sizes_present': True,
                  'latest_disclosure_present': True, 'embedded_files': 0,
                  'all_fonts_embedded': True, 'private_term_matches': 0,
                  'sha256': hashlib.sha256(Path(pdf).read_bytes()).hexdigest()}
    if log:
        message = Path(log).read_text(encoding='utf-8', errors='replace')
        errors = re.findall('Overfull \\\\[hv]box[^\\n]*|Undefined control sequence|Missing character:[^\\n]*', message)
        assert not errors, errors
        lower = message.lower()
        assert 'undefined references' not in lower and 'undefined citations' not in lower
        assert not re.search(r'Warning:.*(?:Citation|Reference).*undefined', message)
        assert "Empty `thebibliography'" not in message
        result['compile_errors'] = 0
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, default=PAPER / 'manuscript.pdf')
    parser.add_argument('--log', type=Path)
    parser.add_argument('--private-terms-file', type=Path,
                        help='Optional local JSON string array; do not commit private terms.')
    args = parser.parse_args()
    terms = json.loads(args.private_terms_file.read_text(encoding='utf-8')) if args.private_terms_file else []
    print(json.dumps(verify(args.pdf, args.log, terms), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
