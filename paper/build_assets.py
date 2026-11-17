"""Extract tables from the completed research; no new random experiments."""
from __future__ import annotations
import csv
import hashlib
import json
from fractions import Fraction as Q
from pathlib import Path
import shutil
import subprocess
import sys

PAPER=Path(__file__).resolve().parent
ROOT=PAPER.parent
sys.path.insert(0,str(ROOT))
from src.model import Deck,availability,joint_forward,summarize

FIGURES=[
    '01_accessibility','03_order_constraint','04_payoff_distributions',
    '05_mean_and_sd','06_variance_decomposition','09_convergence',
    '10_construction_tradeoffs',
]


def read_csv(name):
    with (ROOT/'data'/name).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def write_table(path,columns,header,rows,note=None):
    text=[r'\begin{tabular}{'+columns+'}',r'\toprule',
          ' & '.join(header)+r' \\',r'\midrule']
    text+=[' & '.join(map(str,row))+r' \\' for row in rows]
    text += [r'\bottomrule',r'\end{tabular}']
    if note:
        text += [r'\par\smallskip{\footnotesize '+note+'}']
    path.write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')


def main():
    out=PAPER/'generated'
    out.mkdir(parents=True,exist_ok=True)
    (PAPER/'figures').mkdir(exist_ok=True)
    rows={r['id']:r for r in read_csv('summary.csv')}
    configs=json.loads((ROOT/'data/configurations.json').read_text(encoding='utf-8'))
    alias={name:rows[cfg['id']] for cfg in configs for name in cfg['aliases']}
    b=rows['baseline']
    ref=json.loads((ROOT/'data/baseline_refinement.json').read_text(encoding='utf-8'))
    d=Deck()
    exact=summarize(joint_forward(d,10,4))
    assert float(b['exact_mean'])==float(exact['mean'])
    macros={
        'BaseP':b['exact_p'],'BaseMu':b['exact_conditional_mean'],
        'BaseConditionalVar':b['exact_conditional_variance'],'BaseMean':b['exact_mean'],
        'BaseVar':b['exact_variance'],'BaseWithin':b['exact_within'],
        'BaseActivation':b['exact_activation'],'BaseZero':b['exact_zero'],
        'BaseTail':b['exact_conditional_tail24'],'BaseOverallTail':b['exact_tail24'],
    }
    (out/'numbers.tex').write_text('\n'.join(
        '\\newcommand{\\'+key+'}{'+f'{float(value):.6f}'+'}' for key,value in macros.items()
    )+'\n',encoding='utf-8',newline='\n')
    write_table(out/'baseline_table.tex','rrrrrr',
        ['$s$','$t$',r'$\mu$',r'$\sigma$',r'$\mathbb E(Y)$',r'$\operatorname{SD}(Y)$'],
        [[s,19-s,*[f'{float(alias[f"s_ratio_{s:02d}"][k]):.4f}' for k in (
            'exact_conditional_mean','exact_conditional_sd','exact_mean','exact_sd')]] for s in (6,10,14)])
    time=json.loads((ROOT/'data/completion_summary.json').read_text(encoding='utf-8'))
    write_table(out/'time_table.tex','lrrrrr',
        ['时间',r'$\mathbb E(\tau)$',r'$\operatorname{Var}(\tau)$','$q_{0.5}$','$q_{0.9}$','$q_{0.95}$'],
        [[r'$\tau_'+kind+'$',f'{time[kind]["mean"]:.6f}',f'{time[kind]["variance"]:.6f}',
          time[kind]['q50'],time[kind]['q90'],time[kind]['q95']] for kind in ('C','E')])
    operations=[
        ('基准','baseline'),('删除6张S','s_change_-6'),('增加6张S','s_change_+6'),
        ('以A替换1张T','a_from_t_2'),('以C替换1张T','c_from_t_3'),
        ('以C替换1张S','c_from_s_3'),
    ]
    write_table(out/'operation_table.tex','lrrrrrr',
        ['相对基准操作','$N$','$p$',r'$\mu$',r'$\mathbb E(Y)$',r'$\operatorname{SD}(Y)$',r'$\mathrm{CV}(Y)$'],
        [[label,int(alias[key]['N']),*[f'{float(alias[key][k]):.4f}' for k in (
            'exact_p','exact_conditional_mean','exact_mean','exact_sd','exact_cv')]] for label,key in operations])
    validation=[]
    for label,metric,ci in [('$p$','p','p'),(r'$\mu$','conditional_mean','conditional_mean'),
                            (r'$\mathbb E(Y)$','mean','mean')]:
        for count,source,prefix in [(200000,b,'sim_'),(1000000,ref['summary'],'')]:
            estimate=float(source[prefix+metric])
            interval='['+f'{float(source[prefix+ci+"_ci_low"]):.6f}, {float(source[prefix+ci+"_ci_high"]):.6f}'+']'
            successes = int(source[prefix+'successes']) if metric == 'conditional_mean' else None
            effective_n = f'{successes:,}' if successes is not None else '---'
            validation.append([label,f'{count:,}',effective_n,f'{float(b["exact_"+metric]):.6f}',
                               f'{estimate:.6f}',interval])
    write_table(out/'validation_table.tex','lrrrrr',
                ['指标','排列次数','条件样本量$K$','精确理论','模拟估计','95\\%置信区间'],validation)
    convergence=read_csv('convergence.csv')
    crows=[]
    for m in (2000,10000,50000,200000):
        group=[r for r in convergence if int(r['trials'])==m]
        assert len(group)==30
        rp=(sum(float(r['p_error'])**2 for r in group)/len(group))**.5
        ry=(sum(float(r['mean_error'])**2 for r in group)/len(group))**.5
        crows.append([f'{m:,}',f'{rp:.6f}',f'{(float(exact["p"]*(1-exact["p"]))/m)**.5:.6f}',
                      f'{ry:.6f}',f'{(float(exact["variance"])/m)**.5:.6f}'])
    write_table(out/'convergence_table.tex','rrrrr',
        ['$m$','$p$的RMSE','$p$的理论SE','均值的RMSE','均值的理论SE'],crows)
    provenance={}
    for name in FIGURES:
        source=ROOT/'figures'/f'{name}.pdf'
        provenance[source.relative_to(ROOT).as_posix()]={
            'source':source.relative_to(ROOT).as_posix(),
            'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    # Tagged-card identities identify every coefficient without simulation.
    p=exact['p'];h=4;N=24
    z=2*Q(h,N)*availability(Deck(c=1),10)/p
    alpha=Q(h,N)*availability(Deck(t=8),10)/p
    beta=Q(h*(h-1),N*(N-1))*availability(Deck(t=7),10)/p
    gamma=2*Q(h*(h-1),N*(N-1))*availability(Deck(c=1,t=8),10)/p
    assert (z,alpha,beta,gamma)==(Q(8,35),Q(33,175),Q(93,3325),Q(6,175))
    for s in range(20):
        r=summarize(joint_forward(Deck(s=s,t=19-s),10,4))
        meanx=z+s*alpha
        secondx=z+s*alpha+s*(s-1)*beta+2*s*gamma
        assert r['conditional_mean']==8*meanx
        assert r['conditional_variance']==64*(secondx-meanx**2)
    subprocess.run([sys.executable,str(PAPER/'print_figures.py')],check=True)
    (out/'provenance.json').write_text(json.dumps({
        'figures':provenance,'tagged_moments':{key:str(val) for key,val in
            [('E_Z',z),('alpha',alpha),('beta',beta),('gamma',gamma)]},
        'data_sha256':{name:hashlib.sha256((ROOT/'data'/name).read_bytes()).hexdigest()
            for name in ['summary.csv','completion_summary.json','baseline_refinement.json','convergence.csv']},
        'print_adaptation':'Same saved data and original plotting functions; enlarged labels for A4 print.',
        'print_figure_sha256':{name:hashlib.sha256((PAPER/'figures'/f'{name}.pdf').read_bytes()).hexdigest() for name in FIGURES},
    },ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print('Saved data tables, verified tagged moments, preserved original PDFs and adapted print labels.')


if __name__=='__main__':
    main()
