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
# Graphing Utilities
#
################################################################################
import os
import sys
import math

import statistics
from scipy import stats
from scipy.stats import spearmanr
import numpy as np

import tdfTools as tdf
import dataShow as DataShow
import tdfTimeFunctions as timefunc
from tdfMedicineValues import g_LabValueInfo

NEWLINE_STR = "\n"

MIN_SEQUENCE_LENGTH_FOR_COVARIANCE     = 4

TESTING_TDF = True


################################################################################
# A public procedure.
################################################################################
def TDF_MakeEmptyValueHistogramForAllVariables():
    histogram = {}

    for index, (varName, labInfo) in enumerate(g_LabValueInfo.items()):
        varType = labInfo['dataType']
        minVal = labInfo['minVal']
        maxVal = labInfo['maxVal']

        if (varType == tdf.TDF_DATA_TYPE_INT):
            numClasses = 20
            range = float(maxVal - minVal)
            bucketSize = float(range) / float(numClasses)
        elif (varType == tdf.TDF_DATA_TYPE_FLOAT):
            numClasses = 20
            range = float(maxVal - minVal)
            bucketSize = float(range) / float(numClasses)
        elif (varType == tdf.TDF_DATA_TYPE_BOOL):
            numClasses = 2
            bucketSize = 1
        elif (varType == tdf.TDF_DATA_TYPE_FUTURE_EVENT_CLASS):
            numClasses = tdf.TDF_NUM_FUTURE_EVENT_CATEGORIES
            bucketSize = 1
        else:
            numClasses = 1
            bucketSize = 1

        histEntry = {'name': varName, 'dataType': varType, 
                'minValidVal': minVal, 'maxValidVal': maxVal,
                'numVals': 0, 'minVal': 0, 'maxVal': 0, 'totalVal': 0, 
                'numClasses': numClasses, 'bucketSize': bucketSize, 
                'hist': [0] * numClasses}
        histogram[varName] = histEntry
    # End - for index, (varName, labInfo) in enumerate(g_LabValueInfo.items()):

    return(histogram)
# End - TDF_MakeEmptyValueHistogramForAllVariables




#####################################################
#
# [TDFShow_ShowValueDistribution]
#
#####################################################
def TDFShow_ShowValueDistribution(filePathname, fileType, filePathName):
    return
# End - TDFShow_ShowValueDistribution



#####################################################
#
# [GetStatsForList]
#
#####################################################
def GetStatsForList(valueList):
    # Compute the mean, which is the average of the values.
    # Make sure to treat these as floats to avoid truncation or rounding errors.
    #avgValue = 0
    refAvgValue = 0
    listLen = len(valueList)
    if (listLen > 0):
        #avgValue = float(sum(valueList)) / listLen
        refAvgValue = statistics.mean(valueList)
    #print("Derived avgValue=" + str(avgValue))
    #print("Reference refAvgValue=" + str(refAvgValue))

    # Next, compute the variance.
    # This is a measure of how far spread out the numbers are.
    # Intuitively, this is the average distance from members of the set and the mean.
    # This uses the "Sample Variance" where avgValue is the sample mean, not the
    # mean of some superset "population" from which the sample is drawn.
    # As a result, we divide by listLen-1, but if we used the "population mean" then
    # we would divide by listLen
    #variance = sum((x - avgValue) ** 2 for x in valueList) / listLen
    refVariance = np.var(valueList)
    #print("Derived variance=" + str(variance))
    #print("Reference variance=" + str(refVariance))

    # Standard deviation is simply the sqrt of the Variance
    #stdDev = math.sqrt(variance)
    refStdDev = np.std(valueList)
    #print("Derived stdDev=" + str(stdDev))
    #print("Reference stdDev=" + str(refStdDev))

    return listLen, refAvgValue, refVariance, refStdDev
# End - GetStatsForList





#####################################################
#
# [CalculatePearsonCovarianceForLists]
#
#####################################################
def CalculatePearsonCovarianceForLists(valueList1, valueList2):
    length1, meanVal1, variance1, stdDev1 = GetStatsForList(valueList1)
    length2, meanVal2, variance2, stdDev2 = GetStatsForList(valueList2)

    # Compute the covariance. 
    # This is the tendency for the variables to have a linear relationship.
    # ???It is the slope of the regression line.???
    # It is computed by the average of the products of distances from each list element and the list mean.
    #
    # If a list is sorted in increasing order, then the difference between list elements and the list mean will
    # start with a negative number (the smallest value, so farthest below the mean) and end with a positive number
    # (the largest value, so farthest greater than the mean). 
    # Each value in the list will have a difference to the mean that lays somewhere in the middle 
    # between the most negative and most positive.
    # The two lists are covariant if small values in one list correspond to small values in the other list, and
    # large values in one list correspond to large values in the other list. In other words, the two corresponding
    # values will have distances with the same sign, either both positive or both negative. In either case, their
    # product is a positive value.
    # If the two lists are not covariant, then a number above average in one list will be associated with a
    # number below average in the other list. when they are very different, then their differences to the respective 
    # means will have different polarity, one is positice and one is negative. The product is a negative number.
    # The sum of all of these will be a mix of positive and negative products.
    covariance = 0
    for i in range(0, length1):
        covariance += ((valueList1[i] - meanVal1) * (valueList2[i] - meanVal2))
    # This is the sample covariance, so we should use length-1 to compute the mean.
    # However, the Python library seems to use the population variance, so uses length to compute the mean
    covariance = covariance / length1  # (length1 - 1)
    #refCovariance = np.cov(valueList1, valueList2)[0][1]
    #print("Derived covariance=" + str(covariance))
    #print("Reference covariance=" + str(refCovariance))

    # The absolute value of the covariance can be any number, from -infinity to +infinity.
    # Its absolute value does not tell you anything about how well the lists are correlated.
    # So, normalize the covariance by the variability of the data. This essentially normalizes
    # the covariance by some measure of the range of values (largest - smallest). Now, why don't
    # we normalize the the products of the two ranges like (largest - smallest of set 1) * (largest - smallest of set2)
    # Not sure.
    # Pearson assumes a Gaussian distribution of the data, because it uses the mean value of each list
    # in its calculation.
    # It has values between -1 (negative correlation) and 1 (positive correlation). 0 means no correlation.
    #pearsonCoeff = covariance / (stdDev1 * stdDev2)

    corrMatrix = np.corrcoef(valueList1, valueList2)
    refPearsonCoeff = corrMatrix[0, 1]

    ##refPearsonList = pearsonr(valueList1, valueList2)
    ##refPearsonCoeff2 = refPearsonList[0]
    ##refPValue = refPearsonList[1]

    #print("Derived pearsonCoeff=" + str(pearsonCoeff))
    #print("Reference pearsonCoeff=" + str(refPearsonCoeff))
    ##print("Reference pearsonCoeff2=" + str(refPearsonCoeff2))

    return refPearsonCoeff
