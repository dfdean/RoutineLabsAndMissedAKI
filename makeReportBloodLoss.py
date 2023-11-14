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
# Analyze and Make Graphs for Blood Loss due to Daily Labs
#
################################################################################
import os
import os.path
import sys
import re
import shutil
import time
from datetime import datetime
import datetime

import xml.dom
import xml.dom.minidom
from xml.dom import minidom
from pathlib import Path

import math
import statistics
from scipy import stats
from scipy.stats import spearmanr
import numpy as np

g_libDirPath = "/home/ddean/ddRoot/lib"
# Allow import to pull from the per-user lib directory.
#print("g_libDirPath = " + g_libDirPath)
if g_libDirPath not in sys.path:
    sys.path.insert(0, g_libDirPath)

from xmlTools import *
import tdfTools as tdf
import tdfShow as tdfShow
import dataShow as DataShow
import elixhauser as Elixhauser

# Salisbury guidelines
# Salisbury, et al, "Incidence, Correlates and Outcomes of Acute, Hospital-acquired Anemia in Patients with Acute Myocardial Infarction"
# Circ Cardiovasc Qual Outcomes. 2010 Jul; 3(4): 337–346.
ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN_OVER_60          = 13.2
ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN_60_AND_UNDER     = 13.7
ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN_OVER_60        = 12.2
ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN_60_AND_UNDER   = 12.2

# WHO Guidelines
# Beutler E, Waalen J. The definition of anemia: what is the lower limit of normal of the blood hemoglobin concentration? Blood. 2006;107(5):1747–1750
ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN     = 13.0
ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN   = 12.0

# These are derived by using the absolute hemoglobin levels for each type of anemia and the definition of "non-anemic" Hgb.
# This lets us identify an acute anemia that happens even in a patient who is chronically anemic
MIN_HGB_DROP_FOR_MILD_ANEMIA          = 0.5 # 13.0 - 12.9
MIN_HGB_DROP_FOR_MODERATE_ANEMIA      = 2.0 # 13.0 - 11.0
MIN_HGB_DROP_FOR_SEVERE_ANEMIA        = 4.0 # 13.0 - 9.0

HGB_RISE_PER_TRANSFUSION = 1.0



