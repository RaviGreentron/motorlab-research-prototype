"""Deterministic, training-only anomaly models. Scores are not probabilities."""
import copy
import time
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import StandardScaler

FEATURES = ['i_rms_1','i_rms_2','i_rms_3','v_rms_1','v_rms_2','v_rms_3',
            'i_imbalance_pct','v_imbalance_pct','i_thd_pct','v_thd_pct','power_factor']


class Autoencoder:
    """CPU NumPy tanh bottleneck, linear decoder, Adam, validation early stopping."""
    def __init__(self, latent=4, epochs=350, seed=42, patience=30):
        self.latent, self.epochs, self.seed, self.patience = latent, epochs, seed, patience

    def fit(self, x, validation):
        rng = np.random.default_rng(self.seed)
        d = x.shape[1]
        self.weights = [rng.normal(0, 1/np.sqrt(d), (d,self.latent)), np.zeros(self.latent),
                        rng.normal(0, 1/np.sqrt(self.latent),(self.latent,d)), np.zeros(d)]
        m = [np.zeros_like(w) for w in self.weights]; v = copy.deepcopy(m)
        best, stale, self.history = float('inf'), 0, []
        for epoch in range(1,self.epochs+1):
            w,b,u,c = self.weights
            h = np.tanh(x@w+b); error = h@u+c-x
            g = 2*error/error.size; gh = (g@u.T)*(1-h*h)
            gradients = [x.T@gh,gh.sum(0),h.T@g,g.sum(0)]
            for j,grad in enumerate(gradients):
                m[j] = .9*m[j]+.1*grad; v[j] = .999*v[j]+.001*grad*grad
                self.weights[j] -= .01*(m[j]/(1-.9**epoch))/(np.sqrt(v[j]/(1-.999**epoch))+1e-8)
            loss = float(self.score(validation).mean())
            self.history.append({'epoch':epoch,'train_loss':float(self.score(x).mean()),'validation_loss':loss})
            if loss < best-1e-6:
                best, checkpoint, stale = loss, copy.deepcopy(self.weights), 0
            else: stale += 1
            if stale >= self.patience: break
        self.weights = checkpoint
        self.best_validation_loss = best
        return self

    def score(self,x):
        w,b,u,c = self.weights
        return np.mean((np.tanh(x@w+b)@u+c-x)**2,axis=1)


class DetectorSuite:
    def __init__(self,seed=42): self.seed=seed

    def fit(self,train,early_stop,calibration):
        for a in (train,early_stop,calibration):
            if len(a)<10 or not np.isfinite(a).all(): raise ValueError('Need finite healthy partitions with >=10 rows')
        begin=time.perf_counter()
        self.scaler=StandardScaler().fit(train)
        x=self.scaler.transform(train); ev=self.scaler.transform(early_stop)
        self.median=np.median(x,axis=0)
        self.mad=np.maximum(1.4826*np.median(np.abs(x-self.median),axis=0), .05)
        self.covariance=LedoitWolf().fit(x)
        self.forest=IsolationForest(n_estimators=150,contamination='auto',random_state=self.seed,n_jobs=1).fit(x)
        self.ae=Autoencoder(seed=self.seed).fit(x,ev)
        scores=self.raw_scores(calibration)
        self.thresholds={k:max(float(np.quantile(s,.99)),1e-8) for k,s in scores.items()}
        self.training_seconds=time.perf_counter()-begin
        self.train_count=len(train); self.calibration_count=len(calibration)
        return self

    def raw_scores(self,values):
        x=self.scaler.transform(values)
        return {'A':np.max(np.abs((x-self.median)/self.mad),axis=1),
                'B':-self.forest.score_samples(x),'C':self.ae.score(x)}

    def score(self,values):
        raw=self.raw_scores(values)
        return {k:{'raw':v,'ratio':v/self.thresholds[k], 'alert':v>self.thresholds[k]} for k,v in raw.items()}

    def contributors(self,value):
        x=self.scaler.transform(np.asarray(value).reshape(1,-1))[0]
        z=np.abs((x-self.median)/self.mad)
        return [{'feature':FEATURES[i],'robust_z':float(z[i])} for i in np.argsort(z)[-3:][::-1]]

    def statistical_diagnostics(self,values):
        x=self.scaler.transform(values)
        robust=(x-self.median)/self.mad
        ew=np.zeros(x.shape[1]); cp=np.zeros(x.shape[1]); cn=np.zeros(x.shape[1]); output=[]
        for i,row in enumerate(robust):
            ew=.2*row+.8*ew
            cp=np.maximum(0,cp+row-.5); cn=np.maximum(0,cn-row-.5)
            magnitude=max(float(cp.max()),float(cn.max()))
            output.append({'index':i,'ewma':float(np.max(np.abs(ew))), 'cusum':magnitude,
                           'change_candidate':bool(magnitude>8)})
        return {'classical_z_max':np.max(np.abs(x),axis=1).tolist(),
                'mahalanobis_squared':self.covariance.mahalanobis(x).tolist(),'sequential':output}