# End - CalculatePearsonCovarianceForLists






#####################################################
#
# [CalculateSpearmanCovarianceForLists]
#
# Spearman correlation is just the Pearson correlation coefficient 
# between the rank variables
#####################################################
def CalculateSpearmanCovarianceForLists(valueList1, valueList2):
    listLength = len(valueList1)

    # Make a list of value indexes. 
    # These are the positions of a value in the original value-list.
    indexList1 = list(range(listLength))
    indexList2 = list(range(listLength))

    # Sort the indexes based on the actual values. 
    # This creates a list of value indexes, sorted in the order of the values themselves.
    # So, the first index references to the smallest value, and so on.
    # Because indexList is ordered, the position of an entry in indexList is also its rank.
    # So, the index stored at indexList[x] stores an index into valueList, but x (the index in indexList) is the rank.
    # This uses sort, so it takes O(N*logN) 
    indexList1.sort(key=lambda x: valueList1[x])
    indexList2.sort(key=lambda x: valueList2[x])

    # Now, arrange the ranks into the same order of the items in the original value list.
    # This means valueRanksList[N] stored the rank of the value stored at valueList1[N]
    # The index into indexList is the rank of the value stored in valueList1
    valueRanksList1 = [0] * listLength
    for indexListIndex, valueListIndex in enumerate(indexList1):
        valueRanksList1[valueListIndex] = indexListIndex

    valueRanksList2 = [0] * listLength
    for indexListIndex, valueListIndex in enumerate(indexList2):
        valueRanksList2[valueListIndex] = indexListIndex

    # scipy.stats.spearmanr will take care of computing the ranks for you, you simply have 
    # to give it the data in the correct order:
    refSpearmanCoeff, pValue = spearmanr(valueList1, valueList2)

    #print("=================")
    #print("mySpearman=" + str(mySpearman))
    #mySpearman = CalculatePearsonCovarianceForLists(valueRanksList1, valueRanksList2)
    #print("refSpearmanCoeff=" + str(refSpearmanCoeff))

    return refSpearmanCoeff
# End - CalculateSpearmanCovarianceForLists






################################################################################
#
# [LoadCovariantsFileIntoDicts]
#
################################################################################
def LoadCovariantsFileIntoDicts(covariantResultFilePathName):
    fDebug = False
    allInputVars = []
    allOutputVars = []
    allResults = {}

    # Load the file into a list in memory
    with open(covariantResultFilePathName) as fileH:
        for line in fileH:
            line = line.lstrip()
            line = line.rstrip()
            if (fDebug):
                print(">> line=" + line)

            words = line.split(":")
            varList = words[0]
            coeffStr = words[1]
            coeffFloat = float(coeffStr)
            words = varList.split("~")
            inputVar = words[0]
            outputVar = words[1]
            if (fDebug):
                print("in=" + inputVar + ", out=" + outputVar + "r=" + str(coeffFloat))
            
            # Find the list of inputs for this output variable.
            if outputVar in allResults:
                coeffDict = allResults[outputVar]
            else:
                coeffDict = {}

            coeffDict[inputVar] = coeffFloat
            allResults[outputVar] = coeffDict
            if (inputVar not in allInputVars):
                allInputVars.append(inputVar)
            if (outputVar not in allOutputVars):
                allOutputVars.append(outputVar)
        # End - for line in fileH:

        fileH.close()
    # End - with open(covariantResultFilePathName) as fileH:

    return allInputVars, allOutputVars, allResults
# End - LoadCovariantsFileIntoDicts







