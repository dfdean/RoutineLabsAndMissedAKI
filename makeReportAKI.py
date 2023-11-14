#!/usr/bin/python3
################################################################################
# 
# Copyright (c) 2022-2023 Dawson Dean
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
################################################################################
#
# Analyze and Make Graphs for Detecting AKI with Missing Labs
#
# Ahem. A word about global variables....
# This program is designed to be run separately for each percentage chance of skipping
# a lab. For example, I run it once for 10% chance, then change some parameters, run it
# again for 20% and so on. As a result, some global variables are redefined on each run.
# They may have misleading names, suggesting they are only for the baseline or something
# else. This is unfortunate, and poor coding style. The code was written to do a single
# experiment, morphed a lot as the experiment was tuned, and then set aside. As a result,
# it is not re-usable well-crafted code. It generates the numbers for a specific paper,
# and let's then not ever use it again.
#
# For example, the following globals are set once each time the program is run.
#   g_TotalAKIAllYears, g_TotalAKI1AllYears, g_TotalAKI2AllYears, g_TotalAKI3AllYears
#   g_TotalNumLabsConsidered, g_TotalNumLabsSkipped, g_TotalNumLabsPerformed
# Their value reflects the current probabilities.
################################################################################
import os
import sys
import time
from datetime import datetime
import random

g_libDirPath = "/home/ddean/ddRoot/lib"
g_srcTDFFilePath = "/home/ddean/dLargeData/mlData/UKData/UKHC_4942/UKDailyLabsBloodLossMissedAKI.tdf"
g_WorkbookRootDir = "/home/ddean/ddRoot/AKIWithDailyLabs/"

# Allow import to pull from the per-user lib directory.
#print("g_libDirPath = " + g_libDirPath)
if g_libDirPath not in sys.path:
    sys.path.insert(0, g_libDirPath)

from xmlTools import *
from tdfTools import *
from dataShow import *
import elixhauser as Elixhauser

random.seed(3)

MIN_GFR_FOR_NON_ESRD = 20

g_TotalNumPatients = 0
g_TotalNumAdmissionsAllYears = 0
g_TotalNumESRDAdmissions = 0
g_TotalNumNonESRDAdmissionsAllYears = 0

# Hospital stays
g_TotalDaysInHospital = 0
g_TotalNonESRDDaysInHospital = 0
g_TotalVirtDaysInHospital = 0

# Total AKIs (max 1 per admission)
g_TotalAKIAllYears = 0
g_TotalAKI1AllYears = 0
g_TotalAKI2AllYears = 0
g_TotalAKI3AllYears = 0
g_TotalAKIOnAdmissionAllYears = 0
g_TotalAKI1OnAdmissionAllYears = 0
g_TotalAKI2OnAdmissionAllYears = 0
g_TotalAKI3OnAdmissionAllYears = 0

# Num AKIs per patient 
g_TotalNumPatientsWithAKI = 0

# Elixhauser
g_AllPatientsComorbidityGroup = None
g_AKI1ComorbidityGroup = None
g_AKI2ComorbidityGroup = None
g_AKI3ComorbidityGroup = None
g_CKDComorbidityGroup = None

g_OnDiureticsAtAKI = 0
g_OnVancAtAKI = 0
g_OnACEARBAtAKI = 0
g_OnNSAIDAtAKI = 0
g_OnTacCsaAtAKI = 0
g_OnPamidAtAKI = 0
g_OnChemoAtAKI = 0

g_TotalVirtualDays = 0
g_NumVirtualAdmissions = 0

MAX_NUM_SKIPPED_DAYS = 20
g_DayNumOfAKI = [0] * MAX_NUM_SKIPPED_DAYS
g_DayNumOfAKI1 = [0] * MAX_NUM_SKIPPED_DAYS
g_DayNumOfAKI2 = [0] * MAX_NUM_SKIPPED_DAYS
g_DayNumOfAKI3 = [0] * MAX_NUM_SKIPPED_DAYS
g_NumPtsWithConsecutiveSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS

g_NumAKI0AfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS
g_NumAKI1AfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS
g_NumAKI2AfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS
g_NumAKI3AfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS

g_NumAKI0OnCKDAfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS
g_NumAKI1OnCKDAfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS
g_NumAKI2OnCKDAfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS
g_NumAKI3OnCKDAfterSkippedDays = [0] * MAX_NUM_SKIPPED_DAYS

g_TotalNumLabsConsidered = 0
g_TotalNumLabsChecked = 0
g_TotalNumLabsSkipped = 0
g_TotalNumLabsPerformed = 0

NUM_BASELINE_CR_BUCKETS = 20
INCREMENT_PER_CR_BUCKET = 0.25
g_BaselineCrBeforeAKI = [0] * NUM_BASELINE_CR_BUCKETS

g_NumDaysSkippedXAxis = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
g_NumDaysSkippedXAxisString = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']


######################################################################################
# These are collected from running this code with all labs.
######################################################################################

#############################
# Baseline Variables for Future Tests:
g_BaselineALLNumNonESRDAdmissions = 43683
g_BaselineTotalDaysInHospital = 398359
g_BaselineFractionAnyAKIAllYears = 0.1816
g_BaselineFractionAKI1AllYears = 0.1274
g_BaselineFractionAKI2AllYears = 0.0359
g_BaselineFractionAKI3AllYears = 0.0183
g_BaselineTotalNumLabsChecked = 127953
g_BaselineTotalAKIAllYears = 7935
g_BaselineTotalAKI1AllYears = 5566
g_BaselineTotalAKI2AllYears = 1568
g_BaselineTotalAKI3AllYears = 801


#############################
# Gold Standard
g_GoldStandardListOfAKIFractions = [0.1945, 0.1445, 0.0363, 0.0137]
g_GoldStandardALLNumNonESRDAnyAKI = 2162
g_GoldStandardALLNumNonESRDNoAKI = 8954
g_GoldStandardALLNumNonESRDAKI1 = 1606
g_GoldStandardALLNumNonESRDAKI2 = 404
g_GoldStandardALLNumNonESRDAKI3 = 152
g_GoldStandardALLFractionNonESRDAnyAKI = 0.1945
g_GoldStandardALLFractionNonESRDAKI1 = 0.1445
g_GoldStandardALLFractionNonESRDAKI2 = 0.0363
g_GoldStandardALLFractionNonESRDAKI3 = 0.0137


######################################
# All Admissions

