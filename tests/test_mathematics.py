"""Independent finite-sample oracles, rather than tests that copy the formulas."""
import itertools
import unittest
from collections import Counter
from fractions import Fraction

from src.model import Deck, availability, completion, ordered_probability, joint_forward, joint_reverse, summarize


def exhaustive(deck, n, h):
    cards = list('A'*deck.a+'B'*deck.b+'C'*deck.c+'D'*deck.d+'T'*deck.t+'S'*deck.s)
    joint = Counter()
    accessible = ordered = total = 0
    for perm in itertools.permutations(range(len(cards))):
        labels = [cards[i] for i in perm]
        first = labels[:n]
        ok = all(g in first for g in 'ABC')
        if ok:
            joint[sum(z in 'ABCS' for z in labels[n:n+h])] += 1
        accessible += ok
        seen = set()
        found = False
        for z in first:
            if z == 'C' and 'A' in seen and 'B' in seen:
                found = True
            seen.add(z)
        ordered += found
        total += 1
    return [Fraction(joint[x], total) for x in range(h+1)], Fraction(accessible,total), Fraction(ordered,total)


class MathTests(unittest.TestCase):
    def test_small_decks_against_all_labeled_permutations(self):
        for d,n,h in [(Deck(1,1,1,0,1,1),3,2), (Deck(2,1,1,0,1,1),4,2), (Deck(1,1,2,0,1,1),3,2)]:
            j,p,o=exhaustive(d,n,h)
            self.assertEqual(joint_forward(d,n,h),j)
            self.assertEqual(joint_reverse(d,n,h),j)
            self.assertEqual(availability(d,n,'C'),p)
            self.assertEqual(ordered_probability(d,n,'C'),o)

    def test_baseline_original_numbers_are_regressions_only(self):
        d=Deck()
        j=joint_forward(d,10,4)
        self.assertEqual(j,joint_reverse(d,10,4))
        r=summarize(j)
        self.assertEqual(r['p'],Fraction(25,253))
        self.assertEqual(r['conditional_mean'],Fraction(592,35))
        self.assertEqual(r['mean'],Fraction(2960,1771))
        self.assertEqual(r['variance'],r['within']+r['activation'])

    def test_distributions_and_reverse_identity_over_parameter_changes(self):
        for d in [Deck(),Deck(2,2,3,1,4,7),Deck(1,1,1,0,0,5),Deck(0,1,2,1,4,5),Deck(1,1,2,1,0,0)]:
            for n in [0,min(3,d.N),d.N]:
                h=min(2,d.N-n)
                j=joint_forward(d,n,h)
                self.assertEqual(j,joint_reverse(d,n,h))
                self.assertEqual(sum(j),availability(d,n,'C'))
                r=summarize(j)
                self.assertEqual(sum(r['overall_pmf']),1)
                self.assertTrue(all(q>=0 for q in j))
                if r['p']:
                    self.assertEqual(sum(r['conditional_pmf']),1)

    def test_completion_moments_and_order_at_full_deck(self):
        d=Deck()
        r=completion(d,'E')
        self.assertEqual(sum(r['pmf']),1)
        self.assertEqual(r['mean'],Fraction(205,12))
        self.assertEqual(r['mean'],sum(1-availability(d,n,'E') for n in range(d.N)))
        self.assertEqual(ordered_probability(d,24,'E'),Fraction(3,5))
        self.assertEqual(ordered_probability(d,24,'C'),Fraction(1,2))

    def test_invalid_inputs_and_impossible_events(self):
        for params in [dict(a=-1),dict(c=1.5)]:
            with self.assertRaises((TypeError,ValueError)):
                Deck(**params)
        for n,h in [(-1,1),(25,0),(22,4)]:
            with self.assertRaises(ValueError):
                joint_forward(Deck(),n,h)
        r=summarize(joint_forward(Deck(a=0),10,4))
        self.assertIsNone(r['conditional_mean'])
        self.assertEqual(r['mean'],0)
        with self.assertRaises(ValueError):
            completion(Deck(a=0),'C')

    def test_empty_setup_full_second_sample_and_zero_variance(self):
        d=Deck(1,1,1,0,0,0)
        self.assertEqual(joint_forward(d,0,3),joint_reverse(d,0,3))
        r=summarize(joint_forward(d,3,0))
        self.assertEqual(r['p'],1)
        self.assertEqual(r['variance'],0)
        self.assertEqual(r['conditional_variance'],0)
        self.assertEqual(r['q90'],0)

    def test_second_moment_survival_identity_and_singleton_order_formula(self):
        from src.model import choose
        d=Deck()
        for kind,k in [('C',2),('E',3)]:
            r=completion(d,kind)
            second=sum((2*n+1)*(1-availability(d,n,kind)) for n in range(24))
            self.assertEqual(second,r['variance']+r['mean']**2)
            for n in range(25):
                formula=sum((Fraction(2*(j-1),24*23)*(1-Fraction(choose(22-(n-j),k),choose(22,k))) for j in range(2,n)),Fraction(0))
                self.assertEqual(formula,ordered_probability(d,n,kind))


if __name__=='__main__':
    unittest.main()
