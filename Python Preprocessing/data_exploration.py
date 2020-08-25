#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  5 23:56:35 2019

@author: mike
"""

# Just playing around with the data for now
import pandas as pd
import datetime
import plotly
from matplotlib import pyplot as plt

lines = ['ACRL', 'MBPJ', 'ME', 'MOBO', 'NEC', 'NJCL', 'PVL', 'RVL']

acrl = data[(data['line'] == 'ACRL') & (data['time'] >= datetime.date(2018, 9, 4))] # Date of most recent tweet for ME
mbpj = data[(data['line'] == 'MBPJ') & (data['time'] >= datetime.date(2018, 9, 4))]
me   = data[(data['line'] == 'ME') & (data['time'] >= datetime.date(2018, 9, 4))]
mobo = data[(data['line'] == 'MOBO') & (data['time'] >= datetime.date(2018, 9, 4))]
nec  = data[(data['line'] == 'NEC') & (data['time'] >= datetime.date(2018, 9, 4))]
njcl = data[(data['line'] == 'NJCL') & (data['time'] >= datetime.date(2018, 9, 4))]
pvl  = data[(data['line'] == 'PVL') & (data['time'] >= datetime.date(2018, 9, 4))]
rvl  = data[(data['line'] == 'RVL') & (data['time'] >= datetime.date(2018, 9, 4))]


returns = 10 # Return top 10 reasons
acrl_counts = reason_counts(acrl, phrases, returns)
mbpj_counts = reason_counts(mbpj, phrases, returns)
me_counts   = reason_counts(me, phrases, returns)
mobo_counts = reason_counts(mobo, phrases, returns)
nec_counts  = reason_counts(nec, phrases, returns)
njcl_counts = reason_counts(njcl, phrases, returns)
pvl_counts  = reason_counts(pvl, phrases, returns)
rvl_counts  = reason_counts(rvl, phrases, returns) 

# Join into 1 table
tmp1 = acrl_counts[['reason_str', 'count']].merge(right = mbpj_counts[['reason_str', 'count']], on = 'reason_str', how = 'outer', suffixes=['_arcl','_mbpj'])
tmp2 = me_counts[['reason_str', 'count']].merge(right = mobo_counts[['reason_str', 'count']], on = 'reason_str', how = 'outer', suffixes=['_me','_mobo'])
tmp3 = nec_counts[['reason_str', 'count']].merge(right = njcl_counts[['reason_str', 'count']], on = 'reason_str', how = 'outer', suffixes=['_nec','_njcl'])
tmp4 = pvl_counts[['reason_str', 'count']].merge(right = rvl_counts[['reason_str', 'count']], on = 'reason_str', how = 'outer', suffixes=['_pvl','_rvl'])
all_counts = tmp1.merge(right = tmp2, on = 'reason_str', how = 'outer')
all_counts = all_counts.merge(right = tmp3, on = 'reason_str', how = 'outer')
all_counts = all_counts.merge(right = tmp4, on = 'reason_str', how = 'outer')

plt.bar(rvl_counts['reason_str'], rvl_counts['count'])
