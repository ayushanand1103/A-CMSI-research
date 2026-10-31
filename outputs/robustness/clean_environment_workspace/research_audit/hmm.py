"""Chronological state-count experiments with per-restart diagnostics."""
import logging
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score
from scipy.optimize import linear_sum_assignment
from acmsi.core import features,filtered_probabilities,state_mapping
from .signatures import signature

LOG=logging.getLogger(__name__)


def gaussian_symmetric_kl(m1,c1,m2,c2):
    d=m1-m2; k=len(d)
    i1,i2=np.linalg.pinv(c1),np.linalg.pinv(c2)
    return float(max(0.,.25*(np.trace(i2@c1+i1@c2)+d@(i1+i2)@d-2*k)))


def occupancy_metrics(probability):
    n=len(probability); fractional=probability.sum(axis=0)
    kish=fractional**2/np.maximum((probability**2).sum(axis=0),1e-20)
    effective=[]
    for i in range(probability.shape[1]):
        x=probability[:,i]-probability[:,i].mean(); variance=np.dot(x,x)
        total=0.
        if variance>1e-20:
            for lag in range(1,min(60,n-1)+1):
                rho=np.dot(x[lag:],x[:-lag])/variance
                if rho<=0:
                    break
                total+=rho
        effective.append(n/(1+2*total))
    return fractional,kish,np.asarray(effective)