################################################################################
#
# Correlation Between Hgb Drops and Iron Markers
#
################################################################################
def ShowCorrelationOfAnemiaAndIronMarkers(g_srcTDFFilePath):
    print("\n========================\nCorrelation between Hgb Drop and Labs")
    numPatients = 0
    srcTDF = tdf.TDF_CreateTDFFileReader(g_srcTDFFilePath, 
                                        "Flag_HospitalAdmission;Flag_HospitalDischarge;TransRBC;Hgb;Plt;WBC;Cr;ALT;VancDose;PipTazoDose;CefepimeDose;DaptoDose;MeroDose;MajorSurgeries;GIProcedures;DDimer;Fibrinogen;Haptoglobin;FreeHgb;LDH;Transferrin;TransferrinSat;Iron;TIBC",
                                        "Hgb", [])
    srcTDF.SetTimeResolution(1)
    srcTDF.SetCarryForwardPreviousDataValues(False)


    #######################################
    # Make Histograms for all values under different conditions: 
    #   Transfuse, NoTransfuse, Anemia, NoAnemia
    #
    # Hgb Histograms
    startHgbValueSevereAnemia = tdfShow.TDFShowHistogram("Hgb")
    startHgbValueModAnemia = tdfShow.TDFShowHistogram("Hgb")
    startHgbValueMildAnemia = tdfShow.TDFShowHistogram("Hgb")
    startHgbValueNoAnemia = tdfShow.TDFShowHistogram("Hgb")
    # DDimer Histograms
    ddimerValueSevereAnemia = tdfShow.TDFShowHistogram("DDimer")
    ddimerValueModAnemia = tdfShow.TDFShowHistogram("DDimer")
    ddimerValueMildAnemia = tdfShow.TDFShowHistogram("DDimer")
    ddimerValueNoAnemia = tdfShow.TDFShowHistogram("DDimer")
    # Fibrinogen Histograms
    fibrinogenValueSevereAnemia = tdfShow.TDFShowHistogram("Fibrinogen")
    fibrinogenValueModAnemia = tdfShow.TDFShowHistogram("Fibrinogen")
    fibrinogenValueMildAnemia = tdfShow.TDFShowHistogram("Fibrinogen")
    fibrinogenValueNoAnemia = tdfShow.TDFShowHistogram("Fibrinogen")
    # TIBC Histograms
    TIBCValueSevereAnemia = tdfShow.TDFShowHistogram("TIBC")
    TIBCValueModAnemia = tdfShow.TDFShowHistogram("TIBC")
    TIBCValueMildAnemia = tdfShow.TDFShowHistogram("TIBC")
    TIBCValueNoAnemia = tdfShow.TDFShowHistogram("TIBC")
    # Transferrin Histograms
    TransferrinValueSevereAnemia = tdfShow.TDFShowHistogram("Transferrin")
    TransferrinValueModAnemia = tdfShow.TDFShowHistogram("Transferrin")
    TransferrinValueMildAnemia = tdfShow.TDFShowHistogram("Transferrin")
    TransferrinValueNoAnemia = tdfShow.TDFShowHistogram("Transferrin")
    # Haptoglobin Histograms
    HaptoglobinValueSevereAnemia = tdfShow.TDFShowHistogram("Haptoglobin")
    HaptoglobinValueModAnemia = tdfShow.TDFShowHistogram("Haptoglobin")
    HaptoglobinValueMildAnemia = tdfShow.TDFShowHistogram("Haptoglobin")
    HaptoglobinValueNoAnemia = tdfShow.TDFShowHistogram("Haptoglobin")
    # LDH Histograms
    LDHValueSevereAnemia = tdfShow.TDFShowHistogram("LDH")
    LDHValueModAnemia = tdfShow.TDFShowHistogram("LDH")
    LDHValueMildAnemia = tdfShow.TDFShowHistogram("LDH")
    LDHValueNoAnemia = tdfShow.TDFShowHistogram("LDH")
    # Iron Histograms
    IronValueSevereAnemia = tdfShow.TDFShowHistogram("Iron")
    IronValueModAnemia = tdfShow.TDFShowHistogram("Iron")
    IronValueMildAnemia = tdfShow.TDFShowHistogram("Iron")
    IronValueNoAnemia = tdfShow.TDFShowHistogram("Iron")
    

    # Make lists that we will use to compute Covariances
    numTransfusionsList = []
    firstHgbValueList = []
    DDimerList = []
    FibrinogenList = []
    HaptoglobinList = []
    LDHList = []
    TransferrinList = []
    TransferrinSatList = []
    IronList = []
    TIBCList = []
    totalHgbDropList = []


    # Iterate over every patient
    fFoundPatient = srcTDF.GotoFirstPatient()
    while (fFoundPatient):
        numPatients += 1

        # Get a list of all admissions.
        admissionList = srcTDF.GetAdmissionsForCurrentPatient()
        srcTDF.ExpandAdmissionListWithHgbDropAndTransfusions(admissionList)

        # Process the list, and for each admission, add pairs of values we will use for covariance.
        for admissionInfo in admissionList:
            DDimer = admissionInfo['DDimer']
            Fibrinogen = admissionInfo['Fibrinogen']
            Haptoglobin = admissionInfo['Haptoglobin']
            LDH = admissionInfo['LDH']
            Transferrin = admissionInfo['Transferrin']
            TransferrinSat = admissionInfo['TransferrinSat']
            Iron = admissionInfo['Iron']
            TIBC = admissionInfo['TIBC']

            # Compute the drop in Hemoglobin for this admission.
            # There are several ways to do this, explored more below.
            dropInHgb = (admissionInfo['largestHgbValue'] - admissionInfo['smallestHgbValue'])  + (HGB_RISE_PER_TRANSFUSION * admissionInfo['NumTransfusions'])

            # Add this value to the lists we will use to compute covariance
            numTransfusionsList.append(admissionInfo['NumTransfusions'])
            firstHgbValueList.append(admissionInfo['firstHgbValue'])
            DDimerList.append(DDimer)
            FibrinogenList.append(Fibrinogen)
            HaptoglobinList.append(Haptoglobin)
            LDHList.append(LDH)
            TransferrinList.append(Transferrin)
            TransferrinSatList.append(TransferrinSat)
            IronList.append(Iron)
            TIBCList.append(TIBC)
            totalHgbDropList.append(dropInHgb)

            # Build a set of histograms for no-anemia, mild, moderate, severe
            # No anemia
            if (dropInHgb <= MIN_HGB_DROP_FOR_MILD_ANEMIA):
                startHgbValueNoAnemia.AddValue(admissionInfo['firstHgbValue'])
                ddimerValueNoAnemia.AddValue(DDimer)
                fibrinogenValueNoAnemia.AddValue(Fibrinogen)
                TIBCValueNoAnemia.AddValue(TIBC)
                TransferrinValueNoAnemia.AddValue(Transferrin)
                LDHValueNoAnemia.AddValue(LDH)
                HaptoglobinValueNoAnemia.AddValue(Haptoglobin)
                IronValueNoAnemia.AddValue(Iron)
            # Mild anemia
            elif (dropInHgb <= MIN_HGB_DROP_FOR_MODERATE_ANEMIA):
                startHgbValueMildAnemia.AddValue(admissionInfo['firstHgbValue'])
                ddimerValueMildAnemia.AddValue(DDimer)
                fibrinogenValueMildAnemia.AddValue(Fibrinogen)
                TIBCValueMildAnemia.AddValue(TIBC)
                TransferrinValueMildAnemia.AddValue(Transferrin)
                LDHValueMildAnemia.AddValue(LDH)
                HaptoglobinValueMildAnemia.AddValue(Haptoglobin)
                IronValueMildAnemia.AddValue(Iron)
            # Moderate Anemia
            elif (dropInHgb <= MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                startHgbValueModAnemia.AddValue(admissionInfo['firstHgbValue'])
                ddimerValueModAnemia.AddValue(DDimer)
                fibrinogenValueModAnemia.AddValue(Fibrinogen)
                TIBCValueModAnemia.AddValue(TIBC)
                TransferrinValueModAnemia.AddValue(Transferrin)
                LDHValueModAnemia.AddValue(LDH)
                HaptoglobinValueModAnemia.AddValue(Haptoglobin)
                IronValueModAnemia.AddValue(Iron)
            # Severe Anemia
            else:
                startHgbValueSevereAnemia.AddValue(admissionInfo['firstHgbValue'])
                ddimerValueSevereAnemia.AddValue(DDimer)
                fibrinogenValueSevereAnemia.AddValue(Fibrinogen)
                TIBCValueSevereAnemia.AddValue(TIBC)
                TransferrinValueSevereAnemia.AddValue(Transferrin)
                LDHValueSevereAnemia.AddValue(LDH)
                HaptoglobinValueSevereAnemia.AddValue(Haptoglobin)
                IronValueSevereAnemia.AddValue(Iron)
        # End - for admissionInfo in admissionList:

        fFoundPatient = srcTDF.GotoNextPatient()
    # End - while (patientNode):

    srcTDF.Shutdown() 

    # Now, compute the correlations
    try:
        transferrinToHgbDropCorrelation, transferrinToHgbDropPValue = spearmanr(TransferrinList, totalHgbDropList)
    except Exception:
        transferrinToHgbDropCorrelation = 0
    if (math.isnan(transferrinToHgbDropCorrelation)):
        transferrinToHgbDropCorrelation = 0

    try:
        firstHgbToHgbDropCorrelation, firstHgbToHgbDropPValue = spearmanr(firstHgbValueList, totalHgbDropList)
    except Exception:
        firstHgbToHgbDropCorrelation = 0
    if (math.isnan(firstHgbToHgbDropCorrelation)):
        firstHgbToHgbDropCorrelation = 0

    try:
        TIBCToHgbDropCorrelation, TIBCToHgbDropPValue = spearmanr(TIBCList, totalHgbDropList)
    except Exception:
        TIBCToHgbDropCorrelation = 0
    if (math.isnan(TIBCToHgbDropCorrelation)):
        TIBCToHgbDropCorrelation = 0

    try:
        DDimerToHgbDropCorrelation, DDimerToHgbDropPValue = spearmanr(DDimerList, totalHgbDropList)
    except Exception:
        DDimerToHgbDropCorrelation = 0
    if (math.isnan(DDimerToHgbDropCorrelation)):
        DDimerToHgbDropCorrelation = 0

    try:
        TransferrinSatToHgbDropCorrelation, TransferrinSatToHgbDropPValue = spearmanr(TransferrinSatList, totalHgbDropList)
    except Exception:
        TransferrinSatToHgbDropCorrelation = 0
    if (math.isnan(TransferrinSatToHgbDropCorrelation)):
        TransferrinSatToHgbDropCorrelation = 0

    try:
        LDHToHgbDropCorrelation, LDHToHgbDropPValue = spearmanr(LDHList, totalHgbDropList)
    except Exception:
        LDHToHgbDropCorrelation = 0
    if (math.isnan(LDHToHgbDropCorrelation)):
        LDHToHgbDropCorrelation = 0

    try:
        IronToHgbDropCorrelation, IronToHgbDropPValue = spearmanr(IronList, totalHgbDropList)
    except Exception:
        IronToHgbDropCorrelation = 0
    if (math.isnan(IronToHgbDropCorrelation)):
        IronToHgbDropCorrelation = 0

    try:
        FibrinogenToHgbDropCorrelation, FibrinogenToHgbDropPValue = spearmanr(FibrinogenList, totalHgbDropList)
    except Exception:
        FibrinogenToHgbDropCorrelation = 0
    if (math.isnan(FibrinogenToHgbDropCorrelation)):
        FibrinogenToHgbDropCorrelation = 0


    # Print the correlations between Blood loss and Transferrin, TIBC, Iron
    print("\n\n\nCORRELATIONS:")
    print("transferrinToHgbDropCorrelation = " + str(round(transferrinToHgbDropCorrelation, 4)))
    print("firstHgbToHgbDropCorrelation = " + str(round(firstHgbToHgbDropCorrelation, 4)))
    print("TIBCToHgbDropCorrelation = " + str(round(TIBCToHgbDropCorrelation, 4)))
    print("DDimerToHgbDropCorrelation = " + str(round(DDimerToHgbDropCorrelation, 4)))
    print("TransferrinSatToHgbDropCorrelation = " + str(round(TransferrinSatToHgbDropCorrelation, 4)))
    print("LDHToHgbDropCorrelation = " + str(round(LDHToHgbDropCorrelation, 4)))
    print("IronToHgbDropCorrelation = " + str(round(IronToHgbDropCorrelation, 4)))
    print("FibrinogenToHgbDropCorrelation = " + str(round(FibrinogenToHgbDropCorrelation, 4)))


    # Show histograms of labs like Transferrin/TIBC/Iron etc in Pts with 
    # none/mild/moderate and severe anemia
    tdfShow.ShowFourHistogramsOnOneGraph("Values of Initial Hemoglobin for Anemia", 
                                "Initial Hemoglobin", "Fraction of Cases",
                                startHgbValueNoAnemia, "No Anemia", 'g', 
                                startHgbValueMildAnemia, "Mild Anemia", 'y', 
                                startHgbValueModAnemia, "Mod Anemia", 'o', 
                                startHgbValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramInitialHemoglobinvsLevelOfAnemia.jpg")
    tdfShow.ShowFourHistogramsOnOneGraph("Values of DDimer for Anemia", 
                                "DDimer", "Fraction of Cases",
                                ddimerValueNoAnemia, "No Anemia", 'g', 
                                ddimerValueMildAnemia, "Mild Anemia", 'y', 
                                ddimerValueModAnemia, "Mod Anemia", 'o', 
                                ddimerValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramDDimervsLevelOfAnemia.jpg")
    tdfShow.ShowFourHistogramsOnOneGraph("Values of Fibrinogen for Anemia", 
                                "Fibrinogen", "Fraction of Cases",
                                fibrinogenValueNoAnemia, "No Anemia", 'g', 
                                fibrinogenValueMildAnemia, "Mild Anemia", 'y', 
                                fibrinogenValueModAnemia, "Mod Anemia", 'o', 
                                fibrinogenValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramFibrinogenvsLevelOfAnemia.jpg")
    tdfShow.ShowFourHistogramsOnOneGraph("Values of TIBC for Anemia", 
                                "TIBC", "Fraction of Cases",
                                TIBCValueNoAnemia, "No Anemia", 'g', 
                                TIBCValueMildAnemia, "Mild Anemia", 'y', 
                                TIBCValueModAnemia, "Mod Anemia", 'o', 
                                TIBCValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramTIBCvsLevelOfAnemia.jpg")
    tdfShow.ShowFourHistogramsOnOneGraph("Values of Haptoglobin for Anemia", 
                                "Haptoglobin", "Fraction of Cases",
                                HaptoglobinValueNoAnemia, "No Anemia", 'g', 
                                HaptoglobinValueMildAnemia, "Mild Anemia", 'y', 
                                HaptoglobinValueModAnemia, "Mod Anemia", 'o', 
                                HaptoglobinValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramHaptoglobinvsLevelOfAnemia.jpg")
    tdfShow.ShowFourHistogramsOnOneGraph("Values of Transferrin for Anemia", 
                                "Transferrin", "Fraction of Cases",
                                TransferrinValueNoAnemia, "No Anemia", 'g', 
                                TransferrinValueModAnemia, "Mod Anemia", 'o', 
                                TransferrinValueMildAnemia, "Mild Anemia", 'y', 
                                TransferrinValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramTransferrinvsLevelOfAnemia.jpg")
    tdfShow.ShowFourHistogramsOnOneGraph("Values of LDH for Anemia", 
                                "LDH", "Fraction of Cases",
                                LDHValueNoAnemia, "No Anemia", 'g', 
                                LDHValueMildAnemia, "Mild Anemia", 'y', 
                                LDHValueModAnemia, "Mod Anemia", 'o', 
                                LDHValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramLDHvsLevelOfAnemia.jpg")
    tdfShow.ShowFourHistogramsOnOneGraph("Values of Iron for Anemia", 
                                "Iron", "Fraction of Cases",
                                IronValueNoAnemia, "No Anemia", 'g', 
                                IronValueMildAnemia, "Mild Anemia", 'y', 
                                IronValueModAnemia, "Mod Anemia", 'o', 
                                IronValueSevereAnemia, "Severe Anemia", 'r', 
                                False, g_ReportDir + "HistogramIronvsLevelOfAnemia.jpg")
# End - ShowCorrelationOfAnemiaAndIronMarkers









################################################################################
#
# [ShowEventsDuringAnemia]
#
################################################################################
def ShowEventsDuringAnemia(tdfFilePathName, reportFilePathname):
    fDebug = False
    numPatients = 0
    numAdmissions = 0
    numAdmissionsWithTransfusion = 0
    numAdmissionsWithNoAnemia = 0
    numAdmissionsWithMildAnemia = 0
    numAdmissionsWithModAnemia = 0
    numAdmissionsWithSevereAnemia = 0
    totalNumLabsCollected = 0

    totalNumTransfusions = 0
    totalHgbFirstToLastDrop = 0
    totalHgbPeakToTroughDrop = 0
    totalPltFirstToLastDrop = 0
    totalPltPeakToTroughDrop = 0
    numTransfusions = 0
    numPatientsWithTransfusions = 0
    totalNumAnemiaOnAdmitWHO = 0
    totalNumAnemiaSalisbury = 0
    totalNumNoAnemiaPeakToTrough = 0
    totalNumMildAnemiaPeakToTrough = 0
    totalNumModAnemiaPeakToTrough = 0
    totalNumSevereAnemiaPeakToTrough = 0
    totalNumNoAnemiaFirstToLast = 0
    totalNumMildAnemiaFirstToLast = 0
    totalNumModAnemiaFirstToLast = 0
    totalNumSevereAnemiaFirstToLast = 0

    totalHgbDropWithNoAnemia = 0
    numNoAnemiaWithPltsBelow50 = 0
    numNoAnemiaWithPltsBelow100 = 0
    numNoAnemiaWithWBCOver12 = 0
    numNoAnemiaWithWBCOver15 = 0
    numNoAnemiaOnIVAntibiotics = 0
    numNoAnemiaWithSurgery = 0
    numNoAnemiaWithGIProcedures = 0
    numNoAnemiaDDimersFound = 0
    numNoAnemiaWithHighDDimers = 0
    numNoAnemiaFibrinogensFound = 0
    numNoAnemiaWithFibrinogenBelowNormal = 0
    numNoAnemiaWithLikelyDIC = 0
    numNoAnemiaWithPossibleDIC = 0
    NoAnemiaNoDICNumLabsCollectedList = []
    NoAnemiaNoDICMaxHgbDropList = []

    totalHgbDropWithMildAnemia = 0
    numMildAnemiaWithPltsBelow50 = 0
    numMildAnemiaWithPltsBelow100 = 0
    numMildAnemiaWithWBCOver12 = 0
    numMildAnemiaWithWBCOver15 = 0
    numMildAnemiaOnIVAntibiotics = 0
    numMildAnemiaWithSurgery = 0
    numMildAnemiaWithGIProcedures = 0
    numMildAnemiaDDimersFound = 0
    numMildAnemiaWithHighDDimers = 0
    numMildAnemiaFibrinogensFound = 0
    numMildAnemiaWithFibrinogenBelowNormal = 0
    numMildAnemiaWithLikelyDIC = 0
    numMildAnemiaWithPossibleDIC = 0
    MildAnemiaNoDICNumLabsCollectedList = []
    MildAnemiaNoDICMaxHgbDropList = []

    totalHgbDropWithModAnemia = 0
    numModAnemiaWithPltsBelow50 = 0
    numModAnemiaWithPltsBelow100 = 0
    numModAnemiaWithWBCOver12 = 0
    numModAnemiaWithWBCOver15 = 0
    numModAnemiaOnIVAntibiotics = 0
    numModAnemiaWithSurgery = 0
    numModAnemiaWithGIProcedures = 0
    numModAnemiaDDimersFound = 0
    numModAnemiaWithHighDDimers = 0
    numModAnemiaFibrinogensFound = 0
    numModAnemiaWithFibrinogenBelowNormal = 0
    numModAnemiaWithLikelyDIC = 0
    numModAnemiaWithPossibleDIC = 0
    ModAnemiaNoDICNumLabsCollectedList = []
    ModAnemiaNoDICMaxHgbDropList = []

    totalHgbDropWithSevereAnemia = 0
    numSevereAnemiaWithPltsBelow50 = 0
    numSevereAnemiaWithPltsBelow100 = 0
    numSevereAnemiaWithWBCOver12 = 0
    numSevereAnemiaWithWBCOver15 = 0
    numSevereAnemiaOnIVAntibiotics = 0
    numSevereAnemiaWithSurgery = 0
    numSevereAnemiaWithGIProcedures = 0
    numSevereAnemiaDDimersFound = 0
    numSevereAnemiaWithHighDDimers = 0
    numSevereAnemiaFibrinogensFound = 0
    numSevereAnemiaWithFibrinogenBelowNormal = 0
    numSevereAnemiaWithLikelyDIC = 0
    numSevereAnemiaWithPossibleDIC = 0
    SevereAnemiaNoDICNumLabsCollectedList = []
    SevereAnemiaNoDICMaxHgbDropList = []

    # Make lists that we will use to compute Covariances
    totalHgbDropList = []
    totalPltDropList = []
    numLabsCollectedList = []
    numTransfusionsList = []
    minPlateletsList = []
    firstHgbValueList = []
    numIVAntibioticsList = []
    numSurgeriesList = []
    numGIProceduresList = []
    highestWBCList = []
    LengthOfStayList = []
    numDaysWithLabsList = []

    # Not sure if these are useful
    DDimerList = []
    FibrinogenList = []
    HaptoglobinList = []
    LDHList = []
    TransferrinList = []
    TransferrinSatList = []
    IronList = []
    TIBCList = []

    # Create and initialize the histograms
    maxDaysInReasonableHospitalStay = 60
    HospDayOfTransfusionHistogram = [0] * maxDaysInReasonableHospitalStay
    LabsBeforeTransfusionHistogram = [0] * maxDaysInReasonableHospitalStay
    numDaysInpatientPerAdmissionHistogram = [0] * maxDaysInReasonableHospitalStay
    numLabsDrawnPerAdmissionHistogram = [0] * maxDaysInReasonableHospitalStay
    numPercentagePoints = 100
    transfusionsOnPercentageLabs = [0] * numPercentagePoints

    # Create and Initialize the Comorbidity groups
    allPatientsComorbidityGroup = Elixhauser.ElixhauserGroup()
    noAnemiaComorbidityGroup = Elixhauser.ElixhauserGroup()
    mildAnemiaComorbidityGroup = Elixhauser.ElixhauserGroup()
    modAnemiaComorbidityGroup = Elixhauser.ElixhauserGroup()
    severeAnemiaComorbidityGroup = Elixhauser.ElixhauserGroup()
    anemiaOnAdmitComorbidityGroup = Elixhauser.ElixhauserGroup()

    print("\n========================\n Correlation between Hgb Drop and Labs")
    srcTDF = tdf.TDF_CreateTDFFileReader(tdfFilePathName, 
                                            "Hgb;WBC;Cr;Plt;Procal;CRP;DDimer;Fibrinogen;LDH;Haptoglobin;VancDose;PipTazoDose;CefepimeDose;DaptoDose;MeroDose;MajorSurgeries;GIProcedures;Tbili;HospitalAdmitDate;InHospital;TransRBC;MajorSurgeries;GIProcedures",
                                            'Hgb',
                                            [])
    srcTDF.SetTimeResolution(1)
    srcTDF.SetCarryForwardPreviousDataValues(False)


    # Iterate over every patient
    fFoundPatient = srcTDF.GotoFirstPatient()
    while (fFoundPatient):
        numPatients += 1
        fPatientReceivedTransfusionOnAnyAdmission = False

        # Get a list of all admissions.
        admissionList = srcTDF.GetAdmissionsForCurrentPatient()
        srcTDF.ExpandAdmissionListWithHgbDropAndTransfusions(admissionList)

        # Process the list, and for each admission, add pairs of values we will use for covariance.
        for admissionInfo in admissionList:
            numAdmissions += 1

            #################################
            # Diagnoses. These are used for Elixhauser stats
            diagnosisList = srcTDF.GetDiagnosesForCurrentPatient(admissionInfo['FirstDay'], 
                                                admissionInfo['LastDay'])
            allPatientsComorbidityGroup.AddDiagnosisList(diagnosisList)

            #################################
            # Derive some values
            # This is questionable - A single CMP may include both a BMP and an LFT.
            # But, if you are getting LFT's you may also be getinng an INR or something else so it
            # may be reasonable.
            numLabsCollected = admissionInfo["numBMPCollected"] + admissionInfo["numCBCCollected"] + admissionInfo["numLFTCollected"]
            totalNumLabsCollected += numLabsCollected
            totalNumTransfusions += admissionInfo['NumTransfusions']
            if (admissionInfo['NumTransfusions'] > 0):
                numAdmissionsWithTransfusion += 1
                fPatientReceivedTransfusionOnAnyAdmission = True

            #################################
            # Compute the drop in Hemoglobin for this admission.
            # There are several ways to do this:
            #    Peak to Trough
            #    First to Last
            # Additionally, we have to take into account the number of transfusions.
            #    TheoreticalMaxHgb = maxHgb + (HGB_RISE_PER_TRANSFUSION * numTransfusions)
            currentHgbDropFirstToLast = (admissionInfo['lastHgbValue'] - admissionInfo['firstHgbValue']) + (HGB_RISE_PER_TRANSFUSION * admissionInfo['NumTransfusions'])
            currentHgbDropPeakToTrough = (admissionInfo['largestHgbValue'] - admissionInfo['smallestHgbValue']) + (HGB_RISE_PER_TRANSFUSION * admissionInfo['NumTransfusions'])
            dropInHgb = currentHgbDropPeakToTrough
            dropInPlts = (admissionInfo["largestPltsValue"] - admissionInfo["smallestPltsValue"])

            totalHgbFirstToLastDrop += currentHgbDropFirstToLast
            totalHgbPeakToTroughDrop += currentHgbDropPeakToTrough
            totalPltFirstToLastDrop += (admissionInfo["lastPltsValue"] - admissionInfo["firstPltsValue"])
            totalPltPeakToTroughDrop += (admissionInfo["largestPltsValue"] - admissionInfo["smallestPltsValue"])

            # WHO Anemia
            if ((admissionInfo["gender"] >= 1) and (admissionInfo['firstHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN)):
                totalNumAnemiaOnAdmitWHO += 1
                anemiaOnAdmitComorbidityGroup.AddDiagnosisList(diagnosisList)
            elif ((admissionInfo["gender"] <= 0) and (admissionInfo['firstHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN)):
                totalNumAnemiaOnAdmitWHO += 1
                anemiaOnAdmitComorbidityGroup.AddDiagnosisList(diagnosisList)
            
            # Salisbury guidelines
            if ((admissionInfo["gender"] >= 1) and (admissionInfo["ageInYrs"] <= 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN_60_AND_UNDER)):
                totalNumAnemiaSalisbury += 1
            elif ((admissionInfo["gender"] >= 1) and (admissionInfo["ageInYrs"] > 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN_OVER_60)):
                totalNumAnemiaSalisbury += 1
            elif ((admissionInfo["gender"] <= 0) and (admissionInfo["ageInYrs"] <= 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN_60_AND_UNDER)):
                totalNumAnemiaSalisbury += 1
            elif ((admissionInfo["gender"] <= 0) and (admissionInfo["ageInYrs"] > 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN_OVER_60)):
                totalNumAnemiaSalisbury += 1

            if (currentHgbDropPeakToTrough < MIN_HGB_DROP_FOR_MILD_ANEMIA):
                totalNumNoAnemiaPeakToTrough += 1
            elif (currentHgbDropPeakToTrough < MIN_HGB_DROP_FOR_MODERATE_ANEMIA):
                totalNumMildAnemiaPeakToTrough += 1
            elif (currentHgbDropPeakToTrough < MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                totalNumModAnemiaPeakToTrough += 1
            else: # elif (currentHgbDropPeakToTrough >= MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                totalNumSevereAnemiaPeakToTrough += 1

            if (currentHgbDropFirstToLast < MIN_HGB_DROP_FOR_MILD_ANEMIA):
                totalNumNoAnemiaFirstToLast += 1
            elif (currentHgbDropFirstToLast < MIN_HGB_DROP_FOR_MODERATE_ANEMIA):
                totalNumMildAnemiaFirstToLast += 1
            elif (currentHgbDropFirstToLast < MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                totalNumModAnemiaFirstToLast += 1
            else: # elif (currentHgbDropFirstToLast >= MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                totalNumSevereAnemiaFirstToLast += 1


            #################################
            # Add the current set of values to the lists we will use to compute covariance
            totalHgbDropList.append(dropInHgb)
            totalPltDropList.append(dropInPlts)
            numLabsCollectedList.append(numLabsCollected)
            firstHgbValueList.append(admissionInfo['firstHgbValue'])
            minPlateletsList.append(admissionInfo["smallestPltsValue"])
            numIVAntibioticsList.append(admissionInfo["numIVAntibiotics"])
            numSurgeriesList.append(admissionInfo["numSurgeries"])
            numGIProceduresList.append(admissionInfo["numGIProcedures"])
            highestWBCList.append(admissionInfo["highestWBC"])
            LengthOfStayList.append(admissionInfo["LengthOfStay"])
            numDaysWithLabsList.append(admissionInfo["numDaysWithLabs"])

            #################################
            # Add the current set of values to histograms
            index = admissionInfo["LengthOfStay"]
            if (index >= maxDaysInReasonableHospitalStay):
                index = maxDaysInReasonableHospitalStay - 1
            if (index > 0):
                numDaysInpatientPerAdmissionHistogram[index] += 1

            index = numLabsCollected
            if (index >= maxDaysInReasonableHospitalStay):
                index = maxDaysInReasonableHospitalStay - 1
            if (index > 0):
                numLabsDrawnPerAdmissionHistogram[index] += 1

            for currentAbsVal in admissionInfo["HospDayOfTransfusionList"]:
                index = currentAbsVal
                if (index >= maxDaysInReasonableHospitalStay):
                    index = maxDaysInReasonableHospitalStay - 1
                if (index > 0):
                    HospDayOfTransfusionHistogram[index] += 1
            # End - for currentAbsVal in admissionInfo["HospDayOfTransfusionList"]:

            for currentAbsVal in admissionInfo["TransfusionsAfterNumLabsList"]:
                index = currentAbsVal
                if (index >= maxDaysInReasonableHospitalStay):
                    index = maxDaysInReasonableHospitalStay - 1
                if (index > 0):
                    LabsBeforeTransfusionHistogram[index] += 1
            # End - for currentAbsVal in admissionInfo["TransfusionsAfterNumLabsList"]:


            ###################################
            # No anemia
            if (dropInHgb <= MIN_HGB_DROP_FOR_MILD_ANEMIA):
                numAdmissionsWithNoAnemia += 1
                totalHgbDropWithNoAnemia += dropInHgb

                # Add the diagnoses for this admission to the Comorbidity group
                noAnemiaComorbidityGroup.AddDiagnosisList(diagnosisList)

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 50)):
                    numNoAnemiaWithPltsBelow50 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numNoAnemiaWithPltsBelow100 += 1

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 15)):
                    numNoAnemiaWithWBCOver15 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 12)):
                    numNoAnemiaWithWBCOver12 += 1

                if (admissionInfo["numIVAntibiotics"] > 0):
                    numNoAnemiaOnIVAntibiotics += 1
                if (admissionInfo["numSurgeries"] > 0):
                    numNoAnemiaWithSurgery += 1
                if (admissionInfo["numGIProcedures"] > 0):
                    numNoAnemiaWithGIProcedures += 1
                if (admissionInfo['DDimer'] > 0):
                    numNoAnemiaDDimersFound += 1
                # Upper normal limit is 0.5. But, to be conservative I use a higher threshold.
                if ((admissionInfo['DDimer'] > 0) and (admissionInfo['DDimer'] > 1.0)):
                    numNoAnemiaWithHighDDimers += 1
                if (admissionInfo['Fibrinogen'] > 0):
                    numNoAnemiaFibrinogensFound += 1
                # Fibrinogen in mg/dL range Normal is 208-459
                if ((admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200)):
                    numNoAnemiaWithFibrinogenBelowNormal += 1
                fPossibleDIC = False
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100) 
                        and (admissionInfo['DDimer'] > 0) and (admissionInfo['DDimer'] > 1.0)):
                    numNoAnemiaWithLikelyDIC += 1
                    fPossibleDIC = True
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numNoAnemiaWithPossibleDIC += 1
                    fPossibleDIC = True
                if (not fPossibleDIC):
                   NoAnemiaNoDICNumLabsCollectedList.append(numLabsCollected)
                   NoAnemiaNoDICMaxHgbDropList.append(dropInHgb)
            # End - if (dropInHgb <= 1.0):

            ###################################
            # Mild anemia
            elif (dropInHgb <= MIN_HGB_DROP_FOR_MODERATE_ANEMIA):
                numAdmissionsWithMildAnemia += 1
                totalHgbDropWithMildAnemia += dropInHgb

                # Add the diagnoses for this admission to the Comorbidity group
                mildAnemiaComorbidityGroup.AddDiagnosisList(diagnosisList)

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 50)):
                    numMildAnemiaWithPltsBelow50 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numMildAnemiaWithPltsBelow100 += 1

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 15)):
                    numMildAnemiaWithWBCOver15 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 12)):
                    numMildAnemiaWithWBCOver12 += 1

                if (admissionInfo["numIVAntibiotics"] > 0):
                    numMildAnemiaOnIVAntibiotics += 1
                if (admissionInfo["numSurgeries"] > 0):
                    numMildAnemiaWithSurgery += 1
                if (admissionInfo["numGIProcedures"] > 0):
                    numMildAnemiaWithGIProcedures += 1
                if (admissionInfo['DDimer'] > 0):
                    numMildAnemiaDDimersFound += 1
                # Upper normal limit is 0.5. But, to be conservative I use a higher threshold.
                if ((admissionInfo['DDimer'] > 0) and (admissionInfo['DDimer'] > 1.0)):
                    numMildAnemiaWithHighDDimers += 1
                if (admissionInfo['Fibrinogen'] > 0):
                    numMildAnemiaFibrinogensFound += 1
                # Fibrinogen in mg/dL range Normal is 208-459
                if ((admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200)):
                    numMildAnemiaWithFibrinogenBelowNormal += 1
                fPossibleDIC = False
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100) 
                        and (admissionInfo['DDimer'] > 0) and (admissionInfo['DDimer'] > 1.0)):
                    numMildAnemiaWithLikelyDIC += 1
                    fPossibleDIC = True
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numMildAnemiaWithPossibleDIC += 1
                    fPossibleDIC = True
                if (not fPossibleDIC):
                   MildAnemiaNoDICNumLabsCollectedList.append(numLabsCollected)
                   MildAnemiaNoDICMaxHgbDropList.append(dropInHgb)
            # End - elif (dropInHgb <= 3.0):

            ###################################
            # Moderate Anemia
            elif (dropInHgb < MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                numAdmissionsWithModAnemia += 1
                totalHgbDropWithModAnemia += dropInHgb

                # Add the diagnoses for this admission to the Comorbidity group
                modAnemiaComorbidityGroup.AddDiagnosisList(diagnosisList)

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 50)):
                    numModAnemiaWithPltsBelow50 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numModAnemiaWithPltsBelow100 += 1

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 15)):
                    numModAnemiaWithWBCOver15 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 12)):
                    numModAnemiaWithWBCOver12 += 1

                if (admissionInfo["numIVAntibiotics"] > 0):
                    numModAnemiaOnIVAntibiotics += 1
                if (admissionInfo["numSurgeries"] > 0):
                    numModAnemiaWithSurgery += 1
                if (admissionInfo["numGIProcedures"] > 0):
                    numModAnemiaWithGIProcedures += 1
                if (admissionInfo['DDimer'] > 0):
                    numModAnemiaDDimersFound += 1
                # Upper normal limit is 0.5. But, to be conservative I use a higher threshold.
                if ((admissionInfo['DDimer'] > 0) and (admissionInfo['DDimer'] > 1.0)):
                    numModAnemiaWithHighDDimers += 1
                if (admissionInfo['Fibrinogen'] > 0):
                    numModAnemiaFibrinogensFound += 1
                # Fibrinogen in mg/dL range Normal is 208-459
                if ((admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200)):
                    numModAnemiaWithFibrinogenBelowNormal += 1
                fPossibleDIC = False
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100) 
                        and (admissionInfo['DDimer'] > 0) and (admissionInfo['DDimer'] > 1.0)):
                    numModAnemiaWithLikelyDIC += 1
                    fPossibleDIC = True
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numModAnemiaWithPossibleDIC += 1
                    fPossibleDIC = True
                if (not fPossibleDIC):
                   ModAnemiaNoDICNumLabsCollectedList.append(numLabsCollected)
                   ModAnemiaNoDICMaxHgbDropList.append(dropInHgb)
            # End - elif (dropInHgb < MIN_HGB_DROP_FOR_SEVERE_ANEMIA):

            ###################################
            # Severe Anemia
            elif (dropInHgb >= MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                numAdmissionsWithSevereAnemia += 1
                totalHgbDropWithSevereAnemia += dropInHgb

                # Add the diagnoses for this admission to the Comorbidity group
                severeAnemiaComorbidityGroup.AddDiagnosisList(diagnosisList)

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 50)):
                    numSevereAnemiaWithPltsBelow50 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numSevereAnemiaWithPltsBelow100 += 1

                if ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 15)):
                    numSevereAnemiaWithWBCOver15 += 1
                elif ((tdf.TDF_INVALID_VALUE != admissionInfo["highestWBC"]) and (admissionInfo["highestWBC"] >= 12)):
                    numSevereAnemiaWithWBCOver12 += 1

                if (admissionInfo["numIVAntibiotics"] > 0):
                    numSevereAnemiaOnIVAntibiotics += 1
                if (admissionInfo["numSurgeries"] > 0):
                    numSevereAnemiaWithSurgery += 1
                if (admissionInfo["numGIProcedures"] > 0):
                    numSevereAnemiaWithGIProcedures += 1
                if (admissionInfo['DDimer'] > 0):
                    numSevereAnemiaDDimersFound += 1
                # Upper normal limit is 0.5. But, to be conservative I use a higher threshold.
                if (admissionInfo['DDimer'] > 1.0):
                    numSevereAnemiaWithHighDDimers += 1
                if (admissionInfo['Fibrinogen'] > 0):
                    numSevereAnemiaFibrinogensFound += 1
                # Fibrinogen in mg/dL range Normal is 208-459
                if ((admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200)):
                    numSevereAnemiaWithFibrinogenBelowNormal += 1
                fPossibleDIC = False
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (admissionInfo['Fibrinogen'] > 0) and (admissionInfo['Fibrinogen'] < 200) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100) 
                        and (admissionInfo['DDimer'] > 1.0)):
                    numSevereAnemiaWithLikelyDIC += 1
                    fPossibleDIC = True
                if ((admissionInfo["numIVAntibiotics"] > 0) 
                        and (tdf.TDF_INVALID_VALUE != admissionInfo["smallestPltsValue"]) and (admissionInfo["smallestPltsValue"] < 100)):
                    numSevereAnemiaWithPossibleDIC += 1
                    fPossibleDIC = True
                if (not fPossibleDIC):
                   SevereAnemiaNoDICNumLabsCollectedList.append(numLabsCollected)
                   SevereAnemiaNoDICMaxHgbDropList.append(dropInHgb)
            # End - elif (dropInHgb > MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
        # End - for admissionInfo in admissionList:

        if (fPatientReceivedTransfusionOnAnyAdmission):
            numPatientsWithTransfusions += 1

        fFoundPatient = srcTDF.GotoNextPatient()
    # End - while (fFoundPatient):

    srcTDF.Shutdown() 


    ########################################
    # Print Statistics
    print("\n\n\nStatistics")
    print("\n===========================")
    print("numPatients = " + str(numPatients))
    print("numAdmissions = " + str(numAdmissions))
    print("numAdmissionsWithNoAnemia = " + str(numAdmissionsWithNoAnemia))
    print("numAdmissionsWithMildAnemia = " + str(numAdmissionsWithMildAnemia))
    print("numAdmissionsWithModAnemia = " + str(numAdmissionsWithModAnemia))
    print("numAdmissionsWithSevereAnemia = " + str(numAdmissionsWithSevereAnemia))
    print("\n===========================")
    print("Total Admissions with Transfusions = " + str(numAdmissionsWithTransfusion))
    print("Total Patients Who Received Transfusions = " + str(numPatientsWithTransfusions))
    print("Total numTransfusions = " + str(totalNumTransfusions))
    print("Avg Transfusions Per Admission = " + str(round((totalNumTransfusions / numAdmissionsWithTransfusion), 2)))
    print("\n===========================")
    print("Total num Labs Collected = " + str(totalNumLabsCollected))
    print("\n===========================")
    print("Average Hgb Drop Per Admission (PeakToTrough)= " + str(round((totalHgbPeakToTroughDrop / numAdmissions), 2)))
    print("Average Hgb Drop Per Admission (First to Last)= " + str(round((totalHgbFirstToLastDrop / numAdmissions), 2)))
    print("Average Plt Drop Per Admission (PeakToTrough)= " + str(round((totalPltPeakToTroughDrop / numAdmissions), 2)))
    print("Average Plt Drop Per Admission (First to Last)= " + str(round((totalPltFirstToLastDrop / numAdmissions), 2)))
    print("\n===========================")
    print("Fraction numAdmissionsWith No Anemia = " + str(round((numAdmissionsWithNoAnemia / numAdmissions), 2)))
    print("Average Hgb Drop with No Anemia = " + str(round((totalHgbDropWithNoAnemia / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia with Plts < 50 = " + str(round((numNoAnemiaWithPltsBelow50 / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia with Plts < 100 = " + str(round((numNoAnemiaWithPltsBelow100 / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia with WBC >= 12 = " + str(round((numNoAnemiaWithWBCOver12 / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia with WBC >= 15 = " + str(round((numNoAnemiaWithWBCOver15 / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia On IV Antibiotics = " + str(round((numNoAnemiaOnIVAntibiotics / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia With Surgery = " + str(round((numNoAnemiaWithSurgery / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia With GI Procedures = " + str(round((numNoAnemiaWithGIProcedures / numAdmissionsWithNoAnemia), 2)))
    print("Fraction No Anemia With DDimer = " + str(round((numNoAnemiaDDimersFound / numAdmissionsWithNoAnemia), 2)))
    print("Fraction High DDimers in No Anemia = " + str(round((numNoAnemiaWithHighDDimers / numNoAnemiaDDimersFound), 2)))
    print("Fraction No Anemia With Fibrinogen = " + str(round((numNoAnemiaFibrinogensFound / numAdmissionsWithNoAnemia), 2)))
    print("Fraction Fibrinogen < 1 in No Anemia = " + str(round((numNoAnemiaWithFibrinogenBelowNormal / numNoAnemiaFibrinogensFound), 2)))
    print("Fraction No Anemias with Likely DIC = " + str(round((numNoAnemiaWithLikelyDIC / numAdmissionsWithNoAnemia), 4)))
    print("Fraction No Anemias with Possible DIC = " + str(round((numNoAnemiaWithPossibleDIC / numAdmissionsWithNoAnemia), 2)))
    print("\n===========================")
    print("Fraction numAdmissionsWith MildAnemia = " + str(round((numAdmissionsWithMildAnemia / numAdmissions), 2)))
    print("Average MildAnemia = " + str(round((totalHgbDropWithMildAnemia / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia with Plts < 50 = " + str(round((numMildAnemiaWithPltsBelow50 / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia with Plts < 100 = " + str(round((numMildAnemiaWithPltsBelow100 / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia with WBC >= 12 = " + str(round((numMildAnemiaWithWBCOver12 / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia with WBC >= 15 = " + str(round((numMildAnemiaWithWBCOver15 / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia On IV Antibiotics = " + str(round((numMildAnemiaOnIVAntibiotics / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia With Surgery = " + str(round((numMildAnemiaWithSurgery / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia With GI Procedures = " + str(round((numMildAnemiaWithGIProcedures / numAdmissionsWithMildAnemia), 2)))
    print("Fraction MildAnemia With DDimer = " + str(round((numMildAnemiaDDimersFound / numAdmissionsWithMildAnemia), 2)))
    print("Fraction High DDimers in MildAnemia = " + str(round((numMildAnemiaWithHighDDimers / numMildAnemiaDDimersFound), 2)))
    print("Fraction MildAnemia With Fibrinogen = " + str(round((numMildAnemiaFibrinogensFound / numAdmissionsWithMildAnemia), 2)))
    print("Fraction Fibrinogen < 1 in MildAnemia = " + str(round((numMildAnemiaWithFibrinogenBelowNormal / numMildAnemiaFibrinogensFound), 2)))
    print("Fraction MildAnemias with Likely DIC = " + str(round((numMildAnemiaWithLikelyDIC / numAdmissionsWithMildAnemia), 4)))
    print("Fraction MildAnemias with Possible DIC = " + str(round((numMildAnemiaWithPossibleDIC / numAdmissionsWithMildAnemia), 2)))
    print("\n===========================")
    print("Fraction numAdmissionsWith ModAnemia = " + str(round((numAdmissionsWithModAnemia / numAdmissions), 2)))
    print("Average ModAnemia = " + str(round((totalHgbDropWithModAnemia / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia with Plts < 50 = " + str(round((numModAnemiaWithPltsBelow50 / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia with Plts < 100 = " + str(round((numModAnemiaWithPltsBelow100 / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia with WBC >= 12 = " + str(round((numModAnemiaWithWBCOver12 / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia with WBC >= 15 = " + str(round((numModAnemiaWithWBCOver15 / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia On IV Antibiotics = " + str(round((numModAnemiaOnIVAntibiotics / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia With Surgery = " + str(round((numModAnemiaWithSurgery / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia With GI Procedures = " + str(round((numModAnemiaWithGIProcedures / numAdmissionsWithModAnemia), 2)))
    print("Fraction ModAnemia With DDimer = " + str(round((numModAnemiaDDimersFound / numAdmissionsWithModAnemia), 2)))
    print("Fraction High DDimers in ModAnemia = " + str(round((numModAnemiaWithHighDDimers / numModAnemiaDDimersFound), 2)))
    print("Fraction ModAnemia With Fibrinogen = " + str(round((numModAnemiaFibrinogensFound / numAdmissionsWithModAnemia), 2)))
    print("Fraction Fibrinogen < 1 in ModAnemia = " + str(round((numModAnemiaWithFibrinogenBelowNormal / numModAnemiaFibrinogensFound), 2)))
    print("Fraction ModAnemias with Likely DIC = " + str(round((numModAnemiaWithLikelyDIC / numAdmissionsWithModAnemia), 4)))
    print("Fraction ModAnemias with Possible DIC = " + str(round((numModAnemiaWithPossibleDIC / numAdmissionsWithModAnemia), 2)))
    print("\n===========================")
    print("Fraction numAdmissionsWith SevereAnemia = " + str(round((numAdmissionsWithSevereAnemia / numAdmissions), 2)))
    print("Average SevereAnemia = " + str(round((totalHgbDropWithSevereAnemia / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia with Plts < 50 = " + str(round((numSevereAnemiaWithPltsBelow50 / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia with Plts < 100 = " + str(round((numSevereAnemiaWithPltsBelow100 / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia with WBC >= 12 = " + str(round((numSevereAnemiaWithWBCOver12 / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia with WBC >= 15 = " + str(round((numSevereAnemiaWithWBCOver15 / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia On IV Antibiotics = " + str(round((numSevereAnemiaOnIVAntibiotics / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia With Surgery = " + str(round((numSevereAnemiaWithSurgery / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia With GI Procedures = " + str(round((numSevereAnemiaWithGIProcedures / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction SevereAnemia With DDimer = " + str(round((numSevereAnemiaDDimersFound / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction High DDimers in SevereAnemia = " + str(round((numSevereAnemiaWithHighDDimers / numSevereAnemiaDDimersFound), 2)))
    print("Fraction SevereAnemia With Fibrinogen = " + str(round((numSevereAnemiaFibrinogensFound / numAdmissionsWithSevereAnemia), 2)))
    print("Fraction Fibrinogen < 1 in SevereAnemia = " + str(round((numSevereAnemiaWithFibrinogenBelowNormal / numSevereAnemiaFibrinogensFound), 2)))
    print("Fraction SevereAnemia with Likely DIC = " + str(round((numSevereAnemiaWithLikelyDIC / numAdmissionsWithSevereAnemia), 4)))
    print("Fraction SevereAnemia with Possible DIC = " + str(round((numSevereAnemiaWithPossibleDIC / numAdmissionsWithSevereAnemia), 2)))


    ########################################
    # Print Correlations
    print("\n\n\nCorrelations")
    print("\n===========================")

    ####################################
    try:
        firstHgbToHgbDropCorrelation, pValue = spearmanr(firstHgbValueList, totalHgbDropList)
    except Exception:
        firstHgbToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(firstHgbToHgbDropCorrelation)):
        firstHgbToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman First Hgb vs Hgb Drop = " + str(firstHgbToHgbDropCorrelation) + ", pVal=" + str(pValue))


    ####################################
    try:
        numLabsToHgbDropCorrelation, pValue = spearmanr(numLabsCollectedList, totalHgbDropList)
    except Exception:
        numLabsToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(numLabsToHgbDropCorrelation)):
        numLabsToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Num Labs vs Hgb Drop = " + str(numLabsToHgbDropCorrelation) + ", pVal=" + str(pValue))

    try:
        numDaysWithLabsToHgbDropCorrelation, pValue = spearmanr(numDaysWithLabsList, totalHgbDropList)
    except Exception:
        numDaysWithLabsToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(numDaysWithLabsToHgbDropCorrelation)):
        numDaysWithLabsToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Num Days With Labs vs Hgb Drop = " + str(numDaysWithLabsToHgbDropCorrelation) + ", pVal=" + str(pValue))

    try:
        lengthOfStayToHgbDropCorrelation, pValue = spearmanr(LengthOfStayList, totalHgbDropList)
    except Exception:
        lengthOfStayToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(lengthOfStayToHgbDropCorrelation)):
        lengthOfStayToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Length Of Stay vs Hgb Drop = " + str(lengthOfStayToHgbDropCorrelation) + ", pVal=" + str(pValue))


    ####################################
    try:
        numLabsToPltDropCorrelation, pValue = spearmanr(numLabsCollectedList, totalPltDropList)
    except Exception:
        numLabsToPltDropCorrelation = 0
        pValue = 0
    if (math.isnan(numLabsToPltDropCorrelation)):
        numLabsToPltDropCorrelation = 0
        pValue = 0
    print("Spearman Num Labs vs Plt Drop = " + str(numLabsToPltDropCorrelation) + ", pVal=" + str(pValue))

    try:
        numDaysWithLabsToPltDropCorrelation, pValue = spearmanr(numDaysWithLabsList, totalPltDropList)
    except Exception:
        numDaysWithLabsToPltDropCorrelation = 0
        pValue = 0
    if (math.isnan(numDaysWithLabsToPltDropCorrelation)):
        numDaysWithLabsToPltDropCorrelation = 0
        pValue = 0
    print("Spearman Num Days With Labs vs Hgb Drop = " + str(numDaysWithLabsToPltDropCorrelation) + ", pVal=" + str(pValue))

    try:
        lengthOfStayToPltDropCorrelation, pValue = spearmanr(LengthOfStayList, totalPltDropList)
    except Exception:
        lengthOfStayToPltDropCorrelation = 0
        pValue = 0
    if (math.isnan(lengthOfStayToPltDropCorrelation)):
        lengthOfStayToPltDropCorrelation = 0
        pValue = 0
    print("Spearman Length Of Stay vs Plt Drop = " + str(lengthOfStayToPltDropCorrelation) + ", pVal=" + str(pValue))





    ####################################
    try:
        pltDropToHgbDropCorrelation, pValue = spearmanr(totalPltDropList, totalHgbDropList)
    except Exception:
        pltDropToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(pltDropToHgbDropCorrelation)):
        pltDropToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Plt Drop vs Hgb Drop = " + str(pltDropToHgbDropCorrelation) + ", pVal=" + str(pValue))

    try:
        minPltsToHgbDropCorrelation, pValue = spearmanr(minPlateletsList, totalHgbDropList)
    except Exception:
        minPltsToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(minPltsToHgbDropCorrelation)):
        minPltsToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Min Plts vs Hgb Drop = " + str(minPltsToHgbDropCorrelation) + ", pVal=" + str(pValue))


    ####################################
    try:
        numAntibioticsToHgbDropCorrelation, pValue = spearmanr(numIVAntibioticsList, totalHgbDropList)
    except Exception:
        numAntibioticsToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(numAntibioticsToHgbDropCorrelation)):
        numAntibioticsToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Num Antibiotics vs Hgb Drop = " + str(numAntibioticsToHgbDropCorrelation) + ", pVal=" + str(pValue))

    try:
        numSurgeriesToHgbDropCorrelation, pValue = spearmanr(numSurgeriesList, totalHgbDropList)
    except Exception:
        numSurgeriesToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(numSurgeriesToHgbDropCorrelation)):
        numSurgeriesToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Num Surgeries vs Hgb Drop = " + str(numSurgeriesToHgbDropCorrelation) + ", pVal=" + str(pValue))

    try:
        numGIProceduresToHgbDropCorrelation, pValue = spearmanr(numGIProceduresList, totalHgbDropList)
    except Exception:
        numGIProceduresToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(numGIProceduresToHgbDropCorrelation)):
        numGIProceduresToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Num GI Procedures vs Hgb Drop = " + str(numGIProceduresToHgbDropCorrelation) + ", pVal=" + str(pValue))

    try:
        highestWBCToHgbDropCorrelation, pValue = spearmanr(highestWBCList, totalHgbDropList)
    except Exception:
        highestWBCToHgbDropCorrelation = 0
        pValue = 0
    if (math.isnan(highestWBCToHgbDropCorrelation)):
        highestWBCToHgbDropCorrelation = 0
        pValue = 0
    print("Spearman Highest WBC vs Hgb Drop = " + str(highestWBCToHgbDropCorrelation) + ", pVal=" + str(pValue))





    ########################################
    # Draw Graphs
    dayNumList = []
    for index in range(maxDaysInReasonableHospitalStay - 1):
        dayNumList.append(str(index + 1))

    DataShow.DrawDoubleBarGraph("Anemia by Peak to Trough vs First to Last", 
                                "Anemia", ["None", "Mild", "Mod", "Severe"], 
                                "Fraction of Admissions", 
                                "Peak to Trough", [totalNumNoAnemiaPeakToTrough, totalNumMildAnemiaPeakToTrough, totalNumModAnemiaPeakToTrough, totalNumSevereAnemiaPeakToTrough], 
                                "First to Last", [totalNumNoAnemiaFirstToLast, totalNumMildAnemiaFirstToLast, totalNumModAnemiaFirstToLast, totalNumSevereAnemiaFirstToLast], 
                                False, g_ReportDir + "AnemiaPeaktoTroughvsFirsttoLast.jpg")

    DataShow.DrawBarGraph("Definitions of Anemia by Absolute Hemoglobin", 
                        "Anemia Definition", ["WHO", "Salisbury"],
                        "Fraction of Admissions", 
                        [totalNumAnemiaOnAdmitWHO, totalNumAnemiaSalisbury],
                        False, g_ReportDir + "DefinitionsAnemiaByAbsoluteHemoglobin.jpg")

    DataShow.DrawLineGraph("Transfusion By Hospital Day",
                            "Hospital Day Num", dayNumList, 
                            "Num Transfusions", HospDayOfTransfusionHistogram[1:], 
                            False, 
                            reportFilePathname + "transfusionsVsHospitalDay.jpg")

    DataShow.DrawLineGraph("Transfusion Vs Number Preceeding Labs",
                            "Number preceeding Labs", dayNumList, 
                            "Num Transfusions", LabsBeforeTransfusionHistogram[1:], 
                            False, 
                            reportFilePathname + "transfusionsVsNumLabs.jpg")


    fantasyList = []
    percentNameList = []
    for index in range(numPercentagePoints):
        fantasyList.append(str(index * 0.01))
        percentNameList.append(str(" "))
    DataShow.DrawLineGraph("FANTASY Transfusion times as Fraction of Length of Stay",
                            "Day of Transfusion / Length of Stay", percentNameList, 
                            "Num Transfusions", fantasyList, 
                            False, 
                            reportFilePathname + "fantasyTransfusionsAsPercentOfLabsDrawn.jpg")

    DataShow.DrawLineGraph("Frequency of Lengths of Stay",
                            "Hospital Day Num", dayNumList, 
                            "Num Patients", numDaysInpatientPerAdmissionHistogram[1:], 
                            False, 
                            reportFilePathname + "lengthOfStayFrequencies.jpg")

    DataShow.DrawLineGraph("Frequency of Total Lab Draws",
                            "Hospital Day Num", dayNumList, 
                            "Num Labs", numLabsDrawnPerAdmissionHistogram[1:], 
                            False, 
                            reportFilePathname + "labsPerAdmissionFrequencies.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Anemia", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numAdmissionsWithNoAnemia / numAdmissions), 2), 
                            round((numAdmissionsWithMildAnemia / numAdmissions), 2), 
                            round((numAdmissionsWithModAnemia / numAdmissions), 2), 
                            round((numAdmissionsWithSevereAnemia / numAdmissions), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithAnemia.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Anemia and Average Hgb Drop", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((totalHgbDropWithNoAnemia / numAdmissionsWithNoAnemia), 2), 
                            round((totalHgbDropWithMildAnemia / numAdmissionsWithMildAnemia), 2), 
                            round((totalHgbDropWithModAnemia / numAdmissionsWithModAnemia), 2), 
                            round((totalHgbDropWithSevereAnemia / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "AvgHgbDropWithAnemia.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Platelets Below 50", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithPltsBelow50 / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaWithPltsBelow50 / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaWithPltsBelow50 / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaWithPltsBelow50 / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithPlateletsBelow50.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Platelets Below 100", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithPltsBelow100 / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaWithPltsBelow100 / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaWithPltsBelow100 / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaWithPltsBelow100 / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithPlateletsBelow100.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Peak WBC over 12", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithWBCOver12 / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaWithWBCOver12 / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaWithWBCOver12 / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaWithWBCOver12 / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithWBCOver12.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Peak WBC Over 15", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithWBCOver15 / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaWithWBCOver15 / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaWithWBCOver15 / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaWithWBCOver15 / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithWBCOver15.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions On IV Antibiotics", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaOnIVAntibiotics / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaOnIVAntibiotics / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaOnIVAntibiotics / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaOnIVAntibiotics / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithIVAntibiotics.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with GI Procesures", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithGIProcedures / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaWithGIProcedures / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaWithGIProcedures / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaWithGIProcedures / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithGIProcedures.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Major Surgeries", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithSurgery / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaWithSurgery / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaWithSurgery / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaWithSurgery / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithMajorSurgery.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Likely DIC", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithLikelyDIC / numAdmissionsWithNoAnemia), 4), 
                            round((numMildAnemiaWithLikelyDIC / numAdmissionsWithMildAnemia), 4), 
                            round((numModAnemiaWithLikelyDIC / numAdmissionsWithModAnemia), 4), 
                            round((numSevereAnemiaWithLikelyDIC / numAdmissionsWithSevereAnemia), 4)], 
                        False, g_ReportDir + "FractionAdmissionsWithLikelyDIC.jpg")

    DataShow.DrawBarGraph("Fraction of Admissions with Possible DIC", 
                        "Anemia", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions", 
                        [round((numNoAnemiaWithPossibleDIC / numAdmissionsWithNoAnemia), 2), 
                            round((numMildAnemiaWithPossibleDIC / numAdmissionsWithMildAnemia), 2), 
                            round((numModAnemiaWithPossibleDIC / numAdmissionsWithModAnemia), 2), 
                            round((numSevereAnemiaWithPossibleDIC / numAdmissionsWithSevereAnemia), 2)], 
                        False, g_ReportDir + "FractionAdmissionsWithPossibleDIC.jpg")


    ########################################
    # Print Elixhauser Stats
    print("\n\nElixhauser")
    print("==========================================")
    Elixhauser.PrintStatsForGroups(
        "Comorbidities of Anemia",
        [allPatientsComorbidityGroup, noAnemiaComorbidityGroup, mildAnemiaComorbidityGroup, modAnemiaComorbidityGroup, severeAnemiaComorbidityGroup],
        ["All Patients", "No Anemia", "Mild Anemia", "Moderate Anemia", "Severe Anemia"],
        g_ReportDir + "Comorbidities.csv")

    fractionNoAnemiaPtsWithDiagnosis = noAnemiaComorbidityGroup.GetFractionPatientsWithComorbidity("Anemia")
    fractionMildAnemiaPtsWithCorrectDiagnosis = mildAnemiaComorbidityGroup.GetFractionPatientsWithComorbidity("Anemia")
    fractionModAnemiaPtsWithCorrectDiagnosis = modAnemiaComorbidityGroup.GetFractionPatientsWithComorbidity("Anemia")
    fractionSevereAnemiaPtsWithCorrectDiagnosis = severeAnemiaComorbidityGroup.GetFractionPatientsWithComorbidity("Anemia")
    print("\n\n")
    print("fraction No-Anemia Pts With InCorrect Anemia Diagnosis = " + str(fractionNoAnemiaPtsWithDiagnosis))
    print("fraction Mild Anemia Pts With Anemia Diagnosis = " + str(fractionMildAnemiaPtsWithCorrectDiagnosis))
    print("fraction Mod Anemia Pts With Anemia Diagnosis = " + str(fractionModAnemiaPtsWithCorrectDiagnosis))
    print("fraction Severe Anemia Pts With Anemia Diagnosis = " + str(fractionSevereAnemiaPtsWithCorrectDiagnosis))

    DataShow.DrawBarGraph("Fraction of Patients with Anemia that have Elixhauser Anemia Diagnoses", 
                        "Anemia", ["Mild", "Moderate", "Severe"],
                        "Percent of Admissions", 
                        [fractionMildAnemiaPtsWithCorrectDiagnosis + 100.0, 
                            fractionModAnemiaPtsWithCorrectDiagnosis + 100.0, fractionSevereAnemiaPtsWithCorrectDiagnosis + 100.0],
                        False, g_ReportDir + "FractionAdmissionsWithElixhauserDiagnoses.jpg")
# End - ShowEventsDuringAnemia







################################################################################
#
#
#
################################################################################
def ShowTransfusionsInGroups(srcTDFFilePath):
    numRiseBuckets = 20
    deltaPerRiseBucket = 0.1
    distributionOfRiseAfterTransfuse = [0] * numRiseBuckets
    distributionOfRiseAfterTransfuseMale = [0] * numRiseBuckets
    distributionOfRiseAfterTransfuseFemale = [0] * numRiseBuckets
    numDropBuckets = 20
    distributionOfDropsCausingTransfuse = [0] * numDropBuckets
    deltaPerDropBucket = 0.3

    numPatients = 0
    totalNumAdmissions = 0
    totalNumHgbs = 0
    totalNumTransfusions = 0
    totalNumAdmissionsWithTransfusions = 0
    totalNumPatientsWithTransfusions = 0

    totalRiseAfterTransfusion = 0
    numRisesAfterTransfusion = 0

    totalDropTriggeringTransfusion = 0
    numDropsTriggeringTransfusion = 0

    totalHgbDrops = 0
    numHgbDrops = 0
    distributionOfDropsPerAdmission = [0] * numDropBuckets

    totalPeakToTroughHgbDrops = 0
    numPeakToTroughHgbDrops = 0
    distributionOfPeakToTroughDrops = [0] * numDropBuckets

    admitHgbBelow8 = 0
    admitHgbBelow9 = 0
    admitHgbBelow10 = 0
    admitHgbBelow11 = 0
    admitHgbBelow12 = 0
    admitHgbBelow13 = 0

    numHgbBuckets = 20
    deltaHgbBucket = 0.5
    firstHgbBucket = 5.0
    distributionOfHgbOnAdmission = [0] * numHgbBuckets
    distributionOfHgbForTransfusion = [0] * numHgbBuckets

    numAdmissionsWithNoAnemiaOnAdmit = 0
    numAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge = 0
    numAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge = 0
    numAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge = 0
    numAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge = 0
    numAdmissionsWithAnemiaOnAdmit = 0
    numAdmissionsWithAnemiaOnAdmitAndNoDrop = 0
    numAdmissionsWithAnemiaOnAdmitAndMildDrop = 0
    numAdmissionsWithAnemiaOnAdmitAndModerateDrop = 0
    numAdmissionsWithAnemiaOnAdmitAndSevereDrop = 0

    srcTDF = tdf.TDF_CreateTDFFileReader(srcTDFFilePath, 
                                        "Hgb;WBC;Cr;Plt;Procal;CRP;DDimer;Fibrinogen;LDH;Haptoglobin;VancDose;PipTazoDose;CefepimeDose;DaptoDose;MeroDose;MajorSurgeries;GIProcedures;Tbili;HospitalAdmitDate;InHospital;TransRBC;MajorSurgeries;GIProcedures",
                                        "Hgb", [])
    srcTDF.SetTimeResolution(1)
    srcTDF.SetCarryForwardPreviousDataValues(False)


    # Iterate over every patient
    fFoundPatient = srcTDF.GotoFirstPatient()
    while (fFoundPatient):
        numPatients += 1
        fGotTransfusion = False

        # Get a list of all admissions.
        admissionList = srcTDF.GetAdmissionsForCurrentPatient()
        srcTDF.ExpandAdmissionListWithHgbDropAndTransfusions(admissionList)

        for admissionInfo in admissionList:
            totalNumAdmissions += 1

            totalNumHgbs += admissionInfo['NumHgbs']
            totalNumTransfusions += admissionInfo['NumTransfusions']
            if (admissionInfo['NumTransfusions'] > 0):
                totalNumAdmissionsWithTransfusions += 1
                fGotTransfusion = True

            totalRiseAfterTransfusion += admissionInfo['totalRiseAfterTransfusion']
            numRisesAfterTransfusion += admissionInfo['numRisesAfterTransfusion']

            if (admissionInfo['firstHgbValue'] > 0):
                bucketNum = round(((admissionInfo['firstHgbValue'] - firstHgbBucket) / deltaHgbBucket))
                if (bucketNum >= numHgbBuckets):
                    bucketNum = numHgbBuckets - 1
                if (bucketNum < 0):
                    bucketNum = 0
                distributionOfHgbOnAdmission[bucketNum] += 1
            # End - if (admissionInfo['firstHgbValue'] > 0)


            for hgbRise in admissionInfo['HgbRiseAfterTransfusionList']:
                # Add it to the distribution of rises
                bucketNum = round((hgbRise / deltaPerRiseBucket))
                if (bucketNum >= numRiseBuckets):
                    bucketNum = numRiseBuckets - 1
                if (bucketNum < 0):
                    bucketNum = 0
                distributionOfRiseAfterTransfuse[bucketNum] += 1
            # End - for hgbRise in admissionInfo['HgbRiseAfterTransfusionList']:

            totalDropTriggeringTransfusion += admissionInfo['totalDropTriggeringTransfusion']
            numDropsTriggeringTransfusion += admissionInfo['numDropsLeadingToTransfusion']
            for drop in admissionInfo['DropsPromptingTransfusionList']:
                # Add it to the distribution of drops
                bucketNum = round((drop / deltaPerDropBucket))
                if (bucketNum < 0):
                    bucketNum = 0
                if (bucketNum >= numDropBuckets):
                    bucketNum = numDropBuckets - 1
                distributionOfDropsCausingTransfuse[bucketNum] += 1
                if (admissionInfo['gender'] == 1):
                    distributionOfRiseAfterTransfuseMale[bucketNum] += 1
                else:
                    distributionOfRiseAfterTransfuseFemale[bucketNum] += 1
            # End - for drop in admissionInfo['DropsPromptingTransfusionList']:

            for lastHgbBeforeTransfusion in admissionInfo['HgbPromptingTransfusionList']:
                # Add it to the distribution of Hgb before transfusion
                bucketNum = round(lastHgbBeforeTransfusion / deltaHgbBucket)
                if (bucketNum >= numHgbBuckets):
                    bucketNum = numHgbBuckets - 1
                if (bucketNum < 0):
                    bucketNum = 0
                distributionOfHgbForTransfusion[bucketNum] += 1
            # End - for drop in admissionInfo['HgbPromptingTransfusionList']:

            if (admissionInfo['firstHgbValue'] > 0):
                startHgb = admissionInfo['firstHgbValue']
                if (startHgb < 8.0):
                    admitHgbBelow8 += 1
                elif (startHgb < 9.0):
                    admitHgbBelow9 += 1
                elif (startHgb < 10.0):
                    admitHgbBelow10 += 1
                elif (startHgb < 11.0):
                    admitHgbBelow11 += 1
                elif (startHgb < 12.0):
                    admitHgbBelow12 += 1
                elif (startHgb < 13.0):
                    admitHgbBelow13 += 1
            # End - if (admissionInfo['firstHgbValue'] != tdf.TDF_INVALID_VALUE):


            if ((admissionInfo['firstHgbValue'] > 0) and (admissionInfo['lastHgbValue'] > 0)):
                # Count the drops
                fAnemiaOnAdmission = False
                if ((admissionInfo["gender"] >= 1) and (admissionInfo["ageInYrs"] <= 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN_60_AND_UNDER)):
                    fAnemiaOnAdmission = True
                elif ((admissionInfo["gender"] >= 1) and (admissionInfo["ageInYrs"] > 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_MEN_OVER_60)):
                    fAnemiaOnAdmission = True
                elif ((admissionInfo["gender"] <= 0) and (admissionInfo["ageInYrs"] <= 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN_60_AND_UNDER)):
                    fAnemiaOnAdmission = True
                elif ((admissionInfo["gender"] <= 0) and (admissionInfo["ageInYrs"] > 60) and (admissionInfo['smallestHgbValue'] < ABSOLUTE_HGB_FOR_ANEMIA_IN_WOMEN_OVER_60)):
                    fAnemiaOnAdmission = True

                dropInHgb = (admissionInfo['largestHgbValue'] - admissionInfo['smallestHgbValue'])  + (HGB_RISE_PER_TRANSFUSION * admissionInfo['NumTransfusions'])
                dropInHgbAdmitToDischarge = (admissionInfo['lastHgbValue'] - admissionInfo['firstHgbValue'])  + (HGB_RISE_PER_TRANSFUSION * admissionInfo['NumTransfusions'])

                if (not fAnemiaOnAdmission):
                    numAdmissionsWithNoAnemiaOnAdmit += 1
                    # No anemia
                    if (dropInHgb < MIN_HGB_DROP_FOR_MILD_ANEMIA):
                        numAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge += 1
                    # Mild anemia
                    elif (dropInHgb < MIN_HGB_DROP_FOR_MODERATE_ANEMIA):
                        numAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge += 1
                    # Moderate Anemia
                    elif (dropInHgb < MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                        numAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge += 1
                    # Severe Anemia
                    else:
                        numAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge += 1

                if (fAnemiaOnAdmission):
                    numAdmissionsWithAnemiaOnAdmit += 1
                    # No anemia
                    if (dropInHgb < MIN_HGB_DROP_FOR_MILD_ANEMIA):
                        numAdmissionsWithAnemiaOnAdmitAndNoDrop += 1
                    # Mild anemia
                    elif (dropInHgb < MIN_HGB_DROP_FOR_MODERATE_ANEMIA):
                        numAdmissionsWithAnemiaOnAdmitAndMildDrop += 1
                    # Moderate Anemia
                    elif (dropInHgb < MIN_HGB_DROP_FOR_SEVERE_ANEMIA):
                        numAdmissionsWithAnemiaOnAdmitAndModerateDrop += 1
                    # Severe Anemia
                    else:
                        numAdmissionsWithAnemiaOnAdmitAndSevereDrop += 1
                # End - if (admissionInfo['firstHgbValue'] < 13.0):



                totalPeakToTroughHgbDrops += dropInHgb
                numPeakToTroughHgbDrops += 1
                index = round((dropInHgb / deltaPerDropBucket))
                if (index < 0):
                    index = 0
                if (index >= numDropBuckets):
                    index = numDropBuckets - 1
                distributionOfPeakToTroughDrops[index] += 1


                totalHgbDrops += dropInHgbAdmitToDischarge
                numHgbDrops += 1
                index = round((dropInHgbAdmitToDischarge / deltaPerDropBucket))
                if (index < 0):
                    index = 0
                if (index >= numDropBuckets):
                    index = numDropBuckets - 1
                distributionOfDropsPerAdmission[index] += 1
            # End - if (admissionInfo['firstHgbValue'] != tdf.TDF_INVALID_VALUE):

            if (fGotTransfusion):
                totalNumPatientsWithTransfusions += 1
        # End - for admissionInfo in admissionList:

        fFoundPatient = srcTDF.GotoNextPatient()
    # End - while (patientNode):


    srcTDF.Shutdown() 

    print("\n\n\n")
    print("numPatients = " + str(numPatients))
    print("totalNumAdmissions = " + str(totalNumAdmissions))
    print("TotalNumHgbs = " + str(totalNumHgbs))
    print("Avg Num Hgbs Per Admission = " + str(round(totalNumHgbs / totalNumAdmissions)))

    print("totalNumTransfusions = " + str(totalNumTransfusions))
    print("Avg Num Transfusions Per Admission = " + str(round(totalNumTransfusions / totalNumAdmissions)))
    print("Avg Num Transfusions Per Patient = " + str(round(totalNumTransfusions / numPatients)))
    print("Fraction of Admissions With a Transfusion = " + str(round(totalNumAdmissionsWithTransfusions / totalNumAdmissions)))
    print("Fraction of Patients Who Received a Transfusion = " + str(round(totalNumPatientsWithTransfusions / numPatients)))

    print("\n\n")
    fractionAdmitHgbBelow8 = round((admitHgbBelow8 / totalNumAdmissions), 2)
    fractionAdmitHgbBelow9 = round((admitHgbBelow9 / totalNumAdmissions), 2)
    fractionAdmitHgbBelow10 = round((admitHgbBelow10 / totalNumAdmissions), 2)
    fractionAdmitHgbBelow11 = round((admitHgbBelow11 / totalNumAdmissions), 2)
    fractionAdmitHgbBelow12 = round((admitHgbBelow12 / totalNumAdmissions), 2)
    fractionAdmitHgbBelow13 = round((admitHgbBelow13 / totalNumAdmissions), 2)
    print("admitHgbBelow8 = " + str(admitHgbBelow8) + ", percentOfAdmissions = " + str(fractionAdmitHgbBelow8))
    print("admitHgbBelow9 = " + str(admitHgbBelow9) + ", percentOfAdmissions = " + str(fractionAdmitHgbBelow9))
    print("admitHgbBelow10 = " + str(admitHgbBelow10) + ", percentOfAdmissions = " + str(fractionAdmitHgbBelow10))
    print("admitHgbBelow11 = " + str(admitHgbBelow11) + ", percentOfAdmissions = " + str(fractionAdmitHgbBelow11))
    print("admitHgbBelow12 = " + str(admitHgbBelow12) + ", percentOfAdmissions = " + str(fractionAdmitHgbBelow12))
    print("admitHgbBelow13 = " + str(admitHgbBelow13) + ", percentOfAdmissions = " + str(fractionAdmitHgbBelow13))

    DataShow.DrawBarGraph("Patients with Anemia on Admission", 
                        "Admitting Hemoglobin", ["<8", "<9", "<10", "<11", "<12", "<13"],
                        "Fraction of Admissions", 
                        [fractionAdmitHgbBelow8, fractionAdmitHgbBelow9, fractionAdmitHgbBelow10, fractionAdmitHgbBelow11, 
                            fractionAdmitHgbBelow12, fractionAdmitHgbBelow13], 
                        False, g_ReportDir + "FractionPtsWithAnemiaOnAdmission.jpg")



    xValFloatList = np.arange(firstHgbBucket, (firstHgbBucket + (numHgbBuckets * deltaHgbBucket)), deltaHgbBucket)
    xValStrList = []
    for x in xValFloatList:
        valStr = ""
        if (len(xValStrList) % 2 > 0):
            valStr += "\n"
        valStr += str(round(x, 2))
        xValStrList.append(valStr)
    DataShow.DrawBarGraph("Hemoglobin on Admission", 
                        "Admitting Hemoglobin", xValStrList,
                        "Number of Admissions", distributionOfHgbOnAdmission, 
                        False, g_ReportDir + "HgbOnAdmissionHistogram.jpg")


    print("\n\n")
    print("numRisesAfterTransfusion = " + str(numRisesAfterTransfusion))
    print("totalRiseAfterTransfusion = " + str(totalRiseAfterTransfusion))
    if (numRisesAfterTransfusion > 0):
        print("Avg Rise in Hgb After Transfusion = " + str(round((totalRiseAfterTransfusion / numRisesAfterTransfusion), 3)))

    xValFloatList = np.arange(0, (numRiseBuckets * deltaPerRiseBucket), deltaPerRiseBucket)
    xValStrList = [str(round(x, 2)) for x in xValFloatList]
    DataShow.DrawBarGraph("Rise in Hemoblobin After a Transfusion", 
                        "Rise in Hemoblobin", xValStrList,
                        "Number of Occurrences", 
                        distributionOfRiseAfterTransfuse, 
                        False, g_ReportDir + "RiseInHgbAfterTransfusion.jpg")

    print("Avg Admit-Discharge Hgb Drop = " + str(round((totalHgbDrops / numHgbDrops), 3)))
    xValFloatList = np.arange(0, (numDropBuckets * deltaPerDropBucket), deltaPerDropBucket)
    xValStrList = []
    for x in xValFloatList:
        valStr = ""
        if (len(xValStrList) % 2 > 0):
            valStr += "\n"
        valStr += str(round(x, 2))
        xValStrList.append(valStr)
    DataShow.DrawBarGraph("Drop in Hemoblobin (Admit to Discharge)", 
                        "Drop in Hemoblobin", xValStrList,
                        "Number of Occurrences", 
                        distributionOfDropsPerAdmission, 
                        False, g_ReportDir + "HgbDropAdmitToDischarge.jpg")

    print("Avg Peak to Trough Hgb Drop = " + str(round((totalPeakToTroughHgbDrops / numPeakToTroughHgbDrops), 3)))
    xValFloatList = np.arange(0, (numDropBuckets * deltaPerDropBucket), deltaPerDropBucket)
    xValStrList = []
    for x in xValFloatList:
        valStr = ""
        if (len(xValStrList) % 2 > 0):
            valStr += "\n"
        valStr += str(round(x, 2))
        xValStrList.append(valStr)
    DataShow.DrawBarGraph("Drop in Hemoblobin (Peak to Trough)", 
                        "Drop in Hemoblobin", xValStrList,
                        "Number of Occurrences", 
                        distributionOfPeakToTroughDrops, 
                        False, g_ReportDir + "HgbDropPeakToTrough.jpg")


    print("totalDropTriggeringTransfusion = " + str(totalDropTriggeringTransfusion))
    print("numDropsTriggeringTransfusion = " + str(numDropsTriggeringTransfusion))
    print("Avg Hgb Drop Before Transfusion = " + str(round((totalDropTriggeringTransfusion / numDropsTriggeringTransfusion), 3)))
    xValFloatList = np.arange(0, (numDropBuckets * deltaPerDropBucket), deltaPerDropBucket)
    xValStrList = []
    for x in xValFloatList:
        valStr = ""
        if (len(xValStrList) % 2 > 0):
            valStr += "\n"
        valStr += str(round(x, 2))
        xValStrList.append(valStr)
    DataShow.DrawBarGraph("Drop in Hemoblobin Prompting a Transfusion", 
                        "Drop in Hemoblobin", xValStrList,
                        "Number of Occurrences", 
                        distributionOfDropsCausingTransfuse, 
                        False, g_ReportDir + "DropInHgbPromptingTransfusion.jpg")

    xValFloatList = np.arange(0, (numHgbBuckets * deltaHgbBucket), deltaHgbBucket)
    xValStrList = []
    for x in xValFloatList:
        valStr = ""
        if (len(xValStrList) % 2 > 0):
            valStr += "\n"
        valStr += str(round(x, 2))
        xValStrList.append(valStr)
    DataShow.DrawBarGraph("Hemoblobin Prompting a Transfusion", 
                        "Hemoblobin", xValStrList,
                        "Number of Occurrences", 
                        distributionOfHgbForTransfusion, 
                        False, g_ReportDir + "HgbBeforeTransfusion.jpg")


    print("\n\n")
    fractionAdmissionsWithNoAnemiaOnAdmit = round((numAdmissionsWithNoAnemiaOnAdmit / totalNumAdmissions), 2)
    fractionAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge = round((numAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge / numAdmissionsWithNoAnemiaOnAdmit), 2)
    fractionAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge = round((numAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge / numAdmissionsWithNoAnemiaOnAdmit), 2)
    fractionAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge = round((numAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge / numAdmissionsWithNoAnemiaOnAdmit), 2)
    fractionAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge = round((numAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge / numAdmissionsWithNoAnemiaOnAdmit), 2)

    fractionAdmissionsWithAnemiaOnAdmit = round((numAdmissionsWithAnemiaOnAdmit / totalNumAdmissions), 2)
    fractionAdmissionsWithAnemiaOnAdmitAndNoDrop = round((numAdmissionsWithAnemiaOnAdmitAndNoDrop / numAdmissionsWithAnemiaOnAdmit), 2)
    fractionAdmissionsWithAnemiaOnAdmitAndMildDrop = round((numAdmissionsWithAnemiaOnAdmitAndMildDrop / numAdmissionsWithAnemiaOnAdmit), 2)
    fractionAdmissionsWithAnemiaOnAdmitAndModerateDrop = round((numAdmissionsWithAnemiaOnAdmitAndModerateDrop / numAdmissionsWithAnemiaOnAdmit), 2)
    fractionAdmissionsWithAnemiaOnAdmitAndSevereDrop = round((numAdmissionsWithAnemiaOnAdmitAndSevereDrop / numAdmissionsWithAnemiaOnAdmit), 2)


    print("\n\nAdmissions With No Anemia On Admit")
    print(str(fractionAdmissionsWithNoAnemiaOnAdmit) + "% Admissions With No Anemia On Admit (" + str(numAdmissionsWithNoAnemiaOnAdmit) + "/" + str(totalNumAdmissions) + ")")
    print(str(fractionAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge) + "% with No Anemia (" + str(numAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge) + "/" + str(numAdmissionsWithNoAnemiaOnAdmit) + ")")
    print(str(fractionAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge) + "% with Mild Anemia (" + str(numAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge) + "/" + str(numAdmissionsWithNoAnemiaOnAdmit) + ")")
    print(str(fractionAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge) + "% with Moderate Anemia (" + str(numAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge) + "/" + str(numAdmissionsWithNoAnemiaOnAdmit) + ")")
    print(str(fractionAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge) + "% with Severe Anemia (" + str(numAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge) + "/" + str(numAdmissionsWithNoAnemiaOnAdmit) + ")")

    print("\n\nAdmissions With Anemia On Admit")
    print(str(fractionAdmissionsWithAnemiaOnAdmit) + "% Admissions With Anemia On Admit (" + str(numAdmissionsWithAnemiaOnAdmit) + "/" + str(totalNumAdmissions) + ")")
    print(str(fractionAdmissionsWithAnemiaOnAdmitAndNoDrop) + "% with No Hgb Drop (" + str(numAdmissionsWithAnemiaOnAdmitAndNoDrop) + "/" + str(numAdmissionsWithAnemiaOnAdmit) + ")")
    print(str(fractionAdmissionsWithAnemiaOnAdmitAndMildDrop) + "% with Mild Hgb Drop (" + str(numAdmissionsWithAnemiaOnAdmitAndMildDrop) + "/" + str(numAdmissionsWithAnemiaOnAdmit) + ")")
    print(str(fractionAdmissionsWithAnemiaOnAdmitAndModerateDrop) + "% with Moderate Hgb Drop (" + str(numAdmissionsWithAnemiaOnAdmitAndModerateDrop) + "/" + str(numAdmissionsWithAnemiaOnAdmit) + ")")
    print(str(fractionAdmissionsWithAnemiaOnAdmitAndSevereDrop) + "% with Severe Hgb Drop (" + str(numAdmissionsWithAnemiaOnAdmitAndSevereDrop) + "/" + str(numAdmissionsWithAnemiaOnAdmit) + ")")

    
    DataShow.DrawBarGraph("Drop in Hemoblobin With No Anemia On Admission", 
                        "Drop in Hemoblobin", ["None", "Mild", "Moderate", "Severe"],
                        "Fraction of Admissions with Normal Hgb on Admit", 
                        [fractionAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge, fractionAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge, 
                            fractionAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge, fractionAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge], 
                        False, g_ReportDir + "HgbDropWithNormalHgbOnAdmit.jpg")

    DataShow.DrawBarGraph("Drop in Hemoblobin With Anemia On Admission", 
                          "Drop in Hemoblobin", ["None", "Mild", "Moderate", "Severe"],
                          "Fraction of Admissions with Anemia on Admit", 
                          [fractionAdmissionsWithAnemiaOnAdmitAndNoDrop, fractionAdmissionsWithAnemiaOnAdmitAndMildDrop, 
                                fractionAdmissionsWithAnemiaOnAdmitAndModerateDrop, fractionAdmissionsWithAnemiaOnAdmitAndSevereDrop], 
                          False, g_ReportDir + "HgbDropWithAnemiaOnAdmit.jpg")




    DataShow.DrawDoubleBarGraph("Drop in Hemoblobin With and Without Anemia On Admission", 
                                "Drop in Hemoblobin", ["None", "Mild", "Moderate", "Severe"],
                                "Fraction of Hospitalizations", 
                                "Anemia on Admit", 
                                [fractionAdmissionsWithAnemiaOnAdmitAndNoDrop, fractionAdmissionsWithAnemiaOnAdmitAndMildDrop, 
                                    fractionAdmissionsWithAnemiaOnAdmitAndModerateDrop, fractionAdmissionsWithAnemiaOnAdmitAndSevereDrop],
                                "Normal Hgb on Admit", 
                                [fractionAdmissionsWithNoAnemiaOnAdmitAndNoneDischarge, fractionAdmissionsWithNoAnemiaOnAdmitAndMildOnDischarge, 
                                    fractionAdmissionsWithNoAnemiaOnAdmitAndModerateOnDischarge, fractionAdmissionsWithNoAnemiaOnAdmitAndSevereOnDischarge],
                                False, g_ReportDir + "HgbDropWithAndWithoutAnemiaOnAdmit.jpg")

# End - ShowTransfusionsInGroups







################################################################################
#
# MAIN
#
################################################################################
now = datetime.datetime.now()
startimeStr = now.strftime("%Y-%m-%d %H:%M:%S")
print("Start Time=" + startimeStr)


g_ProjectRootDir = "/home/ddean/ddRoot/BloodLossFromDailyLabs/"
g_ReportDir = g_ProjectRootDir + "Reports/"
g_srcTDFFilePath = "/home/ddean/dLargeData/mlData/UKData/UKHC_4942/UKDailyLabsBloodLossMissedAKI.tdf"

Elixhauser.Elixhauser_LoadLibrary("/home/ddean/dLargeData/mlData/elixhauser/CMR-Reference-File-v2022-1CSV.csv")


##############################
# Anemia and Iron Markers
if (False):
    ShowCorrelationOfAnemiaAndIronMarkers(g_srcTDFFilePath)


##############################
# Reproducibility of Hgb and Cr
if (True):
    print("\n========================\nHgb Reproducibility")
    maxMinutes = 15
    numHistogramBuckets = 31
    rangePerHistogramBucket = 0.1
    tdfShow.ShowValueReproducibility(g_srcTDFFilePath, 
                    'Hgb',
                    maxMinutes,
                    numHistogramBuckets,
                    rangePerHistogramBucket,
                    g_ReportDir + "HgbReproducibility.jpg")
    print("\n========================\nCr Reproducibility")
    rangePerHistogramBucket = 0.05
    tdfShow.ShowValueReproducibility(g_srcTDFFilePath, 
                    'Cr',
                    maxMinutes,
                    numHistogramBuckets,
                    rangePerHistogramBucket,
                    g_ReportDir + "CrReproducibility.jpg")


##############################
# Value Drop Statistics
if (False):
    print("\n========================\nHgb Drop")
    ShowEventsDuringAnemia(g_srcTDFFilePath, g_ReportDir)


##############################
# Value Dynamics
if (False):
    numHistogramBuckets = 14
    print("\n========================\nHgb StdDev vs Days Since Admission")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Hgb', #xValueName
                    "StdDev", # Y axis
                    "DaysSinceAdmit", # xAxis
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    True, # fResetOnTransfusions
                    "StdDev in Hgb vs Days Since Admission",
                    "Standard Deviation",
                    "Days Since Admission",
                    g_ReportDir + "HgbStdDevVsDaysSinceAdmit.jpg")
    print("\n========================\nHgb StdDev vs Skipped Labs")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Hgb', #xValueName
                    "StdDev", # Y axis
                    "SkippedDays", # xAxis
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    True, # fResetOnTransfusions
                    "StdDev in Hgb vs Num Skipped Labs",
                    "Standard Deviation",
                    "Number of Days with Skipped Labs",
                    g_ReportDir + "HgbStdDevVsSkippedDays.jpg")
    print("\n========================\nHgb Variability")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Hgb', #xValueName
                    "Delta", # Y axis
                    "SkippedDays", # xAxis
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    True, # fResetOnTransfusions
                    "Average Change in Hgb vs Num Skipped Labs",
                    "Change From Previous Lab",
                    "Number of Days with Skipped Labs",
                    g_ReportDir + "HgbDeltaVsSkippedDays.jpg")
    print("\n========================\nHgb Variability vs #Labs")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Hgb', #xValueName
                    "Delta", # Y axis
                    "DaysSinceAdmit", # xAxis
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    True, # fResetOnTransfusions
                    "Average Change in Hgb vs Days Since Admission",
                    "Change From Previous Lab",
                    "Days Since Admission",
                    g_ReportDir + "HgbDeltaVsDaysSinceAdmit.jpg")
    print("\n========================\n Cr StdDev vs #LabsDays since admit")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Cr', #xValueName
                    "StdDev", # Y-axis
                    "DaysSinceAdmit",
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    False, # fResetOnTransfusions
                    "Average Creatinine Standard Deviation vs Days since Admission",
                    "Standard Deviation",
                    "Days Since Admission",
                    g_ReportDir + "CrStdDevVsDaysSinceAdmit.jpg")
    print("\n========================\n Cr StdDev vs Num Labs Skipped")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Cr', #xValueName
                    "StdDev", # Y-axis
                    "SkippedDays",
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    False, # fResetOnTransfusions
                    "Average Creatinine Standard Deviation vs Num Skipped Labs",
                    "Standard Deviation",
                    "Number of Days with Skipped Labs",
                    g_ReportDir + "CrStdDevVsSkippedDays.jpg")
    print("\n========================\n Cr Change vs #Days")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Cr', #xValueName
                    "Delta", # Y axis
                    "DaysSinceAdmit", # xAxis
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    False, # fResetOnTransfusions
                    "Average Change in Creatinine vs Days since Admission",
                    "Change From Previous Lab",
                    "Days Since Admission",
                    g_ReportDir + "CrDeltaVsDaysSinceAdmit.jpg")
    print("\n========================\n Cr Change vs Skipped Days")
    tdfShow.ShowValueDynamics(g_srcTDFFilePath, 
                    'Cr', #xValueName
                    "Delta", # Y axis
                    "SkippedDays",
                    0.0, # Threshold
                    numHistogramBuckets,
                    True, # fResetOnAdmissions
                    False, # fResetOnTransfusions
                    "Average Change in Creatinine vs Num Skipped Days",
                    "Change From Previous Lab",
                    "Number of Skipped Labs",
                    g_ReportDir + "CrDeltaVsSkippedDays.jpg")



##############################
# Before and After Transfusion
if (False):
    print("\n========================\n Blood Loss Before and After Change")
    ShowTransfusionsInGroups(g_srcTDFFilePath)



now = datetime.datetime.now()
stopTimeStr = now.strftime("%Y-%m-%d %H:%M:%S")
print("\n\nDone")
print("Stop Time=" + stopTimeStr)






