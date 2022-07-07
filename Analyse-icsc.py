import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3
#import seaborn as sns

from trafficintelligence import storage, indicators, events, utils

parentDirname='/home/covid/Data/'
imgDirname=parentDirname+'FigureR/'
dirnames = ['bernard-bloomfield/2021-06-18/', 'bernard-outremont/2021-06-16/', 'bernard-champagneur/2021-06-16/Fatima/']
xlabels=['Bernard\nBloomfield', 'Bernard\nOutremont', 'Bernard\nChampagneur']

sites = [d.split('/')[0] for d in dirnames]

centiles = [0.15, 0.5, 0.85]
nInstantsIgnoredAtEnds = 5
fps = 29.97

def extractStats(obj, nInstantsIgnoredAtEnds):
    obj.speeds = obj.getVelocities().differentiateSG(11,9,0, nInstantsIgnoredAtEnds = nInstantsIgnoredAtEnds, mode='nearest').norm()#obj.getSpeeds()
    obj.accelerations = obj.getAccelerations(21,15, nInstantsIgnoredAtEnds = nInstantsIgnoredAtEnds, mode='nearest')
    return ([np.mean(obj.speeds)]+list(np.quantile(obj.speeds, centiles)), [np.mean(obj.accelerations)]+list(np.quantile(obj.accelerations, centiles)))

objects = {}
interactions = {}
for dirname in dirnames:
    for fn in utils.listfiles(parentDirname+dirname, 'sqlite'):
        if 'annote' in fn:
            print(fn)
            interactions[fn]=storage.loadInteractionsFromSqlite(fn)
            objects[fn]=storage.loadTrajectoriesFromSqlite(fn, 'object')
            for inter in interactions[fn]:
                inter.setRoadUsers(objects[fn])

speeds = {}
accelerations = {}
for fn in objects.keys():
    site = fn.split('/')[4]
    tmpspeeds = []
    tmpaccels = []
    for o in objects[fn]:
        if o.getUserType() == 4:
            sp, acc = extractStats(o, nInstantsIgnoredAtEnds)
            tmpspeeds.append(sp)
            tmpaccels.append(acc)
    speeds[site] = speeds.get(site, []) + tmpspeeds
    accelerations[site] = accelerations.get(site, []) + tmpaccels

stats = ['moyenne', 'Q15', 'Q50', 'Q85']
for site in speeds.keys():
    speeds[site]=pd.DataFrame(speeds[site], columns=stats)*fps
    accelerations[site]=pd.DataFrame(accelerations[site], columns=stats)*fps*fps
    #print(site)
    #print(speeds[site].describe())
    #print(accelerations[site].describe())

ttcs = {}
distances = {}
cyclistSpeeds = {}
for fn in objects.keys():
    site = fn.split('/')[4]
    for inter in interactions[fn]:
        if inter.length() >= 15:
            cyclist = None
            ped = None
            if inter.roadUser1.getUserType() == 4 and inter.roadUser2.getUserType() == 2:
                cyclist = inter.roadUser1
                ped = inter.roadUser2
            elif inter.roadUser1.getUserType() == 2 and inter.roadUser2.getUserType() == 4:
                cyclist = inter.roadUser2
                ped = inter.roadUser1
            if cyclist is not None:
                ttc = inter.getIndicator('Time to Collision')
                if ttc is not None and len(ttc) > 5:
                    ttcmin = ttc.getMostSevereValue(centile = 15)/fps
                    if ttcmin < 10:
                        ttcs.setdefault(site, []).append(ttcmin)
                d = inter.getIndicator('Distance')
                t = d.getInstantOfMostSevereValue()
                distances.setdefault(site, []).append(d.getMostSevereValue(2))
                if d[t] <= 10:
                    cyclistSpeeds.setdefault(site, []).append(cyclist.speeds[min(len(cyclist.speeds)-1, max(0,t-nInstantsIgnoredAtEnds-cyclist.getFirstInstant()))]*fps)


### Affichage des boxplots
#Vitesses, accelerations
        
for stat in stats:
    plt.figure(figsize=(8,7))
    plt.boxplot([speeds[site][stat] for site in sites], labels=xlabels, meanline=True, showmeans=True, sym= 'b+')
    plt.xlabel('Sites', fontsize=14)
    plt.ylabel('Speed '+stat+' (m/s)', fontsize=14) # Vitesse
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(imgDirname+'vitesses-'+stat+'.pdf')
    #plt.show()

for stat in stats:
    plt.figure(figsize=(8,7))
    plt.boxplot([accelerations[site][stat] for site in sites], labels=xlabels, meanline=True, showmeans=True, sym= '')
    plt.xlabel('Sites', fontsize=14)
    plt.ylabel('Accélération '+stat+' (m/s$^2$)', fontsize=14)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(imgDirname+'accelerations-'+stat+'.pdf')
    #plt.show()
    
# Graphiques: Distances, vitesses des cyclistes, TTC

for ylabel, data in zip(['Distance (m)', '$TTC_{15}$ (s)', 'Instant Speed (m/s)'], [distances, ttcs, cyclistSpeeds]):# Vitesse instantanée
    plt.figure(figsize=(8,7))
    plt.boxplot([data[site] for site in sites], labels=xlabels, meanline=True, showmeans=True, sym= 'b+')
    #if 'TTC' in ylabel:
    #    plt.ylim(ymax=30)
    plt.xlabel('Sites', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(imgDirname+ylabel.lower().replace('$','').replace(' ','-').split('-(')[0]+'.pdf')
#plt.show()
