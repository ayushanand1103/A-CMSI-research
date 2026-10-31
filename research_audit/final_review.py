"""Independent final table-to-output and point-metric review; no model refitting."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,precision_score,recall_score,f1_score


def review(root):
    root=Path(root); out=root/"outputs/robustness"; source=out/"manuscript"; dest=out/"final_review"
    dest.mkdir(exist_ok=True)
    def csv(name):
        return pd.read_csv(out/"evaluation"/name)
    ab=csv("ablation_metrics.csv"); hm=csv("hmm_metrics.csv"); et=csv("evt_metrics.csv")
    selected=["Adaptive","NoProbability","Entropy","NoHMM","Equal","PCA","NoEVT","NoGARCH","EntropyDeficit","PCAFloor"]
    pairs=csv("all_paired_global_holm.csv")
    fallback=pd.read_csv(out/"evt/parameter_stability.csv").groupby("experiment").fallback_fraction.mean().reset_index()
    specs={
        "original_table.tex":(pd.read_csv(out/"original/tables/main_ablation_metrics.csv"),["variant","n","rmse","mae","crisis_auc"]),
        "hmm_table.tex":(hm[hm.variant.str.startswith("HMM")],["variant","n","rmse",("rmse_ci_low","rmse_ci_high"),"mae","auc","brier"]),
        "ablation_table.tex":(ab[ab.variant.isin(selected)],["variant","n","rmse",("rmse_ci_low","rmse_ci_high"),"mae","auc"]),
        "crisis_table.tex":(ab[ab.variant.isin(selected)],["variant","precision","recall","f1","auc",("auc_ci_low","auc_ci_high"),"brier"]),
        "evt_table.tex":(et,["variant","n","rmse",("rmse_ci_low","rmse_ci_high"),"mae","auc","brier"]),
        "diagnostics_table.tex":(csv("hmm_diagnostic_summary.csv"),["states","initial_bic","conditional_test_ll_per_day","mean_rare_state_fraction","median_refit_ari","median_expected_duration","selected_nonmonotone"]),
        "paired_table.tex":(pairs[pairs.family.eq("ablation")&pairs.candidate.eq("Adaptive")],["reference","rmse_improvement","rmse_ci_low","rmse_ci_high","pvalue","p_holm_family","p_holm_global"]),
        "conditional_table.tex":(ab[ab.variant.str.startswith("Conditional")],["variant","n","rmse",("rmse_ci_low","rmse_ci_high"),"mae","auc","brier"]),
        "fallback_table.tex":(fallback,["experiment","fallback_fraction"])}
    records=[]; summaries=[]
    for name,(frame,columns) in specs.items():
        text=(source/name).read_text(encoding="utf-8")
        body=text.split(r"\midrule",1)[1].split(r"\bottomrule",1)[0]
        rows=[line.strip()[:-2].strip().split(" & ") for line in body.splitlines() if line.strip().endswith(r"\\")]
        assert len(rows)==len(frame),(name,len(rows),len(frame))
        count=0
        for row,(_,expected) in zip(rows,frame.iterrows()):
            assert len(row)==len(columns),(name,row)
            for cell,column in zip(row,columns):
                pairs_to_check=list(zip(re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",cell),column)) if isinstance(column,tuple) else [(cell,column)]
                if isinstance(column,tuple):
                    assert len(pairs_to_check)==len(column)
                for value,key in pairs_to_check:
                    target=expected[key]
                    if isinstance(target,str):
                        good=value.replace(r"\_","_")==target; error=0
                    elif pd.isna(target) or not np.isfinite(float(target)):
                        good=value=="--"; error=0
                    else:
                        error=abs(float(value)-float(target))
                        good=error<=.00005000001
                    records.append(dict(table=name,row=str(expected[columns[0]]),field=key,displayed=value,
                                        output_value=target,passed=bool(good),absolute_rounding_difference=error))
                    count+=1
        summaries.append(dict(table=name,rows=len(rows),checked_fields=count,passed=all(r["passed"] for r in records if r["table"]==name)))
    pd.DataFrame(records).to_csv(dest/"table_cell_checks.csv",index=False)
    pd.DataFrame(summaries).to_csv(dest/"table_summary.csv",index=False)
    metric_checks=[]
    for family in ("hmm","ablation","weighting","evt"):
        prediction=csv(f"{family}_predictions.csv"); metric=csv(f"{family}_metrics.csv").set_index("variant")
        for variant,g in prediction.groupby("variant"):
            g=g.dropna(subset=["actual_vol","forecast_vol"])
            y=g.actual_vol.to_numpy(); f=g.forecast_vol.to_numpy()
            truth=g.actual_crisis.to_numpy(); prob=g.crisis_probability.to_numpy(); signal=prob>=.5
            values=dict(n=len(g),rmse=np.sqrt(np.mean((y-f)**2)),mae=np.mean(np.abs(y-f)),
                        auc=roc_auc_score(truth,prob),brier=np.mean((truth-prob)**2),
                        precision=precision_score(truth,signal,zero_division=0),
                        recall=recall_score(truth,signal,zero_division=0),f1=f1_score(truth,signal,zero_division=0))
            for field,expected in values.items():
                difference=abs(expected-float(metric.loc[variant,field]))
                metric_checks.append(dict(family=family,variant=variant,field=field,absolute_error=difference,passed=difference<1e-12))
    pd.DataFrame(metric_checks).to_csv(dest/"independent_metric_checks.csv",index=False)
    text=(source/"main.tex").read_text(encoding="utf-8")
    keys=set(re.findall(r"@\w+\{([^,]+),",(source/"references.bib").read_text(encoding="utf-8")))
    citations={key.strip() for group in re.findall(r"\\cite\w*(?:\[[^]]*\])?\{([^}]+)\}",text) for key in group.split(",")}
    all_tests=all(r["passed"] for r in records+metric_checks)
    result=dict(reviewed_utc=datetime.now(timezone.utc).isoformat(),tables=len(summaries),checked_table_fields=len(records),
                recomputed_metric_fields=len(metric_checks),all_numeric_checks_pass=all_tests,
                citations=len(citations),bibliographic_entries=len(keys),all_citations_defined=citations<=keys,
                no_uncited_entries=keys<=citations,doi_preserved="10.5281/zenodo.23682477" in text,
                negative_primary_finding_explicit="no demonstrated predictive advantage" in text.lower(),
                original_datasets_unchanged=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
                    for name,digest in json.loads((out/"provenance.json").read_text())["dataset_sha256"].items()))
    (dest/"review_checks.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    if not all_tests or not citations<=keys or not result["no_uncited_entries"] or not result["negative_primary_finding_explicit"] or not result["doi_preserved"] or not result["original_datasets_unchanged"]:
        raise SystemExit("Final review numeric/integrity checks failed")
    return result


if __name__=="__main__":
    review(Path(__file__).resolve().parents[1])
