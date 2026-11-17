"""Explicit changes relative to baseline; duplicates reuse a single experiment."""
from dataclasses import asdict,replace
from src.model import Deck


def configurations():
    base=Deck()
    rows=[]
    lookup={}
    def add(identifier,family,operation,deck,n=10,h=4):
        key=(*deck.counts,n,h)
        if key in lookup:
            row=lookup[key]
            row['aliases'].append(identifier)
            row['families'].append(family)
            return
        row=dict(id=identifier,family=family,operation=operation,deck=asdict(deck),n=n,h=h,
                 delta={name:getattr(deck,name)-getattr(base,name) for name in asdict(base)},
                 aliases=[identifier],families=[family])
        rows.append(row)
        lookup[key]=row
    add('baseline','baseline','基准构筑',base)
    for s in range(20):
        add(f's_ratio_{s:02d}','S_T_replacement',f'固定N=24：S={s}，T={19-s}，S/T相互替换',replace(base,s=s,t=19-s))
    for kind in ('s','t'):
        for delta in (-6,-3,3,6,10):
            add(f'{kind}_change_{delta:+d}',f'{kind}_addition_deletion',f'{"增加" if delta>0 else "删除"}{abs(delta)}张{kind.upper()}；其余数量不变',replace(base,**{kind:getattr(base,kind)+delta}))
    for N in range(18,37,2):
        add(f'N_{N}','N_T_change',f'仅改变T，使N={N}；核心和S=10固定',replace(base,t=N-15))
    for core in ('a','b','c'):
        values=(0,2,3) if core in ('a','b') else (0,1,3,4,5)
        for value in values:
            delta=value-getattr(base,core)
            for donor in ('t','s'):
                add(f'{core}_from_{donor}_{value}',f'{core}_{donor}_replacement',f'固定N：{core.upper()}改为{value}，以{donor.upper()}反向替换{delta:+d}张',replace(base,**{core:value,donor:getattr(base,donor)-delta}))
        for value in (1,3,4) if core=='c' else (2,3):
            delta=value-getattr(base,core)
            add(f'{core}_change_{value}',f'{core}_addition_deletion',f'{"增加" if delta>0 else "删除"}{abs(delta)}张{core.upper()}；其余数量不变',replace(base,**{core:value}))
    for n in range(5,21):
        add(f'n_{n}','setup_size',f'卡组固定，只将设置阶段n改为{n}',base,n=n)
    for c in range(1,6):
        for s in range(2,17,2):
            add(f'grid_c{c}_s{s}','heatmap',f'固定N=24、A=B=D=1：C={c},S={s},T={21-c-s}；由T补齐',replace(base,c=c,s=s,t=21-c-s))
    return rows
