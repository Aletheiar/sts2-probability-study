"""Exact combinatorics. All probabilities and algebraic moments use Fraction.

Multiple A/B copies follow the explicit single-active-pair protocol: extra
unrevealed A/B are consumable non-attacks; their effects do not stack.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import combinations, product
from math import comb, sqrt


@dataclass(frozen=True)
class Deck:
    a: int = 1
    b: int = 1
    c: int = 2
    d: int = 1
    t: int = 9
    s: int = 10

    def __post_init__(self):
        if any(type(v) is not int or v < 0 for v in self.counts):
            raise ValueError('Card counts must be nonnegative integers')
        if self.N == 0:
            raise ValueError('Deck must be nonempty')

    @property
    def counts(self):
        return self.a,self.b,self.c,self.d,self.t,self.s

    @property
    def N(self):
        return sum(self.counts)


def choose(n,k):
    """Zero-extended binomial coefficient, including negative arguments."""
    return comb(n,k) if n>=0 and 0<=k<=n else 0


def validate(deck,n,h=0):
    if any(type(z) is not int for z in (n,h)) or not 0<=n<=deck.N or not 0<=h<=deck.N-n:
        raise ValueError('Require integer 0 <= n <= N and 0 <= h <= N-n')


def availability(deck,n,kind='C'):
    """At least one A, one B and one C (or C/D for kind E)."""
    validate(deck,n)
    if kind not in ('C','E'):
        raise ValueError('kind must be C or E')
    groups=(deck.a,deck.b,deck.c+(deck.d if kind=='E' else 0))
    ways=0
    for size in range(4):
        for subset in combinations(groups,size):
            ways+=(-1)**size*choose(deck.N-sum(subset),n)
    return Q(ways,choose(deck.N,n))


def quantile(pmf,level=Q(9,10),scale=1):
    """Left quantile inf{x:F(x)>=level}, never an interpolated quantile."""
    cdf=Q(0)
    for x,p in enumerate(pmf):
        cdf+=p
        if cdf>=level:
            return scale*x
    raise ValueError('PMF is not normalized')


def completion(deck,kind='E'):
    """First collection time in the one-pass permutation, support 0,...,N."""
    cdf=[availability(deck,n,kind) for n in range(deck.N+1)]
    if cdf[-1]!=1:
        raise ValueError('Collection impossible; time has mass at infinity')
    pmf=[cdf[0]]+[cdf[n]-cdf[n-1] for n in range(1,deck.N+1)]
    mean=sum((n*p for n,p in enumerate(pmf)),Q(0))
    second=sum((n*n*p for n,p in enumerate(pmf)),Q(0))
    return dict(cdf=cdf,pmf=pmf,mean=mean,variance=second-mean*mean,
                q50=quantile(pmf,Q(1,2)),q90=quantile(pmf),q95=quantile(pmf,Q(95,100)))


def ordered_probability(deck,n,kind='E'):
    """Exact without-replacement DP: a trigger appears after first A and B.

    State counts A,B,trigger already drawn and whether a valid trigger occurred.
    All other cards are neutral; no gameplay operations are implied.
    """
    validate(deck,n)
    if kind not in ('C','E'):
        raise ValueError('kind must be C or E')
    sizes=(deck.a,deck.b,deck.c+(deck.d if kind=='E' else 0))
    neutral=deck.N-sum(sizes)
    states={(0,0,0,False):Q(1)}
    for step in range(n):
        out={}
        for (a,b,e,flag),p in states.items():
            drawn=(a,b,e)
            for group in range(4):
                remaining=sizes[group]-drawn[group] if group<3 else neutral-(step-a-b-e)
                if remaining<=0:
                    continue
                counts=list(drawn)
                if group<3:
                    counts[group]+=1
                newflag=flag or (group==2 and a>0 and b>0)
                key=(*counts,newflag)
                out[key]=out.get(key,Q(0))+p*Q(remaining,deck.N-step)
        states=out
    assert sum(states.values(),Q(0))==1
    return sum((p for (*_,flag),p in states.items() if flag),Q(0))


def joint_forward(deck,n,h):
    """J[x]=P(I=1,X=x), enumerating stage-one category counts first."""
    validate(deck,n,h)
    result=[Q(0) for _ in range(h+1)]
    den=choose(deck.N,n)
    rest=deck.N-n
    for a in range(1,min(deck.a,n)+1):
        for b in range(1,min(deck.b,n-a)+1):
            for c in range(1,min(deck.c,n-a-b)+1):
                for s in range(min(deck.s,n-a-b-c)+1):
                    o=n-a-b-c-s
                    ways=choose(deck.a,a)*choose(deck.b,b)*choose(deck.c,c)*choose(deck.s,s)*choose(deck.d+deck.t,o)
                    if not ways:
                        continue
                    m=deck.a-a+deck.b-b+deck.c-c+deck.s-s
                    for x in range(h+1):
                        result[x]+=Q(ways*choose(m,x)*choose(rest-m,h-x),den*choose(rest,h))
    assert sum(result,Q(0))==availability(deck,n,'C')
    return result


def joint_reverse(deck,n,h):
    """Independent counting direction: enumerate stage two, then test stage one.

    Its h positions form an unconditional uniform subset. Conditional on it,
    the n setup positions are a uniform subset of the remaining N-h positions.
    """
    validate(deck,n,h)
    result=[Q(0) for _ in range(h+1)]
    if n<3 or min(deck.a,deck.b,deck.c)==0:
        return result
    for a,b,c,s in product(range(h+1),repeat=4):
        o=h-a-b-c-s
        if o<0:
            continue
        ways=choose(deck.a,a)*choose(deck.b,b)*choose(deck.c,c)*choose(deck.s,s)*choose(deck.d+deck.t,o)
        if not ways:
            continue
        remaining=Deck(deck.a-a,deck.b-b,deck.c-c,0,deck.d+deck.t-o,deck.s-s)
        result[a+b+c+s]+=Q(ways,choose(deck.N,h))*availability(remaining,n,'C')
    return result


def summarize(joint):
    """Moments of G=8X|I=1 and Y=8IX, including zero-inflation and tails."""
    p=sum(joint,Q(0))
    overall=list(joint)
    overall[0]+=1-p
    mean=sum((8*x*q for x,q in enumerate(joint)),Q(0))
    second=sum((64*x*x*q for x,q in enumerate(joint)),Q(0))
    variance=second-mean*mean
    conditional=[q/p for q in joint] if p else None
    mu=mean/p if p else None
    var=second/p-mu*mu if p else None
    within=p*var if p else Q(0)
    activation=p*(1-p)*mu*mu if p else Q(0)
    assert within+activation==variance
    return dict(p=p,conditional_pmf=conditional,overall_pmf=overall,
                conditional_mean=mu,conditional_variance=var,
                conditional_sd=sqrt(float(var)) if p else None,
                mean=mean,variance=variance,sd=sqrt(float(variance)),
                within=within,activation=activation,
                activation_share=activation/variance if variance else None,
                conditional_q90=quantile(conditional,scale=8) if p else None,
                q90=quantile(overall,scale=8),zero=overall[0],
                conditional_tail24=sum(conditional[3:],Q(0)) if p else None,
                tail24=sum(overall[3:],Q(0)),cv=sqrt(float(variance))/float(mean) if mean else None)