#####################################################
#
# [GetCovarianceBetweenTwoVars]
#
#####################################################
def GetCovarianceBetweenTwoVars(tdfFile, 
                            valueName1, fAllowDupsInVar1,
                            valueName2, fAllowDupsInVar2,
                            requirePropertyNameList, 
                            requirePropertyRelationList, 
                            requirePropertyValueList):
    fDebug = False
    numStdDevs = 0
    stdDevTotalSum = 0

    # Get information about the requested variables. This splits
    # complicated name values like "eGFR[-30]" into a name and an 
    # offset, like "eGFR" and "-30"
    functionObject1 = None
    functionObject2 = None
    labInfo1, nameStem1, valueOffset1, functionName1 = tdf.TDF_ParseOneVariableName(valueName1)
    if (labInfo1 is None):
        print("!Error! Cannot parse variable: " + valueName1)
        return None, None
    labInfo2, nameStem2, valueOffset2, functionName2 = tdf.TDF_ParseOneVariableName(valueName2)
    if (labInfo2 is None):
        print("!Error! Cannot parse variable: " + valueName2)
        return None, None
    if (functionName1 != ""):
        functionObject1 = timefunc.CreateTimeValueFunction(functionName1, nameStem1)
        if (functionObject1 is None):
            print("\n\n\nERROR!! GetCovarianceBetweenTwoVars Undefined function1: " + functionName1)
            sys.exit(0)
    if (functionName2 != ""):
        functionObject2 = timefunc.CreateTimeValueFunction(functionName2, nameStem2)
        if (functionObject2 is None):
            print("\n\n\nERROR!! GetCovarianceBetweenTwoVars Undefined function2: " + functionName2)
            sys.exit(0)

    var1Type = tdf.TDF_GetVariableType(nameStem1)
    var2Type = tdf.TDF_GetVariableType(nameStem2)
    if (fDebug):
        print("GetCovarianceBetweenTwoVars. varName1=" + nameStem1 + ", type=" + str(var1Type))
        print("GetCovarianceBetweenTwoVars. nameStem1=" + nameStem1 + ", valueOffset1=" + str(valueOffset1))
        print("GetCovarianceBetweenTwoVars. functionName1=" + functionName1 + ", functionObject1=" + str(functionObject1))
        print("GetCovarianceBetweenTwoVars. varName2=" + nameStem2 + ", type=" + str(var2Type))
        print("GetCovarianceBetweenTwoVars. nameStem2=" + nameStem2 + ", valueOffsets=" + str(valueOffset2))
        print("GetCovarianceBetweenTwoVars. functionName2=" + functionName2 + ", functionObject2=" + str(functionObject2))

    # Iterate over every patient to build a list of values.
    # These lists will span patients, so they are useful for boolean values
    # that are always true for one patient and never true for a different patient.
    list1 = []
    list2 = []
    fFoundPatient = tdfFile.GotoFirstPatient()
    while (fFoundPatient):
        currentList1, currentList2 = tdfFile.GetSyncedPairOfValueListsForCurrentPatient(
                                                nameStem1, valueOffset1, functionObject1, fAllowDupsInVar1,
                                                nameStem2, valueOffset2, functionObject2, fAllowDupsInVar2,
                                                requirePropertyNameList,
                                                requirePropertyRelationList,
                                                requirePropertyValueList)
        if (False):
            print("GetCovarianceBetweenTwoVars. currentList1=" + str(currentList1))
            print("GetCovarianceBetweenTwoVars. currentList2=" + str(currentList2))

        list1.extend(currentList1)
        list2.extend(currentList2)

        fFoundPatient = tdfFile.GotoNextPatient()
    # End - while (patientNode):

    correlation = 0
    if (len(list1) > 2):
        if (fDebug):
            print("GetCovarianceBetweenTwoVars using combined lists")
        try:
            # For Boolean, we can use the Point-biserial correlation coefficient.
            if ((var1Type == tdf.TDF_DATA_TYPE_BOOL) 
                    or (var2Type == tdf.TDF_DATA_TYPE_BOOL)):
                correlation, pValue = stats.pointbiserialr(list1, list2)
            else:
                correlation, pValue = spearmanr(list1, list2)
        except Exception:
            correlation = 0
    # End - if (len(list1) > 2):
        

    if (fDebug):
        print("GetCovarianceBetweenTwoVars. correlation=" + str(correlation))

    return correlation
# End - GetCovarianceBetweenTwoVars






################################################################################
#
# [FindOneCovariant]
#
################################################################################
def FindOneCovariant(tdfFilePathName, inputVarname, outputVarname,
                    ReqNameList, ReqRelationList, ReqValueList, 
                    covariantResultFilePathName):
    fDebug = False
    resultLine = inputVarname + "~" + outputVarname + ":"

    if (fDebug):
        print("FindOneCovariant. tdfFilePathName = " + tdfFilePathName)
        print("FindOneCovariant. outputVarname = " + outputVarname + ", inputVarname = " + inputVarname)
        print("FindOneCovariant. ReqNameList = " + str(ReqNameList)
                + ", ReqRelationList = " + str(ReqRelationList)
                + ", ReqValueList = " + str(ReqValueList))
        print("covariantResultFilePathName = " + str(covariantResultFilePathName))
        print("resultLine = " + str(resultLine))

    # Make sure the result file name exists.
    if (not os.path.isfile(covariantResultFilePathName)):
        fileH = open(covariantResultFilePathName, "a")
        fileH.close()

    # It is possible we already found this covariance on a previous instance
    # of this program that crashed. In this case, we are running on a restarted
    # process, so do not waste time recomputing work that is already done.
    # Look for this pair in the result file
    with open(covariantResultFilePathName) as fileH:
        for line in fileH:
            line = line.lstrip()
            if (line.startswith(resultLine)):
                if (fDebug):
                    print("FindOneCovariant. Found outputVarname = " + outputVarname 
                            + ", inputVarname = " + inputVarname 
                            + ", resultLine=" + line)
                lineParts = line.split(':')
                resultValue = "Unknown"
                if (len(lineParts) > 1):
                    resultValue = lineParts[1].rstrip()
                return resultValue
            # End - if (line.startswith(resultLine)):
        # End - for line in fileH:
    # End - with open(covariantResultFilePathName) as fileH:

    if (inputVarname == outputVarname):
        covarResult = 1.0
    else:
        if (fDebug):
            print("FindOneCovariant. tdfFilePathName = " + str(tdfFilePathName))
        tdfFile = tdf.TDF_CreateTDFFileReader(tdfFilePathName, 
                                              inputVarname, outputVarname, ReqNameList)

        fAllowDupInputs = True
        fAllowDupOutputs = True
        covarResult = GetCovarianceBetweenTwoVars(tdfFile, 
                                                    inputVarname, fAllowDupInputs,
                                                    outputVarname, fAllowDupOutputs,
                                                    ReqNameList, ReqRelationList, ReqValueList)
        tdfFile.Shutdown()
    
    # Append the result to the file.
    resultLine += str(covarResult) + NEWLINE_STR
    if (fDebug):
        print("FindOneCovariant. correlation=" + str(covarResult) + ", resultLine = " + str(resultLine))

    fileH = open(covariantResultFilePathName, "a")
    fileH.write(resultLine)
    fileH.close()

    return covarResult
