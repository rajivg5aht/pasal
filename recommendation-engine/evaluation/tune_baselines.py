"""Validation-only grid search and disjoint-user assessment for six configurations.

No final test data or generated-text condition is read or fabricated here.
"""
import argparse
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import prepare_cases, cohort, ranking_metrics, summarize
from models.engine import RecommendationEngine
from models.content.train_snapshot import fingerprint
from switching.policy import PolicyConfig, route

CONFIGURATIONS = ['global_popularity','category_popularity','tfidf','item_cf','fixed_hybrid','switching_without_genai']
COHORTS = ['0','1-4','5-19','20+']


def select_users(cases, per_cohort=100, seed=42):
    if per_cohort < 2:
        raise ValueError('At least two users per cohort requested')
    rng=np.random.default_rng(seed)
    selected=[]
    for label in COHORTS:
        group=sorted((c for c in cases if cohort(c.event_count)==label),key=lambda c:c.visitorid)
        if len(group)<2:
            raise ValueError(f'Insufficient validation users in cohort {label}')
        indices=rng.permutation(len(group))[:per_cohort]
        for position,index in enumerate(indices):
            selected.append((group[index], 'tune' if position < len(indices)//2 else 'assessment'))
    return selected


def weight_grid():
    return [{'content':a/4,'item_cf':b/4,'global_popularity':(4-a-b)/4}
            for a in range(5) for b in range(5-a)]


def policy_grid():
    return [PolicyConfig(lo,hi,confidence,weight)
            for lo,hi,confidence,weight in itertools.product([2,5,10],[10,20,40],[.25,.5,.75],[.25,.5,.75]) if lo<hi]


def switching_key(case,confidence,config):
    strategy=route(case.event_count,confidence,[],config)
    if strategy in {'cf_popularity_hybrid','hybrid_fallback'}:
        return f'cf_pop_{config.cf_weight}',strategy
    return {'content':'tfidf'}.get(strategy,strategy),strategy


def objective(records, key_for):
    # Equal weighting of the three nonzero-history strata. Zero-history routes
    # cannot distinguish these tuning parameters and are assessed separately.
    means=[]
    for label in COHORTS[1:]:
        rows=[r for r in records if r['partition']=='tune' and r['cohort']==label]
        means.append(float(np.mean([r['ndcg'][key_for(r)] for r in rows])))
    return float(np.mean(means))


def run(train_path,validation_path,content_dir,cf_dir,output,per_cohort=100):
    output=Path(output)
    if output.exists(): raise FileExistsError('Use a new evaluation version')
    training=pd.read_csv(train_path)
    validation=pd.read_csv(validation_path)
    cutoff=int(validation.timestamp.min())
    engine=RecommendationEngine(training,cutoff,content_dir,cf_dir)
    if engine.cf_manifest['train_sha256'] != fingerprint(train_path):
        raise ValueError('CF model was fitted on different training events')
    selection=select_users(prepare_cases(training,validation,cutoff),per_cohort)
    weights=weight_grid()
    policies=policy_grid()
    records=[]
    started=time.perf_counter()
    for number,(case,partition) in enumerate(selection,1):
        signals,confidence,selected=engine.signals(case)
        rankings={name:engine.rank(signals[{'tfidf':'content'}.get(name,name)],10)
                  for name in CONFIGURATIONS[:4]}
        if not rankings['category_popularity']:
            rankings['category_popularity']=rankings['global_popularity']
        for index,weight in enumerate(weights):
            rankings[f'fixed_{index}']=engine.rank(engine.blend(signals,weight),10)
        for weight in [.25,.5,.75]:
            rankings[f'cf_pop_{weight}']=engine.rank(engine.blend(signals,{'item_cf':weight,'global_popularity':1-weight}),10)
        records.append({'case':case,'partition':partition,'cohort':cohort(case.event_count),
                        'confidence':confidence,'rankings':rankings,
                        'ndcg':{key:ranking_metrics(recs,case.targets,10)['ndcg'] for key,recs in rankings.items()}})
        if number%25==0:
            print(f'Prepared {number}/{len(selection)} users in {time.perf_counter()-started:.1f}s',flush=True)
    fixed_scores=[objective(records,lambda r,i=i:f'fixed_{i}') for i in range(len(weights))]
    policy_scores=[objective(records,lambda r,p=p:switching_key(r['case'],r['confidence'],p)[0]) for p in policies]
    best_fixed=int(np.argmax(fixed_scores))
    best_policy=int(np.argmax(policy_scores))
    policy=policies[best_policy]
    rows=[]
    for record in records:
        if record['partition']!='assessment': continue
        case=record['case']
        switch,strategy=switching_key(case,record['confidence'],policy)
        for name in CONFIGURATIONS:
            key=f'fixed_{best_fixed}' if name=='fixed_hybrid' else switch if name=='switching_without_genai' else name
            recs=record['rankings'][key]
            eligible_targets=case.targets & engine.eligible - case.seen
            rows.append({'model':name,'visitorid':case.visitorid,'cohort':record['cohort'],
                         'history_events':case.event_count,'target_count':len(case.targets),
                         'eligible_target_count':len(eligible_targets),'targetless':not bool(case.targets),
                         'recommendations':recs,'failure':None,'latency_ms':None,
                         'strategy':strategy if name=='switching_without_genai' else name,
                         **ranking_metrics(recs,case.targets,10)})
    # Precomputed ranks cannot support per-model latency measurements.
    summaries=summarize(rows,engine.eligible)
    for row in summaries: row['p95_latency_ms']=None
    output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summaries,indent=2,allow_nan=False))
    with (output/'per_user.jsonl').open('x') as stream:
        for row in rows: stream.write(json.dumps(row,allow_nan=False)+'\n')
    config={'status':'validation_selected_not_final_test_freeze','cutoff_ms':cutoff,
            'fixed_weights':weights[best_fixed],'switching':asdict(policy),
            'objective':'equal mean NDCG@10 across nonzero-history tuning strata',
            'tie_policy':'first configuration in predeclared grid',
            'genai_condition':'not_evaluated', 'seed':42}
    (output/'selected_config.json').write_text(json.dumps(config,indent=2))
    manifest={'source_sha256':fingerprint(__file__),
              'inputs_sha256':{str(p):fingerprint(p) for p in [train_path,validation_path]},
              'content_manifest':engine.content_manifest,'cf_manifest':engine.cf_manifest,
              'sample': [{'visitorid':c.visitorid,'cohort':cohort(c.event_count),'partition':partition} for c,partition in selection],
              'weight_grid':[{'weights':w,'objective':v} for w,v in zip(weights,fixed_scores)],
              'policy_grid':[{'policy':asdict(p),'objective':v} for p,v in zip(policies,policy_scores)],
              'limitations':['Stratified assessment means are not population-weighted estimates',
                             'Small validation samples; final uncertainty and density experiments outstanding',
                             'No final test or genuine GenAI ablation evaluated',
                             'Shared prepared rankings do not measure request latency']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False))
    return config


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['train','validation','content-dir','cf-dir','output']: p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--per-cohort',type=int,default=100)
    a=p.parse_args()
    print(json.dumps(run(a.train,a.validation,a.content_dir,a.cf_dir,a.output,a.per_cohort),indent=2))
