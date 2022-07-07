from trafficintelligence import storage
import matplotlib.pyplot as plt
import numpy as np

objects = storage.loadTrajectoriesFromSqlite('/home/covid/Data/bernard-outremont/2021-06-16/GH010005-a_gt.sqlite', 'object')
CSpeeds = []
CAccelerations = []
Speeds85 = []
MaxAccelerations = []

centiles = [0.15, 0.5, 0.85]
stats = ['moyenne', 'Q15', 'Q50', 'Q85', 'max']
nInstantsIgnoredAtEnds = 5
fps = 29.97

def extractStats(obj, nInstantsIgnoredAtEnds):
    obj.speeds = obj.getVelocities().differentiateSG(11,9,0, nInstantsIgnoredAtEnds = nInstantsIgnoredAtEnds).norm()#obj.getSpeeds()
    obj.accelerations = obj.getAccelerations(21,15, nInstantsIgnoredAtEnds = nInstantsIgnoredAtEnds)
    return ([np.mean(obj.speeds)]+list(np.quantile(obj.speeds, centiles))+[np.max(obj.speeds)], [np.mean(obj.accelerations)]+list(np.quantile(obj.accelerations, centiles))+[np.max(obj.accelerations)])
    

for o in objects:
    sp, acc = extractStats(o, nInstantsIgnoredAtEnds)
    CSpeeds.append(sp)
    CAccelerations.append(acc)

for s in CSpeeds:
    Speeds85.append(s[3]*fps)
    

for a in CAccelerations:
    MaxAccelerations.append(a[3]*fps*fps)
    
#plt.hist(Speeds85) # n , bins, _ = 
plt.hist([(o.acc[3]*fps*fps) for o in objects])
plt.title('Accelerations (m/s2)')
plt.show()

# recherche d'objets problématiques


for o in objects:
    sp, acc = extractStats(o, nInstantsIgnoredAtEnds)
    o.acc = acc
    if acc[4]*fps*fps > 8 :
       ObjP.append(o)
