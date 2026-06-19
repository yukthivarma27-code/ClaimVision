import os, sys, pandas as pd
sys.path.insert(0, '.')
gt   = pd.read_csv('dataset/sample_claims.csv')
pred = pd.read_csv('evaluation_sample_output.csv')

cols = ['claim_status','issue_type','object_part','severity','evidence_standard_met','valid_image']
for c in cols:
    if c not in gt.columns or c not in pred.columns:
        continue
    gt_v  = gt[c].astype(str).str.strip().str.lower()
    pd_v  = pred[c].astype(str).str.strip().str.lower()
    correct = (gt_v == pd_v).sum()
    total   = len(gt)
    print(f'{c:35s}: {correct}/{total} = {correct/total*100:.0f}%')
    mask = gt_v != pd_v
    if mask.any():
        uid   = gt['user_id'].values
        for i, (g, p) in enumerate(zip(gt_v, pd_v)):
            if g != p:
                print(f'  user={uid[i]}  gt={g}  pred={p}')
