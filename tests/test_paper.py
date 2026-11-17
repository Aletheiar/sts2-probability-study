"""Regression checks for the current manuscript's reported conditional sample sizes."""
from pathlib import Path
import json
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PaperTests(unittest.TestCase):
    def test_validation_table_keeps_effective_conditional_sample_sizes(self):
        table = (ROOT / 'paper/generated/validation_table.tex').read_text(encoding='utf-8')
        self.assertIn('条件样本量', table)
        main = json.loads((ROOT / 'data/simulation_counts.json').read_text(encoding='utf-8'))['baseline']
        repeat = json.loads((ROOT / 'data/baseline_refinement.json').read_text(encoding='utf-8'))['raw']
        rows = [line.split('&') for line in table.splitlines()
                if line.strip().startswith(r'$\mu$')]
        self.assertEqual(len(rows), 2)
        for row, raw in zip(rows, (main, repeat)):
            self.assertEqual(len(row), 6)
            self.assertEqual(int(row[2].strip().replace(',', '')), raw['successes'])
            self.assertEqual(int(row[1].strip().replace(',', '')), raw['trials'])

    def test_tex_has_anonymous_authorship(self):
        text = (ROOT / 'paper/main.tex').read_text(encoding='utf-8')
        self.assertIn('pdfauthor={Anonymous}', text)
        self.assertIn('匿名作者', text)
        self.assertNotRegex(text, r'(?<!\d)\d{12}(?!\d)')

    def test_verifier_rejects_compiler_diagnostics(self):
        try:
            from paper.verify_paper import verify
        except ImportError:
            self.skipTest('Install requirements-paper.txt for PDF verification')
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'main.log'
            for warning in ('Package natbib Warning: There were undefined citations.',
                            r'Overfull \hbox (1.0pt too wide) detected at line 1'):
                with self.subTest(warning=warning):
                    log.write_text(warning + '\n', encoding='utf-8')
                    with self.assertRaises(AssertionError):
                        verify(ROOT / 'paper/manuscript.pdf', log)


if __name__ == '__main__':
    unittest.main()
