import numpy as np, pandas as pd
from src.morphology_space import pca_projection, morphology_distance_matrix

def test_pca_runs():
    df=pd.DataFrame({'observation_id':['a','b','c'], 'aspect_ratio':[1.,2.,3.], 'circularity':[.9,.7,.5]})
    c,var,comp,keep,sc=pca_projection(df)
    assert c.shape[0]==3
    assert len(var)==2

def test_distance_diagonal_zero():
    df=pd.DataFrame({'observation_id':['a','b'], 'aspect_ratio':[1.,2.], 'circularity':[.9,.7]})
    D,_=morphology_distance_matrix(df)
    assert np.allclose(np.diag(D),0)
