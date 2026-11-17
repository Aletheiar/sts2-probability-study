"""Integration checks on saved research outputs, run after experiments."""
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest
from src.model import Deck,joint_forward,summarize

ROOT=Path(__file__).resolve().parents[1]


class DeliverableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'data/artifact_inventory.json').exists():
            raise unittest.SkipTest('Run python -m experiments.run_all for artifact checks')

    def test_exported_distributions_and_summary_match_integer_counts(self):
        raw=json.loads((ROOT/'data/simulation_counts.json').read_text(encoding='utf-8'))
        exact=json.loads((ROOT/'data/exact_results.json').read_text(encoding='utf-8'))
        configs=json.loads((ROOT/'data/configurations.json').read_text(encoding='utf-8'))
        with (ROOT/'data/summary.csv').open(encoding='utf-8-sig',newline='') as f:
            rows={r['id']:r for r in csv.DictReader(f)}
        self.assertEqual(set(raw),set(rows))
        self.assertEqual(len({tuple([*Deck(**r['deck']).counts,r['n'],r['h']]) for r in configs}),len(configs))
        self.assertEqual(len({r['seed'] for r in raw.values()}),len(configs))
        for cfg in configs:
            name=cfg['id'];sim=raw[name];m=sim['trials'];k=sim['successes']
            j=[Fraction(q) for q in exact[name]['joint']]
            self.assertEqual(sum(sim['success_counts']),k)
            self.assertEqual(sum(sim['overall_counts']),m)
            self.assertEqual(sum(batch[0] for batch in sim['batches']),m)
            self.assertEqual([sum(batch[x+1] for batch in sim['batches']) for x in range(cfg['h']+1)],sim['success_counts'])
            self.assertEqual(joint_forward(Deck(**cfg['deck']),cfg['n'],cfg['h']),j)
            theory=summarize(j)
            self.assertEqual(sum(theory['overall_pmf']),1)
            self.assertEqual(float(rows[name]['sim_p']),k/m)
            mean=sum(8*x*count for x,count in enumerate(sim['overall_counts']))/m
            self.assertAlmostEqual(float(rows[name]['sim_mean']),mean)
            for kind in ('c','e'):
                self.assertEqual(sum(sim[f'time_{kind}_counts']),m)
                self.assertTrue(all(a<=b for a,b in zip(sim[f'ordered_{kind}_counts'],sim[f'ordered_{kind}_counts'][1:])))

    def test_structural_polynomials_at_all_integer_parameters(self):
        structural=json.loads((ROOT/'data/structural_identities.json').read_text(encoding='utf-8'))
        for s in range(20):
            r=summarize(joint_forward(Deck(s=s,t=19-s),10,4))
            for key,coeffs in structural['coefficients'].items():
                self.assertEqual(r[key],sum(Fraction(q)*s**degree for degree,q in enumerate(coeffs)))

    def test_figure_pairs_are_vector_pdf_and_large_png(self):
        from PIL import Image
        catalog=json.loads((ROOT/'figures/catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(len(catalog['figures']),10)
        for item in catalog['figures']:
            pdf=(ROOT/'figures'/f'{item["file"]}.pdf').read_bytes()
            self.assertTrue(pdf.startswith(b'%PDF-'))
            self.assertFalse(b'/Subtype /Image' in pdf,item['file'])
            with Image.open(ROOT/'figures'/f'{item["file"]}.png') as im:
                self.assertGreater(im.width,2000)
                self.assertGreater(im.height,1000)

    def test_report_math_markup_and_time_distributions(self):
        text=(ROOT/'research_report.md').read_text(encoding='utf-8')
        self.assertFalse(any(ord(c)<32 and c not in '\r\n\t' for c in text))
        for command in (r'\operatorname{Var}',r'\sigma^2',r'\mu(S)',r'\sum_',r'\ge24'):
            self.assertIn(command,text)
        with (ROOT/'data/completion_pmf.csv').open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        totals={}
        for row in rows:
            key=row['id'],row['kind']
            totals[key]=totals.get(key,0)+float(row['theory'])
        self.assertEqual(len(totals),214)
        for total in totals.values():
            self.assertAlmostEqual(total,1)

    def test_artifact_hashes_and_original_source_provenance(self):
        inventory=json.loads((ROOT/'data/artifact_inventory.json').read_text(encoding='utf-8'))
        for name,expected in inventory.items():
            p=ROOT/name
            self.assertTrue(p.is_file(),name)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),expected['sha256'],name)
        manifest=json.loads((ROOT/'data/run_manifest.json').read_text(encoding='utf-8'))
        for name,expected in manifest['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)


if __name__=='__main__':
    unittest.main()