# End - FindOneCovariant





################################################################################
#
# [MakeCovariantTable]
#
################################################################################
def MakeCovariantTable(covariantResultFilePathName, tableFilePathName):
    fDebug = False

    # Load the raw result file into a list in memory
    allInputVars, allOutputVars, allResults = LoadCovariantsFileIntoDicts(covariantResultFilePathName)
    if (fDebug):
        print("allInputVars = " + str(allInputVars))
        print("allOutputVars = " + str(allOutputVars))
        print("allResults = " + str(allResults))

    # Make a list of all of the input variables. The column starts with a blank
    # entry, which will be the row name in each row.
    columnHeaderStr = " ,"
    for inputVarname in allInputVars:
        columnHeaderStr += (inputVarname + ",")
    columnHeaderStr = columnHeaderStr[:-1]
    if (fDebug):
        print("columnHeaderStr = " + str(columnHeaderStr))
        print("tableFilePathName = " + str(tableFilePathName))

    fileH = DataShow.StartExcelFile(tableFilePathName, columnHeaderStr)

    # For each output variable, make a bar graph and excel file
    for outputVarname in allOutputVars:
        if (fDebug):
            print("outputVarname = " + str(outputVarname))

        if (outputVarname not in allResults):
            print("ERROR! MakeCovariantTable tried to find an output var not in list. var=" 
                    + outputVarname)
            continue
        covarianceDict = allResults[outputVarname]
        if (fDebug):
            print("outputVarname = " + str(outputVarname) + ", covarianceDict = " + str(covarianceDict))

        currentRowStr = outputVarname + ","
        for inputVarname in allInputVars:
            if (inputVarname in covarianceDict):
                corrValue = round(covarianceDict[inputVarname], 4)
                currentRowStr += (str(corrValue) + ",")
            else:
                currentRowStr += ("-,")
        # for inputVarname in inputVarList:
        currentRowStr = currentRowStr[:-1]

        if (fDebug):
            print("currentRowStr = " + str(currentRowStr))

        DataShow.WriteOneLineToExcelFile(fileH, currentRowStr)
    # for outputVarname in outputVarList:

    DataShow.FinishExcelFile(fileH)
# End - MakeCovariantTable




################################################################################
#
# [FindAllCovariants]
#
################################################################################
def FindAllCovariants(
            tdfFilePathName, 
            inputVarList, 
            inputTimeModifierFunctions, 
            outputVarList,
            covariantResultFilePathName):
    fDebug = False

    for outputVarDict in outputVarList:
        print("Covariants for output: " + outputVarDict['resultVar'])
        print("============================================")

        for inputVarname in inputVarList:
            if (fDebug):
                print("FindAllCovariants. Input name=" + inputVarname)

            if (True):
                covarResult = FindOneCovariant(tdfFilePathName, 
                                        inputVarname, 
                                        outputVarDict['resultVar'], 
                                        outputVarDict['ReqNameList'], 
                                        outputVarDict['ReqRelationList'], 
                                        outputVarDict['ReqValueList'],
                                        covariantResultFilePathName)
                print("        " + inputVarname + ": " + str(covarResult))
            # End - if (False)

            for modifier in inputTimeModifierFunctions:
                covarResult = FindOneCovariant(tdfFilePathName, 
                                        inputVarname + modifier, 
                                        outputVarDict['resultVar'], 
                                        outputVarDict['ReqNameList'], 
                                        outputVarDict['ReqRelationList'], 
                                        outputVarDict['ReqValueList'],
                                        covariantResultFilePathName)
                print("        " + inputVarname + modifier + ": " + str(covarResult))
            # for modifier in inputTimeModifierFunctions:
        # for inputVarname in inputVarList:
    # for outputVarname in outputVarList:
# End - FindAllCovariants




################################################################################
#
# [FindValuePairsForAllPatients]
#
################################################################################
def FindValuePairsForAllPatients(tdfFilePathName, xValueName, yValueName,
                               ReqNameList, ReqRelationList, ReqValueList):
    fDebug = False
    resultDict = {}

    if (fDebug):
        print("FindValuePairsForAllPatients. xValueName = " + xValueName 
                    + ", yValueName = " + yValueName)

    tdfFile = tdf.TDF_CreateTDFFileReader(tdfFilePathName, 
                                    xValueName, yValueName, ReqNameList)

    # Iterate over every patient to build a list of values.
    fFoundPatient = tdfFile.GotoFirstPatient()
    while (fFoundPatient):
        resultDict = tdfFile.GetValuePairsForCurrentPatient(xValueName, yValueName,
                                                resultDict,
                                                ReqNameList, ReqRelationList, ReqValueList)

        fFoundPatient = tdfFile.GotoNextPatient()
    # End - while (patientNode):

    tdfFile.Shutdown()

    for index, (xValue, valInfo) in enumerate(resultDict.items()):
        valInfo['Avg'] = valInfo['total'] / valInfo['numVals']

    return resultDict
# End - FindValuePairsForAllPatients





