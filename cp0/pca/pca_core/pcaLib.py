from copy import deepcopy
import numpy as np
from math import *
def discretize(x_o,start,end,n):
    x=deepcopy(x_o)
    interv=float(end -start+0.0001)/n
    if interv<0.0001:
        r=[]
        for i in range(0,n):
            r+=[float(1.0/n)]
        return r
    distr=[]
    i=start+interv
    for i in range(0,n):
        distr+=[0]
    i=0
    while i<n:
        for j in range(0,len(x)):
            if x[j]>=start+i*interv and x[j]<start+(i+1)*interv:
                distr[i]+=1
        i+=1
    sumd=sum(distr)
    for i in range(0,len(distr)):
        distr[i]=float(distr[i])/sumd
    return distr
def discretizecomb(x,y,start,end,n):
    p=[]
    step=float((end-start+0.0001)/n)
    for i in range(n):
        p+=[[]]
        for j in range(n):
            p[-1]+=[0]
    distr=np.ndarray.tolist(np.zeros(7))
    for i in range(0,len(x)):
        indx=int((x[i]-start)/step)
        indy=int((y[i]-start)/step)
        p[indx][indy]+=1.0/len(x)
    return p
def dispTable(mat):
	r=''
	for i in mat:
		s=''
		for j in i:
			s+=repr(round(j,3)).ljust(10)
		r+=s+'\n'
	return r
def mutualinfo(x_o,y_o,start,end,n):
    x=deepcopy(x_o)
    y=deepcopy(y_o)
    l=deepcopy(x+y)
    l=sorted(l)
    I=0
    px=discretize(x,start,end,n)
    py=discretize(y,start,end,n)
    pxy=discretizecomb(x,y,start,end,n)
    for i in range(0,len(px)):
        for j in range(0,len(py)):
            try:
                t=pxy[i][j]/px[i]/py[j]
                if t==0:
                    I+=0 
                else:
                    I+=pxy[i][j]*np.log(t)
            except:
                I+=0
    return I
def sumcorrcoef(corrmat):#Return the sum of each row of the correlation matrix
    r=[]
    for i in corrmat:
        r+=[sum(map(lambda x:float(x),i))]
    return r
def standardize(data_o):
    data=deepcopy(data_o)
    i=0
    r=[]
    for xi in data:
        varx=float(np.var(np.asarray(xi)))
        avgx=sum(np.asarray(xi))/float(len(xi))
        r+=[[]]
        for xij in xi:
            xij=(xij-avgx)/sqrt(varx)
            r[i]+=[xij]
        i+=1
    return r