def run_hmm(returns,sigma,vix,cfg,out,states):
    directory=out/"hmm"/f"states_{states}"; directory.mkdir(parents=True,exist_ok=True)
    marker=directory/"complete.json"
    import json
    key=signature(cfg,[returns,sigma,vix],__file__)
    if marker.exists():
        if json.loads(marker.read_text()).get("signature")!=key:
            raise RuntimeError(f"Stale experiment marker {marker}; rerun this generated configuration with --redo")
        LOG.info("HMM %d states already completed",states)
        return
    f=features(returns,sigma,vix)
    panic=pd.Series(np.nan,index=returns.index,name="P")
    stress=pd.Series(np.nan,index=returns.index,name="stress")
    post=pd.DataFrame(np.nan,index=returns.index,columns=[f"Prob_RiskRank{i}" for i in range(states)])
    restarts=[]; state_rows=[]; transitions=[]; pairs=[]; stability=[]; model_rows=[]
    previous=None
    for fold,start in enumerate(range(cfg.initial_train,len(returns),cfg.refit_every)):
        end=min(start+cfg.refit_every,len(returns))
        train=f.iloc[:start].dropna(); test=f.iloc[start:end]
        scaler=StandardScaler().fit(train); xs=scaler.transform(train)
        best=None; best_ll=-np.inf; selected_seed=None
        for j in range(cfg.restarts):
            seed=cfg.seed+j
            model=GaussianHMM(n_components=states,covariance_type="full",n_iter=cfg.hmm_iter,
                              tol=.01,min_covar=1e-4,random_state=seed)
            record=dict(states=states,fold=fold,seed=seed,train_end=returns.index[start-1])
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    model.fit(xs)
                ll=model.score(xs); history=list(model.monitor_.history)
                delta=history[-1]-history[-2] if len(history)>1 else np.nan
                record.update(log_likelihood=ll,iterations=model.monitor_.iter,last_delta=delta,
                              hit_iteration_limit=model.monitor_.iter>=cfg.hmm_iter,
                              monotone_final=bool(delta>=-1e-6),warnings="; ".join(str(w.message) for w in caught),status="ok")
                if np.isfinite(ll) and ll>best_ll:
                    best,best_ll,selected_seed=model,ll,seed
            except (ValueError,np.linalg.LinAlgError) as error:
                record.update(status="failed",error=str(error))
            restarts.append(record)
        if best is None:
            pd.DataFrame(restarts).to_csv(directory/"restarts.csv",index=False)
            raise RuntimeError(f"All restarts failed: states={states}, fold={fold}")
        ranks,means=state_mapping(best,scaler,list(train))
        order=np.argsort(ranks); pstate=int(np.argmax(ranks))
        tp=filtered_probabilities(best,xs)
        ep=filtered_probabilities(best,scaler.transform(test),tp[-1])
        if fold==0:
            panic.loc[train.index]=tp[:,pstate]; stress.loc[train.index]=tp@ranks
            post.loc[train.index]=tp[:,order]
        panic.loc[test.index]=ep[:,pstate]; stress.loc[test.index]=ep@ranks
        post.loc[test.index]=ep[:,order]
        fractional,kish,ess=occupancy_metrics(tp)
        covars=best.covars_
        for state in range(states):
            stay=float(best.transmat_[state,state])
            state_rows.append(dict(states=states,fold=fold,state=state,risk_rank=float(ranks[state]),n_train=len(train),
                                   expected_occupancy=float(fractional[state]),fraction=float(fractional[state]/len(train)),
                                   hard_occupancy=int((tp.argmax(axis=1)==state).sum()),kish_weight_ess=float(kish[state]),
                                   autocorrelation_ess=float(ess[state]),oos_occupancy=float(ep[:,state].sum()),
                                   oos_fraction=float(ep[:,state].mean()),stay_probability=stay,
                                   expected_duration=1/(1-stay) if stay<1 else np.inf,
                                   rare=bool(fractional[state]<max(20,.01*len(train))),
                                   mean_return=float(means.loc[state,"SPY_Return"]),mean_vix=float(means.loc[state,"VIX"])))
            for target in range(states):
                transitions.append(dict(states=states,fold=fold,from_rank=float(ranks[state]),to_rank=float(ranks[target]),
                                        probability=float(best.transmat_[state,target])))
            for other in range(state+1,states):
                distance=gaussian_symmetric_kl(best.means_[state],covars[state],best.means_[other],covars[other])
                pairs.append(dict(states=states,fold=fold,state_a=state,state_b=other,symmetric_kl=distance,
                                  near_redundant=bool(distance<.1)))
        if previous is not None:
            old,oldscale,oldtrain=previous
            anchor=train.loc[train.index.intersection(oldtrain.index)].iloc[-126:]
            oldp=filtered_probabilities(old,oldscale.transform(anchor))
            newp=filtered_probabilities(best,scaler.transform(anchor))
            oldhard,newhard=oldp.argmax(axis=1),newp.argmax(axis=1)
            confusion=np.zeros((states,states),dtype=int)
            np.add.at(confusion,(oldhard,newhard),1)
            a,b=linear_sum_assignment(-confusion)
            stability.append(dict(states=states,fold=fold,n_anchor=len(anchor),
                                  adjusted_rand=adjusted_rand_score(oldhard,newhard),
                                  hungarian_agreement=confusion[a,b].sum()/len(anchor),
                                  mean_matched_posterior_difference=float(np.abs(oldp[:,a]-newp[:,b]).mean())))
        previous=(best,scaler,train)
        test_scaled=scaler.transform(test)
        # Conditional test likelihood, not a reset to start probabilities.
        extended=np.vstack([xs,test_scaled])
        conditional_ll=best.score(extended)-best.score(xs)
        model_rows.append(dict(states=states,fold=fold,n_train=len(train),n_test=len(test),selected_seed=selected_seed,
                               train_ll=best_ll,train_aic=best.aic(xs),train_bic=best.bic(xs),
                               conditional_test_ll=conditional_ll,conditional_test_ll_per_day=conditional_ll/len(test),
                               train_end=returns.index[start-1],test_start=test.index[0],test_end=test.index[-1]))
        if fold%12==0:
            LOG.info("HMM %d states: fold %d/96",states,fold+1)
    for name,frame in (("panic",panic),("stress",stress),("posteriors",post)):
        frame.to_csv(directory/(name+".csv"),index_label="Date")
    for name,rows in (("restarts",restarts),("occupancy",state_rows),("transitions",transitions),
                       ("redundancy",pairs),("stability",stability),("models",model_rows)):
        pd.DataFrame(rows).to_csv(directory/(name+".csv"),index=False)
    marker.write_text(json.dumps(dict(states=states,folds=len(model_rows),restarts=cfg.restarts,signature=key),indent=2))