################################################################################
#
# [ShowValueReproducibility]
#
################################################################################
def ShowValueReproducibility(tdfFilePathName, xValueName, maxMinutes, 
                            numHistogramBuckets, 
                            rangePerHistogramBucket, chartFilePath):
    fDebug = False
    histogramBuckets = [0] * numHistogramBuckets

    minValue = -1 * ((numHistogramBuckets - 1) / 2) * rangePerHistogramBucket
    maxValue = ((numHistogramBuckets - 1) / 2) * rangePerHistogramBucket
    if (fDebug):
        print("ShowValueReproducibility: rangePerHistogramBucket = " + str(rangePerHistogramBucket))
        print("ShowValueReproducibility: minValue = " + str(minValue) + ", maxValue = " + str(maxValue))


    tdfFile = tdf.TDF_CreateTDFFileReader(tdfFilePathName, 
                                    xValueName, xValueName, [])
    tdfFile.SetTimeResolution(1)
    tdfFile.SetCarryForwardPreviousDataValues(False)

    # Iterate over every patient to build a list of values.
    fFoundPatient = tdfFile.GotoFirstPatient()
    while (fFoundPatient):
        histogramBuckets = tdfFile.GetValueReproducibility(xValueName,
                                                maxMinutes,
                                                histogramBuckets,
                                                numHistogramBuckets,
                                                rangePerHistogramBucket,
                                                minValue)
        fFoundPatient = tdfFile.GotoNextPatient()
    # End - while (patientNode):

    tdfFile.Shutdown()

    indexOfNoError = -(minValue / rangePerHistogramBucket)
    totalCount = sum(histogramBuckets)
    if (fDebug):
        print("ShowValueReproducibility: histogramBuckets = " + str(histogramBuckets))
        print("ShowValueReproducibility: indexOfNoError = " + str(indexOfNoError))
        print("ShowValueReproducibility: histogramBuckets[indexOfNoError] = " + str(histogramBuckets[int(indexOfNoError)]))

    numNoError = histogramBuckets[int(indexOfNoError)]
    ninetyPercentTotal = int(0.9 * totalCount)
    ninetyFivePercentTotal = int(0.95 * totalCount)
    if (fDebug):
        print("ShowValueReproducibility: ninetyPercentTotal = " + str(ninetyPercentTotal))
        print("ShowValueReproducibility: ninetyFivePercentTotal = " + str(ninetyFivePercentTotal))

    print("ShowValueReproducibility: Total Num Test Pairs = " + str(totalCount))
    print("ShowValueReproducibility: Fraction Exact = " + str(round((numNoError / totalCount), 2) * 100.0))


    totalNumEvents = 0
    fPrinted90Percent = False
    for relIndex in range(int((numHistogramBuckets + 1) / 2)):
        lowIndex = indexOfNoError - relIndex
        highIndex = indexOfNoError + relIndex

        if (relIndex == 0):
            totalNumEvents += histogramBuckets[int(indexOfNoError)]
            if (fDebug):
                print("Index: " + str(indexOfNoError) + ", totalNumEvents=" + str(totalNumEvents))
        else:
            totalNumEvents += histogramBuckets[int(lowIndex)]
            totalNumEvents += histogramBuckets[int(highIndex)]
            if (fDebug):
                print("relIndex: " + str(relIndex) 
                        + ", Examine range " + str(lowIndex) + " and " + str(highIndex) 
                        + ", totalNumEvents=" + str(totalNumEvents))


        if ((totalNumEvents >= ninetyPercentTotal) and (not fPrinted90Percent)):
            print("90 percent between index " + str(lowIndex + 1) + ", and " + str(highIndex - 1)
                    + " Expect a variation between -" 
                    + str(rangePerHistogramBucket * relIndex)
                    + " and "
                    + str(rangePerHistogramBucket * relIndex))
            fPrinted90Percent = True
        # if (totalNumEvents >= ninetyPercentTotal):


        if ((totalNumEvents >= ninetyFivePercentTotal)):
            print("95 percent between index " + str(lowIndex + 1) + ", and " + str(highIndex - 1)
                    + " Expect a variation between -" 
                    + str(round((rangePerHistogramBucket * relIndex), 2))
                    + " and "
                    + str(round((rangePerHistogramBucket * relIndex), 2)))
            break
        # if (totalNumEvents >= ninetyFivePercentTotal):
    # for index in range(int((numHistogramBuckets - 1) / 2)):

    xValFloatList = np.arange(minValue, maxValue + rangePerHistogramBucket, rangePerHistogramBucket)
    xValStrList = []
    for x in xValFloatList:
        numStr = ""
        if (len(xValStrList) % 2 > 0):
            numStr = "\n"
        numStr += str(round(x, 2))
        xValStrList.append(numStr)
    # End - for x in xValFloatList:
    if (fDebug):
        print("ShowValueReproducibility: xValFloatList = " + str(xValFloatList))
        print("ShowValueReproducibility: xValStrList = " + str(xValStrList))

    DataShow.DrawBarGraph("Difference Between Simultaneous Tests of " + xValueName, 
                        "", xValStrList,
                        "Number of Occurrences", 
                        histogramBuckets, 
                        False, chartFilePath)
# End - ShowValueReproducibility








