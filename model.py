import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support

TRAIN_FILE="train.csv"

def features(df, cols):
    x=df[cols].apply(pd.to_numeric,errors="coerce").fillna(0)
    f=pd.DataFrame(index=df.index)
    f["mean_usage"]=x.mean(axis=1)
    f["std_usage"]=x.std(axis=1).fillna(0)
    f["median_usage"]=x.median(axis=1)
    f["min_usage"]=x.min(axis=1)
    f["max_usage"]=x.max(axis=1)
    f["range_usage"]=f["max_usage"]-f["min_usage"]
    f["zero_fraction"]=(x==0).mean(axis=1)
    f["q25"]=x.quantile(.25,axis=1)
    f["q75"]=x.quantile(.75,axis=1)
    f["iqr"]=f["q75"]-f["q25"]
    n=x.shape[1]; w=max(7,min(30,n//10))
    f["early_mean"]=x.iloc[:,:w].mean(axis=1)
    f["late_mean"]=x.iloc[:,-w:].mean(axis=1)
    f["late_to_early_ratio"]=(f["late_mean"]/f["early_mean"].replace(0,np.nan)).replace([np.inf,-np.inf],np.nan).fillna(0)
    return f

df=pd.read_csv(TRAIN_FILE)
if "FLAG" not in df.columns:
    raise ValueError("FLAG target column not found in train.csv")

date_cols=[c for c in df.columns if c!="FLAG"]
X=features(df,date_cols)
y=pd.to_numeric(df["FLAG"],errors="coerce").fillna(0).astype(int)

Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
model=RandomForestClassifier(n_estimators=300,class_weight="balanced_subsample",random_state=42,n_jobs=-1)
model.fit(Xtr,ytr)

p=model.predict_proba(Xte)[:,1]
pred=(p>=.5).astype(int)
precision,recall,f1,_=precision_recall_fscore_support(yte,pred,average="binary",zero_division=0)
print(f"ROC-AUC: {roc_auc_score(yte,p):.4f}")
print(f"Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")

full=model.predict_proba(X)[:,1]
risk=pd.DataFrame({"consumer_id":np.arange(len(df)),"risk_score":full})
risk["risk_level"]=pd.cut(risk.risk_score,[-np.inf,.4,.7,np.inf],labels=["LOW","MEDIUM","HIGH"])
risk.to_csv("model_risk_scores.csv",index=False)

# Date estimate: sustained drop relative to a 14-day rolling median.
parsed=pd.to_datetime(date_cols,errors="coerce")
dates_out=[]
if parsed.notna().sum()==len(date_cols):
    vals=df[date_cols].apply(pd.to_numeric,errors="coerce").fillna(0)
    for row in vals.to_numpy():
        s=pd.Series(row,index=parsed)
        base=s.rolling(14,min_periods=7).median()
        ratio=s/base.replace(0,np.nan)
        sustained=(ratio<.60).rolling(7,min_periods=7).mean()>=.70
        dates_out.append(sustained[sustained].index[0] if sustained.any() else pd.NaT)
else:
    dates_out=[pd.NaT]*len(df)

pd.DataFrame({"consumer_id":np.arange(len(df)),"estimated_theft_start_date":dates_out}).to_csv("model_theft_dates.csv",index=False)
print("Created model_risk_scores.csv and model_theft_dates.csv")
