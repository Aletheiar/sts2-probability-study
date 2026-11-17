"""Run exact cross-checks, independent permutation simulations and all exports.

From project root: python -m experiments.run_all
"""
import argparse
import csv
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np

from src.model import Deck,availability,completion,ordered_probability,joint_forward,joint_reverse,summarize,choose
from src.simulation import simulate,empirical_summary,wilson
from experiments.configurations import configurations

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'


def clean(value):
    if isinstance(value,Fraction):
        return float(value)
    if isinstance(value,dict):
        return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [clean(v) for v in value]
    return value


def write_json(path,value):
    path.write_text(json.dumps(clean(value),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')


def write_csv(path,rows):
    if not rows:
        return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys)
        writer.writeheader()
        writer.writerows(clean(row) for row in rows)


def static_exports(deck,raw,label,probability_rows,time_rows,time_statistics):
    """Export both static event types and their complete time distributions."""
    m=raw['trials']
    for kind in ('C','E'):
        result=completion(deck,kind) if availability(deck,deck.N,kind) else None
        counts=raw[f'time_{kind.lower()}_counts']
        if result:
            sim_mean=sum(t*k for t,k in enumerate(counts))/m
            sim_var=sum(k*(t-sim_mean)**2 for t,k in enumerate(counts))/(m-1) if m>1 else None
            sim_q90=next(t for t in range(deck.N+1) if sum(counts[:t+1])>=.9*m)
            time_statistics.append(dict(id=label,kind=kind,exact_mean=result['mean'],exact_variance=result['variance'],exact_q50=result['q50'],exact_q90=result['q90'],exact_q95=result['q95'],sim_mean=sim_mean,sim_variance=sim_var,sim_mean_se=(sim_var/m)**.5 if sim_var is not None else None,sim_q90=sim_q90,mass_infinity=0))
        else:
            time_statistics.append(dict(id=label,kind=kind,mass_infinity=1))
            lo,hi=wilson(counts[-1],m)
            time_rows.append(dict(id=label,kind=kind,n=None,time='infinity',theory=1,estimate=counts[-1]/m,ci_low=lo,ci_high=hi))
        for draw in range(deck.N+1):
            k=sum(counts[:draw+1])
            lo,hi=wilson(k,m)
            probability_rows.append(dict(id=label,kind=kind,n=draw,theory=availability(deck,draw,kind),estimate=k/m,se=(k/m*(1-k/m)/m)**.5,ci_low=lo,ci_high=hi,trials=m))
            if result:
                lo,hi=wilson(counts[draw],m)
                time_rows.append(dict(id=label,kind=kind,n=draw,time='finite',theory=result['pmf'][draw],estimate=counts[draw]/m,ci_low=lo,ci_high=hi))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials',type=int)
    parser.add_argument('--refinement-trials',type=int)
    parser.add_argument('--replicates',type=int)
    args=parser.parse_args()
    config=json.loads((ROOT/'experiments/config.json').read_text(encoding='utf-8'))
    for dest,key in [('trials','trials'),('refinement_trials','refinement_trials'),('replicates','convergence_repetitions')]:
        if getattr(args,dest) is not None:
            config[key]=getattr(args,dest)
    if any(config[k]<=0 for k in ('trials','refinement_trials','convergence_repetitions')):
        raise ValueError('Experiment sizes must be positive')
    DATA.mkdir(exist_ok=True)
    settings=configurations()
    write_json(DATA/'configurations.json',settings)
    write_json(DATA/'run_config.json',config)
    rows=[];raw_all={};exact_all={};pmfs=[];access_rows=[];time_rows=[];time_statistics=[]
    start=time.perf_counter()
    for index,setting in enumerate(settings):
        d=Deck(**setting['deck']);n=setting['n'];h=setting['h'];name=setting['id']
        joint=joint_forward(d,n,h)
        reverse=joint_reverse(d,n,h)
        assert joint==reverse,(name,'independent exact calculations disagree')
        theory=summarize(joint)
        seed=int(np.random.SeedSequence([config['seed'],1,index]).generate_state(1,dtype=np.uint64)[0])
        raw=simulate(d.counts,n,h,config['trials'],seed,static=True)
        sim=empirical_summary(raw)
        raw_all[name]=raw
        exact_all[name]=dict(joint=[str(q) for q in joint],metrics=theory,exact_metrics={k:str(v) for k,v in theory.items() if isinstance(v,Fraction)})
        row=dict(id=name,family=setting['family'],operation=setting['operation'],N=d.N,**setting['deck'],n=n,h=h,trials=raw['trials'],seed=seed)
        row.update({f'exact_{k}':v for k,v in theory.items() if not isinstance(v,list)})
        row.update({f'sim_{k}':v for k,v in sim.items()})
        for metric in ('p','mean','conditional_mean','variance','conditional_variance'):
            sekey={'p':'p_se','mean':'mean_se','conditional_mean':'conditional_mean_se','variance':'variance_se','conditional_variance':'conditional_variance_se'}[metric]
            if sim.get(sekey) and theory[metric] is not None:
                row[f'z_{metric}']=(sim[metric]-float(theory[metric]))/sim[sekey]
        rows.append(row)
        for x,j in enumerate(joint):
            for condition,p,counts,total in [('overall',theory['overall_pmf'][x],raw['overall_counts'],raw['trials']),('success',theory['conditional_pmf'][x] if theory['p'] else None,raw['success_counts'],raw['successes'])]:
                k=counts[x];lo,hi=wilson(k,total)
                pmfs.append(dict(id=name,condition=condition,x=x,g=8*x,theory=p,estimate=k/total if total else None,count=k,total=total,ci_low=lo,ci_high=hi,joint_exact=str(j)))
        static_exports(d,raw,name,access_rows,time_rows,time_statistics)
        print(f'[{index+1}/{len(settings)}] {name}: p={float(theory["p"]):.6f}, EY={float(theory["mean"]):.6f}',flush=True)
    # High-precision baseline check uses its own random stream.
    d=Deck();baseline=summarize(joint_forward(d,10,4))
    seed=int(np.random.SeedSequence([config['seed'],2]).generate_state(1,dtype=np.uint64)[0])
    refined=simulate(d.counts,10,4,config['refinement_trials'],seed,static=True)
    write_json(DATA/'baseline_refinement.json',dict(raw=refined,summary=empirical_summary(refined)))
    # Independent replications at each size estimate RMSE, rather than asserting
    # that a single realized error must decrease monotonically.
    conv=[]
    for size in config['convergence_sizes']:
        for rep in range(config['convergence_repetitions']):
            seed=int(np.random.SeedSequence([config['seed'],3,size,rep]).generate_state(1,dtype=np.uint64)[0])
            raw=simulate(d.counts,10,4,size,seed)
            sim=empirical_summary(raw)
            conv.append(dict(trials=size,replication=rep,seed=seed,p=sim['p'],mean=sim['mean'],p_error=sim['p']-float(baseline['p']),mean_error=sim['mean']-float(baseline['mean']),p_ci_low=sim['p_ci_low'],p_ci_high=sim['p_ci_high'],mean_ci_low=sim['mean_ci_low'],mean_ci_high=sim['mean_ci_high'],success_counts=json.dumps(raw['success_counts']),overall_counts=json.dumps(raw['overall_counts'])))
        print(f'Convergence: {size} x {config["convergence_repetitions"]}',flush=True)
    # Order-constraint formula independent of the DP, all prefixes of baseline.
    order=[]
    for kind,k in [('C',2),('E',3)]:
        for n in range(25):
            dp=ordered_probability(d,n,kind)
            formula=sum((Fraction(2*(j-1),24*23)*(1-Fraction(choose(22-(n-j),k),choose(22,k))) for j in range(2,n)),Fraction(0))
            assert dp==formula
            observed=refined[f'ordered_{kind.lower()}_counts'][n]
            lo,hi=wilson(observed,refined['trials'])
            order.append(dict(kind=kind,n=n,accessible=availability(d,n,kind),ordered=dp,estimate=observed/refined['trials'],ci_low=lo,ci_high=hi,trials=refined['trials']))
    write_csv(DATA/'summary.csv',rows)
    write_csv(DATA/'pmf.csv',pmfs)
    write_csv(DATA/'availability.csv',access_rows)
    write_csv(DATA/'completion_pmf.csv',time_rows)
    write_csv(DATA/'completion_statistics.csv',time_statistics)
    write_csv(DATA/'order.csv',order)
    write_csv(DATA/'convergence.csv',conv)
    write_json(DATA/'simulation_counts.json',raw_all)
    write_json(DATA/'exact_results.json',exact_all)
    write_json(DATA/'completion_summary.json',{kind:dict(**clean(completion(d,kind)),exact_mean=str(completion(d,kind)['mean']),exact_variance=str(completion(d,kind)['variance'])) for kind in ('C','E')})
    # Exchangeability proves degree <= 1 for the mean and <= 2 for variance.
    # Three exact finite experiments identify coefficients, then all 20 S
    # values are checked. This is exact interpolation, not fitted MC data.
    structural=[summarize(joint_forward(Deck(s=s,t=19-s),10,4)) for s in range(20)]
    polynomials={}
    for key in ('conditional_mean','conditional_variance','variance'):
        values=[r[key] for r in structural]
        c2=(values[2]-2*values[1]+values[0])/2
        c1=values[1]-values[0]-c2
        coefficients=[values[0],c1,c2]
        assert all(value==sum(coefficient*s**degree for degree,coefficient in enumerate(coefficients)) for s,value in enumerate(values))
        polynomials[key]=[str(q) for q in coefficients]
    peak=max(range(20),key=lambda s:structural[s]['conditional_variance'])
    write_json(DATA/'structural_identities.json',dict(coefficients=polynomials,coefficient_order='constant, S, S^2',conditional_variance_maximizer=peak,conditional_variance_vertex=str(-Fraction(polynomials['conditional_variance'][1])/(2*Fraction(polynomials['conditional_variance'][2]))),scope='A=B=D=1,C=2,N=24,T=19-S,n=10,h=4; integer 0<=S<=19'))
    write_json(DATA/'run_manifest.json',dict(time_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-start,python=sys.version,numpy=np.__version__,platform=platform.platform(),rng='NumPy PCG64; per-row Generator.permuted on labeled indices',configurations=len(rows),main_trials=sum(r['trials'] for r in rows),refinement_trials=refined['trials'],convergence_trials=sum(r['trials'] for r in conv),source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for pattern in ('src/*.py','experiments/*.py','experiments/config.json') for p in ROOT.glob(pattern)}))
    print('Numerical results saved. Generating figures and research report.',flush=True)
    from experiments.make_figures import main as make_figures
    make_figures()
    from experiments.write_report import main as write_report
    write_report()
    # Seal every deliverable after reports and plots have been written.
    import matplotlib
    manifest=json.loads((DATA/'run_manifest.json').read_text(encoding='utf-8'))
    manifest.update(matplotlib=matplotlib.__version__,elapsed_seconds_total=time.perf_counter()-start)
    write_json(DATA/'run_manifest.json',manifest)
    artifacts=[p for folder in ('src','tests','experiments','data','figures') for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_inventory.json']
    artifacts.extend(ROOT/name for name in ('README.md','requirements.txt','model_audit.md','research_report.md'))
    write_json(DATA/'artifact_inventory.json',{p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in artifacts})
    print(f'Complete: {len(rows)} configurations, {manifest["main_trials"]+manifest["refinement_trials"]+manifest["convergence_trials"]} permutations.',flush=True)


if __name__=='__main__':
    main()