################################################################################
#
# [ShowValueDynamics]
#
################################################################################
def ShowValueDynamics(tdfFilePathName, 
                        valueName, 
                        yAxisStyle,
                        xAxisStyle,
                        valueThreshold,
                        numHistogramBuckets, 
                        fResetOnAdmissions,
                        fResetOnTransfusions,
                        titleStr,
                        yAxisLabel,
                        xAxisLabel,
                        chartFilePath):
    fDebug = False
    listOfResultBuckets = [0] * numHistogramBuckets
    listOfNumItemsInEachBucket = [0] * numHistogramBuckets

    # Get information about the requested variables. This splits
    # complicated name values like "eGFR[-30]" into a name and an 
    # offset, like "eGFR" and "-30"
    labInfo, valueNameStem, valueOffset, functionName = tdf.TDF_ParseOneVariableName(valueName)
    if (labInfo is None):
        print("!Error! Cannot parse variable: " + valueName)
        return
    functionObject = None
    if (functionName != ""):
        functionObject = timefunc.CreateTimeValueFunction(functionName, valueNameStem)
        if (functionObject is None):
            print("ERROR!! Undefined function: " + functionName)
            return
    if (fDebug):
        print("ShowValueDynamics. valueNameStem = " + valueNameStem)

    # Open the TDF file for reading.
    # Call SetCarryForwardPreviousDataValues so we only see a value when it actually happens,
    # not at every time after it happens until a new value is reported.
    tdfFile = tdf.TDF_CreateTDFFileReader(tdfFilePathName, 
                                            valueNameStem + ";HospitalAdmitDate;InHospital;TransRBC", 
                                            valueNameStem, [])
    tdfFile.SetCarryForwardPreviousDataValues(False)


    # Iterate over every patient to build a list of values.
    fFoundPatient = tdfFile.GotoFirstPatient()
    while (fFoundPatient):
        currentListOfResultBuckets, currentListOfNumItemsInEachBucket = tdfFile.GetValueDynamicsForOnePatient(valueNameStem, 
                                                                                    numHistogramBuckets, 
                                                                                    yAxisStyle,
                                                                                    xAxisStyle,
                                                                                    valueThreshold,
                                                                                    fResetOnAdmissions,
                                                                                    fResetOnTransfusions)

        if (fDebug):
            print("ShowValueDynamics: listOfNumItemsInEachBucket = " + str(listOfNumItemsInEachBucket))
            print("ShowValueDynamics: listOfResultBuckets = " + str(listOfResultBuckets))
            print("ShowValueDynamics: currentListOfNumItemsInEachBucket = " + str(currentListOfNumItemsInEachBucket))
            print("ShowValueDynamics: currentListOfResultBuckets = " + str(currentListOfResultBuckets))

        # Add the results of this patient's lists to the running totals
        listOfNumItemsInEachBucket = [a + b for a, b in zip(listOfNumItemsInEachBucket, currentListOfNumItemsInEachBucket)]
        listOfResultBuckets = [a + b for a, b in zip(listOfResultBuckets, currentListOfResultBuckets)]

        if (fDebug):
            print("ShowValueDynamics: Updated listOfNumItemsInEachBucket = " + str(listOfNumItemsInEachBucket))
            print("ShowValueDynamics: Updated listOfResultBuckets = " + str(listOfResultBuckets))
            
        fFoundPatient = tdfFile.GotoNextPatient()
    # End - while (patientNode):

    tdfFile.Shutdown()

    # Compute the average values
    yValueList = [0 if count <= 0 else round((val / count), 4) for val, count in zip(listOfResultBuckets, listOfNumItemsInEachBucket)]
    if (fDebug):
        print("listOfResultBuckets = " + str(listOfResultBuckets))
        print("listOfNumItemsInEachBucket = " + str(listOfNumItemsInEachBucket))
        print("yValueList = " + str(yValueList))

    # Compute the StdDev
    if (yAxisStyle == "StdDev"):
        yValueList = [round(math.sqrt(val), 4) for val in yValueList]
        if (fDebug):
            print("STDDEV - yValueList = " + str(yValueList))

    # Make a list of strings for the X-axis values.
    xValFloatList = np.arange(0, numHistogramBuckets, 1)
    xValStrList = [str(round(x, 2)) for x in xValFloatList]
    if (fDebug):
        print("ShowValueDynamics: xValFloatList = " + str(xValFloatList))
        print("ShowValueDynamics: xValStrList = " + str(xValStrList))

    DataShow.DrawBarGraph(titleStr,
                            xAxisLabel, xValStrList,
                            yAxisLabel, yValueList, 
                            False, 
                            chartFilePath)
# End - ShowValueDynamics






