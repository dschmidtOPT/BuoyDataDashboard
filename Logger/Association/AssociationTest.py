# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 10:38:38 2023

@author: dschmidt

OptMdasArpaContactT
    p.TimeUnixSec = x.TimeUnixSec
    p.CountPublish = x.CountPublish
    p.SenderId = x.SenderId
    p.TargetNumber = x.TargetNumber
    p.ReportedTimestamp = x.ReportedTimestamp
    p.OlderThan30Sec = x.OlderThan30Sec
    p.OlderThan1Min = x.OlderThan1Min
    p.OlderThan3Min = x.OlderThan3Min
    p.TtSymbolEchoAcquired = x.TtSymbolEchoAcquired
    p.TargetTracked = x.TargetTracked
    p.ManualTarget = x.ManualTarget
    p.AcquiredAsManual = x.AcquiredAsManual
    p.HaveEcho = x.HaveEcho
    p.ToBeDisplayed = x.ToBeDisplayed
    p.RefTarget = x.RefTarget
    p.DangerousTarget = x.DangerousTarget
    p.InsideGuardZone = x.InsideGuardZone
    p.ApprovedAsDanger = x.ApprovedAsDanger
    p.IdCount = x.IdCount
    p.ConningDistanceM = x.ConningDistanceM
    p.ConningBearingDeg = x.ConningBearingDeg
    p.AntennaDistanceM = x.AntennaDistanceM
    p.AntennaBearingDeg = x.AntennaBearingDeg
    p.TrueTargetSpeedMs = x.TrueTargetSpeedMs
    p.TrueTargetCourseDeg = x.TrueTargetCourseDeg
    p.RelativeTargetSpeedMs = x.RelativeTargetSpeedMs
    p.RelativeTargetCourseDeg = x.RelativeTargetCourseDeg
    p.ClosestPointOfApproachM = x.ClosestPointOfApproachM
    p.TimeToClosestApproachSec = x.TimeToClosestApproachSec
    p.BowCrossingRangeM = x.BowCrossingRangeM
    p.BowCrossingTimeSec = x.BowCrossingTimeSec
    p.AntennaNumber = x.AntennaNumber
    p.AbsoluteLocationValid = x.AbsoluteLocationValid
    p.TargetLatitude = x.TargetLatitude
    p.TargetLongitude = x.TargetLongitude
    p.Pcomms = x.Pcomms.Copy()
    """
import time
import os
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.path import Path
from matplotlib import pyplot as plt
from matplotlib import transforms



verts = [
    (0., 1.),
    (0.5, -1.),
    (0., -0.25),
    (-0.5, -1.),
    (0, 1)
    ]

codes = [
    Path.MOVETO,
    Path.LINETO,
    Path.LINETO,
    Path.LINETO,
    Path.CLOSEPOLY
    ]


# Association to AIS contacts or other ARPA tracks
def associateARPA( newARPA, margin = 0.1 ) :
    #margin is NM threshold parameter to tweak
    #ARPAs = getSensor.tracks()   ## or whatever function queries all track objects
    norm_dist = 100 ## Initialize over threshold
    while ( norm_dist > margin ) and ARPAs:
            # cycle through known ARPA contacts until position matches within threshold
            thisContact = ARPAs.pop(0)
            norm_dist = (  ( thisContact.y_pos - newARPA.pos_y)**2 + ( thisContact.x_pos - newARPA.pos_x )**2 )**0.5
    if not ARPAs:   # No ARPA contacts matching the newARPA target position within margin
            # cycle through known AIS contacts until position matches within threshold
            norm_dist = 100
            AISs = getVesselPosition() ## or whatever function queries all AIS contact objects
            while ( norm_dist > margin ) and AISs:
                  thisContact = AISs.pop(0)
                  norm_dist = (  ( thisContact.y_pos - newARPA.pos_y)**2 + ( thisContact.x_pos - newARPA.pos_x )**2 )**0.5
    if not AIS:  #No AIS contacts matching the position either within threshold, create a new vesselID
        return new_vessel_id
    return thisContact.id


class OptMdasArpaContact:
    TargetCounting = -1
    def __init__(self, tstamp):
        TimeUnixSec = tstamp
        CountPublish = None 
        SenderId = "MDAS-01"
        TargetNumber = None
        ReportedTimestamp = time.strftime('%H:%M:%S') #, time.time) 
        OlderThan30Sec = False         
        OlderThan1Min = False
        OlderThan3Min = False
        TtSymbolEchoAcquired = False
        TargetTracked = True
        ManualTarget = True
        AcquiredAsManual = True
        HaveEcho = False
        ToBeDisplayed = True
        RefTarget = None
        DangerousTarget = False
        InsideGuardZone = False
        ApprovedAsDanger = False
        OptMdasArpaContact.TargetCounting += 1 
        IdCount = OptMdasArpaContact.TargetCounting
        ConningDistanceM = -1
        ConningBearingDeg = -1
        AntennaDistanceM = -1
        AntennaBearingDeg = -1
        TrueTargetSpeedMs = -1
        TrueTargetCourseDeg = -1
        RelativeTargetSpeedMs = -1
        RelativeTargetCourseDeg = -1
        ClosestPointOfApproachM = -1
        TimeToClosestApproachSec = -1
        BowCrossingRangeM = -1
        BowCrossingTimeSec = -1
        AntennaNumber = -1
        AbsoluteLocationValid = -1
        TargetLatitude = -1
        TargetLongitude = -1
        Pcomms = ''

## Global ##

ARPAs = []


fig = plt.figure(0)
ax = fig.add_subplot(111)
plt.ion()


## Populate the fake data ##
t_all = []
x_all = []
y_all = []
dropout_count = 6

for dt,xs,func in zip([3, 4, 5, 3, 2,10, 3], [ np.linspace( 0, np.pi/2, 11),
                                 np.linspace( -0.5, 0.5, 15 ),
                                 np.linspace( 0.5, 0.5, 15 ),
                                 np.linspace( 0, np.pi/2, 15 ),
                                 np.linspace( 0.5, 1.2, 10),
                                 np.linspace( -0.5, 1, 5),
                                 np.linspace( 1, 1.5, 15)
                                 ],
                                 ['np.sin( 1.5 * x ) - 0.75',
                                  '5 * x',
                                  '1.5 - i*0.2',
                                  '-1*np.sin(0.5*x**3) -1',
                                  '-3 * np.cos(3*x**2) -1',
                                  '-0.25*x + 2',
                                  '-8*x**2 + 2'
                                  ]):
    t = 0
    i = 0 
    for x in xs:
        if (i % dropout_count == 0):
            t += 2*dt
            i += 1 
            continue
        y = eval(func)
        x_all.append( x )
        y_all.append( y )
        t_all.append( t )
        t +=dt
        i += 1
        
        
ax.set_title("Raw Track Data, Uncorrelated")
ax.set_xlabel("Long [ref only]")
ax.set_ylabel("Lat [ref only]")
ax.set_xlim([-1,2])
ax.set_ylim([-3,3])
ax.scatter(0.75,-0.5,50,color = 'r', marker="^",label="TB1 Asset")
ax.legend(loc='best')

bucket = pd.DataFrame({ 't': t_all,
                        'x': x_all,
                        'y': y_all 
                      })
bucket = bucket.sort_values(by='t')

for i,row in bucket.iterrows():
    x = row['x']
    y = row['y']
    t = row['t']
    thisContact = OptMdasArpaContact( t )
    newARPA = associateARPA( thisContact )
    if newARPA:
        ARPAs.append( newARPA )
    plt.pause(0.4)
    ax.scatter( row['x'], row['y'], 10, marker = 's', label = '__nolegend__' )
    
plt.show()


