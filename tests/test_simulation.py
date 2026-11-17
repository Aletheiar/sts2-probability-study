import unittest
import numpy as np
from src.simulation import simulate, wilson, empirical_summary


class SimulationTests(unittest.TestCase):
    def test_permutation_extremes_and_reproducibility(self):
        # Setup must be exactly A/B/C in a three-card deck; payoff phase empty.
        r=simulate((1,1,1,0,0,0),3,0,100,99,static=True)
        self.assertEqual(r['success_counts'],[100])
        self.assertEqual(sum(r['time_c_counts']),100)
        self.assertEqual(r['time_c_counts'][3],100)
        r1=simulate((1,1,2,1,9,10),10,4,1000,123)
        r2=simulate((1,1,2,1,9,10),10,4,1000,123)
        self.assertEqual(r1,r2)
        self.assertEqual(sum(r1['overall_counts']),1000)
        self.assertEqual(sum(r1['success_counts']),r1['successes'])

    def test_missing_core_cannot_start(self):
        r=simulate((0,1,2,1,9,10),10,4,100,6)
        self.assertEqual(r['successes'],0)
        self.assertIsNone(empirical_summary(r)['conditional_mean'])

    def test_intervals_and_moments_on_hand_computed_sample(self):
        r=dict(trials=4,successes=3,success_counts=[1,1,1],overall_counts=[2,1,1])
        s=empirical_summary(r)
        self.assertEqual(s['mean'],6)
        self.assertAlmostEqual(s['variance'],176/3)
        self.assertEqual(s['conditional_mean'],8)
        self.assertEqual(s['conditional_variance'],64)
        self.assertEqual(wilson(0,100)[0],0)
        self.assertEqual(wilson(100,100)[1],1)
        self.assertGreater(s['mean_se'],0)


if __name__=='__main__':
    unittest.main()