#10PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered10PercentRandom = 91758
g_NumLabsSkipped10PercentRandom = 9244
g_NumAKI10PercentRandom = [1869, 1390, 353, 126]
g_NumPtsWithConsecutiveSkippedDays10PercentRandom = [36546, 1878, 109, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI10PercentRandom = [0.1935, 0.1439, 0.0366, 0.013]
g_SensitivityAnyAKI10PercentRandom = 0.8645
g_SensitivityAKI110PercentRandom = 0.8655
g_SensitivityAKI210PercentRandom = 0.8738
g_SensitivityAKI310PercentRandom = 0.8289

#20PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered20PercentRandom = 91758
g_NumLabsSkipped20PercentRandom = 18456
g_NumAKI20PercentRandom = [1551, 1151, 293, 107]
g_NumPtsWithConsecutiveSkippedDays20PercentRandom = [28677, 2918, 336, 23, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI20PercentRandom = [0.1896, 0.1407, 0.0358, 0.0131]
g_SensitivityAnyAKI20PercentRandom = 0.7174
g_SensitivityAKI120PercentRandom = 0.7167
g_SensitivityAKI220PercentRandom = 0.7252
g_SensitivityAKI320PercentRandom = 0.7039

#30PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered30PercentRandom = 91758
g_NumLabsSkipped30PercentRandom = 27617
g_NumAKI30PercentRandom = [1254, 939, 230, 85]
g_NumPtsWithConsecutiveSkippedDays30PercentRandom = [21720, 3333, 578, 73, 16, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI30PercentRandom = [0.1858, 0.1391, 0.0341, 0.0126]
g_SensitivityAnyAKI30PercentRandom = 0.58
g_SensitivityAKI130PercentRandom = 0.5847
g_SensitivityAKI230PercentRandom = 0.5693
g_SensitivityAKI330PercentRandom = 0.5592

#40PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered40PercentRandom = 91758
g_NumLabsSkipped40PercentRandom = 36828
g_NumAKI40PercentRandom = [960, 720, 179, 61]
g_NumPtsWithConsecutiveSkippedDays40PercentRandom = [15904, 3190, 737, 152, 28, 14, 7, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI40PercentRandom = [0.1779, 0.1334, 0.0332, 0.0113]
g_SensitivityAnyAKI40PercentRandom = 0.444
g_SensitivityAKI140PercentRandom = 0.4483
g_SensitivityAKI240PercentRandom = 0.4431
g_SensitivityAKI340PercentRandom = 0.4013

#50PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered50PercentRandom = 91758
g_NumLabsSkipped50PercentRandom = 46069
g_NumAKI50PercentRandom = [702, 528, 135, 39]
g_NumPtsWithConsecutiveSkippedDays50PercentRandom = [10868, 2702, 802, 211, 51, 18, 15, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI50PercentRandom = [0.1735, 0.1305, 0.0334, 0.0096]
g_SensitivityAnyAKI50PercentRandom = 0.3247
g_SensitivityAKI150PercentRandom = 0.3288
g_SensitivityAKI250PercentRandom = 0.3342
g_SensitivityAKI350PercentRandom = 0.2566

#60PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered60PercentRandom = 91758
g_NumLabsSkipped60PercentRandom = 55158
g_NumAKI60PercentRandom = [482, 372, 87, 23]
g_NumPtsWithConsecutiveSkippedDays60PercentRandom = [6799, 2045, 724, 234, 77, 24, 13, 8, 1, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI60PercentRandom = [0.1712, 0.1321, 0.0309, 0.0082]
g_SensitivityAnyAKI60PercentRandom = 0.2229
g_SensitivityAKI160PercentRandom = 0.2316
g_SensitivityAKI260PercentRandom = 0.2153
g_SensitivityAKI360PercentRandom = 0.1513

#70PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered70PercentRandom = 91758
g_NumLabsSkipped70PercentRandom = 64307
g_NumAKI70PercentRandom = [315, 253, 55, 7]
g_NumPtsWithConsecutiveSkippedDays70PercentRandom = [3766, 1421, 526, 232, 95, 39, 18, 12, 4, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI70PercentRandom = [0.1754, 0.1409, 0.0306, 0.0039]
g_SensitivityAnyAKI70PercentRandom = 0.1457
g_SensitivityAKI170PercentRandom = 0.1575
g_SensitivityAKI270PercentRandom = 0.1361
g_SensitivityAKI370PercentRandom = 0.0461

#80PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered80PercentRandom = 91758
g_NumLabsSkipped80PercentRandom = 73480
g_NumAKI80PercentRandom = [162, 128, 30, 4]
g_NumPtsWithConsecutiveSkippedDays80PercentRandom = [1555, 683, 294, 151, 71, 25, 23, 13, 7, 2, 4, 2, 0, 2, 0, 0, 0, 0, 0, 0]
g_FractionAKI80PercentRandom = [0.189, 0.1494, 0.035, 0.0047]
g_SensitivityAnyAKI80PercentRandom = 0.0749
g_SensitivityAKI180PercentRandom = 0.0797
g_SensitivityAKI280PercentRandom = 0.0743
g_SensitivityAKI380PercentRandom = 0.0263

#90PercentRandomVariables. (COPY THESE INTO THE CODE)
g_NumLabsConsidered90PercentRandom = 91758
g_NumLabsSkipped90PercentRandom = 82788
g_NumAKI90PercentRandom = [42, 36, 6, 0]
g_NumPtsWithConsecutiveSkippedDays90PercentRandom = [365, 190, 92, 59, 26, 19, 10, 13, 2, 4, 0, 1, 0, 2, 0, 0, 0, 0, 0, 1]
g_FractionAKI90PercentRandom = [0.1707, 0.1463, 0.0244, 0.0]
g_SensitivityAnyAKI90PercentRandom = 0.0194
g_SensitivityAKI190PercentRandom = 0.0224
g_SensitivityAKI290PercentRandom = 0.0149
g_SensitivityAKI390PercentRandom = 0.0



######################################
# ONLY LONG Admissions

g_LongAdmissionGoldStandardListOfAKIFractions = [0.1392, 0.1186, 0.0173, 0.0033]
g_LongAdmissionGoldStandardALLNumNonESRDAnyAKI = 209
g_LongAdmissionGoldStandardALLNumNonESRDNoAKI = 1292
g_LongAdmissionGoldStandardALLNumNonESRDAKI1 = 178
g_LongAdmissionGoldStandardALLNumNonESRDAKI2 = 26
g_LongAdmissionGoldStandardALLNumNonESRDAKI3 = 5
g_LongAdmissionGoldStandardALLFractionNonESRDAnyAKI = 0.1392
g_LongAdmissionGoldStandardALLFractionNonESRDAKI1 = 0.1186
g_LongAdmissionGoldStandardALLFractionNonESRDAKI2 = 0.0173
g_LongAdmissionGoldStandardALLFractionNonESRDAKI3 = 0.0033

#10PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered10PercentRandom = 10350
g_LongAdmissionNumLabsSkipped10PercentRandom = 1019
g_LongAdmissionNumAKI10PercentRandom = [181, 157, 19, 5]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays10PercentRandom = [5614, 321, 23, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI10PercentRandom = [0.1347, 0.1168, 0.0141, 0.0037]
g_LongAdmissionSensitivityAnyAKI10PercentRandom = 0.866
g_LongAdmissionSensitivityAKI110PercentRandom = 0.882
g_LongAdmissionSensitivityAKI210PercentRandom = 0.7308
g_LongAdmissionSensitivityAKI310PercentRandom = 1.0

#20PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered20PercentRandom = 10350
g_LongAdmissionNumLabsSkipped20PercentRandom = 2007
g_LongAdmissionNumAKI20PercentRandom = [156, 137, 15, 4]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays20PercentRandom = [4489, 526, 54, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI20PercentRandom = [0.1322, 0.1161, 0.0127, 0.0034]
g_LongAdmissionSensitivityAnyAKI20PercentRandom = 0.7464
g_LongAdmissionSensitivityAKI120PercentRandom = 0.7697
g_LongAdmissionSensitivityAKI220PercentRandom = 0.5769
g_LongAdmissionSensitivityAKI320PercentRandom = 0.8

#30PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered30PercentRandom = 10350
g_LongAdmissionNumLabsSkipped30PercentRandom = 3080
g_LongAdmissionNumAKI30PercentRandom = [131, 113, 15, 3]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays30PercentRandom = [3433, 593, 128, 22, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI30PercentRandom = [0.1314, 0.1133, 0.015, 0.003]
g_LongAdmissionSensitivityAnyAKI30PercentRandom = 0.6268
g_LongAdmissionSensitivityAKI130PercentRandom = 0.6348
g_LongAdmissionSensitivityAKI230PercentRandom = 0.5769
g_LongAdmissionSensitivityAKI330PercentRandom = 0.6

#40PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered40PercentRandom = 10350
g_LongAdmissionNumLabsSkipped40PercentRandom = 4193
g_LongAdmissionNumAKI40PercentRandom = [106, 93, 11, 2]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays40PercentRandom = [2468, 596, 160, 35, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI40PercentRandom = [0.1312, 0.1151, 0.0136, 0.0025]
g_LongAdmissionSensitivityAnyAKI40PercentRandom = 0.5072
g_LongAdmissionSensitivityAKI140PercentRandom = 0.5225
g_LongAdmissionSensitivityAKI240PercentRandom = 0.4231
g_LongAdmissionSensitivityAKI340PercentRandom = 0.4

#50PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered50PercentRandom = 10350
g_LongAdmissionNumLabsSkipped50PercentRandom = 5237
g_LongAdmissionNumAKI50PercentRandom = [84, 75, 8, 1]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays50PercentRandom = [1694, 525, 171, 40, 15, 8, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI50PercentRandom = [0.134, 0.1196, 0.0128, 0.0016]
g_LongAdmissionSensitivityAnyAKI50PercentRandom = 0.4019
g_LongAdmissionSensitivityAKI150PercentRandom = 0.4213
g_LongAdmissionSensitivityAKI250PercentRandom = 0.3077
g_LongAdmissionSensitivityAKI350PercentRandom = 0.2

#60PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered60PercentRandom = 10350
g_LongAdmissionNumLabsSkipped60PercentRandom = 6257
g_LongAdmissionNumAKI60PercentRandom = [60, 55, 4, 1]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays60PercentRandom = [1134, 401, 151, 51, 20, 12, 2, 5, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI60PercentRandom = [0.1274, 0.1168, 0.0085, 0.0021]
g_LongAdmissionSensitivityAnyAKI60PercentRandom = 0.2871
g_LongAdmissionSensitivityAKI160PercentRandom = 0.309
g_LongAdmissionSensitivityAKI260PercentRandom = 0.1538
g_LongAdmissionSensitivityAKI360PercentRandom = 0.2

#70PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered70PercentRandom = 10350
g_LongAdmissionNumLabsSkipped70PercentRandom = 7247
g_LongAdmissionNumAKI70PercentRandom = [42, 38, 3, 1]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays70PercentRandom = [640, 296, 126, 52, 25, 17, 7, 5, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI70PercentRandom = [0.1284, 0.1162, 0.0092, 0.0031]
g_LongAdmissionSensitivityAnyAKI70PercentRandom = 0.201
g_LongAdmissionSensitivityAKI170PercentRandom = 0.2135
g_LongAdmissionSensitivityAKI270PercentRandom = 0.1154
g_LongAdmissionSensitivityAKI370PercentRandom = 0.2

#80PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered80PercentRandom = 10350
g_LongAdmissionNumLabsSkipped80PercentRandom = 8235
g_LongAdmissionNumAKI80PercentRandom = [23, 20, 2, 1]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays80PercentRandom = [301, 178, 101, 32, 20, 18, 11, 4, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI80PercentRandom = [0.115, 0.1, 0.01, 0.005]
g_LongAdmissionSensitivityAnyAKI80PercentRandom = 0.11
g_LongAdmissionSensitivityAKI180PercentRandom = 0.1124
g_LongAdmissionSensitivityAKI280PercentRandom = 0.0769
g_LongAdmissionSensitivityAKI380PercentRandom = 0.2

#90PercentRandomVariables. (COPY THESE INTO THE CODE)
g_LongAdmissionNumLabsConsidered90PercentRandom = 10350
g_LongAdmissionNumLabsSkipped90PercentRandom = 9302
g_LongAdmissionNumAKI90PercentRandom = [8, 6, 1, 1]
g_LongAdmissionNumPtsWithConsecutiveSkippedDays90PercentRandom = [79, 35, 22, 14, 2, 18, 5, 6, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0]
g_LongAdmissionFractionAKI90PercentRandom = [0.1379, 0.1034, 0.0172, 0.0172]
g_LongAdmissionSensitivityAnyAKI90PercentRandom = 0.0383
g_LongAdmissionSensitivityAKI190PercentRandom = 0.0337
g_LongAdmissionSensitivityAKI290PercentRandom = 0.0385
g_LongAdmissionSensitivityAKI390PercentRandom = 0.2


######################################
# ONLY BandSkipping

#10Percent Variables for BandSkipping:
g_NumLabsConsidered10PercentBandSkipping = 91758
g_NumLabsSkipped10PercentBandSkipping = 3435
g_NumAKI10PercentBandSkipping = [1956, 1433, 376, 147]
g_NumPtsWithConsecutiveSkippedDays10PercentBandSkipping = [39477, 56, 719, 55, 7, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI10PercentBandSkipping = [0.1916, 0.1403, 0.0368, 0.0144]
g_SensitivityAnyAKI10PercentBandSkipping = 0.9047
g_SensitivityAKI110PercentBandSkipping = 0.8923
g_SensitivityAKI210PercentBandSkipping = 0.9307
g_SensitivityAKI310PercentBandSkipping = 0.9671

#20Percent Variables for BandSkipping:
g_NumLabsConsidered20PercentBandSkipping = 91758
g_NumLabsSkipped20PercentBandSkipping = 6429
g_NumAKI20PercentBandSkipping = [1774, 1273, 356, 145]
g_NumPtsWithConsecutiveSkippedDays20PercentBandSkipping = [34225, 97, 1310, 142, 28, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI20PercentBandSkipping = [0.189, 0.1356, 0.0379, 0.0154]
g_SensitivityAnyAKI20PercentBandSkipping = 0.8205
g_SensitivityAKI120PercentBandSkipping = 0.7927
g_SensitivityAKI220PercentBandSkipping = 0.8812
g_SensitivityAKI320PercentBandSkipping = 0.9539

#30Percent Variables for BandSkipping:
g_NumLabsConsidered30PercentBandSkipping = 91758
g_NumLabsSkipped30PercentBandSkipping = 9054
g_NumAKI30PercentBandSkipping = [1634, 1169, 325, 140]
g_NumPtsWithConsecutiveSkippedDays30PercentBandSkipping = [29369, 139, 1742, 195, 50, 6, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI30PercentBandSkipping = [0.1921, 0.1374, 0.0382, 0.0165]
g_SensitivityAnyAKI30PercentBandSkipping = 0.7558
g_SensitivityAKI130PercentBandSkipping = 0.7279
g_SensitivityAKI230PercentBandSkipping = 0.8045
g_SensitivityAKI330PercentBandSkipping = 0.9211

#40Percent Variables for BandSkipping:
g_NumLabsConsidered40PercentBandSkipping = 91758
g_NumLabsSkipped40PercentBandSkipping = 11507
g_NumAKI40PercentBandSkipping = [1480, 1051, 299, 130]
g_NumPtsWithConsecutiveSkippedDays40PercentBandSkipping = [24837, 131, 2260, 263, 71, 18, 4, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI40PercentBandSkipping = [0.1924, 0.1367, 0.0389, 0.0169]
g_SensitivityAnyAKI40PercentBandSkipping = 0.6846
g_SensitivityAKI140PercentBandSkipping = 0.6544
g_SensitivityAKI240PercentBandSkipping = 0.7401
g_SensitivityAKI340PercentBandSkipping = 0.8553

#50Percent Variables for BandSkipping:
g_NumLabsConsidered50PercentBandSkipping = 91758
g_NumLabsSkipped50PercentBandSkipping = 13583
g_NumAKI50PercentBandSkipping = [1317, 915, 277, 125]
g_NumPtsWithConsecutiveSkippedDays50PercentBandSkipping = [20597, 138, 2670, 317, 84, 16, 2, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI50PercentBandSkipping = [0.1941, 0.1349, 0.0408, 0.0184]
g_SensitivityAnyAKI50PercentBandSkipping = 0.6092
g_SensitivityAKI150PercentBandSkipping = 0.5697
g_SensitivityAKI250PercentBandSkipping = 0.6856
g_SensitivityAKI350PercentBandSkipping = 0.8224

#60Percent Variables for BandSkipping:
g_NumLabsConsidered60PercentBandSkipping = 91758
g_NumLabsSkipped60PercentBandSkipping = 15356
g_NumAKI60PercentBandSkipping = [1196, 824, 244, 128]
g_NumPtsWithConsecutiveSkippedDays60PercentBandSkipping = [16715, 123, 2983, 409, 83, 27, 7, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI60PercentBandSkipping = [0.2022, 0.1393, 0.0412, 0.0216]
g_SensitivityAnyAKI60PercentBandSkipping = 0.5532
g_SensitivityAKI160PercentBandSkipping = 0.5131
g_SensitivityAKI260PercentBandSkipping = 0.604
g_SensitivityAKI360PercentBandSkipping = 0.8421

#70Percent Variables for BandSkipping:
g_NumLabsConsidered70PercentBandSkipping = 91758
g_NumLabsSkipped70PercentBandSkipping = 16905
g_NumAKI70PercentBandSkipping = [1067, 704, 244, 119]
g_NumPtsWithConsecutiveSkippedDays70PercentBandSkipping = [13238, 115, 3280, 492, 112, 20, 9, 5, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI70PercentBandSkipping = [0.2086, 0.1377, 0.0477, 0.0233]
g_SensitivityAnyAKI70PercentBandSkipping = 0.4935
g_SensitivityAKI170PercentBandSkipping = 0.4384
g_SensitivityAKI270PercentBandSkipping = 0.604
g_SensitivityAKI370PercentBandSkipping = 0.7829

#80Percent Variables for BandSkipping:
g_NumLabsConsidered80PercentBandSkipping = 91758
g_NumLabsSkipped80PercentBandSkipping = 18395
g_NumAKI80PercentBandSkipping = [927, 571, 241, 115]
g_NumPtsWithConsecutiveSkippedDays80PercentBandSkipping = [9794, 103, 3555, 520, 124, 28, 12, 7, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI80PercentBandSkipping = [0.218, 0.1343, 0.0567, 0.027]
g_SensitivityAnyAKI80PercentBandSkipping = 0.4288
g_SensitivityAKI180PercentBandSkipping = 0.3555
g_SensitivityAKI280PercentBandSkipping = 0.5965
g_SensitivityAKI380PercentBandSkipping = 0.7566

#90Percent Variables for BandSkipping:
g_NumLabsConsidered90PercentBandSkipping = 91758
g_NumLabsSkipped90PercentBandSkipping = 19759
g_NumAKI90PercentBandSkipping = [812, 476, 224, 112]
g_NumPtsWithConsecutiveSkippedDays90PercentBandSkipping = [6453, 87, 3791, 573, 136, 35, 14, 7, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
g_FractionAKI90PercentBandSkipping = [0.2395, 0.1404, 0.0661, 0.033]
g_SensitivityAnyAKI90PercentBandSkipping = 0.3756
g_SensitivityAKI190PercentBandSkipping = 0.2964
g_SensitivityAKI290PercentBandSkipping = 0.5545
g_SensitivityAKI390PercentBandSkipping = 0.7368


########################
g_SensitivityListForAllAKI = [g_SensitivityAnyAKI10PercentRandom, g_SensitivityAnyAKI20PercentRandom, g_SensitivityAnyAKI30PercentRandom, g_SensitivityAnyAKI40PercentRandom, g_SensitivityAnyAKI50PercentRandom, g_SensitivityAnyAKI60PercentRandom, g_SensitivityAnyAKI70PercentRandom, g_SensitivityAnyAKI80PercentRandom, g_SensitivityAnyAKI90PercentRandom]

g_SensitivityListForAKI1 = [g_SensitivityAKI110PercentRandom, g_SensitivityAKI120PercentRandom, g_SensitivityAKI130PercentRandom, g_SensitivityAKI140PercentRandom, g_SensitivityAKI150PercentRandom, g_SensitivityAKI160PercentRandom, g_SensitivityAKI170PercentRandom, g_SensitivityAKI180PercentRandom, g_SensitivityAKI190PercentRandom]

g_SensitivityListForAKI2 = [g_SensitivityAKI210PercentRandom, g_SensitivityAKI220PercentRandom, g_SensitivityAKI230PercentRandom, g_SensitivityAKI240PercentRandom, g_SensitivityAKI250PercentRandom, g_SensitivityAKI260PercentRandom, g_SensitivityAKI270PercentRandom, g_SensitivityAKI280PercentRandom, g_SensitivityAKI290PercentRandom]

g_SensitivityListForAKI3 = [g_SensitivityAKI310PercentRandom, g_SensitivityAKI320PercentRandom, g_SensitivityAKI330PercentRandom, g_SensitivityAKI340PercentRandom, g_SensitivityAKI350PercentRandom, g_SensitivityAKI360PercentRandom, g_SensitivityAKI370PercentRandom, g_SensitivityAKI380PercentRandom, g_SensitivityAKI390PercentRandom]

######################################################################
INCLUDE_ADDITIVE_CRITERIA_FOR_AKI = True
MAX_CR_FOR_ADDITIVE_CRITERIA_FOR_AKI = 1.7

########################
# Make Virtual Admissions.
# VIRTUAL_ADMISSIONS_ONLY should be combined with either COMPUTE_GOLD_STANDARD or RANDOM_CHANCE_OF_SKIP or SUMMARIZE_RANDOM or SKIP_ELEMENTS_IF_IN_BAND
MIN_NUMBER_DAYS_FOR_SIMULATE_SKIPPING = 3

########################
UPPER_BAND_DISTANCE_FROM_AVG = 1.3
LOWER_BAND_DISTANCE_FROM_AVG = 0.7
MIN_SEQ_LENGTH_FOR_BAND = 2
g_NumValuesToSkipInBollinger = 1


g_TotalCSVFileOutput = ""


################################################################################
#
# [ProcessOneLabValue]
#
################################################################################
def ProcessOneLabValue(valueFloat, numDaysSkipped, lowestCrIn48Hrs, lowestCrInAdmission, fIsCKD, medList):
    global MAX_NUM_SKIPPED_DAYS
    global g_NumPtsWithConsecutiveSkippedDays
    global g_NumAKI0AfterSkippedDays
    global g_NumAKI1AfterSkippedDays
    global g_NumAKI2AfterSkippedDays
    global g_NumAKI3AfterSkippedDays
    global g_NumAKI0OnCKDAfterSkippedDays
    global g_NumAKI1OnCKDAfterSkippedDays
    global g_NumAKI2OnCKDAfterSkippedDays
    global g_NumAKI3OnCKDAfterSkippedDays

    # From "2012 Kidney Disease: Improving Global Outcomes (KDIGO) Clinical Practice Guideline for Acute Kidney Injury (AKI)", 
    #   Kidney International Supplements (2012) 2, iv
    # AKI is defined as any of the following (Not Graded):
    #   Increase in SCr by X0.3 mg/dl (X26.5 lmol/l) within 48 hours; or
    #   Increase in SCr to X1.5 times baseline, which is known or presumed to have occurred within the prior 7 days; or
    #   Urine volume o0.5 ml/kg/h for 6 hours
    akin1Threshold = 1.5 * lowestCrInAdmission
    akin2Threshold = 2.0 * lowestCrInAdmission
    akin3Threshold = 3.0 * lowestCrInAdmission
    if ((INCLUDE_ADDITIVE_CRITERIA_FOR_AKI) and (lowestCrIn48Hrs <= MAX_CR_FOR_ADDITIVE_CRITERIA_FOR_AKI)):
        akin1aThreshold = lowestCrIn48Hrs + 0.3
    else:
        akin1aThreshold = akin1Threshold

    akiGrade = 0
    if (valueFloat >= akin3Threshold):
        akiGrade = 3
    elif (valueFloat >= akin2Threshold):
        akiGrade = 2
    elif (valueFloat >= akin1Threshold):
        akiGrade = 1
    elif ((lowestCrIn48Hrs > 0) and (valueFloat >= akin1aThreshold)):
        akiGrade = 1

    if (numDaysSkipped >= MAX_NUM_SKIPPED_DAYS):
        numDaysSkipped = MAX_NUM_SKIPPED_DAYS - 1

    g_NumPtsWithConsecutiveSkippedDays[numDaysSkipped] += 1

    ##################################
    if (akiGrade == 0):
        g_NumAKI0AfterSkippedDays[numDaysSkipped] += 1
        if (fIsCKD):
            g_NumAKI0OnCKDAfterSkippedDays[numDaysSkipped] += 1
    elif (akiGrade == 1):
        g_NumAKI1AfterSkippedDays[numDaysSkipped] += 1
        if (fIsCKD):
            g_NumAKI1OnCKDAfterSkippedDays[numDaysSkipped] += 1
    elif (akiGrade == 2):
        g_NumAKI2AfterSkippedDays[numDaysSkipped] += 1
        if (fIsCKD):
            g_NumAKI2OnCKDAfterSkippedDays[numDaysSkipped] += 1
    elif (akiGrade == 3):
        g_NumAKI3AfterSkippedDays[numDaysSkipped] += 1
        if (fIsCKD):
            g_NumAKI3OnCKDAfterSkippedDays[numDaysSkipped] += 1


    return akiGrade
# End - ProcessOneLabValue





################################################################################
#
# [RecordOneAKI]
#
################################################################################
def RecordOneAKI(akiGrade, baselineCr, medList, akiDayNum):
    global g_TotalNumNonESRDAdmissionsAllYears
    global g_TotalAKIAllYears
    global g_TotalAKI1AllYears
    global g_TotalAKI2AllYears
    global g_TotalAKI3AllYears
    global g_OnDiureticsAtAKI
    global g_OnVancAtAKI
    global g_OnACEARBAtAKI
    global g_OnNSAIDAtAKI
    global g_OnTacCsaAtAKI
    global g_OnPamidAtAKI
    global g_OnChemoAtAKI
    global g_DayNumOfAKI
    global g_DayNumOfAKI1
    global g_DayNumOfAKI2
    global g_DayNumOfAKI3

    if (akiGrade <= 0):
        return

    g_TotalAKIAllYears += 1
    if (akiGrade == 3):
        g_TotalAKI3AllYears += 1
    elif (akiGrade == 2):
        g_TotalAKI2AllYears += 1
    elif (akiGrade == 1):
        g_TotalAKI1AllYears += 1

    bucketNum = int(baselineCr / INCREMENT_PER_CR_BUCKET)
    if (bucketNum >= NUM_BASELINE_CR_BUCKETS):
        bucketNum = NUM_BASELINE_CR_BUCKETS - 1
    g_BaselineCrBeforeAKI[bucketNum] += 1

    # Record when this happened.
    if (akiDayNum >= MAX_NUM_SKIPPED_DAYS):
        akiDayNum = MAX_NUM_SKIPPED_DAYS - 1
    g_DayNumOfAKI[akiDayNum] += 1
    if (akiGrade == 3):
        g_DayNumOfAKI3[akiDayNum] += 1
    elif (akiGrade == 2):
        g_DayNumOfAKI2[akiDayNum] += 1
    elif (akiGrade == 1):
        g_DayNumOfAKI1[akiDayNum] += 1


    if (("FurosIV" in medList) or ("Furos" in medList) or ("Tors" in medList) or ("Bumet" in medList) 
            or ("Spiro" in medList) or ("Chlorthal" in medList)):
        g_OnDiureticsAtAKI += 1
    if ("Vanc" in medList):
        g_OnVancAtAKI += 1
    if (("Lisin" in medList) or ("Enalapril" in medList) or ("Losar" in medList) or ("Valsar" in medList)):
        g_OnACEARBAtAKI += 1
    if (("Ibup" in medList) or ("Ketor" in medList) or ("Naprox" in medList) or ("Diclof" in medList)):
        g_OnNSAIDAtAKI += 1
    if (("Tac" in medList) or ("CsA" in medList)):
        g_OnTacCsaAtAKI += 1
    if (("Pamid" in medList)):
        g_OnPamidAtAKI += 1
    if (("Cisplat" in medList) or ("Tenof" in medList) or ("MTX" in medList)):
        g_OnChemoAtAKI += 1
# End - RecordOneAKI








################################################################################
#
# [ExamineLabList]
#
################################################################################
def ExamineLabList(eventList, medList, fIsCKD, diagnosisList):
    global g_TotalNumNonESRDAdmissionsAllYears
    global g_TotalNumLabsChecked
    global g_TotalAKIOnAdmissionAllYears
    global g_TotalAKI1OnAdmissionAllYears
    global g_TotalAKI2OnAdmissionAllYears
    global g_TotalAKI3OnAdmissionAllYears
    global g_AllPatientsComorbidityGroup
    global g_AKI1ComorbidityGroup
    global g_AKI2ComorbidityGroup
    global g_AKI3ComorbidityGroup
    global g_CKDComorbidityGroup

    g_TotalNumNonESRDAdmissionsAllYears += 1
    g_AllPatientsComorbidityGroup.AddDiagnosisList(diagnosisList)

    # Count the first value.
    if (len(eventList) > 0):
        g_TotalNumLabsChecked += 1

    # Now, iterate through each event
    lowestCrInAdmission = -1
    firstCrInAdmission = -1
    fHavePreviousValue = False
    previousDayNum = -1
    previousValue = -1
    twoDayPrevValue = -1
    lowestCrInSequence = -1
    highestAKIGradeInSequence = 0
    firstDayOfAdmission = -1
    for eventInfo in eventList:
        dayNum = eventInfo["Day"]
        valueFloat = eventInfo["Val"]

        if (firstDayOfAdmission == -1):
            firstDayOfAdmission = dayNum
        if (firstCrInAdmission == -1):
            firstCrInAdmission = valueFloat

        dayNumInCurrentAdmission = dayNum - firstDayOfAdmission
        #print("dayNumInCurrentAdmission = " + str(dayNumInCurrentAdmission))

        if ((fHavePreviousValue) and (dayNum != previousDayNum)):
            numDaysSkipped = (dayNum - previousDayNum) - 1

            g_TotalNumLabsChecked += 1
            if ((lowestCrInAdmission == -1) or (valueFloat < lowestCrInAdmission)):
                lowestCrInAdmission = valueFloat
            if ((lowestCrInSequence == -1) or (valueFloat < lowestCrInSequence)):
                lowestCrInSequence = valueFloat

            lowestCrIn48Hrs = previousValue
            if ((twoDayPrevValue > 0) and (twoDayPrevValue < lowestCrIn48Hrs)):
                lowestCrIn48Hrs = twoDayPrevValue

            currentAKIGrade = ProcessOneLabValue(valueFloat, numDaysSkipped, lowestCrIn48Hrs, 
                                                 lowestCrInSequence, fIsCKD, medList)

            # If a Cr rises to AKIN1 then to AKIN2 then to AKIN3, we just count the AKIN3.
            # So, only record the highest grade AKI.
            if (currentAKIGrade > highestAKIGradeInSequence):
                highestAKIGradeInSequence = currentAKIGrade
            # If we peaked, and then are coming down, then record that AKI and reset the state
            # so after this recovery we can find a second AKI
            elif ((currentAKIGrade < highestAKIGradeInSequence) and (highestAKIGradeInSequence > 0)):
                # If this is the peak of the admission AKI, then do not count it.
                # We will count the admitting AKI at the end of the admission, after we have
                # found the final baseline Cr
                if (lowestCrInSequence != firstCrInAdmission):
                    RecordOneAKI(highestAKIGradeInSequence, lowestCrInSequence, medList, 
                                 dayNumInCurrentAdmission)
                # End - if (lowestCrInSequence != firstCrInAdmission):

                # Reset the state so we can find a second AKI on the same admission.
                previousValue = -1
                highestAKIGradeInSequence = 0
                lowestCrInSequence = -1    
            # End - elif ((currentAKIGrade < highestAKIGradeInSequence) and (highestAKIGradeInSequence > 0)):
        # End - if (fHavePreviousValue):

        fHavePreviousValue = True
        previousDayNum = dayNum
        twoDayPrevValue = previousValue
        previousValue = valueFloat
    # End - for eventInfo in eventList:

    # Finish the AKI we were tracking. It may never have resolved, for example if a patient dies or
    # leaves AMA.
    if (highestAKIGradeInSequence > 0):
        RecordOneAKI(highestAKIGradeInSequence, lowestCrInSequence, medList, 
                    dayNumInCurrentAdmission)

    # Check if there was an AKI on admission.
    # This is a bit like doing a film effect by filming a structure crumbling and then
    # playing the film backwards so the structure seems to assemble.
    # We look for an AKI on admission by looking for a recovery back to the old baseline,
    # then pretending it went in the reverse order.
    if ((firstCrInAdmission != -1) and (lowestCrInAdmission != -1)):
        currentAKIGrade = ProcessOneLabValue(firstCrInAdmission, numDaysSkipped, firstCrInAdmission, 
                                             lowestCrInAdmission, fIsCKD, medList)
        if (currentAKIGrade > 0):
            RecordOneAKI(currentAKIGrade, lowestCrInAdmission, medList, 0)
            g_TotalAKIOnAdmissionAllYears += 1
            if (currentAKIGrade == 3):
                g_TotalAKI3OnAdmissionAllYears += 1
                g_AKI3ComorbidityGroup.AddDiagnosisList(diagnosisList)
            elif (currentAKIGrade == 2):
                g_TotalAKI2OnAdmissionAllYears += 1
                g_AKI2ComorbidityGroup.AddDiagnosisList(diagnosisList)
            elif (currentAKIGrade == 1):
                g_TotalAKI1OnAdmissionAllYears += 1
                g_AKI1ComorbidityGroup.AddDiagnosisList(diagnosisList)
        # End - if (currentAKIGrade > 0)
    # if ((firstCrInAdmission != -1) and (lowestCrInAdmission != -1)):
# End - ExamineLabList







################################################################################
#
# [FilterLabList]
#
# This implements virtual admissions. It calls ExamineLabList() for each virtual
# admission.
################################################################################
def FilterLabList(eventList, fRandomSkips, fBandSkips, randomChanceOfSkip, 
                    medList, fIsCKD, diagnosisList,
                    firstDayInt, vitrualAdmissionStartsAfterNDaysInHospital):
    global g_TotalNumLabsConsidered
    global g_TotalNumLabsSkipped
    global g_TotalNumLabsPerformed
    global g_TotalVirtualDays
    global g_NumVirtualAdmissions
    global g_TotalVirtDaysInHospital
    global g_NumValuesToSkipInBollinger

    currentEventList = []
    previousDayNum = -1
    numValuesInSeq = 0
    sumOfValuesInSeq = 0
    latestPreviousValue = -1
    fSkipNextNValues = 0
    fAlwaysUseValue = False
    g_NumValuesToSkipInBollinger = 1
    for eventInfo in eventList:
        dayNum = eventInfo["Day"]
        valueFloat = eventInfo["Val"]

        if (vitrualAdmissionStartsAfterNDaysInHospital > 0):
            daysInHospital = dayNum - firstDayInt
            if (daysInHospital < vitrualAdmissionStartsAfterNDaysInHospital):
                continue

        # If this extends a current sublist, then add it.
        if ((previousDayNum == -1) or ((previousDayNum + 1) == dayNum)):
            g_TotalVirtualDays += 1

            # However, we must first decide whether to add an item
            fIncludeDay = True

            ################################
            if (fSkipNextNValues > 0):
                fIncludeDay = False
                fSkipNextNValues = fSkipNextNValues - 1
                # If we finish skipping a series of values, then always take the next value
                # Once you start skipping, the Band stops collecting latest values, so the next decision
                # will still be based on the old stable value and will reach the same conclusion.
                # Don't skip too many in a row or 1 stable period will prevent you from checking ever again.
                if (fSkipNextNValues <= 0):
                    fAlwaysUseValue = True
            ################################
            elif (fAlwaysUseValue):
                fIncludeDay = True
                fAlwaysUseValue = False
            ################################
            # Random skips
            elif ((fRandomSkips) and (random.random() < randomChanceOfSkip)):
                fIncludeDay = False
            ################################
            # Bollinger-Band like skips
            elif ((fBandSkips) 
                    and (numValuesInSeq >= MIN_SEQ_LENGTH_FOR_BAND) 
                    and (latestPreviousValue > 0)):
                avgVal = float(sumOfValuesInSeq / numValuesInSeq)
                upperBand = avgVal * UPPER_BAND_DISTANCE_FROM_AVG
                lowerBand = avgVal * LOWER_BAND_DISTANCE_FROM_AVG
                if ((latestPreviousValue >= lowerBand) 
                        and (latestPreviousValue <= upperBand) 
                        and (random.random() < randomChanceOfSkip)):
                    fSkipNextNValues = g_NumValuesToSkipInBollinger
                    g_NumValuesToSkipInBollinger += 1
                    fIncludeDay = False
                # End - if ((latestPreviousValue >= lowerBand) and (latestPreviousValue <= upperBand)):
            # End - if (fBandSkips)


            g_TotalNumLabsConsidered += 1
            if (fIncludeDay):
                g_TotalNumLabsPerformed += 1
                numValuesInSeq += 1
                sumOfValuesInSeq += valueFloat
                latestPreviousValue = valueFloat
                currentEventList.append(eventInfo)
            else:
                g_TotalNumLabsSkipped += 1
        else:
            # Otherwise, we have skipped a day, so have ended a series of contiguous days.
            # Process the sub-list we have so far
            if (len(currentEventList) >= MIN_NUMBER_DAYS_FOR_SIMULATE_SKIPPING):
                g_NumVirtualAdmissions += 1
                g_TotalVirtDaysInHospital += len(currentEventList)
                ExamineLabList(currentEventList, medList, fIsCKD, diagnosisList)

            # Now, start a new sub-list
            currentEventList = []
            currentEventList.append(eventInfo)
            numValuesInSeq = 1
            sumOfValuesInSeq = valueFloat
            latestPreviousValue = valueFloat
        # End - Finishing one sequence and starting the next

        previousDayNum = dayNum
    # End - for eventInfo in eventList:

    # Process any sub-list we were building when we hit the end of the main list
    if (len(currentEventList) >= MIN_NUMBER_DAYS_FOR_SIMULATE_SKIPPING):
        g_NumVirtualAdmissions += 1
        g_TotalVirtDaysInHospital += len(currentEventList)
        ExamineLabList(currentEventList, medList, fIsCKD, diagnosisList)
# End - FilterLabList






################################################################################
#
# [FindAKIInfo]
#
################################################################################
def FindAKIInfo(srcFilePathName, fVirtualAdmissions, fRandomSkips, fBandSkips, 
                randomChanceOfSkip, vitrualAdmissionStartsAfterNDaysInHospital):
    global g_TotalNumPatients
    global g_TotalNumESRDAdmissions
    global g_TotalNumAdmissionsAllYears
    global g_TotalDaysInHospital
    global g_TotalNonESRDDaysInHospital
    global g_TotalNumPatientsWithAKI
    global g_AllPatientsComorbidityGroup
    global g_AKI1ComorbidityGroup
    global g_AKI2ComorbidityGroup
    global g_AKI3ComorbidityGroup
    global g_CKDComorbidityGroup

    # Create and Initialize the Comorbidity groups
    g_AllPatientsComorbidityGroup = Elixhauser.ElixhauserGroup()
    g_AKI1ComorbidityGroup = Elixhauser.ElixhauserGroup()
    g_AKI2ComorbidityGroup = Elixhauser.ElixhauserGroup()
    g_AKI3ComorbidityGroup = Elixhauser.ElixhauserGroup()
    g_CKDComorbidityGroup = Elixhauser.ElixhauserGroup()

    g_AKI1ComorbidityGroup.TrackAdditionalComorbidity("AKI")
    g_AKI2ComorbidityGroup.TrackAdditionalComorbidity("AKI")
    g_AKI3ComorbidityGroup.TrackAdditionalComorbidity("AKI")
    g_AKI1ComorbidityGroup.TrackAdditionalComorbidity("AKIEx")
    g_AKI2ComorbidityGroup.TrackAdditionalComorbidity("AKIEx")
    g_AKI3ComorbidityGroup.TrackAdditionalComorbidity("AKIEx")
    g_CKDComorbidityGroup.TrackAdditionalComorbidity("CKD")



    MIN_INTERVAL_BETWEEN_DATA_POINTS_IN_HOURS = 1

    srcTDF = TDF_CreateTDFFileReader(srcFilePathName, "Cr;GFR", "", [])
    srcTDF.SetTimeResolution(1)
    srcTDF.SetCarryForwardPreviousDataValues(False)

    # Iterate over every patient
    fFoundPatient = srcTDF.GotoFirstPatient()
    while (fFoundPatient):
        g_TotalNumPatients += 1
        saveNumAKIsBeforePatient = g_TotalAKIAllYears

        # Get a list of all admissions.
        admissionList = srcTDF.GetAdmissionsForCurrentPatient()
        for admissionInfo in admissionList:
            firstDay = admissionInfo['FirstDay']
            lastDay = admissionInfo['LastDay']
            team = admissionInfo['Team']
            admitClass = admissionInfo['AdmitClass']
            medList = admissionInfo['Meds']

            # Get all data points for the patient.
            firstDayInt = int(firstDay)
            lastDayInt = int(lastDay)

            lengthOfStay = (lastDayInt - firstDayInt) + 1
            g_TotalDaysInHospital += lengthOfStay

            # Check if the patient looks like a dialysis patient.
            gfrEventList = srcTDF.GetValuesBetweenDays("GFR", firstDayInt, lastDayInt, True)
            fIsDialysisPatient = True
            highestGFR = -1
            for eventInfo in gfrEventList:
                valueFloat = eventInfo["Val"]

                # A bad AKI may cause GFR to drop to 15 or lower for a brief period before rebounding.
                # However, a dialysis patient will never have a decent GFR, even after a run.
                # If a patient never has a GFR over 20, then they are a dialysis patient.
                if (valueFloat >= MIN_GFR_FOR_NON_ESRD):
                    fIsDialysisPatient = False
                    # Don't stop looking, we still need to see the highest GFR

                if ((highestGFR < 0) or (valueFloat >= highestGFR)):
                    highestGFR = valueFloat
            # End - for eventInfo in gfrEventList:

            g_TotalNumAdmissionsAllYears += 1

            # If this is a dialysis patient, then ignore all future admissions
            if (fIsDialysisPatient):
                g_TotalNumESRDAdmissions += 1
                # Skip this admission.
                # Do not give up on the patient - they may return for a future admission 
                # after a transplant or recovery.
                continue

            g_TotalNonESRDDaysInHospital += lengthOfStay

            #################################
            # Diagnoses. These are used for Elixhauser stats
            diagnosisList = srcTDF.GetDiagnosesForCurrentPatient(firstDay, lastDay)
            g_AllPatientsComorbidityGroup.AddDiagnosisList(diagnosisList)

            if (highestGFR < 60):
                fIsCKD = True
                g_CKDComorbidityGroup.AddDiagnosisList(diagnosisList)
            else:
                fIsCKD = False

            saveNumAKIsBeforeAdmission = g_TotalAKIAllYears
            crEventList = srcTDF.GetValuesBetweenDays("Cr", firstDayInt, lastDayInt, True)

            if (fVirtualAdmissions):
                FilterLabList(crEventList, fRandomSkips, fBandSkips, randomChanceOfSkip, 
                                medList, fIsCKD, diagnosisList,
                                firstDayInt, vitrualAdmissionStartsAfterNDaysInHospital)
            else:
                ExamineLabList(crEventList, medList, fIsCKD, diagnosisList)
            
            if (saveNumAKIsBeforePatient != g_TotalAKIAllYears):
                g_TotalNumPatientsWithAKI += 1
        # End - for admissionInfo in admissionList:

        fFoundPatient = srcTDF.GotoNextPatient()
    # End - while (patientNode):
# End - FindAKIInfo




################################################################################
#
# RecordNumberResult
#
################################################################################
def RecordNumberResult(captionStr, singleValue):
    global g_TotalCSVFileOutput

    g_TotalCSVFileOutput = g_TotalCSVFileOutput + captionStr + "," + str(singleValue) + "\n"
    print(captionStr + ": " + str(singleValue))
# End - RecordNumberResult



################################################################################
#
# RecordVectorResult
#
################################################################################
def RecordVectorResult(captionStr, valueList):
    global g_TotalCSVFileOutput

    newLineStr = ""
    for value in valueList:
        newLineStr = newLineStr + str(value) + ","

    # Remove the comma at the end.
    if (newLineStr != ""):
        newLineStr = newLineStr[:-1]

    g_TotalCSVFileOutput = g_TotalCSVFileOutput + captionStr + "," + newLineStr + "\n"
    print(captionStr + ": " + str(valueList))
# End - RecordVectorResult



################################################################################
#
# [WriteCSVFile]
#
################################################################################
def WriteCSVFile(filePathName):
    global g_TotalCSVFileOutput

    if (g_TotalCSVFileOutput == ""):
        return

    fileH = open(filePathName, "w+")
    fileH.write(g_TotalCSVFileOutput)
    fileH.close()
# End - WriteCSVFile



################################################################################
#
# [ComputeBaseline]
#
# Report Results for Baseline AKI
# This is all patients, with whatever labs were drawn.
################################################################################
def ComputeBaseline(filePathName):
    fRandomSkips = False
    fBandSkips = False
    randomChanceOfSkip = 0
    FindAKIInfo(filePathName, False, fRandomSkips, fBandSkips, randomChanceOfSkip, 0)

    reportDirectoryPath = g_WorkbookRootDir + "AllPatients/"

    ##################################
    # Number of Patients
    RecordNumberResult("Num Patients (including ESRD)", g_TotalNumPatients)
    RecordNumberResult("Num Admissions All Years", g_TotalNumAdmissionsAllYears)
    RecordNumberResult("Num ESRD Admissions All Years", g_TotalNumESRDAdmissions)
    RecordNumberResult("Num Non-ESRD Admissions All Years", g_TotalNumNonESRDAdmissionsAllYears)

    RecordNumberResult("Num Hospital Days for ALL Admissions", g_TotalDaysInHospital)
    RecordNumberResult("Num Hospital Days for Non-ESRD Admissions", g_TotalNonESRDDaysInHospital)
    RecordNumberResult("Num Days with Cr Checked for Non-ESRD Admissions (all years)", g_TotalNumLabsChecked)
    fractionDaysWithCr = round(float(g_TotalNumLabsChecked / g_TotalNonESRDDaysInHospital), 4)
    RecordNumberResult("Fraction of Hospital Days with non-ESRD pt and a Cr checked (all years)", fractionDaysWithCr)

    ##################################
    # Number of Patients with AKI
    RecordNumberResult("Total Patients on a Non-ESRD Admission with at least 1 AKI", g_TotalNumPatientsWithAKI)
    RecordNumberResult("Num Non-ESRD Admissions with any AKI All Years", g_TotalAKIAllYears)
    RecordNumberResult("Num Non-ESRD Admissions with AKI-1 All Years", g_TotalAKI1AllYears)
    RecordNumberResult("Num Non-ESRD Admissions with AKI-2 All Years", g_TotalAKI2AllYears)
    RecordNumberResult("Num Non-ESRD Admissions with AKI-3 All Years", g_TotalAKI3AllYears)

    fractionAnyAKIAllYears = round((g_TotalAKIAllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI1AllYears = round((g_TotalAKI1AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI2AllYears = round((g_TotalAKI2AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI3AllYears = round((g_TotalAKI3AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    RecordNumberResult("Fraction Non-ESRD Admissions with Any AKI All Years", fractionAnyAKIAllYears)
    RecordNumberResult("Fraction Non-ESRD Admissions with AKI 1 All Years", fractionAKI1AllYears)
    RecordNumberResult("Fraction Non-ESRD Admissions with AKI 2 All Years", fractionAKI2AllYears)
    RecordNumberResult("Fraction Non-ESRD Admissions with AKI 3 All Years", fractionAKI3AllYears)

    RecordNumberResult("Num Non-ESRD Admissions with any AKI At Admission All Years", g_TotalAKIOnAdmissionAllYears)
    RecordNumberResult("Num Non-ESRD Admissions with AKI-1 At Admission All Years", g_TotalAKI1OnAdmissionAllYears)
    RecordNumberResult("Num Non-ESRD Admissions with AKI-2 At Admission All Years", g_TotalAKI2OnAdmissionAllYears)
    RecordNumberResult("Num Non-ESRD Admissions with AKI-3 At Admission All Years", g_TotalAKI3OnAdmissionAllYears)

    fractionAnyAKIPOAAllYears = round((g_TotalAKIOnAdmissionAllYears / g_TotalAKIAllYears), 4)
    fractionAKI1POAAllYears = round((g_TotalAKI1OnAdmissionAllYears / g_TotalAKI1AllYears), 4)
    fractionAKI2POAAllYears = round((g_TotalAKI2OnAdmissionAllYears / g_TotalAKI2AllYears), 4)
    fractionAKI3POAAllYears = round((g_TotalAKI3OnAdmissionAllYears / g_TotalAKI3AllYears), 4)
    RecordNumberResult("Fraction Non-ESRD Admissions with Any AKI On Admission All Years", fractionAnyAKIPOAAllYears)
    RecordNumberResult("Fraction Non-ESRD Admissions with AKI 1 On Admission All Years", fractionAKI1POAAllYears)
    RecordNumberResult("Fraction Non-ESRD Admissions with AKI 2 On Admission All Years", fractionAKI2POAAllYears)
    RecordNumberResult("Fraction Non-ESRD Admissions with AKI 3 On Admission All Years", fractionAKI3POAAllYears)

    numIatrogenicAnyAKIAllYears = g_TotalAKIAllYears - g_TotalAKIOnAdmissionAllYears
    numIatrogenicAKI1AllYears = g_TotalAKI1AllYears - g_TotalAKI1OnAdmissionAllYears
    numIatrogenicAKI2AllYears = g_TotalAKI2AllYears - g_TotalAKI2OnAdmissionAllYears
    numIatrogenicAKI3AllYears = g_TotalAKI3AllYears - g_TotalAKI3OnAdmissionAllYears
    RecordNumberResult("Num Iatrogenic Any AKI All Years", numIatrogenicAnyAKIAllYears)
    RecordNumberResult("Num Iatrogenic AKI 1 All Years", numIatrogenicAKI1AllYears)
    RecordNumberResult("Num Iatrogenic AKI 2 All Years", numIatrogenicAKI2AllYears)
    RecordNumberResult("Num Iatrogenic AKI 3 All Years", numIatrogenicAKI3AllYears)

    fractionIatrogenicAnyAKIAllYears = round((numIatrogenicAnyAKIAllYears / g_TotalAKIAllYears), 4)
    fractionIatrogenicAKI1AllYears = round((numIatrogenicAKI1AllYears / g_TotalAKI1AllYears), 4)
    fractionIatrogenicAKI2AllYears = round((numIatrogenicAKI2AllYears / g_TotalAKI2AllYears), 4)
    fractionIatrogenicAKI3AllYears = round((numIatrogenicAKI3AllYears / g_TotalAKI3AllYears), 4)
    RecordNumberResult("Fraction of Any AKI are Iatrogenic All Years", fractionIatrogenicAnyAKIAllYears)
    RecordNumberResult("Fraction of AKI 1 are Iatrogenic All Years", fractionIatrogenicAKI1AllYears)
    RecordNumberResult("Fraction of AKI 2 are Iatrogenic All Years", fractionIatrogenicAKI2AllYears)
    RecordNumberResult("Fraction of AKI 3 are Iatrogenic All Years", fractionIatrogenicAKI3AllYears)

    categoryList = ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3']
    DrawBarGraph("Fraction of Non-ESRD Admissions with AKI", 
                 "Non-ESRD Patients", ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3'], 
                 "Fraction of Admissions", [fractionAnyAKIAllYears, fractionAKI1AllYears, fractionAKI2AllYears, fractionAKI3AllYears],
                 False, reportDirectoryPath + "TotalFractionAKIByType.jpg")

    categoryList = ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3']
    DrawDoubleBarGraph("Fraction of Each Class of AKI that Happens Before And After Admission", 
                       "Non-ESRD Patients", categoryList, "Fraction of AKIs",
                       "Before Admission", 
                       [fractionAnyAKIPOAAllYears, fractionAKI1POAAllYears, fractionAKI2POAAllYears, fractionAKI3POAAllYears],
                       "After Admission", 
                       [fractionIatrogenicAnyAKIAllYears, fractionIatrogenicAKI1AllYears, fractionIatrogenicAKI2AllYears, fractionIatrogenicAKI3AllYears],
                       False, reportDirectoryPath + "AKIPOAvsIatrogenic.jpg")



    ##################################
    # Number of Consecutive Days Without Labs
    #RecordVectorResult("Num Consecutive Days without checking Creatinine", g_NumPtsWithConsecutiveSkippedDays)
    fractionSkippedDays = []
    for numLabs in g_NumPtsWithConsecutiveSkippedDays:
        fractionLabsWithCr = round(float(numLabs / g_TotalNumLabsChecked), 4)
        fractionSkippedDays.append(fractionLabsWithCr)
    DrawLineGraph("Fraction of Creatinine Labs After Consecutive Skipped Days", 
                  "Num Consecutive Days Skipped", g_NumDaysSkippedXAxis, 
                  "Fractions of Cr Labs", fractionSkippedDays, 
                  False, reportDirectoryPath + "FractionSkippedDaysLine.jpg")


    # Iatrogenic vs PoA AKI
    numIatrogenicAKIAll = sum(g_DayNumOfAKI) - g_DayNumOfAKI[0]
    numIatrogenicAKI1 = sum(g_DayNumOfAKI1) - g_DayNumOfAKI1[0]
    numIatrogenicAKI2 = sum(g_DayNumOfAKI2) - g_DayNumOfAKI2[0]
    numIatrogenicAKI3 = sum(g_DayNumOfAKI3) - g_DayNumOfAKI3[0]
    fractionOfAKIPerDay = [round((x / numIatrogenicAKIAll), 3) for x in g_DayNumOfAKI]
    fractionOfAKI1PerDay = [round((x / numIatrogenicAKI1), 3) for x in g_DayNumOfAKI1]
    fractionOfAKI2PerDay = [round((x / numIatrogenicAKI2), 3) for x in g_DayNumOfAKI2]
    fractionOfAKI3PerDay = [round((x / numIatrogenicAKI3), 3) for x in g_DayNumOfAKI3]
    fractionOfAKIPerDay[0] = 0
    fractionOfAKI1PerDay[0] = 0
    fractionOfAKI2PerDay[0] = 0
    fractionOfAKI3PerDay[0] = 0
    print("g_DayNumOfAKI = " + str(g_DayNumOfAKI))
    print("g_DayNumOfAKI1 = " + str(g_DayNumOfAKI1))
    print("g_DayNumOfAKI2 = " + str(g_DayNumOfAKI2))
    print("g_DayNumOfAKI3 = " + str(g_DayNumOfAKI3))
    print("fractionOfAKIPerDay = " + str(fractionOfAKIPerDay))
    print("fractionOfAKI1PerDay = " + str(fractionOfAKI1PerDay))
    print("fractionOfAKI2PerDay = " + str(fractionOfAKI2PerDay))
    print("fractionOfAKI3PerDay = " + str(fractionOfAKI3PerDay))
    DrawMultiLineGraph("Day Number When AKI Happens", 
                       "Day Number", g_NumDaysSkippedXAxis,
                       "Fraction of each AKI", 
                       ["All AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
                       [fractionOfAKIPerDay, fractionOfAKI1PerDay, fractionOfAKI2PerDay, fractionOfAKI3PerDay], 
                       False, reportDirectoryPath + "DayNumberOfAKILine.jpg")


    ##################################
    # Characterize Our AKIs
    fractionOfAKIsWithBaseline = [0] * NUM_BASELINE_CR_BUCKETS
    for index in range(NUM_BASELINE_CR_BUCKETS):
        if (g_BaselineCrBeforeAKI[index] > 0):
            fractionOfAKIsWithBaseline[index] = round(float(g_BaselineCrBeforeAKI[index]) / float(g_TotalAKIAllYears), 3)
    #RecordVectorResult("Number of AKI With Baseline Cr (in 0.25 increments) before AKI", g_BaselineCrBeforeAKI)
    #RecordVectorResult("Fraction Of AKIs With Baseline Cr (in 0.25 increments)", fractionOfAKIsWithBaseline)

    BaselineCrXLabelList = []
    for index in range(NUM_BASELINE_CR_BUCKETS):
        BaselineCrXLabelList.append(str(index * INCREMENT_PER_CR_BUCKET))

    DrawBarGraph("Baseline Cr before AKI as a Fraction of All AKIs", 
                 "Baseline Cr", BaselineCrXLabelList, 
                 "Fraction of AKIs", fractionOfAKIsWithBaseline, 
                 False, reportDirectoryPath + "BaselineCrBeforeAKI.jpg")


    RecordNumberResult("Number of AKI in Pt on Diuretic", g_OnDiureticsAtAKI)
    RecordNumberResult("Number of AKI in Pt on Vanc", g_OnVancAtAKI)
    RecordNumberResult("Number of AKI in Pt on ACE/ARB", g_OnACEARBAtAKI)
    RecordNumberResult("Number of AKI in Pt on NSAID", g_OnNSAIDAtAKI)
    RecordNumberResult("Number of AKI in Pt on Tac/Csa", g_OnTacCsaAtAKI)
    RecordNumberResult("Number of AKI in Pt on Pamidronate", g_OnPamidAtAKI)
    RecordNumberResult("Number of AKI in Pt on Chemo", g_OnChemoAtAKI)

    fractionAKIOnDiureticsAtAKI = round(float(g_OnDiureticsAtAKI / g_TotalAKIAllYears), 4)
    fractionAKIOnVancAtAKI = round(float(g_OnVancAtAKI / g_TotalAKIAllYears), 4)
    fractionAKIOnACEARBAtAKI = round(float(g_OnACEARBAtAKI / g_TotalAKIAllYears), 4)
    fractionAKIOnNSAIDAtAKI = round(float(g_OnNSAIDAtAKI / g_TotalAKIAllYears), 4)
    fractionAKIOnTacCsaAtAKI = round(float(g_OnTacCsaAtAKI / g_TotalAKIAllYears), 4)
    fractionAKIOnPamidAtAKI = round(float(g_OnPamidAtAKI / g_TotalAKIAllYears), 4)
    fractionAKIOnChemoAtAKI = round(float(g_OnChemoAtAKI / g_TotalAKIAllYears), 4)

    RecordNumberResult("Fraction of AKI in Pt on Diuretic", fractionAKIOnDiureticsAtAKI)
    RecordNumberResult("Fraction of AKI in Pt on Vanc", fractionAKIOnVancAtAKI)
    RecordNumberResult("Fraction of AKI in Pt on ACE/ARB", fractionAKIOnACEARBAtAKI)
    RecordNumberResult("Fraction of AKI in Pt on NSAID", fractionAKIOnNSAIDAtAKI)
    RecordNumberResult("Fraction of AKI in Pt on Tac/Csa", fractionAKIOnTacCsaAtAKI)
    RecordNumberResult("Fraction of AKI in Pt on Pamidronate", fractionAKIOnPamidAtAKI)
    RecordNumberResult("Fraction of AKI in Pt on Chemo", fractionAKIOnChemoAtAKI)

    DrawBarGraph("Fraction of AKIs on Known Nephrotoxins", 
                "Nephrotoxin", ["NSAID", "Vanc", "ACE/ARB", "Diuretic", "Tac/Csa", "Chemo", "Pamidronate"], 
                "Fraction of AKIs", [fractionAKIOnNSAIDAtAKI, fractionAKIOnVancAtAKI, fractionAKIOnACEARBAtAKI, fractionAKIOnDiureticsAtAKI, fractionAKIOnTacCsaAtAKI, fractionAKIOnChemoAtAKI, fractionAKIOnPamidAtAKI],                
                False, reportDirectoryPath + "FractionAKIsOnNephrotoxins.jpg")


    ##################################
    # Num Skipped Labs before AKIs
    #DrawMultiLineGraph("Num AKI After Consecutive Days without checking Creatinine", 
    #                   "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
    #                   "Num Patients", 
    #                   ["No AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
    #                   [g_NumAKI0AfterSkippedDays, g_NumAKI1AfterSkippedDays, g_NumAKI2AfterSkippedDays, g_NumAKI3AfterSkippedDays], 
    #                   False, reportDirectoryPath + "NumAKIvsNumSkippedDaysLine.jpg")
    fractionOfAKI1PerDay = [round((x / g_TotalAKI1AllYears), 3) for x in g_NumAKI1AfterSkippedDays]
    fractionOfAKI2PerDay = [round((x / g_TotalAKI2AllYears), 3) for x in g_NumAKI2AfterSkippedDays]
    fractionOfAKI3PerDay = [round((x / g_TotalAKI3AllYears), 3) for x in g_NumAKI3AfterSkippedDays]
    DrawMultiLineGraph("Fraction of AKI After N Consecutive Days without checking Creatinine", 
                        "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
                        "Num Patients", 
                        ["KDIGO 1", "KDIGO 2", "KDIGO 3"], 
                        [fractionOfAKI1PerDay, fractionOfAKI2PerDay, fractionOfAKI3PerDay], 
                        False, reportDirectoryPath + "FractionAKIvsNumSkippedDaysLine.jpg")


    ########################################
    # Print Elixhauser Stats
    ########################################
    # Print Elixhauser Stats
    print("\n\nElixhauser")
    print("==========================================")
    Elixhauser.PrintStatsForGroups(
        "Comorbidities of AKI",
        [g_AllPatientsComorbidityGroup, g_AKI1ComorbidityGroup, g_AKI2ComorbidityGroup, g_AKI3ComorbidityGroup],
        ["All Patients", "KDIGO 1", "KDIGO 2", "KDIGO 3"],
        reportDirectoryPath + "Comorbidities.csv")

    fractionCKDPtsWithCorrectDiagnosis = g_CKDComorbidityGroup.GetFractionPatientsWithComorbidity("CKD")
    fractionAKI1PtsWithCorrectDiagnosis = g_AKI1ComorbidityGroup.GetFractionPatientsWithComorbidity("AKI")
    fractionAKI2PtsWithCorrectDiagnosis = g_AKI2ComorbidityGroup.GetFractionPatientsWithComorbidity("AKI")
    fractionAKI3PtsWithCorrectDiagnosis = g_AKI3ComorbidityGroup.GetFractionPatientsWithComorbidity("AKI")
    fractionAKI1PtsWithCorrectExtendedDiagnosis = g_AKI1ComorbidityGroup.GetFractionPatientsWithComorbidity("AKIEx")
    fractionAKI2PtsWithCorrectExtendedDiagnosis = g_AKI2ComorbidityGroup.GetFractionPatientsWithComorbidity("AKIEx")
    fractionAKI3PtsWithCorrectExtendedDiagnosis = g_AKI3ComorbidityGroup.GetFractionPatientsWithComorbidity("AKIEx")
    print("\n\n")
    print("fraction CKDPts With CKD Diagnosis = " + str(fractionCKDPtsWithCorrectDiagnosis))
    print("fraction AKI1 Pts With AKI Diagnosis = " + str(fractionAKI1PtsWithCorrectDiagnosis))
    print("fraction AKI2 Pts With AKI Diagnosis = " + str(fractionAKI2PtsWithCorrectDiagnosis))
    print("fraction AKI3 Pts With AKI Diagnosis = " + str(fractionAKI3PtsWithCorrectDiagnosis))
    print("fraction AKI1 Pts With AKI Extended Diagnosis = " + str(fractionAKI1PtsWithCorrectExtendedDiagnosis))
    print("fraction AKI2 Pts With AKI Extended Diagnosis = " + str(fractionAKI2PtsWithCorrectExtendedDiagnosis))
    print("fraction AKI3 Pts With AKI Extended Diagnosis = " + str(fractionAKI3PtsWithCorrectExtendedDiagnosis))

    DrawBarGraph("Fraction of Patients with AKI that have Correct Elixhauser AKI Diagnoses", 
                        "Anemia", ["KDIGO 1", "KDIGO 2", "KDIGO 3"],
                        "Percent of Admissions", 
                        [fractionAKI1PtsWithCorrectDiagnosis * 100.0, 
                            fractionAKI2PtsWithCorrectDiagnosis * 100.0, 
                            fractionAKI3PtsWithCorrectDiagnosis * 100.0],
                        False, reportDirectoryPath + "FractionAdmissionsWithCorrectElixHauserDiagnoses.jpg")
    DrawBarGraph("Fraction of Patients with AKI that have Correct Extended AKI Diagnoses", 
                        "Anemia", ["KDIGO 1", "KDIGO 2", "KDIGO 3"],
                        "Percent of Admissions", 
                        [fractionAKI1PtsWithCorrectExtendedDiagnosis * 100.0, 
                            fractionAKI2PtsWithCorrectExtendedDiagnosis * 100.0, 
                            fractionAKI3PtsWithCorrectExtendedDiagnosis * 100.0],
                        False, reportDirectoryPath + "FractionAdmissionsWithCorrectExtendedDiagnoses.jpg")


    # These are collected from running this code with all labs.
    print("\n\n\n# Variables for Future Tests:")
    print("g_BaselineALLNumNonESRDAdmissions = " + str(g_TotalNumNonESRDAdmissionsAllYears))
    print("g_BaselineTotalDaysInHospital = " + str(g_TotalDaysInHospital))
    print("g_BaselineFractionAnyAKIAllYears = " + str(fractionAnyAKIAllYears))
    print("g_BaselineFractionAKI1AllYears = " + str(fractionAKI1AllYears))
    print("g_BaselineFractionAKI2AllYears = " + str(fractionAKI2AllYears))
    print("g_BaselineFractionAKI3AllYears = " + str(fractionAKI3AllYears))
    print("g_BaselineTotalNumLabsChecked = " + str(g_TotalNumLabsChecked))
    print("g_BaselineTotalAKIAllYears = " + str(g_TotalAKIAllYears))
    print("g_BaselineTotalAKI1AllYears = " + str(g_TotalAKI1AllYears))
    print("g_BaselineTotalAKI2AllYears = " + str(g_TotalAKI2AllYears))
    print("g_BaselineTotalAKI3AllYears = " + str(g_TotalAKI3AllYears))
# End - ComputeBaseline







################################################################################
#
# [ComputeCostVariables]
#
################################################################################
def ComputeCostVariables(filePathName):
    totalNumPatients = 0
    totalNumAdmissions = 0
    totalNumHgb = 0
    totalNumCr = 0

    MIN_INTERVAL_BETWEEN_DATA_POINTS_IN_HOURS = 1
    srcTDF = TDF_CreateTDFFileReader(filePathName, "Cr;GFR;Hgb", "", [])
    srcTDF.SetTimeResolution(1)
    srcTDF.SetCarryForwardPreviousDataValues(False)

    # Iterate over every patient
    fFoundPatient = srcTDF.GotoFirstPatient()
    while (fFoundPatient):
        totalNumPatients += 1

        # Get a list of all admissions.
        admissionList = srcTDF.GetAdmissionsForCurrentPatient()
        for admissionInfo in admissionList:
            # Get all data points for the patient.
            firstDay = admissionInfo['FirstDay']
            lastDay = admissionInfo['LastDay']
            firstDayInt = int(firstDay)
            lastDayInt = int(lastDay)

            # Check if the patient looks like a dialysis patient.
            gfrEventList = srcTDF.GetValuesBetweenDays("GFR", firstDayInt, lastDayInt, False)
            fIsDialysisPatient = True
            for eventInfo in gfrEventList:
                valueFloat = eventInfo["Val"]
                if (valueFloat >= MIN_GFR_FOR_NON_ESRD):
                    fIsDialysisPatient = False
            # End - for eventInfo in gfrEventList:

            if (fIsDialysisPatient):
                continue
            totalNumAdmissions += 1

            # Count the Hgb
            hgbEventList = srcTDF.GetValuesBetweenDays("Hgb", firstDayInt, lastDayInt, False)
            for eventInfo in hgbEventList:
                valueFloat = eventInfo["Val"]
                if (valueFloat > 0):
                    totalNumHgb += 1
            # End - for eventInfo in hgbEventList:

            # Count the Cr
            crEventList = srcTDF.GetValuesBetweenDays("Cr", firstDayInt, lastDayInt, False)
            for eventInfo in crEventList:
                valueFloat = eventInfo["Val"]
                if (valueFloat > 0):
                    totalNumCr += 1
            # End - for eventInfo in crEventList:

        fFoundPatient = srcTDF.GotoNextPatient()
    # End - while (patientNode):


    print("total Num Patients = " + str(totalNumPatients))
    print("total Num Admissions = " + str(totalNumAdmissions))
    print("total Num Hgb = " + str(totalNumHgb))
    print("total Num Cr = " + str(totalNumCr))
    print("Avg Hgb Per Year = " + str(totalNumHgb / 5))
    print("Avg Cr Per Year = " + str(totalNumCr / 5))
# End - ComputeCostVariables






################################################################################
#
# [PrintJavaScriptArrays]
#
################################################################################
def PrintJavaScriptArrays():
    declStr = ""
    for sensNum in g_SensitivityListForAllAKI:
        if (declStr != ""):
            declStr += ", "
        declStr += str(sensNum)
    # End - for sensNum in g_SensitivityListForAllAKI:
    print("const AllAKISensitivityWithRandomSkipsArray = [" + declStr + "];")

    declStr = ""
    for sensNum in g_SensitivityListForAKI1:
        if (declStr != ""):
            declStr += ", "
        declStr += str(sensNum)
    # End - for sensNum in g_SensitivityListForAKI1:
    print("const AKI1SensitivityWithRandomSkipsArray = [" + declStr + "];")

    declStr = ""
    for sensNum in g_SensitivityListForAKI2:
        if (declStr != ""):
            declStr += ", "
        declStr += str(sensNum)
    # End - for sensNum in g_SensitivityListForAKI2:
    print("const AKI2SensitivityWithRandomSkipsArray = [" + declStr + "];")

    declStr = ""
    for sensNum in g_SensitivityListForAKI3:
        if (declStr != ""):
            declStr += ", "
        declStr += str(sensNum)
    # End - for sensNum in g_SensitivityListForAKI3:
    print("const AKI3SensitivityWithRandomSkipsArray = [" + declStr + "];")
# End - PrintJavaScriptArrays






################################################################################
#
# [ComputeGoldStandardWithOnlyDailyLabs]
#
# Report Results for AKI when we ONLY take Daily Labs
# So, this is a restricted view, BUT it is the best case when we compute skipping strategies
################################################################################
def ComputeGoldStandardWithOnlyDailyLabs(filePathName, vitrualAdmissionStartsAfterNDaysInHospital):
    fRandomSkips = False
    fBandSkips = False
    randomChanceOfSkip = 0
    FindAKIInfo(filePathName, True, fRandomSkips, fBandSkips, randomChanceOfSkip, vitrualAdmissionStartsAfterNDaysInHospital)

    if (vitrualAdmissionStartsAfterNDaysInHospital > 0):
        reportDirectoryPath = g_WorkbookRootDir + "LongAdmissionGoldStandardDailyLabs/"
    else:
        reportDirectoryPath = g_WorkbookRootDir + "GoldStandardDailyLabs/"

    ##################################
    # Number of Patients
    RecordNumberResult("Num Virtual Non-ESRD Admissions All Years", g_TotalNumNonESRDAdmissionsAllYears)
    RecordNumberResult("Num Virtual Non-ESRD Admissions", g_NumVirtualAdmissions)
    RecordNumberResult("Num Virtual Non-ESRD Hospital Days", g_TotalVirtDaysInHospital)
    RecordNumberResult("Avg Virtual Length Of Stay", round((g_TotalVirtualDays / g_NumVirtualAdmissions), 4))

    ##################################
    # Number of Patients with AKI
    RecordNumberResult("Num Non-ESRD Patients with any AKI All Years", g_TotalAKIAllYears)
    RecordNumberResult("Num Non-ESRD Patients with AKI-1 All Years", g_TotalAKI1AllYears)
    RecordNumberResult("Num Non-ESRD Patients with AKI-2 All Years", g_TotalAKI2AllYears)
    RecordNumberResult("Num Non-ESRD Patients with AKI-3 All Years", g_TotalAKI3AllYears)

    # Note, this program is run separately for the baseline and also for each fraction of 
    # labs skipped. As a result, g_TotalNumLabsChecked is valid for whatever experiment this
    # is currently running. I know, poor design. 
    categoryList = ['Total Admissions', 'Total Hospital Days', 'Total Labs']
    allPatients = [g_BaselineALLNumNonESRDAdmissions, g_BaselineTotalDaysInHospital, g_BaselineTotalNumLabsChecked]
    dailyLabsPatients = [g_NumVirtualAdmissions, g_TotalVirtDaysInHospital, g_TotalNumLabsChecked]
    DrawDoubleBarGraph("Actual Admissions vs Virtual Admissions with Daily Labs", 
                       "Non-ESRD Patients", categoryList, "",
                       "Actual", allPatients, 
                       "Virtual w/ Daily Labs", dailyLabsPatients,
                       False, reportDirectoryPath + "ActualvsVirtualAdmissions.jpg")

    # g_TotalAKIAllYears is now computed to be only for Gold Standard, because I filter out any sections that do not have daily labs.
    print("")
    fractionAnyAKIAllYears = round(float(g_TotalAKIAllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI1AllYears = round(float(g_TotalAKI1AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI2AllYears = round(float(g_TotalAKI2AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI3AllYears = round(float(g_TotalAKI3AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    RecordNumberResult("Fraction of Non-ESRD Patients with any AKI All Years", fractionAnyAKIAllYears)
    RecordNumberResult("Fraction of Non-ESRD Patients with AKI-1 All Years", fractionAKI1AllYears)
    RecordNumberResult("Fraction of Non-ESRD Patients with AKI-2 All Years", fractionAKI2AllYears)
    RecordNumberResult("Fraction of Non-ESRD Patients with AKI-3 All Years", fractionAKI3AllYears)

    g_GoldStandardALLNumNonESRDAnyAKI = g_TotalAKIAllYears
    g_GoldStandardALLNumNonESRDNoAKI = g_TotalNumNonESRDAdmissionsAllYears - g_TotalAKIAllYears
    g_GoldStandardALLNumNonESRDAKI1 = g_TotalAKI1AllYears
    g_GoldStandardALLNumNonESRDAKI2 = g_TotalAKI2AllYears
    g_GoldStandardALLNumNonESRDAKI3 = g_TotalAKI3AllYears
    g_GoldStandardALLFractionNonESRDAnyAKI = fractionAnyAKIAllYears
    g_GoldStandardALLFractionNonESRDAKI1 = fractionAKI1AllYears
    g_GoldStandardALLFractionNonESRDAKI2 = fractionAKI2AllYears
    g_GoldStandardALLFractionNonESRDAKI3 = fractionAKI3AllYears

    GoldStandardListOfAKIFractions = [fractionAnyAKIAllYears, fractionAKI1AllYears, fractionAKI2AllYears, fractionAKI3AllYears]
    categoryList = ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3']
    allAdmissions = [g_BaselineFractionAnyAKIAllYears, g_BaselineFractionAKI1AllYears, g_BaselineFractionAKI2AllYears, g_BaselineFractionAKI3AllYears]
    virtualAdmissionsWithDailyLabs = [fractionAnyAKIAllYears, fractionAKI1AllYears, fractionAKI2AllYears, fractionAKI3AllYears]
    DrawDoubleBarGraph("Fraction of Patients With AKI from All Admissions vs Virtual Admissions with Daily Labs", 
                       "Non-ESRD Patients", categoryList, "Number of Patients", 
                       "All Admissions", allAdmissions, 
                       "Virtual Admissions With Daily Labs", virtualAdmissionsWithDailyLabs,
                       False, reportDirectoryPath + "FractionAKIFromAllvsVirtualAdmissions.jpg")


    ########################################
    # Print Elixhauser Stats
    ########################################
    # Print Elixhauser Stats
    print("\n\nElixhauser")
    print("==========================================")
    Elixhauser.PrintStatsForGroups(
        "Comorbidities of AKI",
        [g_AllPatientsComorbidityGroup, g_AKI1ComorbidityGroup, g_AKI2ComorbidityGroup, g_AKI3ComorbidityGroup],
        ["All Patients", "KDIGO 1", "KDIGO 2", "KDIGO 3"],
        reportDirectoryPath + "Comorbidities.csv")

    fractionCKDPtsWithCorrectDiagnosis = g_CKDComorbidityGroup.GetFractionPatientsWithComorbidity("CKD")
    fractionAKI1PtsWithCorrectDiagnosis = g_AKI1ComorbidityGroup.GetFractionPatientsWithComorbidity("AKI")
    fractionAKI2PtsWithCorrectDiagnosis = g_AKI2ComorbidityGroup.GetFractionPatientsWithComorbidity("AKI")
    fractionAKI3PtsWithCorrectDiagnosis = g_AKI3ComorbidityGroup.GetFractionPatientsWithComorbidity("AKI")
    fractionAKI1PtsWithCorrectExtendedDiagnosis = g_AKI1ComorbidityGroup.GetFractionPatientsWithComorbidity("AKIEx")
    fractionAKI2PtsWithCorrectExtendedDiagnosis = g_AKI2ComorbidityGroup.GetFractionPatientsWithComorbidity("AKIEx")
    fractionAKI3PtsWithCorrectExtendedDiagnosis = g_AKI3ComorbidityGroup.GetFractionPatientsWithComorbidity("AKIEx")
    print("\n\n")
    print("fraction CKDPts With CKD Diagnosis = " + str(fractionCKDPtsWithCorrectDiagnosis))
    print("fraction AKI1 Pts With AKI Diagnosis = " + str(fractionAKI1PtsWithCorrectDiagnosis))
    print("fraction AKI2 Pts With AKI Diagnosis = " + str(fractionAKI2PtsWithCorrectDiagnosis))
    print("fraction AKI3 Pts With AKI Diagnosis = " + str(fractionAKI3PtsWithCorrectDiagnosis))
    print("fraction AKI1 Pts With AKI Extended Diagnosis = " + str(fractionAKI1PtsWithCorrectExtendedDiagnosis))
    print("fraction AKI2 Pts With AKI Extended Diagnosis = " + str(fractionAKI2PtsWithCorrectExtendedDiagnosis))
    print("fraction AKI3 Pts With AKI Extended Diagnosis = " + str(fractionAKI3PtsWithCorrectExtendedDiagnosis))

    DrawBarGraph("Fraction of Patients with AKI that have Correct Elixhauser AKI Diagnoses", 
                        "Anemia", ["KDIGO 1", "KDIGO 2", "KDIGO 3"],
                        "Percent of Admissions", 
                        [fractionAKI1PtsWithCorrectDiagnosis * 100.0, 
                            fractionAKI2PtsWithCorrectDiagnosis * 100.0, 
                            fractionAKI3PtsWithCorrectDiagnosis * 100.0],
                        False, reportDirectoryPath + "FractionAdmissionsWithCorrectElixHauserDiagnoses.jpg")
    DrawBarGraph("Fraction of Patients with AKI that have Correct Extended AKI Diagnoses", 
                        "Anemia", ["KDIGO 1", "KDIGO 2", "KDIGO 3"],
                        "Percent of Admissions", 
                        [fractionAKI1PtsWithCorrectExtendedDiagnosis * 100.0, 
                            fractionAKI2PtsWithCorrectExtendedDiagnosis * 100.0, 
                            fractionAKI3PtsWithCorrectExtendedDiagnosis * 100.0],
                        False, reportDirectoryPath + "FractionAdmissionsWithCorrectExtendedDiagnoses.jpg")

    # These are collected from running this code with all labs.
    if (vitrualAdmissionStartsAfterNDaysInHospital > 0):
        prefixStr = "LongAdmission"
    else:
        prefixStr = ""
    print("\n\n\n# Variables for Future Tests: (COPY THESE INTO THE CODE)")
    print("g_" + prefixStr + "GoldStandardListOfAKIFractions = " + str(GoldStandardListOfAKIFractions))
    print("g_" + prefixStr + "GoldStandardALLNumNonESRDAnyAKI = " + str(g_GoldStandardALLNumNonESRDAnyAKI))
    print("g_" + prefixStr + "GoldStandardALLNumNonESRDNoAKI = " + str(g_GoldStandardALLNumNonESRDNoAKI))
    print("g_" + prefixStr + "GoldStandardALLNumNonESRDAKI1 = " + str(g_GoldStandardALLNumNonESRDAKI1))
    print("g_" + prefixStr + "GoldStandardALLNumNonESRDAKI2 = " + str(g_GoldStandardALLNumNonESRDAKI2))
    print("g_" + prefixStr + "GoldStandardALLNumNonESRDAKI3 = " + str(g_GoldStandardALLNumNonESRDAKI3))
    print("g_" + prefixStr + "GoldStandardALLFractionNonESRDAnyAKI = " + str(g_GoldStandardALLFractionNonESRDAnyAKI))
    print("g_" + prefixStr + "GoldStandardALLFractionNonESRDAKI1 = " + str(g_GoldStandardALLFractionNonESRDAKI1))
    print("g_" + prefixStr + "GoldStandardALLFractionNonESRDAKI2 = " + str(g_GoldStandardALLFractionNonESRDAKI2))
    print("g_" + prefixStr + "GoldStandardALLFractionNonESRDAKI3 = " + str(g_GoldStandardALLFractionNonESRDAKI3))
# End - ComputeGoldStandardWithOnlyDailyLabs






################################################################################
#
# [FindAKIWithRandomSkips]
#
# Report Results for AKI when we ONLY take Daily Labs but we Randomly ignore labs
################################################################################
def FindAKIWithRandomSkips(filePathName, randomChanceOfSkip, fLongAdmissionsOnly):
    if (fLongAdmissionsOnly):
        reportDirectoryPath = g_WorkbookRootDir + "LongAdmissionRandomSkips/"
    else:
        reportDirectoryPath = g_WorkbookRootDir + "RandomSkips/"

    testResultIndex = int(randomChanceOfSkip * 10)
    testResultPercentSuffix = str(testResultIndex) + "0PercentRandom"
    if (fLongAdmissionsOnly):
        testResultPercentPrefix = "LongAdmissionSkipping" + str(testResultIndex) + "0PercentRandom"
    else:
        testResultPercentPrefix = "Skipping" + str(testResultIndex) + "0PercentRandom"

    fRandomSkips = True
    fBandSkips = False
    if (fLongAdmissionsOnly):
            vitrualAdmissionStartsAfterNDaysInHospital = 14
    else:
        vitrualAdmissionStartsAfterNDaysInHospital = 0

    # This will assign g_TotalAKIAllYears, g_TotalAKI1AllYears, g_TotalAKI2AllYears, g_TotalAKI3AllYears
    FindAKIInfo(filePathName, True, fRandomSkips, fBandSkips, randomChanceOfSkip, vitrualAdmissionStartsAfterNDaysInHospital)

    print("\n============ Skipping " + testResultPercentSuffix)
    ##################################
    # Basic Test Characteristics
    RecordNumberResult(testResultPercentPrefix + "Total Num Labs Considered", g_TotalNumLabsConsidered)
    RecordNumberResult(testResultPercentPrefix + "Total Num Labs Skipped", g_TotalNumLabsSkipped)
    RecordNumberResult(testResultPercentPrefix + "Total Num Labs Performed", g_TotalNumLabsPerformed)

    ##################################
    # Number of Patients with AKI
    RecordNumberResult(testResultPercentPrefix + "Num Non-ESRD Patients with any AKI All Years", g_TotalAKIAllYears)
    RecordNumberResult(testResultPercentPrefix + "Num Non-ESRD Patients with AKI-1 All Years", g_TotalAKI1AllYears)
    RecordNumberResult(testResultPercentPrefix + "Num Non-ESRD Patients with AKI-2 All Years", g_TotalAKI2AllYears)
    RecordNumberResult(testResultPercentPrefix + "Num Non-ESRD Patients with AKI-3 All Years", g_TotalAKI3AllYears)

    fractionAnyAKIAllYears = round(float(g_TotalAKIAllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI1AllYears = round(float(g_TotalAKI1AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI2AllYears = round(float(g_TotalAKI2AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI3AllYears = round(float(g_TotalAKI3AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    print("")
    RecordNumberResult(testResultPercentPrefix + "Fraction of Non-ESRD Patients with any AKI All Years", fractionAnyAKIAllYears)
    RecordNumberResult(testResultPercentPrefix + "Fraction of Non-ESRD Patients with AKI-1 All Years", fractionAKI1AllYears)
    RecordNumberResult(testResultPercentPrefix + "Fraction of Non-ESRD Patients with AKI-2 All Years", fractionAKI2AllYears)
    RecordNumberResult(testResultPercentPrefix + "Fraction of Non-ESRD Patients with AKI-3 All Years", fractionAKI3AllYears)

    categoryList = ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3']
    virtualAdmissionsWithSkips = [fractionAnyAKIAllYears, fractionAKI1AllYears, fractionAKI2AllYears, fractionAKI3AllYears]
    if (fLongAdmissionsOnly):
        listOfAKIFractions = g_LongAdmissionGoldStandardListOfAKIFractions
    else:
        listOfAKIFractions = g_GoldStandardListOfAKIFractions
    DrawDoubleBarGraph(testResultPercentPrefix + "Fraction of Patients With AKI Identified in Virtual Admissions", 
                       "Non-ESRD Patients", categoryList, "Fraction of Patients", 
                       "No Labs Skipped", listOfAKIFractions,
                       "Random Skips", virtualAdmissionsWithSkips,
                       False, reportDirectoryPath + testResultPercentPrefix + "FractionOfPtsAKIFromDailyvsSkippedLabs.jpg")


    ##################################
    # Sensitivity
    if (fLongAdmissionsOnly):
        sensitivityAnyAKI = round(float(g_TotalAKIAllYears / g_LongAdmissionGoldStandardALLNumNonESRDAnyAKI), 4)
        sensitivityAKI1 = round(float(g_TotalAKI1AllYears / g_LongAdmissionGoldStandardALLNumNonESRDAKI1), 4)
        sensitivityAKI2 = round(float(g_TotalAKI2AllYears / g_LongAdmissionGoldStandardALLNumNonESRDAKI2), 4)
        sensitivityAKI3 = round(float(g_TotalAKI3AllYears / g_LongAdmissionGoldStandardALLNumNonESRDAKI3), 4)
    else:
        sensitivityAnyAKI = round(float(g_TotalAKIAllYears / g_GoldStandardALLNumNonESRDAnyAKI), 4)
        sensitivityAKI1 = round(float(g_TotalAKI1AllYears / g_GoldStandardALLNumNonESRDAKI1), 4)
        sensitivityAKI2 = round(float(g_TotalAKI2AllYears / g_GoldStandardALLNumNonESRDAKI2), 4)
        sensitivityAKI3 = round(float(g_TotalAKI3AllYears / g_GoldStandardALLNumNonESRDAKI3), 4)

    print("")
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI", sensitivityAnyAKI)
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI-1", sensitivityAKI1)
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI-2", sensitivityAKI2)
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI-3", sensitivityAKI3)

    categoryList = ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3']
    sensitivityWithSkips = [sensitivityAnyAKI, sensitivityAKI1, sensitivityAKI2, sensitivityAKI3]
    DrawBarGraph("Sensitivity of AKI when Skipping " + testResultPercentSuffix, 
                 "Non-ESRD Patients", categoryList, 
                 "Sensitivity", sensitivityWithSkips,
                 False, reportDirectoryPath + testResultPercentPrefix + "Sensitivity.jpg")


    ##################################
    # Number of Consecutive Days Without Labs
    #RecordVectorResult(testResultPercentPrefix + "Num Consecutive Days without checking Creatinine with Skipped Labs", 
    #                   g_NumPtsWithConsecutiveSkippedDays)
    #DrawBarGraph(testResultPercentPrefix + "Consecutive Days without checking Creatinine with Skipped Labs", 
    #             "Num Consecutive Days Skipped", g_NumDaysSkippedXAxisString, 
    #             "Num Patients", g_NumPtsWithConsecutiveSkippedDays, 
    #             False, reportDirectoryPath + testResultPercentPrefix + "DailyLabsNumSkippedDaysBar.jpg")


    ##################################
    # Num AKIs after different lengths of Skipped Labs
    #print("\n=======================")
    #RecordVectorResult(testResultPercentPrefix + "Num Without AKI After Consecutive Days without checking Creatinine", g_NumAKI0AfterSkippedDays)
    #RecordVectorResult(testResultPercentPrefix + "Num KDIGO 1 AKI After Days without checking Creatinine", g_NumAKI1AfterSkippedDays)
    #RecordVectorResult(testResultPercentPrefix + "Num KDIGO 2 AKI After Days without checking Creatinine", g_NumAKI2AfterSkippedDays)
    #RecordVectorResult(testResultPercentPrefix + "Num KDIGO 3 AKI After Days without checking Creatinine", g_NumAKI3AfterSkippedDays)
    #DrawMultiLineGraph("Num AKI After Consecutive Days without checking Creatinine", 
    #                  testResultPercentPrefix + "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
    #                   "Num Patients", 
    #                   ["No AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
    #                   [g_NumAKI0AfterSkippedDays, g_NumAKI1AfterSkippedDays, g_NumAKI2AfterSkippedDays, g_NumAKI3AfterSkippedDays], 
    #                   False, reportDirectoryPath + testResultPercentPrefix + "NumAKIvsNumSkippedDaysLine.jpg")


    FractionPtsAfterNSkippedDaysWithNoAKI = [0.0] * MAX_NUM_SKIPPED_DAYS
    FractionPtsAfterNSkippedDaysWithAKI1 = [0.0] * MAX_NUM_SKIPPED_DAYS
    FractionPtsAfterNSkippedDaysWithAKI2 = [0.0] * MAX_NUM_SKIPPED_DAYS
    FractionPtsAfterNSkippedDaysWithAKI3 = [0.0] * MAX_NUM_SKIPPED_DAYS
    for index in range(MAX_NUM_SKIPPED_DAYS):
        if (g_NumPtsWithConsecutiveSkippedDays[index] > 0):
            FractionPtsAfterNSkippedDaysWithNoAKI[index] = round(float(g_NumAKI0AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)
            FractionPtsAfterNSkippedDaysWithAKI1[index] = round(float(g_NumAKI1AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)
            FractionPtsAfterNSkippedDaysWithAKI2[index] = round(float(g_NumAKI2AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)
            FractionPtsAfterNSkippedDaysWithAKI3[index] = round(float(g_NumAKI3AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)

    #RecordVectorResult(testResultPercentPrefix + "Fraction of Pts with NO AKI After N Consecutive Skipped Days", 
    #    g_FractionPtsAfterNSkippedDaysWithNoAKI)
    #RecordVectorResult(testResultPercentPrefix + "Fraction of Pts with AKI 1 After N Consecutive Skipped Days", 
    #    g_FractionPtsAfterNSkippedDaysWithAKI1)
    #RecordVectorResult(testResultPercentPrefix + "Fraction of Pts with AKI 2 After N Consecutive Skipped Days",
    #    g_FractionPtsAfterNSkippedDaysWithAKI2)
    #RecordVectorResult(testResultPercentPrefix + "Fraction of Pts with AKI 3 After N Consecutive Skipped Days", 
    #    g_FractionPtsAfterNSkippedDaysWithAKI3)
    #DrawMultiLineGraph(testResultPercentPrefix + "Fraction of Pts After N Consecutive Days without checking Creatinine with AKI",
    #                   "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
    #                   "Num Patients", 
    #                   ["No AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
    #                   [g_FractionPtsAfterNSkippedDaysWithNoAKI, g_FractionPtsAfterNSkippedDaysWithAKI1, 
    #                        g_FractionPtsAfterNSkippedDaysWithAKI2, g_FractionPtsAfterNSkippedDaysWithAKI3], 
    #                   False, reportDirectoryPath + testResultPercentPrefix + "FractionAKIvsNumSkippedDaysLine.jpg")

    #print("")
    #RecordVectorResult(testResultPercentPrefix + "Num Without AKI on CKD After Consecutive Days without checking Creatinine", g_NumAKI0OnCKDAfterSkippedDays)
    #RecordVectorResult(testResultPercentPrefix + "Num KDIGO 1 AKI on CKD After Days without checking Creatinine", g_NumAKI1OnCKDAfterSkippedDays)
    #RecordVectorResult(testResultPercentPrefix + "Num KDIGO 2 AKI on CKD After Days without checking Creatinine", g_NumAKI2OnCKDAfterSkippedDays)
    #RecordVectorResult(testResultPercentPrefix + "Num KDIGO 3 AKI on CKD After Days without checking Creatinine", g_NumAKI3OnCKDAfterSkippedDays)

    DrawMultiLineGraph("Num AKI on CKD After Consecutive Days without checking Creatinine", 
                       "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
                       "Num Patients", 
                       ["No AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
                       [g_NumAKI0OnCKDAfterSkippedDays, g_NumAKI1OnCKDAfterSkippedDays, g_NumAKI2OnCKDAfterSkippedDays, g_NumAKI3OnCKDAfterSkippedDays], 
                       False, reportDirectoryPath + testResultPercentPrefix + "NumAKIOnCKDvsNumSkippedDaysLine.jpg")

    #WriteCSVFile(reportDirectoryPath + testResultPercentPrefix + "RandomSkipObservedAKI.csv")

    # This is done to collect stats for comparing all random thresholds.
    g_NumAKINPercentSkip = [g_TotalAKIAllYears, g_TotalAKI1AllYears, g_TotalAKI2AllYears, g_TotalAKI3AllYears]
    g_FractionAKINPercentSkip = [fractionAnyAKIAllYears, fractionAKI1AllYears, fractionAKI2AllYears, fractionAKI3AllYears]
    if (fLongAdmissionsOnly):
        prefixStr = "LongAdmission"
    else:
        prefixStr = ""

    print("\n\n\n#" + testResultPercentSuffix + "Variables. (COPY THESE INTO THE CODE)")
    print("g_" + prefixStr + "NumLabsConsidered" + testResultPercentSuffix + " = " + str(g_TotalNumLabsConsidered))
    print("g_" + prefixStr + "NumLabsSkipped" + testResultPercentSuffix + " = " + str(g_TotalNumLabsSkipped))
    print("g_" + prefixStr + "NumAKI" + testResultPercentSuffix + " = " + str(g_NumAKINPercentSkip))
    print("g_" + prefixStr + "NumPtsWithConsecutiveSkippedDays" + testResultPercentSuffix + " = " + str(g_NumPtsWithConsecutiveSkippedDays))
    print("g_" + prefixStr + "FractionAKI" + testResultPercentSuffix + " = " + str(g_FractionAKINPercentSkip))
    print("g_" + prefixStr + "SensitivityAnyAKI" + testResultPercentSuffix + " = " + str(sensitivityAnyAKI))
    print("g_" + prefixStr + "SensitivityAKI1" + testResultPercentSuffix + " = " + str(sensitivityAKI1))
    print("g_" + prefixStr + "SensitivityAKI2" + testResultPercentSuffix + " = " + str(sensitivityAKI2))
    print("g_" + prefixStr + "SensitivityAKI3" + testResultPercentSuffix + " = " + str(sensitivityAKI3))
# End - FindAKIWithRandomSkips





################################################################################
#
# [SummarizeRandomSkips]
#
################################################################################
def SummarizeRandomSkips():
    reportDirectoryPath = g_WorkbookRootDir + "RandomSkips/"

    xAxisValueList = []
    xAxisNameList = []
    for percent in range(1, 10):
        percentNum = percent * 10
        xAxisValueList.append(percentNum)
        xAxisNameList.append(str(percentNum))

    # The considered number is always the same.
    g_NumLabsConsidered = g_NumLabsConsidered10PercentRandom
    g_NumSkippedLabs = [g_NumLabsSkipped10PercentRandom, g_NumLabsSkipped20PercentRandom, g_NumLabsSkipped30PercentRandom, 
                        g_NumLabsSkipped40PercentRandom, g_NumLabsSkipped50PercentRandom, g_NumLabsSkipped60PercentRandom, 
                        g_NumLabsSkipped70PercentRandom, g_NumLabsSkipped80PercentRandom, g_NumLabsSkipped90PercentRandom]

    DrawBarGraph("Number Labs Skipped",
                 "Percent Labs Skipped", xAxisValueList, "Num Labs Skipped", 
                 g_NumSkippedLabs, 
                 False, reportDirectoryPath + "NumLabsSkipped.jpg")


    sensitivityToAnyAKIvsRandomProb = [g_SensitivityAnyAKI10PercentRandom, g_SensitivityAnyAKI20PercentRandom, g_SensitivityAnyAKI30PercentRandom, 
                                    g_SensitivityAnyAKI40PercentRandom, g_SensitivityAnyAKI50PercentRandom, g_SensitivityAnyAKI60PercentRandom,
                                    g_SensitivityAnyAKI70PercentRandom, g_SensitivityAnyAKI80PercentRandom, g_SensitivityAnyAKI90PercentRandom]

    sensitivityToAKI1vsRandomProb = [g_SensitivityAKI110PercentRandom, g_SensitivityAKI120PercentRandom, g_SensitivityAKI130PercentRandom, 
                                    g_SensitivityAKI140PercentRandom, g_SensitivityAKI150PercentRandom, g_SensitivityAKI160PercentRandom,
                                    g_SensitivityAKI170PercentRandom, g_SensitivityAKI180PercentRandom, g_SensitivityAKI190PercentRandom]

    sensitivityToAKI2vsRandomProb = [g_SensitivityAKI210PercentRandom, g_SensitivityAKI220PercentRandom, g_SensitivityAKI230PercentRandom, 
                                    g_SensitivityAKI240PercentRandom, g_SensitivityAKI250PercentRandom, g_SensitivityAKI260PercentRandom,
                                    g_SensitivityAKI270PercentRandom, g_SensitivityAKI280PercentRandom, g_SensitivityAKI290PercentRandom]

    sensitivityToAKI3vsRandomProb = [g_SensitivityAKI310PercentRandom, g_SensitivityAKI320PercentRandom, g_SensitivityAKI330PercentRandom, 
                                    g_SensitivityAKI340PercentRandom, g_SensitivityAKI350PercentRandom, g_SensitivityAKI360PercentRandom,
                                    g_SensitivityAKI370PercentRandom, g_SensitivityAKI380PercentRandom, g_SensitivityAKI390PercentRandom]


    DrawMultiLineGraph("Sensitivity of AKI Detected on Daily Labs with Percent Labs Skipped", 
                       "Percent Labs Skipped", xAxisValueList, "Sensitivity", 
                       ["All AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"],
                       [sensitivityToAnyAKIvsRandomProb, sensitivityToAKI1vsRandomProb, sensitivityToAKI2vsRandomProb, sensitivityToAKI3vsRandomProb], 
                       False, reportDirectoryPath + "SensitivityOfAKIvsPercentLabsSkipped.jpg")

    numMissedAKIWith10Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI10PercentRandom[0]
    numMissedAKIWith20Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI20PercentRandom[0]
    numMissedAKIWith30Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI30PercentRandom[0]
    numMissedAKIWith40Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI40PercentRandom[0]
    numMissedAKIWith50Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI50PercentRandom[0]
    numMissedAKIWith60Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI60PercentRandom[0]
    numMissedAKIWith70Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI70PercentRandom[0]
    numMissedAKIWith80Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI80PercentRandom[0]
    numMissedAKIWith90Percent = g_GoldStandardALLNumNonESRDAnyAKI - g_NumAKI80PercentRandom[0]

    numLabsPerAKIWith10PercentSkip = round((g_NumLabsSkipped10PercentRandom / numMissedAKIWith10Percent), 4)
    numLabsPerAKIWith20PercentSkip = round((g_NumLabsSkipped20PercentRandom / numMissedAKIWith20Percent), 4)
    numLabsPerAKIWith30PercentSkip = round((g_NumLabsSkipped30PercentRandom / numMissedAKIWith30Percent), 4)
    numLabsPerAKIWith40PercentSkip = round((g_NumLabsSkipped40PercentRandom / numMissedAKIWith40Percent), 4)
    numLabsPerAKIWith50PercentSkip = round((g_NumLabsSkipped50PercentRandom / numMissedAKIWith50Percent), 4)
    numLabsPerAKIWith60PercentSkip = round((g_NumLabsSkipped60PercentRandom / numMissedAKIWith60Percent), 4)
    numLabsPerAKIWith70PercentSkip = round((g_NumLabsSkipped70PercentRandom / numMissedAKIWith70Percent), 4)
    numLabsPerAKIWith80PercentSkip = round((g_NumLabsSkipped80PercentRandom / numMissedAKIWith80Percent), 4)
    numLabsPerAKIWith90PercentSkip = round((g_NumLabsSkipped90PercentRandom / numMissedAKIWith90Percent), 4)

    DrawBarGraph("Number of Labs Saved Per Missed AKI", 
                "Percent Labs Skipped", ["10", "20", "30", "40", "50", "60", "70", "80", "90"], 
                "Num Missed AKIs", [numLabsPerAKIWith10PercentSkip, numLabsPerAKIWith20PercentSkip, numLabsPerAKIWith30PercentSkip, numLabsPerAKIWith40PercentSkip, numLabsPerAKIWith50PercentSkip, numLabsPerAKIWith60PercentSkip, numLabsPerAKIWith70PercentSkip, numLabsPerAKIWith80PercentSkip, numLabsPerAKIWith90PercentSkip],
                False, reportDirectoryPath + "LabsSavedPerMissedAKI.jpg")
# End - SummarizeRandomSkips




################################################################################
#
# [SummarizeLongAdmissions]
#
################################################################################
def SummarizeLongAdmissions():
    reportDirectoryPath = g_WorkbookRootDir + "LongAdmissionRandomSkips/"

    xAxisValueList = []
    xAxisNameList = []
    for percent in range(1, 10):
        percentNum = percent * 10
        xAxisValueList.append(percentNum)
        xAxisNameList.append(str(percentNum))


    # The considered number is always the same.
    g_NumLabsConsidered = g_LongAdmissionNumLabsConsidered10PercentRandom
    g_NumSkippedLabs = [g_LongAdmissionNumLabsSkipped10PercentRandom, g_LongAdmissionNumLabsSkipped20PercentRandom, g_LongAdmissionNumLabsSkipped30PercentRandom, 
                        g_LongAdmissionNumLabsSkipped40PercentRandom, g_LongAdmissionNumLabsSkipped50PercentRandom, g_LongAdmissionNumLabsSkipped60PercentRandom, 
                        g_LongAdmissionNumLabsSkipped70PercentRandom, g_LongAdmissionNumLabsSkipped80PercentRandom, g_LongAdmissionNumLabsSkipped90PercentRandom]

    DrawBarGraph("Number Labs Skipped",
                 "Percent Labs Skipped", xAxisValueList, "Num Labs Skipped", 
                 g_NumSkippedLabs, 
                 False, reportDirectoryPath + "NumLabsSkipped.jpg")


    sensitivityToAnyAKIvsRandomProb = [g_LongAdmissionSensitivityAnyAKI10PercentRandom, g_LongAdmissionSensitivityAnyAKI20PercentRandom, g_LongAdmissionSensitivityAnyAKI30PercentRandom, 
                                    g_LongAdmissionSensitivityAnyAKI40PercentRandom, g_LongAdmissionSensitivityAnyAKI50PercentRandom, g_LongAdmissionSensitivityAnyAKI60PercentRandom,
                                    g_LongAdmissionSensitivityAnyAKI70PercentRandom, g_LongAdmissionSensitivityAnyAKI80PercentRandom, g_LongAdmissionSensitivityAnyAKI90PercentRandom]

    sensitivityToAKI1vsRandomProb = [g_LongAdmissionSensitivityAKI110PercentRandom, g_LongAdmissionSensitivityAKI120PercentRandom, g_LongAdmissionSensitivityAKI130PercentRandom, 
                                    g_LongAdmissionSensitivityAKI140PercentRandom, g_LongAdmissionSensitivityAKI150PercentRandom, g_LongAdmissionSensitivityAKI160PercentRandom,
                                    g_LongAdmissionSensitivityAKI170PercentRandom, g_LongAdmissionSensitivityAKI180PercentRandom, g_LongAdmissionSensitivityAKI190PercentRandom]

    sensitivityToAKI2vsRandomProb = [g_LongAdmissionSensitivityAKI210PercentRandom, g_LongAdmissionSensitivityAKI220PercentRandom, g_LongAdmissionSensitivityAKI230PercentRandom, 
                                    g_LongAdmissionSensitivityAKI240PercentRandom, g_LongAdmissionSensitivityAKI250PercentRandom, g_LongAdmissionSensitivityAKI260PercentRandom,
                                    g_LongAdmissionSensitivityAKI270PercentRandom, g_LongAdmissionSensitivityAKI280PercentRandom, g_LongAdmissionSensitivityAKI290PercentRandom]

    sensitivityToAKI3vsRandomProb = [g_LongAdmissionSensitivityAKI310PercentRandom, g_LongAdmissionSensitivityAKI320PercentRandom, g_LongAdmissionSensitivityAKI330PercentRandom, 
                                    g_LongAdmissionSensitivityAKI340PercentRandom, g_LongAdmissionSensitivityAKI350PercentRandom, g_LongAdmissionSensitivityAKI360PercentRandom,
                                    g_LongAdmissionSensitivityAKI370PercentRandom, g_LongAdmissionSensitivityAKI380PercentRandom, g_LongAdmissionSensitivityAKI390PercentRandom]

    DrawMultiLineGraph("Sensitivity of AKI Detected on Daily Labs with Percent Labs Skipped", 
                       "Percent Labs Skipped", xAxisValueList, "Sensitivity", 
                       ["All AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"],
                       [sensitivityToAnyAKIvsRandomProb, sensitivityToAKI1vsRandomProb, sensitivityToAKI2vsRandomProb, sensitivityToAKI3vsRandomProb], 
                       False, reportDirectoryPath + "SensitivityOfAKIvsPercentLabsSkipped.jpg")
# End - SummarizeLongAdmissions






################################################################################
#
# [FindAKIWithBandSkips]
#
# Skip Values Within an Band
################################################################################
def FindAKIWithBandSkips(filePathName, randomChanceOfSkip):
    reportDirectoryPath = g_WorkbookRootDir + "Bands/"

    testResultIndex = int(randomChanceOfSkip * 10)
    testResultPercentSuffix = str(testResultIndex) + "0Percent"
    testResultPercentPrefix = "BandSkipping" + str(testResultIndex) + "0Percent"

    fRandomSkips = False
    fBandSkips = True
    vitrualAdmissionStartsAfterNDaysInHospital = 0
    FindAKIInfo(filePathName, True, fRandomSkips, fBandSkips, randomChanceOfSkip, vitrualAdmissionStartsAfterNDaysInHospital)

    ##################################
    # Basic Test Characteristics
    RecordNumberResult("Total Num Labs Considered", g_TotalNumLabsConsidered)
    RecordNumberResult("Total Num Labs Skipped", g_TotalNumLabsSkipped)
    RecordNumberResult("Total Num Labs Performed", g_TotalNumLabsPerformed)

    ##################################
    # Number of Patients with AKI
    RecordNumberResult("Num Non-ESRD Patients with any AKI All Years", g_TotalAKIAllYears)
    RecordNumberResult("Num Non-ESRD Patients with AKI-1 All Years", g_TotalAKI1AllYears)
    RecordNumberResult("Num Non-ESRD Patients with AKI-2 All Years", g_TotalAKI2AllYears)
    RecordNumberResult("Num Non-ESRD Patients with AKI-3 All Years", g_TotalAKI3AllYears)

    fractionAnyAKIAllYears = round(float(g_TotalAKIAllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI1AllYears = round(float(g_TotalAKI1AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI2AllYears = round(float(g_TotalAKI2AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)
    fractionAKI3AllYears = round(float(g_TotalAKI3AllYears / g_TotalNumNonESRDAdmissionsAllYears), 4)

    RecordNumberResult("Fraction of Non-ESRD Patients with any AKI All Years", fractionAnyAKIAllYears)
    RecordNumberResult("Fraction of Non-ESRD Patients with AKI-1 All Years", fractionAKI1AllYears)
    RecordNumberResult("Fraction of Non-ESRD Patients with AKI-2 All Years", fractionAKI2AllYears)
    RecordNumberResult("Fraction of Non-ESRD Patients with AKI-3 All Years", fractionAKI3AllYears)

    categoryList = ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3']
    virtualAdmissionsWithSkips = [fractionAnyAKIAllYears, fractionAKI1AllYears, fractionAKI2AllYears, fractionAKI3AllYears]
    DrawDoubleBarGraph("Fraction of Patients With AKI Identified in Virtual Admissions", 
                       "Non-ESRD Patients", categoryList, "Fraction of Patients", 
                       "No Labs Skipped", g_LongAdmissionGoldStandardListOfAKIFractions,
                       "Band Skips", virtualAdmissionsWithSkips,
                       False, reportDirectoryPath + "FractionAKIFromDailyvsBandSkippedLabs.jpg")

    print("")
    RecordVectorResult("Num Consecutive Days without checking Creatinine with Skipped Labs", g_NumPtsWithConsecutiveSkippedDays)
    DrawBarGraph("Consecutive Days without checking Creatinine with Band Skipped Labs", 
                 "Num Consecutive Days Skipped", g_NumDaysSkippedXAxisString, 
                 "Num Patients", g_NumPtsWithConsecutiveSkippedDays, 
                 False, reportDirectoryPath + "DailyLabsNumSkippedDaysBar.jpg")


    ##################################
    # Sensitivity
    sensitivityAnyAKI = round(float(g_TotalAKIAllYears / g_GoldStandardALLNumNonESRDAnyAKI), 4)
    sensitivityAKI1 = round(float(g_TotalAKI1AllYears / g_GoldStandardALLNumNonESRDAKI1), 4)
    sensitivityAKI2 = round(float(g_TotalAKI2AllYears / g_GoldStandardALLNumNonESRDAKI2), 4)
    sensitivityAKI3 = round(float(g_TotalAKI3AllYears / g_GoldStandardALLNumNonESRDAKI3), 4)

    print("")
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI", sensitivityAnyAKI)
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI-1", sensitivityAKI1)
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI-2", sensitivityAKI2)
    RecordNumberResult(testResultPercentPrefix + "Sensitivity for Any AKI-3", sensitivityAKI3)

    categoryList = ['Any AKI', 'KDIGO 1', 'KDIGO 2', 'KDIGO 3']
    sensitivityWithSkips = [sensitivityAnyAKI, sensitivityAKI1, sensitivityAKI2, sensitivityAKI3]
    DrawBarGraph("Sensitivity of AKI when Skipping " + testResultPercentSuffix, 
                 "Non-ESRD Patients", categoryList, 
                 "Sensitivity", sensitivityWithSkips,
                 False, reportDirectoryPath + testResultPercentPrefix + "Sensitivity.jpg")




    ##################################
    # Num AKIs after different lengths of Skipped Labs
    #print("\n=======================")
    #RecordVectorResult("Num Without AKI After Consecutive Days without checking Creatinine", g_NumAKI0AfterSkippedDays)
    #RecordVectorResult("Num KDIGO 1 AKI After Days without checking Creatinine", g_NumAKI1AfterSkippedDays)
    #RecordVectorResult("Num KDIGO 2 AKI After Days without checking Creatinine", g_NumAKI2AfterSkippedDays)
    #RecordVectorResult("Num KDIGO 3 AKI After Days without checking Creatinine", g_NumAKI3AfterSkippedDays)
    #DrawMultiLineGraph("Num AKI After Consecutive Days without checking Creatinine", 
    #                   "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
    #                   "Num Patients", 
    #                   ["No AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
    #                   [g_NumAKI0AfterSkippedDays, g_NumAKI1AfterSkippedDays, g_NumAKI2AfterSkippedDays, g_NumAKI3AfterSkippedDays], 
    #                   False, reportDirectoryPath + "NumAKIvsNumSkippedDaysLine.jpg")

    g_FractionPtsAfterNSkippedDaysWithNoAKI = [0.0] * MAX_NUM_SKIPPED_DAYS
    g_FractionPtsAfterNSkippedDaysWithAKI1 = [0.0] * MAX_NUM_SKIPPED_DAYS
    g_FractionPtsAfterNSkippedDaysWithAKI2 = [0.0] * MAX_NUM_SKIPPED_DAYS
    g_FractionPtsAfterNSkippedDaysWithAKI3 = [0.0] * MAX_NUM_SKIPPED_DAYS
    for index in range(MAX_NUM_SKIPPED_DAYS):
        if (g_NumPtsWithConsecutiveSkippedDays[index] > 0):
            g_FractionPtsAfterNSkippedDaysWithNoAKI[index] = round(float(g_NumAKI0AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)
            g_FractionPtsAfterNSkippedDaysWithAKI1[index] = round(float(g_NumAKI1AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)
            g_FractionPtsAfterNSkippedDaysWithAKI2[index] = round(float(g_NumAKI2AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)
            g_FractionPtsAfterNSkippedDaysWithAKI3[index] = round(float(g_NumAKI3AfterSkippedDays[index]) / float(g_NumPtsWithConsecutiveSkippedDays[index]), 4)
    #RecordVectorResult("Fraction of Pts with NO AKI After N Consecutive Skipped Days", g_FractionPtsAfterNSkippedDaysWithNoAKI)
    #RecordVectorResult("Fraction of Pts with AKI 1 After N Consecutive Skipped Days", g_FractionPtsAfterNSkippedDaysWithAKI1)
    #RecordVectorResult("Fraction of Pts with AKI 2 After N Consecutive Skipped Days", g_FractionPtsAfterNSkippedDaysWithAKI2)
    #RecordVectorResult("Fraction of Pts with AKI 3 After N Consecutive Skipped Days", g_FractionPtsAfterNSkippedDaysWithAKI3)

    DrawMultiLineGraph("Fraction of Pts After N Consecutive Days without checking Creatinine with AKI", 
                       "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
                       "Num Patients", 
                       ["No AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
                       [g_FractionPtsAfterNSkippedDaysWithNoAKI, g_FractionPtsAfterNSkippedDaysWithAKI1, g_FractionPtsAfterNSkippedDaysWithAKI2, g_FractionPtsAfterNSkippedDaysWithAKI3], 
                       False, reportDirectoryPath + "FractionAKIvsNumSkippedDaysLine.jpg")

    #print("")
    #RecordVectorResult("Num Without AKI on CKD After Consecutive Days without checking Creatinine", g_NumAKI0OnCKDAfterSkippedDays)
    #RecordVectorResult("Num KDIGO 1 AKI on CKD After Days without checking Creatinine", g_NumAKI1OnCKDAfterSkippedDays)
    #RecordVectorResult("Num KDIGO 2 AKI on CKD After Days without checking Creatinine", g_NumAKI2OnCKDAfterSkippedDays)
    #RecordVectorResult("Num KDIGO 3 AKI on CKD After Days without checking Creatinine", g_NumAKI3OnCKDAfterSkippedDays)
    #DrawMultiLineGraph("Num Pts with AKI on CKD After Consecutive Days without checking Creatinine", 
    #                   "Num Consecutive Days without checking Creatinine", g_NumDaysSkippedXAxis,
    #                   "Num Patients", 
    #                   ["No AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"], 
    #                   [g_NumAKI0OnCKDAfterSkippedDays, g_NumAKI1OnCKDAfterSkippedDays, g_NumAKI2OnCKDAfterSkippedDays, g_NumAKI3OnCKDAfterSkippedDays], 
    #                   False, reportDirectoryPath + "NumAKIOnCKDvsNumSkippedDaysLine.jpg")

    #WriteCSVFile(reportDirectoryPath + "BandSkipObservedAKI.csv")

    # This is done to collect stats for comparing all random thresholds.
    g_NumAKINPercentSkip = [g_TotalAKIAllYears, g_TotalAKI1AllYears, g_TotalAKI2AllYears, g_TotalAKI3AllYears]
    g_FractionAKINPercentSkip = [fractionAnyAKIAllYears, fractionAKI1AllYears, fractionAKI2AllYears, fractionAKI3AllYears]
    print("\n\n\n#" + testResultPercentSuffix + " Variables for BandSkipping:")
    print("g_NumLabsConsidered" + testResultPercentSuffix + "BandSkipping = " + str(g_TotalNumLabsConsidered))
    print("g_NumLabsSkipped" + testResultPercentSuffix + "BandSkipping = " + str(g_TotalNumLabsSkipped))
    print("g_NumAKI" + testResultPercentSuffix + "BandSkipping = " + str(g_NumAKINPercentSkip))
    print("g_NumPtsWithConsecutiveSkippedDays" + testResultPercentSuffix + "BandSkipping = " + str(g_NumPtsWithConsecutiveSkippedDays))
    print("g_FractionAKI" + testResultPercentSuffix + "BandSkipping = " + str(g_FractionAKINPercentSkip))
    print("g_SensitivityAnyAKI" + testResultPercentSuffix + "BandSkipping = " + str(sensitivityAnyAKI))
    print("g_SensitivityAKI1" + testResultPercentSuffix + "BandSkipping = " + str(sensitivityAKI1))
    print("g_SensitivityAKI2" + testResultPercentSuffix + "BandSkipping = " + str(sensitivityAKI2))
    print("g_SensitivityAKI3" + testResultPercentSuffix + "BandSkipping = " + str(sensitivityAKI3))
# End - FindAKIWithBandSkips








################################################################################
#
# [SummarizeBollingerBandResults]
#
################################################################################
def SummarizeBollingerBandResults():
    reportDirectoryPath = g_WorkbookRootDir + "Bands/"

    xAxisValueList = []
    xAxisNameList = []
    for percent in range(1, 10):
        percentNum = percent * 10
        xAxisValueList.append(percentNum)
        xAxisNameList.append(str(percentNum))

    # The considered number is always the same.
    g_NumSkippedLabsRandom = [g_NumLabsSkipped10PercentRandom, g_NumLabsSkipped20PercentRandom, g_NumLabsSkipped30PercentRandom, 
                        g_NumLabsSkipped40PercentRandom, g_NumLabsSkipped50PercentRandom, g_NumLabsSkipped60PercentRandom, 
                        g_NumLabsSkipped70PercentRandom, g_NumLabsSkipped80PercentRandom, g_NumLabsSkipped90PercentRandom]

    g_NumSkippedLabsRandomBand = [g_NumLabsSkipped10PercentBandSkipping, g_NumLabsSkipped20PercentBandSkipping, g_NumLabsSkipped30PercentBandSkipping, 
                        g_NumLabsSkipped40PercentBandSkipping, g_NumLabsSkipped50PercentBandSkipping, g_NumLabsSkipped60PercentBandSkipping, 
                        g_NumLabsSkipped70PercentBandSkipping, g_NumLabsSkipped80PercentBandSkipping, g_NumLabsSkipped90PercentBandSkipping]

    DrawBarGraph("Number Labs Skipped",
                 "Percent Labs Skipped", xAxisValueList, "Num Labs Skipped", 
                 g_NumSkippedLabsRandomBand, 
                 False, reportDirectoryPath + "NumLabsSkippedWithBandRandom.jpg")

    DrawMultiLineGraph("Number Labs Skipped for Random vs Band Random", 
                       "Percent Labs Skipped", xAxisValueList, "Num Labs Skipped", 
                       ["Random", "Band Random"],
                       [g_NumSkippedLabsRandom, g_NumSkippedLabsRandomBand], 
                       False, reportDirectoryPath + "NumLabsSkippedWithRandomvsBandRandom.jpg")




    sensitivityToAnyAKIvsRandomProb = [g_SensitivityAnyAKI10PercentRandom, g_SensitivityAnyAKI20PercentRandom, g_SensitivityAnyAKI30PercentRandom, 
                                    g_SensitivityAnyAKI40PercentRandom, g_SensitivityAnyAKI50PercentRandom, g_SensitivityAnyAKI60PercentRandom,
                                    g_SensitivityAnyAKI70PercentRandom, g_SensitivityAnyAKI80PercentRandom, g_SensitivityAnyAKI90PercentRandom]

    sensitivityToAnyAKIvsRandomBand = [g_SensitivityAnyAKI10PercentBandSkipping, g_SensitivityAnyAKI20PercentBandSkipping, g_SensitivityAnyAKI30PercentBandSkipping, 
                                    g_SensitivityAnyAKI40PercentBandSkipping, g_SensitivityAnyAKI50PercentBandSkipping, g_SensitivityAnyAKI60PercentBandSkipping, 
                                    g_SensitivityAnyAKI70PercentBandSkipping, g_SensitivityAnyAKI80PercentBandSkipping, g_SensitivityAnyAKI90PercentBandSkipping]

    sensitivityToAKI1vsRandomBand = [g_SensitivityAKI110PercentBandSkipping, g_SensitivityAKI120PercentBandSkipping, g_SensitivityAKI130PercentBandSkipping, 
                                    g_SensitivityAKI140PercentBandSkipping, g_SensitivityAKI150PercentBandSkipping, g_SensitivityAKI160PercentBandSkipping, 
                                    g_SensitivityAKI170PercentBandSkipping, g_SensitivityAKI180PercentBandSkipping, g_SensitivityAKI190PercentBandSkipping]

    sensitivityToAKI2vsRandomBand = [g_SensitivityAKI210PercentBandSkipping, g_SensitivityAKI220PercentBandSkipping, g_SensitivityAKI230PercentBandSkipping, 
                                    g_SensitivityAKI240PercentBandSkipping, g_SensitivityAKI250PercentBandSkipping, g_SensitivityAKI260PercentBandSkipping, 
                                    g_SensitivityAKI270PercentBandSkipping, g_SensitivityAKI280PercentBandSkipping, g_SensitivityAKI290PercentBandSkipping]

    sensitivityToAKI3vsRandomBand = [g_SensitivityAKI310PercentBandSkipping, g_SensitivityAKI320PercentBandSkipping, g_SensitivityAKI330PercentBandSkipping, 
                                    g_SensitivityAKI340PercentBandSkipping, g_SensitivityAKI350PercentBandSkipping, g_SensitivityAKI360PercentBandSkipping, 
                                    g_SensitivityAKI370PercentBandSkipping, g_SensitivityAKI380PercentBandSkipping, g_SensitivityAKI390PercentBandSkipping]

    DrawMultiLineGraph("Sensitivity of AKI Detected on Daily Labs with Percent Labs Band Skipped", 
                       "Percent Labs Skipped", xAxisValueList, "Sensitivity", 
                       ["All AKI", "KDIGO 1", "KDIGO 2", "KDIGO 3"],
                       [sensitivityToAnyAKIvsRandomBand, sensitivityToAKI1vsRandomBand, sensitivityToAKI2vsRandomBand, sensitivityToAKI3vsRandomBand],
                       False, reportDirectoryPath + "SensitivityOfAKIvsPercentLabsBandSkipped.jpg")

    DrawMultiLineGraph("Sensitivity of AKI Detected on Daily Labs with Percent Labs - Band vs Random", 
                       "Percent Labs Skipped", xAxisValueList, "Sensitivity", 
                       ["Random", "Band Random"],
                       [sensitivityToAnyAKIvsRandomProb, sensitivityToAnyAKIvsRandomBand], 
                       False, reportDirectoryPath + "SensitivityOfAKIvsPercentLabsBandSkipped.jpg")
# End - SummarizeBollingerBandResults






################################################################################
#
# MAIN
#
################################################################################
startimeStr = str(datetime.now().time())

Elixhauser.Elixhauser_LoadLibrary("/home/ddean/dLargeData/mlData/elixhauser/CMR-Reference-File-v2022-1CSV.csv")
print("\n\n\n=======================")

if (False):
    print("ComputeBaseline \n\n")
    ComputeBaseline(g_srcTDFFilePath)

if (False):
    print("ComputeGoldStandardWithOnlyDailyLabs \n\n")
    vitrualAdmissionStartsAfterNDaysInHospital = 0
    ComputeGoldStandardWithOnlyDailyLabs(g_srcTDFFilePath, vitrualAdmissionStartsAfterNDaysInHospital)

if (False):
    print("FindAKIWithRandomSkips 10 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.1, False)

if (False):
    print("FindAKIWithRandomSkips 20 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.2, False)

if (False):
    print("FindAKIWithRandomSkips 30 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.3, False)

if (False):
    print("FindAKIWithRandomSkips 40 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.4, False)

if (False):
    print("FindAKIWithRandomSkips 50 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.5, False)

if (False):
    print("FindAKIWithRandomSkips 60 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.6, False)

if (False):
    print("FindAKIWithRandomSkips 70 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.7, False)

if (False):
    print("FindAKIWithRandomSkips 80 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.8, False)

if (False):
    print("FindAKIWithRandomSkips 90 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.9, False)

if (False):
    SummarizeRandomSkips()

if (False):
    print("GoldStandardWithOnlyDailyLabs for Long Admissions \n\n")
    vitrualAdmissionStartsAfterNDaysInHospital = 14
    ComputeGoldStandardWithOnlyDailyLabs(g_srcTDFFilePath, vitrualAdmissionStartsAfterNDaysInHospital)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 10 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.1, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 20 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.2, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 30 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.3, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 40 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.4, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 50 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.5, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 60 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.6, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 70 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.7, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 80 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.8, True)

if (False):
    print("FindAKIWithRandomSkips LongAdmissions 90 \n")
    FindAKIWithRandomSkips(g_srcTDFFilePath, 0.9, True)

if (False):
    SummarizeLongAdmissions()

if (False):
    print("FindAKIWithBandSkips 10 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.1)

if (False):
    print("FindAKIWithBandSkips 20 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.2)

if (False):
    print("FindAKIWithBandSkips 30 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.3)

if (False):
    print("FindAKIWithBandSkips 40 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.4)

if (False):
    print("FindAKIWithBandSkips 50 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.5)

if (False):
    print("FindAKIWithBandSkips 60 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.6)

if (False):
    print("FindAKIWithBandSkips 70 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.7)

if (False):
    print("FindAKIWithBandSkips 80 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.8)

if (False):
    print("FindAKIWithBandSkips 90 \n")
    FindAKIWithBandSkips(g_srcTDFFilePath, 0.9)

if (False):
    SummarizeBollingerBandResults()

if (False):
    print("Compute Cost Variables \n\n")
    ComputeCostVariables(g_srcTDFFilePath)

if (True):
    PrintJavaScriptArrays()

print("")
stopTimeStr = str(datetime.now().time())
print("Start Time=" + startimeStr)
print("Stop Time=" + stopTimeStr)
print("")


