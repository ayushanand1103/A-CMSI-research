"""Original fixed calibration reproduced, with explicit common-date masks."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge,LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline


def calibrate(portfolio,target,cfg,mask=None,conditional=None):
    common=portfolio.notna().all(axis=1)
    if mask is not None:
        common &= mask.reindex(portfolio.index,fill_value=False)
    records=[]; audit=[]
    for start in range(cfg.initial_train,len(portfolio),cfg.refit_every):
        end=min(start+cfg.refit_every,len(portfolio))
        candidates=np.arange(cfg.initial_train,max(start-cfg.horizon,cfg.initial_train))
        train=candidates[common.iloc[candidates].to_numpy()&target.future_vol.iloc[candidates].notna().to_numpy()]
        test=np.arange(start,end); test=test[common.iloc[test].to_numpy()]
        if len(train)<126 or not len(test):
            continue
        audit.append(dict(test_start=portfolio.index[start],n_train=len(train),
                          latest_training_feature=portfolio.index[train[-1]],
                          latest_target_end=portfolio.index[train[-1]+cfg.horizon]))
        # This baseline is train-only and cannot use current/future label prevalence.
        constants={"TrainMean":float(target.future_vol.iloc[train].mean()),
                   "RealizedVolBaseline":None}
        for variant in list(portfolio)+list(constants):
            x=portfolio[[variant]] if variant in portfolio else None
            if conditional and variant in conditional:
                x=conditional[variant]
            if x is not None:
                regression=make_pipeline(StandardScaler(),Ridge(alpha=1.))
                regression.fit(x.iloc[train],np.log(target.future_vol.iloc[train].clip(lower=1e-8)))
                vol=np.exp(regression.predict(x.iloc[test]))
                y=target.future_crisis.iloc[train]
                if y.nunique()<2:
                    prob=np.full(len(test),float(y.mean()))
                else:
                    classifier=make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=300,random_state=cfg.seed))
                    classifier.fit(x.iloc[train],y)
                    prob=classifier.predict_proba(x.iloc[test])[:,1]
            else:
                vol=target.current_vol.iloc[test].to_numpy() if variant=="RealizedVolBaseline" else np.full(len(test),constants[variant])
                prob=np.full(len(test),float(target.future_crisis.iloc[train].mean()))
            for j,i in enumerate(test):
                records.append(dict(Date=portfolio.index[i],variant=variant,actual_vol=target.future_vol.iloc[i],
                                    forecast_vol=vol[j],actual_crisis=target.future_crisis.iloc[i],crisis_probability=prob[j]))
    result=pd.DataFrame(records)
    if result.empty:
        raise RuntimeError("No eligible forecasts")
    return result,pd.DataFrame(audit)