################################################################################
#
# [ShowValueStdDevForConditions]
#
################################################################################
def ShowValueStdDevForConditions(tdfFilePathName,    
                                 varForStdDev, 
                                 varForConditions,
                                 listOfBuckets,
                                 titleStr,
                                 yAxisLabel,
                                 xAxisLabel,
                                 chartFilePath):
    fDebug = False
    numHistogramBuckets = len(listOfBuckets)

    for bucketInfo in listOfBuckets:
        bucketInfo['avgStdDev'] = 0
        bucketInfo['avgIntervalChange'] = 0
        bucketInfo['numStdDevs'] = 0
        bucketInfo['totalStdDev'] = 0
        bucketInfo['totalAvgIntervalChanges'] = 0
        bucketInfo['numAvgIntervalChanges'] = 0


    # Get information about the requested variables. This splits
    # complicated name values like "eGFR[-30]" into a name and an 
    # offset, like "eGFR" and "-30"
    labInfo, varForStdDevNameStem, varForStdDevOffset, functionName = tdf.TDF_ParseOneVariableName(varForStdDev)
    if (labInfo is None):
        print("!Error! Cannot parse variable: " + varForStdDev)
        return
    varForStdDevFunctionObject = None
    if (functionName != ""):
        varForStdDevFunctionObject = timefunc.CreateTimeValueFunction(functionName, varForStdDevNameStem)
        if (varForStdDevFunctionObject is None):
            print("ERROR!! Undefined function: " + functionName)
            return
    if (fDebug):
        print("ShowValueStdDevForConditions. varForStdDevFunctionObject = " + varForStdDevFunctionObject)


    labInfo, varForConditionsNameStem, varForConditionsOffset, functionName = tdf.TDF_ParseOneVariableName(varForConditions)
    if (labInfo is None):
        print("!Error! Cannot parse variable: " + varForConditions)
        return
    varForConditionsFunctionObject = None
    if (functionName != ""):
        varForConditionsFunctionObject = timefunc.CreateTimeValueFunction(functionName, varForConditions)
        if (varForConditionsFunctionObject is None):
            print("ERROR!! Undefined function: " + functionName)
            return
    if (fDebug):
        print("varForConditionsFunctionObject = " + varForConditionsFunctionObject)


    # Open the TDF file for reading.
    # Call SetCarryForwardPreviousDataValues so we only see a value when it actually happens,
    # not at every time after it happens until a new value is reported.
    tdfFile = tdf.TDF_CreateTDFFileReader(tdfFilePathName, 
                                            varForStdDevNameStem + ";" + varForConditionsNameStem, 
                                            varForStdDevNameStem, [])
    tdfFile.SetCarryForwardPreviousDataValues(False)


    # Iterate over every patient to build a list of values.
    fFoundPatient = tdfFile.GotoFirstPatient()
    while (fFoundPatient):
        listOfBuckets = tdfFile.GetValueStdDevForConditionsForOnePatient(
                                            varForStdDevNameStem, 
                                            varForConditionsNameStem,
                                            listOfBuckets,
                                            numHistogramBuckets)
        if (fDebug):
            print("ShowValueStdDevForConditions: bucketInfo = " + str(bucketInfo))
            
        fFoundPatient = tdfFile.GotoNextPatient()
    # End - while (patientNode):

    tdfFile.Shutdown()


    # Compute the StdDev from the sum of the stdDevs
    if (fDebug):
        print("listOfBuckets = " + str(listOfBuckets))
    yValueList = 0
    for bucketInfo in listOfBuckets:
        if (bucketInfo['numStdDevs'] <= 0):
            bucketInfo['avgStdDev'] = 0
        else:
            bucketInfo['avgStdDev'] = round((bucketInfo['totalStdDev'] / bucketInfo['numStdDevs']), 4)

        #yValueList.append(round(math.sqrt(bucketInfo['avgStdDev']), 4))
        yValueList.append(bucketInfo['avgStdDev'], 4)

        if (fDebug):
            print("bucketInfo[numStdDevs] = " + str(bucketInfo['numStdDevs']))
            print("bucketInfo[totalStdDev] = " + str(bucketInfo['totalStdDev']))
            print("bucketInfo[avgStdDev] = " + str(bucketInfo['avgStdDev']))
    # End - for bucketInfo in listOfBuckets:
    if (fDebug):
        print("yValueList = " + str(yValueList))

    # Make a list of strings for the X-axis values.
    xValFloatList = np.arange(0, numHistogramBuckets, 1)
    xValStrList = [str(round(x, 2)) for x in xValFloatList]
    if (fDebug):
        print("ShowValueStdDevForConditions: xValFloatList = " + str(xValFloatList))
        print("ShowValueStdDevForConditions: xValStrList = " + str(xValStrList))

    DataShow.DrawBarGraph(titleStr,
                            xAxisLabel, xValStrList,
                            yAxisLabel, yValueList, 
                            False, 
                            chartFilePath)
# End - ShowValueStdDevForConditions






################################################################################
#
# [ShowFourHistogramsOnOneGraph]
#
################################################################################
def ShowFourHistogramsOnOneGraph(titleStr, xLabelStr, yLabelStr,
                                histogram1, label1Str, color1, 
                                histogram2, label2Str, color2, 
                                histogram3, label3Str, color3, 
                                histogram4, label4Str, color4, 
                                showInGUI, filePath):
    xValueList = list(range(0, histogram1.GetNumBuckets()))

    # You cannot do ".-o" because "o" is a style marker, not a color.
    formatStrList = [".-g", ".-c", ".-y", ".-r"]
    yNamesList = [label1Str, label2Str, label3Str, label4Str]
    ySequencesList = [histogram1.GetBucketsAsPercentages(),
                        histogram2.GetBucketsAsPercentages(),
                        histogram3.GetBucketsAsPercentages(),
                        histogram4.GetBucketsAsPercentages()]

    DataShow.DrawMultiLineGraphEx(titleStr, xLabelStr, xValueList, 
                                yLabelStr, yNamesList, ySequencesList, formatStrList,
                                showInGUI, filePath)
# End - ShowFourHistogramsOnOneGraph







################################################################################
#
# [MakeCovariantBarGraphs]
#
################################################################################
def SortFunction(item):
    if (math.isnan(item[1])):
        return 0 

    return abs(item[1])
# End - SortFunction




################################################################################
#
# [MakeCovariantBarGraphs]
#
################################################################################
def MakeCovariantBarGraphs(resultFilePathName, 
                            inputVarList, 
                            timeModifierFunctions, 
                            outputVarList, 
                            numImportantVariables, 
                            covariancePathNamePrefix):
    fDebug = False
    
    # Load the raw result file into a list in memory
    allInputVars, allOutputVars, allResults = LoadCovariantsFileIntoDicts(resultFilePathName)
    if (fDebug):
        print("allInputVars = " + str(allInputVars))
        print("allOutputVars = " + str(allOutputVars))
        print("allResults = " + str(allResults))

    for outputVarname in allOutputVars:
        if (outputVarname not in allResults):
            continue
        covarianceDict = allResults[outputVarname]
        if (fDebug):
            print("outputVarname = " + str(outputVarname))
            print("covarianceDict = " + str(covarianceDict))

        sortedList = sorted(covarianceDict.items(), key=SortFunction, reverse=True)
        if (fDebug):
            print("sortedList = " + str(sortedList))

        MakeSingleCovariantBarGraph(
                            sortedList, 
                            outputVarname, 
                            numImportantVariables, 
                            covariancePathNamePrefix + outputVarname + ".jpg")
    # for outputVarname in allOutputVars:
