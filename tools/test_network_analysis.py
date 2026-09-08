"""Behaviour checks for leakage, calendar gaps and a known synthetic lag signal."""
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from network_analysis import analyse_pair, design_frame, finalize, weekly_returns, validate_policy

P = json.loads((Path(__file__).resolve().parent.parent/'data/causal/policy.json').read_text(encoding='utf-8'))


class AnalysisChecks(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(841)
        idx = pd.date_range('2000-01-07', periods=500, freq='W-FRI')
        self.x = pd.Series(rng.normal(size=500), index=idx)
        self.m = pd.Series(rng.normal(size=500), index=idx)
        self.y = 1.8*self.x.shift(1) + .3*self.m.shift(1) + pd.Series(rng.normal(0,.35,500), index=idx)

    def test_detect_known_direction_not_reverse(self):
        forward = analyse_pair(self.x,self.y,self.m,P)
        backward = analyse_pair(self.y,self.x,self.m,P)
        finalize([forward,backward],P)
        self.assertEqual(forward['decision'],'candidate')
        self.assertNotEqual(backward['decision'],'candidate')
        self.assertGreater(forward['effect'],1)

    def test_future_data_do_not_change_training_test(self):
        a=analyse_pair(self.x,self.y,self.m,P)
        future=self.y.copy();future.loc[future.index>pd.Timestamp(a['train_end'])]*=-7
        b=analyse_pair(self.x,future,self.m,P)
        self.assertAlmostEqual(a['p_value'],b['p_value'])
        self.assertAlmostEqual(a['effect'],b['effect'])
        self.assertNotAlmostEqual(a['rmse_gain'],b['rmse_gain'])
        for fold in b['folds']:
            self.assertLess(fold['train_end'],fold['start'])

    def test_missing_week_not_compressed(self):
        missing=self.x.index[25]
        x=self.x.drop(missing)
        frame=design_frame(x,self.y,self.m,2)
        self.assertNotIn(self.x.index[26],frame.index)
        self.assertNotIn(self.x.index[27],frame.index)

    def test_partial_week_excluded(self):
        idx=pd.date_range('2026-08-28',periods=12,freq='D')
        prices=pd.Series(np.arange(12)+100,index=idx)
        r=weekly_returns(prices,'2026-09-08',P)
        self.assertLessEqual(r.index.max(),pd.Timestamp('2026-09-04'))

    def test_small_sample_stays_unscored(self):
        r=analyse_pair(self.x.iloc[:30],self.y.iloc[:30],self.m.iloc[:30],P)
        finalize([r],P)
        self.assertEqual(r['decision'],'insufficient');self.assertIsNone(r['q_value'])

    def test_bad_policy_rejected(self):
        with self.assertRaises(ValueError): validate_policy({**P,'lags':0})


if __name__=='__main__': unittest.main()
