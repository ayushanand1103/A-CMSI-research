"""Controlled probability/multiplier ablations and weighting alternatives."""
import numpy as np
import pandas as pd
from acmsi.core import ASSETS,zscore,entropy_weights,floor_weights,build_indices


def deficit_weights(z,window):
    # Recompute entropy levels; normalized entropy weights do not retain their level.
    def deficit(x):
        a=np.abs(x)
        if a.sum()<1e-12:
            return 1.
        p=a[a>0]/a.sum()
        return max(0.,1+np.sum(p*np.log(p))/np.log(len(x)))
    d=z.rolling(window).apply(deficit,raw=True)
    out=d.div(d.sum(axis=1).replace(0,np.nan),axis=0)
    zero=d.notna().all(axis=1)&d.sum(axis=1).lt(1e-12)
    out.loc[zero,:]=1/z.shape[1]
    return out


def controlled(returns,sigma,panic,stress,tail,cfg):
    _,original,_,_=build_indices(returns,sigma,panic,stress,tail,cfg)
    v,t,p=zscore(sigma,cfg.window),zscore(tail,cfg.window),zscore(panic,cfg.window)
    asset_outputs=[]; weight_rows=[]; conditional={}
    for asset in ASSETS:
        z=pd.DataFrame(dict(V=v[asset],P=p,T=t[asset]))
        factors=pd.DataFrame(dict(V=1.3-.5*stress,P=.8+.3*stress,T=.9+.5*stress))
        no_p=z[["V","T"]]
        np_w=floor_weights(entropy_weights(no_p,cfg.entropy_window)*factors[["V","T"]],cfg.min_weight)
        d_w=floor_weights(deficit_weights(z,cfg.entropy_window),cfg.min_weight)
        # Original PCA is retained unchanged; the corrected-floor variant is separate.
        pca_w=pd.DataFrame(np.nan,index=z.index,columns=z.columns)
        for start in range(0,len(z),cfg.refit_every):
            history=z.iloc[:start].dropna()
            if len(history)<126:
                continue
            _,_,vh=np.linalg.svd(history-history.mean(),full_matrices=False)
            load=np.abs(vh[0]); load/=load.sum()
            pca_w.iloc[start:start+cfg.refit_every]=cfg.min_weight+(1-3*cfg.min_weight)*load
        asset_outputs.append(pd.DataFrame(dict(NoProbability=(np_w*no_p).sum(axis=1,min_count=2),
                                               EntropyDeficit=(d_w*z).sum(axis=1,min_count=3),
                                               PCAFloor=(pca_w*z).sum(axis=1,min_count=3))))
        for kind,w in (("NoProbability",np_w),("EntropyDeficit",d_w),("PCAFloor",pca_w)):
            complete=w.dropna()
            weight_rows.append(dict(asset=asset,variant=kind,n=len(complete),minimum=float(complete.min().min()),
                                    max_sum_error=float((complete.sum(axis=1)-1).abs().max()),
                                    nonnegative=bool((complete>=0).all().all()),
                                    floor_satisfied=bool((complete>=cfg.min_weight-1e-12).all().all())))
    revised=original.join(sum(asset_outputs)/len(ASSETS))
    # Average V/T components, common P, and stress are not calibrated composite weights.
    # This is an explicitly multivariate incremental-information regression diagnostic.
    avg_v=v.mean(axis=1,skipna=False); avg_t=t.mean(axis=1,skipna=False)
    for name,frame in {
        "ConditionalVT":pd.DataFrame(dict(V=avg_v,T=avg_t)),
        "ConditionalVTP":pd.DataFrame(dict(V=avg_v,T=avg_t,P=p)),
        "ConditionalVTStress":pd.DataFrame(dict(V=avg_v,T=avg_t,stress=stress)),
        "ConditionalVTPStress":pd.DataFrame(dict(V=avg_v,T=avg_t,P=p,stress=stress))}.items():
        revised[name]=frame.mean(axis=1,skipna=False)
        conditional[name]=frame
    # Entropy is the no-multiplier ablation; NoHMM removes P AND multipliers.
    return revised,pd.DataFrame(weight_rows),conditional
