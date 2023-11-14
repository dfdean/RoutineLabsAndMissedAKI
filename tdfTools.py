#####################################################################################
# 
# Copyright (c) 2020-2023 Dawson Dean
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
#####################################################################################
#
# TDF - Timeline Data Format
#
# The file is xml file format that is designed to store time-series of data for medical 
# applications. All Elements have close tags, and comments are standard XML comments.
#
# To read a TDF file, we typically iterate at several levels:
#   For each partition in the file
#       For each patient in the partition
#           For each data entry in the current patient
#
# You do not have to iterate over partitions, so you can instead just iterate over
#   all patients in the file. However, this allows you to have different worker processes
#   for a single file, and so avoid Python memory growth. That is important, because on very
#   large files, Python's heap can grow to consume all virtual memory and crash the process.
# So, in the simplest case:
#
#   For each patient in the file
#       For each data entry in the current patient
#
##########################################
#
# XML Syntax
# ------------
#  <TDF>
#  Parent Element: None (document root)
#  Child Elements: Head, PatientList
#  Text Contents: None
#  Attributes: None
#
#  <Head>
#  Parent Element: TDF
#  Child Elements: Description, Created, DataSource, Events, DataValues
#  Text Contents: None
#  Attributes: None
#
#  <Vocab>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: One of the element vocabularies. Current supported values are:
#           Medicine
#  Attributes: None
#
#  <Description>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: A human readable string that describes this data.
#  Attributes: None
#
#  <DataType>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: A human readable string that describes what this data is. For medical data, this includes "Patient", "Derived"
#  Attributes: None
#
#  <DataSource>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: A human readable string that describes where this data was extracted from
#  Attributes: None
#
#  <Created>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: Contains the time and data that the file was generated
#  Attributes: None
#
#  <Keywords>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: Contains a comma-separated list of Keywords
#  Attributes: None
#
#  <Events>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: Contains a comma-separated list of events
#  Attributes: None
#
#  <DataValues>
#  Parent Element: Head
#  Child Elements: None
#  Text Contents: Contains a comma-separated list of events
#  Attributes: None
#
#  <PatientList>
#  Parent Element: TDF
#  Child Elements: A list of <Patient> elements
#  Text Contents: None
#  Attributes: None
#
#
#  <Patient id=nnn gender=male race=c>
#  Parent Element: PatientList
#  Child Elements:
#     This contains all data and events for a single patient. This related
#     data is stored as nested elements below the Patient element.
#  Text Contents: None
#  Attributes: 
#       id = nnn
#           A unique id within this file. It is de-identified, so it is not
#           related to any actual MRN.
#
#       gender = "aaa" where aaa is one of:
#           M - Male
#           F - Female
#
#       race = "aaa" where aaa is one of:
#           ? - Unknown
#           W - white, caucasian
#           Af - African, African American
#           L - Latin, Hispanic
#           A - Asian
#           I - Asian Indian
#           AI - American Indian, Alaskan
#           ME - Middle Eastern
#
#
#  <E C=className V=value T=ttt V=aaa/bbb/ccc D=detail />
#  Parent Element: Patient
#  Child Elements: None
#  Text Contents:
#     This element describes one or more events that happened at a time.
#     The events are a comma-separated list of words in the text of the element.
#  Attributes:
#      T="ttt" is the timestamp for when the event happened
#      C = className where className is described in TDFMedicineValues
#      V = value   where value is described in TDFMedicineValues
#      P = Priority. This is only used for RadImg
#      D - Detail 
#  Optional Attributes - These may be included in some Events of class "Admit"
#       DiedThisAdmission = T/F  Died During the Admission
#       DiedIn12Mos = T/F
#       Readmit30D = T/F Readmit In 30 Days
#
#
#
#  <OC scope=xxx>  name=value, name=value, name=value   </OC>
#       OC is short for "Outcomes" and this element contains a text list of outcomes either during 
#       a single admission or for the patient after all admissions. 
#       If the scope attribute is "Admit" then this applies just to the admission
#       If the scope attribute is "All" then this applies to the patient after all admissions.
#
#       In the text contents, name is one of:
#           DiedThisAdmission - The value is "T" or "F". Died During the Admission
#           DiedIn12Mos - The value is "T" or "F"
#           ReadmitIn30Days - The value is "T" or "F"
#
#
#
#  <D C=className T=ttt>  name=value, name=value, name=value   </D>
#  Parent Element: Parient
#  Child Elements: None
#  Text Contents:
#   This element contains all data that is sampled at a single time.
#   An example is a Basic Metabolic Panel, which has 7 lab values, and all are
#   drawn from the same blood sample at the same time.    
#   The data values are stored as a text string of name=value pairs.
#             Na=131,K=3.7
#  Attributes:
#      T="ttt" is the timestamp for when the event happened
#
#      C = className  where className is one of:
#           L - Labs
#           V - Vitals
#           D - Diagnoses
#
#       O = options which is a set of options flags. For diagnoses, this is 0 or 1 which
#           means whether the value was present on admission
#
#       V - A series of name value pairs, in the form:
#           name1=val1,name2=valw,name3=val3
#           The values are numbers except in a few specific cases below.
#
#       The time category when an event will happen. 
#       This includes events that never happen, because it assigns a special category to that.
#       Each "Future_Category_XXX" variable is a category:
#       0 = EVENT is happening now or has previously happened
#       1 = EVENT will happen in 1 day
#       2 = EVENT will happen in 3 days
#       3 = EVENT will happen in 7 days
#       4 = EVENT will happen in 14 days
#       5 = EVENT will happen in 30 days
#       6 = EVENT will happen in 90 days
#       7 = EVENT will happen in 180 days
#       8 = EVENT will happen in 365 days
#       9 = EVENT will happen in 730 days (2yrs, some ESRD models use this)
#       10 = EVENT will happen in 1095 days (3yrs)
#       11 = EVENT will happen in 1825 days (5yrs, some ESRD models use this)
#       12 = EVENT will happen in 3650 days (10yrs, Framingham uses this)
#       13 = EVENT will not happen in the next 10yrs
#
#
#  <M T=xxxx diag=value>
#  This is a medication.
#  Attributes:
#      T="ttt" is the timestamp for when the event happened
#      C = medType, which is one of the following:
#         IRx - This is an inpatient prescription. The date is when it was ordered, so it starts after this date.
#         HRx - This is a home prescription. The date is when it was ordered, so it starts after this date.
#         Rec - This is an inpatient med-rec, which is when it was reconciled. The date is the time of the med-rec, so the med was given up tp this date.
#         Mar - This is an inpatient administration, recorded in the MAR.
#         Blood - This is a transfusion
#      ST="ttt" this is a stop time. This is usually unreliable. Some hospitals set an arbitrary
#         stop time, like 1 year from start, to indicate a med that continues until it is explicitly discontinued.
#
#   The body of the element is a list of medications.
#           med1,med2,med3,......,medn
#   Where each med is a tuple string:
#       drugName:dose:doseRoute:dosesPerDay
#       Dose is a floating point number, like 12.5 or 50    
#           The units of the dose string are implied by the med, but are usually mg.
#       The dose route is:
#           i - IV
#           o - oral
#           t - topical
#       The dosesPerDay is an integer. It is assumed doses are spread out evenly over the day, so 
#       for example, 2 doses per day would imply Q12h.
#
#
#  <Text T=ttt C=nnn>  some-text   </Text>
#  Parent Element: Patient
#  Child Elements: None
#  Text Contents:
#     This is a free text note or report 
#  Attributes:
#      T="ttt" is the timestamp for when the procedure was reported.
#      C="nnn" where nnn is one of:
#           Note
#
#
##########################################
#
# TimeStamps are a formatted string that is the time code. Each TimeStamp has the
# format:   
#          dd:hh:mm
# or:
#          dd:hh:mm:ss
#
# where:
#   dd is the number of days. 
#       The number may be positive or negative depending on whether the timecode
#       is before or after the indexEvent of the timeline.
#   hh is the number of hours. 
#   mm is the number of minutes. 
#   ss is the number of seconds. This is optional and not used for medical data.
#
# All numbers are 2 or more digits. They are padded with a leading 0 if the 
# number is < 10.
#
# Days are the day in your lifetime, so 365 is the 1st birthday, 3650 is the tenth birthday and
# 36500 is the 100th birthday. This representation has several advantages:
# 1. It is deidentified. It has no relation to the calendar date
# 2. It is easy to compute time intervals, like whether 2 dates are within 30 days of each other.
# 3. The same timestamp tells you when something happened in relation to all other events, and also
#   exactly how old the patient is at each event.
# 
#
##########################################
#
# The Reader API allows clients to iterate over patients and read values
# for a patient. A client may specify criteria that restricts data to specific sections.
# Some example criteria include:
#     - Values while a patient is in the hospital only
#     - Everything between admission and discharge to the hospital
#     - All events between a surgery and discharge. This looks at post-operative complications.
#     - All events between dialysis and 1 day later. This looks at post-dialysis complications.
#
##########################################
# DEPRECATED FEATURES:
#
#  <Preexisting> name=value   </Preexisting>
#  ***** DEPRECATED ***** (Used only in Myeloma)
#  Parent Element: Patient
#  Child Elements: None
#  Text Contents:
#   This is a comma-separated list of pre-existing conditions. 
#   These exist before any timed values.
#   Name is a condition, and the value is T or F
#  Attributes: None
#
#  <FinalDiag>  name=value   </FinalDiag>
#  ***** DEPRECATED ***** (Used only in Myeloma)
#  Parent Element: Patient
#  Child Elements: None
#  Text Contents:
#   This is a comma-separated list of final conditions
#   Name is a condition, and the value is T or F
#  Attributes:
#      T="ttt" is the timestamp for when the event happened
#
#      diag = xxxxx
################################################################################

import os
import sys
import math
import numpy as np
import re
from datetime import datetime
import copy

# Normally we have to set the search path to load these.
# But, this .py file is always in the same directories as these imported modules.
import xmlTools as dxml
import tdfTimeFunctions as timefunc

# Import g_LabValueInfo
from tdfMedicineValues import g_LabValueInfo
from tdfMedicineValues import g_FunctionInfo
from tdfMedicineValues import g_InterestingMeds

DEBUG_WRITER = True

# WARNING! These are also defined in tdfMedicineValues.py
# We really need a public include file with just these values.
# Until then, any change here must be duplicated in tdfMedicineValues.py
TDF_DATA_TYPE_INT                   = 0
TDF_DATA_TYPE_FLOAT                 = 1
TDF_DATA_TYPE_BOOL                  = 2
TDF_DATA_TYPE_FUTURE_EVENT_CLASS    = 3
TDF_DATA_TYPE_STRING_LIST           = 4
TDF_DATA_TYPE_UNKNOWN               = -1

# These are the values for a future event variable.
TDF_FUTURE_EVENT_CATEGORY_NOW_OR_PAST    = 0
TDF_FUTURE_EVENT_CATEGORY_IN_1_DAY       = 1
TDF_FUTURE_EVENT_CATEGORY_IN_3_DAYS      = 2
TDF_FUTURE_EVENT_CATEGORY_IN_7_DAYS      = 3
TDF_FUTURE_EVENT_CATEGORY_IN_14_DAYS     = 4
TDF_FUTURE_EVENT_CATEGORY_IN_30_DAYS     = 5
TDF_FUTURE_EVENT_CATEGORY_IN_90_DAYS     = 6
TDF_FUTURE_EVENT_CATEGORY_IN_180_DAYS    = 7
TDF_FUTURE_EVENT_CATEGORY_IN_365_DAYS    = 8
TDF_FUTURE_EVENT_CATEGORY_IN_730_DAYS    = 9
TDF_FUTURE_EVENT_CATEGORY_IN_1095_DAYS   = 10
TDF_FUTURE_EVENT_CATEGORY_IN_1825_DAYS   = 11
TDF_FUTURE_EVENT_CATEGORY_IN_3650_DAYS   = 12
TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS   = 13

# WARNING! These are also defined in tdfMedicineValues.py
# We really need a public include file with just these values.
# Until then, any change here must be duplicated in tdfMedicineValues.py
TDF_NUM_FUTURE_EVENT_CATEGORIES = 14
TDF_MAX_FUTURE_EVENT_CATEGORY = (TDF_NUM_FUTURE_EVENT_CATEGORIES - 1)

g_CategoryToNumDays = {
    TDF_FUTURE_EVENT_CATEGORY_NOW_OR_PAST: 0,
    TDF_FUTURE_EVENT_CATEGORY_IN_1_DAY: 1,
    TDF_FUTURE_EVENT_CATEGORY_IN_3_DAYS: 3,
    TDF_FUTURE_EVENT_CATEGORY_IN_7_DAYS: 7,
    TDF_FUTURE_EVENT_CATEGORY_IN_14_DAYS: 14,
    TDF_FUTURE_EVENT_CATEGORY_IN_30_DAYS: 30,
    TDF_FUTURE_EVENT_CATEGORY_IN_90_DAYS: 90,
    TDF_FUTURE_EVENT_CATEGORY_IN_180_DAYS: 180,
    TDF_FUTURE_EVENT_CATEGORY_IN_365_DAYS: 365,
    TDF_FUTURE_EVENT_CATEGORY_IN_730_DAYS: 730,
    TDF_FUTURE_EVENT_CATEGORY_IN_1095_DAYS: 1095,
    TDF_FUTURE_EVENT_CATEGORY_IN_1825_DAYS: 1825,
    TDF_FUTURE_EVENT_CATEGORY_IN_3650_DAYS: 3650,
    TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS: 10000
    }

# WARNING! These are also defined in tdfMedicineValues.py
# We really need a public include file with just these values.
# Until then, any change here must be duplicated in tdfMedicineValues.py
ANY_EVENT_OR_VALUE = "ANY"

# This is 0-based, so January is 0
g_DaysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

NEWLINE_STR = "\n"

MAX_PREVIOUS_LAB_EXTRA_PREVIOUS = 365
MAX_PREVIOUS_LAB_EXTRA_FUTURE   = 60

# These separate variables in a list, or rows of variables in a sequence.
VARIABLE_LIST_SEPARATOR             = ";"
VARIABLE_ROW_SEPARATOR              = "/"

# These are the parts of a single variable name.
# A variable name can include an offset and functions
# Some examples:   a   a[3]    a.f()
VARIABLE_FUNCTION_PARAM_SEPARATOR   = ","
VARIABLE_START_OFFSET_MARKER        = "["
VARIABLE_STOP_OFFSET_MARKER         = "]"
VARIABLE_START_PARAM_ARGS_MARKER    = "("
VARIABLE_STOP_PARAM_ARGS_MARKER     = ")"
VARIABLE_FUNCTION_MARKER            = "."

RESET_MELD_STATE_WHEN_IMPROVES  = True
RESET_CKD_STATE_WHEN_IMPROVES   = True

# These are the parts of a TDF Condition. It is stored as a Dict
TDF_CONDITION_NAME_LIST     = "nameList"
TDF_CONDITION_VALUE_LIST    = "valueList"
TDF_CONDITION_RELATION_LIST = "relationList"
TDF_CONDITION_LIST_LENGTH   = "listLength"
TDF_CONDITION_COMPILED      = "compiled"

TDF_INVALID_VALUE = -314159265
# This allows testing for TDF_INVALID_VALUE this resilient to rounding errors and
# conversions between int and float. Use if (x > TDF_SMALLEST_VALID_VALUE):
# If this were C, I would use #define IS_VALID_VALUE(x) (x > TDF_SMALLEST_VALID_VALUE)
# Note, however, that times/dates (day number) and indexes are always positive, so they
# may compare to 0 to test validity.
TDF_SMALLEST_VALID_VALUE = -1000

g_TDF_Log_Buffer = ""

MIN_CR_RISE_FOR_AKI = 0.3

g_PaddingStr = """____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________\
____________________________________________________________________________________________________"""



################################################################################
#
# [TDF_GetDataTypeName]
#
################################################################################
def TDF_GetDataTypeName(typeID):
    if (typeID == TDF_DATA_TYPE_FLOAT):
        return("Float")
    if (typeID == TDF_DATA_TYPE_INT):
        return("Int")
    if (typeID == TDF_DATA_TYPE_BOOL):
        return("Bool")
    if (typeID == TDF_DATA_TYPE_FUTURE_EVENT_CLASS):
        return("FutureEventClass")

    return("Unknown")
# End - TDF_GetDataTypeName



################################################################################
#
# [TDF_Log]
#
################################################################################
def TDF_Log(message):
    global g_TDF_Log_Buffer
    g_TDF_Log_Buffer = g_TDF_Log_Buffer + "TDF: " + message + "\n"
    print(message)
# End - TDF_Log



################################################################################
#
# [TDF_GetLog]
#
################################################################################
def TDF_GetLog():
    global g_TDF_Log_Buffer
    return(g_TDF_Log_Buffer)
# End - TDF_GetLog



################################################################################
# 
# [TDF_MakeTimeStamp]
#
# This creates a formatted string that is the time code. Each timecode has the
# format:
#          dd:hh:mm
# or:
#          dd:hh:mm:ss
#
# where:
#   dd is the number of days. 
#       The number may be positive or negative depending on whether the timecode
#       is before or after the indexEvent of the timeline.
#   hh is the number of hours. 
#   mm is the number of minutes. 
#   ss is the number of seconds. This is optional and not used for medical data.
#
# All numbers are 2 or more digits. They are padded with a leading 0 if the 
# number is < 10.
################################################################################
def TDF_MakeTimeStamp(days, hours, minutes):
    result = "{0:0>2d}:{1:0>2d}:{2:0>2d}".format(days, hours, minutes)
    #print("\nresult=" + result)
    return result
# End - TDF_MakeTimeStamp




################################################################################
# 
# [TDF_ConvertTimeStampToInt]
#
# This parses a formatted string that is a time code and converts it to the
# number of seconds. Each timecode has the format:   nn:nn:nn:nn
# where:
#
#   nn is the number of days
#   nn is the number of hours
#   nn is the number of minutes 
#   nn is the number of seconds 
#
# All numbers are 2 or more digits. They are padded with a leading 0 if the 
# number is < 10.
#  
################################################################################
def TDF_ConvertTimeStampToInt(timeCode):
    words = timeCode.split(':')

    # Add days in seconds
    result = (int(words[0]) * 24 * 60 * 60)

    # Add hours in seconds
    result += (int(words[1]) * 60 * 60)

    # Add minutes in seconds
    result += (int(words[2]) * 60)

    # Add seconds if they are present - these are optional
    if (len(words) >= 4):
        result = result + int(words[3])

    return result
# End - TDF_ConvertTimeStampToInt





################################################################################
# 
# This parses a formatted string that is a time code and converts it to separate 
# integers
################################################################################
def TDF_ParseTimeStamp(timeCode):
    if (timeCode == ""):
        TDF_Log("Error. TDF_ParseTimeStamp invalid str: " + timeCode)
        return 0, 0, 0

    # This is days, hours, min
    words = timeCode.split(':')
    return int(words[0]), int(words[1]), int(words[2])
# End - TDF_ParseTimeStamp






################################################################################
# 
# [TDF_ConvertDateToTDFTimeStamp]
#
# Note, g_DaysInMonth is 0-based, while the date strings use months that are 1-based.
################################################################################
def TDF_ConvertDateToTDFTimeStamp(dateYear, dateMonth, dateDayOfMonth, birthDateYear, 
                                    birthDateMonth, birthDateDayOfMonth):
    global g_DaysInMonth
    deltaDays = 0
    dateHours = 0
    dateMin = 0

    # 1900 was NOT a leap year but 2000 was a leap year
    fIsDateLeapYear = 0
    fIsBirthDateLeapYear = 0
    if (((dateYear - 1900) % 4) == 0):
        fIsDateLeapYear = 1
    if (((birthDateYear - 1900) % 4) == 0):
        fIsBirthDateLeapYear = 1

    #####################################
    # Find the time between the two dates.
    # First, assume they are in different years. This is the normal case.
    if (dateYear > birthDateYear):
        # Advance days to the start of the next month after the birthday.
        deltaDays = (g_DaysInMonth[birthDateMonth - 1] - birthDateDayOfMonth)
        if ((fIsBirthDateLeapYear) and (birthDateMonth == 2)):
            deltaDays += 1

        # Advance to the start of the next year
        startMonth = birthDateMonth + 1
        if ((fIsBirthDateLeapYear) and (startMonth == 2)):
            deltaDays += 1
        while (startMonth <= 12):
            deltaDays = deltaDays + g_DaysInMonth[startMonth - 1]
            startMonth = startMonth + 1
        birthDateYear = birthDateYear + 1

        # Advance to the target year. 
        if (dateYear > birthDateYear):
            deltaDays = deltaDays + ((dateYear - birthDateYear) * 365)
            # Compute the number of leap years we skip.
            # 1900 was NOT a leap year but 2000 was a leap year
            numLeapYearsInYear = math.floor((dateYear - 1900) / 4)
            numLeapYearsInBirthYear = math.floor((birthDateYear - 1900) / 4)
            numSkippedLeapYears = numLeapYearsInYear - numLeapYearsInBirthYear
            if (numSkippedLeapYears > 0):
                deltaDays = deltaDays + numSkippedLeapYears

        # Advance to the target month.
        startMonth = 1
        while (startMonth < dateMonth):
            deltaDays = deltaDays + g_DaysInMonth[startMonth - 1]
            startMonth = startMonth + 1
        # Add a day if we skipped over Feb 29 in a leap year.
        if ((fIsDateLeapYear) and (dateMonth > 2)):
            deltaDays += 1

        # Advance to the target day
        deltaDays = deltaDays + dateDayOfMonth


    ################################
    elif ((dateYear == birthDateYear) and (dateMonth > birthDateMonth)):
        # Advance to the start of the next month.
        deltaDays = (g_DaysInMonth[birthDateMonth - 1] - birthDateDayOfMonth)
        # Add a day if we skipped over Feb 29 in a leap year.
        if ((fIsBirthDateLeapYear) and (birthDateMonth == 2)):
            deltaDays += 1

        # Advance to the target month
        startMonth = birthDateMonth + 1
        while (startMonth < dateMonth):
            deltaDays = deltaDays + g_DaysInMonth[startMonth - 1]
            startMonth = startMonth + 1
        # Add a day if we skipped over Feb 29 in a leap year.
        if ((fIsBirthDateLeapYear) and (birthDateMonth == 1)):
            deltaDays += 1

        # Advance to the target day
        deltaDays = deltaDays + dateDayOfMonth
    ################################
    elif ((dateYear == birthDateYear) and (dateMonth == birthDateMonth)):
        # Advance to the target day
        deltaDays = (dateDayOfMonth - birthDateDayOfMonth)
    else:
        print("TDF_ConvertDateToTDFTimeStamp: Unexpected data relationshops")
        print("TDF_ConvertDateToTDFTimeStamp: dateYear = " + str(dateYear))
        print("TDF_ConvertDateToTDFTimeStamp: dateMonth = " + str(dateMonth))
        print("TDF_ConvertDateToTDFTimeStamp: dateDayOfMonth = " + str(dateDayOfMonth))
        print("TDF_ConvertDateToTDFTimeStamp: birthDateYear = " + str(birthDateYear))
        print("TDF_ConvertDateToTDFTimeStamp: birthDateMonth = " + str(birthDateMonth))
        print("TDF_ConvertDateToTDFTimeStamp: birthDateDayOfMonth = " + str(birthDateDayOfMonth))
        return("")

    result = TDF_MakeTimeStamp(deltaDays, dateHours, dateMin)
    return result
# End - TDF_ConvertDateToTDFTimeStamp








