"""Academic plots from saved numerical outputs, PNG and vector PDF."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from experiments.io_utils import ROOT,read_csv,read_json,load_results

FIG=ROOT/'figures'
BLUE='#31688e';ORANGE='#bf6b25';GREEN='#37846a';GRAY='#777777'


def style():
    candidates=['Microsoft YaHei','SimHei','SimSun','Noto Sans CJK SC']
    available={f.name for f in font_manager.fontManager.ttflist}
    selected=next((f for f in candidates if f in available),None)
    if selected is None:
        raise RuntimeError('No Chinese font found; install Noto Sans CJK SC or Microsoft YaHei')
    plt.rcParams.update({'font.family':selected,'font.size':10,'axes.titlesize':11,'axes.labelsize':10,
                         'axes.unicode_minus':False,'pdf.fonttype':42,'ps.fonttype':42,
                         'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,
                         'savefig.dpi':300,'figure.constrained_layout.use':True})
    return selected


def save(fig,name,caption,catalog):
    for ext in ('png','pdf'):
        fig.savefig(FIG/f'{name}.{ext}',bbox_inches='tight')
    catalog.append(dict(file=name,caption=caption))
    plt.close(fig)


def main():
    FIG.mkdir(exist_ok=True)
    font=style()
    rows,byid,aliases=load_results()
    config=read_json('run_config.json')
    m=config['trials'];refine=config['refinement_trials'];reps=config['convergence_repetitions']
    avail=read_csv('availability.csv');times=read_csv('completion_pmf.csv');order=read_csv('order.csv')
    pmfs=read_csv('pmf.csv');conv=read_csv('convergence.csv')
    b=byid['baseline'];catalog=[]
    fig,axs=plt.subplots(1,3,figsize=(13,4))
    for kind,color,label in [('C',BLUE,'A、B、至少一张C'),('E',ORANGE,'A、B、至少一张C/D')]:
        subset=[r for r in avail if r['id']=='baseline' and r['kind']==kind]
        axs[0].plot([r['n'] for r in subset],[r['theory'] for r in subset],color=color,label=label)
        pts=[r for r in subset if r['n'] in (5,10,15,20)]
        axs[0].scatter([r['n'] for r in pts],[r['estimate'] for r in pts],color=color,s=20,marker='x')
        ns=list(range(18,37,2));pr=[]
        for N in ns:
            rid=aliases[f'N_{N}']['id']
            pr.append(next(r['theory'] for r in avail if r['id']==rid and r['kind']==kind and r['n']==10))
        axs[1].plot(ns,pr,color=color,marker='o',markersize=3,label=label)
    for core,values,color in [('a',[0,1,2,3],BLUE),('c',[0,1,2,3,4,5],ORANGE)]:
        p=[b['exact_p'] if v==({'a':1,'c':2}[core]) else aliases[f'{core}_from_t_{v}']['exact_p'] for v in values]
        axs[2].plot(values,p,marker='o',color=color,label=f'{core.upper()}替换T；其余核心固定')
    for ax in axs:
        ax.set_ylabel('组件联合可及概率');ax.grid(alpha=.18);ax.legend(fontsize=8)
    axs[0].set(xlabel='揭示张数 n',title='（a）基准卡组：实线理论、叉号模拟')
    axs[1].set(xlabel='总张数 N（仅增删T）',title='（b）固定 n=10、S=10')
    axs[1].set_xticks([18,22,26,30,34,36])
    axs[2].set(xlabel='所变关键类别的副本数',title='（c）固定 N=24、n=10')
    save(fig,'01_accessibility',f'精确理论可及性曲线；（a）叉号为每组{m}次实体排列模拟。改变 N 只增删T；增加关键牌采用固定N替换T。',catalog)

    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for kind,color,offset in [('C',BLUE,-.18),('E',ORANGE,.18)]:
        r=[x for x in times if x['id']=='baseline' and x['kind']==kind]
        axs[0].bar(np.array([x['n'] for x in r])+offset,[x['theory'] for x in r],width=.35,color=color,alpha=.75,label=f'{kind}类：精确PMF')
        axs[0].plot([x['n']+offset for x in r],[x['estimate'] for x in r],'.',color='black',markersize=2)
        r=[x for x in avail if x['id']=='baseline' and x['kind']==kind]
        axs[1].step([x['n'] for x in r],[x['theory'] for x in r],where='post',color=color,label=f'{kind}类精确CDF')
    axs[0].set(xlabel='首次见齐张数 T',ylabel='概率质量',title='（a）精确分布与模拟点')
    axs[1].axhline(.9,ls=':',color=GRAY,lw=1);axs[1].axvline(23,ls=':',color=GRAY,lw=1)
    axs[1].set(xlabel='揭示张数 n',ylabel='累计概率',title='（b）两类90%分位数均为23张')
    for ax in axs:ax.legend(fontsize=9);ax.grid(alpha=.15)
    save(fig,'02_completion_time',f'基准首次见齐时间：柱/阶梯为精确理论值，黑点为{m}次模拟；两类90%分位数均为23。',catalog)

    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,kind in zip(axs,('C','E')):
        r=[x for x in order if x['kind']==kind]
        ax.plot([x['n'] for x in r],[x['accessible'] for x in r],color=BLUE,label='只要求组件见齐：理论')
        ax.plot([x['n'] for x in r],[x['ordered'] for x in r],color=ORANGE,label='另要求触发牌晚于A/B：理论')
        pts=[x for x in r if x['n'] in (5,10,15,20,24)]
        ax.errorbar([x['n'] for x in pts],[x['estimate'] for x in pts],yerr=[[x['estimate']-x['ci_low'] for x in pts],[x['ci_high']-x['estimate'] for x in pts]],fmt='x',color=ORANGE,ms=5,label=f'顺序事件：{refine:,}次模拟及95%区间')
        ax.set(xlabel='揭示张数 n',ylabel='事件概率',title=f'{kind}类组件：同一排列中的不同事件');ax.legend(fontsize=8);ax.grid(alpha=.15)
    save(fig,'03_order_constraint',f'基准无顺序/有顺序事件的精确概率。叉号及Wilson区间来自独立{refine}次模拟；不能视为战斗执行概率。',catalog)

    fig,axs=plt.subplots(1,2,figsize=(11,4))
    xs=np.arange(5)
    for i,(s,color) in enumerate([(6,BLUE),(10,ORANGE),(14,GREEN)]):
        rid=aliases[f's_ratio_{s:02d}']['id']
        r=[x for x in pmfs if x['id']==rid and x['condition']=='success']
        xpos=xs+(i-1)*.24
        axs[0].bar(xpos,[x['theory'] for x in r],width=.23,color=color,alpha=.7,label=f'S={s}：理论')
        axs[0].errorbar(xpos,[x['estimate'] for x in r],yerr=[[x['estimate']-x['ci_low'] for x in r],[x['ci_high']-x['estimate'] for x in r]],fmt='.',color='black',ms=3,lw=.7)
    for offset,condition,color,label in [(-.18,'success',BLUE,'成功条件下 G'),(.18,'overall',ORANGE,'总体 Y')]:
        r=[x for x in pmfs if x['id']=='baseline' and x['condition']==condition]
        axs[1].bar(xs+offset,[x['theory'] for x in r],width=.35,color=color,label=label)
    axs[0].set(xticks=xs,xlabel='消耗张数 X',ylabel='条件概率',title='（a）成功条件下：理论柱、模拟点及95%区间')
    axs[1].set(xticks=xs,xticklabels=[str(8*x) for x in xs],xlabel='格挡收益',ylabel='概率',title='（b）基准：条件与总体精确分布')
    for ax in axs:ax.legend(fontsize=9)
    save(fig,'04_payoff_distributions',f'条件消耗数的精确混合超几何分布与{m}次模拟；右图比较基准条件和总体收益，总体0同时包含未启动和启动后0消耗。',catalog)

    ratios=[aliases[f's_ratio_{s:02d}'] for s in range(20)]
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,metric1,metric2,title in [(axs[0],'exact_conditional_mean','exact_mean','（a）收益期望'),(axs[1],'exact_conditional_sd','exact_sd','（b）收益标准差')]:
        for metric,color,label in [(metric1,BLUE,'成功条件下 G：理论'),(metric2,ORANGE,'总体 Y：理论')]:
            ax.plot(range(20),[r[metric] for r in ratios],color=color,label=label)
            for s in (6,10,14):
                ax.scatter(s,ratios[s][metric],color=color,s=24)
        ax.set(xlabel='普通非攻击牌 S 数量（S替换T，N=24）',ylabel='格挡点数',title=title,xticks=[0,3,6,9,12,15,19]);ax.legend(fontsize=9);ax.grid(alpha=.15)
    save(fig,'05_mean_and_sd','固定N、S/T替换的精确收益期望和标准差，圆点标注S=6、10、14。条件与总体标准差有不同变化方向。',catalog)

    selected=[aliases[f's_ratio_{s:02d}'] for s in (6,10,14)]+[aliases['s_change_+6'],aliases['a_from_t_2']]
    labels=['S=6\n替换T','S=10\n基准','S=14\n替换T','增加6张S\nN=30','A替换T\nA=2']
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    within=np.array([r['exact_within'] for r in selected]);activation=np.array([r['exact_activation'] for r in selected])
    for ax,scale,title in [(axs[0],np.ones(5),'（a）精确总体方差的绝对贡献'),(axs[1],within+activation,'（b）精确方差贡献比例')]:
        ax.bar(range(5),within/scale,color=BLUE,label='启动后波动：pσ²')
        ax.bar(range(5),activation/scale,bottom=within/scale,color=ORANGE,label='启动混合差异：p(1−p)μ²')
        ax.set(xticks=range(5),xticklabels=labels,ylabel='方差（格挡²）' if ax is axs[0] else '方差份额',title=title)
    handles,legend_labels=axs[0].get_legend_handles_labels()
    fig.legend(handles,legend_labels,loc='outside lower center',ncols=2,fontsize=9)
    save(fig,'06_variance_decomposition','全方差公式的精确分解；操作成本由横轴说明，比较成功后的条件波动与成功/失败条件均值差异。',catalog)

    fig,axs=plt.subplots(2,2,figsize=(11,8))
    for ax,metric,title in zip(axs.flat,['exact_p','exact_conditional_mean','exact_mean','exact_cv'],['（a）协议启动概率 p','（b）条件收益均值 μ','（c）总体收益均值 E(Y)','（d）总体变异系数 SD(Y)/E(Y)']):
        arr=np.array([[aliases[f'grid_c{c}_s{s}'][metric] for s in range(2,17,2)] for c in range(1,6)])
        mesh=ax.pcolormesh(np.arange(9),np.arange(6),arr,cmap='viridis',edgecolors='white',linewidth=.6)
        ax.set(xticks=np.arange(8)+.5,xticklabels=list(range(2,17,2)),yticks=np.arange(5)+.5,yticklabels=list(range(1,6)),xlabel='S 数量',ylabel='C 数量',title=title)
        colorbar=fig.colorbar(mesh,ax=ax,pad=.02,shrink=.9)
        colorbar.solids.set_rasterized(False)
    save(fig,'07_sensitivity_heatmap',f'精确理论敏感性：N=24、A=B=D=1，T=21−C−S；每个网格配置另做{m}次排列验证。PDF网格为矢量单元。',catalog)

    fig,axs=plt.subplots(2,1,figsize=(12,7),sharex=True)
    ix=np.arange(1,len(rows)+1)
    err=np.array([r['sim_mean']-r['exact_mean'] for r in rows]);se=np.array([r['sim_mean_se'] for r in rows])
    axs[0].errorbar(ix,err,yerr=1.959963984540054*se,fmt='.',color=BLUE,ms=3,lw=.6)
    axs[0].axhline(0,color='black',lw=.8);axs[0].set(ylabel='总体均值估计误差（格挡）',title=f'（a）每配置{m:,}次：模拟减理论；误差棒为逐指标95% CLT区间')
    for metric,color,label in [('p',BLUE,'启动概率'),('mean',ORANGE,'总体均值'),('conditional_mean',GREEN,'条件均值')]:
        pts=[(i+1,r[f'z_{metric}']) for i,r in enumerate(rows) if r.get(f'z_{metric}') is not None]
        axs[1].scatter([x for x,y in pts],[y for x,y in pts],s=12,color=color,label=label,alpha=.75)
    axs[1].axhspan(-1.96,1.96,color='gray',alpha=.1)
    for z in (-1.96,0,1.96):axs[1].axhline(z,color=GRAY,ls=':',lw=.8)
    axs[1].set(xlabel='配置序号（顺序对应 data/summary.csv）',ylabel='标准化误差（估计误差/估计标准误）',title='（b）灰带为 ±1.96；多指标比较不要求全部落入带内');axs[1].legend(ncols=3,fontsize=9)
    save(fig,'08_monte_carlo_errors',f'{len(rows)}个独立配置的理论与模拟误差；区间均为逐指标95%，不作多重检验通过率断言。',catalog)

    fig,axs=plt.subplots(1,2,figsize=(11,4))
    sizes=sorted({int(r['trials']) for r in conv})
    for ax,metric,var,title in [(axs[0],'p_error',b['exact_p']*(1-b['exact_p']),'（a）启动概率估计'),(axs[1],'mean_error',b['exact_variance'],'（b）总体收益均值估计')]:
        rmse=[np.sqrt(np.mean([r[metric]**2 for r in conv if r['trials']==size])) for size in sizes]
        ax.loglog(sizes,rmse,'o-',color=BLUE,label='独立重复实验的RMSE')
        ax.loglog(sizes,[np.sqrt(var/size) for size in sizes],'--',color=ORANGE,label='精确方差给出的标准误尺度')
        ax.set(xlabel='每次实验的排列次数 m',ylabel='估计误差尺度',title=title);ax.legend(fontsize=9);ax.grid(alpha=.15,which='both')
    save(fig,'09_convergence',f'各样本量独立重复{reps}次；RMSE为实际模拟结果，虚线由理论方差给出，尺度随m^(−1/2)变化。',catalog)

    fig,axs=plt.subplots(1,2,figsize=(11,4))
    paths=[([aliases[f's_change_{delta:+d}'] for delta in (-6,-3)]+[b]+[aliases[f's_change_{delta:+d}'] for delta in (3,6,10)],BLUE,'仅增删S'),(ratios,ORANGE,'S替换T；N固定')]
    for seq,color,label in paths:
        axs[0].plot([r['exact_p'] for r in seq],[r['exact_conditional_mean'] for r in seq],'o-',color=color,ms=3,label=label)
        axs[1].plot([r['s'] for r in seq],[r['exact_mean'] for r in seq],'o-',color=color,ms=3,label=label)
    axs[0].set(xlabel='协议启动概率 p',ylabel='条件收益均值 μ',title='（a）增加S与S/T替换的不同权衡')
    axs[1].set(xlabel='S 数量',ylabel='总体收益期望 E(Y)',title='（b）操作不同，指标变化也不同')
    for ax in axs:ax.legend(fontsize=9);ax.grid(alpha=.15)
    save(fig,'10_construction_tradeoffs','比较固定其他数量而增删S与固定N的S/T替换；曲线是精确理论值。只在已建模指标和所示参数范围内解释权衡。',catalog)
    (FIG/'catalog.json').write_text(json.dumps(dict(font=font,figures=catalog),ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    (FIG/'README.md').write_text('# 图表说明\n\n所有图均提供300 dpi PNG和嵌入中文字体的矢量PDF。\n\n'+'\n\n'.join(f'**{r["file"]}**：{r["caption"]}' for r in catalog),encoding='utf-8',newline='\n')
    from PIL import Image,ImageOps,ImageDraw
    sheet=Image.new('RGB',(1500,1100),'white')
    draw=ImageDraw.Draw(sheet)
    for i,item in enumerate(catalog):
        with Image.open(FIG/f'{item["file"]}.png') as im:
            sheet.paste(ImageOps.contain(im,(490,235)),((i%3)*500,(i//3)*275+24))
        draw.text(((i%3)*500+8,(i//3)*275+5),item['file'],fill='black')
    sheet.save(FIG/'contact_sheet.png')
    print(f'Figures: {len(catalog)} pairs; Chinese font: {font}',flush=True)


if __name__=='__main__':
    main()
