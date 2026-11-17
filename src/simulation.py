"""Permutation-only Monte Carlo; deliberately does not import src.model."""
from math import sqrt
import numpy as np

Z95=1.959963984540054


def wilson(k,m,z=Z95):
    if m<=0:
        return None,None
    p=k/m
    den=1+z*z/m
    center=(p+z*z/(2*m))/den
    half=z*sqrt(p*(1-p)/m+z*z/(4*m*m))/den
    return max(0.,center-half) if k else 0., min(1.,center+half) if k<m else 1.


def simulate(counts,n,h,trials,seed,static=False,batch_size=5000):
    """Uniformly permute labeled indices independently along each row.

    Category codes: A=0,B=1,C=2,D=3,T=4,S=5. Returned histograms are
    sufficient statistics; no theoretical probability is sampled.
    """
    if len(counts)!=6 or any(type(z) is not int or z<0 for z in counts):
        raise ValueError('Need six nonnegative integer counts')
    N=sum(counts)
    if N<=0 or not 0<=n<=N or not 0<=h<=N-n or trials<=0 or batch_size<=0:
        raise ValueError('Invalid sample sizes')
    labels=np.repeat(np.arange(6),counts)
    rng=np.random.Generator(np.random.PCG64(seed))
    hist=np.zeros(h+1,dtype=np.int64)
    time_c=np.zeros(N+2,dtype=np.int64)
    time_e=np.zeros(N+2,dtype=np.int64)
    ordered_c=np.zeros(N+1,dtype=np.int64)
    ordered_e=np.zeros(N+1,dtype=np.int64)
    batches=[]
    for start in range(0,trials,batch_size):
        size=min(batch_size,trials-start)
        indices=rng.permuted(np.broadcast_to(np.arange(N),(size,N)),axis=1)
        cards=labels[indices]
        first=cards[:,:n]
        ok=np.any(first==0,axis=1)&np.any(first==1,axis=1)&np.any(first==2,axis=1)
        second=cards[:,n:n+h]
        x=np.sum((second!=3)&(second!=4),axis=1)
        local=np.bincount(x[ok],minlength=h+1)
        hist+=local
        batches.append([size,*map(int,local)])
        if static:
            pos=np.arange(1,N+1)
            a=np.min(np.where(cards==0,pos,N+1),axis=1)
            b=np.min(np.where(cards==1,pos,N+1),axis=1)
            c=np.min(np.where(cards==2,pos,N+1),axis=1)
            e=np.min(np.where((cards==2)|(cards==3),pos,N+1),axis=1)
            ab=np.maximum(a,b)
            time_c+=np.bincount(np.maximum(ab,c),minlength=N+2)
            time_e+=np.bincount(np.maximum(ab,e),minlength=N+2)
            oc=np.min(np.where((cards==2)&(pos[None,:]>ab[:,None]),pos,N+1),axis=1)
            oe=np.min(np.where(((cards==2)|(cards==3))&(pos[None,:]>ab[:,None]),pos,N+1),axis=1)
            ordered_c+=np.cumsum(np.bincount(oc,minlength=N+2))[:N+1]
            ordered_e+=np.cumsum(np.bincount(oe,minlength=N+2))[:N+1]
    successes=int(hist.sum())
    overall=hist.copy()
    overall[0]+=trials-successes
    result=dict(trials=int(trials),seed=int(seed),successes=successes,
                success_counts=list(map(int,hist)),overall_counts=list(map(int,overall)),
                batches=batches,batch_size=batch_size)
    if static:
        result.update(time_c_counts=list(map(int,time_c)),time_e_counts=list(map(int,time_e)),
                      ordered_c_counts=list(map(int,ordered_c)),ordered_e_counts=list(map(int,ordered_e)))
    return result


def sample_moments(counts):
    m=sum(counts)
    if not m:
        return dict(mean=None,variance=None,sd=None,se=None,ci_low=None,ci_high=None,variance_se=None)
    mean=sum(8*x*k for x,k in enumerate(counts))/m
    central2=sum(k*(8*x-mean)**2 for x,k in enumerate(counts))/m
    central4=sum(k*(8*x-mean)**4 for x,k in enumerate(counts))/m
    variance=central2*m/(m-1) if m>1 else None
    se=sqrt(variance/m) if m>1 else None
    return dict(mean=mean,variance=variance,sd=sqrt(variance) if variance is not None else None,
                se=se,ci_low=mean-Z95*se if se is not None else None,
                ci_high=mean+Z95*se if se is not None else None,
                variance_se=sqrt(max(0,central4-central2**2)/m) if m>1 else None)


def empirical_summary(raw):
    m=raw['trials']
    k=raw['successes']
    result=dict(p=k/m,p_se=sqrt(k/m*(1-k/m)/m),successes=k)
    result['p_ci_low'],result['p_ci_high']=wilson(k,m)
    for prefix,counts in [('',raw['overall_counts']),('conditional_',raw['success_counts'])]:
        for name,value in sample_moments(counts).items():
            key=prefix+('mean_se' if name=='se' else ('mean_'+name if name.startswith('ci_') else name))
            result[key]=value
    result['conditional_tail24']=sum(raw['success_counts'][3:])/k if k else None
    result['conditional_tail24_ci_low'],result['conditional_tail24_ci_high']=wilson(sum(raw['success_counts'][3:]),k)
    return result
