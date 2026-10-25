"""Numerical and temporal-integrity tests; run python -m unittest discover -s tests."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/".deps"))
import tempfile
import unittest
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy import stats
from acmsi.core import (Config, zscore, fit_tail, filtered_probabilities,
                        entropy_weights, floor_weights, build_indices, dm_test)
from acmsi.validation import targets, walk_forward


class NumericalTests(unittest.TestCase):
    def test_weight_simplex_and_floor(self):
        x=pd.DataFrame([[0,1,100],[1,1,1]],columns=list("VPT"))
        w=floor_weights(x)
        np.testing.assert_allclose(w.sum(axis=1),1)
        self.assertTrue((w>=.05).all().all())

    def test_entropy_zero_and_missing(self):
        x=pd.DataFrame(np.zeros((12,3)))
        w=entropy_weights(x,5)
        self.assertTrue(w.iloc[:4].isna().all().all())
        np.testing.assert_allclose(w.iloc[4:],1/3)

    def test_zscore_does_not_use_future(self):
        x=pd.Series(np.arange(50,dtype=float))
        y=x.copy(); y.iloc[30:]=1e6
        pd.testing.assert_series_equal(zscore(x,10).iloc[:30],zscore(y,10).iloc[:30])

    def test_gpd_formula_and_finite_mean(self):
        rng=np.random.default_rng(4)
        x=stats.genpareto.rvs(.2,scale=.01,size=10000,random_state=rng)
        row=fit_tail(x,.90)
        self.assertEqual(row['status'],'ok')
        self.assertGreater(row['ES99'],row['VaR99'])
        q=(1-.99)/(row['n_exceed']/row['n'])
        expected=row['u']+row['beta']/row['xi']*(q**(-row['xi'])-1)
        self.assertAlmostEqual(row['VaR99'],expected)
        self.assertEqual(fit_tail(x[:252],.99)['status'],'insufficient_exceedances')
        self.assertTrue(np.isnan(fit_tail(x,.99)['VaR95']))

    def test_forward_filter_matches_prefix_and_chunk(self):
        model=GaussianHMM(n_components=2,covariance_type='full',init_params='')
        model.startprob_=np.array([.8,.2]); model.transmat_=np.array([[.95,.05],[.1,.9]])
        model.means_=np.array([[0.],[3.]]); model.covars_=np.array([[[1.]],[[1.]]])
        x=np.array([[0.],[1.],[3.],[-1.],[2.]])
        full=filtered_probabilities(model,x)
        np.testing.assert_allclose(full[:3],filtered_probabilities(model,x[:3]))
        np.testing.assert_allclose(full[3:],filtered_probabilities(model,x[3:],full[2]))
        np.testing.assert_allclose(full.sum(axis=1),1)
        for i in range(len(x)):
            np.testing.assert_allclose(full[i],model.predict_proba(x[:i+1])[-1],atol=1e-12)

    def test_forward_target_alignment(self):
        idx=pd.bdate_range('2020-01-01',periods=80)
        r=pd.DataFrame(np.random.default_rng(2).normal(0,.01,(80,3)),index=idx,columns=['AAPL','MSFT','SPY'])
        p=100*np.exp(r.cumsum())
        posterior=pd.DataFrame({'Prob_RiskRank0':.6,'Prob_RiskRank1':.4},index=idx)
        t=targets(r,p,posterior,30)
        self.assertAlmostEqual(t.future_vol.iloc[0],r.SPY.iloc[1:31].std()*np.sqrt(252))
        self.assertTrue(t.future_vol.iloc[-30:].isna().all())
        self.assertTrue(t.future_crisis.iloc[-30:].isna().all())
        posterior.iloc[:10,:]=np.nan
        t=targets(r,p,posterior,30)
        self.assertTrue(t.future_transition.iloc[:10].isna().all())

    def test_index_prefix_invariance(self):
        rng=np.random.default_rng(3)
        idx=pd.bdate_range('2015-01-01',periods=850)
        r=pd.DataFrame(rng.normal(0,.01,(850,3)),index=idx,columns=['AAPL','MSFT','SPY'])
        sigma=pd.DataFrame(rng.uniform(.01,.03,(850,3)),index=idx,columns=r.columns)
        tail=sigma*2+abs(r)
        p=pd.Series(rng.uniform(0,1,850),index=idx)
        cfg=Config(window=60,entropy_window=21)
        full=build_indices(r,sigma,p,p,tail,cfg)[1]
        prefix=build_indices(r.iloc[:700],sigma.iloc[:700],p.iloc[:700],p.iloc[:700],tail.iloc[:700],cfg)[1]
        pd.testing.assert_frame_equal(full.iloc[:700],prefix)

    def test_calibration_label_embargo(self):
        rng=np.random.default_rng(4)
        idx=pd.bdate_range('2015-01-01',periods=520)
        x=pd.Series(rng.normal(size=520),index=idx)
        variants=['Adaptive','Equal','PCA','Entropy','NoEVT','NoHMM','NoGARCH','Adaptive4']
        portfolio=pd.DataFrame({v:x*(1+i*.1) for i,v in enumerate(variants)})
        target=pd.DataFrame({'future_vol':rng.uniform(.1,.4,520),'current_vol':.2,
                             'future_crisis':rng.integers(0,2,520),
                             'future_transition':rng.integers(0,2,520)},index=idx)
        cfg=Config(initial_train=100,bootstrap=10)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory); (output/'tables').mkdir()
            walk_forward(portfolio,target,cfg,output)
            audit=pd.read_csv(output/'tables/main_calibration_audit.csv')
            self.assertTrue((pd.to_datetime(audit.latest_target_end)<pd.to_datetime(audit.test_start)).all())

    def test_dm_loss_direction(self):
        rng=np.random.default_rng(5)
        actual=rng.normal(size=600)
        result=dm_test(actual,actual+.1,actual+rng.normal(size=600),30)
        self.assertLess(result['dm'],0)
        self.assertLess(result['pvalue'],.05)


if __name__=='__main__':
    unittest.main()
