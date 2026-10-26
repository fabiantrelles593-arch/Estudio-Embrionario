from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from skimage import draw, measure, morphology
from metrics_2d import measure_mask
from morphology_space import pca_projection, morphology_distance_matrix

OUT = Path(__file__).resolve().parents[1] / 'demo'
OUT.mkdir(exist_ok=True)


def blob(n=256, axes=(35, 20), angle=0.0):
    y, x = np.mgrid[:n, :n]
    cy, cx = n/2, n/2
    ca, sa = np.cos(angle), np.sin(angle)
    xr = ca*(x-cx) + sa*(y-cy)
    yr = -sa*(x-cx) + ca*(y-cy)
    return (xr/axes[0])**2 + (yr/axes[1])**2 <= 1


def branched(n=256):
    m=np.zeros((n,n),bool)
    rr,cc=draw.line(35,128,220,128); m[rr,cc]=1
    rr,cc=draw.line(110,128,175,80); m[rr,cc]=1
    rr,cc=draw.line(140,128,195,180); m[rr,cc]=1
    return morphology.dilation(m, morphology.disk(8))


def make_dataset():
    cases=[]
    specs=[('SYN_A',(34,22),0),('SYN_B',(48,16),0),('SYN_C',(58,13),0),('SYN_D',None,None)]
    for i,(sid,axes,ang) in enumerate(specs):
        mask = branched() if axes is None else blob(axes=axes,angle=ang)
        p=OUT/f'{sid}.png';
        from skimage import io
        io.imsave(p,(mask*255).astype(np.uint8))
        d=measure_mask(mask).__dict__
        d.update({'observation_id':sid,'specimen_id':sid,'image_id':sid,'stage':'not_applicable','modality':'SYNTHETIC','view':'synthetic','source':'internal','asset_identifier':sid,'license_status':'not_applicable','segmentation_method':'known_mask','quality_flag':'PASS'})
        cases.append(d)
    return pd.DataFrame(cases)

if __name__=='__main__':
    df=make_dataset()
    df.to_csv(OUT/'synthetic_morphology.csv',index=False)
    coords,var,comp,keep,scaler=pca_projection(df)
    coords['observation_id']=df.loc[keep,'observation_id'].to_numpy()
    coords.to_csv(OUT/'synthetic_pca.csv',index=False)
    D,_=morphology_distance_matrix(df)
    D.to_csv(OUT/'synthetic_distance_matrix.csv')
    print('PCA explained variance:', var.tolist())
    print(coords.to_string(index=False))
