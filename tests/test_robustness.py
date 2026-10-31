"""Additional scientific audit tests independent of experiment outcomes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/".deps"))
import unittest
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from acmsi.core import Config,entropy_weights,floor_weights
from acmsi.models import make_variance
from research_audit.indices import deficit_weights,controlled
from research_audit.statistics import block_indices,values,global_adjustment
from research_audit.calibration import calibrate
from research_audit.signatures import signature


class RobustnessTests(unittest.TestCase):
    def test_experiment_signature_tracks_inputs_and_config(self):
        from dataclasses import replace
        x=pd.DataFrame({'x':[1.,2.,3.]})
        source=Path(__file__)
        original=signature(Config(),[x],source)
        self.assertEqual(original,signature(Config(),[x.copy()],source))
        self.assertNotEqual(original,signature(replace(Config(),seed=43),[x],source))
        changed=x.copy(); changed.iloc[-1,0]=4
        self.assertNotEqual(original,signature(Config(),[changed],source))
    def test_deficit_and_direct_entropy_distinct(self):
        z=pd.DataFrame({'steady':np.ones(20),'spike':np.r_[np.zeros(19),1.]})
        direct=entropy_weights(z,20).iloc[-1]
        deficit=deficit_weights(z,20).iloc[-1]
        self.assertGreater(direct['steady'],direct['spike'])
        self.assertGreater(deficit['spike'],deficit['steady'])
        np.testing.assert_allclose(floor_weights(deficit_weights(z,20)).dropna().sum(axis=1),1)

    def test_deficit_prefix_invariance(self):
        z=pd.DataFrame(np.random.default_rng(1).normal(size=(100,3)))
        pd.testing.assert_frame_equal(deficit_weights(z,20).iloc[:70],deficit_weights(z.iloc[:70],20))

    def test_auc_and_metrics_with_ties(self):
        g=pd.DataFrame(dict(actual_vol=[.1,.2,.3,.4],forecast_vol=[.2,.2,.2,.3],
                            actual_crisis=[0,1,0,1],crisis_probability=[.2,.5,.5,.9]))
        m=values(g)
        self.assertAlmostEqual(m['auc'],roc_auc_score(g.actual_crisis,g.crisis_probability))
        self.assertAlmostEqual(m['precision'],2/3)
        self.assertAlmostEqual(m['recall'],1)

    def test_paired_blocks_preserve_order_within_block(self):
        ix=block_indices(100,draws=20,block=10,seed=42)
        for row in ix:
            np.testing.assert_array_equal(np.diff(row.reshape(-1,10),axis=1)%100,1)

    def test_volatility_prefix_invariance_fixed_training(self):
        rng=np.random.default_rng(3); x=rng.normal(0,.01,500)
        spec=('EGARCH','t')
        fit=make_variance(x[:350],spec).fit(disp='off',show_warning=False)
        short=make_variance(x[:425],spec).fix(fit.params).conditional_volatility
        full=make_variance(x,spec).fix(fit.params).conditional_volatility
        np.testing.assert_allclose(short,full[:425],atol=1e-12)

    def test_calibration_future_target_mutation(self):
        rng=np.random.default_rng(4); idx=pd.bdate_range('2015-01-01',periods=520)
        x=pd.DataFrame({'Adaptive':rng.normal(size=520)},index=idx)
        target=pd.DataFrame({'future_vol':rng.uniform(.1,.4,520),'current_vol':.2,
                             'future_crisis':rng.integers(0,2,520)},index=idx)
        cfg=Config(initial_train=100)
        a,_=calibrate(x,target,cfg)
        changed=target.copy(); changed.iloc[320:,changed.columns.get_loc('future_vol')]=100
        changed.iloc[320:,changed.columns.get_loc('future_crisis')]=1
        b,_=calibrate(x,changed,cfg)
        for column in ('forecast_vol','crisis_probability'):
            np.testing.assert_allclose(a.loc[a.Date<idx[350],column],b.loc[b.Date<idx[350],column])

    def test_global_holm_not_less_than_raw(self):
        a=pd.DataFrame({'pvalue':[.01,.04,.9]})
        out=global_adjustment([a])
        self.assertTrue((out.p_holm_global>=out.pvalue).all())


if __name__=='__main__':
    unittest.main()