# End - MakeCovariantBarGraphs





################################################################################
#
# [MakeCovariantBarGraphs]
#
################################################################################
def MakeSingleCovariantBarGraph(sortedList, outputVarname, numImportantVariables, 
                                barGraphFilePathName):
    fDebug = False
    xValueList = []
    yValueList = []

    for entry in sortedList:
        inputName = entry[0]
        coeffFloat = round(entry[1], 4)
        if (fDebug):
            print("inputName = " + str(inputName))
            print("coeffFloat = " + str(coeffFloat))

        yValueList.append(coeffFloat)
        if ((len(xValueList) % 2) == 0):
            xValueList.append(inputName)
        else:
            xValueList.append("\n" + inputName)
        if (len(xValueList) >= numImportantVariables):
            break
    # End for entry in sortedList:

    if (len(xValueList) <= 0):
        return

    # Make the bar graph
    graphTitleStr = "Covariance with " + outputVarname + " (Top " + str(len(xValueList)) + " of " + str(len(sortedList)) + ")"
    DataShow.DrawBarGraph(graphTitleStr,
                          " ", xValueList, 
                          "Covariance", yValueList, 
                          False, barGraphFilePathName)

    if (fDebug):
        print("graphTitleStr = " + str(graphTitleStr))
        print("barGraphFilePathName = " + str(barGraphFilePathName))
# End - MakeCovariantBarGraphs






################################################################################
#
#
################################################################################
class TDFShowHistogram():
    #####################################################
    # Constructor - This method is part of any class
    #####################################################
    def __init__(self, varName):
        self.varType = tdf.TDF_DATA_TYPE_INT
        self.minVal = 0
        self.maxVal = 10
        self.numClasses = 1
        self.bucketSize = 1

        if ((varName is not None) and (varName != "")):
            self.Init(varName)
    # End -  __init__


    #####################################################
    # [TDFShowHistogram::
    # Destructor - This method is part of any class
    #####################################################
    def __del__(self):
        return


    #####################################################
    #
    # [TDFShowHistogram::Init]
    #
    #####################################################
    def Init(self, varName):
        labInfo, valueNameStem, valueOffset, functionName = tdf.TDF_ParseOneVariableName(varName)
        if (labInfo is None):
            print("!Error! Cannot parse variable: " + varName)
            return

        self.varName = varName
        self.varType = labInfo['dataType']
        self.minVal = labInfo['minVal']
        self.maxVal = labInfo['maxVal']

        if (self.varType == tdf.TDF_DATA_TYPE_INT):
            self.numClasses = 20
            range = float(self.maxVal - self.minVal)
            self.bucketSize = float(range) / float(self.numClasses)
        elif (self.varType == tdf.TDF_DATA_TYPE_FLOAT):
            self.numClasses = 20
            range = float(self.maxVal - self.minVal)
            self.bucketSize = float(range) / float(self.numClasses)
        elif (self.varType == tdf.TDF_DATA_TYPE_BOOL):
            self.numClasses = 2
            self.bucketSize = 1
        elif (self.varType == tdf.TDF_DATA_TYPE_FUTURE_EVENT_CLASS):
            self.numClasses = tdf.TDF_NUM_FUTURE_EVENT_CATEGORIES
            self.bucketSize = 1
        else:
            self.numClasses = 1
            self.bucketSize = 1

        self.numVals = 0
        self.totalVal = 0 
        self.histogramBuckets = [0] * self.numClasses        
    # End - Init


    #####################################################
    #
    # [TDFShowHistogram::AddValue]
    #
    #####################################################
    def AddValue(self, value):
        # Ignore values of 0
        if (value <= 0):
            return

        if (value < self.minVal):
            value = self.minVal
        offset = value - self.minVal

        bucketNum = round(offset / self.bucketSize)
        if (bucketNum >= self.numClasses):
            bucketNum = self.numClasses - 1

        self.numVals += 1
        self.totalVal += value 
        self.histogramBuckets[bucketNum] += 1
    # End - AddValue



    #####################################################
    #
    # [TDFShowHistogram::GetNumBuckets]
    #
    #####################################################
    def GetNumBuckets(self):
        return self.numClasses
    # End - GetNumBuckets()



    #####################################################
    #
    # [TDFShowHistogram::GetBuckets]
    #
    #####################################################
    def GetBuckets(self):
        return self.histogramBuckets
    # End - GetBuckets()



    #####################################################
    #
    # [TDFShowHistogram::GetBucketsAsPercentages]
    #
    #####################################################
    def GetBucketsAsPercentages(self):
        fDebug = False
        if (fDebug):
            print("GetBucketsAsPercentages. self.numClasses = " + str(self.numClasses))

        resultArray = self.histogramBuckets
        if (fDebug):
            print("GetBucketsAsPercentages. resultArray = " + str(resultArray))
        sumOfElements = sum(resultArray)
        if (fDebug):
            print("GetBucketsAsPercentages. sumOfElements = " + str(sumOfElements))

        if (sumOfElements <= 0):
            scaledList = [0] * len(resultArray)
        else:
            scaledList = [(float(x) / sumOfElements) * 100.0 for x in resultArray]
        if (fDebug):
            print("GetBucketsAsPercentages. scaledList = " + str(scaledList))

        return scaledList
    # End - GetBucketsAsPercentages()

# End - class TDFShowHistogram



