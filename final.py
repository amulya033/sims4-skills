#!/usr/bin/env python3
import pandas as pd
import sys
from itertools import groupby

def put_stuff(path='activities.csv', max_uses=10):
    # loading csv file
    orig = pd.read_csv(path)
    orig = orig.dropna(subset=['Activity']).fillna(0)
    skill_cols = list(orig.columns[2:])
    expanded = []
    for _, row in orig.iterrows():
        remaining = max_uses
        take = 1
        while remaining > 0:
            count = min(take, remaining)
            new = row.copy()
            new['Time'] = int(row['Time']) * count
            for s in skill_cols:
                new[s] = int(row[s]) * count
            expanded.append(new)
            remaining -= count
            take <<= 1
    return pd.DataFrame(expanded).reset_index(drop=True), skill_cols

def skilling(skill_cols):
    print("Available skills:")
    for s in skill_cols:
        print(f"  - {s}")
    resp = input("\nEnter three skills (comma-separated), with priority 1-3: ")
    lookup = {s.lower(): s for s in skill_cols}
    chosen = []
    for part in resp.split(','):
        key = part.strip().lower()
        if key in lookup:
            chosen.append(lookup[key])
    if len(chosen) != 3:
        print("Error: enter exactly three valid skills.")
        sys.exit(1)
    return chosen

def actual_stuff(df, skill_cols, chosen, total_minutes=1440, xp_per_min=8):
    P = len(df)
    full_mask = (1<<3)-1
    durations = df['Time'].tolist()
    xp_rate = [sum(row[s] for s in chosen)*xp_per_min 
               for _, row in df.iterrows()]
    masks = []
    for _, row in df.iterrows():
        m = 0
        for bit, skill in enumerate(chosen):
            if row[skill] > 0:
                m |= 1 << bit
        masks.append(m)

    NEG_INF = -10**15
    dp = [[NEG_INF]*8 for _ in range(total_minutes+1)]
    choice = [[None]*8 for _ in range(total_minutes+1)]
    dp[0][0] = 0

    for t in range(1, total_minutes+1):
        for mask in range(8):
            dp[t][mask] = dp[t-1][mask]
            choice[t][mask] = (-1, mask, 1)
        # try each bounded activity
        for i in range(P):
            d = durations[i]
            if d > t:
                continue
            rate = xp_rate[i]
            skm = masks[i]
            for prev in range(8):
                val = dp[t-d][prev]
                if val == NEG_INF:
                    continue
                nm = prev | skm
                cand = val + rate * d
                if cand > dp[t][nm]:
                    dp[t][nm] = cand
                    choice[t][nm] = (i, prev, d)

    best = dp[total_minutes][full_mask]
    if best == NEG_INF:
        print("No schedule can cover all three skills in 24 h.")
        sys.exit(1)

    # backtrack
    sched = []
    t, mask = total_minutes, full_mask
    while t > 0:
        i, prev, used = choice[t][mask]
        if i is None:
            break
        if i >= 0:
            sched.append(df.at[i,'Activity'])
            t -= used
            mask = prev
        else:
            t -= 1
    sched.reverse()
    return best, sched

def print_stuff(schedule, total_xp, chosen):
    print(f"\nSkills prioritized: {', '.join(chosen)}")
    print(f"Max total XP in 24 h: {total_xp}")
    print("Optimal schedule:")
    for act, grp in groupby(schedule):
        cnt = sum(1 for _ in grp)
        if cnt > 1:
            print(f"  • {act} [×{cnt}]")
        else:
            print(f"  • {act}")

def main():
    df, skills = put_stuff('activities.csv', max_uses=10)
    chosen = skilling(skills)
    total_xp, sched = actual_stuff(df, skills, chosen)
    print_stuff(sched, total_xp, chosen)

if __name__=='__main__':
    main()