################################################################################
#
# This is used only for writing a TDF File. Typically, it is used when importing 
# data from some other format into TDF.
#
################################################################################
class TDFFileWriter():
    #####################################################
    # Constructor - This method is part of any class
    #####################################################
    def __init__(self):
        self.Latest_Value_Day = TDF_INVALID_VALUE
        self.Latest_Value_Hour = TDF_INVALID_VALUE
        self.Latest_Value_Min = TDF_INVALID_VALUE
        self.Latest_Value_Sec = TDF_INVALID_VALUE
    # End -  __init__


    #####################################################
    # [TDFFileWriter::
    # Destructor - This method is part of any class
    #####################################################
    def __del__(self):
        return


    #####################################################
    #
    # [TDFFileWriter::SaveAndClose]
    #
    # Called to explicitly release resources
    #####################################################
    def SaveAndClose(self):
        self.outputFileH.flush()
        self.outputFileH.close()
    # End of SaveAndClose



    #####################################################
    #
    # [TDFFileWriter::__SetFileOutputFileHandle__
    # 
    #####################################################
    def __SetFileOutputFileHandle__(self, fileH):
        self.outputFileH = fileH
    # End -  __SetFileOutputFileHandle__



    #####################################################
    #
    # [TDFFileWriter::WriteHeader]
    #
    #####################################################
    def WriteHeader(self, comment, dataSourceStr, keywordStr):
        self.outputFileH.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + NEWLINE_STR)
        self.outputFileH.write("<TDF version=\"0.1\" xmlns=\"http://www.dawsondean.com/ns/TDF/\">" + NEWLINE_STR)
        self.outputFileH.write(NEWLINE_STR)
        self.outputFileH.write("<Head>" + NEWLINE_STR)
        self.outputFileH.write("    <Vocabulary>Medicine</Vocabulary>" + NEWLINE_STR)
        self.outputFileH.write("    <VocabularyDefinition></VocabularyDefinition>" + NEWLINE_STR)
        self.outputFileH.write("    <Description>" + comment + "</Description>" + NEWLINE_STR)    
        self.outputFileH.write("    <DataSource>" + dataSourceStr + "</DataSource>" + NEWLINE_STR)
        self.outputFileH.write("    <Created>" + datetime.today().strftime('%b-%d-%Y') + " "
                + datetime.today().strftime('%H:%M') + "</Created>" + NEWLINE_STR)
        self.outputFileH.write("    <PatientLocationIndex></PatientLocationIndex>" + NEWLINE_STR)
        self.outputFileH.write("    <Properties>" + keywordStr + "</Properties>" + NEWLINE_STR)
        self.outputFileH.write("    <Padding>" + g_PaddingStr + "</Padding>" + NEWLINE_STR)

        self.outputFileH.write("</Head>" + NEWLINE_STR)    
        self.outputFileH.write(NEWLINE_STR)
        self.outputFileH.write("<PatientList>" + NEWLINE_STR)    
    # End of WriteHeader




    #####################################################
    #
    # [TDFFileWriter::WriteFooter]
    #
    #####################################################
    def WriteFooter(self):
        self.outputFileH.write(NEWLINE_STR + "</PatientList>" + NEWLINE_STR)    
        self.outputFileH.write(NEWLINE_STR + "</TDF>" + NEWLINE_STR)
        self.outputFileH.write(NEWLINE_STR + NEWLINE_STR)
    # End of WriteFooter




    #####################################################
    #
    # [TDFFileWriter::WriteXMLNode]
    #
    #####################################################
    def WriteXMLNode(self, xmlNode):
        #print("Starting WriteXMLNode")
        bytesStr = xmlNode.toprettyxml(indent='  ', newl='', encoding="utf-8")
        textStr = bytesStr.decode("utf-8", "strict")  

        self.outputFileH.write(NEWLINE_STR + NEWLINE_STR)
        self.outputFileH.write(textStr)
    # End of WriteXMLNode




    ################################################################################
    # 
    # [TDFFileWriter::StartPatientNode]
    #
    ################################################################################
    def StartPatientNode(self, patientID, gender, race):
        self.Latest_Value_Day = TDF_INVALID_VALUE
        self.Latest_Value_Hour = TDF_INVALID_VALUE
        self.Latest_Value_Min = TDF_INVALID_VALUE
        self.Latest_Value_Sec = TDF_INVALID_VALUE

        textStr = NEWLINE_STR + NEWLINE_STR + "<Patient"
        textStr = textStr + " id=\"" + str(patientID) + "\""

        if ((gender is not None) and (gender != "")):
            textStr = textStr + " gender=\"" + gender + "\""

        if ((race is not None) and (race != "")):
            textStr = textStr + " race=\"" + race + "\""

        textStr = textStr + ">" + NEWLINE_STR

        self.outputFileH.write(textStr)
    # End - StartPatientNode




    ################################################################################
    # 
    # [TDFFileWriter::FinishPatientNode]
    #
    ################################################################################
    def FinishPatientNode(self):
        self.Latest_Value_Day = TDF_INVALID_VALUE
        self.Latest_Value_Hour = TDF_INVALID_VALUE
        self.Latest_Value_Min = TDF_INVALID_VALUE
        self.Latest_Value_Sec = TDF_INVALID_VALUE

        self.outputFileH.write("</Patient>" + NEWLINE_STR)
    # End - FinishPatientNode




    ################################################################################
    # 
    # [TDFFileWriter::WriteOutcomesNode]
    #
    ################################################################################
    def WriteOutcomesNode(self, diedDuringAdmission, diedIn12MonthsStr, readmit30D):
        bodyStr = ""
        if ((diedDuringAdmission is not None) and (diedDuringAdmission != "")):
            bodyStr = bodyStr + "DiedThisAdmission=" + diedDuringAdmission + ";"
        if ((diedIn12MonthsStr is not None) and (diedIn12MonthsStr != "")):
            bodyStr = bodyStr + "DiedIn12Mos=" + diedIn12MonthsStr + ";"
        if ((readmit30D is not None) and (readmit30D != "")):
            bodyStr = bodyStr + "Readmit30D=" + readmit30D + ";"

        # Remove the last ";"
        if (bodyStr != ""):
            bodyStr = bodyStr[:-1]

        if (DEBUG_WRITER):
            if ((">" in bodyStr) or ("<" in bodyStr)):
                print("ERROR!!!!! WriteOutcomesNode is trying to write a str with illegal char")
                print("bodyStr = [" + bodyStr + "]")
                sys.exit(0)

        textStr = "    <OC scope=\"Admit\">"  + bodyStr + "</OC>" + NEWLINE_STR
        self.outputFileH.write(textStr)
    # End - WriteOutcomesNode





    ################################################################################
    # 
    # [TDFFileWriter::WriteDataNode]
    #
    ################################################################################
    def WriteDataNode(self, classStr, timeStampStr, optionStr, valueStr):
        # Search for a bug where time is unordered.
        if (DEBUG_WRITER):
            days, hours, min = TDF_ParseTimeStamp(timeStampStr)
            fFoundBug = False
            if (self.Latest_Value_Day != TDF_INVALID_VALUE):
                if (days < self.Latest_Value_Day):
                    fFoundBug = True
                if ((days == self.Latest_Value_Day) and (hours < self.Latest_Value_Hour)):
                    fFoundBug = True
                if ((days == self.Latest_Value_Day) and (hours == self.Latest_Value_Hour) and (min < self.Latest_Value_Min)):
                    fFoundBug = True
                if (fFoundBug):
                    print("FOUND Time Bug!!!!")
                    print("WriteDataNode. classStr=" + str(classStr))
                    print("valueStr = " + str(valueStr))
                    print("self.Latest_Value_Day = " + str(self.Latest_Value_Day))
                    print("self.Latest_Value_Hour = " + str(self.Latest_Value_Hour))
                    print("self.Latest_Value_Min = " + str(self.Latest_Value_Min))
                    print("days = " + str(days))
                    print("hours = " + str(hours))
                    print("min = " + str(min))
                    sys.exit(0)
                # End - if (fFoundBug):
            # End - if (self.Latest_Value_Day > 0):

            self.Latest_Value_Day = days
            self.Latest_Value_Hour = hours
            self.Latest_Value_Min = min
        # End - if (DEBUG_WRITER)

        xmlStr = "    <D C=\"" + classStr + "\" T=\"" + timeStampStr + "\""

        if ((optionStr is not None) and (optionStr != "")):
            optionStr = optionStr.replace(" ", "")
            xmlStr = xmlStr + " O=\"" + optionStr + "\""

        valueStr = valueStr.replace('=>', '')
        valueStr = valueStr.replace('=<', '')
        valueStr = valueStr.replace('>=', '')
        valueStr = valueStr.replace('<=', '')
        valueStr = valueStr.replace('>', '')
        valueStr = valueStr.replace('<', '')
        valueStr = valueStr.replace("+", "")
        valueStr = valueStr.replace("-", "")
        valueStr = valueStr.replace(" ", "")

        if (DEBUG_WRITER):
            if ((">" in valueStr) or ("<" in valueStr)):
                print("ERROR!!!!! WriteDataNode is trying to write a str with illegal char")
                print("valueStr = [" + valueStr + "]")
                sys.exit(0)

        xmlStr = xmlStr + ">" + valueStr + "</D>" + NEWLINE_STR
        self.outputFileH.write(xmlStr)
    # End - WriteDataNode



    ################################################################################
    # 
    # [TDFFileWriter::WriteEventNode]
    #
    ################################################################################
    def WriteEventNode(self, eventType, timeStampStr, calendarTimeStr, stopTimeStr, valueStr, detailStr):
        # Search for a bug where time is unordered.
        if (DEBUG_WRITER):
            days, hours, min = TDF_ParseTimeStamp(timeStampStr)
            fFoundBug = False
            if (self.Latest_Value_Day != TDF_INVALID_VALUE):
                if (days < self.Latest_Value_Day):
                    fFoundBug = True
                if ((days == self.Latest_Value_Day) and (hours < self.Latest_Value_Hour)):
                    fFoundBug = True
                if ((days == self.Latest_Value_Day) and (hours == self.Latest_Value_Hour) and (min < self.Latest_Value_Min)):
                    fFoundBug = True
                if (fFoundBug):
                    print("FOUND Time Bug!!!!")
                    print("WriteEventNode. eventType=" + str(eventType))
                    print("valueStr = " + str(valueStr))
                    print("detailStr = " + str(detailStr))
                    print("self.Latest_Value_Day = " + str(self.Latest_Value_Day))
                    print("self.Latest_Value_Hour = " + str(self.Latest_Value_Hour))
                    print("self.Latest_Value_Min = " + str(self.Latest_Value_Min))
                    print("days = " + str(days))
                    print("hours = " + str(hours))
                    print("min = " + str(min))
                    sys.exit(0)
                # End - if (fFoundBug):
            # End - if (self.Latest_Value_Day > 0):

            self.Latest_Value_Day = days
            self.Latest_Value_Hour = hours
            self.Latest_Value_Min = min
        # End - if (DEBUG_WRITER)


        xmlStr = "    <E C=\"" + eventType + "\" T=\"" + timeStampStr + "\""

        if ((calendarTimeStr is not None) and (calendarTimeStr != "")):
            # Remove characters that would create an invalid XML file.
            calendarTimeStr = calendarTimeStr.replace('>', '') 
            calendarTimeStr = calendarTimeStr.replace('<', '') 
            calendarTimeStr = calendarTimeStr.replace("=>", "")
            xmlStr = xmlStr + " CT=\"" + calendarTimeStr + "\""

        if ((stopTimeStr is not None) and (stopTimeStr != "")):
            xmlStr = xmlStr + "ST=\"" + timeStampStr + "\""

        if ((valueStr is not None) and (valueStr != "")):
            # Remove characters that would create an invalid XML file.
            valueStr = valueStr.replace('=>', '')
            valueStr = valueStr.replace('=<', '')
            valueStr = valueStr.replace('>=', '')
            valueStr = valueStr.replace('<=', '')
            valueStr = valueStr.replace('>', '')
            valueStr = valueStr.replace('<', '')
            valueStr = valueStr.replace("+", "")
            valueStr = valueStr.replace("-", "")
            valueStr = valueStr.replace(" ", "")

            if (DEBUG_WRITER):
                if ((">" in valueStr) or ("<" in valueStr)):
                    print("ERROR!!!!! WriteEventNode is trying to write a str with illegal char")
                    print("valueStr = [" + valueStr + "]")
                    sys.exit(0)

            xmlStr = xmlStr + " V=\"" + valueStr + "\""

        if ((detailStr is not None) and (detailStr != "")):
            # Remove characters that would create an invalid XML file.
            detailStr = detailStr.replace('=>', '')
            detailStr = detailStr.replace('=<', '')
            detailStr = detailStr.replace('>=', '')
            detailStr = detailStr.replace('<=', '')
            detailStr = detailStr.replace('>', '')
            detailStr = detailStr.replace('<', '')
            detailStr = detailStr.replace("+", "")
            detailStr = detailStr.replace("-", "")
            detailStr = detailStr.replace(" ", "")

            if (DEBUG_WRITER):
                if ((">" in detailStr) or ("<" in detailStr)):
                    print("ERROR!!!!! WriteEventNode is trying to write a str with illegal char")
                    print("detailStr = [" + detailStr + "]")
                    sys.exit(0)

            xmlStr = xmlStr + " D=\"" + detailStr + "\""

        xmlStr = xmlStr + " />" + NEWLINE_STR

        self.outputFileH.write(xmlStr)
    # End - WriteEventNode




    ################################################################################
    # 
    # [TDFFileWriter::WriteTextNode]
    #
    ################################################################################
    def WriteTextNode(self, textType, extraAttributeName, extraAttributeValue, textStr):
        # Remove characters that would create an invalid XML file.
        textStr = textStr.replace('>', '') 
        textStr = textStr.replace('<', '') 
        textStr = textStr.replace("=<", "")
        textStr = textStr.replace("=", "")
        textStr = textStr.replace("=>", "")

        xmlStr = "    <Text C=\"" + textType + "\""
        if ((extraAttributeName != "") and (extraAttributeValue != "")):
            xmlStr = xmlStr + " " + extraAttributeName + "=\"" + extraAttributeValue + "\""
        xmlStr = xmlStr + ">"

        if (DEBUG_WRITER):
            if ((">" in textStr) or ("<" in textStr)):
                print("ERROR!!!!! WriteTextNode is trying to write a str with illegal char")
                print("textStr = [" + textStr + "]")
                sys.exit(0)

        xmlStr = xmlStr + textStr + "</Text>" + NEWLINE_STR

        self.outputFileH.write(xmlStr)
    # End - WriteTextNode




    ################################################################################
    # 
    # [TDFFileWriter::AppendNameValuePairToStr]
    #
    ################################################################################
    def AppendNameValuePairToStr(self, totalStr, name, valueStr):
        if ((name is None) or (valueStr is None)):
            print("Error. AppendNameValuePairToStr discarding NONE name or value str")
            return(totalStr)

        #name = name.lstrip()
        #valueStr = valueStr.lstrip()
        # Remove characters that would create an invalid XML file.
        valueStr = valueStr.replace('=>', '')
        valueStr = valueStr.replace('=<', '')
        valueStr = valueStr.replace('>=', '')
        valueStr = valueStr.replace('<=', '')
        valueStr = valueStr.replace('>', '')
        valueStr = valueStr.replace('<', '')

        if (name == ""):
            print("Error. AppendNameValuePairToStr discarding empty name str")
            return(totalStr)    

        if (valueStr == ""):
            print("Error. AppendNameValuePairToStr discarding empty value str")
            return(totalStr)    

        try:
            # Lint gets upset that I do not use this, but I am only doing it to check the conversion works.
            dummyFloatVal = float(valueStr)
        except Exception:
            print("Error. AppendNameValuePairToStr discarding non-numeric valueStr: " + str(valueStr))
            return(totalStr)    

        totalStr = totalStr + name + "=" + valueStr + ","

        if (DEBUG_WRITER):
            if ((">" in totalStr) or ("<" in totalStr)):
                print("ERROR!!!!! AppendNameValuePairToStr is trying to write a str with illegal char")
                print("totalStr = [" + totalStr + "]")
                sys.exit(0)

        return(totalStr)
    # End - AppendNameValuePairToStr

# End - class TDFFileWriter




################################################################################
# 
# [TDFFileWriter_AppendMedInfoToStr]
#
# This builds up a comma-separated list of values, each has the form:
#       medName:dose:route:doseRoute:dosesPerDayStr
#
# Dose is a string of a float (like 12.5)
# The dose Units is implied by the drug. For example, most PO meds are mg, 
# while insulin is Units, creams are applications, inhaleds are puffs, etc.
#
# doseRoute is "i", "o", 't', ...
# The route matters, for example, Lasix IV is approx 2x lasix PO.
################################################################################
def TDFFileWriter_AppendMedInfoToStr(totalStr, drugName, doseStr, doseRoute, dosesPerDayStr):
    if ((drugName is None) or (drugName == "") or (totalStr is None)):
        print("Error. TDFFileWriter_AppendMedInfoToStr discarding NONE name or value str")
        return(totalStr)

    try:
        # Lint gets upset that I do not use this, but I am only doing it to check the conversion works.
        dummyFloatVal = float(doseStr)
    except Exception:
        print("Error. TDFFileWriter_AppendMedInfoToStr discarding non-numeric doseStr: " + str(doseStr))
        return(totalStr)

    if (doseRoute == ""):
        doseRoute = "o"
    if (dosesPerDayStr == ""):
        dosesPerDayStr = "0"


    if (dosesPerDayStr != ""):
        try:
            # Lint gets upset that I do not use this, but I am only doing it to check the conversion works.
            dummyDosesPerDayInt = float(dosesPerDayStr)
        except Exception:
            print("Error. TDFFileWriter_AppendMedInfoToStr discarding non-numeric dosesPerDayStr: " + str(dosesPerDayStr))
            return(totalStr)    
    # End - if (dosesPerDayStr != ""):
    if (dosesPerDayStr == ""):
        dosesPerDayStr = "1"


    totalStr = totalStr + drugName + ":" + doseStr + ":" + doseRoute + ":" + dosesPerDayStr + ","
    return(totalStr)
# End - TDFFileWriter_AppendMedInfoToStr



################################################################################
# 
# [TDFFileWriter_AppendProcInfoToStr]
#
# This builds up a comma-separated list of values, each has the form:
#       procSubType:cptCode
#
# procType is a string: Proc or Surg
# procSubType is a string: EGD, ERCP, Colonoscopy, or Major/Endo
# 
################################################################################
def TDFFileWriter_AppendProcInfoToStr(totalStr, procSubType, cptCode):
    if ((procSubType is None) or (procSubType == "") or (totalStr is None)):
        print("Error. TDFFileWriter_AppendProcInfoToStr discarding NONE name or value str")
        return(totalStr)

    totalStr = totalStr + procSubType + ":" + cptCode + ","
    return(totalStr)
# End - TDFFileWriter_AppendProcInfoToStr









################################################################################
#
# This is used to read a TDF file. It is read-only, and is designed to be called
# by a Neural Net or similar program.
################################################################################
class TDFFileReader():
    #####################################################
    #
    # [TDFFileReader::__init__]
    #
    #####################################################
    def __init__(self, tdfFilePathName, inputNameListStr, resultValueName, requirePropertyNameList):
        #print("TDFFileReader.__init__. Pathname = " + tdfFilePathName)
        #print("TDFFileReader.__init__. inputNameListStr = " + inputNameListStr + ", resultValueName = " + resultValueName)

        super(TDFFileReader, self).__init__()

        # Save the parameters
        self.tdfFilePathName = tdfFilePathName
        self.MinutesPerTimelineEntry = 60 * 24   # 1 bucket per day
        self.fileHandle = None
        self.DebugMode = False

        # Initialize some parsing control options to their default values.
        # These may be overridden later.
        self.fCarryForwardPreviousDataValues = True

        ###################
        self.ParseVariableList(inputNameListStr, resultValueName, 
                               requirePropertyNameList)

        ###################
        # Open the file.
        # Opening in binary mode is important. I do seek's to arbitrary positions
        # and that is only allowed when a file is opened in binary.
        try:
            self.fileHandle = open(self.tdfFilePathName, 'rb') 
        except Exception:
            TDF_Log("Error from opening TDF file. File=" + self.tdfFilePathName)
            return
        self.lineNum = 0

        ####################
        # Read the file header as a series of text lines and create a single
        # large text string for just the header. Stop at the body, which may
        # be quite large, and may not fit in in memory all at once.
        self.fileHeaderStr = ""        
        while True: 
            # Get next line from file 
            try:
                binaryLine = self.fileHandle.readline() 
            except UnicodeDecodeError as err:
                print("Unicode Error from reading Lab file. lineNum=" + str(self.lineNum) + ", err=" + str(err))
                continue
            except Exception:
                print("Error from reading Lab file. lineNum=" + str(self.lineNum))
                continue
            self.lineNum += 1

            # Convert the text from Unicode to ASCII. 
            try:
                currentLine = binaryLine.decode("ascii", "ignore")
            except UnicodeDecodeError as err:
                print("Unicode Error from converting string. lineNum=" + str(self.lineNum) + ", err=" + str(err))
                continue
            except Exception:
                print("Error from converting string. lineNum=" + str(self.lineNum))
                continue

            self.fileHeaderStr += currentLine

            # Remove whitespace, including the trailing newline.
            currentLine = currentLine.rstrip()
            currentLine = currentLine.lstrip()
            if (currentLine == "</Head>"):
                break
        # End - Read the file header

        # Add a closing element to make the header string into a complete XML string, 
        # and then we can parse it into XML
        self.fileHeaderStr += "</TDF>"
        #print("__init__. Header str=" + self.fileHeaderStr)
        self.headerXMLDOM = dxml.XMLTools_ParseStringToDOM(self.fileHeaderStr)
        if (self.headerXMLDOM is None):
            TDF_Log("TDFFileReader::__init__. Error from parsing string:")

        self.headerNode = dxml.XMLTools_GetNamedElementInDocument(self.headerXMLDOM, "Head")
        if (self.headerNode is None):
            print("TDFReader.__init__. Head elements is missing: [" + self.fileHeaderStr + "]")
            return

        # Initalize the iterator to start at the beginning.
        self.currentPatientNodeStr = ""
        self.LastTimeLineIndex = TDF_INVALID_VALUE
    # End -  __init__



    #####################################################
    #
    # [TDFFileReader::__del__]
    #
    # Destructor. This method is part of any class
    #####################################################
    def __del__(self):
        self.Shutdown()
    # End of destructor




    #####################################################
    #
    # [TDFFileReader::Shutdown]
    #
    # Called to explicitly release resources
    #####################################################
    def Shutdown(self):
        if (self.fileHandle is not None):
            try:
                self.fileHandle.close()
            except Exception:
                pass
        self.fileHandle = None
    # End of Shutdown


    #####################################################
    # [TDFFileReader::SetTimeResolution]
    #####################################################
    def SetTimeResolution(self, minutesPerTimelineEntry):
        self.MinutesPerTimelineEntry = minutesPerTimelineEntry


    #####################################################
    # [TDFFileReader::SetCarryForwardPreviousDataValues]
    #####################################################
    def SetCarryForwardPreviousDataValues(self, fEnabled):
        self.fCarryForwardPreviousDataValues = fEnabled


    #####################################################
    # [TDFFileReader::SetDebugMode]
    #####################################################
    def SetDebugMode(self, fOption):
        self.DebugMode = fOption



    #####################################################
    #
    # [TDFFileReader::ParseVariableList]
    #
    #####################################################
    def ParseVariableList(self, inputNameListStr, resultValueName, requirePropertyNameList):
        fDebug = False
        if (fDebug):
            print("TDFFileReader::ParseVariableList. inputNameListStr=" + str(inputNameListStr))
            print("TDFFileReader::ParseVariableList. resultValueName=" + str(resultValueName))
            print("TDFFileReader::ParseVariableList. requirePropertyNameList=" + str(requirePropertyNameList))

        # Get information about the requested variables. Each variable may be a simple value, 
        # like "Cr", or a value at an offset, like "Cr[-1]" or a function like Cr.rate
        # Note, one name may appear several times in the list, but have different functions
        # or offsets. 
        self.allValueVarNameList = inputNameListStr.split(VARIABLE_LIST_SEPARATOR)

        # Before we expand the list, count how many vars we return to teh client.
        self.numInputValues = len(self.allValueVarNameList)

        # Get information about the result. However, this is optional
        if ((resultValueName is not None) and (resultValueName != "")):
            self.resultLabInfo, self.resultValueName, self.resultValueOffset, resultFunctionName = TDF_ParseOneVariableName(resultValueName)
            if (self.resultLabInfo is None):
                TDF_Log("ERROR TDFFileReader::ParseVariableList Undefined resultValueName: " + resultValueName)
                sys.exit(0)
            self.resultDataType = self.resultLabInfo['dataType']
        else:
            self.resultValueName = ""
            self.resultLabInfo = None
            self.resultValueOffset = 0
            self.resultDataType = TDF_DATA_TYPE_INT

        # Add any other variables we will use. This will include params for start/stop and criteria
        # The list starts with the valiables used for inputs. So, the contents of the total array
        # will look like this:
        # ------------------------------------------------------
        # | Inputs | Outputs | Filtering Values | Dependencies |
        # ------------------------------------------------------
        if (self.resultValueName != ""):
            self.allValueVarNameList.append(self.resultValueName)
        if (requirePropertyNameList is not None):
            for nameIndex, nameStr in enumerate(requirePropertyNameList):
                self.allValueVarNameList.append(nameStr)

        # Parse the initial list of variables needed.
        # This may not be all; once we closely look at the variables, we may
        # realize we need more variables to compute derived values.
        numVarsInFullNameList = len(self.allValueVarNameList)
        self.allValuesLabInfoList = [None] * numVarsInFullNameList
        self.allValueOffsets = [0] * numVarsInFullNameList
        self.allValuesFunctionNameList = [""] * numVarsInFullNameList
        self.allValuesFunctionObjectList = [None] * numVarsInFullNameList
        # Each iteration parses a single variable.
        for valueIndex, valueName in enumerate(self.allValueVarNameList):
            labInfo, valueName, valueOffset, functionName = TDF_ParseOneVariableName(valueName)
            self.allValueVarNameList[valueIndex] = valueName
            self.allValuesLabInfoList[valueIndex] = labInfo
            self.allValueOffsets[valueIndex] = valueOffset
            self.allValuesFunctionNameList[valueIndex] = functionName

            if (fDebug):
                print("TDFFileReader::ParseVariableList. valueNameStem=" + str(valueName))
                print("TDFFileReader::ParseVariableList. labInfo=" + str(labInfo))
                print("TDFFileReader::ParseVariableList. valueOffset=" + str(valueOffset))
                print("TDFFileReader::ParseVariableList. functionName=" + str(functionName))
        # End - for valueIndex, valueName in enumerate(inputValueNameList):


        # Use the variable name stem (found by parsing the full variable names) 
        # and look these up in the dictionary to pull in all dependencies.
        # This will also look up dependency variables in the dictionary.
        #
        # I use an old-fashioned C-style loop here because I am iterating through the
        # array as I am also growing the array. So, the stop index may be different for each 
        # loop iteration.
        index = 0
        while (True):
            if (index >= len(self.allValueVarNameList)):
                break

            valueName = self.allValueVarNameList[index]
            labInfo = self.allValuesLabInfoList[index]
            # If some dependency variables were added to the list on a previous iteration, then 
            # we may need to  parse them now.
            if (labInfo is None):
                TDF_Log("\n\n\nERROR!! TDFFileReader::ParseVariableList Did not have a parsed variable for [" + valueName + "]")
                print("self.allValueVarNameList = " + str(self.allValueVarNameList))
                sys.exit(0)
            # End - if (labInfo == None)

            if (self.allValuesFunctionNameList[index] != ""):
                self.allValuesFunctionObjectList[index] = timefunc.CreateTimeValueFunction(
                                                                        self.allValuesFunctionNameList[index],
                                                                        self.allValueVarNameList[index])
                if (self.allValuesFunctionObjectList[index] is None):
                    print("\n\n\nERROR!! TDFFileReader::ParseVariableList Undefined function: " 
                            + self.allValuesFunctionNameList[index])
                    sys.exit(0)
            # End - if (self.allValuesFunctionNameList[index] != ""):

            # Now, grow the list of input variables by pulling in any dependencies.
            # The user may request a derived variable, which means we have to also collect any 
            # dependencies that are used to derive that variable.
            variableNameListStr = labInfo['VariableDependencies']
            if (variableNameListStr != ""):
                variableNameList = variableNameListStr.split(";")
                if (variableNameList is not None):
                    for nameIndex, nameStr in enumerate(variableNameList):
                        labInfo, valueName, valueOffset, functionName = TDF_ParseOneVariableName(nameStr)

                        # This is a bit subtle.
                        # The names in the list will be pulled in whenever they are available.
                        # It does not matter if the original variable name specified an offset like Cr[-3]
                        # So, for example, even if Cr is in the list as part of Cr[-3], a new Cr dependency
                        # does NOT need to be added. The original Cr, even with the offset, will cause the
                        # code that compiles a timeline to store every instance of a Cr in the file.
                        # So, avoid unnecessary duplicate names.
                        #
                        # HOWEVER! input variables specified by the user may include functions. We need
                        # a different function state, so if we have 2 input variables that are different
                        # functions applied to the same value (like "Cr.rate" and Cr.accel") then we need
                        # separate entries, with duplicated base variable.
                        if ((valueName != "") and (valueName not in self.allValueVarNameList)):
                            self.allValueVarNameList.append(valueName)
                            self.allValuesLabInfoList.append(labInfo)
                            self.allValueOffsets.append(valueOffset)
                            self.allValuesFunctionNameList.append(functionName)
                            self.allValuesFunctionObjectList.append(None)
                    # End - for nameIndex, nameStr in enumerate(variableNameList):
                # End - if (variableNameList is not None):
            # End - if (variableNameListStr != ""):

            index += 1
        # End - while (True):


        self.allValueVarNameList.append("StartCKD5Date")
        self.allValueVarNameList.append("StartCKD4Date")

        if (fDebug):
            print("TDFFileReader::ParseVariableList. self.numInputValues=" + str(self.numInputValues))
            print("TDFFileReader::ParseVariableList. self.allValueVarNameList=" + str(self.allValueVarNameList))
            print("TDFFileReader::ParseVariableList. self.allValueOffsets=" + str(self.allValueOffsets))
            print("TDFFileReader::ParseVariableList. self.allValuesFunctionNameList=" + str(self.allValuesFunctionNameList))
            print("TDFFileReader::ParseVariableList. self.allValuesFunctionObjectList=" + str(self.allValuesFunctionObjectList))
            print("TDFFileReader::ParseVariableList. self.allValuesLabInfoList=" + str(self.allValuesLabInfoList))
    # End -  ParseVariableList




    #####################################################
    #
    # [TDFFileReader::GetRawXMLStrForHeader]
    #
    # This is used by the TDF writer class when making
    # a derived TDF file from an original source.
    #####################################################
    def GetRawXMLStrForHeader(self):
        resultStr = self.fileHeaderStr

        # Remove the </TDF> we added to make it parseable.
        resultStr = resultStr[:-6]
        # Add the PatientList element.
        resultStr = resultStr + "<PatientList>"

        return(resultStr)
    # End of GetRawXMLStrForHeader



    #####################################################
    #
    # [TDFFileReader::GetRawXMLStrForFooter]
    #
    # This is used by the TDF writer class when making
    # a derived TDF file from an original source.
    #####################################################
    def GetRawXMLStrForFooter(self):
        footerStr = "\n\n</PatientList>\n</TDF>\n\n"
        return(footerStr)
    # End of GetRawXMLStrForFooter



    #####################################################
    #
    # [TDFFileReader::GetRawXMLStrForFirstPatient]
    #
    # Returns a string for the XML of the first patient.
    # This is used by the TDF writer class when making
    # a derived TDF file from an original source.
    #####################################################
    def GetRawXMLStrForFirstPatient(self):
        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.GotoFirstPatientEx()
        if (not fFoundPatient):
            return("")

        return self.currentPatientNodeStr
    # End - GetRawXMLStrForFirstPatient(self)



    #####################################################
    #
    # [TDFFileReader::GetRawXMLStrForNextPatient]
    #
    # Returns a string for the XML of the next patient.
    # This is used by the TDF writer class when making
    # a derived TDF file from an original source.
    #####################################################
    def GetRawXMLStrForNextPatient(self):
        #TDF_Log("GetRawXMLStrForNextPatient")
        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.ReadNextPatientXMLStrImpl(TDF_INVALID_VALUE)
        if ((not fFoundPatient) or (fEOF)):
            return(None)

        # We parse so the reader will also be able to examine properties in the patient.
        # This lets us split a large file by properties
        fFoundPatient = self.ParseCurrentPatientImpl()
        if ((not fFoundPatient) or (fEOF)):
            return(None)

        return self.currentPatientNodeStr
    # End - GetRawXMLStrForNextPatient(self)



    #####################################################
    # [TDFFileReader::GetXMLNodeForCurrentPatient]
    #####################################################
    def GetXMLNodeForCurrentPatient(self):
        return self.currentPatientNode
    # End - GetXMLNodeForCurrentPatient(self)



    #####################################################
    #
    # [TDFFileReader::GetFileDescriptionStr]
    # valueName may be any property in the header.
    #####################################################
    def GetFileDescriptionStr(self, valueName):
        xmlStr = dxml.XMLTools_GetChildNodeTextAsStr(self.headerNode, valueName, "")
        return(xmlStr)
    # End of GetFileDescriptionStr




    #####################################################
    #
    # [TDFFileReader::GotoFirstPatient]
    #
    # Returns a single boolean fFoundPatient
    #   This is True iff the procedure found a valid patient entry.
    #   This is False if it hit the end of the file
    #####################################################
    def GotoFirstPatient(self):
        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.GotoFirstPatientEx()
        return(fFoundPatient)
    # End - GotoFirstPatient




    #####################################################
    #
    # [TDFFileReader::GotoFirstPatientEx]
    #
    # This returns more information than GotoFirstPatient
    #
    # Returns a single boolean fFoundPatient
    #   This is True iff the procedure found a valid patient entry.
    #   This is False if it hit the end of the file
    #####################################################
    def GotoFirstPatientEx(self):
        self.fileHandle.seek(0, 0)

        # Advance in the file to the start of the patient list
        while True: 
            # Get next line from file 
            try:
                binaryLine = self.fileHandle.readline() 
            except UnicodeDecodeError as err:
                print("Unicode Error from reading Lab file. lineNum=" + str(self.lineNum) + ", err=" + str(err))
                continue
            except Exception:
                print("Error from reading Lab file. lineNum=" + str(self.lineNum))
                continue
            self.lineNum += 1

            # Convert the text from Unicode to ASCII. 
            try:
                currentLine = binaryLine.decode("ascii", "ignore")
            except UnicodeDecodeError as err:
                print("Unicode Error from converting string. lineNum=" + str(self.lineNum) + ", err=" + str(err))
                continue
            except Exception:
                print("Error from converting string. lineNum=" + str(self.lineNum))
                continue

            # If we hit the end of the file, then we did not find a next patient.
            if (currentLine == ""):
                return False, False, TDF_INVALID_VALUE, TDF_INVALID_VALUE

            # Remove whitespace, including the trailing newline.
            currentLine = currentLine.rstrip()
            currentLine = currentLine.lstrip()
            #TDF_Log("GotoFirstPatientEx. currentLine=" + currentLine)
            if (currentLine == "<PatientList>"):
                break
        # End - Advance to the first patient

        # Now, go to the first patient
        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.GotoNextPatientEx()
        return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile
    # End - GotoFirstPatientEx




    #####################################################
    #
    # [TDFFileReader::GotoNextPatient]
    #
    # Returns a single boolean fFoundPatient
    #   This is True iff the procedure found a valid patient entry.
    #   This is False if it hit the end of the file
    #####################################################
    def GotoNextPatient(self):
        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.GotoNextPatientEx()
        return fFoundPatient
    # End - GotoNextPatient(self)




    #####################################################
    #
    # [TDFFileReader::GotoNextPatientEx]
    # This returns more information than GotoNextPatient
    #####################################################
    def GotoNextPatientEx(self):
        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.ReadNextPatientXMLStrImpl(TDF_INVALID_VALUE)
        if ((not fFoundPatient) or (fEOF)):
            return False, False, 0, 0

        fFoundPatient = self.ParseCurrentPatientImpl()

        return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile
    # End - GotoNextPatientEx(self)





    #####################################################
    #
    # [TDFFileReader::ReadPatientAtKnownPosition]
    #
    #####################################################
    def ReadPatientAtKnownPosition(self, startPatientPosInFile, stopPatientPosInFile):
        patientLength = stopPatientPosInFile - startPatientPosInFile
        self.currentPatientNodeStr = ""

        try:
            self.fileHandle.seek(startPatientPosInFile, 0)
            dataBytes = self.fileHandle.read(patientLength)
        except Exception:
            return False

        # Convert the text from Unicode to ASCII. 
        try:
            myStr = dataBytes.decode("ascii", "ignore")
        except UnicodeDecodeError:
            return False
        except Exception:
            return False

        self.currentPatientNodeStr = myStr
        FoundPatient = self.ParseCurrentPatientImpl()
        if (not FoundPatient):
            print("ReadPatientAtKnownPosition. Error!. Read data = [" + myStr + "] FoundPatient = " + str(FoundPatient))
            print("\n\nReadPatientAtKnownPosition. BAIL\n\n")
            sys.exit(0)

        return FoundPatient
    # End - ReadPatientAtKnownPosition




    #####################################################
    #
    # [TDFFileReader::GotoFirstPatientInPartition]
    #
    # This returns two values: fFoundPatient, fEOF
    #   fFoundPatient - True if we read a complete patient
    #   fEOF - True if we hit the end of the file
    #
    # This will find the next patient that starts within the
    # current partition. The selected patient may extend beyond
    # the end of the partition, which is OK. 
    #####################################################
    def GotoFirstPatientInPartition(self, startPatientPosInFile, stopPatientPosInFile, startPartition, stopPartition):
        #TDF_Log("GotoFirstPatientInPartition. startPartition=" + str(startPartition) + 
        #            ", stopPartition=" + str(stopPartition))
        fFoundPatient = False
        fEOF = False

        # If we already know the positoin of the patient, then just read
        # it. We don't need to find it.
        if ((startPatientPosInFile > 0) and (stopPatientPosInFile > 0)):
            fFoundPatient = self.ReadPatientAtKnownPosition(startPatientPosInFile, stopPatientPosInFile)
            return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile

        # Otherwise, we are looking for the patient in the file.
        # If this is the beginning of the file, then skip over the header.
        if (startPartition == 0):
            fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.GotoFirstPatientEx()
            if (not fFoundPatient):
                fEOF = True
            return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile

        # Otherwise, jump to the partition starting position. 
        # Note, the partition boundaries are arbitrary byte positions, so
        # this may jump to the middle of a line of text. That is OK, since
        # we will still advance until we see a valid start of a patient element.
        self.fileHandle.seek(startPartition, 0)

        # Now, go to the first patient
        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.GotoNextPatientInPartition(TDF_INVALID_VALUE, 
                                                                                                    TDF_INVALID_VALUE, stopPartition)
        #TDF_Log("GotoFirstPatientInPartition. fFoundPatient=" + str(fFoundPatient))

        return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile
    # End - GotoFirstPatientInPartition






    #####################################################
    #
    # [TDFFileReader::GotoNextPatientInPartition]
    #
    # This returns two values: fFoundPatient, fEOF
    #   fFoundPatient - True if we read a complete patient
    #   fEOF - True if we hit the end of the file
    #
    # This will find the next patient that starts within the
    # current partition. The selected patient may extend beyond
    # the end of the partition, which is OK. 
    #####################################################
    def GotoNextPatientInPartition(self, startPatientPosInFile, stopPatientPosInFile, stopPartition):
        # If we already know the positoin of the patient, then just read
        # it. We don't need to find it.
        if ((startPatientPosInFile > 0) and (stopPatientPosInFile > 0)):
            fEOF = False
            fFoundPatient = self.ReadPatientAtKnownPosition(startPatientPosInFile, stopPatientPosInFile)
            return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile

        fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile = self.ReadNextPatientXMLStrImpl(stopPartition)
        if ((not fFoundPatient) or (fEOF)):
            return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile

        fFoundPatient = self.ParseCurrentPatientImpl()

        return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile
    # End - GotoNextPatientInPartition(self)





    #####################################################
    #
    # [TDFFileReader::ReadNextPatientXMLStrImpl]
    #
    # This returns four values:
    #   fFoundPatient - True if we read a complete patient
    #   fEOF - True if we hit the end of the file
    #   startPatientPosInFile - Where valid patient data actually started
    #   stopPatientPosInFile - Where valid patient data actually stopped
    #
    # It is OK to start a patient before the end of the partition and 
    # then read it past the end. So, we may read a patient that 
    # stretches past the end of the partition. But, it is NOT OK
    # to start a patient after the end of the partition.
    #####################################################
    def ReadNextPatientXMLStrImpl(self, stopPartition):
        #print("ReadNextPatientXMLStrImpl. stopPartition=" + str(stopPartition))
        fFoundPatient = False
        fEOF = False
        startPatientPosInFile = TDF_INVALID_VALUE
        stopPatientPosInFile = TDF_INVALID_VALUE

        ####################
        # Read the next patient node as a text string
        # 1. This ASSUMES we are about to read the <Patient> opening tag for the next patient.
        #     We start just before the first patient when opening a file.
        #     We stop just before the next patient when we read one patient.
        self.currentPatientNodeStr = ""
        fStartedPatientSection = False
        while True: 
            currentLinePositon = self.fileHandle.tell()

            # Check if we have run past the end of the partition
            # It is OK to start a patient before the end of the partition and then read it past the end
            # if possible (we read a little extra data at the end to allow for this).
            # But, it is NOT OK to start a patient after the end of the partition.
            if ((currentLinePositon >= stopPartition) and (stopPartition > 0) and (not fStartedPatientSection)):
                break

            # Get next line from file 
            try:
                binaryLine = self.fileHandle.readline() 
            except UnicodeDecodeError as err:
                print("Unicode Error from reading TDF file. lineNum=" + str(self.lineNum) + ", err=" + str(err))
                continue
            except Exception:
                print("Error from reading Lab file. lineNum=" + str(self.lineNum))
                continue
            self.lineNum += 1

            # Convert the text from Unicode to ASCII. 
            try:
                currentLine = binaryLine.decode("ascii", "ignore")
            except UnicodeDecodeError as err:
                print("Unicode Error from converting string. lineNum=" + str(self.lineNum) + ", err=" + str(err))
                continue
            except Exception:
                print("Error from converting string. lineNum=" + str(self.lineNum))
                continue

            # If we hit the end of the file, then we did not find a next patient.
            if (currentLine == ""):
                fEOF = True
                break

            # Before we decide to save the line, remove whitespace for comparisons.
            # Gotcha 1: Do this to a temp copy, but save the original line with the whitespace
            # Gotcha 2: Do this before we decide we are in the patient. Don't save text before the patient starts.
            #print("ReadNextPatientXMLStrImpl. currentLine=" + currentLine)
            lineTokenText = currentLine.lstrip()
            lineTokenText = lineTokenText.rstrip()
            lineTokenText = lineTokenText.lower()

            # Now, check if this is the start of a patient element
            # Notice the patient element may contain attributes, so don't compare 
            # with "<patient>"
            if ((not fStartedPatientSection) and (lineTokenText.startswith("<patient"))):
                fStartedPatientSection = True
                startPatientPosInFile = currentLinePositon
                #print("ReadNextPatientXMLStrImpl. Found start of patient. startPatientPosInFile=" + str(startPatientPosInFile))

            if (fStartedPatientSection):
                currentLine = currentLine.replace("=<", "")
                self.currentPatientNodeStr += currentLine
            # End - if (fStartedPatientSection):

            # Stop when we have read the entire patient.
            # Do not do this if we just hit an end. We may hit the end of one patient that
            # started on a previous buffer before getting to the first patient in the current buffer.
            if ((lineTokenText == "</patient>") and (fStartedPatientSection)):
                # If we found both the start and end of a patient, then we founf thew whole patient.
                fFoundPatient = True
                stopPatientPosInFile = self.fileHandle.tell()
                break
        # End - Read the file header

        #print("ReadNextPatientXMLStrImpl. currentLinePositon=" + str(currentLinePositon))
        #print("ReadNextPatientXMLStrImpl. Done. startPatientPosInFile=" + str(startPatientPosInFile))
        return fFoundPatient, fEOF, startPatientPosInFile, stopPatientPosInFile
    # End - ReadNextPatientXMLStrImpl(self)





    #####################################################
    #
    # [TDFFileReader::FindAllPatientsInPartition]
    #
    # This returns two values: fFoundPatient, fEOF
    #   fFoundPatient - True if we read a complete patient
    #   fEOF - True if we hit the end of the file
    #####################################################
    def FindAllPatientsInPartition(self, startPartition, stopPartition):
        #TDF_Log("FindAllPatientsInPartition. startPartition=" + str(startPartition) + 
        #            ", stopPartition=" + str(stopPartition))
        fEOF = False
        fFoundOpenElement = False
        currentOpenElementPosition = TDF_INVALID_VALUE
        currentCloseElementPosition = TDF_INVALID_VALUE
        openElement = re.compile('<patient', re.IGNORECASE)
        closeElement = re.compile('</patient>', re.IGNORECASE)
        resultPatientPositionLists = []

        # Jump to the partition starting position. 
        # Note, the partition boundaries are arbitrary byte positions, so
        # this may jump to the middle of a line of text. That is OK, since
        # we will still advance until we see a valid start of a patient element.
        self.fileHandle.seek(startPartition, 0)

        # Advance in the file to the start of each patient
        while True: 
            currentLinePositonInFile = self.fileHandle.tell()
            # Check if we have run past the end of the partition
            # It is OK to start a patient before the end of the partition and then read it past the end.
            # But, it is NOT OK to start a patient after the end of the partition.
            if ((stopPartition > 0) and (not fFoundOpenElement) and (currentLinePositonInFile >= stopPartition)):
                break

            # Get next line from file 
            try:
                binaryLine = self.fileHandle.readline() 
            except UnicodeDecodeError as err:
                print("Unicode Error from reading Lab file. lineNum=" + str(self.lineNum))
                print("err=" + str(err))
                continue
            except Exception:
                print("Error from reading Lab file. lineNum=" + str(self.lineNum))
                continue
            self.lineNum += 1

            # Convert the text from Unicode to ASCII. 
            try:
                currentLine = binaryLine.decode("ascii", "ignore")
            except UnicodeDecodeError as err:
                print("Unicode Error from converting string. lineNum=" + str(self.lineNum))
                print("err=" + str(err))
                continue
            except Exception:
                print("Error from converting string. lineNum=" + str(self.lineNum))
                continue

            # If we hit the end of the file, then we did not find a next patient.
            if (currentLine == ""):
                fEOF = True
                break

            # Scan through a string, looking for any location where this RE matches.
            # If we haven't found an open element, then we are looking for one
            # If we found an open element, then we are looking for the next close.
            if (fFoundOpenElement):
                matchResult = closeElement.match(currentLine)
            else:  # if (not fFoundOpenElement)
                matchResult = openElement.match(currentLine)

            if matchResult:
                if (fFoundOpenElement):
                    # If we previously found an open and just now found a close, then we have
                    # the entire element
                    fFoundOpenElement = False
                    currentCloseElementPosition = currentLinePositonInFile + len(currentLine)
                    newDict = {"start": currentOpenElementPosition, "stop": currentCloseElementPosition}
                    resultPatientPositionLists.append(newDict)
                else:  # (not fFoundOpenElement)
                    # If we had not previously found an open and just now found an open, then we are
                    # ready to search for the close
                    fFoundOpenElement = True
                    currentOpenElementPosition = currentLinePositonInFile
            # End - if matchResult

        # End - Advance in the file to the start of each patient

        return resultPatientPositionLists, fEOF
    # End - FindAllPatientsInPartition






    #####################################################
    #
    # [TDFFileReader::ParseCurrentPatientImpl]
    #
    # Returns True/False. 
    #   It returns True if it found a valid patient entry.
    #####################################################
    def ParseCurrentPatientImpl(self):
        #print("ParseCurrentPatientImpl")

        # Parse the text string into am XML DOM
        self.currentPatientXMLDOM = dxml.XMLTools_ParseStringToDOM(self.currentPatientNodeStr)
        if (self.currentPatientXMLDOM is None):
            TDF_Log("ParseCurrentPatientImpl. Error from parsing string:")
            return

        self.currentPatientNode = dxml.XMLTools_GetNamedElementInDocument(self.currentPatientXMLDOM, "Patient")
        if (self.currentPatientNode is None):
            TDF_Log("ParseCurrentPatientImpl. Patient elements is missing: [" + self.currentPatientNodeStr + "]")
            return

        # Get some properties from the patient. These apply to all data entries within this patient.
        genderStr = self.currentPatientNode.getAttribute("gender")
        if (genderStr == "M"):
            self.CurrentIsMale = 1
        else:
            self.CurrentIsMale = 0
        self.CurrentRaceStr = self.currentPatientNode.getAttribute("race")
        #print(">>self.CurrentRaceStr = " + self.CurrentRaceStr)
        if (self.CurrentRaceStr == ""):
            self.CurrentRaceStr = "W"

        self.CurrentWtInKg = TDF_INVALID_VALUE
        wtInKgStr = self.currentPatientNode.getAttribute("wt")
        if ((wtInKgStr) and (wtInKgStr != "")):
            self.CurrentWtInKg = float(wtInKgStr)

        # Generate a timeline of actual and derived data values.
        # This covers the entire patient.
        self.CompilePatientTimelineImpl()

        return True
    # End - ParseCurrentPatientImpl(self)





    #####################################################
    #
    # [TDFFileReader::CompilePatientTimelineImpl]
    #
    # This ASSUMES ParseVariableList() has already run (it's called in the constructor).
    # As a result, these are ALL valid: 
    #       self.allValueVarNameList, self.allValueOffsets, self.allValuesFunctionNameList
    #
    # I have debated whether ForwardPassAccumulator should be a dict or an array.
    # I like the idea of an array, than can just map to the list
    # of requested values once we need to return values. This probably can be performance
    # tunes, and I am influenced by the idea that Google's AKI neural net seems to do that.
    #
    # However, there are a lot of internal values, like DayofDischarge that need to be
    # collected and maintained and are never returned to the client. The number of these
    # may change over time. A dict is more efficient at this, and uses Python's internal
    # implementation, rather than writing something like an enumerator loop to find all 
    # cases of a variable in the list. Moverover, a dict handles the problem of duplicate
    # entries.
    #####################################################
    def CompilePatientTimelineImpl(self):
        fDebug = False

        if (fDebug):
            print("\n\n\nCompilePatientTimelineImpl: Start")

        self.DiagnosisList = []
        self.CompiledTimeline = []

        # At any given time, self.ForwardPassAccumulator has the most recent
        # value for each lab.
        self.ForwardPassAccumulator = {}
        self.latestTimeLineEntryTimeDays = TDF_INVALID_VALUE
        self.latestTimeLineEntryIntervalInDay = TDF_INVALID_VALUE
        self.latestTimeLineEntry = None

        # Initialize the forwardPassAccumulator with the values.
        for nameIndex, nameStr in enumerate(self.allValueVarNameList):
            self.ForwardPassAccumulator[nameStr] = TDF_INVALID_VALUE

        # Initialize the latest labs with a few special values that don't change.
        if ("IsMale" in self.allValueVarNameList):
            self.ForwardPassAccumulator['IsMale'] = int(self.CurrentIsMale)
        if ("WtKg" in self.allValueVarNameList):
            self.ForwardPassAccumulator['WtKg'] = int(self.CurrentWtInKg)
        if ("IsCaucasian" in self.allValueVarNameList):
            if (self.CurrentRaceStr.lower() == "w"):
                self.ForwardPassAccumulator['IsCaucasian'] = 1
            else:
                self.ForwardPassAccumulator['IsCaucasian'] = 0

        # Initially, all outcomes are false for this patient. 
        # This will change as we move forward through the timeline.
        if ("DiedThisAdmission" in self.allValueVarNameList):
            self.ForwardPassAccumulator['DiedThisAdmission'] = 0
        if ("DiedIn12Mos" in self.allValueVarNameList):
            self.ForwardPassAccumulator['DiedIn12Mos'] = 0
        if ("ReadmitIn30Days" in self.allValueVarNameList):
            self.ForwardPassAccumulator['ReadmitIn30Days'] = 0
        if ("PreexistingMyeloma" in self.allValueVarNameList):
            self.ForwardPassAccumulator['PreexistingMyeloma'] = 0
        if ("DiagMyeloma" in self.allValueVarNameList):
            self.ForwardPassAccumulator['DiagMyeloma'] = 0
        if ("HospitalAdmitDate" in self.allValueVarNameList):
            self.ForwardPassAccumulator['HospitalAdmitDate'] = TDF_INVALID_VALUE
        if ("InAKI" in self.allValueVarNameList):
            self.ForwardPassAccumulator['InAKI'] = TDF_INVALID_VALUE
        if ("InHospital" in self.allValueVarNameList):
            self.ForwardPassAccumulator['InHospital'] = 0
        if ("MajorSurgeries" in self.allValueVarNameList):
            self.ForwardPassAccumulator['MajorSurgeries'] = 0
        if ("GIProcedures" in self.allValueVarNameList):
            self.ForwardPassAccumulator['GIProcedures'] = 0


        # Now we have a basic initialized accumulator, save a copy of it.
        # Each new data point will start with either a copy of the previous data
        # point (to carry old values forward) or else a copy of this basic empty
        # accumulator. 
        savedInitialDataList = copy.deepcopy(self.ForwardPassAccumulator)

        # Some values, like drug doses, are never carried forward, and instead
        # are re-ordered daily.
        variablesToResetOnEachDay = []
        variablesToNoneOnEachDay = []
        variablesToZeroOnEachDay = []
        variablesToRemoveOnEachDay = []
        for medInfoIndex, dailyDoseName in enumerate(g_InterestingMeds):
            if (dailyDoseName in self.allValueVarNameList):
                variablesToResetOnEachDay.append(dailyDoseName)
            # End - if (dailyDoseName in self.allValueVarNameList)
        # End - for labInfoIndex, medInfo in enumerate(g_InterestingMeds)
        if ('Procedure' in self.allValueVarNameList):
            variablesToNoneOnEachDay.append('Procedure')
        if ('Surgery' in self.allValueVarNameList):
            variablesToNoneOnEachDay.append('Surgery')
        if ('MajorSurgeries' in self.allValueVarNameList):
            variablesToZeroOnEachDay.append('MajorSurgeries')
        if ('GIProcedures' in self.allValueVarNameList):
            variablesToZeroOnEachDay.append('GIProcedures')
        variablesToRemoveOnEachDay.append('Flag_HospitalAdmission')
        variablesToRemoveOnEachDay.append('Flag_HospitalDischarge')

        # These are the times that milestones are reached. These are computed on the
        # forward pass, and then saved into the timeline on the reverse pass
        self.EventualDeathDate = TDF_INVALID_VALUE
        self.StartMELD40Date = TDF_INVALID_VALUE
        self.StartMELD30Date = TDF_INVALID_VALUE
        self.StartMELD20Date = TDF_INVALID_VALUE
        self.StartMELD10Date = TDF_INVALID_VALUE
        self.StartCKD5Date = TDF_INVALID_VALUE
        self.StartCKD4Date = TDF_INVALID_VALUE
        self.StartCKD3bDate = TDF_INVALID_VALUE
        self.StartCKD3aDate = TDF_INVALID_VALUE

        self.FutureBaselineCr = TDF_INVALID_VALUE
        self.baselineCrSeries = None
        if ("baselineCr" in self.allValueVarNameList):
            self.baselineCrSeries = timefunc.CTimeSeries(7)

        self.NextFutureDischargeDate = TDF_INVALID_VALUE
        self.NextFutureIntubationDate = TDF_INVALID_VALUE
        self.NextFutureRapidResponseDate = TDF_INVALID_VALUE
        self.NextFutureTransferToICUDate = TDF_INVALID_VALUE
        self.NextFutureTransferToWardDate = TDF_INVALID_VALUE

        # Initialize the daily med list for the forward pass.            
        self.NewMedsForCurrentDay = dict()

        # These are used in the forward pass to fix a bug in TDF files.
        # Some XML nodes may have out of order dates.
        # Probably from an admit order, which is dated earlier than the first labs of the admission.
        prevTimeCode = TDF_INVALID_VALUE
        prevDateDays = TDF_INVALID_VALUE
        prevDateHours = TDF_INVALID_VALUE

        ######################################
        # FORWARD PASS
        # Keep a running list of the latest values for all lab values. This includes
        # all lab values.
        currentNode = dxml.XMLTools_GetFirstChildNode(self.currentPatientNode)
        currentTimelinePointID = -1
        if (fDebug):
            print("=======================================================\nStart Forward Pass")
        while (currentNode):
            nodeType = dxml.XMLTools_GetElementName(currentNode).lower()

            #print("Forward Pass. NodeType: " + nodeType)
            # We ignore any nodes other than Data and Events and Outcomes
            if ((nodeType != "e") and (nodeType != "d") and (nodeType != "oc")):
                # Go to the next XML node in the TDF
                currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
                continue

            # Get the timestamp for this XML node.
            currentTimeCode = TDF_INVALID_VALUE
            timeStampStr = currentNode.getAttribute("T")
            if ((timeStampStr is not None) and (timeStampStr != "")):
                labDateDays, labDateHours, labDateMins = TDF_ParseTimeStamp(timeStampStr)
                currentTimeCode = TDF_ConvertTimeStampToInt(timeStampStr)

            if ((currentTimeCode < 0) or (nodeType == "oc")):
                # Just copy the old timestamp forward.
                currentTimeCode = prevTimeCode
                labDateDays = prevDateDays
                labDateHours = prevDateHours

            # If we have a run of elements with no time code at the start, then
            # Skip them all until we get a time code.
            if (currentTimeCode < 0):
                currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
                continue

            # These are used in the forward pass to fix a bug in TDF files.
            # Some XML nodes may have out of order dates.
            # Probably from an admit order, which is dated earlier than the first labs of the admission.
            if ((prevTimeCode > 0) and (currentTimeCode < prevTimeCode)):
                # Just copy the old timestamp forward.
                currentTimeCode = prevTimeCode
                labDateDays = prevDateDays
                labDateHours = prevDateHours
            prevTimeCode = currentTimeCode
            prevDateDays = labDateDays
            prevDateHours = labDateHours

            # We divide each day into N intervals. An interval lasts at least 1 minute.
            # Find which interval this time is in.
            labDateMinuteInDay = (labDateHours * 60) + labDateMins
            labDateIntervalInDay = int(labDateMinuteInDay / self.MinutesPerTimelineEntry)

            dataClass = ""
            if (nodeType == "d"):
                dataClass = currentNode.getAttribute("C").lower()

            # Find where we store the data from this XML node in the runtime timeline.
            # There may be separate XML nodes for labs, vitals and events that all map to the same
            # timeline entry. Collapse all lab and vitals data from the same time to a single interval.
            reuseLatestData = False
            if ((self.latestTimeLineEntryTimeDays >= 0)
                    and (self.latestTimeLineEntryTimeDays == labDateDays)
                    and (self.latestTimeLineEntryIntervalInDay >= 0)
                    and (self.latestTimeLineEntryIntervalInDay == labDateIntervalInDay)):
                reuseLatestData = True
            # Outcome dates are sloppy. However, do not overuse too much
            # because that allows a later diagnosis to overwrite the date of a much
            # earlier data point.
            elif ((nodeType == "oc")
                    and (self.latestTimeLineEntryTimeDays >= 0)):
                reuseLatestData = True
            # Diagnosis dates are sloppy. However, do not overuse too much
            # because that allows a later diagnosis to overwrite the date of a much
            # earlier data point.
            elif ((nodeType == "d") and (dataClass == "d")
                    and (self.latestTimeLineEntryTimeDays >= 0)
                    and (self.latestTimeLineEntryTimeDays == labDateDays)):
                reuseLatestData = True
            # Events reuse the most recent data point if it is in the same day and hour
            elif ((nodeType == "e")
                    and (self.latestTimeLineEntryTimeDays == labDateDays)
                    and (self.latestTimeLineEntryTimeDays >= 0)):
                reuseLatestData = True

            if (not self.fCarryForwardPreviousDataValues):
                reuseLatestData = False


            # Get the timeline entry for this time, create a new timeline entry if necessary.
            if ((reuseLatestData) and (self.latestTimeLineEntry is not None)):
                #print("Reuse existing timeline entry")
                timelineEntry = self.latestTimeLineEntry
            else:
                # Otherwise, we are starting a new timeline entry.

                # If we are starting a new day, first finish out the previous day by adding
                # everything to the last entry of the previous day.
                if ((self.latestTimeLineEntryTimeDays >= 0) and (self.latestTimeLineEntry is not None) 
                        and (labDateDays != self.latestTimeLineEntryTimeDays)):
                    self.AddFinalEventsToFinishCurrentDay()
                # End of closing out a day.

                # Make a new time slot. 
                currentTimelinePointID += 1
                timelineEntry = {'TimeDays': labDateDays, 'TimeIntervalNum': labDateIntervalInDay, 'TID': currentTimelinePointID}

                # Add it to the list
                self.CompiledTimeline.append(timelineEntry)
                self.latestTimeLineEntry = timelineEntry
                self.latestTimeLineEntryTimeDays = labDateDays
                self.latestTimeLineEntryIntervalInDay = labDateIntervalInDay
    
                # Each timeline node needs a private copy of the latest labs.
                # Make a copy of the most recent labs, so we inherit any labs up to this point.
                # This node may overwrite any of the labs that change.
                if (self.fCarryForwardPreviousDataValues):
                    newDataList = copy.deepcopy(self.ForwardPassAccumulator)

                    # Some values, like drug doses, are never carried forward, and instead
                    # are re-ordered daily. Other values, like procedures, are never carried forward.
                    for valueName in variablesToResetOnEachDay:
                        newDataList[valueName] = TDF_INVALID_VALUE
                    for valueName in variablesToNoneOnEachDay:
                        newDataList[valueName] = None
                    for valueName in variablesToZeroOnEachDay:
                        newDataList[valueName] = 0
                    for valueName in variablesToRemoveOnEachDay:
                        if (valueName in newDataList):
                            del newDataList[valueName]
                    # End - for medName in variablesToNoneOnEachDay
                else:
                    newDataList = copy.deepcopy(savedInitialDataList)

                timelineEntry['data'] = newDataList
                timelineEntry['eventNodeList'] = []
                self.ForwardPassAccumulator = newDataList
            # End - if ((not reuseLatestData) or (self.latestTimeLineEntry is None)):

            # Read the contents of this XML node into the runtime timeline data structures.
            # Outcomes
            if (nodeType == "oc"):
                self.ProcessOutcomesNodeForwardImpl(currentNode)
            # Events
            elif (nodeType == "e"):
                timelineEntry['eventNodeList'].append(currentNode)
                self.ProcessEventNodeForwardImpl(currentNode, labDateDays, labDateHours, labDateMins)
            # Data
            elif (nodeType == "d"):
                self.ProcessDataNodeForwardImpl(currentNode, labDateDays, labDateHours, labDateMins)

            ###################################
            # Compute "SPECIAL" calculated values
            # However, other calculated values are computed when we compile the timeline, before the reverse pass.
            # This allows them to be used for future predictions, like GFR is needed to compute Days_Until_CKD4. 
            # This means a few special values (like MELD and GFR) need to be done in the forward
            # pass, so they can later be used to calculate days until values in the backward pass.
            if (self.allValuesLabInfoList is not None):
                for labInfoIndex, labInfo in enumerate(self.allValuesLabInfoList):
                    if (labInfo is None):
                        continue
                    if (labInfo['Calculated']):
                        labName = self.allValueVarNameList[labInfoIndex]
                        self.CalculateDerivedValuesFORWARDPass(labName, labDateDays, self.ForwardPassAccumulator)
                # End - for labInfoIndex, labInfo in enumerate(self.allValuesLabInfoList):
            # End - if (self.allValuesLabInfoList is not None):

            # Go to the next XML node in the TDF
            currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
        # End - while (currentNode):

        # Set all meds for the last day in the timeline.
        if ((self.latestTimeLineEntryTimeDays >= 0) and (self.latestTimeLineEntry is not None)): 
            self.AddFinalEventsToFinishCurrentDay()
        # End of closing out a day.

        self.LastTimelinePointID = currentTimelinePointID
        self.LastTimeLineIndex = len(self.CompiledTimeline) - 1        


        # Do a SECOND forward pass.
        # This loop will iterate over each step in the timeline.
        # We do this as a SEPARATE loop, becuase it uses the final values for each day.
        # The first forward pass may write several labs for the same day. For example,
        # when there is a bad lab and we do a re-check lab.
        # Alternatively, the time granularity may map high freq events to low freq records
        # and so several values may overwrite each other.
        # Do this when we have settled on a final value for each time slot.
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            latestValues = timelineEntry['data']
            self.RecordTimeMilestonesOnForwardPass(latestValues, currentDayNum)
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1):


        ######################################
        # REVERSE PASS
        # Keep a running list of the next occurrence of each event.
        if (fDebug):
            print("=======================================================\nStart Reverse Pass")
        timeLineIndex = self.LastTimeLineIndex
        while (timeLineIndex >= 0):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            # Get a reference to the data collected up to this point in FORWARD order.
            # This was compiled in the previous loop, which did the forward pass.
            reversePassTimeLineData = timelineEntry['data']

            # Now, update the events at this node using data pulled from the future 
            # in REVERSE order.
            for currentNode in timelineEntry['eventNodeList']:
                self.ProcessEventNodeInReverseImpl(reversePassTimeLineData, currentNode, currentDayNum)

            # Remove any references so the data can eventually be garbage collected when we are
            # done with the XML but still using the timeline.
            timelineEntry['eventNodeList'] = []

            ###################################
            # Compute "SPECIAL" calculated values
            # Some calculated values need to be done using future knowledge,
            # not just past knowledge.
            self.CalculateAllDerivedValuesREVERSEPass(reversePassTimeLineData, currentDayNum)

            timeLineIndex = timeLineIndex - 1
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1):

    # End - CompilePatientTimelineImpl(self)






    ################################################################################
    #
    # [TDFFileReader::AddFinalEventsToFinishCurrentDay]
    #
    ################################################################################
    def AddFinalEventsToFinishCurrentDay(self):
        # At the end of each day, we update the list of medications.
        # Drug events happen when a drug is ordered, not each time it is given.
        # Moreover, a drug may be given BID or TID, so we want the total daily dose.
        # So, we simulate you give the whole dose at the end of the day. Really, this
        # is the total-daily-dose.
        #
        # We update the list of daily meds any time a new order.
        # All meds from day N should be entered on the same day. This is a big deal for 
        # clinics where two adjacent days in the timeline may really be months apart in calendar time.
        # Values in self.NewMedsForCurrentDay are the complete dose for a single day.

        # Copy the daily med lists to the timeline
        timeLineData = self.latestTimeLineEntry['data']
        for index, (medDoseName, medDose) in enumerate(self.NewMedsForCurrentDay.items()):
            if (medDoseName in self.allValueVarNameList):
                #if ("PipTazoDose" == medDoseName):
                #   print("AddFinalEventsToFinishCurrentDay. medDoseName=" + medDoseName + ", medDose=" + str(medDose))
                timeLineData[medDoseName] = medDose
        # End - for index, (medName, medDose) in enumerate(self.NewMedsForCurrentDay.items()):

        # Reset the list of new med additions for the new day we are about to start.
        self.NewMedsForCurrentDay = dict()
    # End - AddFinalEventsToFinishCurrentDay(self)






    ################################################################################
    #
    # [TDFFileReader::ProcessDataNodeForwardImpl]
    #
    # This processes any DATA node as we move forward in the the timeline. 
    # It updates self.ForwardPassAccumulator, possibly overwriting earlier outcomes.
    ################################################################################
    def ProcessDataNodeForwardImpl(self, dataNode, labDateDays, labDateHours, labDateMins):
        #print("ProcessDataNodeForwardImpl")
        dataClass = dataNode.getAttribute("C")
        labTextStr = str(dxml.XMLTools_GetTextContents(dataNode))

        ###################################
        # Labs and Vitals
        # Copy labs and vitals into the accumulator
        if ((dataClass == "L") or (dataClass == "V")):
            assignmentList = labTextStr.split(',')
            for assignment in assignmentList:
                #print("ProcessDataNodeForwardImpl. assignment=" + assignment)        
                assignmentParts = assignment.split('=')
                if (len(assignmentParts) < 2):
                    continue
                labName = assignmentParts[0]
                labvalueStr = assignmentParts[1]
                labValueFloat = float(TDF_INVALID_VALUE)

                # Look up the lab. Optimistically, try the lab name as is, it is usually a valid name
                try:
                    labInfo = g_LabValueInfo[labName]
                    labMinVal = float(labInfo['minVal'])
                    labMaxVal = float(labInfo['maxVal'])
                    foundValidLab = True
                except Exception:
                    foundValidLab = False

                # Do not save any values that are not used. There are many defined variables, and
                # a single hospital database may have many different values. We only care about some.
                # Don't spend the time or memory saving everything.
                if ((foundValidLab) and (labName not in self.allValueVarNameList)):
                    foundValidLab = False

                # Some labs are *only* computed. This lets us ensure they are correctly calculated
                # using a known algorithm and done in a consistent manner.
                if (labName == "GFR"):
                    foundValidLab = False

                # Try to parse the value.
                if (foundValidLab):
                    try:
                        labValueFloat = float(labvalueStr)
                    except Exception:
                        # Replace invalid characters.
                        labvalueStr = labvalueStr.replace('>', '') 
                        labvalueStr = labvalueStr.replace('<', '') 
                        try:
                            labValueFloat = float(labvalueStr)
                        except Exception:
                            foundValidLab = False
                # End - if ((labName != "") and (labValue != "")):

                # Rule out ridiculous values. Often, vitals will be entered incorrectly
                # or similar things. This won't catch all invalid entries, but will catch
                # some.
                if ((foundValidLab) and ((labValueFloat < TDF_SMALLEST_VALID_VALUE) or (labValueFloat >= (10 * labMaxVal)))):
                    foundValidLab = False

                # Now, clip the value to the min and max for this variable and then save it.
                if (foundValidLab):
                    if (labValueFloat < float(labMinVal)):
                        labValueFloat = float(labMinVal)
                    if (labValueFloat > float(labMaxVal)):
                        labValueFloat = float(labMaxVal)
                    self.ForwardPassAccumulator[labName] = labValueFloat
                # End - if (foundValidLab)
            # End - for assignment in assignmentList
        # End - if ((dataClass == "L") or (dataClass == "V")):

        # Import Diagnosis Nodes
        if (dataClass == "D"):
            self.DiagnosisList.append({"day": labDateDays, "diag": labTextStr})
        # End - if (dataClass == "D"):

        # Some values come from the timestamp, not the contents, of the data element.
        if ("AgeInYrs" in self.allValueVarNameList):
            result = int(labDateDays / 365)
            self.ForwardPassAccumulator["AgeInYrs"] = result
        if ("AgeInDays" in self.allValueVarNameList):
            result = int(labDateDays)
            self.ForwardPassAccumulator["AgeInDays"] = result
    # End - ProcessDataNodeForwardImpl






    ################################################################################
    #
    # [TDFFileReader::CalculateDerivedValuesFORWARDPass]
    #
    # This is called when we build the timeline. Some values like GFR and MELD 
    # are needed for the reverse pass.
    #
    # It CANNOT use values from the future, like days_until_death. Those are computed
    # on the reverse pass which comes later.
    ################################################################################
    def CalculateDerivedValuesFORWARDPass(self, varName, currentDayNum, varValueDict):
        #print("CalculateDerivedValuesFORWARDPass")

        ##############################################
        if (varName == "GFR"):
            try:
                currrentCr = varValueDict['Cr']
            except Exception:
                currrentCr = TDF_INVALID_VALUE
            try:
                patientAge = varValueDict['AgeInYrs']
            except Exception:
                patientAge = TDF_INVALID_VALUE
            try:
                fIsMale = varValueDict['IsMale']
            except Exception:
                fIsMale = TDF_INVALID_VALUE

            eGFR = self.CalculateGFR(currrentCr, patientAge, fIsMale)
            if (eGFR > TDF_SMALLEST_VALID_VALUE):
                eGFR = round(eGFR)
                varValueDict[varName] = eGFR
        # End - if (varName = "GFR"):

        ##############################################
        elif (varName == "MELD"):
            try:
                serumCr = varValueDict['Cr']
                serumNa = varValueDict['Na']
                tBili = varValueDict['Tbili']
                inr = varValueDict['INR']
            except Exception:
                serumCr = TDF_INVALID_VALUE
                serumNa = TDF_INVALID_VALUE
                tBili = TDF_INVALID_VALUE
                inr = TDF_INVALID_VALUE

            if ((serumCr > TDF_SMALLEST_VALID_VALUE) and (tBili > TDF_SMALLEST_VALID_VALUE) and (serumNa > TDF_SMALLEST_VALID_VALUE) and (inr > TDF_SMALLEST_VALID_VALUE)):
                # Clip bili, INR and Cr to specific ranges. The formula is not
                # validated for vals outside those ranges.
                if (inr < 1.0):
                    inr = 1.0
                if (tBili < 1.0):
                    tBili = 1.0
                if (serumCr < 1.0):
                    serumCr = 1.0
                if (serumCr > 4.0):
                    serumCr = 4.0
                if (serumNa < 125):
                    serumNa = 125
                if (serumNa > 137):
                    serumNa = 137

                # If the base is not passed as a second parameter, then math.log() returns natural log.
                lnCr = math.log(float(serumCr))
                lntBili = math.log(float(tBili))
                lnINR = math.log(float(inr))

                # Be careful, some formula will rearrange the parens, so add 6.43 rather than 10*0.643, but it is the same.
                meldScore = 10 * ((0.957 * lnCr) + (0.378 * lntBili) + (1.12 * lnINR) + 0.643)
                if (meldScore > 11.0):
                    # MELD = MELD(i) + 1.32*(137-Na) – [0.033*MELD(i)*(137-Na)]
                    meldScore = meldScore + (1.32 * (137 - serumNa)) - (0.033 * meldScore * (137 - serumNa))

                result = round(meldScore)
                varValueDict[varName] = result

        ##############################################
        # Compute the baseline Cr
        # ------------------------
        # The baseline Cr is tricky and requires past and future knowledge.
        # Consider a pt with Cr 1.0, then goes to an AKI with peak Cr 2.9 then
        # recovers to a new baseline Cr of 1.4.
        #
        # Baseline is the lowest value of the past 7 days, but also cannot be higher 
        # than the lowest future value.
        # We will calculate it here based on past history, but may revise the value on the
        # forward pass using future information.
        if (varName == "BaselineCr"):
            # Try to extend the running history of recent Cr values
            try:
                currrentCr = varValueDict['Cr']
            except Exception:
                currrentCr = TDF_INVALID_VALUE
            if (currrentCr > TDF_SMALLEST_VALID_VALUE):
                self.baselineCrSeries.AddNewValue(currrentCr, currentDayNum, 0, 0)

            # Now, update the value
            result = self.baselineCrSeries.GetLowestValue()
            varValueDict[varName] = result
        # End - if (varName == "BaselineCr")

        ##############################################
        elif (varName == "BUNCrRatio"):
            try:
                serumBUN = varValueDict['BUN']
            except Exception:
                serumBUN = TDF_INVALID_VALUE
            try:
                currrentCr = varValueDict['Cr']
            except Exception:
                currrentCr = TDF_INVALID_VALUE
            if ((serumBUN > TDF_SMALLEST_VALID_VALUE) and (currrentCr > TDF_SMALLEST_VALID_VALUE)):
                result = float(serumBUN) / float(currrentCr)
                result = round(result)
                varValueDict[varName] = result


        ##############################################
        elif (varName == "TIBC"):
            try:
                serumTransferrin = varValueDict['Transferrin']
            except Exception:
                serumTransferrin = TDF_INVALID_VALUE
            try:
                serumFeSat = varValueDict['TransferrinSat']
            except Exception:
                serumFeSat = TDF_INVALID_VALUE
            try:
                serumIron = varValueDict['Iron']
            except Exception:
                serumIron = TDF_INVALID_VALUE

            # TS = (Fe / TIBC) * 100 
            # or TIBC = (Fe / TS) * 100
            if ((serumIron > TDF_SMALLEST_VALID_VALUE) and (serumFeSat > TDF_SMALLEST_VALID_VALUE)):
                result = float(serumIron) / float(serumFeSat)
                result = round(result) * 100
                varValueDict[varName] = result
            # Transferrin (mg/dL) = 0.8 x TIBC (µg of iron/dL) – 43
            elif ((serumTransferrin > TDF_SMALLEST_VALID_VALUE)):
                result = (float(serumTransferrin) + 43) / 0.8
                result = round(result) * 100
                varValueDict[varName] = result


        ##############################################
        elif (varName == "NeutLymphRatio"):
            try:
                AbsNeutrophils = varValueDict['AbsNeutrophils']
            except Exception:
                AbsNeutrophils = TDF_INVALID_VALUE
            try:
                AbsLymphs = varValueDict['AbsLymphs']
            except Exception:
                AbsLymphs = TDF_INVALID_VALUE
            if ((AbsNeutrophils > TDF_SMALLEST_VALID_VALUE) and (AbsLymphs > TDF_SMALLEST_VALID_VALUE)):
                result = float(AbsNeutrophils) / float(AbsLymphs)
                result = round(result)
                varValueDict[varName] = result

        ##############################################
        elif (varName == "AnionGap"):
            try:
                serumNa = varValueDict['Na']
                serumCl = varValueDict['Cl']
                serumCO2 = varValueDict['CO2']
            except Exception:
                serumNa = TDF_INVALID_VALUE
                serumCl = TDF_INVALID_VALUE
                serumCO2 = TDF_INVALID_VALUE
            if ((serumNa > TDF_SMALLEST_VALID_VALUE) and (serumCl > TDF_SMALLEST_VALID_VALUE) and (serumCO2 > TDF_SMALLEST_VALID_VALUE)):
                varValueDict[varName] = serumNa - (serumCl + serumCO2)

        ##############################################
        elif (varName == "ProtGap"):
            try:
                serumTProt = varValueDict['TProt']
                serumAlb = varValueDict['Alb']
            except Exception:
                serumTProt = TDF_INVALID_VALUE
                serumAlb = TDF_INVALID_VALUE
            if ((serumTProt > TDF_SMALLEST_VALID_VALUE) and (serumAlb > TDF_SMALLEST_VALID_VALUE)):
                varValueDict[varName] = serumTProt - serumAlb

        ##############################################
        elif (varName == "UrineAnionGap"):
            try:
                urineNa = varValueDict['UNa']
                urineK = varValueDict['UK']
                urineCl = varValueDict['UCl']
            except Exception:
                urineNa = TDF_INVALID_VALUE
                urineK = TDF_INVALID_VALUE
                urineCl = TDF_INVALID_VALUE
            if ((urineNa > TDF_SMALLEST_VALID_VALUE) and (urineK > TDF_SMALLEST_VALID_VALUE) and (urineCl > TDF_SMALLEST_VALID_VALUE)):
                varValueDict[varName] = (urineNa + urineK) - urineCl

        ##############################################
        elif (varName == "UACR"):
            try:
                result = varValueDict['UPEPAlb']
            except Exception:
                result = TDF_INVALID_VALUE

            if (result < TDF_SMALLEST_VALID_VALUE):
                try:
                    urineAlb = varValueDict['UAlb']
                    urineCr = varValueDict['UCr']
                except Exception:
                    urineAlb = TDF_INVALID_VALUE
                    urineCr = TDF_INVALID_VALUE

                if ((urineAlb > TDF_SMALLEST_VALID_VALUE) and (urineCr > TDF_SMALLEST_VALID_VALUE)):
                    result = float(urineAlb) / float(urineCr)

            if (result > TDF_SMALLEST_VALID_VALUE):
                varValueDict[varName] = result

        ##############################################
        elif (varName == "UPCR"):
            try:
                result = varValueDict['UPEPTProt']
            except Exception:
                result = TDF_INVALID_VALUE

            if (result < TDF_SMALLEST_VALID_VALUE):
                try:
                    result = varValueDict['UPCR']
                except Exception:
                    result = TDF_INVALID_VALUE

            if (result < TDF_SMALLEST_VALID_VALUE):
                try:
                    urineProt = varValueDict['UProt']
                    urineCr = varValueDict['UCr']
                except Exception:
                    urineProt = TDF_INVALID_VALUE
                    urineCr = TDF_INVALID_VALUE
                if ((urineProt > TDF_SMALLEST_VALID_VALUE) and (urineCr > TDF_SMALLEST_VALID_VALUE)):
                    result = float(urineProt) / float(urineCr)

            if (result > TDF_SMALLEST_VALID_VALUE):
                varValueDict[varName] = result

        ##############################################
        elif (varName == "FENa"):
            try:
                serumCr = varValueDict['Cr']
                serumNa = varValueDict['Na']
                urineCr = varValueDict['UCr']
                urineNa = varValueDict['UNa']
            except Exception:
                serumCr = TDF_INVALID_VALUE
                serumNa = TDF_INVALID_VALUE
                urineCr = TDF_INVALID_VALUE
                urineNa = TDF_INVALID_VALUE

            if ((serumCr > TDF_SMALLEST_VALID_VALUE) and (serumNa > TDF_SMALLEST_VALID_VALUE) and (urineCr > TDF_SMALLEST_VALID_VALUE) and (urineNa > TDF_SMALLEST_VALID_VALUE)):
                result = 100.0 * float(serumCr * urineNa) / float(serumNa * urineCr)
                #result = round(result, 1)
                varValueDict[varName] = result

        ##############################################
        elif (varName == "FEUrea"):
            try:
                serumCr = varValueDict['Cr']
                serumBUN = varValueDict['BUN']
                urineCr = varValueDict['UCr']
                urineUUN = varValueDict['UUN']
            except Exception:
                serumCr = TDF_INVALID_VALUE
                serumBUN = TDF_INVALID_VALUE
                urineCr = TDF_INVALID_VALUE
                urineUUN = TDF_INVALID_VALUE

            if ((serumCr > TDF_SMALLEST_VALID_VALUE) and (serumBUN > TDF_SMALLEST_VALID_VALUE) and (urineCr > TDF_SMALLEST_VALID_VALUE) and (urineUUN > TDF_SMALLEST_VALID_VALUE)):
                result = 100.0 * float(serumCr * urineUUN) / float(serumBUN * urineCr)
                #result = round(result, 1)
                varValueDict[varName] = result

        ##############################################
        elif (varName == "AdjustCa"):
            try:
                tCal = varValueDict['Ca']
                alb = varValueDict['Alb']
            except Exception:
                tCal = TDF_INVALID_VALUE
                alb = TDF_INVALID_VALUE

            if ((tCal > TDF_SMALLEST_VALID_VALUE) and (alb > TDF_SMALLEST_VALID_VALUE)):
                result = float(tCal) + (0.8 * (4.0 - float(alb)))
                #result = round(result, 1)
                varValueDict[varName] = result
            else:
                try:
                    tCal = varValueDict['Ca']
                except Exception:
                    tCal = TDF_INVALID_VALUE
                if (tCal > TDF_SMALLEST_VALID_VALUE):
                    varValueDict[varName] = tCal

        ##############################################
        elif (varName == "KappaLambdaRatio"):
            try:
                kappaVal = varValueDict['FLCKappa']
                lambdaVal = varValueDict['FLCLambda']
            except Exception:
                kappaVal = TDF_INVALID_VALUE
                lambdaVal = TDF_INVALID_VALUE

            if ((kappaVal > TDF_SMALLEST_VALID_VALUE) and (lambdaVal > TDF_SMALLEST_VALID_VALUE)):
                result = float(kappaVal) / float(lambdaVal)
                varValueDict[varName] = result

        ##############################################
        elif (varName == "HospitalDay"):
            try:
                if (varValueDict['HospitalAdmitDate'] > TDF_SMALLEST_VALID_VALUE):
                    varValueDict['HospitalDay'] = (currentDayNum - varValueDict['HospitalAdmitDate']) + 1
            except Exception:
                pass
    # End - CalculateDerivedValuesFORWARDPass





    ################################################################################
    #
    # [TDFFileReader::CalculateGFR]
    #
    # This can use several formula. In all cases, SCr (standardized serum creatinine) = mg/dL
    # However, I ONLY use CKD EPI. It is pretty good, and I use the same consistent estimate,
    # and it does not rely on values like Cystatin C which are not reliably measured.
    #
    # CKD EPI (2021)
    #   eGFR = 142 x min(SCr/κ, 1)^α x max(SCr/κ, 1)^-1.209 x 0.9938^Age x 1.012 [if female] 
    #   Where:
    #      kappa = 0.7 (females) or 0.9 (males)
    #      alpha = -0.241 (females) or -0.302 (males)
    # See: https://www.kidney.org/content/ckd-epi-creatinine-equation-2021
    #
    ################################################################################
    def CalculateGFR(self, currrentCr, patientAge, fIsMale):
        eGFR = TDF_INVALID_VALUE

        #######################
        # CKD EPI
        # eGFR = 141 x min(SCr/κ, 1)^α x max(SCr /κ, 1)^-1.209 x 0.993Age x 1.018 [if female] x 1.159 [if Black]
        #   Where:
        #      SCr (standardized serum creatinine) = mg/dL
        #      kappa = 0.7 (females) or 0.9 (males)
        #      alpha = -0.329 (females) or -0.411 (males)
        # See: https://www.kidney.org/content/ckd-epi-creatinine-equation-2009
        if ((currrentCr > TDF_SMALLEST_VALID_VALUE) and (patientAge > TDF_SMALLEST_VALID_VALUE)):
            if (fIsMale > 0):
                kappa = 0.9
                alpha = -0.302
            else:
                kappa = 0.7
                alpha = -0.241

            creatKappaRatio = float(currrentCr) / kappa
            eGFR = 142.0

            if (creatKappaRatio < 1):
                eGFR = eGFR * math.pow(creatKappaRatio, alpha)

            if (creatKappaRatio > 1):
                eGFR = eGFR * math.pow(creatKappaRatio, -1.209)

            eGFR = eGFR * math.pow(0.9938, patientAge)
            if (fIsMale <= 0):
                eGFR = eGFR * 1.018

        return eGFR
    # End - TDFFileReader::CalculateGFR()




    ################################################################################
    #
    # [TDFFileReader::ProcessEventNodeForwardImpl]
    #
    # This processes any EVENT node as we move forward in the the timeline. 
    # It updates self.ForwardPassAccumulator, possibly overwriting earlier outcomes.
    ################################################################################
    def ProcessEventNodeForwardImpl(self, eventNode, eventDateDays, eventDateHours, eventDateMins):
        fDebug = False

        eventClass = eventNode.getAttribute("C")
        eventValue = eventNode.getAttribute("V")
        if (fDebug):
            print("ProcessEventNodeForwardImpl. Class=" + eventClass + ", Value=" + eventValue)

        ############################################
        if (eventClass == "Admit"):
            if ('InHospital' in self.allValueVarNameList):
                self.ForwardPassAccumulator['InHospital'] = 1
            if ('HospitalAdmitDate' in self.allValueVarNameList):
                self.ForwardPassAccumulator['HospitalAdmitDate'] = eventDateDays
            # Flag_HospitalAdmission is *always* added
            self.ForwardPassAccumulator['Flag_HospitalAdmission'] = 1

        ############################################
        elif (eventClass == "Discharge"):
            if ('InHospital' in self.allValueVarNameList):
                self.ForwardPassAccumulator['InHospital'] = 0
            if ('HospitalAdmitDate' in self.allValueVarNameList):
                self.ForwardPassAccumulator['HospitalAdmitDate'] = TDF_INVALID_VALUE
            # Flag_HospitalDischarge is *always* added
            self.ForwardPassAccumulator['Flag_HospitalDischarge'] = 1

        ############################################
        elif (eventClass == "Transfer"):
            if ('InICU' in self.allValueVarNameList):
                if (eventValue.startswith("ICU")):
                    self.ForwardPassAccumulator['InICU'] = 1
                else:
                    self.ForwardPassAccumulator['InICU'] = 0

        ############################################
        elif (eventClass == "Proc"):
            if (("GIProcedures" in self.allValueVarNameList) and (("EGD:" in eventValue) or ("Colonoscopy:" in eventValue))):
                self.ForwardPassAccumulator['GIProcedures'] = 1

            if ('Procedure' in self.allValueVarNameList):
                self.ForwardPassAccumulator['Procedure'] = eventValue
            ############
            if ((eventValue == "Dialysis") and ('MostRecentDialysisDate' in self.allValueVarNameList)):
                self.ForwardPassAccumulator['MostRecentDialysisDate'] = eventDateDays
            ############
            elif ((eventValue == "CardiacCath") and ('MostRecentCardiacCathDate' in self.allValueVarNameList)):
                self.ForwardPassAccumulator['MostRecentCardiacCathDate'] = eventDateDays
            ############
            elif ((eventValue == "Intubation") and ('MostRecentIntubationDate' in self.allValueVarNameList)):
                self.ForwardPassAccumulator['MostRecentIntubationDate'] = eventDateDays

        ############################################
        elif (eventClass == "Surg"):
            #print("ProcessEventNodeForwardImpl. Found a Surgery. eventValue=" + eventValue)
            if ('MajorSurgeries' in self.allValueVarNameList):
                #print("ProcessEventNodeForwardImpl. Count a Surgery")
                self.ForwardPassAccumulator['MajorSurgeries'] += 1

            if ('Surgery' in self.allValueVarNameList):
                print("ProcessEventNodeForwardImpl. Name a Surgery")
                self.ForwardPassAccumulator['Surgery'] = eventValue

            if ((eventValue == "Major/Cardiac/CABG") and ('MostRecentCABGDate' in self.allValueVarNameList)):
                self.ForwardPassAccumulator['MostRecentCABGDate'] = eventDateDays
            elif ((eventValue.startswith("Major")) and ('MostRecentMajorSurgeryDate' in self.allValueVarNameList)):
                self.ForwardPassAccumulator['MostRecentMajorSurgeryDate'] = eventDateDays

        ############################################
        # Transfusions
        elif (eventClass == "Blood"):
            doseStr = eventNode.getAttribute("D")
            eventValParts = eventValue.split(":")
            eventValue = eventValParts[0].lower()
            doseValue = ""
            if (eventValue == "rbc"):
                doseValue = "TransRBC"
            elif (eventValue == "plts"):
                doseValue = "TransPlts"
            elif (eventValue == "ffp"):
                doseValue = "TransFFP"
            elif (eventValue == "cryo"):
                doseValue = "TransCryo"
    
            if (fDebug):
                print("Transfusing: eventValue=" + eventValue + ", doseValue=" + doseValue + ", doseStr=" + str(doseStr))
            if (doseValue in self.allValueVarNameList):
                doseStr = doseStr.lstrip()
                self.ForwardPassAccumulator[doseValue] = 1

        ############################################
        # Inpatient medications
        elif (eventClass == "IMed"):
            if (fDebug):
                print("ProcessEventNodeForwardImpl. Process a new medication=" + eventClass + ", Value=" + eventValue)

            drugInfoList = eventValue.split(",")
            for drugInfo in drugInfoList:
                if (fDebug):
                    print("ProcessEventNodeForwardImpl. Found a Med. drugInfo=" + drugInfo)
                medNameAndDoseParts = drugInfo.split(":")
                medName = medNameAndDoseParts[0]
                if (len(medNameAndDoseParts) >= 2):
                    doseStr = medNameAndDoseParts[1]
                else:
                    doseStr = ""

                if (medName in g_InterestingMeds):
                    medInfo = g_InterestingMeds[medName]
                    dailyDoseName = medInfo["DailyDoseLabName"]
                    if (len(medNameAndDoseParts) >= 4):
                        doseStr = medNameAndDoseParts[3]
                    else:
                        doseStr = "1"
                    # Be careful. Some orders, are "Pharmacist to dose" and do not have a dose.
                    if ((doseStr == "0") or (doseStr == "")):
                        doseStr = "1"

                    if ((medName == "Vanc") or (medName == "PipTazo") or (medName == "Clopidogrel") or (medName == "HeparinDrip")
                            or (medName == "Cefepime") or (medName == "PipTazo") or (medName == "EnoxTherap") 
                            or (medName == "Metro") or (medName == "Mero") or (medName == "Coum") or (medName == "Amik")
                            or (medName == "Erta") or (medName == "Vori") or (medName == "Tobra")
                            or (medName == "Spiro") or (medName == "Furos") or (medName == "Lisin") or (medName == "Ceftriax")
                            or (medName == "Bumet") or (medName == "Tors") or (medName == "Ibup") or (medName == "Chlorthal")
                            or (medName == "Naprox") or (medName == "Dapto") or (medName == "Diclof") or (medName == "Losar")
                            or (medName == "Rivaroxaban") or (medName == "Valsar") or (medName == "Enalapril") 
                            or (medName == "Ketor") or (medName == "Tac") or (medName == "Cyc") or (medName == "MTX")):
                        pass
                    else:
                        pass
                        #print("ProcessEventNodeForwardImpl. Interesting medName=" + medName 
                        #       + ", dailyDoseName=" + dailyDoseName + ", Dose=" + doseStr)

                    # Add this to the daily total. Some meds may be given daily, or Q12h or Q8h.
                    # We use the total daily dose for each day.
                    if (dailyDoseName in self.NewMedsForCurrentDay):
                        self.NewMedsForCurrentDay[dailyDoseName] += float(doseStr)
                    else:
                        self.NewMedsForCurrentDay[dailyDoseName] = float(doseStr)
                    # End - if ((dailyDoseName != "") and (dailyDoseName in self.allValueVarNameList)):
                # End - if (medName in g_InterestingMeds)
            # End - for drugInfo in drugInfoList
        # End - elif (eventClass == "Med"):
    # End - ProcessEventNodeForwardImpl





    ################################################################################
    #
    # [TDFFileReader::ProcessOutcomesNodeForwardImpl]
    #
    # This processes any OUTCOME (OC) node as we move forward in the the timeline. 
    #
    #  <OC scope=xxx>  name=value, name=value, name=value   </OC>
    #
    # It updates self.ForwardPassAccumulator, possibly overwriting earlier outcomes.
    ################################################################################
    def ProcessOutcomesNodeForwardImpl(self, outcomesNode):
        listStr = dxml.XMLTools_GetTextContents(outcomesNode)
        #print("ProcessOutcomesNodeForwardImpl. listStr=[" + listStr + "]")
        if ((listStr is None) or (listStr == "")):
            return

        listStr = listStr.replace("\" DiedIn12Mos=\"", "\"; DiedIn12Mos=\"")

        nameValuePairList = listStr.split(';')
        for nameValuePair in nameValuePairList:
            #print("ProcessOutcomesNodeForwardImpl. nameValuePair=[" + nameValuePair + "]")
            nameValueParts = nameValuePair.split('=')
            if (len(nameValueParts) <= 1):
                continue

            name = nameValueParts[0]
            #print("ProcessOutcomesNodeForwardImpl. name=[" + name + "]")
            if (name in self.allValueVarNameList):
                value = nameValueParts[1]
                value = value.replace("\"", "")
                value = value.lower()
                if (name == "DiedThisAdmission"):
                    if ((value == "t") and ("DiedThisAdmission" in self.allValueVarNameList)):
                        self.ForwardPassAccumulator['DiedThisAdmission'] = 1
                elif (name == "DiedIn12Mos"):
                    if (value == "t"):
                        self.ForwardPassAccumulator['DiedIn12Mos'] = 1
                elif (name == "ReadmitIn30Days"):
                    if (value == "t"):
                        self.ForwardPassAccumulator['ReadmitIn30Days'] = 1
                elif (name == "PreexistingMyeloma"):
                    if (value == "t"):
                        self.ForwardPassAccumulator['PreexistingMyeloma'] = 1
                elif (name == "DiagMyeloma"):
                    if (value == "t"):
                        self.ForwardPassAccumulator['DiagMyeloma'] = 1
                # End - if (len(nameValueParts) > 1):
            # End - if (name in self.allValueVarNameList):
        # End - for index, nameValuePair in nameValuePairList:
    # End - ProcessOutcomesNodeForwardImpl




    ################################################################################
    #
    # [TDFFileReader::RecordTimeMilestonesOnForwardPass]
    #
    # This is done on the FORWARD pass
    ################################################################################
    def RecordTimeMilestonesOnForwardPass(self, timeLineData, currentDayNum):
        fDebug = False
        #print("RecordTimeMilestonesOnForwardPass")

        # In an AKI, the eGFR (I know, it's not validated for AKI...) may change up and down.
        # We say you start a particular stage of eGFR if the current eGFR meets a criteria now
        # and will not fail to meet that criteria again in the future.
        # For example, you are CKD4 if you meet CKD4 now and will never be CKD3b in the future.
        # As a result, on the forward pass, if you do meet CKD 3b now, then cancel any previous
        # timestamps for CKD4, since they were obviously premature (they were an AKI that resolved).
        if ("GFR" in timeLineData):
            currentGFR = timeLineData["GFR"]
            if (fDebug):
                print("RecordTimeMilestonesOnForwardPass. currentDayNum=" + str(currentDayNum) + ", currentGFR=" + str(currentGFR))

            if (currentGFR < TDF_SMALLEST_VALID_VALUE):
                pass
            elif (currentGFR <= 15):
                if (self.StartCKD5Date < 0):
                    self.StartCKD5Date = currentDayNum
                    if (fDebug):
                        print("RecordTimeMilestonesOnForwardPass. Set StartCKD5Date=" + str(currentDayNum))
                if (self.StartCKD4Date < 0):
                    self.StartCKD4Date = currentDayNum
                if (self.StartCKD3bDate < 0):
                    self.StartCKD3bDate = currentDayNum
                if (self.StartCKD3aDate < 0):
                    self.StartCKD3aDate = currentDayNum
            elif ((currentGFR > 15) and (currentGFR <= 30)):
                if (self.StartCKD4Date < 0):
                    self.StartCKD4Date = currentDayNum
                if (self.StartCKD3bDate < 0):
                    self.StartCKD3bDate = currentDayNum
                if (self.StartCKD3aDate < 0):
                    self.StartCKD3aDate = currentDayNum
                self.StartCKD5Date = TDF_INVALID_VALUE
                if (fDebug):
                    print("RecordTimeMilestonesOnForwardPass. Cleared StartCKD5Date")
            elif ((currentGFR > 30) and (currentGFR <= 45)):
                if (self.StartCKD3bDate < 0):
                    self.StartCKD3bDate = currentDayNum
                if (self.StartCKD3aDate < 0):
                    self.StartCKD3aDate = currentDayNum
                self.StartCKD4Date = TDF_INVALID_VALUE
                self.StartCKD5Date = TDF_INVALID_VALUE
                if (fDebug):
                    print("RecordTimeMilestonesOnForwardPass. Cleared StartCKD5Date")
            elif ((currentGFR > 45) and (currentGFR < 60)):
                if (self.StartCKD3aDate < 0):
                    self.StartCKD3aDate = currentDayNum
                self.StartCKD3bDate = TDF_INVALID_VALUE
                self.StartCKD4Date = TDF_INVALID_VALUE
                self.StartCKD5Date = TDF_INVALID_VALUE
                if (fDebug):
                    print("RecordTimeMilestonesOnForwardPass. Cleared StartCKD5Date")
            elif (currentGFR >= 60):
                self.StartCKD3aDate = TDF_INVALID_VALUE
                self.StartCKD3bDate = TDF_INVALID_VALUE
                self.StartCKD4Date = TDF_INVALID_VALUE
                self.StartCKD5Date = TDF_INVALID_VALUE
                if (fDebug):
                    print("RecordTimeMilestonesOnForwardPass. Cleared StartCKD5Date")


        # MELD progresses similar to CKD.
        # A low MELD today will erase any worse estimates of MELD in the past
        if ("MELD" in timeLineData):
            currentMELD = timeLineData["MELD"]
            if (currentMELD < TDF_SMALLEST_VALID_VALUE):
                pass
            elif (currentMELD >= 40):
                if (self.StartMELD40Date < 0):
                    self.StartMELD40Date = currentDayNum
                if (self.StartMELD30Date < 0):
                    self.StartMELD30Date = currentDayNum
                if (self.StartMELD20Date < 0):
                    self.StartMELD20Date = currentDayNum
                if (self.StartMELD10Date < 0):
                    self.StartMELD10Date = currentDayNum
            elif ((currentMELD >= 30) and (currentMELD < 40)):
                if (self.StartMELD30Date < 0):
                    self.StartMELD30Date = currentDayNum
                if (self.StartMELD20Date < 0):
                    self.StartMELD20Date = currentDayNum
                if (self.StartMELD10Date < 0):
                    self.StartMELD10Date = currentDayNum
                self.StartMELD40Date = TDF_INVALID_VALUE
            elif ((currentMELD >= 20) and (currentMELD < 30)):
                if (self.StartMELD20Date < 0):
                    self.StartMELD20Date = currentDayNum
                if (self.StartMELD10Date < 0):
                    self.StartMELD10Date = currentDayNum
                self.StartMELD30Date = TDF_INVALID_VALUE
                self.StartMELD40Date = TDF_INVALID_VALUE
            elif ((currentMELD >= 10) and (currentMELD < 20)):
                if (self.StartMELD10Date < 0):
                    self.StartMELD10Date = currentDayNum
                self.StartMELD20Date = TDF_INVALID_VALUE
                self.StartMELD30Date = TDF_INVALID_VALUE
                self.StartMELD40Date = TDF_INVALID_VALUE
            elif (currentMELD < 10):
                self.StartMELD10Date = TDF_INVALID_VALUE
                self.StartMELD20Date = TDF_INVALID_VALUE
                self.StartMELD30Date = TDF_INVALID_VALUE
                self.StartMELD40Date = TDF_INVALID_VALUE
    # End - RecordTimeMilestonesOnForwardPass







    ################################################################################
    #
    # [TDFFileReader::CalculateAllDerivedValuesREVERSEPass]
    #
    # This processes any DATA node as we move REVERSE in the the timeline. 
    # It also propagates values backward in time. This lets nodes record the time until 
    # some future event
    #
    # This runs after the forward and since it is in reverse everything from the future is
    # already known. As a result, it can calculate values based on both current data 
    # and future events. For example, on the forward pass, we computed the date when some 
    # milestones are first met. Now, on the reverse pass, update each timeline point with 
    # data about the future. So, every value will know when a future milestone will be met.
    ################################################################################
    def CalculateAllDerivedValuesREVERSEPass(self, reversePassTimeLineData, currentDayNum):
        #print("CalculateAllDerivedValuesREVERSEPass")
        currentCr = TDF_INVALID_VALUE
        inAKI = 0

        ##########################################
        # Update the baseline Cr
        # ------------------------
        # The baseline Cr is tricky and requires past and future knowledge.
        # Consider a pt with Cr 1.0, then goes to an AKI with peak Cr 2.9 then
        # recovers to a new baseline Cr of 1.4.
        #
        # Baseline is the lowest value of the past 7 days, but also cannot be higher 
        # than the lowest future value.
        #
        # If a future Cr (one we previously saw in the reverse direction) is
        # LESS than the current Cr, then the current Cr reflects an AKI, not baseline.
        # In this case, just copy the future baseline back to this point.
        # Otherwise, update the Cr.
        if ("BaselineCr" in self.allValueVarNameList):
            # These were calculated earlier, on the FORWARD pass, using a TimeSeries
            # which was a running list of the most recent 7 days of recent values
            try:
                baselineCr = reversePassTimeLineData['BaselineCr']
            except Exception:
                baselineCr = TDF_INVALID_VALUE

            # Extend the lowest Cr from the future by adding information from present.
            # The future lowest Cr is the lowest value of all Cr from now into the future.
            try:
                currentCr = reversePassTimeLineData['Cr']
            except Exception:
                currentCr = TDF_INVALID_VALUE
            if (currentCr > TDF_SMALLEST_VALID_VALUE):
                if ((self.FutureBaselineCr < TDF_SMALLEST_VALID_VALUE) or (currentCr < self.FutureBaselineCr)):
                    self.FutureBaselineCr = currentCr
            # End - if (currentCr > TDF_SMALLEST_VALID_VALUE):

            # The current baseline cannot be worse than what it will be.
            if ((self.FutureBaselineCr > TDF_SMALLEST_VALID_VALUE) and (self.FutureBaselineCr < baselineCr)):
                reversePassTimeLineData["BaselineCr"] = self.FutureBaselineCr
        # End - if ("BaselineCr" in self.allValueVarNameList):


        ##########################################
        if ("BaselineGFR" in self.allValueVarNameList):
            try:
                baselineCr = reversePassTimeLineData['BaselineCr']
            except Exception:
                baselineCr = TDF_INVALID_VALUE
            try:
                patientAge = reversePassTimeLineData['AgeInYrs']
            except Exception:
                patientAge = TDF_INVALID_VALUE
            try:
                fIsMale = reversePassTimeLineData['IsMale']
            except Exception:
                fIsMale = TDF_INVALID_VALUE

            eGFR = self.CalculateGFR(baselineCr, patientAge, fIsMale)
            if (eGFR > TDF_SMALLEST_VALID_VALUE):
                reversePassTimeLineData["BaselineGFR"] = round(eGFR)
        # End - if (varName = "BaselineGFR"):


        ##########################################
        # Now we know the baselines, we can decide whether we are in an AKI.
        # If we are not at baseline Cr, then we are in AKI
        if ("InAKI" in self.allValueVarNameList):
            deltaCr = TDF_INVALID_VALUE
            try:
                currentCr = reversePassTimeLineData['currentCr']
            except Exception:
                currentCr = TDF_INVALID_VALUE
            try:
                baselineCr = reversePassTimeLineData['BaselineCr']
            except Exception:
                baselineCr = TDF_INVALID_VALUE

            if ((currentCr > TDF_SMALLEST_VALID_VALUE) and (baselineCr > TDF_SMALLEST_VALID_VALUE)):
                deltaCr = currentCr - baselineCr
                inAKI = 0
                # Like KDIGO, I use 0.3 as the threshold, but only for basic Cr
                # The threshold should depend on the CKD. A variation of 0.3
                # when the baseline GFR is 20 and Cr is 2.5, is probably not a real AKI.
                # Still, this is what the guidelines say.
                if ((baselineCr <= 1.5) and (deltaCr >= 0.3)):
                    inAKI = 1
                if (deltaCr >= (1.5 * baselineCr)):
                    inAKI = 1
            # End - if ((currentCr > TDF_SMALLEST_VALID_VALUE) and (baselineCr > TDF_SMALLEST_VALID_VALUE)):

            reversePassTimeLineData["InAKI"] = inAKI
            # Computing the dates of the next AKI or AKI recovery is different than CKD.
            # CKD stage monotonically increases, but AKI's may come and go. As a result,
            # We must store these in the timeline itself, not in member variables.
            if (inAKI):
                reversePassTimeLineData["NextAKIDate"] = currentDayNum
            else:
                reversePassTimeLineData["NextCrAtBaselineDate"] = currentDayNum
        # End - if ("InAKI" in self.allValueVarNameList):


        ##########################################
        # Computing the dates of the next AKI or AKI recovery is different than CKD.
        # CKD stage monotonically increases, but AKI's may come and go. As a result,
        # we only use the AKI from the timeline.
        if ("Future_Days_Until_AKI" in self.allValueVarNameList):
            try:
                dateOfNextAKI = reversePassTimeLineData['NextAKIDate']
            except Exception:
                dateOfNextAKI = TDF_INVALID_VALUE
            deltaDays = dateOfNextAKI - currentDayNum
            if ((dateOfNextAKI > 0) and (deltaDays > 0)):
                reversePassTimeLineData["Future_Days_Until_AKI"] = deltaDays
            else:
                reversePassTimeLineData["Future_Days_Until_AKI"] = TDF_INVALID_VALUE

        if ("Future_Category_AKI" in self.allValueVarNameList):
            try:
                dateOfNextAKI = reversePassTimeLineData['NextAKIDate']
            except Exception:
                dateOfNextAKI = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Category_AKI"] = self.ComputeOutcomeCategory(currentDayNum, dateOfNextAKI)

        if ("Future_Days_Until_AKIResolution" in self.allValueVarNameList):
            try:
                dateOfNextAKIResolution = reversePassTimeLineData['NextCrAtBaselineDate']
            except Exception:
                dateOfNextAKIResolution = TDF_INVALID_VALUE

            deltaDays = dateOfNextAKIResolution - currentDayNum
            if ((dateOfNextAKIResolution > 0) and (deltaDays > 0)):
                reversePassTimeLineData["Future_Days_Until_AKIResolution"] = deltaDays
            else:
                reversePassTimeLineData["Future_Days_Until_AKIResolution"] = TDF_INVALID_VALUE


        ##########################################
        # These dates were calculated on the forward pass, but they get propagated backward
        # once we do the reverse pass. They are only valid once we have seen the entire timeline.
        if ("EventualDeathDate" in self.allValueVarNameList):
            reversePassTimeLineData["EventualDeathDate"] = self.EventualDeathDate
        if ("StartCKD5Date" in self.allValueVarNameList):
            reversePassTimeLineData["StartCKD5Date"] = self.StartCKD5Date
        if ("StartCKD4Date" in self.allValueVarNameList):
            reversePassTimeLineData["StartCKD4Date"] = self.StartCKD4Date
        if ("StartCKD3bDate" in self.allValueVarNameList):
            reversePassTimeLineData["StartCKD3bDate"] = self.StartCKD3bDate
        if ("StartCKD3aDate" in self.allValueVarNameList):
            reversePassTimeLineData["StartCKD3aDate"] = self.StartCKD3aDate
        if ("StartMELD40Date" in self.allValueVarNameList):
            reversePassTimeLineData["StartMELD40Date"] = self.StartMELD40Date
        if ("StartMELD30Date" in self.allValueVarNameList):
            reversePassTimeLineData["StartMELD30Date"] = self.StartMELD30Date
        if ("StartMELD20Date" in self.allValueVarNameList):
            reversePassTimeLineData["StartMELD20Date"] = self.StartMELD20Date
        if ("StartMELD10Date" in self.allValueVarNameList):
            reversePassTimeLineData["StartMELD10Date"] = self.StartMELD10Date

        ##############################################
        # Death
        if ("Future_Boolean_Death" in self.allValueVarNameList):
            result = 1 if (self.EventualDeathDate > 0) else 0
            reversePassTimeLineData["Future_Boolean_Death"] = result

        if ("Future_Days_Until_Death" in self.allValueVarNameList):
            if ((self.EventualDeathDate > 0) and (currentDayNum <= self.EventualDeathDate)):
                daysUntilDeath = self.EventualDeathDate - currentDayNum
            else:
                daysUntilDeath = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_Death"] = daysUntilDeath

        if ("Future_Category_Death" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_Death"] = self.ComputeOutcomeCategory(currentDayNum, self.EventualDeathDate)

        ##############################################
        # CKD 5
        if ("Future_Boolean_CKD5" in self.allValueVarNameList):
            result = 1 if (self.StartCKD5Date > 0) else 0
            reversePassTimeLineData["Future_Boolean_CKD5"] = result

        if ("Future_Days_Until_CKD5" in self.allValueVarNameList):
            if ((self.StartCKD5Date > 0) and (currentDayNum <= self.StartCKD5Date)):
                daysUntilEvent = self.StartCKD5Date - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_CKD5"] = daysUntilEvent

        if ("Future_Category_CKD5" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_CKD5"] = self.ComputeOutcomeCategory(currentDayNum, self.StartCKD5Date)

        if ("Future_CKD5_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD5Date > 0):
                daysUntilEvent = self.StartCKD5Date - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD5_2YRS"] = eventWillHappen

        if ("Future_CKD5_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD5Date > 0):
                daysUntilEvent = self.StartCKD5Date - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD5_5YRS"] = eventWillHappen

        ##############################################
        # CKD 4
        if ("Future_Boolean_CKD4" in self.allValueVarNameList):
            result = 1 if (self.StartCKD4Date > 0) else 0
            reversePassTimeLineData["Future_Boolean_CKD4"] = result

        if ("Future_Days_Until_CKD4" in self.allValueVarNameList):
            if ((self.StartCKD4Date > 0) and (currentDayNum <= self.StartCKD4Date)):
                daysUntilEvent = self.StartCKD4Date - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_CKD4"] = daysUntilEvent

        if ("Future_Category_CKD4" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_CKD4"] = self.ComputeOutcomeCategory(currentDayNum, self.StartCKD4Date)

        if ("Future_CKD4_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD4Date > 0):
                daysUntilEvent = self.StartCKD4Date - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD4_2YRS"] = eventWillHappen

        if ("Future_CKD4_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD4Date > 0):
                daysUntilEvent = self.StartCKD4Date - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD4_5YRS"] = eventWillHappen

        ##############################################
        # CKD 3b
        if ("Future_Boolean_CKD3b" in self.allValueVarNameList):
            result = 1 if (self.StartCKD3bDate > 0) else 0
            reversePassTimeLineData["Future_Boolean_CKD3b"] = result

        if ("Future_Days_Until_CKD3b" in self.allValueVarNameList):
            if ((self.StartCKD3bDate > 0) and (currentDayNum <= self.StartCKD3bDate)):
                daysUntilEvent = self.StartCKD3bDate - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_CKD3b"] = daysUntilEvent

        if ("Future_Category_CKD3b" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_CKD3b"] = self.ComputeOutcomeCategory(currentDayNum, self.StartCKD3bDate)

        if ("Future_CKD3b_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD3bDate > 0):
                daysUntilEvent = self.StartCKD3bDate - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD3b_2YRS"] = eventWillHappen

        if ("Future_CKD3b_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD3bDate > 0):
                daysUntilEvent = self.StartCKD3bDate - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD3b_5YRS"] = eventWillHappen

        ##############################################
        # CKD 3a
        if ("Future_Boolean_CKD3a" in self.allValueVarNameList):
            result = 1 if (self.StartCKD3aDate > 0) else 0
            reversePassTimeLineData["Future_Boolean_CKD3a"] = result

        if ("Future_Days_Until_CKD3a" in self.allValueVarNameList):
            if ((self.StartCKD3aDate > 0) and (currentDayNum <= self.StartCKD3aDate)):
                daysUntilEvent = self.StartCKD3aDate - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_CKD3a"] = daysUntilEvent

        if ("Future_Category_CKD3a" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_CKD3a"] = self.ComputeOutcomeCategory(currentDayNum, self.StartCKD3aDate)

        if ("Future_CKD3a_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD3aDate > 0):
                daysUntilEvent = self.StartCKD3aDate - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD3a_2YRS"] = eventWillHappen

        if ("Future_CKD3a_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartCKD3aDate > 0):
                daysUntilEvent = self.StartCKD3aDate - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_CKD3a_5YRS"] = eventWillHappen

        ##############################################
        # MELD 40
        if ("Future_Boolean_MELD40" in self.allValueVarNameList):
            result = 1 if (self.StartMELD40Date > 0) else 0
            reversePassTimeLineData["Future_Boolean_MELD40"] = result

        if ("Future_Days_Until_MELD40" in self.allValueVarNameList):
            if ((self.StartMELD40Date > 0) and (currentDayNum <= self.StartMELD40Date)):
                daysUntilEvent = self.StartMELD40Date - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_MELD40"] = daysUntilEvent

        if ("Future_Category_MELD40" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_MELD40"] = self.ComputeOutcomeCategory(currentDayNum, self.StartMELD40Date)

        if ("Future_MELD40_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD40Date > 0):
                daysUntilEvent = self.StartMELD40Date - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD40_2YRS"] = eventWillHappen

        if ("Future_MELD40_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD40Date > 0):
                daysUntilEvent = self.StartMELD40Date - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD40_5YRS"] = eventWillHappen

        ##############################################
        # MELD 30
        if ("Future_Boolean_MELD30" in self.allValueVarNameList):
            result = 1 if (self.StartMELD30Date > 0) else 0
            reversePassTimeLineData["Future_Boolean_MELD30"] = result

        if ("Future_Days_Until_MELD30" in self.allValueVarNameList):
            if ((self.StartMELD30Date > 0) and (currentDayNum <= self.StartMELD30Date)):
                daysUntilEvent = self.StartMELD30Date - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_MELD30"] = daysUntilEvent

        if ("Future_Category_MELD30" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_MELD30"] = self.ComputeOutcomeCategory(currentDayNum, self.StartMELD30Date)

        if ("Future_MELD30_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD30Date > 0):
                daysUntilEvent = self.StartMELD30Date - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD30_2YRS"] = eventWillHappen

        if ("Future_MELD30_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD30Date > 0):
                daysUntilEvent = self.StartMELD30Date - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD30_5YRS"] = eventWillHappen

        ##############################################
        # MELD 20
        if ("Future_Boolean_MELD20" in self.allValueVarNameList):
            result = 1 if (self.StartMELD20Date > 0) else 0
            reversePassTimeLineData["Future_Boolean_MELD20"] = result

        if ("Future_Days_Until_MELD20" in self.allValueVarNameList):
            if ((self.StartMELD20Date > 0) and (currentDayNum <= self.StartMELD20Date)):
                daysUntilEvent = self.StartMELD20Date - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_MELD20"] = daysUntilEvent

        if ("Future_Category_MELD20" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_MELD20"] = self.ComputeOutcomeCategory(currentDayNum, self.StartMELD20Date)

        if ("Future_MELD20_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD20Date > 0):
                daysUntilEvent = self.StartMELD20Date - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD20_2YRS"] = eventWillHappen

        if ("Future_MELD20_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD20Date > 0):
                daysUntilEvent = self.StartMELD20Date - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD20_5YRS"] = eventWillHappen

        ##############################################
        # MELD 10
        if ("Future_Boolean_MELD10" in self.allValueVarNameList):
            result = 1 if (self.StartMELD10Date > 0) else 0
            reversePassTimeLineData["Future_Boolean_MELD10"] = result

        if ("Future_Days_Until_MELD10" in self.allValueVarNameList):
            if ((self.StartMELD10Date > 0) and (currentDayNum <= self.StartMELD10Date)):
                daysUntilEvent = self.StartMELD10Date - currentDayNum
            else:
                daysUntilEvent = TDF_INVALID_VALUE
            reversePassTimeLineData["Future_Days_Until_MELD10"] = daysUntilEvent

        if ("Future_Category_MELD10" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_MELD10"] = self.ComputeOutcomeCategory(currentDayNum, self.StartMELD10Date)

        if ("Future_MELD10_2YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD10Date > 0):
                daysUntilEvent = self.StartMELD10Date - currentDayNum
                if (daysUntilEvent < 730):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD10_2YRS"] = eventWillHappen

        if ("Future_MELD10_5YRS" in self.allValueVarNameList):
            eventWillHappen = False
            if (self.StartMELD10Date > 0):
                daysUntilEvent = self.StartMELD10Date - currentDayNum
                if (daysUntilEvent < 1825):
                    eventWillHappen = True
            reversePassTimeLineData["Future_MELD10_5YRS"] = eventWillHappen


        ##############################################
        # Length of Stay
        if ("LengthOfStay" in self.allValueVarNameList):
            try:
                CurrentAdmitDay = reversePassTimeLineData['HospitalAdmitDate']
            except Exception:
                CurrentAdmitDay = TDF_INVALID_VALUE

            if ((CurrentAdmitDay > 0) and (self.NextFutureDischargeDate > 0)):
                reversePassTimeLineData['LengthOfStay'] = self.NextFutureDischargeDate - CurrentAdmitDay
            else:
                reversePassTimeLineData['LengthOfStay'] = TDF_INVALID_VALUE

        ##############################################
        # Discharge
        # If we know the next discharge date, then we can compute how soon that will happen.
        if ("Future_Days_Until_Discharge" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Days_Until_Discharge"] = TDF_INVALID_VALUE
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureDischargeDate > 0)):
                daysUntilEvent = self.NextFutureDischargeDate - currentDayNum
                if (daysUntilEvent < 0):
                    daysUntilEvent = 0
                reversePassTimeLineData["Future_Days_Until_Discharge"] = daysUntilEvent
        # End - if (self.NextFutureDischargeDate > 0):

        if ("Future_Category_Discharge" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_Discharge"] = TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureDischargeDate > 0)):
                reversePassTimeLineData["Future_Category_Discharge"] = self.ComputeOutcomeCategory(currentDayNum, self.NextFutureDischargeDate)
        # End - if (self.NextFutureDischargeDate > 0):

        ##############################################
        # Rapid Response
        if ("Future_Days_Until_RapidResponse" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Days_Until_RapidResponse"] = TDF_INVALID_VALUE
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureRapidResponseDate > 0)):
                daysUntilEvent = self.NextFutureRapidResponseDate - currentDayNum
                if (daysUntilEvent < 0):
                    daysUntilEvent = 0
                reversePassTimeLineData["Future_Days_Until_RapidResponse"] = daysUntilEvent
        # if (self.NextFutureRapidResponseDate > 0):

        if ("Future_Category_RapidResponse" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_RapidResponse"] = TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureRapidResponseDate > 0)):
                reversePassTimeLineData["Future_Category_RapidResponse"] = self.ComputeOutcomeCategory(currentDayNum, self.NextFutureRapidResponseDate)
        # if (self.NextFutureRapidResponseDate > 0):

        if ("Future_Boolean_RapidResponse" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Boolean_RapidResponse"] = 0
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureRapidResponseDate > 0)):
                reversePassTimeLineData["Future_Boolean_RapidResponse"] = 1
        # if (self.NextFutureRapidResponseDate > 0):

        ##############################################
        # Transfer to ICU
        if ("Future_Days_Until_TransferIntoICU" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Days_Until_TransferIntoICU"] = TDF_INVALID_VALUE
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureTransferToICUDate > 0)):
                daysUntilEvent = self.NextFutureTransferToICUDate - currentDayNum
                if (daysUntilEvent < 0):
                    daysUntilEvent = 0
                reversePassTimeLineData["Future_Days_Until_TransferIntoICU"] = daysUntilEvent
        # End - if (self.NextFutureTransferToICUDate > 0):

        if ("Future_Category_TransferIntoICU" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_TransferIntoICU"] = TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureTransferToICUDate > 0)):
                reversePassTimeLineData["Future_Category_TransferIntoICU"] = self.ComputeOutcomeCategory(currentDayNum, self.NextFutureTransferToICUDate)
        # End - if (self.NextFutureTransferToICUDate > 0):

        if ("Future_Boolean_TransferIntoICU" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Boolean_TransferIntoICU"] = 0
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureTransferToICUDate > 0)):
                reversePassTimeLineData["Future_Boolean_TransferIntoICU"] = 1
        # End - if (self.NextFutureTransferToICUDate > 0):

        ##############################################
        # Transfer to Ward
        if ("Future_Days_Until_TransferOutOfICU" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Days_Until_TransferOutOfICU"] = TDF_INVALID_VALUE
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureTransferToWardDate > 0)):
                daysUntilEvent = self.NextFutureTransferToWardDate - currentDayNum
                if (daysUntilEvent < 0):
                    daysUntilEvent = 0
                reversePassTimeLineData["Future_Days_Until_TransferOutOfICU"] = daysUntilEvent
        # End - if (self.NextFutureTransferToWardDate > 0):

        if ("Future_Category_TransferOutOfICU" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_TransferOutOfICU"] = TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureTransferToWardDate > 0)):
                reversePassTimeLineData["Future_Category_TransferOutOfICU"] = self.ComputeOutcomeCategory(currentDayNum, self.NextFutureTransferToWardDate)
        # End - if (self.NextFutureTransferToWardDate > 0):

        if ("Future_Boolean_TransferOutOfICU" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Boolean_TransferOutOfICU"] = 0
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureTransferToWardDate > 0)):
                reversePassTimeLineData["Future_Boolean_TransferOutOfICU"] = 1
        # End - if (self.NextFutureTransferToWardDate > 0):

        ##############################################
        # Intubation
        if ("Future_Days_Until_Intubation" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Days_Until_Intubation"] = TDF_INVALID_VALUE
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureIntubationDate > 0)):
                daysUntilEvent = self.NextFutureIntubationDate - currentDayNum
                if (daysUntilEvent < 0):
                    daysUntilEvent = 0
                reversePassTimeLineData["Future_Days_Until_Intubation"] = daysUntilEvent
        # End - if (self.NextFutureIntubationDate > 0):

        if ("Future_Category_Intubation" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Category_Intubation"] = TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureIntubationDate > 0)):
                reversePassTimeLineData["Future_Category_Intubation"] = self.ComputeOutcomeCategory(currentDayNum, self.NextFutureIntubationDate)
        # End - if (self.NextFutureIntubationDate > 0):

        if ("Future_Boolean_Intubation" in self.allValueVarNameList):
            reversePassTimeLineData["Future_Boolean_Intubation"] = 0
            if (('InHospital' in reversePassTimeLineData) and (reversePassTimeLineData['InHospital'] > 0) and (self.NextFutureIntubationDate > 0)):
                reversePassTimeLineData["Future_Boolean_Intubation"] = 1
        # End - if (self.NextFutureIntubationDate > 0):

    # End - CalculateAllDerivedValuesREVERSEPass







    ################################################################################
    #
    # [TDFFileReader::ProcessEventNodeInReverseImpl]
    #
    # This processes any EVENT node as we move REVERSE in the the timeline. 
    # It also propagates values backward in time. This lets nodes record the time until 
    # some future event. 
    ################################################################################
    def ProcessEventNodeInReverseImpl(self, reversePassTimeLineData, eventNode, eventDateDays):
        eventClass = eventNode.getAttribute("C")
        #print("ProcessEventNodeInReverseImpl. eventClass=" + str(eventClass))

        #####################
        if (eventClass == "Admit"):
            self.NextFutureDischargeDate = TDF_INVALID_VALUE
            self.NextFutureIntubationDate = TDF_INVALID_VALUE
            self.NextFutureRapidResponseDate = TDF_INVALID_VALUE
            self.NextFutureTransferToICUDate = TDF_INVALID_VALUE
            self.NextFutureTransferToWardDate = TDF_INVALID_VALUE
        #####################
        elif (eventClass == "Discharge"):
            #print("Discharge Event in reverse pass")
            self.NextFutureDischargeDate = eventDateDays
            self.NextFutureIntubationDate = TDF_INVALID_VALUE
            self.NextFutureRapidResponseDate = TDF_INVALID_VALUE
            self.NextFutureTransferToICUDate = TDF_INVALID_VALUE
            self.NextFutureTransferToWardDate = TDF_INVALID_VALUE

            # If we see a discharge and earlier on the forward pass we knew the patient died on this admission,
            # then compute the day of death. Only do this once, the last time we expect to see the patient die,
            # which is the first time we see this when travelling in the reverse direction.
            if (('DiedThisAdmission' in reversePassTimeLineData) 
                    and (reversePassTimeLineData['DiedThisAdmission'] > 0) 
                    and (self.EventualDeathDate <= 0)):
                self.EventualDeathDate = eventDateDays
        #####################
        elif (eventClass == "Transfer"):
            eventValue = eventNode.getAttribute("V")
            if ((eventValue == "Ward") or (eventValue == "Prog")):
                self.NextFutureTransferToWardDate = eventDateDays
            elif (eventValue.startswith("ICU")):
                self.NextFutureTransferToICUDate = eventDateDays
        #####################
        elif (eventClass == "RapidResponse"):
            self.NextFutureRapidResponseDate = eventDateDays
        #####################
        elif (eventClass == "Proc"):
            eventValue = eventNode.getAttribute("V")
            if (eventValue == "proc/Intubation"):
                self.NextFutureIntubationDate = eventDateDays
    # End - ProcessEventNodeInReverseImpl







    #####################################################
    #
    # [TDFFileReader::GetBoundsForDataFetch]
    #
    #####################################################
    def GetBoundsForDataFetch(self, resultLabInfo):
        # By default, we will read the entire window.
        firstTimelineIndex = 0
        lastTimelineIndex = self.LastTimeLineIndex

        if (resultLabInfo is None):
            return firstTimelineIndex, lastTimelineIndex

        # If this result assumes that we will know a future outcome (several results do), then 
        # make sure we only include data points that know whether the future outcome happened.
        # Clip the data window so we only include data points that have enough future information.
        # If we need to predict a result N days in the future, then do not return data that cannot
        # accurately know that in the future.
        # This loop will iterate over each step in the timeline.
        NameOfFutureLabValue = resultLabInfo['FuturePredictedValue']
        if (NameOfFutureLabValue != ""):
            numFutureDaysNeeded = int(resultLabInfo['numFutureDaysNeeded'])
            #print("GetBoundsForDataFetch. Clipping. NameOfFutureLabValue=" + str(NameOfFutureLabValue))
            #print("GetBoundsForDataFetch. Clipping. numFutureDaysNeeded=" + str(numFutureDaysNeeded))

            if (numFutureDaysNeeded > 0):
                # First, find the latest day with the required lab values.
                # This is the value we want to predict, so we will stop *before* this day.
                #lastTimelineIndex = len(self.CompiledTimeline) - 1
                futureDayNum = TDF_INVALID_VALUE
                while (lastTimelineIndex >= firstTimelineIndex):
                    #print("Look at future data. lastTimelineIndex=" + str(lastTimelineIndex))
                    timelineEntry = self.CompiledTimeline[lastTimelineIndex]
                    futureDataValues = timelineEntry['data']
                    if ((NameOfFutureLabValue == ANY_EVENT_OR_VALUE) or (NameOfFutureLabValue in futureDataValues)):
                        futureDayNum = timelineEntry['TimeDays']
                        #print("Found future date with the info. futureDayNum=" + str(futureDayNum))
                        break
                    lastTimelineIndex = lastTimelineIndex - 1
                # End - while (lastTimelineIndex >= firstTimelineIndex)

                futureDayNum = futureDayNum - numFutureDaysNeeded
                if (futureDayNum < 0):
                    #print("GetBoundsForDataFetch. Clipping. futureDayNum=" + str(futureDayNum))
                    return TDF_INVALID_VALUE, TDF_INVALID_VALUE

                # Clip to a date that can predict sufficiently far ahead.        
                while (lastTimelineIndex >= firstTimelineIndex):
                    timelineEntry = self.CompiledTimeline[lastTimelineIndex]
                    currentDayNum = timelineEntry['TimeDays']
                    #print("Look at possible days. currentDayNum=" + str(currentDayNum))
                    if (futureDayNum >= currentDayNum):
                        #print("Found new max day. currentDayNum=" + str(currentDayNum))
                        break
                    lastTimelineIndex = lastTimelineIndex - 1
                # End - while (lastTimelineIndex >= firstTimelineIndex):

                if (lastTimelineIndex < firstTimelineIndex):
                    #print("GetBoundsForDataFetch. Clipping. lastTimelineIndex=" + str(lastTimelineIndex))
                    #print("GetBoundsForDataFetch. Clipping. futureDayNum=" + str(futureDayNum))
                    return TDF_INVALID_VALUE, TDF_INVALID_VALUE
            # End - if (numFutureDaysNeeded > 0)    
        # End - if (NameOfFutureLabValues != ""):

        return firstTimelineIndex, lastTimelineIndex
    # End - GetBoundsForDataFetch





    #####################################################
    #
    # [TDFFileReader::GetNamedValueFromTimeline]
    #
    #####################################################
    def GetNamedValueFromTimeline(self, valueName, offset, 
                                functionObject, timeLineIndex, timelineEntry, currentDayNum):
        fDebug = False
        result = TDF_INVALID_VALUE
        fFoundIt = False

        if (fDebug):
            print("GetNamedValueFromTimeline. valueName=" + str(valueName) + ", offset=" + str(offset))
            print("GetNamedValueFromTimeline. functionObject=" + str(functionObject))
            print("GetNamedValueFromTimeline. timelineEntry = " + str(timelineEntry))

        ############################
        # This is the simple case, we want a value from the current position in the timeline
        # Or, is this uses a function that is the relative change, then we also need the latest
        if ((offset == 0) or (functionObject is not None)):
            latestValues = timelineEntry['data']
            if (valueName not in latestValues):
                return False, TDF_INVALID_VALUE

            result = latestValues[valueName]
            if (TDF_INVALID_VALUE == result):
                return False, TDF_INVALID_VALUE

            if (fDebug):
                print("GetNamedValueFromTimeline. result = " + str(result))

            # If there is no function, then we are done.
            if (functionObject is not None):
                dayNum = timelineEntry['TimeDays']
                timeMin = 0
                #timeMin = timelineEntry['TimeIntervalNum'] * self.MinutesPerTimelineEntry
                #if (timeMin >= 1440): # 24*60 = 1440
                #    timeMin = 1440
                #if (timeMin < 0):
                #    timeMin = 0
                if (fDebug):
                    print("GetNamedValueFromTimeline. Apply function for value " + valueName + ", init value=" + str(result))
                    #print("GetNamedValueFromTimeline. functionObject=" + str(functionObject))
                result = functionObject.ComputeNewValue(result, dayNum, timeMin)
                if (fDebug):
                    print("GetNamedValueFromTimeline. Function returns result=" + str(result))

                # This normally just means the function may just not have enough historical
                # data to give a meaningful result.
                if (result == TDF_INVALID_VALUE):
                    if (fDebug):
                        print("GetNamedValueFromTimeline. Function returned TDF_INVALID_VALUE")
                    return False, TDF_INVALID_VALUE

                if (fDebug):
                    print("GetNamedValueFromTimeline. Apply function for value " + valueName + "output=" + str(result))
            # End - if (functionObject is not None):

            return True, result
        # End - if (offset == 0):

        
        targetDayNum = currentDayNum + offset
        if (fDebug):
            print("GetNamedValueFromTimeline. currentDayNum=" + str(currentDayNum) + ", offset=" + str(offset) 
                    + ", targetDayNum=" + str(targetDayNum))


        ############################
        # If offset<0, then we want a value from a previous position in the timeline.
        if (offset < 0):
            # We may search to before the current window. That is ok.
            # The point of a past lab value is to get a trend, or baseline, and
            # that should not be clipped to a single event, like one hospital admission.
            pastTimeLineIndex = timeLineIndex
            while (pastTimeLineIndex >= 0):
                pastTimelineEntry = self.CompiledTimeline[pastTimeLineIndex]
                pastDayNum = pastTimelineEntry['TimeDays']
                #print("GetNamedValueFromTimeline. pastDayNum=" + str(pastDayNum))
                if (pastDayNum <= targetDayNum):
                    # Don't do anything if we are too far back. If I want a lab from
                    # 30 days before now, don't confuse this with a lab 6 years ago.
                    if ((targetDayNum - pastDayNum) >= MAX_PREVIOUS_LAB_EXTRA_PREVIOUS):
                        #print("GetNamedValueFromTimeline. Too far back. pastDayNum=" + str(pastDayNum))
                        return False, TDF_INVALID_VALUE

                    pastLabValues = pastTimelineEntry['data']
                    if (valueName in pastLabValues):
                        #print("GetNamedValueFromTimeline. valueName is in prevDay. pastDayNum=" + str(pastDayNum))
                        result = pastLabValues[valueName]                        
                        if (TDF_INVALID_VALUE != result):
                            fFoundIt = True
                            break
                # End - if (pastDayNum <= targetDayNum):

                pastTimeLineIndex = pastTimeLineIndex - 1
            # End - while (pastTimeLineIndex >= 0):
        # End - if (offset < 0):


        ############################
        # If offset>0, then we want a value from a future position in the timeline.
        if (offset > 0):
            # We may search past the current window. That is ok.
            futureTimeLineIndex = timeLineIndex

            while (futureTimeLineIndex <= self.LastTimeLineIndex):
                futureTimelineEntry = self.CompiledTimeline[futureTimeLineIndex]
                futureDayNum = futureTimelineEntry['TimeDays']
                #print("GetNamedValueFromTimeline. futureDayNum=" + str(futureDayNum))

                if (futureDayNum >= targetDayNum):
                    # Don't do anything if we are too far ahead. If I want a lab from
                    # 3 days after now, don't confuse this with a lab 6 years in the future
                    if ((futureDayNum - targetDayNum) >= MAX_PREVIOUS_LAB_EXTRA_FUTURE):
                        #print("GetNamedValueFromTimeline. Too far ahead. futureDayNum=" + str(futureDayNum))
                        return False, TDF_INVALID_VALUE

                    futureLabValues = futureTimelineEntry['data']
                    if (valueName in futureLabValues):
                        #print("GetNamedValueFromTimeline. valueName is in future. futureDayNum=" + str(futureDayNum))
                        result = futureLabValues[valueName]
                        if (TDF_INVALID_VALUE != result):
                            fFoundIt = True
                            break
                # End - if (futureDayNum >= targetDayNum):

                futureTimeLineIndex += 1
            # End - while (futureTimeLineIndex <= self.lastTimeLineIndex):
        # End - if (offset > 0):

        return fFoundIt, result
    # End - GetNamedValueFromTimeline





    #####################################################
    #
    # [TDFFileReader::CheckIfCurrentTimeMeetsCriteria]
    #
    #####################################################
    def CheckIfCurrentTimeMeetsCriteria(self, 
                                        propertyRelationList, 
                                        propertyNameList, 
                                        propertyValueList, 
                                        timeLineIndex,
                                        timelineEntry,
                                        currentDayNum):
        fDebug = False
        latestValues = timelineEntry['data']

        numProperties = len(propertyNameList)                                                
        for propNum in range(numProperties):
            valueName = propertyNameList[propNum]
            if (valueName not in latestValues):
                return(False)

            actualVal = latestValues[valueName]
            if ((actualVal == TDF_INVALID_VALUE) or (actualVal <= TDF_SMALLEST_VALID_VALUE)):
                return(False)

            targetVal = float(propertyValueList[propNum])
            relationName = propertyRelationList[propNum]
            try:
                labInfo = g_LabValueInfo[valueName]
            except Exception:
                print("Error! CheckIfCurrentTimeMeetsCriteria found undefined lab name: " + valueName)
                return(False)
            dataTypeName = labInfo['dataType']
            if (fDebug):
                print("CheckIfCurrentTimeMeetsCriteria: dataTypeName=" + TDF_GetDataTypeName(dataTypeName))
                print("CheckIfCurrentTimeMeetsCriteria: targetVal=" + str(targetVal))
                print("CheckIfCurrentTimeMeetsCriteria: actualVal=" + str(actualVal))

            ###############
            if (relationName == ".EQ."):
                if (dataTypeName == TDF_DATA_TYPE_FLOAT):
                    if (float(actualVal) != float(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                elif ((dataTypeName == TDF_DATA_TYPE_INT) or (dataTypeName == TDF_DATA_TYPE_FUTURE_EVENT_CLASS)):
                    if (int(actualVal) != int(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                elif (dataTypeName == TDF_DATA_TYPE_BOOL):
                    if (int(actualVal) != int(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
            ###############
            elif (relationName == ".NEQ."):
                if (dataTypeName == TDF_DATA_TYPE_FLOAT):
                    if (float(actualVal) == float(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                elif ((dataTypeName == TDF_DATA_TYPE_INT) or (dataTypeName == TDF_DATA_TYPE_FUTURE_EVENT_CLASS)):
                    if (int(actualVal) == int(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
            ###############
            elif (relationName == ".LT."):
                if (dataTypeName == TDF_DATA_TYPE_FLOAT):
                    if (float(actualVal) >= float(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                elif ((dataTypeName == TDF_DATA_TYPE_INT) or (dataTypeName == TDF_DATA_TYPE_FUTURE_EVENT_CLASS)):
                    if (int(actualVal) >= int(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
            ###############
            elif (relationName == ".LTE."):
                if (dataTypeName == TDF_DATA_TYPE_FLOAT):
                    if (float(actualVal) > float(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                elif ((dataTypeName == TDF_DATA_TYPE_INT) or (dataTypeName == TDF_DATA_TYPE_FUTURE_EVENT_CLASS)):
                    if (int(actualVal) > int(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
            ###############
            elif (relationName == ".GT."):
                if (dataTypeName == TDF_DATA_TYPE_FLOAT):
                    if (float(actualVal) <= float(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                elif ((dataTypeName == TDF_DATA_TYPE_INT) or (dataTypeName == TDF_DATA_TYPE_FUTURE_EVENT_CLASS)):
                    if (int(actualVal) <= int(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                #print("Check Filter. dataTypeName=" + str(dataTypeName))
                #print("Check Filter. actualVal=" + str(actualVal))
                #print("Check Filter. targetVal=" + str(targetVal))
            ###############
            elif (relationName == ".GTE."):
                if (dataTypeName == TDF_DATA_TYPE_FLOAT):
                    if (float(actualVal) < float(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
                elif ((dataTypeName == TDF_DATA_TYPE_INT) or (dataTypeName == TDF_DATA_TYPE_FUTURE_EVENT_CLASS)):
                    if (int(actualVal) < int(targetVal)):
                        if (fDebug):
                            print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                        return(False)
            ###############
            else:
                if (fDebug):
                    print("CheckIfCurrentTimeMeetsCriteria: targetVal does not match required value")
                return(False)
        # End - for propNum in range(numProperties):

        if (fDebug):
            print("CheckIfCurrentTimeMeetsCriteria: targetVal does indeed match required value")
        return(True)
    # End - CheckIfCurrentTimeMeetsCriteria





    #####################################################
    #
    # [TDFFileReader::GetDataForCurrentPatient]
    #
    # This returns two Numpy Arrays:
    #   - The first is an array of inputs. This is an NxM array
    #           Each column is 1 timestep, and each array is one input variable.
    #
    #   - The second is an array of results. This is an Nx1 array.
    #           It is the result at each time step
    #
    # This method is NOT part of DataSet - it is a special iterator
    #####################################################
    def GetDataForCurrentPatient(self, 
                                requirePropertyRelationList,
                                requirePropertyNameList,
                                requirePropertyValueList,
                                fAddMinibatchDimension,
                                minIntervalInHours):
        fDebug = False
        prevResultValue = TDF_INVALID_VALUE
        numRequireProperties = len(requirePropertyNameList)

        if (fDebug):
            print("GetDataForCurrentPatient, start")
            print("GetDataForCurrentPatient, self.allValueVarNameList=" + str(self.allValueVarNameList))
            #print("GetDataForCurrentPatient, self.allValuesLabInfoList=" + str(self.allValuesLabInfoList))
            print("GetDataForCurrentPatient, self.allValueOffsets=" + str(self.allValueOffsets))
            print("GetDataForCurrentPatient, self.allValuesFunctionNameList=" + str(self.allValuesFunctionNameList))
            print("GetDataForCurrentPatient, self.allValuesFunctionObjectList=" + str(self.allValuesFunctionObjectList))

        # Find where we will look for the data. We may not consider data values
        # that run right up to the end.        
        firstTimelineIndex, lastTimelineIndex = self.GetBoundsForDataFetch(self.resultLabInfo)
        if (firstTimelineIndex < 0):
            if (fDebug):
                print("GetDataForCurrentPatient, No data. firstTimelineIndex=" + str(firstTimelineIndex))
            return 0, None, None

        # Count the max possible number of complete data nodes.
        # We may return less than this, but this lets us allocate result storage.
        maxNumCompleteLabSets = (lastTimelineIndex - firstTimelineIndex) + 1
        if (maxNumCompleteLabSets <= 0):
            if (fDebug):
                print("GetDataForCurrentPatient, No data. maxNumCompleteLabSets=" + str(maxNumCompleteLabSets))
            return 0, None, None

        # Make a vector big enough to hold all possible labs.
        # We will likely not need all of this space, but there is enough
        # room for the most extreme case.
        if (fAddMinibatchDimension):
            inputArray = np.zeros((maxNumCompleteLabSets, 1, self.numInputValues))
            resultArray = np.zeros((maxNumCompleteLabSets, 1, 1))
        else:
            inputArray = np.zeros((maxNumCompleteLabSets, self.numInputValues))
            resultArray = np.zeros((maxNumCompleteLabSets, 1))

        # Initialize all time function objects
        # Things like velocity and acceleration start at an initial state for each different patient
        for nameIndex, functionObject in enumerate(self.allValuesFunctionObjectList):
            if (functionObject is not None):
                functionObject.Reset()

        # This loop will iterate over each step in the timeline.
        timeLineIndex = firstTimelineIndex
        numReturnedDataSets = 0
        lastHourReturned = TDF_INVALID_VALUE
        while (timeLineIndex <= lastTimelineIndex):
            if (fDebug):
                print("GetDataForCurrentPatient loop. timeLineIndex=" + str(timeLineIndex))

            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            currentMinuteInDay = timelineEntry['TimeIntervalNum'] * self.MinutesPerTimelineEntry
            currentHour = currentMinuteInDay / 60
            #currentMin = currentMinuteInDay - (currentHour * 60)
            if (fDebug):
                print("GetDataForCurrentPatient. timelineEntry=" + str(timelineEntry))

            # We may keep high frequency data, like vitals, along with low frequency data
            # like Cr. If a value is missing, we always use the most recent past value, which
            # can make low frequency data like Cr still return a series like high frequency data.
            # We want to avoid that, so skip values that happen more frequently than we want.
            # HOWEVER. We take the latest value in each bucket, so the latest lab value in that
            # day. This prevents a vitals recorded at just after midnight (with still the previous days labs)
            # from blocking more recent labs drawn later in the day (like on morning lab draws).
            fOverwriteLatestLabs = False
            if ((lastHourReturned > 0) and (minIntervalInHours > 0) 
                    and (((currentDayNum * 24) + currentHour) < (lastHourReturned + minIntervalInHours))):
                fOverwriteLatestLabs = True
                if (fDebug):
                    print("GetDataForCurrentPatient. Overwrite. lastHourReturned=" + str(lastHourReturned))
                    print("GetDataForCurrentPatient. Overwrite. currentDayNum=" + str(currentDayNum))
                    print("GetDataForCurrentPatient. Overwrite. currentHour=" + str(currentHour))
                    print("GetDataForCurrentPatient. Overwrite. minIntervalInHours=" + str(minIntervalInHours))

            # Check if there are additional requirements for a timeline entry.
            # Do this BEFORE we actually try to read the properties. It may save us the work
            # of getting properties only to throw them away.
            fOKToUseTimepoint = True
            if (numRequireProperties > 0):
                if (fDebug):
                    print("Check required properties. numRequireProperties=" + str(numRequireProperties))
                    print("Check required properties. requirePropertyRelationList=" + str(requirePropertyRelationList))
                    print("Check required properties. requirePropertyNameList=" + str(requirePropertyNameList))
                    print("Check required properties. requirePropertyValueList=" + str(requirePropertyValueList))
                fOKToUseTimepoint = self.CheckIfCurrentTimeMeetsCriteria(requirePropertyRelationList,
                                                        requirePropertyNameList,
                                                        requirePropertyValueList,
                                                        timeLineIndex, 
                                                        timelineEntry, 
                                                        currentDayNum)

            # Find the labs we are looking for.
            # There are often lots of labs, but this only return labs that are relevant.
            if (fOKToUseTimepoint):
                if (fDebug):
                    print("GetDataForCurrentPatient. fOKToUseTimepoint=" + str(fOKToUseTimepoint))

                foundAllInputs = True
                for valueIndex in range(self.numInputValues):
                    # Get information about the lab.
                    try:
                        valueName = self.allValueVarNameList[valueIndex]
                    except Exception:
                        if (fDebug):
                            print("Error! GetDataForCurrentPatient found undefined lab name: " + valueName)
                        foundAllInputs = False
                        break

                    # Get the lab value itself.
                    foundIt, result = self.GetNamedValueFromTimeline(valueName, self.allValueOffsets[valueIndex],
                                                                    self.allValuesFunctionObjectList[valueIndex],
                                                                    timeLineIndex, timelineEntry, currentDayNum)
                    if (not foundIt):
                        if (fDebug):
                            print("GetDataForCurrentPatient. Could not find valueName=" + str(valueName))
                        foundAllInputs = False
                        break

                    try:
                        if (fOverwriteLatestLabs):
                            if (fAddMinibatchDimension):
                                inputArray[numReturnedDataSets][0][valueIndex] = result
                            else:
                                inputArray[numReturnedDataSets][valueIndex] = result
                        else:
                            if (fAddMinibatchDimension):
                                inputArray[numReturnedDataSets][0][valueIndex] = result
                            else:
                                inputArray[numReturnedDataSets][valueIndex] = result
                    except Exception:
                        print("GetDataForCurrentPatient. EXCEPTION when writing one value")
                        print("GetDataForCurrentPatient. valueName=" + valueName + ", fOverwriteLatestLabs=" + str(fOverwriteLatestLabs))
                        print("GetDataForCurrentPatient. fAddMinibatchDimension=" + str(fAddMinibatchDimension))
                        print("numReturnedDataSets=" + str(numReturnedDataSets) + ", valueIndex=" + str(valueIndex))
                        print("maxNumCompleteLabSets=" + str(maxNumCompleteLabSets) + ", self.numInputValues=" + str(self.numInputValues))
                        print("GetDataForCurrentPatient. inputArray.shape=" + str(inputArray.shape))
                        sys.exit(0)

                    if (fDebug):
                        print("GetDataForCurrentPatient. valueName=" + valueName + ", index=" + str(valueIndex) + ", value=" + str(result))
                        print("GetDataForCurrentPatient. result=" + str(result))
                # End - for valueIndex, valueName in enumerate(self.allValueVarNameList):
            # End - if (fOKToUseTimepoint)
            else:
                foundAllInputs = False

            # If we did not find all of the Input values here, move on and try the next timeline position.
            if (not foundAllInputs):
                timeLineIndex += 1
                continue

            # Now, try to get the result for this time step.
            # Note, this is NOT normalized. That is a category ID, or exact value like INR, 
            # so we want the actual numeric value, not a normalized version.            
            foundResult, result = self.GetNamedValueFromTimeline(self.resultValueName, 
                                                                self.resultValueOffset, None,
                                                                timeLineIndex, timelineEntry, currentDayNum)

            # Only return interers/floats that are unique values. So, remove dups.
            # But, only do this for ints and floats. NOT for TDF_DATA_TYPE_FUTURE_EVENT_CLASS 
            # or TDF_DATA_TYPE_BOOL
            if ((self.resultDataType == TDF_DATA_TYPE_INT) or (self.resultDataType == TDF_DATA_TYPE_FLOAT)):
                if ((foundResult) and (prevResultValue > TDF_SMALLEST_VALID_VALUE) and (result == prevResultValue)):
                    foundResult = False
            # End - if ((foundIt) and (prevResultValue > TDF_SMALLEST_VALID_VALUE) and (result == prevResultValue)):
            prevResultValue = result

            # If we found all values, then assemble the next vector of results.
            if (foundResult):
                if (fDebug):
                    print("GetDataForCurrentPatient. Got inputs and result. foundResult=" + str(foundResult))    
                    print("GetDataForCurrentPatient. found self.resultValueName: " + str(self.resultValueName))

                if (fOverwriteLatestLabs):
                    if (fAddMinibatchDimension):
                        resultArray[numReturnedDataSets][0][0] = result
                    else:
                        resultArray[numReturnedDataSets][0] = result
                else:
                    if (fAddMinibatchDimension):
                        resultArray[numReturnedDataSets][0][0] = result
                    else:
                        resultArray[numReturnedDataSets][0] = result
                    numReturnedDataSets += 1
                    if (numReturnedDataSets >= maxNumCompleteLabSets):
                        break
                    lastHourReturned = (currentDayNum * 24) + currentHour
                # End - if (foundAllInputs):

            timeLineIndex += 1
        # End - while (timeLineIndex <= lastTimelineIndex)

        if (numReturnedDataSets <= 0):
            if (fDebug):
                print("GetDataForCurrentPatient, numReturnedDataSets is 0 (" + str(numReturnedDataSets) + ")")
            return 0, None, None
        # End - if (numReturnedDataSets <= 0):

        if (fDebug):
            print("GetDataForCurrentPatient. numReturnedDataSets=" + str(numReturnedDataSets))

        if (numReturnedDataSets > maxNumCompleteLabSets):
            TDF_Log("ERROR! numReturnedDataSets != numCompleteLabSets")
            numReturnedDataSets = maxNumCompleteLabSets

        # The client expects that the returned arrays will be the exact size.
        # We have to return a full array, without any unused rows.
        if (fAddMinibatchDimension):
            inputArray = inputArray[:numReturnedDataSets, :1, :self.numInputValues]
            resultArray = resultArray[:numReturnedDataSets, :1, :1]
        else:
            inputArray = inputArray[:numReturnedDataSets, :self.numInputValues]
            resultArray = resultArray[:numReturnedDataSets, :1]

        if (fDebug):
            print("GetDataForCurrentPatient. inputArray = " + str(inputArray))
            #sys.exit(0)

        return numReturnedDataSets, inputArray, resultArray
    # End - GetDataForCurrentPatient()




    #####################################################
    #
    # [TDFFileReader::CmpValueForCurrentPatient]
    #
    #####################################################
    def CmpValueForCurrentPatient(self, valueName, compareValue):
        fDebug = False
        if (fDebug):
            print("CmpValueForCurrentPatient. valueName=" + valueName + ", compareValue=" + str(compareValue))

        # This loop will iterate over each step in the timeline.
        timeLineIndex = 0
        while (timeLineIndex <= self.LastTimeLineIndex):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            if (fDebug):
                print("CmpValueForCurrentPatient loop. timeLineIndex=" + str(timeLineIndex))
                print("CmpValueForCurrentPatient. timelineEntry=" + str(timelineEntry))

            # Get the lab value itself.
            foundIt, result = self.GetNamedValueFromTimeline(valueName, 0, None,
                                                            timeLineIndex, timelineEntry, currentDayNum)
            if (foundIt):
                if (fDebug):
                    print("CmpValueForCurrentPatient Found Value. result=" + str(result))
                if (result == compareValue):
                    if (fDebug):
                        print("CmpValueForCurrentPatient Found Matching")
                        print("\n\nBAIL\n\n")
                        sys.exit(0)
                    return True
            # End - if (foundIt)

            timeLineIndex += 1
        # End - while (timeLineIndex <= self.LastTimeLineIndex)

        return False
    # End - CmpValueForCurrentPatient()





    #####################################################
    #
    # [TDFFileReader::GetSyncedPairOfValueListsForCurrentPatient]
    #
    # This returns two lists of values, and is used when we compute 
    # correlations
    #####################################################
    def GetSyncedPairOfValueListsForCurrentPatient(self, 
                                    nameStem1, 
                                    valueOffset1, 
                                    functionObject1, 
                                    fAllowDupsInVar1, 
                                    nameStem2, 
                                    valueOffset2, 
                                    functionObject2,
                                    fAllowDupsInVar2,
                                    requirePropertyNameList,
                                    requirePropertyRelationList,
                                    requirePropertyValueList):
        fDebug = False
        numRequireProperties = len(requirePropertyNameList)
        foundPrevValues = False
        prevValue1 = TDF_INVALID_VALUE
        prevValue2 = TDF_INVALID_VALUE
        valueList1 = []
        valueList2 = []

        fAllowDupsInVar1 = True
        fAllowDupsInVar2 = True

        if (fDebug):
            print("GetSyncedPairOfValueListsForCurrentPatient")

        # Initialize the time function objects
        # Things like velocity and acceleration start at an initial state for each different patient
        if (functionObject1 is not None):
            functionObject1.Reset()
        if (functionObject2 is not None):
            functionObject2.Reset()

        # This loop will iterate over each step in the timeline.
        numEntriesChecked = 0
        entryWithFirstFinding = -1
        numValuePairsIncludingDups = 0
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            if (fDebug):
                print("GetSyncedPairOfValueListsForCurrentPatient. timeLineIndex=" + str(timeLineIndex))
                print("GetSyncedPairOfValueListsForCurrentPatient. timelineEntry=" + str(timelineEntry))

            # Check if this is a timeline entry we care about.
            # For example, we may only care about labs while a patient is in the hospital,
            # or labes for a patient with a minimal level of kidney disease.
            if (numRequireProperties > 0):
                foundNewValue = self.CheckIfCurrentTimeMeetsCriteria(requirePropertyRelationList,
                                                                    requirePropertyNameList,
                                                                    requirePropertyValueList,
                                                                    timeLineIndex, 
                                                                    timelineEntry, 
                                                                    currentDayNum)
                if not foundNewValue:
                    continue
            # End - if (numRequireProperties > 0):
            numEntriesChecked += 1

            # Find the labs we are looking for.
            foundNewValue, value1 = self.GetNamedValueFromTimeline(nameStem1, valueOffset1, functionObject1,
                                                                   timeLineIndex, timelineEntry, currentDayNum)
            if not foundNewValue:
                continue

            foundNewValue, value2 = self.GetNamedValueFromTimeline(nameStem2, valueOffset2, functionObject2,
                                                                   timeLineIndex, timelineEntry, currentDayNum)
            if not foundNewValue:
                continue

            # If we found both values, make sure this is not a repeat.
            # We may carry past values forward every time there is new data, like
            # new vital signs. As a result, a slower changing lab may be repeated many 
            # times until a true new value appears.
            # We use the fact that both values are identical to indicate this is a repeat.
            # This may rarely miss a true case of identical values at different times, but
            # that is rare.
            numValuePairsIncludingDups += 1
            if (foundPrevValues):
                if ((not fAllowDupsInVar1) and (prevValue1 == value1)):
                    if (fDebug):
                        print("GetSyncedPairOfValueListsForCurrentPatient. skip dups in value1: " + nameStem1)
                    continue
                if ((not fAllowDupsInVar2) and (prevValue2 == value2)):
                    if (fDebug):
                        print("GetSyncedPairOfValueListsForCurrentPatient. skip dups in value2: " + nameStem2)
                    continue
            # End - if (foundPrevValues)

            if (entryWithFirstFinding < 0):
                entryWithFirstFinding = numEntriesChecked

            foundPrevValues = True
            prevValue1 = value1
            prevValue2 = value2

            valueList1.append(value1)
            valueList2.append(value2)

            if (fDebug):
                print("GetSyncedPairOfValueListsForCurrentPatient. Found pair of values. value1=" 
                        + str(value1) + ", value2=" + str(value2))
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1)

        if (fDebug):
            print("GetSyncedPairOfValueListsForCurrentPatient. valueList1 = " + str(valueList1))
            print("GetSyncedPairOfValueListsForCurrentPatient. valueList2 = " + str(valueList2))

        if ((fDebug) and (entryWithFirstFinding >= 0)):
            print("GetSyncedPairOfValueListsForCurrentPatient: numEntriesChecked=" + str(numEntriesChecked) 
                    + ", entryWithFirstFinding=" + str(entryWithFirstFinding))
            print("    numValuePairsIncludingDups=" + str(numValuePairsIncludingDups))

        return valueList1, valueList2
    # End - GetSyncedPairOfValueListsForCurrentPatient()






    #####################################################
    #
    # [TDFFileReader::GetValueStdDevForConditionsForOnePatient]
    #
    #####################################################
    def GetValueStdDevForConditionsForOnePatient(self, 
                                    varForStdDev,
                                    varForCondition,
                                    listOfBuckets,
                                    numHistogramBuckets):
        fDebug = False

        # This loop will iterate over each step in the timeline.
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            if (fDebug):
                print("GetValueStdDevForConditionsForOnePatient. timeLineIndex=" + str(timeLineIndex))
                print("GetValueStdDevForConditionsForOnePatient. timelineEntry=" + str(timelineEntry))

            # Find the labs we are looking for.
            foundValueForStdDev, value = self.GetNamedValueFromTimeline(varForStdDev, 0, None,
                                                                timeLineIndex, timelineEntry, currentDayNum)
            if not foundValueForStdDev:
                continue

            foundValueForCondition, valueForCondition = self.GetNamedValueFromTimeline(varForCondition, 0, None,
                                                                 timeLineIndex, timelineEntry, currentDayNum)
            if not foundValueForCondition:
                continue

            if (fDebug):
                print("GetValueStdDevForConditionsForOnePatient. Found pair of values. value=" + str(value) 
                                    + ", valueForCondition=" + str(valueForCondition))

            # Look for the new condition.
            for bucketIndex, bucketInfo in enumerate(listOfBuckets.items()):
                if ((valueForCondition >= bucketInfo['min'])
                        and (valueForCondition < bucketInfo['max'])):
                    break
            # End - for bucketIndex, bucketInfo in enumerate(listOfBuckets.items()):
            if (bucketIndex >= numHistogramBuckets):
                print("ERROR. Could not find bucket for valueForCondition = " + str(valueForCondition))
                sys.exit(0)
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1)
    # End - GetValueStdDevForConditionsForOnePatient()






    #####################################################
    #
    # [TDFFileReader::GetValuePairsForCurrentPatient]
    #
    #####################################################
    def GetValuePairsForCurrentPatient(self, 
                                    xValueName,
                                    yValueName,
                                    resultDict,
                                    requirePropertyNameList,
                                    requirePropertyRelationList,
                                    requirePropertyValueList):
        fDebug = False
        numRequireProperties = len(requirePropertyNameList)


        # Get information about the requested variables. This splits
        # complicated name values like "eGFR[-30]" into a name and an 
        # offset, like "eGFR" and "-30"
        xLabInfo, xNameStem, xValueOffset, xFunctionName = TDF_ParseOneVariableName(xValueName)
        if (xLabInfo is None):
            TDF_Log("!Error! Cannot parse variable: " + xValueName)
            return None, None
        yLabInfo, yNameStem, yValueOffset, yFunctionName = TDF_ParseOneVariableName(yValueName)
        if (yLabInfo is None):
            TDF_Log("GetValuePairsForCurrentPatient Error! Cannot parse variable: " + yValueName)
            return None, None

        xFunctionObject = None
        if (xFunctionName != ""):
            xFunctionObject = timefunc.CreateTimeValueFunction(xFunctionName, xNameStem)
            if (xFunctionObject is None):
                print("GetValuePairsForCurrentPatient ERROR!! Undefined function: " + xFunctionName)
                sys.exit(0)
        yFunctionObject = None
        if (yFunctionName != ""):
            yFunctionObject = timefunc.CreateTimeValueFunction(yFunctionName, yNameStem)
            if (yFunctionObject is None):
                print("GetValuePairsForCurrentPatient ERROR!! Undefined function: " + yFunctionName)
                sys.exit(0)


        # This loop will iterate over each step in the timeline.
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            if (fDebug):
                print("GetValuePairsForCurrentPatient. timeLineIndex=" + str(timeLineIndex))
                print("GetValuePairsForCurrentPatient. timelineEntry=" + str(timelineEntry))

            # Check if this is a timeline entry we care about.
            # For example, we may only care about labs while a patient is in the hospital,
            # or labes for a patient with a minimal level of kidney disease.
            if (numRequireProperties > 0):
                foundNewValue = self.CheckIfCurrentTimeMeetsCriteria(requirePropertyRelationList,
                                                                    requirePropertyNameList,
                                                                    requirePropertyValueList,
                                                                    timeLineIndex, 
                                                                    timelineEntry, 
                                                                    currentDayNum)
                if not foundNewValue:
                    continue
            # End - if (numRequireProperties > 0):

            # Find the labs we are looking for.
            foundXValue, xValue = self.GetNamedValueFromTimeline(xNameStem, xValueOffset, xFunctionObject,
                                                                   timeLineIndex, timelineEntry, currentDayNum)
            if not foundXValue:
                continue

            foundYValue, yValue = self.GetNamedValueFromTimeline(yNameStem, yValueOffset, yFunctionObject,
                                                                   timeLineIndex, timelineEntry, currentDayNum)
            if not foundYValue:
                continue

            if (xValue in resultDict):
                dictEntry = resultDict[xValue]
            else:
                dictEntry = {'numVals': 0, 'total': 0}

            dictEntry['numVals'] += 1
            dictEntry['total'] += yValue
            resultDict[xValue] = dictEntry

            if (fDebug):
                print("GetValuePairsForCurrentPatient. Found pair of values. xValue=" + str(xValue) + ", yValue=" + str(yValue))
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1)

        return resultDict
    # End - GetValuePairsForCurrentPatient()






    #####################################################
    #
    # [TDFFileReader::GetValueReproducibility]
    #
    #####################################################
    def GetValueReproducibility(self, 
                                valueName,
                                maxMinutes,
                                histogramBuckets,
                                numHistogramBuckets,
                                rangePerHistogramBucket,
                                lowestHistogramBucket):
        fDebug = False


        ########################################
        # This loop will iterate over each step in the timeline.
        prevDayNum = 0
        prevMinuteBucketNum = 0
        prevValue = TDF_INVALID_VALUE
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            currentMinuteBucketNum = timelineEntry['TimeIntervalNum']
            if (fDebug):
                print("GetValueReproducibility. timeLineIndex=" + str(timeLineIndex) + ", timelineEntry=" + str(timelineEntry))

            # Find the labs we are looking for.
            latestValues = timelineEntry['data']
            if (valueName not in latestValues):
                continue
            try:
                currentValue = float(latestValues[valueName])
            except Exception:
                currentValue = TDF_INVALID_VALUE
            if ((currentValue == TDF_INVALID_VALUE) or (currentValue <= TDF_SMALLEST_VALID_VALUE)):
                continue

            if ((prevValue != TDF_INVALID_VALUE) and (prevDayNum == currentDayNum)):
                deltaMinutes = currentMinuteBucketNum - prevMinuteBucketNum
                if ((deltaMinutes > 0) and (deltaMinutes <= maxMinutes)):
                    deltaValue = currentValue - prevValue
                    if (deltaValue < lowestHistogramBucket):
                        deltaValue = lowestHistogramBucket
                
                    offset = deltaValue - lowestHistogramBucket
                    bucketNum = round(offset / rangePerHistogramBucket)
                    if (bucketNum >= numHistogramBuckets):
                        bucketNum = numHistogramBuckets - 1

                    histogramBuckets[bucketNum] += 1
                # End - if (deltaMinutes <= maxMinutes):
            # End - if ((prevValue != TDF_INVALID_VALUE) and (prevDayNum == currentDayNum)):

            prevDayNum = currentDayNum
            prevMinuteBucketNum = currentMinuteBucketNum
            prevValue = currentValue
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1)

        return histogramBuckets
    # End - GetValueReproducibility()




    #####################################################
    #
    # [TDFFileReader::GetValueDynamicsForOnePatient]
    #
    #####################################################
    def GetValueDynamicsForOnePatient(self, 
                                    valueName,
                                    numHistogramBuckets,
                                    yAxisStyle,
                                    xAxisStyle,
                                    valueThreshold,
                                    fResetOnAdmissions,
                                    fResetOnTransfusions):
        fDebug = False
        listOfPreviousValueDicts = []
        listOfResultBuckets = [0] * numHistogramBuckets
        listOfNumItemsInEachBucket = [0] * numHistogramBuckets

        ########################################
        # This loop will iterate over each step in the timeline.
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            latestValues = timelineEntry['data']

            # Reset the state when we have an admission or a transfusion
            fResetState = False
            if ((fResetOnAdmissions)
                    and ("HospitalAdmitDate" in latestValues) 
                    and (latestValues["HospitalAdmitDate"] == currentDayNum)):
                fResetState = True
            # End - if (fResetOnAdmissions):
            if ((fResetOnTransfusions) 
                    and ("TransRBC" in latestValues) 
                    and (latestValues["TransRBC"] == 1)):
                fResetState = True
            # End - if (fResetOnTransfusions):

            if (fResetState):
                if (fDebug):
                    print("GetValueDynamicsForOnePatient. Reset state")

                listOfResultBuckets, listOfNumItemsInEachBucket = self.AddToValueDynamicsList(
                                            listOfPreviousValueDicts,
                                            numHistogramBuckets,
                                            yAxisStyle,
                                            xAxisStyle,
                                            valueThreshold,
                                            listOfResultBuckets,
                                            listOfNumItemsInEachBucket)
                listOfPreviousValueDicts = []
            # End - if (fResetState):

            # Find the labs we are looking for.
            if ((valueName not in latestValues) or (latestValues[valueName] == TDF_INVALID_VALUE)
                    or (latestValues[valueName] <= TDF_SMALLEST_VALID_VALUE)):
                continue

            currentValue = float(latestValues[valueName])
            listOfPreviousValueDicts.append({'d': currentDayNum, 'v': currentValue})
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1)

        # Add the last list of values we were adding up before we hit the end of all values.
        # If we do not reset during the middle of a sequence of values, then this may be
        # the only time we add values.
        listOfResultBuckets, listOfNumItemsInEachBucket = self.AddToValueDynamicsList(
                                                    listOfPreviousValueDicts,
                                                    numHistogramBuckets,
                                                    yAxisStyle,
                                                    xAxisStyle,
                                                    valueThreshold,
                                                    listOfResultBuckets,
                                                    listOfNumItemsInEachBucket)

        return listOfResultBuckets, listOfNumItemsInEachBucket
    # End - GetValueDynamicsForOnePatient()





    #####################################################
    #
    # [TDFFileReader::AddToValueDynamicsList]
    #
    #####################################################
    def AddToValueDynamicsList(self, 
                                listOfPreviousValueDicts,
                                numHistogramBuckets,
                                yAxisStyle,
                                xAxisStyle,
                                valueThreshold,
                                listOfResultBuckets,
                                listOfNumItemsInEachBucket):
        fDebug = False
        if (fDebug):
            print("AddToValueDynamicsList: listOfPreviousValueDicts = " + str(listOfPreviousValueDicts))
            print("AddToValueDynamicsList: numHistogramBuckets = " + str(numHistogramBuckets))
            print("AddToValueDynamicsList: listOfResultBuckets = " + str(listOfResultBuckets))
            print("AddToValueDynamicsList: listOfNumItemsInEachBucket = " + str(listOfNumItemsInEachBucket))



        mean = TDF_INVALID_VALUE
        if ((yAxisStyle == "StdDev") or (yAxisStyle == "Var")):
            listLength = len(listOfPreviousValueDicts)
            if (listLength <= 0):
                return listOfResultBuckets, listOfNumItemsInEachBucket
            mean = sum(entry['v'] for entry in listOfPreviousValueDicts) / listLength
            if (fDebug):
                print("AddToValueDynamicsList: mean = " + str(mean))                
        # End - if ((yAxisStyle == "StdDev") or (yAxisStyle == "Var")):


        prevDayNum = 0
        prevValue = TDF_INVALID_VALUE
        firstDayNum = TDF_INVALID_VALUE
        for index, valueDict in enumerate(listOfPreviousValueDicts):
            currentDayNum = valueDict['d']
            currentValue = valueDict['v']
            if (fDebug):
                print("valueDict = " + str(valueDict) + ", currentDayNum = " + str(currentDayNum) 
                        + ", currentValue = " + str(currentValue))

            if (firstDayNum == TDF_INVALID_VALUE):
                firstDayNum = currentDayNum

            if ((mean != TDF_INVALID_VALUE) 
                or ((prevValue != TDF_INVALID_VALUE) and (prevDayNum != currentDayNum))):
                ########################################
                # First, decide where to put a new value
                if (xAxisStyle == "SkippedDays"):
                    bucketNum = currentDayNum - prevDayNum
                ####################
                elif (xAxisStyle == "NumLabs"):
                    bucketNum = index
                ####################
                elif (xAxisStyle == "DaysSinceAdmit"):
                    bucketNum = currentDayNum - firstDayNum
                ####################
                else:
                    bucketNum = index

                if (bucketNum >= numHistogramBuckets):
                    bucketNum = numHistogramBuckets - 1
                if (fDebug):
                    print("AddToValueDynamicsList. bucketNum = " + str(bucketNum))

                ########################################
                # Next, decide what value to store and store it.
                ####################
                if ((yAxisStyle == "StdDev") or (yAxisStyle == "Var")):
                    listOfResultBuckets[bucketNum] += ((currentValue - mean) ** 2)
                    if (fDebug):
                        print("AddToValueDynamicsList. res = " + str(listOfResultBuckets[bucketNum]))
                ####################
                elif (yAxisStyle == "Delta"):
                    listOfResultBuckets[bucketNum] += (currentValue - prevValue)
                ####################
                elif (yAxisStyle == "DeltaOverThreshold"):
                    if ((currentValue - prevValue) >= valueThreshold):
                        listOfResultBuckets[bucketNum] += 1
                ####################
                elif (yAxisStyle == "ValOverThreshold"):
                    if (currentValue > valueThreshold):
                        listOfResultBuckets[bucketNum] += 1
                ####################
                elif (yAxisStyle == "ValBelowThreshold"):
                    if (currentValue < valueThreshold):
                        listOfResultBuckets[bucketNum] += 1
                ####################
                elif (yAxisStyle == "Max"):
                    valueChange = currentValue - prevValue
                    if (valueChange > listOfResultBuckets[bucketNum]):
                        listOfResultBuckets[bucketNum] = valueChange
                ####################
                else:
                    listOfResultBuckets[bucketNum] = currentValue - prevValue

                listOfNumItemsInEachBucket[bucketNum] += 1
            # End - if ((prevValue != TDF_INVALID_VALUE) and (prevDayNum != currentDayNum)):

            prevDayNum = currentDayNum
            prevValue = currentValue
        # End - for valueDict in listOfPreviousValueDicts:

        if (fDebug):
            print("AddToValueDynamicsList: listOfResultBuckets = " + str(listOfResultBuckets))
            print("AddToValueDynamicsList: listOfNumItemsInEachBucket = " + str(listOfNumItemsInEachBucket))

        return listOfResultBuckets, listOfNumItemsInEachBucket
    # End - AddToValueDynamicsList






    #####################################################
    #
    # [TDFFileReader::GetValuesBetweenDays]
    #
    # This returns one lists of values, and is used when we 
    # look for changes in the timing of values.
    #####################################################

    def GetValuesBetweenDays(self, valueName, firstDay, lastDay, fOnlyOneValuePerDay):
        foundPrevValues = False
        prevDayNum = -1
        valueList = []

        # Get information about the requested variables. This splits
        # complicated name values like "eGFR[-30]" into a name and an 
        # offset, like "eGFR" and "-30"
        labInfo, nameStem, valueOffset, functionName = TDF_ParseOneVariableName(valueName)
        if (labInfo is None):
            TDF_Log("!Error! Cannot parse variable: " + valueName)
            return valueList

        functionObject = None
        if (functionName != ""):
            functionObject = timefunc.CreateTimeValueFunction(functionName, nameStem)
            if (functionObject is None):
                print("\n\n\nERROR!! GetValuesBetweenDays Undefined function: " + functionName)
                sys.exit(0)

        # This loop will iterate over each step in the timeline.
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]

            currentDayNum = timelineEntry['TimeDays']
            if (currentDayNum < firstDay):
                continue
            if (currentDayNum > lastDay):
                break

            if ((fOnlyOneValuePerDay) and (foundPrevValues) and (prevDayNum == currentDayNum)):
                continue
            prevDayNum = currentDayNum

            latestValues = timelineEntry['data']
            if (valueName not in latestValues):
                continue

            value = latestValues[valueName]
            try:
                valueFloat = float(value)
            except Exception:
                valueFloat = TDF_INVALID_VALUE
            if ((valueFloat == TDF_INVALID_VALUE) or (valueFloat <= TDF_SMALLEST_VALID_VALUE)):
                continue
            foundPrevValues = True

            # Normalize the values
            labMinVal = float(labInfo['minVal'])
            labMaxVal = float(labInfo['maxVal'])
            if (valueFloat < float(labMinVal)):
                valueFloat = float(labMinVal)
            if (valueFloat > float(labMaxVal)):
                valueFloat = float(labMaxVal)

            newDict = {"Day": currentDayNum, "Val": valueFloat}
            valueList.append(newDict)
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1)

        return valueList
    # End - GetValuesBetweenDays()




    #####################################################
    #
    # [TDFFileReader::TestGetRawTimelineData]
    #
    #####################################################
    def TestGetRawTimelineData(self, timeLineIndex):
        if ((timeLineIndex < 0) or (timeLineIndex >= len(self.CompiledTimeline))):
            return False, 0, 0, {}

        timelineEntry = self.CompiledTimeline[timeLineIndex]
        currentDayNum = timelineEntry['TimeDays']
        currentMinuteInDay = timelineEntry['TimeIntervalNum'] * self.MinutesPerTimelineEntry
        currentHour = currentMinuteInDay / 60
        currentMin = currentMinuteInDay - (currentHour * 60)
        
        #timeStamp = TDF_MakeTimeStamp(currentDayNum, currentHour, currentMin)
        dataDict = timelineEntry['data']

        timeStampAsInt = 0
        timeStampAsInt = timeStampAsInt + (currentDayNum * 24 * 60 * 60)
        # Add hours in seconds
        timeStampAsInt = timeStampAsInt + (currentHour * 60 * 60)
        # Add minutes in seconds
        timeStampAsInt = timeStampAsInt + (currentMin * 60)

        return True, timeStampAsInt, currentDayNum, dataDict
    # End - TestGetRawTimelineData





    ################################################################################
    #
    # [TDFFileReader::ComputeOutcomeCategory]
    #
    # You cannot do "TimeUntil_xxx" because that cannot express the idea that the event "xxx" may
    # never happen. Instead, use categories, like "xxx will happen", "xxxx will not happen" or
    # time-bound categories like "xxx will happen in 3mos"
    # Each "Outcome_XXX" variable is a category:
    ################################################################################
    def ComputeOutcomeCategory(self, currentDate, outcomeDate):
        # 13 = EVENT will NOT happen in the next 10yrs
        if (outcomeDate < 0):
            return(TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS)

        # 0 = EVENT is happening now or has previously happened
        daysUntilOutcome = outcomeDate - currentDate
        if (daysUntilOutcome <= 0):
            return(TDF_FUTURE_EVENT_CATEGORY_NOW_OR_PAST)

        # 1 = EVENT will happen in 1 day
        if (daysUntilOutcome <= 1):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_1_DAY)

        # 2 = EVENT will happen in 3 days
        if (daysUntilOutcome <= 3):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_3_DAYS)

        # 3 = EVENT will happen in 7 days
        if (daysUntilOutcome <= 7):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_7_DAYS)

        # 4 = EVENT will happen in 14 days
        if (daysUntilOutcome <= 14):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_14_DAYS)

        # 5 = EVENT will happen in 30 days
        if (daysUntilOutcome <= 30):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_30_DAYS)

        # 6 = EVENT will happen in 90 days
        if (daysUntilOutcome <= 90):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_90_DAYS)

        # 7 = EVENT will happen in 180 days
        if (daysUntilOutcome <= 180):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_180_DAYS)

        # 8 = EVENT will happen in 365 days
        if (daysUntilOutcome <= 365):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_365_DAYS)

        # 9 = EVENT will happen in 730 days
        if (daysUntilOutcome <= 730):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_730_DAYS)

        # 10 = EVENT will happen in 1095 days (3yrs)
        if (daysUntilOutcome <= 1095):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_1095_DAYS)

        # 11 = EVENT will happen in 1825 days (5yrs) (some ESRD models use this)
        if (daysUntilOutcome <= 1825):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_1825_DAYS)

        # 12 = EVENT will happen in 3650 days (10yrs)  (10yrs, Framingham uses this)
        if (daysUntilOutcome <= 3650):
            return(TDF_FUTURE_EVENT_CATEGORY_IN_3650_DAYS)

        # 13 = EVENT will NOT happen in the next 10yrs
        return(TDF_FUTURE_EVENT_CATEGORY_NOT_IN_10YRS)
    # End - ComputeOutcomeCategory




    #####################################################
    #
    # [TDFFileReader::GetValueList]
    #
    #####################################################
    def GetValueList(self, valueName, backgroundValueName):
        valueList = []
        backGroundValue = TDF_INVALID_VALUE

        # Manage invalid params
        if ((valueName is None) or (valueName == "")):
            return []
        if (backgroundValueName is None):
            backgroundValueName = ""

        # Parse the input variable param
        labInfo, valueNameStem, valueOffset, functionName = TDF_ParseOneVariableName(valueName)
        functionObject = None
        if (functionName != ""):
            functionObject = timefunc.CreateTimeValueFunction(functionName, valueOffset)
            if (functionObject is None):
                print("\n\n\nERROR!! TDFFileReader::GetValueList: Undefined function: " + functionName)
                sys.exit(0)
            functionObject.Reset()
        # End - if (self.allValuesFunctionNameList[index] != ""):


        # Look through every value in the timeline.
        prevValue = -1
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            latestValues = timelineEntry['data']
            currentDayNum = timelineEntry['TimeDays']

            if ((backgroundValueName != "")
                    and (backgroundValueName in latestValues) 
                    and (TDF_INVALID_VALUE != latestValues[backgroundValueName])):
                backGroundValue = latestValues[backgroundValueName]

            if ((backgroundValueName == "") or (backGroundValue != TDF_INVALID_VALUE)):
                # Get the lab value itself.
                foundIt, result = self.GetNamedValueFromTimeline(valueNameStem, valueOffset, functionObject,
                                                                 timeLineIndex, timelineEntry, currentDayNum)
                if ((foundIt) and (prevValue != result)):
                    valueInfo = {'T': currentDayNum, 'V': result, 'B': backGroundValue}
                    valueList.append(valueInfo)
                    prevValue = result
                # End - if ((foundIt) and (prevValue != result)):
            # End - if ((backgroundValueName is None) or (backgroundValueName == "") or (backGroundValue != TDF_INVALID_VALUE)):
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1):

        return valueList
    # End - GetValueList()





    #####################################################
    #
    # [TDFFileReader::GetAdmissionsForCurrentPatient]
    #
    #####################################################
    def GetAdmissionsForCurrentPatient(self):
        admissionInfo = None
        eventList = []
        currentMedArray = []
        isMale = 0

        # Get some properties from the patient. These apply to all data entries within this patient.
        genderStr = self.currentPatientNode.getAttribute("gender")
        if (genderStr == "M"):
            isMale = 1

        currentNode = dxml.XMLTools_GetFirstChildNode(self.currentPatientNode)
        while (currentNode):
            nodeType = dxml.XMLTools_GetElementName(currentNode).lower()

            # We ignore any nodes other than Events
            if (nodeType != "e"):
                # Go to the next XML node in the TDF
                currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
                continue

            # Get the timestamp for this XML node.
            timeStampStr = currentNode.getAttribute("T")
            if ((timeStampStr is not None) and (timeStampStr != "")):
                labDateDays, labDateHours, labDateMins = TDF_ParseTimeStamp(timeStampStr)
            else:
                # If we have a run of elements with no time code at the start, then
                # Skip them all until we get a time code.
                currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
                continue

            eventClass = currentNode.getAttribute("C")
            eventValue = currentNode.getAttribute("V")
            eventDetail = currentNode.getAttribute("D")
            ############################################
            if ((eventClass == "Admit") or (eventClass == "Clinic")):
                ageInYrs = int(labDateDays / 365)
                admissionInfo = {'FirstDay': labDateDays, 'FirstHour': labDateHours, 'FirstMin': labDateMins,
                                'LastDay': labDateDays, 'LastHour': labDateHours, 'LastMin': labDateMins,
                                'Team': eventValue, 'AdmitClass': eventDetail, 'Meds': "", "gender": isMale, "ageInYrs": ageInYrs}
                eventList.append(admissionInfo)
                currentMedArray = []

            ############################################
            if ((eventClass == "IMed") and (admissionInfo is not None)):
                medListStr = admissionInfo['Meds']
                xmlMedListArray = eventValue.split(",")
                for currentMed in xmlMedListArray:
                    currentMed = currentMed.split(":")[0]
                    if (currentMed not in currentMedArray):
                        currentMedArray.append(currentMed)
                        medListStr = medListStr + currentMed + ","
                        admissionInfo['Meds'] = medListStr
                # End - for fullMedStr in xmlMedListArray:
            # End - elif ((eventClass == "IMed") and (admissionInfo is not None))

            ############################################
            if (((eventClass == "Discharge") or (eventClass == "Clinic")) 
                    and (admissionInfo is not None)):
                admissionInfo['LastDay'] = labDateDays
                admissionInfo['LastHour'] = labDateHours
                admissionInfo['LastMin'] = labDateMins
                admissionInfo = None

            # Go to the next XML node in the TDF
            currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
        # End - while (currentNode):

        return eventList
    # End - GetAdmissionsForCurrentPatient()





    #####################################################
    #
    # [TDFFileReader::GetDiagnosesForCurrentPatient]
    #
    #####################################################
    def GetDiagnosesForCurrentPatient(self, firstDayNum, lastDayNum):
        fDebug = False
        totalDiagnosisList = []

        currentNode = dxml.XMLTools_GetFirstChildNode(self.currentPatientNode)
        while (currentNode):
            nodeType = dxml.XMLTools_GetElementName(currentNode).lower()

            # We ignore any nodes other than Diagnoses
            if (nodeType != "d"):
                currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
                continue

            eventClass = currentNode.getAttribute("C").lower()
            if (eventClass != "d"):
                currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
                continue

            # Get the timestamp for this XML node.
            timeStampStr = currentNode.getAttribute("T")
            if ((timeStampStr is not None) and (timeStampStr != "")):
                labDateDays, labDateHours, labDateMins = TDF_ParseTimeStamp(timeStampStr)
            else:
                currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
                continue

            if ((labDateDays >= firstDayNum) and (labDateDays <= lastDayNum)):
                # <D C="D" T="20136:00:21">U/733.99,U/V58.81,U/429.3</D>
                diagnosisListStr = str(dxml.XMLTools_GetTextContents(currentNode))
                if (fDebug):
                    print("GetDiagnosesForCurrentPatient. diagnosisListStr = " + str(diagnosisListStr))
                diagICDPairList = diagnosisListStr.split(",")
                for diagICDPair in diagICDPairList:
                    icdParts = diagICDPair.split("/")
                    if (len(icdParts) > 1):
                        if (fDebug):
                            print("GetDiagnosesForCurrentPatient. icdParts[0] = " + str(icdParts[0]) 
                                    + ", icdParts[1] = " + str(icdParts[1]))
                        totalDiagnosisList.append(icdParts[1])
                # End - for diagICDPair in diagICDPairList:
            # End - if ((labDateDays >= firstDayNum) and (labDateDays <= lastDayNum)):
            elif (labDateDays > lastDayNum):
                break

            # Go to the next XML node in the TDF
            currentNode = dxml.XMLTools_GetAnyPeerNode(currentNode)
        # End - while (currentNode):

        if (fDebug):
            print("GetDiagnosesForCurrentPatient. totalDiagnosisList = " + str(totalDiagnosisList))

        return totalDiagnosisList
    # End - GetDiagnosesForCurrentPatient()





    ################################################################################
    #
    # [ExpandAdmissionListWithHgbDropAndTransfusions]
    #
    ################################################################################
    def ExpandAdmissionListWithHgbDropAndTransfusions(self, admissionList):
        fDebug = False
        if (fDebug):
            print("\n\n\nExpandAdmissionListWithHgbDropAndTransfusions")

        for admissionInfo in admissionList:
            admissionInfo['NumHgbs'] = 0
            admissionInfo['NumTransfusions'] = 0
            admissionInfo['firstHgbValue'] = TDF_INVALID_VALUE
            admissionInfo['lastHgbValue'] = TDF_INVALID_VALUE
            admissionInfo['smallestHgbValue'] = TDF_INVALID_VALUE
            admissionInfo['largestHgbValue'] = TDF_INVALID_VALUE
            admissionInfo['firstPltsValue'] = TDF_INVALID_VALUE
            admissionInfo['lastPltsValue'] = TDF_INVALID_VALUE
            admissionInfo['largestPltsValue'] = TDF_INVALID_VALUE
            admissionInfo['smallestPltsValue'] = TDF_INVALID_VALUE
            admissionInfo['highestWBC'] = TDF_INVALID_VALUE
            admissionInfo['largestHgbValueBeforeNextTransfusion'] = TDF_INVALID_VALUE
            admissionInfo['totalDropTriggeringTransfusion'] = 0
            admissionInfo['numDropsLeadingToTransfusion'] = 0
            admissionInfo['totalRiseAfterTransfusion'] = 0
            admissionInfo['numRisesAfterTransfusion'] = 0
            admissionInfo['numIVAntibiotics'] = 0
            admissionInfo['numSurgeries'] = 0
            admissionInfo['numGIProcedures'] = 0
            admissionInfo['DDimer'] = -1
            admissionInfo['Fibrinogen'] = -1
            admissionInfo['Haptoglobin'] = -1
            admissionInfo['FreeHgb'] = -1
            admissionInfo['LDH'] = -1
            admissionInfo['Transferrin'] = -1
            admissionInfo['TransferrinSat'] = -1
            admissionInfo['Iron'] = -1
            admissionInfo['TIBC'] = -1
            admissionInfo["numBMPCollected"] = 0
            admissionInfo["numCBCCollected"] = 0
            admissionInfo["numLFTCollected"] = 0
            admissionInfo["LengthOfStay"] = 0  
            admissionInfo['numDaysWithLabs'] = 0  
            admissionInfo['HospDayOfTransfusionList'] = []
            admissionInfo['TransfusionsAfterNumLabsList'] = []
            admissionInfo['DropsPromptingTransfusionList'] = []
            admissionInfo['HgbPromptingTransfusionList'] = []
            admissionInfo['HgbRiseAfterTransfusionList'] = []
        # End - for admissionInfo in admissionList:

        ########################################
        # This loop will iterate over each step in the timeline.
        admissionInfo = None
        lastHgbBeforeTransfusion = TDF_INVALID_VALUE
        firstHgbInCurrentSegment = TDF_INVALID_VALUE
        fTransfused = False
        fFoundLabs = False
        prevDayNum = -1
        prevDayNumWithLabs = -1
        numDaysWithLabs = 0
        for timeLineIndex in range(self.LastTimeLineIndex + 1):
            timelineEntry = self.CompiledTimeline[timeLineIndex]
            currentDayNum = timelineEntry['TimeDays']
            latestValues = timelineEntry['data']
            fFoundLabs = False

            ##############################
            if (("Flag_HospitalAdmission" in latestValues) and (latestValues["Flag_HospitalAdmission"] > 0)):
                # Close out the prebious admission before we start a new one.
                if ((admissionInfo is not None) and (prevDayNum > 0)):
                    admissionInfo['LengthOfStay'] = prevDayNum - admissionInfo['FirstDay']
                    admissionInfo['numDaysWithLabs'] = numDaysWithLabs

                admissionInfo = None
                for admissionInfo in admissionList:
                    if (admissionInfo['FirstDay'] == currentDayNum):
                        admissionInfo = admissionInfo
                        break
                # End - for admissionInfo in admissionList:

                lastHgbBeforeTransfusion = TDF_INVALID_VALUE
                firstHgbInCurrentSegment = TDF_INVALID_VALUE
                numDaysWithLabs = 0
            # End - if (("Flag_HospitalAdmission" in latestValues) and (latestValues["Flag_HospitalAdmission"] == currentDayNum)):

            if (("Flag_HospitalDischarge" in latestValues) and (latestValues["Flag_HospitalDischarge"] > 0)):
                # Close out the prebious admission before we start a new one.
                if (admissionInfo is not None):
                    admissionInfo['numDaysWithLabs'] = numDaysWithLabs
                    if (prevDayNum > 0):
                        admissionInfo['LengthOfStay'] = prevDayNum - admissionInfo['FirstDay']
                # End - if (admissionInfo is not None):

                admissionInfo = None
                lastHgbBeforeTransfusion = TDF_INVALID_VALUE
                firstHgbInCurrentSegment = TDF_INVALID_VALUE
                numDaysWithLabs = 0
            # End - if (("Flag_HospitalAdmission" in latestValues) and (latestValues["Flag_HospitalAdmission"] == currentDayNum)):

            ##############################
            if (("TransRBC" in latestValues) and (latestValues["TransRBC"] >= 1)):
                if (admissionInfo is not None):
                    admissionInfo['NumTransfusions'] += 1
                    admissionInfo['HospDayOfTransfusionList'].append(currentDayNum - admissionInfo['FirstDay'])
                    admissionInfo['TransfusionsAfterNumLabsList'].append(numDaysWithLabs)

                    if ((lastHgbBeforeTransfusion != TDF_INVALID_VALUE) 
                            and (firstHgbInCurrentSegment != TDF_INVALID_VALUE)):
                        drop = firstHgbInCurrentSegment - lastHgbBeforeTransfusion
                        admissionInfo['DropsPromptingTransfusionList'].append(drop)
                        admissionInfo['HgbPromptingTransfusionList'].append(lastHgbBeforeTransfusion)
                        admissionInfo['totalDropTriggeringTransfusion'] += drop
                        admissionInfo['numDropsLeadingToTransfusion'] += 1
                    # End - if ((lastHgbBeforeTransfusion != TDF_INVALID_VALUE) and (firstHgbInCurrentSegment != TDF_INVALID_VALUE)):
                # End - if admissionInfo

                firstHgbInCurrentSegment = TDF_INVALID_VALUE
                fTransfused = True
            # End - if (("TransRBC" in latestValues) and (latestValues["TransRBC"] == 1)):

            ##############################
            if (("Hgb" in latestValues) and (TDF_INVALID_VALUE != latestValues["Hgb"])):
                hgbValue = latestValues["Hgb"]
                if (hgbValue <= 3.0):
                    hgbValue = 3.0

                if (admissionInfo is not None):
                    admissionInfo['NumHgbs'] += 1

                    admissionInfo['lastHgbValue'] = hgbValue
                    if (admissionInfo['firstHgbValue'] == TDF_INVALID_VALUE):
                        admissionInfo['firstHgbValue'] = hgbValue
                    if ((admissionInfo['largestHgbValue'] == TDF_INVALID_VALUE) 
                            or (hgbValue > admissionInfo['largestHgbValue'])):
                        admissionInfo['largestHgbValue'] = hgbValue
                    if ((admissionInfo['smallestHgbValue'] == TDF_INVALID_VALUE) 
                            or (hgbValue < admissionInfo['smallestHgbValue'])):
                        admissionInfo['smallestHgbValue'] = hgbValue
                    if ((admissionInfo['largestHgbValueBeforeNextTransfusion'] == TDF_INVALID_VALUE) 
                            or (hgbValue > admissionInfo['largestHgbValueBeforeNextTransfusion'])):
                        admissionInfo['largestHgbValueBeforeNextTransfusion'] = hgbValue
                # End - if (admissionInfo):

                if ((admissionInfo is not None) and (fTransfused)
                        and (lastHgbBeforeTransfusion != TDF_INVALID_VALUE)
                        and (hgbValue > lastHgbBeforeTransfusion)):
                    hgbRise = hgbValue - lastHgbBeforeTransfusion
                    admissionInfo['totalRiseAfterTransfusion'] += hgbRise
                    admissionInfo['numRisesAfterTransfusion'] += 1
                    admissionInfo['HgbRiseAfterTransfusionList'].append(hgbRise)
                # End - if (fTransfused):

                fTransfused = False
                lastHgbBeforeTransfusion = hgbValue
                if (TDF_INVALID_VALUE == firstHgbInCurrentSegment):
                    firstHgbInCurrentSegment = hgbValue
            # End - if (("Hgb" in latestValues) and (TDF_INVALID_VALUE != latestValues["Hgb"])):


            ##############################
            if (("Plt" in latestValues) and (TDF_INVALID_VALUE != latestValues["Plt"]) and (admissionInfo is not None)):
                pltValue = latestValues["Plt"]

                admissionInfo['lastPltsValue'] = pltValue
                if (admissionInfo['firstPltsValue'] == TDF_INVALID_VALUE):
                    admissionInfo['firstPltsValue'] = pltValue
                if ((admissionInfo['largestPltsValue'] == TDF_INVALID_VALUE) 
                        or (pltValue > admissionInfo['largestPltsValue'])):
                    admissionInfo['largestPltsValue'] = pltValue
                if ((admissionInfo['smallestPltsValue'] == TDF_INVALID_VALUE) 
                        or (pltValue < admissionInfo['smallestPltsValue'])):
                    admissionInfo['smallestPltsValue'] = pltValue
            # End - if (("Plt" in latestValues) and (TDF_INVALID_VALUE != latestValues["Plt"]) and (admissionInfo is not None):):

            ##############################
            if (("WBC" in latestValues) and (TDF_INVALID_VALUE != latestValues["WBC"]) and (admissionInfo is not None)):
                wbc = latestValues["WBC"]
                if ((admissionInfo['highestWBC'] == TDF_INVALID_VALUE) 
                        or (wbc > admissionInfo['highestWBC'])):
                    admissionInfo['highestWBC'] = wbc
                admissionInfo["numCBCCollected"] += 1
                fFoundLabs = True

            ##############################
            if (("Cr" in latestValues) and (TDF_INVALID_VALUE != latestValues["Cr"]) and (admissionInfo is not None)):
                admissionInfo["numBMPCollected"] += 1
                fFoundLabs = True

            ##############################
            if (("ALT" in latestValues) and (TDF_INVALID_VALUE != latestValues["ALT"]) and (admissionInfo is not None)):
                #print("ExpandAdmissionListWithHgbDropAndTransfusions. Count a LFT")
                admissionInfo["numLFTCollected"] = 0
                fFoundLabs = True

            ##############################
            # Antibiotics
            if (("VancDose" in latestValues) and (admissionInfo is not None) and (latestValues["VancDose"] > 0)):
                admissionInfo['numIVAntibiotics'] += 1
            if (("PipTazoDose" in latestValues) and (latestValues["PipTazoDose"] > 0) and (admissionInfo is not None)):
                admissionInfo['numIVAntibiotics'] += 1
            if (("CefepimeDose" in latestValues) and (latestValues["CefepimeDose"] > 0) and (admissionInfo is not None)):
                admissionInfo['numIVAntibiotics'] += 1
            if (("DaptoDose" in latestValues) and (latestValues["DaptoDose"] > 0) and (admissionInfo is not None)):
                admissionInfo['numIVAntibiotics'] += 1

            ##############################
            # Check to see if the patient had a GI procedure
            if (("MajorSurgeries" in latestValues) and (latestValues["MajorSurgeries"] > 0) and (admissionInfo is not None)):
                admissionInfo['numSurgeries'] += 1
            if (("GIProcedures" in latestValues) and (latestValues["GIProcedures"] > 0) and (admissionInfo is not None)):
                admissionInfo['numGIProcedures'] += 1

            ##############################
            if ((admissionInfo is not None) and ("DDimer" in latestValues) and (latestValues["DDimer"] > 0)):
                admissionInfo['DDimer'] = latestValues["DDimer"]

            ##############################
            if (("Fibrinogen" in latestValues) and (latestValues["Fibrinogen"] > 0) and (admissionInfo is not None)):
                admissionInfo['Fibrinogen'] = latestValues["Fibrinogen"]

            ##############################
            if (("Haptoglobin" in latestValues) and (TDF_INVALID_VALUE != latestValues["Haptoglobin"])
                    and (admissionInfo is not None) and (admissionInfo["Haptoglobin"] < 0)):
                admissionInfo['Haptoglobin'] = latestValues["Haptoglobin"]

            ##############################
            if (("FreeHgb" in latestValues) and (TDF_INVALID_VALUE != latestValues["FreeHgb"])
                    and (admissionInfo is not None) and (admissionInfo["FreeHgb"] < 0)):
                admissionInfo['FreeHgb'] = latestValues["FreeHgb"]

            ##############################
            if (("LDH" in latestValues) and (TDF_INVALID_VALUE != latestValues["LDH"])
                    and (admissionInfo is not None) and (admissionInfo["LDH"] < 0)):
                admissionInfo['LDH'] = latestValues["LDH"]

            ##############################
            if (("Transferrin" in latestValues) and (TDF_INVALID_VALUE != latestValues["Transferrin"])
                    and (admissionInfo is not None) and (admissionInfo["Transferrin"] < 0)):
                admissionInfo['Transferrin'] = latestValues["Transferrin"]

            ##############################
            if (("TransferrinSat" in latestValues) and (TDF_INVALID_VALUE != latestValues["TransferrinSat"])
                    and (admissionInfo is not None) and (admissionInfo["TransferrinSat"] < 0)):
                admissionInfo['TransferrinSat'] = latestValues["TransferrinSat"]

            ##############################
            if (("Iron" in latestValues) and (TDF_INVALID_VALUE != latestValues["Iron"])
                    and (admissionInfo is not None) and (admissionInfo["Iron"] < 0)):
                admissionInfo['Iron'] = latestValues["Iron"]

            ##############################
            if (("TIBC" in latestValues) and (TDF_INVALID_VALUE != latestValues["TIBC"])
                    and (admissionInfo is not None) and (admissionInfo["TIBC"] < 0)):
                admissionInfo['TIBC'] = latestValues["TIBC"]

            if (fFoundLabs):
                if (prevDayNumWithLabs != currentDayNum):
                    numDaysWithLabs += 1
                prevDayNumWithLabs = currentDayNum
            # End - if (fFoundLabs)

            prevDayNum = currentDayNum
        # End - for timeLineIndex in range(self.LastTimeLineIndex + 1):

        # Close out the last admission
        if (admissionInfo is not None):
            admissionInfo['numDaysWithLabs'] = numDaysWithLabs
            if (prevDayNum > 0):
                admissionInfo['LengthOfStay'] = prevDayNum - admissionInfo['FirstDay']
        # End - if (admissionInfo is not None):

        return admissionList
    # End - ExpandAdmissionListWithHgbDropAndTransfusions





    ################################################################################
    #
    # [TDF_CheckValue]
    #
    ################################################################################
    def TDF_CheckValue(self, value, timelineIndex):
        fDebug = False
        targetValueName = ""
        targetValueVal = 0
        targetFromInitialDate = -1
        targetDayNum = -1

        if (timelineIndex > self.LastTimeLineIndex):
            return

        startTimelineEntry = self.CompiledTimeline[timelineIndex]
        startDayNum = startTimelineEntry['TimeDays']
        startValueList = startTimelineEntry['data']
        startValue = startValueList[value]
        fGoalIsToBeLessThanTarget = True
        fValueIsBool = False
        fMustReachGoalOnExactDay = False
        numPositiveCases = 0
        numNegativeCases = 0
        fError = False
        errorMsg = None
        
        ##############################
        if (value == 'Future_Boolean_CKD5'):
            targetValueName = "GFR"
            targetValueVal = 15
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_Boolean_CKD4'): 
            targetValueName = "GFR"
            targetValueVal = 30
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_Boolean_CKD3b'): 
            targetValueName = "GFR"
            targetValueVal = 45
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_Boolean_CKD3a'): 
            targetValueName = "GFR"
            targetValueVal = 60
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_Boolean_MELD10'): 
            targetValueName = "MELD"
            targetValueVal = 10
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_Boolean_MELD20'): 
            targetValueName = "MELD"
            targetValueVal = 20
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_Boolean_MELD30'): 
            targetValueName = "MELD"
            targetValueVal = 30
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_Boolean_MELD40'): 
            targetValueName = "MELD"
            targetValueVal = 40
            targetDayNum = -1
            fValueIsBool = True
        elif (value == 'Future_CKD5_2YRS'): 
            targetValueName = "GFR"
            targetValueVal = 15
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_CKD4_2YRS'): 
            targetValueName = "GFR"
            targetValueVal = 30
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_CKD3b_2YRS'): 
            targetValueName = "GFR"
            targetValueVal = 45
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_CKD3a_2YRS'): 
            targetValueName = "GFR"
            targetValueVal = 60
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD10_2YRS'): 
            targetValueName = "MELD"
            targetValueVal = 10
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD20_2YRS'): 
            targetValueName = "MELD"
            targetValueVal = 20
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD30_2YRS'): 
            targetValueName = "MELD"
            targetValueVal = 30
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD40_2YRS'): 
            targetValueName = "MELD"
            targetValueVal = 40
            targetDayNum = startDayNum + (2 * 365)
            fValueIsBool = True
        elif (value == 'Future_CKD5_5YRS'): 
            targetValueName = "GFR"
            targetValueVal = 15
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_CKD4_5YRS'): 
            targetValueName = "GFR"
            targetValueVal = 30
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_CKD3b_5YRS'): 
            targetValueName = "GFR"
            targetValueVal = 45
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_CKD3a_5YRS'): 
            targetValueName = "GFR"
            targetValueVal = 60
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD10_5YRS'): 
            targetValueName = "MELD"
            targetValueVal = 10
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD20_5YRS'): 
            targetValueName = "MELD"
            targetValueVal = 20
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD30_5YRS'): 
            targetValueName = "MELD"
            targetValueVal = 30
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_MELD40_5YRS'): 
            targetValueName = "MELD"
            targetValueVal = 40
            targetDayNum = startDayNum + (5 * 365)
            fValueIsBool = True
        elif (value == 'Future_Days_Until_CKD5'): 
            targetValueName = "GFR"
            targetValueVal = 15
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        elif (value == 'Future_Days_Until_CKD4'): 
            targetValueName = "GFR"
            targetValueVal = 30
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        elif (value == 'Future_Days_Until_CKD3b'): 
            targetValueName = "GFR"
            targetValueVal = 45
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        elif (value == 'Future_Days_Until_CKD3a'): 
            targetValueName = "GFR"
            targetValueVal = 60
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        elif (value == 'Future_Days_Until_MELD10'): 
            targetValueName = "MELD"
            targetValueVal = 10
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        elif (value == 'Future_Days_Until_MELD20'): 
            targetValueName = "MELD"
            targetValueVal = 20
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        elif (value == 'Future_Days_Until_MELD30'): 
            targetValueName = "MELD"
            targetValueVal = 30
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        elif (value == 'Future_Days_Until_MELD40'): 
            targetValueName = "MELD"
            targetValueVal = 40
            targetDayNum = startDayNum + startValue
            fValueIsBool = False
            fMustReachGoalOnExactDay = True
        # Future Disease Stages by Time Category
        elif (value == 'Future_Category_CKD5'): 
            targetValueName = "GFR"
            targetValueVal = 15
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        elif (value == 'Future_Category_CKD4'): 
            targetValueName = "GFR"
            targetValueVal = 30
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        elif (value == 'Future_Category_CKD3b'): 
            targetValueName = "GFR"
            targetValueVal = 45
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        elif (value == 'Future_Category_CKD3a'): 
            targetValueName = "GFR"
            targetValueVal = 60
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        elif (value == 'Future_Category_MELD10'): 
            targetValueName = "MELD"
            targetValueVal = 10
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        elif (value == 'Future_Category_MELD20'): 
            targetValueName = "MELD"
            targetValueVal = 20
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        elif (value == 'Future_Category_MELD30'): 
            targetValueName = "MELD"
            targetValueVal = 30
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        elif (value == 'Future_Category_MELD40'): 
            targetValueName = "MELD"
            targetValueVal = 40
            targetDayNum = startDayNum + g_CategoryToNumDays[startValue]
            fValueIsBool = False
            fMustReachGoalOnExactDay = False
        else:
            return

        #elif (value == 'Future_Days_Until_AKI': 
        #elif (value == 'Future_Days_Until_AKIResolution': 
        #elif (value == 'Future_Days_Until_Death': 
        #elif (value == 'Future_Days_Until_Discharge': 
        #elif (value == 'Future_Days_Until_RapidResponse': 
        #elif (value == 'Future_Days_Until_TransferIntoICU': 
        #elif (value == 'Future_Days_Until_TransferOutOfICU': 
        #elif (value == 'Future_Days_Until_Intubation': 
        #elif (value == 'Future_Category_Death': 
        #elif (value == 'Future_Category_Discharge': 
        #elif (value == 'Future_Category_RapidResponse': 
        #elif (value == 'Future_Category_TransferIntoICU': 
        #elif (value == 'Future_Category_TransferOutOfICU': 
        #elif (value == 'Future_Category_Intubation': 
        # Future Disease Stages by Boolean
        #'Future_Boolean_Death'
        #'Future_Boolean_RapidResponse'
        #'Future_Boolean_TransferIntoICU'
        #'Future_Boolean_TransferOutOfICU'
        #'Future_Boolean_Intubation'
        #elif (value == 'Future_Category_AKI': 
        #elif (value == 'Future_Category_AKIResolution': 

        if (fDebug):
            print("TDF_CheckValue. value=" + str(value) + ", timelineIndex=" + str(timelineIndex))
            print("TDF_CheckValue. targetValueVal=" + str(targetValueVal) + ", targetDayNum=" + str(targetDayNum))
            print("fGoalIsToBeLessThanTarget = " + str(fGoalIsToBeLessThanTarget))

        index = timelineIndex
        currentDayNum = -1
        currentValue = -1
        numPositiveCases = 0
        numNegativeCases = 0
        numTotalCases = 0
        errorDayNum = 0
        while (index <= self.LastTimeLineIndex):
            currentTimelineEntry = self.CompiledTimeline[index]
            currentDayNum = currentTimelineEntry['TimeDays']
            latestValues = currentTimelineEntry['data']

            if ((targetValueName in latestValues) and (latestValues[targetValueName] != TDF_INVALID_VALUE)):
                currentValue = latestValues[targetValueName]
                numTotalCases += 1
                if (fDebug):
                    print("currentDayNum=" + str(currentDayNum) + ", currentValue=" + str(currentValue))

                #########################################
                # Check Booleans
                if (fValueIsBool):
                    # Only check boolean conditions up to the time limit if there is one.
                    # Some conditions may assert something for all time, while others may assert something
                    # only for 2 years or so.
                    if ((targetDayNum <= 0) or (currentDayNum < targetDayNum)):
                        if (fGoalIsToBeLessThanTarget):
                            if (currentValue <= targetValueVal):
                                numPositiveCases += 1
                                if (fDebug):
                                    print("Positive Case 1")
                            else:
                                numPositiveCases = 0
                                if (fDebug):
                                    print("Reset all positive Cases 1")
                        elif (not fGoalIsToBeLessThanTarget):
                            if (currentValue > targetValueVal):
                                numPositiveCases += 1
                                if (fDebug):
                                    print("Positive Case 2")
                            else:
                                numPositiveCases = 0
                                if (fDebug):
                                    print("Reset all positive Cases 2")
                    # End - if ((targetDayNum <= 0) or (currentDayNum < targetDayNum)):
                    else:
                        if ((fGoalIsToBeLessThanTarget) and (currentValue > targetValueVal)):
                            numPositiveCases = 0
                            if (fDebug):
                                print("Reset all positive Cases 3")
                        elif ((not fGoalIsToBeLessThanTarget) and (currentValue <= targetValueVal)):
                            numPositiveCases = 0
                            if (fDebug):
                                print("Reset all positive Cases 4")
                # End - if (targetDayNum < 0):
                #########################################
                # Check exact integers before the predicted day
                elif ((not fValueIsBool) and (fMustReachGoalOnExactDay) and (currentDayNum < startValue)):
                    if ((fGoalIsToBeLessThanTarget) and (currentValue < targetValueVal)):
                        numNegativeCases += 1
                    elif ((not fGoalIsToBeLessThanTarget) and (currentValue >= targetValueVal)):
                        numNegativeCases += 1
                #########################################
                # Check exact integers on the predicted day
                elif ((not fValueIsBool) and (fMustReachGoalOnExactDay) and (currentDayNum >= startValue)):
                    if ((fGoalIsToBeLessThanTarget) and (currentValue < targetValueVal)):
                        numPositiveCases += 1
                    elif ((not fGoalIsToBeLessThanTarget) and (currentValue >= targetValueVal)):
                        numPositiveCases += 1
                #########################################
                # Check integer ranges before the predicted day
                elif ((not fValueIsBool) and (not fMustReachGoalOnExactDay) and (currentDayNum < startValue)):
                    if ((fGoalIsToBeLessThanTarget) and (currentValue < targetValueVal)):
                        numPositiveCases += 1
                    elif ((not fGoalIsToBeLessThanTarget) and (currentValue >= targetValueVal)):
                        numPositiveCases += 1
            # End - if (targetValueName in latestValues):

            index += 1
        # End - while (index <= self.LastTimeLineIndex):


        #########################################
        # Check Booleans
        if ((numTotalCases > 0) and (fValueIsBool)):
            # You can have any number of negative cases but must end with positive cases.
            if ((startValue) and (numPositiveCases == 0)):
                fError = True
                errorMsg = "Never reached condition 1"
            if ((not startValue) and (numPositiveCases > 0)):
                fError = True
                errorMsg = "Incorrectly reached condition 2"
        #########################################
        # Check exact integers before the predicted day
        elif ((numTotalCases > 0) and (not fValueIsBool) and (fMustReachGoalOnExactDay)):
            if (numNegativeCases > 0):
                fError = True
                errorMsg = "Reached condition too soon 3"
            if (numPositiveCases <= 0):
                fError = True
                errorMsg = "Never reached condition 4"

        if (fError):
            fullErrorMsg = "TDF_CheckValue Error! "
            if (errorMsg is not None):
                fullErrorMsg += errorMsg
            print(fullErrorMsg)
            print("TDF_CheckValue. startValue=" + str(startValue) + ", startDayNum=" + str(startDayNum))
            print("TDF_CheckValue. fGoalIsToBeLessThanTarget=" + str(fGoalIsToBeLessThanTarget) + ", fMustReachGoalOnExactDay=" + str(fMustReachGoalOnExactDay))
            print("TDF_CheckValue. fValueIsBool=" + str(fValueIsBool) + ", numTotalCases=" + str(numTotalCases))
            print("TDF_CheckValue. targetValueVal=" + str(targetValueVal) + ", targetDayNum=" + str(targetDayNum))
            print("TDF_CheckValue. numPositiveCases=" + str(numPositiveCases) + ", numNegativeCases=" + str(numNegativeCases))
            print("TDF_CheckValue. timelineIndex=" + str(timelineIndex) + ", self.LastTimeLineIndex=" + str(self.LastTimeLineIndex))
            index = timelineIndex
            while (index <= self.LastTimeLineIndex):
                currentTimelineEntry = self.CompiledTimeline[index]
                currentDayNum = currentTimelineEntry['TimeDays']
                latestValues = currentTimelineEntry['data']
                print(str(index) + ": day=" + str(currentDayNum) + ", latestValues" + str(latestValues))
                index += 1
            # End - while (index <= self.LastTimeLineIndex):

            sys.exit(0)
        # End  - if (fError):
    # End - TDF_CheckValue



# End - class TDFFileReader








################################################################################
# A public procedure.
################################################################################
def TDF_GetVariableType(fullValueName):
    # Get information about the lab.
    labInfo, valueName, valueOffset, functionName = TDF_ParseOneVariableName(fullValueName)
    if (labInfo is None):
        #print("Error! TDF_GetVariableType found undefined lab name: " + valueName)
        return(TDF_DATA_TYPE_UNKNOWN)

    # If the functionName is not NULL, then use that to determine the type
    if ((functionName is not None) and (functionName in g_FunctionInfo)):
        functionInfo = g_FunctionInfo[functionName]
        funcReturnType = functionInfo['resultDataType']
        # Some functions are always the same type as the variable
        if (funcReturnType != TDF_DATA_TYPE_UNKNOWN):
            return funcReturnType
    # End - if ((functionName is not None) and (functionName in g_FunctionInfo)):

    dataType = labInfo['dataType']
    return(dataType)
# End - TDF_GetVariableType




################################################################################
# A public procedure.
################################################################################
def TDF_GetMinMaxValuesForVariable(fullValueName):
    # Get information about the lab.
    labInfo, valueName, valueOffset, functionName = TDF_ParseOneVariableName(fullValueName)
    if (labInfo is None):
        print("Error! TDF_GetMinMaxValuesForVariable found undefined lab name: " + valueName)
        return TDF_INVALID_VALUE, TDF_INVALID_VALUE

    labMinVal = float(labInfo['minVal'])
    labMaxVal = float(labInfo['maxVal'])
    return labMinVal, labMaxVal
# End - TDF_GetMinMaxValuesForVariable




################################################################################
# A public procedure.
################################################################################
def TDF_GetNumClassesForVariable(fullValueName):
    # Get information about the lab.
    labInfo, valueName, valueOffset, functionName = TDF_ParseOneVariableName(fullValueName)
    if (labInfo is None):
        print("Error! TDF_GetNumClassesForVariable found undefined lab name: " + valueName)
        return(1)

    # A boolean is treated like a 2-class category variable.
    if (labInfo['dataType'] == TDF_DATA_TYPE_BOOL):
        numVals = 2
    elif (labInfo['dataType'] == TDF_DATA_TYPE_FUTURE_EVENT_CLASS):
        return(TDF_NUM_FUTURE_EVENT_CATEGORIES)
    else:
        numVals = 1

    return(numVals)
# End - TDF_GetNumClassesForVariable




#####################################################
#
# [TDFFileReader::TDF_ParseOneVariableName]
#
#####################################################
def TDF_ParseOneVariableName(valueName):
    labInfo = None
    valueOffset = 0
    functionName = ""

    # The variable names come from a user config file, so may have whitespace.
    valueName = valueName.lstrip()
    valueName = valueName.rstrip()

    # Any variable may have a function. For example: Cr.rate
    # Check if there is a function marker to see if we need to 
    # parse this.
    if (VARIABLE_FUNCTION_MARKER in valueName):
        nameParts = valueName.split(VARIABLE_FUNCTION_MARKER, 1)
        valueName = nameParts[0]
        functionName = nameParts[1]
    # End - if (VARIABLE_START_PARAM_ARGS_MARKER in varName):

    # A single name may have the form "foo" or "foo[n]" where n is an offset.
    # Split the names into name stems and optional offsets
    if (VARIABLE_START_OFFSET_MARKER in valueName):
        nameParts = valueName.split(VARIABLE_START_OFFSET_MARKER, 1)
        valueName = nameParts[0]
        valueOffsetStr = nameParts[1]
        valueOffsetStr = valueOffsetStr.split(VARIABLE_STOP_OFFSET_MARKER, 1)[0]
        valueOffset = int(valueOffsetStr.lower())

    if ((valueName != "") and (valueName in g_LabValueInfo)):
        labInfo = g_LabValueInfo[valueName]

    return labInfo, valueName, valueOffset, functionName
# End - TDF_ParseOneVariableName





################################################################################
#
# [TDF_NormalizeInputValue]
#
# dataTypeName has values:
#   "NormFraction" 
#   "NormInt0-100"
################################################################################
def TDF_NormalizeInputValue(labValue, minVal, maxVal, dataTypeName):
    # Clip the value to within the min and max.
    # Some patients can have *really* odd values, like a patient who refuses 
    # transfusion can have a Hgb around 3.0.
    if (labValue < float(minVal)):
        labValue = float(minVal)
    if (labValue > float(maxVal)):
        labValue = float(maxVal)

    # Normalize the value to a number between 0..1 for where this
    # value lands in the range of possible values.
    valRange = float(maxVal) - float(minVal)
    #print("NormalizeLabValueImpl. valRange=" + str(valRange))

    offset = float(labValue) - float(minVal)
    #print("NormalizeLabValueImpl. offset=" + str(offset))

    if (valRange > 0):
        normalFloatValue = float(offset) / float(valRange)
    else:
        normalFloatValue = 0.0

    resultVal = int(round(normalFloatValue * 100.0))

    #print("TDF_NormalizeInputValue. normalValue=" + str(normalValue))
    return(resultVal)
# End - TDF_NormalizeInputValue





################################################################################
#
# [TDF_ParseUserValueListString]
#
# A public procedure.
# This is used to parse the data passed in a HTTP request to a web server into
# an array of input values.
################################################################################
def TDF_ParseUserValueListString(inputNameListStr, userProvidedDataStr, fParseInputSeries):
    # Parse the input names into a list.
    # Leave the offsets on the names, as those offsets willremain on the name for both
    # the variables and the values.
    inputValueNameList = inputNameListStr.split(VARIABLE_LIST_SEPARATOR)
    numValsInEachVector = len(inputValueNameList)      

    if (fParseInputSeries):
        vectorStrList = userProvidedDataStr.split(VARIABLE_ROW_SEPARATOR)
        numVectors = len(vectorStrList)
    else:
        numVectors = 1

    # Make a vector big enough to hold the labs.
    inputArray = np.empty((numVectors, 1, numValsInEachVector))

    # Parse the string for each vector separately, one in each loop iteration
    # If this is a single input vector, then numVectors = 1 and this will only iterate once.
    foundAllInputs = True
    for vectorNum in range(numVectors):
        #print("TDF_ParseUserValueListString vectorNum=" + str(vectorNum))

        if (fParseInputSeries):
            currentVectorStr = vectorStrList[vectorNum]
        else:
            currentVectorStr = userProvidedDataStr
        #print("TDF_ParseUserValueListString currentVectorStr=" + str(currentVectorStr))

        # Parse the named data values into a list.
        # A web client may pass the inputs in any order, so we will have to search
        # this list for each input in turn, and then reassemble them in the correct order.
        # Leave the offsets on the names, as those offsets will remain on the name for both
        # the variables and the values.
        userProvidedInputValueList = currentVectorStr.split(VARIABLE_LIST_SEPARATOR)
        userProvidedInputDataDict = {}
        for valueIndex, valueStr in enumerate(userProvidedInputValueList):
            partsList = valueStr.split('=')
            valName = partsList[0]
            # Be careful about the value.
            # Some parameters are strings (like the "predictionType" opCode)
            try:
                floatVal = float(partsList[1])
            except Exception:
                floatVal = 0.0
            userProvidedInputDataDict[valName] = floatVal
        # End - for valueIndex, valueStr in enumerate(userProvidedInputValueList):


        # Find the labs we are looking for in the current vector of user data.
        # The user inputs may have extra data, or else data in different order.
        # This will leave offsets on the variables, like Cr[-3]. 
        # The userdata will also include these offsets, so we exactly match the entire string.
        for nameIndex, nameStr in enumerate(inputValueNameList):
            if nameStr in userProvidedInputDataDict:
                valueNameStem = nameStr
                if (VARIABLE_START_OFFSET_MARKER in valueNameStem):
                    valueNameStem = valueNameStem.split(VARIABLE_START_OFFSET_MARKER, 1)[0]

                # Get information about the lab.
                try:
                    # Use the full name, including offsets, to get the user-provided value
                    userValue = userProvidedInputDataDict[nameStr]
                    # Use only the name stem, withOUT offsets, to look up the datatype
                    labInfo = g_LabValueInfo[valueNameStem]
                except Exception:
                    foundAllInputs = False
                    break

                labMinVal = float(labInfo['minVal'])
                labMaxVal = float(labInfo['maxVal'])
                dataTypeName = labInfo['dataType']
                #print("Found valueNameStem=" + str(valueNameStem))
                #print("Found nameStr labInfo=" + str(labInfo))

                # Normalize the lab value so all values range between 0.0 and 1.0
                normValue = TDF_NormalizeInputValue(userValue, labMinVal, labMaxVal, dataTypeName)
                inputArray[vectorNum][0][nameIndex] = normValue
            # End - if nameStr in userProvidedInputDataDict:
            else:
                #print("nameStr Not In Dictionary: nameStr=" + str(nameStr))
                foundAllInputs = False
                break
        # End - for nameIndex, nameStr in enumerate(inputValueNameList):

        if (not foundAllInputs):
            break
    # End - for vectorNum in range(numVectors):

    if (not foundAllInputs):
        return False, 0, None

    return True, numVectors, inputArray
# End - TDF_ParseUserValueListString






################################################################################
#
# [CreateFilePartitionList]
#
# A public procedure to create a dictionary of partitions in a file.
# This is used by mlEngine to break up a file into chunks
################################################################################
def CreateFilePartitionList(tdfFilePathName, partitionSizeInBytes):
    #print("CreateFilePartitionList. tdfFilePathName = " + tdfFilePathName)
    partitionList = []

    try:
        fileInfo = os.stat(tdfFilePathName)
        fileLength = fileInfo.st_size
    except Exception:
        return partitionList

    partitionStartPos = 0
    while (partitionStartPos < fileLength):
        partitionStopPos = partitionStartPos + partitionSizeInBytes
        if (partitionStopPos >= fileLength):
            partitionStopPos = fileLength
        newDict = {'start': partitionStartPos, 'stop': partitionStopPos, 'ptListStr': ""}
        partitionList.append(newDict)

        partitionStartPos = partitionStopPos
    # End - while (partitionStartPos < fileLength):

    return partitionList
# End - CreateFilePartitionList



################################################################################
# A public procedure.
################################################################################
def TDF_GetNamesForAllVariables():
    listStr = ""
    for index, (varName, labInfo) in enumerate(g_LabValueInfo.items()):
        listStr = listStr + varName + VARIABLE_LIST_SEPARATOR

    # Remove the last separator
    listStr = listStr[:-1]
    return listStr
# End - TDF_GetNamesForAllVariables





################################################################################
# A public procedure to create the DataLoader
################################################################################
def TDF_CreateTDFFileReader(tdfFilePathName, inputNameListStr, resultValueName, 
                            requirePropertyNameList):

    reader = TDFFileReader(tdfFilePathName, inputNameListStr, resultValueName, 
                            requirePropertyNameList)
    return reader
# End - TDF_CreateTDFFileReader




################################################################################
# 
################################################################################
def TDF_CreateNewFileWriter(fileH):
    writer = TDFFileWriter()
    writer.__SetFileOutputFileHandle__(fileH)

    return writer
# End - TDF_CreateNewFileWriter






