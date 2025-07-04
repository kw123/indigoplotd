#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# INDIGOplot Plugin
# 2014-02-23
# Developed by Karl Wachs
# karlwachs@me.com
# please use as you see fit, no warrenty
## need to test in files arenot there or bad data read
import linecache
import os, sys, re, threading, subprocess, pwd, signal
import codecs
import copy
import datetime
import time
import xml.etree.ElementTree
import math
import getNumber as GT
##import versionCheck.versionCheck as VS
import cProfile
import pstats
import logging
import traceback
import platform
from checkIndigoPluginName import checkIndigoPluginName 


try:
	import json
except:
	import simplejson as json


try:
	unicode("x")
except:
	unicode = str()

###hardwired constants:
dataOffsetInTimeDataNumbers =   5
noOfTimeTypes				=	3
noOfStatesPerDeviceG		=	8
noOfMinutesInTimeBins		=	[5,60,60*24]
binTypeNames				=	["Minutes","Hours","Days"]
binTypeFileNames			=	["Minute","Hour","Day"]
#MinuteHourDayNorm			=	[12.,1,1/24.]# for normalization to hours
#nsecsInTimeTypeBin			=	[5*60,60*60,24*60*60]
DeltaNormHOURFactor			=	60.*60.
##integrateConstantMinuteHourDay=	[1./(12.)* 1./(5.*60.),(1.)/(60.*60.),(24.)/(24.*60.*60.)]
integrateConstantMinuteHourDay=	[1./(12.),(1.),(24.)]
subStrForTimeString			=	[14,14,14]
stdColors=	[
	"#FFA500","#FF0000","#A00000","#FFFF00","#A0A000","#00FF00","#00A000","#00FFFF","#00A0A0","#0000FF","#0000A0","#8B00B2","#4B0082","#000000","#383838","#E0E0E0","#FFFFFF"]

emptyDEVICE={	"Name"				:"None"													# plain name of device
			,	"deviceNumberIsUsed":0														# 0/1 used / unused
			,	"Id"				:0														# devID
			,	"devOrVar"			:"Dev-"													# Dev- / Var-
			,	"state"				:["None" for j in range(noOfStatesPerDeviceG+1)]	# staes of devcies like temperature ...
			,	"stateToIndex"		:[0 for j in range(noOfStatesPerDeviceG+1)]			# column index of datafile
			,	"measurement"		:["average" for j in range(noOfStatesPerDeviceG+1)]	# avrega, min/max/sum/count /...
			,	"fillGaps"			:["1" for j in range(noOfStatesPerDeviceG+1)]		# "0": do not fill gaps if no new data in time bin, "1" default: use last bin info if there is no new data
			,	"minValue"			:[-200. for j in range(noOfStatesPerDeviceG+1)]		# low cutoff value
			,	"maxValue"			:[+50000. for j in range(noOfStatesPerDeviceG+1)]	# high cutOff value
			,	"offset"			:[0. for j in range(noOfStatesPerDeviceG+1)]		# add raw number with this offset
			,	"multiplier"		:[1. for j in range(noOfStatesPerDeviceG+1)]		# multiply raw data with this number after adding offset
			,	"resetType"			:["0" for j in range(noOfStatesPerDeviceG+1)]		# 0= do not use
			,	"nickName"			:["" for j in range(noOfStatesPerDeviceG+1)]		# 0= do not use
			}

emptyLine = {	   "lineType"			:"6"
				  ,"lineWidth"			:"1"
				  ,"lineColor"			:"#000000"
				  ,"lineShift"			:0
				  ,"lineFunc"			:"None"
				  ,"lineSmooth"			:"None"
				  ,"lineMultiplier"		:1.
				  ,"lineOffset"			:0.
				  ,"lineLeftRight"		:"Left"
				  ,"lineKey"			:""
				  ,"lineToColumnIndexA"	:0
				  ,"lineToColumnIndexB"	:0
				  ,"lineToColumnIndexAfile"	:""
				  ,"lineToColumnIndexBfile"	:""
				  ,"lineNumbersFormat"	:"%3.1f"
				  ,"lineNumbersOffset"	:"0,1"
				  ,"lineEveryRepeat"	:"1"
				  ,"lineFromTo"	        :""
				}


emptyPlot={"Grid"				:"0"
		  ,"Border"				:"1+2+4+8"  # x,y,xTop,Yright border lines in Plot (this is GNUPLOT syntax: "set border 1+2+4+8"
		  ,"PlotType"			:"dataFromTimeSeries"
		  ,"XYvPolar"			:"xy"
		  ,"PlotFileOrVariName"	:""
		  ,"PlotFileLastupdates"	:"0"
		  ,"TitleText"			:""
		  ,"ExtraText"			:""
		  ,"ExtraTextXPos"		:"0.5"
		  ,"ExtraTextYPos"		:"0.5"
		  ,"ExtraTextRotate"	:"0"
		  ,"ExtraTextFrontBack"	:"front"
		  ,"ExtraTextSize"		:"8"
		  ,"ExtraTextColorRGB"	:"#000000"
		  ,"NumberIsUsed"		:0
		  ,"TextSize"			:"8"
		  ,"TextMATFont"		:"sans-serif"
		  ,"TextFont"			:"0"
		  ,"TextColor"			:"#000000"
		  ,"DeviceNamePlot"		:"None"

		  ,"LeftScaleRange"		:"00:100"
		  ,"LeftScaleTics"		:"20,40,60,80,100"
		  ,"LeftLabel"			:"    Temperature F"
		  ,"LeftLog"			:"linear"
		  ,"LeftScaleDecPoints"	:"0"

		  ,"RightScaleRange"	:"00:200"
		  ,"RightScaleTics"		:"0,20,40,60,80,100"
		  ,"RightLabel"			:"Humidty and ON-Time%                     ."
		  ,"RightLog"			:"linear"
		  ,"RightScaleDecPoints":"0"

		  ,"XScaleRange"		:""
		  ,"XScaleTics"			:""
		  ,"XLabel"				:"x-axis Text"
		  ,"XLabelPos"			:"0.9,-0.1"
		  ,"RXNumbers"			:"30"
		  ,"XLog"				:"linear"
		  ,"XScaleDecPoints"	:"0"
		  ,"XScaleFormat"		:""

		  ,"resxy"				:["820,350","1024,768"]
		  ,"Textscale21"		:"1.5"
		  ,"MHDDays"			:["2","14","90"]
		  ,"MHDShift"			:["0","0","0"]
		  ,"MHDFormat"			:["","",""]
		  ,"ampm"				:"24"
		  ,"boxWidth"			:"0.5"
		  ,"Raw"				:""
		  ,"drawZeroLine"		:True
		  ,"compressPNGfile"	:False
		  ,"Background"			:"#FFFFFF"
		  ,"TransparentBackground":"1.0"
		  ,"TransparentBlocks"	:"1.0"
		  ,"errorCount"			:0
		  ,"dataSource"			:"interactive"
		  ,"variableInText"		:""
		  ,"enabled"			:"True"
		  ,"lines":{}
		  }
#		,"lines":{"1":copy.deepcopy(emptyLine)}}

availableLineTypes		="DOT. DOTx DOT* DOTo DOTv DOT^ DOTs DOT+ DOT- DOT-. DOT| LineDashed LineSolid Histogram Histogram0 Histogram1 Histogram2 Histogram3 Histogram4 Histogram5 Histogram6 Histogram7 FilledCurves Numbers Impulses averageRight averageLeft firstBin lastBin rightY"
availableSmoothTypes	="soft medium strong trailingAverage average3Bins combine3Bins None"
availableFuncTypes		="+ - / * C E S None"

### Consumption costs variables, fixed static:

noOfCostTimePeriods				= 30
noOfCostTypes					= 2
availCostTypes					= ["Period","WeekDay"]
noOfCosts						= 5
emptyCost						= {"cost":[0.11,0,0,0,0]  # cost in $ Euo GBP...
								 , "consumed":[0.,9999999999.,9999999999.,9999999999.,9999999999.] # kWh consumed next step
								 , "day": 99		# day of week Monday =0
								 , "hour":99		# hour of day
								 , "Period":"2999000000"} # YYYY month day hour

noOfValuesMeasured				= 13
emptyValues						= [0 for i in range(noOfValuesMeasured)]
noOfConsumptionTypes			= 4
availConsumptionTypes			= ["eConsumption","gConsumption","wConsumption","oConsumption"]
emptyconsumedDuringPeriod		= [{"testDayHour":"-1","lastDay":"-1","lastResetBin":-1,"currentCostTimeBin":-1,"lastCostTimeBin":-1,"lastCostBinWithData":-1,"valueAtStartOfTimeBin":0.,"valueAtStartOfCostBin":0.,"costAtLastCostBracket":0.} for i in range(noOfTimeTypes)]




stateNiceWords={								# these "nice words" are shown to the uuser not the acucmEnergydatetime.timedelta ..
				"hvacHeaterIsOn":		"Heat-ON"
				,"hvacCoolerIsOn":		"AC-ON"
				,"hvacFanIsOn":			"FAN-ON"
				,"setpointHeat":		"Setpoint Heat"
				,"setpointCool":		"Setpoint Cool"
				,"temperatureInput1":	"Temperature"
				,"temperature":			"Temperature"
				,"temperatureF":		"Temperature [F]"
				,"temperatureC":		"Temperature [C]"
				,"humidity":			"Humidity [%]"
				,"accumEnergydatetime.timedelta":"Energy Measuremt Time"
				,"accumEnergyTotal":	"Energy [Watt-Hour]"
				,"curEnergyLevel":		"Power [Watt]"
				,"hvacDehumidifierIsOn":"Dehumidifier-ON"
				,"hvacHumidifierIsOn":	"Humidifier-ON"
				,"rainrate":			"Rain Rate"
				,"currentDayTotal":		"Rain Today"
				,"sensorValue":			"Sensor Value"
				,"humidityInput1" :		"Humditity"
				,"UVLevel" :			"UVLevel"
				,"avgSpeed" :			"Avg Wind Speed"
				,"directionDegrees" :	"Wind Direction [Deg]"
				,"gust" :				"Wind Gust"
				,"DistanceAway" :		"Distance"
				,"BatteryLevel" :		"Battery Level [%]"
				,"batteryLevel":		"Battery Level [%]"
				,"BatteryTimeRemaining":"Battery Time Remaining"
				,"dewPointC" :			"Dewpoint [C]"
				,"dewPointF" :			"Dewpoint [F]"
				,"pressureInches" :		"Pressure [in]"
				,"visibility" :			"Visibility"
				,"windDegrees" :		"Wind-Direction [Deg]"
				,"windKnots" :			"Wind-Speed [k]"
				,"windMPH" :			"Wind-Speed [MPH]"
				,"onOffState" :			"On/Off"
				,"activeZone":			"Sprinkler Zone"
				,"speedLevel":			"Fan Speed [%]"
				,"speedIndex":			"Fan Speed [0-3]"
				,"brightnessLevel":		"Brightness Level [%]" 	}

supportedMeasurements = ["average","count","max","min","sum","integrate","delta","deltaNormHour","deltaMax"
						 ,"eConsumption","gConsumption","wConsumption","oConsumption"
						 ,"Direction0toPiNorth","Direction0toPiEast","Direction0to360North","Direction0to360East"
						 ,"event","eventUP","eventCHANGE","eventDOWN","eventANY","eventCOUNT"]



pluginName           ="INDIGOplotD"

################################################################################
class Plugin(indigo.PluginBase):

####-----------------             ---------
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		self.pathToPlugin				= os.getcwd()+"/"
		## = /Library/Application Support/Perceptive Automation/Indigo 7.2/Plugins/INDIGOPLOTD.indigoPlugin/Contents/Server Plugin
		self.pluginShortName 			= "INDIGOplotD"
		self.quitNow					= ""

###############  common for all plugins ############
		self.getInstallFolderPath		= indigo.server.getInstallFolderPath()+"/"
		self.indigoPath					= indigo.server.getInstallFolderPath()+"/"
		self.indigoRootPath 			= indigo.server.getInstallFolderPath().split("Indigo")[0]
		self.pathToPlugin 				= self.completePath(os.getcwd())

		major, minor, release 			= indigo.server.version.split(".")
		self.indigoVersion 				= float(major)+float(minor)/10.
		self.indigoRelease 				= release

		self.pluginVersion				= pluginVersion
		self.pluginId					= pluginId
		self.pluginName					= pluginId.split(".")[-1]
		self.myPID						= os.getpid()
		self.pluginState				= "init"

		self.myPID 						= os.getpid()
		self.MACuserName				= pwd.getpwuid(os.getuid())[0]

		self.MAChome					= os.path.expanduser("~")
		self.userIndigoDir				= self.MAChome + "/indigo/"
		self.indigoPreferencesPluginDir = self.getInstallFolderPath+"Preferences/Plugins/"+self.pluginId+"/"
		self.indigoPluginDirOld			= self.userIndigoDir + self.pluginShortName+"/"
		self.PluginLogFile				= indigo.server.getLogsFolderPath(pluginId=self.pluginId) +"/plugin.log"

		formats=	{   logging.THREADDEBUG: "%(asctime)s %(msg)s",
						logging.DEBUG:       "%(asctime)s %(msg)s",
						logging.INFO:        "%(asctime)s %(msg)s",
						logging.WARNING:     "%(asctime)s %(msg)s",
						logging.ERROR:       "%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s",
						logging.CRITICAL:    "%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s" }

		date_Format = { logging.THREADDEBUG: "%Y-%m-%d %H:%M:%S",		# 5
						logging.DEBUG:       "%Y-%m-%d %H:%M:%S",		# 10
						logging.INFO:        "%Y-%m-%d %H:%M:%S",		# 20
						logging.WARNING:     "%Y-%m-%d %H:%M:%S",		# 30
						logging.ERROR:       "%Y-%m-%d %H:%M:%S",		# 40
						logging.CRITICAL:    "%Y-%m-%d %H:%M:%S" }		# 50
		formatter = LevelFormatter(fmt="%(msg)s", datefmt="%Y-%m-%d %H:%M:%S", level_fmts=formats, level_date=date_Format)

		self.plugin_file_handler.setFormatter(formatter)
		self.indiLOG = logging.getLogger("Plugin")  
		self.indiLOG.setLevel(logging.THREADDEBUG)

		self.indigo_log_handler.setLevel(logging.INFO)

		self.indiLOG.log(20,"initializing  ... ")
		self.indiLOG.log(20,"path To files:          =================")
		self.indiLOG.log(10,"indigo                  {}".format(self.indigoRootPath))
		self.indiLOG.log(10,"installFolder           {}".format(self.indigoPath))
		self.indiLOG.log(10,"plugin.py               {}".format(self.pathToPlugin))
		self.indiLOG.log(10,"indigo                  {}".format(self.indigoRootPath))
		self.indiLOG.log(20,"detailed logging        {}".format(self.PluginLogFile))
		#self.indiLOG.log(20,"testing logging levels, for info only: ")
		#self.indiLOG.log( 0,"logger  enabled for     0 ==> TEST ONLY ")
		#self.indiLOG.log( 5,"logger  enabled for     THREADDEBUG    ==> TEST ONLY ")
		#self.indiLOG.log(10,"logger  enabled for     DEBUG          ==> TEST ONLY ")
		#self.indiLOG.log(20,"logger  enabled for     INFO           ==> TEST ONLY ")
		#self.indiLOG.log(30,"logger  enabled for     WARNING        ==> TEST ONLY ")
		#self.indiLOG.log(40,"logger  enabled for     ERROR          ==> TEST ONLY ")
		#self.indiLOG.log(50,"logger  enabled for     CRITICAL       ==> TEST ONLY ")
		self.indiLOG.log(10,"Plugin short Name       {}".format(self.pluginShortName))
		self.indiLOG.log(10,"my PID                  {}".format(self.myPID))	 
		self.indiLOG.log(10,"Achitecture             {}".format(platform.platform()))	 
		self.indiLOG.log(10,"OS                      {}".format(platform.mac_ver()[0]))	 
		self.indiLOG.log(10,"indigo V                {}".format(indigo.server.version))	 
		self.indiLOG.log(10,"python V                {}.{}.{}".format(sys.version_info[0], sys.version_info[1] , sys.version_info[2]))	 

		self.pythonPath = ""
		if sys.version_info[0] >2:
			if os.path.isfile("/Library/Frameworks/Python.framework/Versions/Current/bin/python3"):
				self.pythonPath				= "/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
		else:
			if os.path.isfile("/usr/local/bin/python"):
				self.pythonPath				= "/usr/local/bin/python"
			elif os.path.isfile("/usr/bin/python2.7"):
				self.pythonPath				= "/usr/bin/python2.7"
		if self.pythonPath == "":
				self.indiLOG.log(40,"FATAL error:  none of python versions 2.7 3.x is installed  ==>  stopping {}".format(self.pluginId))
				self.quitNOW = "none of python versions 2.7 3.x is installed "
				exit()
		self.indiLOG.log(20,"using '{}' for utily programs".format(self.pythonPath))

###############  END common for all plugins ############
		self.userIndigoPluginDir		= self.indigoPreferencesPluginDir


####-----------------             ---------
	def __del__(self):
		indigo.PluginBase.__del__(self)


###########################     INIT    ## START ########################
	
####----------------- @ startup set global parameters, create directories etc ---------
	def startup(self):
		if not checkIndigoPluginName(self, indigo): 
			exit() 
			
		self.debugLevel = []
		for d in ["Restore","General","Initialize","Plotting","Matplot","SQL","Special","all"]:
			if self.pluginPrefs.get("debug"+d, False): self.debugLevel.append(d)



		self.justSaved	= False
		self.msgCount	= 0
		self.msg2		=False
		self.initBy		="reset"

		self.DEVICE = {}
		self.dataColumnCount = 0

		self.myPID = os.getpid()
		self.MACuserName = pwd.getpwuid(os.getuid())[0]
		self.MAChome     = os.path.expanduser("~")+"/"

		self.supressGnuWarnings                 = self.pluginPrefs.get("supressGnuWarnings",False)
		self.indigoPNGdir						= self.pluginPrefs.get("indigoPNGdir",self.userIndigoPluginDir)  #  this is the data directory

		if len(self.indigoPNGdir)<6:	self.indigoPNGdir  =	self.userIndigoPluginDir
		if self.indigoPNGdir[-1] !="/": self.indigoPNGdir +="/"  # add a / if not there


		try: 
			GT.getNumber(1)
		except  Exception as e:
			if self.decideMyLog("Plotting"): self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.sleep(1000)


			
		if not os.path.exists(self.userIndigoPluginDir):
			os.mkdir(self.userIndigoPluginDir)
		if not os.path.exists(self.userIndigoPluginDir):
			if self.decideMyLog("Plotting"): self.indiLOG.log(40,"error creating the plugin data dir did not work, can not create: "+ self.userIndigoPluginDir)
			self.sleep(1000)
			exit()


		self.indiLOG.log(10,"initializing  ... ;  debuglevel={}, apiversion:{}".format(self.debugLevel, indigo.server.apiVersion))



## basic paramters that do not change:
		self.indigoInitialized					=	False
		self.indigoInitializedMainLoop			=	False


		# find the current indigo version number and path to indigo directories
		# /Library/Application Support/Perceptive Automation/Indigo n/
		try:
			major, minor, release = map(int, indigo.server.version.split("."))
			indigoVersion = major
		except  Exception as e:
			if self.decideMyLog("Plotting"): self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.sleep(100)
			return

		
			

		try:
			ndays			=	json.loads(self.pluginPrefs.get("noOfDays", "[8,38,390]"))
			self.noOfDays	=	ndays
			self.indiLOG.log(10," number of days per bin category are: {}".format(self.noOfDays)+" for [days, hours, minutes] data ")
			self.noOfTimeBins	=	[int((60*24*self.noOfDays[0])//noOfMinutesInTimeBins[0]), int((60*24*self.noOfDays[1])//noOfMinutesInTimeBins[1]), int((60*24*self.noOfDays[2])//noOfMinutesInTimeBins[2])]
		except:
			self.noOfDays	=	[8,38,390]
			pass
		

		try:
			self.expertONOFF						= self.pluginPrefs["expertONOFF"]
		except:
			self.expertONOFF						= False
		try:
			self.showExpertParameters				= self.pluginPrefs["showExpertParameters"]
		except:
			self.showExpertParameters				= False


#		self.indigoPath = indigo.server.getInstallFolderPath()
		self.eventDataPresent   				=	{}
		self.sqlNumbOfRecsImported				=	0
		self.pidSQL								=	"-1"
		self.newPREFS							=	False
		self.newPLOTS							=	""
		self.sqlDynamic							=	self.pluginPrefs.get("sqlDynamic", "batch2Days")
		if self.sqlDynamic.find("-resetTo-") >-1:
			self.sqlDynamic = "batch2Days" #set back to default mode
			self.pluginPrefs["sqlDynamic"] = "batch2Days"


		### and the path to indigo:
		self.indigoSQLliteLogsPath				=	self.indigoPath+"Logs/"
		self.liteOrPsql							=	self.pluginPrefs.get("liteOrPsql","sqlite")
		self.liteOrPsqlString					=	self.pluginPrefs.get("liteOrPsqlString","")
		if self.liteOrPsql	 == "psql":
			if len(self.liteOrPsqlString) < 15 or self.liteOrPsqlString.find("psql") ==-1:
				self.indiLOG.log(40,"postgres psl command string likely wrong, in config \"postgre command string\"\n setting to: /Applications/Postgres.app/Contents/Versions/latest/bin/psql indigo_history -U postgres")
				self.liteOrPsqlString =  "/Applications/Postgres.app/Contents/Versions/latest/bin/psql indigo_history -U postgres"

		self.originalCopySQL					=	self.pluginPrefs.get("originalCopySQL","original")
		self.originalCopySQLActive				=	"-1"

		self.colDataON							=	False
		self.lastSQLHeader						=	0
		self.sqlNumbOfRecsRead  				=	0
		
		self.gnuVersion							=	""
		self.gnuOffset							=	0
		t = time.time()
		self.UTCdelta							=	int(  time.mktime(datetime.datetime.utcfromtimestamp(t+10).timetuple()) -t )/100*100
		self.secsEpochToMillenium				=	time.mktime(datetime.datetime.strptime("200001010000", "%Y%m%d%H%M").timetuple())
		self.secsSinceMillenium					=	 t - self.secsEpochToMillenium
		
		self.samplingPeriod						=	int(self.pluginPrefs.get("samplingPeriod", "60"))
		
		self.showAB								=	"NSA"
		
		
		self.matplotcommand						=	self.userIndigoPluginDir+"matplot/matplot.cmd"
		self.MPlogfile							=	self.userIndigoPluginDir+"matplot/matplot.log"
		self.matplotPid							=	self.userIndigoPluginDir+"matplot/matplot.pid"
		self.matPLOTParameterFile				=	self.userIndigoPluginDir+"matplot/matplot.json"			# this is the config file name + -plot.cfg and -device.cfg
		self.plotSizeNames						=	["S1","S2"] # file names for size 1 and size 2 of plots
		self.plotTimeNames						=	["minute","hour","day"] # files name for the different binings
		self.updateALL							=	False
		self.waitWithPlotting					=	True
		self.newConsumptionParams				=	""  # will be sued to store changes in e/g/w/oConsumption cost and schedules, then sql updates is called for those "cols" that qualify
		self.waitWithRedoIndex 					=	False
		self.sqlErrorCount						=	{}
		self.currentDeviceId					=	0
		self.sqlImportControl                   =   {}
		self.triggerList=[]

		self.fileData=[]
		self.fileData.append(self.userIndigoPluginDir+"data/"+self.plotTimeNames[0]+".dat") # data file names
		self.fileData.append(self.userIndigoPluginDir+"data/"+self.plotTimeNames[1]+".dat")
		self.fileData.append(self.userIndigoPluginDir+"data/"+self.plotTimeNames[2]+".dat")
		
		self.waitWithSQL =False
		


		try:
			self.PLOTlistLast	=	json.loads(self.pluginPrefs.get("PLOTlistLast", "['0','',0,0]"))
		except:
			self.PLOTlistLast	=	['0','',0,0]
		
		self.PLOTlist		=	[]


		try:
			indigo.variable.create("INDIGOplotD-Script-Message", "")
		except:
			pass


# if we start from scratch set matplot as defaut if version > 10.8
		if not os.path.isdir( self.userIndigoPluginDir ):
			try:
				os.makedirs(self.userIndigoPluginDir )  # make the data dir if it does not exist yet
			except:
				pass
		if not os.path.isdir( self.userIndigoPluginDir ): 
			self.indiLOG.log(50,f"Fatal error could not create indigoplot directory Directory: {self.userIndigoPluginDir} ")
			self.indiLOG.log(50,f"please create directory manually")
			self.quitNOW =  "error Fatal error could not create indigoplot directory"
			self.sleep(100)
			return

		try:
			if not os.path.isdir( self.indigoPNGdir ):
				import platform
				osVersion= platform.mac_ver()[0].split(".") # = eg [10,9,0]
				if int(osVersion[0]) >9 and int(osVersion[1]) >8:
					self.pluginPrefs["gnuORmat"]= "mat"
				os.makedirs(self.indigoPNGdir )  # make the data dir if it does not exist yet
		except:
			pass
		if not os.path.isdir( self.indigoPNGdir ):
			self.indiLOG.log(50,f"error could not create indigoplot PNG file Directory: {self.indigoPNGdir} ")
			self.indigoPNGdir = self.userIndigoPluginDir
			self.indiLOG.log(50,f"please create directory manually, temporaily set to:{self.indigoPNGdir}")
			self.sleep(1)


		
		try:
			os.makedirs(self.userIndigoPluginDir+"temp/" )
		except:
			pass
		try:
			os.makedirs(self.userIndigoPluginDir+"data/" )
		except:
			pass
		try:
			os.makedirs(self.userIndigoPluginDir+"matplot/" )
		except:
			pass
		try:
			os.makedirs(self.userIndigoPluginDir+"sql/" )
		except:
			pass
		try:
			os.makedirs(self.userIndigoPluginDir+"gnu/" )
		except:
			pass
		try:
			os.makedirs(self.userIndigoPluginDir+"py/" )
		except:
			pass
		try:
			os.makedirs(self.userIndigoPluginDir+"data/Columns" )
		except:
			pass
		ret = False
		if not os.path.isdir( self.userIndigoPluginDir+"temp" ): ret=True
		if not os.path.isdir( self.userIndigoPluginDir+"data" ): ret=True
		if not os.path.isdir( self.userIndigoPluginDir+"matplot" ): ret=True
		if not os.path.isdir( self.userIndigoPluginDir+"sql" ): ret=True
		if not os.path.isdir( self.userIndigoPluginDir+"gnu" ): ret=True
		if not os.path.isdir( self.userIndigoPluginDir+"py" ): ret=True
		if ret :
			self.indiLOG.log(40," Fatal error could not create indigoplot sub-directories ")
			self.quitNOW = "Fatal error could not create indigoplot sub-directories "
			return

			
		if os.path.isfile("/Library/Frameworks/Python.framework/Versions/Current/bin/python3"):
			self.pythonPath				= "/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
		elif os.path.isfile("/usr/local/bin/python"):
			self.pythonPath				= "/usr/local/bin/python"
		elif os.path.isfile("/usr/bin/python2.7"):
			self.pythonPath				= "/usr/bin/python2.7"
		else:
			self.indiLOG.log(40,"FATAL error:  none of python versions 2.7 3.x is installed  ==>  stopping INDIGOplotD")
			self.quitNOW = "none of python versions 2.7 3.x is installed "
			return
		
		#self.pythonPath				= "/usr/local/bin/python"
		self.indiLOG.log(10,"using '" +self.pythonPath +"' for utily programs")
		
		self.checkcProfile()

		self.clearFlags()



## basic paramters that do not change  -- END

		self.pidMATPLOT						=	"x"
		if  self.pluginPrefs.get("gnuORmat", "mat") =="gnu":
			self.pluginPrefs["fontsGNUONOFF"]=	True
			self.pluginPrefs["fontsMATONOFF"]=	False
			self.gnuORmatSET("gnu")
		else:
			self.gnuORmatSET("mat")
			self.pluginPrefs["fontsMATONOFF"]=	True
			self.pluginPrefs["fontsGNUONOFF"]=	False
		self.pluginPrefs["ExpertsP"]		=	False
		self.lineAlreadySelected			=	False
		self.currentPlotType				=	emptyPlot["PlotType"]
		self.currentXYvPolar				=	emptyPlot["XYvPolar"]
		self.listOfLinesForFileOrVari		=	[(0,"None")]

# setup gnu paramters
		self.gnuPlotBinary						=	self.pluginPrefs.get("gnuPlotBin","")
		self.gnuOffset= 0
		if os.path.isfile('/opt/local/bin/gnuplot'): self.gnuPlotBinary = "/opt/local/bin/gnuplot"
		if os.path.isfile('/usr/local/bin/gnuplot'): self.gnuPlotBinary = "/usr/local/bin/gnuplot"

		if self.pluginPrefs.get("gnuORmat", "mat") == "gnu":
			if self.gnuPlotBinary != "":
				if not os.path.isfile(self.gnuPlotBinary):
					self.doInstallGnuplot()
		self.testFonts()
		self.gnuTime()

		self.indiLOG.log(10,"SQLMode: "+self.sqlDynamic +";  GNUPLOT/MATPLOT: {}".format(self.pluginPrefs.get("gnuORmat", "mat"))+";  GNUplotVersion= {}".format(self.gnuVersion)+";  PLOT-Directory= {}".format(self.indigoPNGdir))


#		self.sleep(10)
		

# these might change depending on history, but we set them to a defalt value, they might be overwritten
		self.dataColumnCount				=	0  # count of device/props used for plots/lines
		self.dataColumnCountFileOffset      =	1  # first column of data  for dataColumnCount
		self.oldValuesDict					=	0
		self.buttonConfirmDevicePressed		=	False
		self.oldselectedExistingOrNewDevice	=	-1
		self.waitWithPLOTsync				=	False		# make sync plots with indigo wait 0.5 secs to give it time to updates tables
		self.waitWithPlotting				=	False		# checked in plotNow  if plottig should be done right now
		self.checkPlot1 						=	True		# set in plot now and checked for successfull plotting afterwards

		self.quitNOW						=	""		# can be set anywhere to anything but False then INDIGOPLOTD will stop (and start again)
		self.parameterVersion				=	"3"
		self.RGBreturned					=	["" for i in range(3)]
		self.removeThisDevice				=	[]
		self.devicesAdded					=	0
		self.scriptNewDevice  				=	0
		self.indigoCommand					=	[]

		self.eventSQLjobState               = "" 

# clear memmory
		self.resetDeviceParameters()
		self.resetPlotParameters()



# read history setting
		self.getDeviceParametersFromFile(calledfrom="startup")
		self.initializeData()
		self.getConsumptionDataFromFile()
		if self.syncPlotsWithIndigo(Force=True) ==-1: return


		### check if we need to updates SQL data files..
		SQLNeedsupdates=False
		if os.path.isfile(self.userIndigoPluginDir+"sql/version"):
			f=self.openEncoding(self.userIndigoPluginDir+"sql/version","r")
			if f.read().find("3")==-1:
				SQLNeedsupdates=True
			f.close()
		else:
			SQLNeedsupdates=True



		if not SQLNeedsupdates:
	# get disk data if there is any
			temp =  dataOffsetInTimeDataNumbers
			dataVersion = self.pluginPrefs.get("dataVersion", "0")
			if str(dataVersion) == "0":
				temp =0
			self.indiLOG.log(10,"dataversion {}".format(dataVersion) +"  dataOffsetInTimeDataNumbers:{}".format(dataOffsetInTimeDataNumbers))
			self.getDiskData(0,temp)
			self.getDiskData(1,temp)
			self.getDiskData(2,temp)
			self.upgradeDataStructure()

		else: 
			self.indiLOG.log(20," upgrading to new sql data structure ")
			self.initializeData()
			self.putDiskData(0)
			self.putDiskData(1)
			self.putDiskData(2)


# setup data pointer / indexes
		if self.redolineDataSource(calledfrom="startup") ==-1:
			if self.redolineDataSource(calledfrom="startup") ==-1:
				self.redolineDataSource(calledfrom="startup")

# read SQL data if available
		if self.sqlDynamic.find("batch")==0:
			if self.sqlDynamic.find("batch2Days")==0:
				self.ReloadSQL2Days()
			else:
				self.ReloadSQL()
			
			self.sqlNumbOfRecsImported =0
			self.devicesAdded =	2

			self.mkCopyOfDB()
			
			sqlUPTIME0  = self.procUPtime("SQL Logger.indigoPlugin")
			if sqlUPTIME0 < 10:
				self.indiLOG.log(10," wait for SQL logger to finish start up -- before retrieving SQL data ")
				for ii in range(10):
					self.sleep(10) # wait till sql logger is finished
					sqlUPTIME1 = self.procUPtime("SQL Logger.indigoPlugin") 
					if  sqlUPTIME1 -  sqlUPTIME0 < 1: break
					sqlUPTIME0 = sqlUPTIME1
				self.indiLOG.log(20," wait for SQL logger ended")    
					

			while True:
				self.setupSQLDataBatch(calledfrom="startup")
				if self.originalCopySQLActive =="-1": break
				if self.decideMyLog("SQL"): self.indiLOG.log(20," waiting for db copy job to finish ")
				self.sleep(30)            

			### check if we need to updates SQL data files..
			SQLNeedsupdates=False
			if os.path.isfile(self.userIndigoPluginDir+"sql/version"):
				f=self.openEncoding(self.userIndigoPluginDir+"sql/version","r")
				if f.read().find("3")==-1:
					SQLNeedsupdates=True
				f.close()
			else:
				SQLNeedsupdates=True
			
			if SQLNeedsupdates:
				self.fixSQLFiles(wait=True)
				f=self.openEncoding(self.userIndigoPluginDir+"sql/version","w")
				f.write("sql version   3   installed")
				f.close()
				self.indiLOG.log(20," updating SQL files to version 2")
			else:
				self.sleep(5)


# save to disk
		self.putDiskData(0)
		self.putDiskData(1)
		self.putDiskData(2)
		
# redo indexes
		if self.redolineDataSource(calledfrom="startup") ==-1:
			if self.redolineDataSource(calledfrom="startup") ==-1:
				if self.redolineDataSource(calledfrom="startup") ==-1:
						self.redolineDataSource(calledfrom="startup")
# if any corruption, remove device
		if len(self.removeThisDevice) > 0:
			self.indiLOG.log(20," removeThisDevice called in startup after redo")
			self.removeDevice()
			if self.redolineDataSource(calledfrom="startup") ==-1:
				if self.redolineDataSource(calledfrom="startup") ==-1:
					if self.redolineDataSource(calledfrom="startup") ==-1:
							self.redolineDataSource(calledfrom="startup")
		self.cleanData()

# do we have ny real day, if yes ==> initialized
		if self.dataColumnCount > 0 :
			self.indigoInitialized = True	# if there is any data this number is > 0 ie we asume we have a valid configuration and can start collecting data




		self.fixPy()
		if self.syncPlotsWithIndigo(Force=True) ==-1: return

		self.checkMinMaxFiles()


		self.indiLOG.log(10,"initializing  ...2 ")
		self.putDiskData(0)
		self.putDiskData(1)
		self.putDiskData(2)
		
		return
		
	########################################
	def upgradeDataStructure(self):
		#### add 4 columns at the beginning for last min/hour/day data 
		try:
		## now do the data
			self.dataVersion = int(self.pluginPrefs.get("dataVersion", "0"))
			if self.dataVersion  < 2:
					for  TTI in range(noOfTimeTypes):
						ncols=  len(self.timeDataNumbers[TTI][0])
						if ncols == self.dataColumnCount+1: addCols=True
						else:                               addCols=False
						for timeIndex in range(self.noOfTimeBins[TTI]):
							if addCols:
								for jj in range(dataOffsetInTimeDataNumbers):
									self.timeDataNumbers[TTI][timeIndex].append("")
								for kk in range(1+dataOffsetInTimeDataNumbers,ncols+dataOffsetInTimeDataNumbers):
									self.timeDataNumbers[TTI][timeIndex][kk+dataOffsetInTimeDataNumbers] = self.timeDataNumbers[TTI][timeIndex][kk]

			self.pluginPrefs["dataVersion"] = "2"

			self.fillWithTimeIndicators()
			
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return
		
	########################################
	def fillWithTimeIndicators(self):
		#### add 5 columns at the beginning for last min/hour/day data 

		try:
				for  TTI in range(noOfTimeTypes):
					for timeIndex in range(self.noOfTimeBins[TTI]):
						x = str(self.timeBinNumbers[TTI][timeIndex])
						self.timeDataNumbers[TTI][timeIndex][1] = 0 # week day 0-6
						self.timeDataNumbers[TTI][timeIndex][2] = 0 # 0/1 if last bin in month
						self.timeDataNumbers[TTI][timeIndex][3] = 0 # 0/1 if last bin in year
						self.timeDataNumbers[TTI][timeIndex][4] = 0 # not used ??
						self.timeDataNumbers[TTI][timeIndex][5] = timeIndex
						if timeIndex >0:
								self.timeDataNumbers[TTI][timeIndex][1] = datetime.datetime.strptime(x,"%Y%m%d%H%M%S").weekday()
								if x[-8:]  ==   "01000000":  # last bin  in month
									self.timeDataNumbers[TTI][timeIndex-1][2] = 1
								if x[-10:] == "0101000000":  # last bin  in year
										#      mmddHHMSS
									self.timeDataNumbers[TTI][timeIndex-1][3] = 1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return
		
	########################################
	def deviceStartComm(self, dev):	
		nPlot= str(dev.id)
		if nPlot in self.PLOT:
			self.PLOT[nPlot]["NumberIsUsed"] = 1
			if dev.enabled: self.PLOT[nPlot]["enabled"] = "True"
		return
	
	########################################
	def deviceStopComm(self, dev):
		return
		try:
			if self.justSaved: return
			nPlot= str(dev.id)
			self.PLOT[nPlot]["NumberIsUsed"]=0 # stop plotting until restart
			self.writePlotParameters()
			if self.decideMyLog("Initialize"): self.indiLOG.log(10,"deviceStopComm  ... id:{}".format(dev.id)+"  name:"+dev.name)
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return
	########################################
	def deviceCreated(self,dev):
		if self.decideMyLog("Initialize"): self.indiLOG.log(10,"deviceCreated  .. . id:{}".format(dev.id)+"  name:"+dev.name)
		self.syncPlotsWithIndigo()
		return
	########################################
	def deviceDeleted(self,dev):
		nPlot = str(dev.id)
		if self.decideMyLog("General"): self.indiLOG.log(10,"Plot Deleted  .. . id:"+nPlot+"  name:"+dev.name)
		self.removeThisPlotFile(nPlot)  # remove the gnu png files etc
		if nPlot in self.PLOT: del self.PLOT[nPlot]
		self.writePlotParameters()
		return



	########################################	initialize values/ programs ..	########################################	########################################	######################################
	def gnuTime(self):
		
		if self.gnuVersion.find("4.") >-1:
			self.gnuOffset= self.secsEpochToMillenium
		else:
			self.gnuOffset= 0


	########################################
	def ReloadSQL (self):
		if self.dataColumnCount <1: return
		self.clearSqlData(True)
		self.devicesAdded 				    =	2
		self.sqlColListStatus				=	[49  for i in range(self.dataColumnCount+1)]
		self.sqlHistListStatus				=	[10  for i in range(self.dataColumnCount+1)]
		self.sqlColListStatusRedo			=	[0  for i in range(self.dataColumnCount+1)]
		self.sqlColListStatus[0]			=	0
		self.sqlHistListStatus[0]			=	0
		self.sqlLastID				    	=	["0"  for i in range(self.dataColumnCount+1)]
		self.updateALL				    	=	True
		for theCol in range(1,self.dataColumnCount+1):
			devNo= self.dataColumnToDevice0Prop1Index[theCol][0]																			# for shorter typing
			stateNo=self.dataColumnToDevice0Prop1Index[theCol][1]
			if self.DEVICE["{}".format(devNo)]["measurement"][stateNo].find("Consumption") >-1:
				self.sqlHistListStatus[theCol]=50
			theDeviceId		= "{}".format(self.DEVICE["{}".format(devNo)]["Id"])
			theState	= self.DEVICE["{}".format(devNo)]["state"][stateNo]
			if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState):	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState)
	
		self.startColumnData()
		self.indiLOG.log(10,"command: reLoad SQL started")
		return
	########################################
	def ReloadSQL2Days (self):
		if self.dataColumnCount <1: return
		if self.sqlDynamic.find("-resetTo-") >-1:
			self.sqlDynamic = "batch2Days" # if messed up
		else:
			self.sqlDynamic					=	"batch2Days-resetTo-"+self.sqlDynamic
		self.devicesAdded 					=	2
		self.sqlColListStatus				=	[10  for i in range(0,self.dataColumnCount+1)]
		self.sqlHistListStatus				=	[10  for i in range(0,self.dataColumnCount+1)]
		self.sqlColListStatusRedo			=	[0  for i in range(0,self.dataColumnCount+1)]
		self.sqlHistListStatus[0]			=	0
		self.sqlColListStatus[0]			=	0
		self.updateALL					=	False
		for theCol in range(1,self.dataColumnCount+1):
			devNo= self.dataColumnToDevice0Prop1Index[theCol][0]																			# for shorter typing
			stateNo=self.dataColumnToDevice0Prop1Index[theCol][1]
			if self.DEVICE["{}".format(devNo)]["measurement"][stateNo].find("Consumption") >-1:
				self.sqlHistListStatus[theCol]=50
		self.startColumnData()
		self.indiLOG.log(10,"command: reLoad data from SQL for last 2 days started")
		return


	def startColumnData(self):
		if self.colDataON:
			f=self.openEncoding(self.userIndigoPluginDir+"data/columns/command","w")
			f.write(json.dumps(self.sqlColListStatus)+"\n")
			f.write(json.dumps(self.sqlHistListStatus)+"\n")
			f.write(json.dumps(self.sqlDynamic)+"\n")
			f.close()
		return


	########################################
	def doInitGNU(self):
		self.getDeviceParametersFromFile(calledfrom="doInitGNU")
		if self.redolineDataSource(calledfrom="doInitGNU") ==-1:
			if self.redolineDataSource(calledfrom="doInitGNU") ==-1:
				if self.redolineDataSource(calledfrom="doInitGNU") ==-1:
					if self.redolineDataSource(calledfrom="doInitGNU") ==-1:
						self.redolineDataSource(calledfrom="doInitGNU")
		self.setupGNUPlotFiles(calledfrom="doInitGNU")
		if self.decideMyLog("General"): self.indiLOG.log(10,"command: recreate plot Parameters done")
		return

	########################################
	def doInstallGnuplot(self):

		if self.decideMyLog("Initialize"): self.indiLOG.log(10,"installing gnuplot ")
		subprocess.Popen(["/usr/bin/open", self.userIndigoPluginDir+"gnu/installgnuplot.scpt"])
		for i in range(20):
			self.sleep(10)
			if os.path.isfile('/opt/local/bin/gnuplot'):
				self.gnuPlotBinary = "/opt/local/bin/gnuplot"
			if os.path.isfile('/usr/local/bin/gnuplot'):
				self.gnuPlotBinary = "/usr/local/bin/gnuplot"
			if len(self.gnuPlotBinary) > 0:
				self.indiLOG.log(10,"command: InstallGnuplot done")
				return True
		self.indiLOG.log(30,"command: InstallGnuplot not finshed, GNUplot is not (yet) installed  ...  if finshed later, reload INDIGOplotD to set all parameters properly")
		return False

	########################################
	def fixPy(self):
	
		cmd=self.pythonPath+" '"+self.indigoPath+"Plugins/"+self.pluginName+".indigoPlugin/Contents/Server Plugin/fixpy.py'  "+self.userIndigoPluginDir+"py/ > /dev/null 2>&1 &"
		subprocess.Popen( cmd, shell=True)
		self.indiLOG.log(20,"checking py-restore files")
		return

	########################################
	def clearFlags(self):
		if self.decideMyLog("General"): self.indiLOG.log(10,"clearing plot flags")
		if os.path.isfile(self.userIndigoPluginDir+"sql/sqlcmd.log"): os.remove(self.userIndigoPluginDir+"sql/sqlcmd.log")
		
		for gnuNames in os.listdir(self.userIndigoPluginDir+'gnu'):
			if ".err" in gnuNames: os.remove(self.userIndigoPluginDir+'gnu/'+gnuNames)
			if ".ok" in gnuNames: os.remove(self.userIndigoPluginDir+'gnu/'+gnuNames)
			if ".done" in gnuNames: os.remove(self.userIndigoPluginDir+'gnu/'+gnuNames)



	

	########################################
	def resetDeviceParameters(self):
		self.dataColumnCount						= 0
		self.sqlLastID								= ["0"]
		self.sqlLastImportedDate					= ["0"]
		self.sqlHistListStatus						= [0]
		self.sqlColListStatusRedo					= [0]
		self.sqlColListStatus						= [0]

		self.firstBinToFillFromSQL					=	[0 for k in range(noOfTimeTypes)]
#		self.timeBinStart							=	[0 for k in range(noOfTimeTypes)]		# in seconds; mark the starting point of the time bin used  to determine if "ON" was set in this timebin.
		self.FirstBinDate							=	"0000"+"00"+"00"+"00"+"00" +"00"  # yyyy mm DD HH MM
		self.DATAlimitseConsumption					=	20000.	# max swing
		self.DATAlimitseConsumptionAccum			=	+200.	# max increase = 200KWH
		self.DEVICE									=	{}
		self.DEVICE["0"]							=	copy.deepcopy(emptyDEVICE)
		self.dataColumnCount						=	0
		self.selectableStatesInDevice				=	[(0,"None")]
		self.oldDevNo								=	-1
		self.currentDevNo							=	0
		self.deviceIdNew							=	0
		self.deviceIdOld							=	-1
		self.listOfSelectedDataColumnsAndDevPropName=	[(0,"None")]                                              ## [seqnumber,devName-theMeasurement- prop]
		self.dataColumnToDevice0Prop1Index			=	[ [0,0]]
		self.devIdToTypeandName						=	{}
		self.listOfPreselectedDevices				=	[]
		self.addNewDevice							=	True
		self.pluginPrefs["DefineDevices"]			=	False
		self.pluginPrefs["text1-2"]					=	""
		self.pluginPrefs["selectedExistingOrNewDevice"]	= 0
		self.pluginPrefs["selectDeviceStatesOK"]	=	False
		self.pluginPrefs["ExpertsAndDevices"]		=	False
		self.pluginPrefs["DefineDevicesAndNew"]		=	False
		self.pluginPrefs["DefineDevicesAndOld"]		=	False
		self.pluginPrefs["DefineDevicesDummy"]		=	True
		
		self.preSelectDevices()                 # make list of valid devices
		return


	########################################	get device and plot parameters from file	########################################	########################################	######################################


	########################################
#	write configuration parameters to file
	########################################
	
	def writePlotParameters(self):

		xxyy=copy.deepcopy(self.PLOT)
		for nPlot in xxyy:
			for key in xxyy[nPlot]:
				if key =="lines":
					for line in xxyy[nPlot][key]:
						for key2 in xxyy[nPlot][key][line]:
							xxyy[nPlot][key][line][key2]= self.convertVariableOrDeviceStateToText(xxyy[nPlot][key][line][key2])
				else:
					xxyy[nPlot][key]= self.convertVariableOrDeviceStateToText(xxyy[nPlot][key])
		out ={"PLOT":xxyy,"DEVICE":self.DEVICE,"dataColumnToDevice0Prop1Index":self.dataColumnToDevice0Prop1Index,"dataOffsetInTimeDataNumbers":dataOffsetInTimeDataNumbers,"PNGdir":self.indigoPNGdir}
		f=self.openEncoding( self.matPLOTParameterFile, "w")
		f.write(json.dumps(out,sort_keys=True, indent=2))
		f.close()

		
		return
				
	########################################
	def resetPlotParameters(self):

		self.theFontDir		=	"/Library/Fonts/"
		self.theFont		=	"Arial Unicode.ttf"
	
		self.CurrentLineNo	= "0"
		self.PLOT			= {}



		## Make list of fonts:
		self.fontNames		= []
		self.fontNames2		= []
		self.fontNames2.append("System-font")
		self.fontNames2.append("System-font")
		nFont=1
		for fnames in os.listdir(self.theFontDir):
			if ".ttf" in fnames:						# only ttf fonts
				test = fnames.replace(" ","")			# for test remove blanks
				if test[:-4].isalnum():					# remove non ascii names ie chinese
					nFont+=1
					self.fontNames.append((nFont,fnames))		# add to list
					self.fontNames2.append(fnames)
		self.fontNames.append((1,"System-font"))
	

		return
		
	########################################
	def getConsumptionDataFromFile(self):
		self.periodTypeForConsumptionType={}
		self.lastConsumptionPeriodBinWithData ={}
		for i in range(noOfConsumptionTypes):
			self.periodTypeForConsumptionType[availConsumptionTypes[i]]= availCostTypes[0]		# set it to  "Period"
			self.lastConsumptionPeriodBinWithData[availConsumptionTypes[i]] =0
		self.consumptionCostData={}

		for consumptionType in availConsumptionTypes:			# add emptycost if cost does not exist
			xxx = []
			for j in range(noOfCostTimePeriods+1):
				xxx.append(copy.deepcopy(emptyCost))
			self.consumptionCostData[consumptionType]=xxx


		
		try:
			f=self.openEncoding(self.userIndigoPluginDir+"data/consumptionCost","r")
			self.consumptionCostData =json.loads(f.read())
			f.close()
		except:
				pass



		for consumptionType in availConsumptionTypes:			# add emptyCost if cost does not exist
			if consumptionType in self.consumptionCostData:
				ccD = self.consumptionCostData[consumptionType]
				pTFCT=self.periodTypeForConsumptionType
				pTFCT[consumptionType]= availCostTypes[1]		# set defualt to it to  "WeekDay"
				for n in range(0,noOfCostTimePeriods+1):
					if str(ccD[n]["Period"])==emptyCost["Period"]:ccD[n]["Period"]=emptyCost["Period"]
					if ccD[n]["Period"]<emptyCost["Period"]:	pTFCT[consumptionType] ="Period"
					if ccD[n]["day"]<9:							pTFCT[consumptionType] ="WeekDay"
				continue



		self.getLastConsumptionyCostPeriodBinWithData()  # set it to 0


		self.valuesFromIndigo 	=[[[0 for l in range(noOfValuesMeasured)] for i in range(self.dataColumnCount+1)] for k in range(noOfTimeTypes)]
		self.consumedDuringPeriod ={}

		try:
			f=self.openEncoding(self.userIndigoPluginDir+"data/consumedDuringPeriod","r")
			self.consumedDuringPeriod =json.loads(f.read())
			f.close()
		except  Exception as e:
			self.consumedDuringPeriod ={}
			self.indiLOG.log(30,"..../data/consumedDuringPeriod  file not available, resetting consumption data to 0")

		# check if format is good, if not reset
		if len(self.consumedDuringPeriod) >0:
			try:
				for theCol in self.consumedDuringPeriod:
					x=self.consumedDuringPeriod[theCol][0]["testDayHour"]
			except:
				self.indiLOG.log(40,"..../data/consumedDuringPeriod  file old format, resetting consumption data to 0")
				self.consumedDuringPeriod ={} # reseting  from old format
		

		try:
			f=self.openEncoding(self.userIndigoPluginDir+"data/valuesFromIndigo","r")
			self.valuesFromIndigo  =json.loads(f.read())
			f.close()
			self.initBy		="file"
		except  Exception as e:
			self.indiLOG.log(40," Line '%s' msg:'%s'" % (sys.exc_info()[2].tb_lineno, e)+" resetting valuesFromIndigo to 0)")
			self.valuesFromIndigo 	=[[[0 for l in range(noOfValuesMeasured)] for i in range(self.dataColumnCount+1)] for k in range(noOfTimeTypes)]


		if len(self.valuesFromIndigo[0][0] ) <noOfValuesMeasured:
			self.valuesFromIndigo 	=[[[0 for l in range(noOfValuesMeasured)] for i in range(self.dataColumnCount+1)] for k in range(noOfTimeTypes)]
			self.initBy		="reset"
		if len(self.valuesFromIndigo[0] ) <self.dataColumnCount+1:
			self.valuesFromIndigo 	=[[[0 for l in range(noOfValuesMeasured)] for i in range(self.dataColumnCount+1)] for k in range(noOfTimeTypes)]
			self.initBy		="reset"
		if len(self.valuesFromIndigo) <noOfTimeTypes:
			self.valuesFromIndigo 	=[[[0 for l in range(noOfValuesMeasured)] for i in range(self.dataColumnCount+1)] for k in range(noOfTimeTypes)]
			self.initBy		="reset"
		try:
			f.close()
		except:
			pass

		try:
			for devNo in self.DEVICE:
				for stateNo in range(1,noOfStatesPerDeviceG+1):
					try:
						theCol= self.DEVICE[devNo]["stateToIndex"][stateNo]
					except:
						self.indiLOG.log(40," device is malformed, fixing: {}".format(self.DEVICE[devNo]))
						self.DEVICE[devNo]["stateToIndex"]=[0,0,0,0,0,0,0,0,0]
						return -1
					if theCol ==0: continue
					if self.DEVICE[devNo]["measurement"][stateNo].find("Consumption")==-1 and  self.DEVICE[devNo]["measurement"][stateNo] != "integrate"  and  self.DEVICE[devNo]["measurement"][stateNo] != "eventCOUNT":
						self.DEVICE[devNo]["resetType"][stateNo]="0"
						if str(theCol) in self.consumedDuringPeriod:
							del self.consumedDuringPeriod["{}".format(theCol)]
					else:
						if not str(theCol) in self.consumedDuringPeriod:
							self.consumedDuringPeriod["{}".format(theCol)] = copy.deepcopy(emptyconsumedDuringPeriod)

		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.indiLOG.log(40," device data: {}".format(self.DEVICE))


		self.putconsumedDuringPeriod()
		self.putConsumptionCostData()


			
		return 1


	########################################
	def putconsumedDuringPeriod(self):
		try:
			f=self.openEncoding(self.userIndigoPluginDir+"data/consumedDuringPeriod","w")
			f.write(json.dumps(self.consumedDuringPeriod))
			f.close()
			f=self.openEncoding(self.userIndigoPluginDir+"data/valuesFromIndigo","w")
			f.write(json.dumps(self.valuesFromIndigo))
			f.close()
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			pass

		return
	########################################
	def putConsumptionCostData(self):
		try:
			f=self.openEncoding(self.userIndigoPluginDir+"data/consumptionCost","w")
			f.write(json.dumps(self.consumptionCostData))
			f.close()
		except  Exception as e:
			self.indiLOG.log(40,"in Line '%s' has error='%s'" % ( sys.exc_info()[2].tb_lineno, e))
			pass
		return
	
	
	
	########################################
	def getLastConsumptionyCostPeriodBinWithData(self):
	#,consumptionType="eConsumption",consumptionPeriod="Period"):
		for consumptionType in availConsumptionTypes:
			consumptionPeriod = self.periodTypeForConsumptionType[consumptionType]
			self.lastConsumptionPeriodBinWithData[consumptionType]=0
			if consumptionPeriod =="Period":
				for lastPeriod in range(noOfCostTimePeriods,0,-1):
					if self.consumptionCostData[consumptionType][lastPeriod]["Period"] <emptyCost["Period"]:
							if self.consumptionCostData[consumptionType][lastPeriod]["cost"][0]>0.:
								self.lastConsumptionPeriodBinWithData[consumptionType]= lastPeriod
								break
			else:
				for lastPeriod in range(noOfCostTimePeriods,0,-1):
					if self.consumptionCostData[consumptionType][lastPeriod]["day"] <9:
						if self.consumptionCostData[consumptionType][lastPeriod]["day"] <9:
							if self.consumptionCostData[consumptionType][lastPeriod]["cost"][0]>0.:
								self.lastConsumptionPeriodBinWithData[consumptionType]= lastPeriod
								break
		return
	########################################
	def getCurrentCostTimeBin(self, timeString,consumptionType):
		currCostTimeBin=0
		try:
			if timeString=="0":
				self.dd=datetime.datetime.now()
				xx = self.dd.strftime("%Y%m%d%H")
			else:
#				self.dd = datetime.datetime.strptime(timeString[:12],'%Y%m%d%H%M')  # this is a factor of 4.5 slower than the next line
				self.dd = datetime.datetime(int(timeString[0:4]),int(timeString[4:6]),int(timeString[6:8]),int(timeString[8:10]),int(timeString[10:12]))
				xx = (timeString[:10])
			x=self.dd
			
			lastCostBinWithValues= 0
		
			consumptionPeriod=self.periodTypeForConsumptionType[consumptionType]
			if self.lastConsumptionPeriodBinWithData[consumptionType] !=0:
				cCD = self.consumptionCostData[consumptionType]
				if consumptionPeriod == "Period":
					for i in range(self.lastConsumptionPeriodBinWithData[consumptionType],0,-1):
						if cCD[i]["Period"] ==emptyCost["Period"]:	continue
						if cCD[i]["Period"] > xx:			continue
						currCostTimeBin=i
						for jj in range(noOfCosts,0,-1):
							if cCD[currCostTimeBin]["cost"][jj-1] >0:
								lastCostBinWithValues= jj-1
								break
						break
				else:
					day 	=	x.weekday()
					hour 	=	x.hour
					for i in range(self.lastConsumptionPeriodBinWithData[consumptionType],0,-1):
						if cCD[i]["day"]	> day and cCD[i]["day"] >=0 :	continue  # day < 0 = all days
						if cCD[i]["hour"]	> hour:							continue
						currCostTimeBin=i
						for jj in range(noOfCosts,0,-1):
							if cCD[currCostTimeBin]["cost"][jj-1] >0:
								lastCostBinWithValues= jj-1
								break
						break

		except  Exception as e:
			self.indiLOG.log(40,"bad time string supplied.. '%s' in Line '%s' has error='%s'" % (timeString, sys.exc_info()[2].tb_lineno, e))
		return currCostTimeBin, lastCostBinWithValues
	########################################
	def getCurrentResetPeriod(self, timeString, resetPeriods, lastRbin):

		try:
			if timeString=="0":	x = time.strftime("%Y%m%d%H",time.localtime())
			else:				x = timeString[:10]
			
			nOfPeriods=len(resetPeriods)
			for nn in range(max(lastRbin,0), nOfPeriods):
#			for nn in range(0, nOfPeriods):
				Tbin= str(resetPeriods[nn])
				if x >= resetPeriods[nn]: continue
				return nn-1
			return nOfPeriods-1
		except  Exception as e:
			self.indiLOG.log(40,"bad time string supplied.. '%s' in Line '%s' has error='%s'" % (timeString, sys.exc_info()[2].tb_lineno, e))
		return 0
		
	########################################
	def calcConsumptionCostValue(self,measuredValue, currentCostTimeBin,valueAtStartOfCostBin,lastCostBinWithData,lastmeasuredValue,consumptionType,doPrint=False):
		
		try:
			cCD=self.consumptionCostData[consumptionType][currentCostTimeBin]  # get cost bin / period
			measuredValue		-=valueAtStartOfCostBin		#17				# current measuredValue - measuredValue of beginning of cost bin.. we have to start at 0 consumed at beginning of cost period
			lastmeasuredValue	-=valueAtStartOfCostBin		#17
			if doPrint: self.indiLOG.log(20,"measuredValue {}".format(measuredValue)+";lastmeasuredValue {}".format(lastmeasuredValue)+ "; cCD {}".format(cCD))
			for cB in range(lastCostBinWithData,-1,-1):						# start at highest (existing) cost bin , work down.
				delta=measuredValue -cCD["consumed"][cB]					# is this in this cost/consumed bracket?
				if doPrint: self.indiLOG.log(20,"cb: {}".format(cb)+ " cost {}".format(cCD["cost"][cB])+"; delta {}".format(delta))
				if delta >=0:
					if cB ==0:
						return (delta)*cCD["cost"][cB],0.					# if yes return  consumed in this bracket * cost of this bracket

					if lastmeasuredValue > cCD["consumed"][cB]:
						return delta*cCD["cost"][cB],0.						# if yes return  consumed in this bracket * cost of this bracket

					return (  (cCD["consumed"][cB]- lastmeasuredValue)*cCD["cost"][cB-1]  +  delta*cCD["cost"][cB]  )    ,    (cCD["consumed"][cB]-cCD["consumed"][cB-1]) * cCD["cost"][cB-1]# if yes return  consumed in thsi barcket * cost of this bracket
		
		
			return 0,0																	# nothing found, return 0  should not happen or first consumed energy number is forced to be 0.0
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
	
	########################################
	def  getDeviceParametersFromFile(self,calledfrom=""):
		self.dataColumnToDevice0Prop1Index=[[0,0]]
		self.DEVICE={}
		self.DEVICE["0"] =copy.deepcopy(emptyDEVICE)
		self.dataColumnCount=0
		
		try:
			f=self.openEncoding(self.userIndigoPluginDir+"data/indexes","r")
			line = f.readline()
			f.close()
			if len(line)>2:
				self.dataColumnToDevice0Prop1Index	= json.loads(line.strip("\n"))
				self.dataColumnCount				= len(self.dataColumnToDevice0Prop1Index)-1
		except:
			try:
				f.close()
			except:
				pass
			try:
				self.dataColumnToDevice0Prop1Index	= json.loads(self.pluginPrefs["dataColumnToDevice0Prop1Index"])
				self.pluginPrefs["dataColumnToDevice0Prop1Index"]=""
				self.dataColumnCount = len(self.dataColumnToDevice0Prop1Index)-1
			except:
				pass

		if self.dataColumnCount >0:
			try:
				f=self.openEncoding(self.userIndigoPluginDir+"data/devices","r")
				line = f.readline()
				f.close()
				if len(line)>10:
					self.DEVICE	= json.loads(line.strip("\n"))
				else:
					if self.dataColumnCount>0:
						self.dataColumnCount =0
						self.dataColumnToDevice0Prop1Index=[[0,0]]
			except:
				try:
					f.close()
				except:
					pass
				try:
					if self.dataColumnCount >0:
						self.DEVICE						= json.loads(self.pluginPrefs["DEVICE"])
					self.pluginPrefs["DEVICE"]=""
				except:
					pass

		if len(self.DEVICE)<1:
			self.dataColumnCount =0
			self.dataColumnToDevice0Prop1Index=[[0,0]]
		
		self.dataColumnCount= len(self.dataColumnToDevice0Prop1Index)-1
		if self.dataColumnCount <=0:
				self.dataColumnCount =0
				self.dataColumnToDevice0Prop1Index=[[0,0]]
				self.DEVICE={}
				self.DEVICE["0"] =copy.deepcopy(emptyDEVICE)


		self.sqlLastID =["0" for i in range(self.dataColumnCount+1)]






#		check if devices that have no data, remove them
		devsToDelete=[]
		for nDev in self.DEVICE:
			if nDev =="0": continue
			try:
				ix= self.DEVICE[nDev]["Name"]
				if ix == "None": devsToDelete.append(n)
			except:
				devsToDelete.append(nDev)
		if len(devsToDelete)>0: self.indiLOG.log(30,"getDeviceParametersFromFile devsToDelete  {}".format(devsToDelete))

		for nDev in devsToDelete:
			self.indiLOG.log(30," deleting empty device{}".format(nDev))
			del self.DEVICE[nDev]


#		check if bad indexes to empty devices ...
#       dataColumnToDevice0Prop1Index:[[0, 0], [1, 3], [1, 4], [1, 5]] (first index is devce, second is state)
		indToDelete=[]
		for n in range(len(self.dataColumnToDevice0Prop1Index),-1):
			try:#                                                      device
				stateNo =self.dataColumnToDevice0Prop1Index[n,1]
				devNo =self.dataColumnToDevice0Prop1Index[n,0]
				ix = self.DEVICE["{}".format(devNo)]["state"][stateNo]
				if ix == "None": indToDelete.append(n)
			except:
				indToDelete.append(n)
		if len(indToDelete)>0: self.indiLOG.log(30,"getDeviceParametersFromFile in ToDelete {}".format(indToDelete))
			
		for n in indToDelete:
			del self.dataColumnToDevice0Prop1Index[n]


#		check if there are old data fields.. rename them
		for nDev in self.DEVICE:
			if nDev =="0": continue
			DEV=self.DEVICE[nDev]
			if DEV["Name"].find("Var") >-1: 	DEV["Name"] = DEV["Name"][4:]
			if "PropsDType" in DEV:
				DEV["measurement"] = copy.deepcopy(DEV["PropsDType"])
				del DEV["PropsDType"]
			if "PropsName" in DEV:
				DEV["state"] = copy.deepcopy(DEV["PropsName"])
				del DEV["PropsName"]
			if "PropToIndex" in DEV:
				DEV["stateToIndex"] = DEV["PropToIndex"]
				del DEV["PropToIndex"]
			if "Type" in DEV:
				DEV["devOrVar"] = DEV["Type"]
				del DEV["Type"]
			if "offset" not in DEV:
				DEV["offset"] = copy.deepcopy(emptyDEVICE["offset"])
			if "multiplier" not in DEV:
				DEV["multiplier"] = copy.deepcopy(emptyDEVICE["multiplier"])
			if "minValue" not in DEV:
				DEV["minValue"] = copy.deepcopy(emptyDEVICE["minValue"])
			if "maxValue" not in DEV:
				DEV["maxValue"] = copy.deepcopy(emptyDEVICE["maxValue"])
			if "fillGaps" not in DEV:
				DEV["fillGaps"] = copy.deepcopy(emptyDEVICE["fillGaps"])
			if "resetType" not in DEV:
				DEV["resetType"] = copy.deepcopy(emptyDEVICE["resetType"])
			if "nickName" not in DEV:
				DEV["nickName"] = copy.deepcopy(emptyDEVICE["nickName"])
				for stateNo in range(1,noOfStatesPerDeviceG+1):
					DEV["nickName"][stateNo] = self.getNickName(nDev,stateNo)
			else:
				for stateNo in range(1,noOfStatesPerDeviceG+1):
					if DEV["state"][stateNo]=="None":
						DEV["nickName"][stateNo]=""
					else:
						if DEV["nickName"][stateNo]=="":
							DEV["nickName"][stateNo] = self.getNickName(nDev,stateNo)
			
			for stateNo in range(1,noOfStatesPerDeviceG+1):
				try:
					theCol= DEV["stateToIndex"][stateNo]
				except:
					self.indiLOG.log(40," device is malformed, deleting: {}".format(DEV))
					DEV["stateToIndex"]=[0,0,0,0,0,0,0,0,0]
			DEV["resetType"][0]="0"
			for stateNo in range(1,noOfStatesPerDeviceG+1):
				try:
					if DEV["resetType"][stateNo]=="Period":
						DEV["resetType"][stateNo]="0"
				except:
					self.indiLOG.log(40,"DEV period failure  {}".format(DEV["resetType"][stateNo]))

		try:
			self.DEVICE["0"] =copy.deepcopy(emptyDEVICE)
		except:
			self.indiLOG.log(40,"getDeviceParametersFromFile error adding empty dev  calledfrom="+calledfrom)

		self.putDeviceParametersToFile(calledfrom="getDeviceParametersFromFile")

		return
		

	########################################
	def putDeviceParametersToFile(self,calledfrom=""):
		
		f=self.openEncoding(self.userIndigoPluginDir+"data/indexes","w")
		f.write(json.dumps(self.dataColumnToDevice0Prop1Index)+"\n")
		f.close()
		f=self.openEncoding(self.userIndigoPluginDir+"data/devices","w")
		f.write(json.dumps(self.DEVICE)+"\n")
		f.close()
#		self.pluginPrefs["dataColumnToDevice0Prop1Index"]	=	json.dumps(self.dataColumnToDevice0Prop1Index)

#		self.pluginPrefs["DEVICE"]							=	json.dumps(self.DEVICE)

#		self.pluginPrefs["sqlLastID"]						=	json.dumps(self.sqlLastID)

		return


	########################################	commands from plugin/indigoplot/  menue
	########################################	commands from plugin/indigoplot/  menue
	########################################	commands from plugin/indigoplot/  menue
	def inpDummy(self,valuesDict="",typeID=""):
		return
	########################################
	def inpPlotALL(self):
		self.indigoCommand.append("PlotALL")
		self.indiLOG.log(20,"command: PlotALL")
		return
	########################################
	def inpPrintData(self):
		self.indigoCommand.append("PrintData")
		self.indiLOG.log(20,"command: PrintData")
		return
	########################################
	def inpPrintdevStates(self):
		self.indigoCommand.append("PrintDevStates")
		self.indiLOG.log(20,"command: print device states")
		return
	########################################
	def inpPrintPlotData(self,valuesDict, menuId):
		self.indigoCommand.append("PrintPlotData:{}".format(valuesDict["selPrintToPlot"]))
		return valuesDict
	########################################
	def inpPrintDeviceData(self):
		self.indigoCommand.append("PrintDeviceData")
		self.indiLOG.log(20,"command: PrintDeviceData")
		return
	########################################
	def inpReloadSQL(self):
		if self.sqlDynamic =="None":
			self.indiLOG.log(20,"command: ReloadSQL ignored, FIRST SWITCH SQL ON in Configuration ")
			return
		self.indigoCommand.append("ReloadSQL")
		self.indiLOG.log(20,"command: ReloadSQL")
		return
	########################################
	def inpReloadSQL2Days(self):
		if self.sqlDynamic =="None":
			self.indiLOG.log(20,"command: ReloadSQL 2 DAYS  ignored, FIRST SWITCH SQL ON in Configuration ")
			return
		self.indigoCommand.append("ReloadSQL2Days")
		self.indiLOG.log(10,"command: Reload last 2 days from SQL")
		return
	########################################
	def inpSavePy(self):
		self.indigoCommand.append("inpSavePy")
		self.indiLOG.log(10,"command: create Python code for PLOTs in "+self.userIndigoPluginDir+"py/ManualSavedConfig.....py")
		return
	########################################
	def inpInstallGnuplot(self):
		self.indigoCommand.append("InstallGnuplot")
		self.indiLOG.log(20,"command: InstallGnuplot")
		return
	########################################
	def inpDebugON(self):
		self.debugLevel = ["all"]
		self.indiLOG.log(20,"command: debug ON")
		return
	########################################
	def inpDebugOFF(self):
		self.debugLevel = []
		self.indiLOG.log(20,"command: debug OFF")
		return
	########################################
	def inpMATPLOT(self):
		self.gnuORmatSET("mat")
		self.indiLOG.log(20,"command: switch to MATPLOT")
		return
	########################################
	def inpGNUPLOT(self):
		self.gnuORmatSET("gnu")
		self.indiLOG.log(20,"command: switch to GNUPLOT")
		return
	########################################
	def inpPauseDataCollection(self):
		self.indigoCommand.append("PauseDataCollection")
		self.indiLOG.log(20,"command: PauseDataCollection")
		return
	########################################
	def inpContinueDataCollection(self):
		self.indigoCommand.append("ContinueDataCollection")
		self.indiLOG.log(20,"command: ContinueDataCollection")
		return
	########################################
	def inpFnameToLog(self):
		self.indigoCommand.append("fNameToLog")
		self.indiLOG.log(20,"command: write the looong path/filenames of plotfiles to logfile for copy and paste")
		return
	########################################
	def inpResetDeviceConfigurationParameters(self,valuesDict=None, typeId=""):
		self.indiLOG.log(20,"command: reset device parameters")


		self.removeThisDevice=[]
		for devNo in self.DEVICE:
			self.removeThisDevice.append(devNo)
		self.removeDevice()
		self.resetDeviceParameters()
		for nPlot in self.PLOT:
			self.PLOT[nPlot]["lines"]={}
			devID = int(nPlot)
			dev =indigo.devices[devID]
			props=dev.pluginProps
			props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
			dev.replacePluginPropsOnServer(props)

		self.doInitData()
		self.initializeData()
		self.putDiskData(0)
		self.putDiskData(1)
		self.putDiskData(2)
		self.indiLOG.log(20,"command: reset device parameters done ")
		self.redolineDataSource(calledfrom="inpResetDeviceConfigurationParameters")
				
		return
	########################################
	########################################
	def PrintPlotData(self,plotId):
	
		try:
			out = "\n"
			for nPlot in self.PLOT:
				if nPlot=="0": continue
				try:
					theName= indigo.devices[int(nPlot)].name
				except:
					continue
				if nPlot!= plotId and plotId !="": continue
				out += "\nPLOT:: {:25s} deviceID: {}".format(theName, nPlot)
			
				keylist = sorted(self.PLOT[nPlot].keys())
				for key in keylist:
					if key == "lines": 		continue
					if key == "errorCount":	continue
					out += "\n{:>25}>>{}<<".format(key, self.PLOT[nPlot][key])
			
				for nLine in range(1,50):
					line = str(nLine)
					if line in self.PLOT[nPlot]["lines"]:
						keylist = sorted(self.PLOT[nPlot]["lines"][line].keys())
						out2 = ""
						for k in keylist:
							if k == "lineKey": continue
							if k.find("line") == 0:
								out2 += "{}>{}<; ".format(k[4:], self.PLOT[nPlot]["lines"][line][k])
							else:
								out2 += " {}>{}< ".format(k, self.PLOT[nPlot]["lines"][line][k])
						out += "\n-l# {}/{:>25s}: {}".format(nLine, self.PLOT[nPlot]["lines"][line]["lineKey"], out2.strip(";"))
			self.indiLOG.log(10,"{}".format(out))
			self.indiLOG.log(20,"print dev/ state config : check plugin.log file")
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		return
	########################################
	########################################
	def PrintDeviceData(self):
		try:
			outLog = "\n"
			#		  1234  1234567 123456789012345 1234567890123456789012345 123456
			outLog+= "\nDev#, dev/var ID============= Name                      Status" 
			#			 12345678901234567890 12345678901234567890 1234567890 1234567890 1234567890 1234567890 12345 123456 123456789012
			outLog+= "\n   ---------------State Measurement              offset    multipl   minValue   maxValue   Col filGps    resetType nickName" 
			for nn in range (1,10):
				devNo  = str(nn)
				if devNo not in self.DEVICE: continue
				DEV = self.DEVICE[devNo]
				outLog += "\n{:4}  {:7} {:15} {:>20} ok:{}".format(devNo, DEV["devOrVar"], DEV["Id"], DEV["Name"], DEV["deviceNumberIsUsed"])
				for i in range(1,noOfStatesPerDeviceG+1):
					if DEV["state"][i] == "None": continue
					outLog += "\n{:2} {:>20} {:<20} {:>10} {:>10} {:>10} {:>10} {:>5} {:>6} {:>12} {:>50}".format(i, DEV["state"][i], DEV["measurement"][i], DEV["offset"][i], DEV["multiplier"][i], DEV["minValue"][i], DEV["maxValue"][i], DEV["stateToIndex"][i], DEV["fillGaps"][i], DEV["resetType"][i].strip("{u"), DEV["nickName"][i])
				
			outLog+= "\nIndex list for dataColumn to Device#/State# "
			outLog+= "\nColumn=Dev#/St#    Column=Dev#/St#    Column=Dev#/St#    Column=Dev#/St#    Column=Dev#/St#    "
			for jCol in range(1,self.dataColumnCount+1,5):
				for theCol in range( jCol,min(jCol+5,self.dataColumnCount+1),1):
					outLog+= "\n{:>6d}={:>4}/{:>3}  ".format( theCol, self.dataColumnToDevice0Prop1Index[theCol][0], self.dataColumnToDevice0Prop1Index[theCol][1])

			outLog+= "\n" 

			mapDayNumerToDayName=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday","EveryDay"]
			for consumptionType in self.consumptionCostData:
				try:
					len(consumptionType)
				except:
					self.indiLOG.log(40,"error, consumption type malformed: {}".format(consumptionType))
					continue
				try:
					outLog+= "\nConsumption Cost data;    type {}".format(consumptionType)+" {}".format(self.periodTypeForConsumptionType[consumptionType])
				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
				oneline = False
				for n in range(1,noOfCostTimePeriods+1) :
					cCD = self.consumptionCostData[consumptionType][n]
					outStr = ""
					if self.periodTypeForConsumptionType[consumptionType] =="Period":
						try:
							if str(cCD["Period"]).find("2999")==-1:
								outStr+= "    Period Schedule={}".format(n)
								outStr+= ":  YEAR: {}".format(cCD["Period"])[0:4]
								outStr+= ";  MONTH: {}".format(cCD["Period"])[4:6]
								outStr+= ";  DAY:  {}".format(cCD["Period"])[6:8]
								outStr+= ";  HOUR: {}".format(cCD["Period"])[8:10]
								outStr+= "; Cost@consumed=  "
								for i in range(noOfCosts):
									if cCD["cost"][i] != 0:
										outStr+= "Cost= {}".format(cCD["cost"][i]).rjust(5)+", starting @ {}".format(cCD["consumed"][i]).rjust(5) +" Units;  "
										oneline=True
						except  Exception as e:
							self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
					else:
						try:
							if cCD["day"] <9 :
								try:
									day = mapDayNumerToDayName[cCD["day"]].ljust(8)
								except:
									day = mapDayNumerToDayName[7]
								outStr += "    WeekDay Schedule={}".format(n)
								outStr += ":  day= "	+day
								outStr += ";  hour= {}".format(cCD["hour"]).ljust(2)+"; "
								for i in range(noOfCosts):
									if cCD["cost"][i] != 0:
										outStr+= "Cost= {}".format(cCD["cost"][i]).rjust(5)+", starting @ {}".format(cCD["consumed"][i]).rjust(5) +" Units;  "
										oneline=True
						except  Exception as e:
							self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

					if len(outStr) > 0:
						outLog+= "\n" 
						outLog+= outStr

				outLog+= " ...not defined"
			self.indiLOG.log(10, outLog)
			self.indiLOG.log(20,"print dev/ state config done, check plugin.log file")
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		return
	########################################
	def PrintDataToLog(self):
		for TTI in range(noOfTimeTypes):
			if self.decideMyLog("Plotting"): self.indiLOG.log(10, ("PlotType# "+ binTypeNames[TTI]).ljust(25)+"  Data Columns  ...")

			out = "c;w;m;y;-;-;"
			for theCol in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount+1+dataOffsetInTimeDataNumbers):
				out += str(theCol).rjust(7)+";"

			if self.decideMyLog("Plotting"): self.indiLOG.log(10,("Date        #M:").ljust(25)+ out)
			goodLines=0
			goodLinesSection=0
			for j in range(self.noOfTimeBins[i]):
				out =""
				goodData=False
				for theCol in range(1,1+dataOffsetInTimeDataNumbers):
						out += "%1d;"%float(self.timeDataNumbers[TTI][j][theCol])
				if (self.noOfTimeBins[i]-j) < 100: goodLines=0
				for theCol in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount+1+dataOffsetInTimeDataNumbers):
					try:
						out += "%7.1f;"%float(self.timeDataNumbers[TTI][j][theCol])
						goodData=True
					except:
						out += "no-data;"
				if goodData:
					goodLines+=1
					if goodLines > 25:
						goodLinesSection +=1
						if goodLinesSection >200:
							goodLines =0
							goodLinesSection =0
							if self.decideMyLog("Plotting"): self.indiLOG.log(10,("break  ").ljust(25)+"   ................... ")
						continue
					if self.decideMyLog("Plotting"): self.indiLOG.log(10,(str(self.timeBinNumbers[TTI][j]).ljust(14)+str(self.timeDataNumbers[TTI][j][0]).rjust(4)+": ").ljust(25) +out)
			out = "c;w;m;y;-;-;"
			for theCol in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount+1+dataOffsetInTimeDataNumbers):
				out += str(theCol).rjust(7)+";"
			if self.decideMyLog("Plotting"): self.indiLOG.log(10,("Date       #M").ljust(25)+ out,)
			self.indiLOG.log(10,"END")
	
		return
	########################################
	def PrintData(self):
		if self.decideMyLog("General"): self.indiLOG.log(10," printing data to formatted file")
		try:
			for TTI in range(noOfTimeTypes):
				f=self.openEncoding(self.fileData[TTI]+".formatted", "w")
				out = ""
				for theCol in range(1,self.dataColumnCount+1):
					out += str(theCol).rjust(7)+";"
				f.write("Date           #dat;W;M;Y;-;   n;{}\n".format(out))
				goodLines=0
				for j in range(self.noOfTimeBins[TTI]):
					out=""
					out += "%5d;"%int(float(self.timeDataNumbers[TTI][j][0]))
					for theCol in range(1,1+dataOffsetInTimeDataNumbers-1):
						out += "%1d;"%int(float(self.timeDataNumbers[TTI][j][theCol]))
					theCol =dataOffsetInTimeDataNumbers
					out += "%4d;"%int(float(self.timeDataNumbers[TTI][j][theCol]))
					goodData=False
					if (self.noOfTimeBins[TTI]-j) < 100: goodLines=0
					for theCol in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount+1+dataOffsetInTimeDataNumbers):
						try:
							if abs(float(self.timeDataNumbers[TTI][j][theCol])) > 99999:
								out += "%7d;"%int(float(self.timeDataNumbers[TTI][j][theCol]))
							elif abs(float(self.timeDataNumbers[TTI][j][theCol])) <10:
								out += "%7.4f;"%float(self.timeDataNumbers[TTI][j][theCol])
							elif abs(float(self.timeDataNumbers[TTI][j][theCol])) <100:
								out += "%7.3f;"%float(self.timeDataNumbers[TTI][j][theCol])
							elif abs(float(self.timeDataNumbers[TTI][j][theCol])) <1000:
								out += "%7.2f;"%float(self.timeDataNumbers[TTI][j][theCol])
							else:
								out += "%7.1f;"%float(self.timeDataNumbers[TTI][j][theCol])
							goodData=True
						except:
							out += "no-data;"
					if goodData:
						f.write( (str(self.timeBinNumbers[TTI][j]).ljust(14))+out+"\n")
				out=""
				for theCol in range(1,self.dataColumnCount+1):
					out += str(theCol).rjust(7)+";"
				f.write("Date           #dat;W;M;Y;-;   n;"+out+"\n")
				f.write("\nCurrent measurement values: \n")
				xxx=["currentValues.","lastMeasurem./T","#ofMeasuremts/LastM","LastT","TBI","FirstM-1","FirstT-1","LastM-1","LastT-1","TBI-1","LastM-2","LastT-2","TBI-2","13","14","15","16","17","18","19","20","21","22"]
				for NV in range(noOfValuesMeasured):
					out=(xxx[NV]+":").ljust(14+5+4+dataOffsetInTimeDataNumbers*2)
					for theCol in range(1,self.dataColumnCount+1):
						xxxxx = "*******;"
						x = float(self.valuesFromIndigo[TTI][theCol][NV])
						if NV==4 or NV==9 or NV==12:	xxxxx = ("%7d;"  %int(x))[-8:]
						elif NV<5 or float(self.valuesFromIndigo[TTI][theCol][9]) >0:
							if	 abs(x) > 99999:		xxxxx = ("%7d;" %int(x))[-8:]
							elif abs(x) <10:			xxxxx = ("%7.4f;"    %x)[-8:]
							elif abs(x) <100:			xxxxx = ("%7.3f;"    %x)[-8:]
							elif abs(x) <1000:			xxxxx = ("%7.2f;"    %x)[-8:]
							else:						xxxxx = ("%7.1f;"    %x)[-8:]
						out+= xxxxx
					f.write( out+"\n")
				
				out=""
				for theCol in range(1,self.dataColumnCount+1):
					out += str(theCol).rjust(7)+";"
				f.write("\nResetPeriod+Cost Parmeters: \n")
				out=""
				colList= []
				for col in self.consumedDuringPeriod:
					colList.append(col)
				f.write(" comsuption  columns {}".format(colList)+"\n")
				for val in emptyconsumedDuringPeriod[TTI]:
					out=str(val).ljust(32)+":"
					for col in range(1,self.dataColumnCount+1):
						if str(col) in colList:	out+="%7d;"%float(self.consumedDuringPeriod["{}".format(col)][TTI][val])
						else:					out+=" ".rjust(7)+";"
					f.write( out+"\n")
				out=""
				for theCol in range(1,self.dataColumnCount+1):
					out += str(theCol).rjust(7)+";"
				f.write((" ").ljust(33)+out+"\n")


				f.close()
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			try:
				f.close()
			except:
				pass

		return






#---------------  my first plot  in menue-------------

	########################################  create pick list for eleigible devices ie plots
	def filterPlotNames(self, filter="self",valesDict="none",typeId=""):
		self.PLOTlist=[]
		for nPlot in self.PLOT:
			name=self.PLOT[nPlot]["DeviceNamePlot"]
			self.PLOTlist.append((nPlot,"Edit: "+name))
		self.PLOTlist.append(("1","NEW: Name of plot"))
		if self.PLOTlistLast[1]!="":
			self.PLOTlist.append(("0","Edit last: "+self.PLOTlistLast[1]))
		return self.PLOTlist

	######################################## this is called once the new  plot name is selected
	def plotNameSelectedCALLBACK(self,  valuesDict=None,typeId=""):
		nPlot=str(valuesDict["nPlot"])
		## wrong/ no entry
		if nPlot =="" :
			valuesDict["fistPlotMessageText"] = "Please enter plot name"
			return valuesDict

		if nPlot=="0":
			nPlot = self.PLOTlistLast[0]


		## new plot requested, set flag
		if nPlot =="1":
			valuesDict["oldNew"] ="new"
			return valuesDict
		
		valuesDict["oldNew"] ="old"



		## for existing plots
		self.currentPlotName	= self.PLOT[nPlot]["DeviceNamePlot"]
		self.deviceId = nPlot
		lineInPlot=False
		
		if "lines" in self.PLOT[nPlot]:
			if "1" in self.PLOT[nPlot]["lines"]:
				lineInPlot=True
		else:
			self.PLOT[nPlot]["lines"]={}
		
		if not lineInPlot:
			self.PLOT[nPlot]["lines"]["1"] = copy.deepcopy(emptyLine)

		valuesDict["TitleText"]							=self.PLOT[nPlot]["TitleText"]
		valuesDict["TextSize"]							=self.PLOT[nPlot]["TextSize"]
		valuesDict["TextColor"]							=self.PLOT[nPlot]["TextColor"]
		valuesDict["Background"]						=self.PLOT[nPlot]["Background"]
		valuesDict["lineType"]							=self.PLOT[nPlot]["lines"]["1"]["lineType"]
		valuesDict["lineWidth"]							=self.PLOT[nPlot]["lines"]["1"]["lineWidth"]
		valuesDict["lineColor"]							=self.PLOT[nPlot]["lines"]["1"]["lineColor"]

		if self.PLOT[nPlot]["lines"]["1"]["lineToColumnIndexAfile"] =="":
			theCol=self.PLOT[nPlot]["lines"]["1"]["lineToColumnIndexA"]
			state=""
			devNo=0
			devID=0
			stateNo=0
			if theCol  > 0:
				devNo= self.dataColumnToDevice0Prop1Index[theCol][0]
				stateNo=self.dataColumnToDevice0Prop1Index[theCol][1]
				state = self.DEVICE["{}".format(devNo)]["state"][stateNo]
				devID = self.DEVICE["{}".format(devNo)]["Id"]
			valuesDict["selectedDeviceIDMFP"] = devID
			self.currentDeviceId = devID
			valuesDict["selDeviceStateMFP"] = state

		return valuesDict



	########################################   this is for new to be created  plots
	def buttonConfirNewPlotNameCALLBACK(self,  valuesDict="",typeId=""):
		self.currentPlotName =valuesDict["newPlotName"]
		return valuesDict

	########################################   this will create/ modify new / existing plot  (MFP= ModiFy Plot)
	def buttonConfirmSelectionMFPCALLBACK(self,  valuesDict=None, typeId=""):

		try:
			name= self.currentPlotName
		except:
			valuesDict["fistPlotMessageText"] = "Please enter configuration"
			return valuesDict
		logLevel= ""
		if "Restore" in self.debugLevel: logLevel= "1"
		resxy0= ""
		resxy1=""
		if valuesDict["plotSize"] =="850,350":	resxy0="850,350"
		else:									resxy1="1024,768"
		self.createOrModifyPlot({
			"deviceNameOfPlot"      : self.currentPlotName
			,"TitleText"            : valuesDict["TitleText"]
			,"TextSize"             : valuesDict["TextSize"]
			,"TextColor"            : valuesDict["TextColor"]
			,"resxy0"               : resxy0
			,"resxy1"               : resxy1
			,"Background"           : valuesDict["Background"]
			,"dataSource"           : u'mini'
			,"LeftLabel"            : u''
			,"LeftScale"            : u''
			,"LeftScaleRange"		: u''
			,"LeftScaleTics"		: u''
			,"LeftLog"				: u'linear'
			,"LeftScaleDecPoints"	: u'0'
			,"RightLabel"           : u''
			,"RightScale"            : u''
			,"RightScaleRange"		: u''
			,"RightScaleTics"		: u''
			,"RightLog"				: u'linear'
			,"RightScaleDecPoints"	: u'0'
			,"boxWidth"				: u'0.5'
			,"drawZeroLine"			: u'False'
			,"logLevel"             : logLevel
		})


		devID= int(self.currentDeviceId)
		if devID==0:
			valuesDict["fistPlotMessageText"] = "Please enter configuration"
			return valuesDict
		
		try:
			dev = indigo.devices[devID]
			devName= dev.name
			state = valuesDict["selDeviceStateMFP"]
			devOrVar="Dev-"
		except:
			dev = indigo.variables[devID]
			devName = dev.name
			state ="value"
			devOrVar="Var-"
		
		
		self.createOrModifyLine({
				"deviceNameOfPlot"                   : self.currentPlotName
				,"deviceOrVariableToBePlottedLineA"  : devName
				,"StateToBePlottedLineA"             : state
				,"devOrVarA"                         : devOrVar
				,"MeasurementLineA"                  : "average"
				,"lineNumber"                        : u'1'
				,"lineType"                          : copy.deepcopy(valuesDict["lineType"])
				,"lineWidth"                         : copy.deepcopy(valuesDict["lineWidth"])
				,"lineColor"                         : copy.deepcopy(valuesDict["lineColor"])
				,"lineKey"                           : copy.deepcopy(emptyLine["lineKey"])
				,"lineMultiplier"                    : copy.deepcopy(emptyLine["lineMultiplier"])
				,"lineOffset"                        : copy.deepcopy(emptyLine["lineOffset"])
				,"lineLeftRight"                     : copy.deepcopy(emptyLine["lineLeftRight"])
				,"lineEveryRepeat"					 : copy.deepcopy(emptyLine["lineEveryRepeat"])
				,"lineNumbersFormat"                 : copy.deepcopy(emptyLine["lineNumbersFormat"])
				,"lineNumbersOffset"                 : copy.deepcopy(emptyLine["lineNumbersOffset"])
				,"lineSmooth"                        : copy.deepcopy(emptyLine["lineSmooth"])
				,"logLevel"                          : logLevel
			})

		for nPlot in self.PLOT:
			if self.PLOT[nPlot]["DeviceNamePlot"] == self.currentPlotName:
				valuesDict["nPlot"]= nPlot
				valuesDict["oldNew"] ="old"
				self.plotNow(createNow=self.PLOT[nPlot]["DeviceNamePlot"],showNow="")
				self.PLOTlistLast[0] =nPlot
				self.PLOTlistLast[1] =self.currentPlotName
				nCol = self.PLOT[nPlot]["lines"]["1"]["lineToColumnIndexA"]
				devNo		=	self.dataColumnToDevice0Prop1Index[nCol][0]
				stateNo		=	self.dataColumnToDevice0Prop1Index[nCol][1]
				self.PLOTlistLast[2] = devNo
				self.PLOTlistLast[3] = stateNo
				self.pluginPrefs["PLOTlistLast"]=json.dumps(self.PLOTlistLast)
				break
		return valuesDict


	########################################   this will show plot on screen
	def showPlotMFPCALLBACK(self,  valuesDict=None, typeId=""):
		try:
			self.plotNow(createNow=self.currentPlotName,showNow=self.currentPlotName)
		except:
			self.indiLOG.log(10,"showPlotMFPCALLBACK:  plot not confirmed ")
		return valuesDict

	########################################
	def filterselDeviceStatesMFP (self, filter="",  valuesDict="",typeId=""):
		devID= int(self.currentDeviceId)
		if devID !=0:
			try:
				dev = indigo.devices[devID]
				self.deviceDevOrVarNew="Dev-"
			except:
				dev = indigo.variables[devID]
				self.deviceDevOrVarNew="Var-"
		else:
			return [(0,0)]

		try:
			retList= self.preSelectStates(devID)
			return retList
		except:
			return [(0,0)]


#---------------  my first plot ------------- END









	########################################
	def filterselSQLdevState(self,  filter, valuesDict, xxx, ID=""):
		retList=[]
		for n in range(len(self.listOfSelectedDataColumnsAndDevPropNameSORTED)):
			if self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0]==0: continue
			if self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0]==-1: continue
			retList.append((self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0],self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][1]))
		return retList


	########################################
	def filterColumns(self,  filter, valuesDict,xxx):
		retList=[]
		for n in range(len(self.listOfSelectedDataColumnsAndDevPropNameSORTED)):
			if self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0]==0: continue
			if self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0]==-1: continue
			retList.append((self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0],"%02d"%self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0]+"-"+self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][1]))
		return retList






	########################################
	def getLastSQLforEventdata(self, colList):
		try:
			if max(self.sqlHistListStatus) > 0: 
				if self.decideMyLog("SQL"): self.indiLOG.log(30,"waiting for regular SQL job to finish before we do EVENT data: ")    
				return 
			devstateList = "COL,devID,State: "
			for tc in colList:
				theCol = int(tc)
				devNo= self.dataColumnToDevice0Prop1Index[theCol][0]																			# for shorter typing
				stateNo=self.dataColumnToDevice0Prop1Index[theCol][1]
				theDeviceId		= "{}".format(self.DEVICE["{}".format(devNo)]["Id"])
				theState	    = self.DEVICE["{}".format(devNo)]["state"][stateNo]
				devstateList += tc+"/"+theDeviceId+"/"+theState+";"
				self.sqlColListStatus[theCol] = 10
				if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done"):	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done")
				self.devicesAdded = 5
				self.eventSQLjobState = "requested"
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"started sql job for EVENT data: {}".format(devstateList) )    
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.indiLOG.log(10,"theCol:{}  len(dataCo...):{}  dataColumnToDevice0Prop1Index:{}".format(tc, len(self.dataColumnToDevice0Prop1Index), self.dataColumnToDevice0Prop1Index))




	########################################
	def buttonConfirmSQLDevStateCALLBACKaction(self, action1, typeId=""):
		self.buttonConfirmSQLDevStateCALLBACK(valuesDict=action1.props, typeId="")

	########################################
	def buttonConfirmSQLDevStateCALLBACK(self, valuesDict, typeId=""):
		theCol= int(valuesDict["selSELdevStateColumn"])

		for n in range(len(self.listOfSelectedDataColumnsAndDevPropNameSORTED)):
			if self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][0] == theCol:
				self.indiLOG.log(10," DevStateSelected to re-read:  # {}".format(theCol) +" : "+self.listOfSelectedDataColumnsAndDevPropNameSORTED[n][1])
				break
		
		
		devNo= self.dataColumnToDevice0Prop1Index[theCol][0]																			# for shorter typing
		stateNo=self.dataColumnToDevice0Prop1Index[theCol][1]
		theDeviceId		= "{}".format(self.DEVICE["{}".format(devNo)]["Id"])
		theState	= self.DEVICE["{}".format(devNo)]["state"][stateNo]
		if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState):			
			os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState)
			try:    os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done")
			except: pass
			if self.decideMyLog("SQL"): self.indiLOG.log(10," delete: sql/"+theDeviceId+"-"+theState)
		self.FirstBinDate					="0000"+"00"+"00"+"00"+"00"+"00"  # yyyy mm DD HH
		self.sqlColListStatus[theCol]  = 10
		self.sqlHistListStatus[theCol] = 50
		self.devicesAdded 			= 5
		self.newPREFS				= True
		return valuesDict



	########################################
	def filterselBackUpFiles(self,  filter="self", valuesDict=None, typeId=""):
		retList =[(0,0)]         	# nothing there yet
		pyFiles = os.listdir(self.userIndigoPluginDir+'py')
		pyFiles.sort()

		for pyFile in pyFiles:
			if pyFile.find(".py") >-1:	# use only fy files
				retList.append((pyFile,pyFile))
		
		return retList
	
	########################################
	def buttonConfirmBackUpFileCALLBACK(self, valuesDict=None, typeId=""):
		self.BackupFileSelected = valuesDict["selBackUpFile"]
		nn=0
		ff = "{}py/{}".format(self.userIndigoPluginDir, self.BackupFileSelected)
		self.indiLOG.log(20," BackupFileSelected {}".format(ff))
		f=self.openEncoding( ff ,"r")

		pyCommands = ""
		for line in f.readlines():
			self.indiLOG.log(20," backup line executing: {}".format(line))
			if line.find("#") ==0: continue
			if line =="": continue
			if len(line) < 2: continue
			if line.find("ndigo.server.getPlugin(")>-1: continue
			if line.find("isEnabled()")>-1: continue
			pp = line.find("' n     ,\"logLevel")
			if pp >-1:
				line = line[:pp]+"'  "+line[pp+4:]
			if line.find("executeAction") >-1:
				# replace:
				#  plug.executeAction("addDeviceAndStateToSelectionList"      , props ={"devic....            ==>            self.addDeviceAndStateToSelectionList(    action ={"devic....
				position = line.find('"')
				line2	 = line[position+1:]
				line	 = "self."+line2.replace('"','(',1).replace(',','',1).replace('props','action',1)
			nn+=1
			
			if self.decideMyLog("Plotting"): self.indiLOG.log(10,"{}  {}".format(nn, line.strip("\n")))
			pyCommands+=line
		self.waitWithSQL =True
		f.close()
		try:
			exec(pyCommands)
		except:
			exc_type, exc_obj, tb = sys.exc_info()
			f = tb.tb_frame
			lineno = tb.tb_lineno
			filename = f.f_code.co_filename
			linecache.checkcache(filename)
			line = linecache.getline(filename, lineno, f.f_globals)
			self.indiLOG.log(40,"Error importing old configuration, statement  in  restore file is bad:\n                             {}".format(exc_obj))
		self.waitWithSQL = False
		

		self.indiLOG.log(10," Restore config finished")
		return valuesDict


	########################################
	def buttonConfirmdeleteColumnCALLBACK(self, valuesDict=None, typeId=""):
		columnToRemove = int(valuesDict["columnToRemove"])
		devNo   = self.dataColumnToDevice0Prop1Index[columnToRemove][0]
		stateNo = self.dataColumnToDevice0Prop1Index[columnToRemove][1]
		self.indiLOG.log(30, "removing column:{}".format(columnToRemove)+"  devNo:{}".format(devNo)+"  stateNo:{}".format(stateNo)  )
		self.removePropFromDevice(devNo,stateNo,writeD=True,reDo=True)
		return valuesDict





	########################################
	def FnameToLog(self,DeviceName="all"):
		self.indiLOG.log(20,"IndigoPlot png file names: copy and paste to field <URL:>  below Display: <RefreshingImage URL>")
		for nPlot in self.PLOT:
			if self.PLOT[nPlot]["NumberIsUsed"] ==1:
				if DeviceName =="all" or DeviceName == self.PLOT[nPlot]["DeviceNamePlot"]:
					for tt in range(0,noOfTimeTypes):
						for ss in range(0,2):
							Fnamepng= self.indigoPNGdir+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotTimeNames[tt]+"-"+self.plotSizeNames[ss]+".png"
							self.indiLOG.log(20,"   file://"+Fnamepng.replace(" ","%20"))
	
		if DeviceName =="all": self.indiLOG.log(20,"command: write the looong path/filenames of plotfiles to logfile for copy and paste .. DONE")
		return


	########################################	commands from plugin/indigoplot/  menue	END
	########################################	commands from plugin/indigoplot/  menue	END
	########################################	commands from plugin/indigoplot/  menue	END
	########################################	commands from plugin/indigoplot/  menue	END



	
	########################################
	def createPy(self, aType=""):


		d0= str(datetime.datetime.now()).replace(":","").replace("-","").replace(" ","-")[:15].strip("-")
		if   aType=="manual":	 fName="py/ManuallySavedConfig--"+d0+".py"
		elif aType=="export":	 fName="data/export.py"
		elif aType=="exportMini":fName="data/exportMini"
		else:					 fName="py/RestoreConfigAndPlots-"+d0+".py"
		try:
	#		if os.path.isfile(self.userIndigoPluginDir+"py/examplesToCreateAndManagePlots.py"):
	#			os.rename(self.userIndigoPluginDir+"py/examplesToCreateAndManagePlots.py", self.userIndigoPluginDir+"py/examplesToCreateAndManagePlots-"+d0+"-.py")
				
			f=self.openEncoding(self.userIndigoPluginDir+fName , "w")

			if aType=="exportMini":
				kk = 0
				for nPlot in self.PLOT:
					kk+=1
					PL =self.PLOT[nPlot]
					if PL["dataSource"] !="mini": continue
					f.write(u'{}'.format(PL["DeviceNamePlot"]).replace("'","\'")+":{")
					f.write(u'"deviceNameOfPlot":"{}'.format(PL["DeviceNamePlot"]).replace("'","\'")+'"')
					f.write(u',"PlotType":"{}'.format(PL["PlotType"])+'"')
					f.write(u',"XYvPolar":"{}'.format(PL["XYvPolar"])+'"')
					f.write(u',"Grid":"{}'.format(PL["Grid"])+'"')
					f.write(u',"Border":"{}'.format(PL["Border"])+'"')
					f.write(u',"PlotFileOrVariName":"{}'.format(PL["PlotFileOrVariName"])+'"')
					f.write(u',"TitleText":"{}'.format(PL["TitleText"]).replace("'","\'")+'"')
					f.write(u',"TextSize":"{}'.format(PL["TextSize"])+'"')
					f.write(u',"TextMATFont":"{}'.format(PL["TextMATFont"])+'"')
					f.write(u',"TextFont":"{}'.format(PL["TextFont"])+'"')  ## could be 0, need to fix
					f.write(u',"TextColor":"{}'.format(PL["TextColor"])+'"')
					f.write(u',"LeftScaleRange":"{}'.format(PL["LeftScaleRange"])+'"')
					f.write(u',"LeftScaleTics":"{}'.format(PL["LeftScaleTics"])+'"')
					f.write(u',"LeftLog":"{}'.format(PL["LeftLog"])+'"')
					f.write(u',"LeftScaleDecPoints":"{}'.format(PL["LeftScaleDecPoints"])+'"')
					f.write(u',"LeftLabel":"{}'.format(PL["LeftLabel"]).replace("'","\'")+'"')
					f.write(u',"resxy0":"{}'.format(PL["resxy"][0])+'"')
					f.write(u',"resxy1":"{}'.format(PL["resxy"][1])+'"')
					f.write(u',"MinuteBinNoOfDays":"{}'.format(PL["MHDDays"][0])+'"')
					f.write(u',"HourBinNoOfDays":"{}'.format(PL["MHDDays"][1])+'"')
					f.write(u',"DayBinNoOfDays":"{}'.format(PL["MHDDays"][2])+'"')
					f.write(u',"MinuteBinShift":"{}'.format(PL["MHDShift"][0])+'"')
					f.write(u',"HourBinShift":"{}'.format(PL["MHDShift"][1])+'"')
					f.write(u',"DayBinShift":"{}'.format(PL["MHDShift"][2])+'"')
					f.write(u',"MinuteXScaleFormat":"{}'.format(PL["MHDFormat"][0])+'"')
					f.write(u',"HourXScaleFormat":"{}'.format(PL["MHDFormat"][1])+'"')
					f.write(u',"DayXScaleFormat":"{}'.format(PL["MHDFormat"][2])+'"')
					f.write(u',"Background":"{}'.format(PL["Background"])+'"')
					f.write(u',"TransparentBlocks":"{}'.format(PL["TransparentBlocks"])+'"')
					f.write(u',"TransparentBackground":"{}'.format(PL["TransparentBackground"])+'"')
					f.write(u',"dataSource":"{}'.format(PL["dataSource"])+'"')
					f.write(u',"drawZeroLine":"{}'.format(PL["drawZeroLine"])+'"')
					f.write(u',"compressPNGfile":"{}'.format(PL["compressPNGfile"])+'"')
					f.write(u',"enabled":"{}'.format(PL["enabled"])+'"')
					nLine = "1"
					if nLine in PL["lines"]:
						f.write(u',"lines":{')
						f.write(u'"lineNumber":"{}'.format(nLine)+'"')
						f.write(u',"lineType":"{}'.format(PL["lines"][nLine]["lineType"])+'"')
						f.write(u',"lineKey":"{}'.format(PL["lines"][nLine]["lineKey"])+'"')
						f.write(u',"lineShift":"{}'.format(PL["lines"][nLine]["lineShift"])+'"')
						f.write(u',"lineWidth":"{}'.format(PL["lines"][nLine]["lineWidth"])+'"')
						f.write(u',"lineColor":"{}'.format(PL["lines"][nLine]["lineColor"])+'"')
						f.write(u',"lineMultiplier":"{}'.format(PL["lines"][nLine]["lineMultiplier"])+'"')
						f.write(u',"lineOffset":"{}'.format(PL["lines"][nLine]["lineOffset"])+'"')
						f.write(u',"lineLeftRight":"{}'.format(PL["lines"][nLine]["lineLeftRight"])+'"')
						f.write(u',"lineEveryRepeat":"{}'.format(PL["lines"][nLine]["lineEveryRepeat"])+'"')
						f.write(u',"lineFromTo":"{}'.format(PL["lines"][nLine]["lineFromTo"])+'\'     ## if not 0 use as x range for THIS line  format= from:to \n')
						f.write(u',"lineNumbersFormat":"{}'.format(PL["lines"][nLine]["lineNumbersFormat"])+'"')
						f.write(u',"lineNumbersOffset":"{}'.format(PL["lines"][nLine]["lineNumbersOffset"])+'"')
						f.write(u',"lineSmooth":"{}'.format(PL["lines"][nLine]["lineSmooth"])+'"')
						
						if PL["PlotType"] == "dataFromTimeSeries":
							if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexAfile"] =="":
								index =int(PL["lines"][nLine]["lineToColumnIndexA"])
								devNo = int(self.dataColumnToDevice0Prop1Index[index][0])
								DEV		=	self.DEVICE["{}".format(devNo)]
								stateNo = int(self.dataColumnToDevice0Prop1Index[index][1])
								if DEV["Name"].find("Var-") ==-1:
									f.write(u',"deviceOrVariableToBePlottedLineA":"{}'.format(DEV["Name"]).replace("'","\'")+'"')
								else:
									f.write(u',"deviceOrVariableToBePlottedLineA":"{}'.format(DEV["Name"][4:])+'"')
								f.write(u',"devOrVarA":"{}'.format(DEV["devOrVar"])+'"')
								f.write(u',"StateToBePlottedLineA":"{}'.format(DEV["state"][stateNo])+'"')
								f.write(u',"MeasurementLineA":"{}'.format(DEV["measurement"][stateNo])+'"')
								f.write(u',"multiplierA":"{}'.format(DEV["multiplier"][stateNo])+'"')
								f.write(u',"offsetA":"{}'.format(DEV["offset"][stateNo])+'"')
								f.write(u',"minValueA":"{}'.format(DEV["minValue"][stateNo])+'"')
								f.write(u',"maxValueA":"{}'.format(DEV["maxValue"][stateNo])+'"')
								f.write(u',"fillGapsA":{}'.format(DEV["fillGaps"][stateNo]))
								f.write(u',"resetTypeA":"'+json.dumps(DEV["resetType"][stateNo])+'"')
							f.write(u',"lineFunc":"{}'.format(PL["lines"][nLine]["lineFunc"])+'"')
						f.write(u'}')
					f.write(u'}\n')


			if aType != "exportMini":
				f.write(u'#########  python file you can use to create YOUR existing plots.\n')
				f.write(u'#########   They can be used in action groups or your plugins, use them as examples.\n')
				f.write(u'#########  In addtions examples are shown how to delete plots, devices .. \n')
				f.write(u'#########     and how to add device/states to the tracking list for plots  \n')
				f.write(u'\n')
				f.write(u'\n')
				f.write(u'plug = indigo.server.getPlugin("'+self.pluginId+'")\n')
				f.write(u'if not plug.isEnabled(): return   #### INDIGOplotD must be enabled, otherwise nothing here works\n')

				f.write(u'\n')
				f.write(u'######### \n')
				f.write(u'######### section to change general configuration parameters these are YOUR current config paramaters\n')
				f.write(u'#########  comment out the parameters you dont like to change with a # in the begining of the line\n')
				f.write(u'######### \n')
				f.write(u'\n')
				f.write(u'ppp ={\n')
				f.write(u'     "debugLevel":               u\''+json.dumps(self.debugLevel)+'\'                ### All,Restore,SQL,Initial, ...\n')
				f.write(u'    ,"gnuPlotBin":               u\'{}'.format(self.gnuPlotBinary)+'\'               ### path to GNUplot binary  could be eg /usr/local/bin/gnuplot\n')
				f.write(u'    ,"gnuORmat":                 u\'{}'.format(self.gnuORmat)+'\'                    ### mat or gnu\n')
				f.write(u'    ,"sqlDynamic":               u\'{}'.format(self.sqlDynamic)+'\'                  ###  batch or batch2Days or None \n')
				f.write(u'    ,"indigoPNGdir":             u\'{}'.format(self.indigoPNGdir)+'\'                ### psetConfigParametersath to plotdirectory  \n')


				for consumptionType in self.consumptionCostData:
					for n in range(1,noOfCostTimePeriods+1):
						EE=self.consumptionCostData[consumptionType][n]
						xstring='    ,"'+consumptionType+str(n)+'":             u\''
						if self.consumptionCostData[consumptionType][n]["Period"] =="Period":
							if EE["Period"].find("2999")>-1: 	continue
							xstring+='{"Period":{}'.format(EE["Period"])
							xstring+=',"day":{}'.format(EE["day"])
							xstring+=',"hour":{}'.format(EE["hour"])
						else:
							if EE["day"]	>=9: continue
							xstring+='{"day":{}'.format(EE["day"])
							xstring+=',"hour":{}'.format(EE["hour"])
							xstring+=',"Period":{}'.format(EE["Period"])

						xstring+=',"cost":{}'.format(EE["cost"])
						xstring+=',"consumed":{}'.format(EE["consumed"])+'}'
						f.write(xstring+'\' \n')
				f.write(u'    ,"logLevel":                 u\'1\'}\n')
				f.write(u'plug.executeAction("setConfigParameters"      , props =ppp)\n')


				f.write(u'######### \n')
				f.write(u'#########------------------------------------------------------------------------------------------------------------------------\n')
				f.write(u'######### \n')
				f.write(u'######### section with examples how to create/delete devices-states-measurement  to start/stop data tracking for use in plots/lines \n')
				f.write(u'#########       this is the same function as the device/state/measurement selection in the configmenue \n')
				f.write(u'######### \n')
			

				for devNo in self.DEVICE:
					f.write(u'\n')
					f.write(u'\n')
					DEV= self.DEVICE["{}".format(devNo)]
					if DEV["Name"] == "":		continue
					if DEV["Name"] == "None":		continue
					f.write(u'## section for {}\n'.format(self.DEVICE[devNo]["Name"]))
					for stateNo in range(1,noOfStatesPerDeviceG+1):
						if DEV["state"][stateNo] == "":		continue
						if DEV["state"][stateNo] == "None": 	continue
						f.write(u'\n')
						if DEV["Name"].find("Var-") ==-1:
							f.write(u'ppp ={{"deviceOrVariableName":u\'{}\' # name of device or variable to be tracked \n'.format(DEV["Name"]))
						else:
							f.write(u'ppp ={{"deviceOrVariableName":u\'{}\' # name of device or variable to be tracked \n'.format(DEV["Name"]))
						f.write(u'     ,"devOrVar":         u\'{}'.format(DEV["devOrVar"])+'\' #  Dev- or Var- \n')
						f.write(u'     ,"state":            u\'{}'.format(DEV["state"][stateNo])+'\'  #  state that should be tracked \n')
						f.write(u'     ,"measurement":      u\'{}'.format(DEV["measurement"][stateNo])+'\' #  measurement that should be recored average,min,max,..,eConsumption... \n')
						f.write(u'     ,"multiplier":       u\'{}'.format(DEV["multiplier"][stateNo])+'\'  # optional data is multiplied with this value\n')
						f.write(u'     ,"offset":           u\'{}'.format(DEV["offset"][stateNo])+'\'  # optional data is added with this value\n')
						f.write(u'     ,"minValue":         u\'{}'.format(DEV["minValue"][stateNo])+'\'  # optional lower cutoff value\n')
						f.write(u'     ,"maxValue":         u\'{}'.format(DEV["maxValue"][stateNo])+'\'  # optional high cutoff value\n')
						f.write(u'     ,"fillGaps":         u\'{}'.format(DEV["fillGaps"][stateNo])+'\'  # optional fill data gaps if no info available with last data point\n')
						f.write(u'     ,"resetType":        u\''+json.dumps(DEV["resetType"][stateNo])+'\'  # options: 0 Period day week month bin PeriodNoCost dayNoCost weekNoCost monthNoCost binNoCost  only for consumption data\n')
						f.write(u'     ,"nickName":         u\''+json.dumps(DEV["nickName"][stateNo])+'\' \n')
						f.write(u'     ,"logLevel":         u\'1\'          ###  values:  blank =off  if debug mode on , 0 = error 1 = regular logging\n')
						f.write(u'     }\n')
						f.write(u'plug.executeAction("addDeviceAndStateToSelectionList" , props =ppp)\n')
						f.write(u'#plug.executeAction("deleteDeviceAndStateFromSelectionList" , props =ppp)\n')
						f.write(u'#plug.executeAction("deleteDeviceFromSelectionList"         , props ={{"deviceOrVariableName": u\'{}'.format(DEV["Name"])+'\'}\n')
			



				kk = 0
				for nPlot in self.PLOT:
					kk+=1
					PL =self.PLOT[nPlot]
					f.write(u'\n')
					f.write(u'\n')
					f.write(u'######### \n')
					f.write(u'######### section for {}'.format(PL["DeviceNamePlot"])+' ID="{}'.format(nPlot)+'"   start-----------------------------------------------------\n')
					f.write(u'######### \n')
					f.write(u'\n')
					f.write(u'plot{}'.format(kk)+'={\n')
					f.write(u'  "deviceNameOfPlot"     : u\'{}'.format(PL["DeviceNamePlot"])+'\'\n')
					f.write(u' ,"PlotType"             : u\'{}'.format(PL["PlotType"])+'\'  ### dataFromTimeSeries  dataFromFile  dataFromVariable\n')
					f.write(u' ,"XYvPolar"             : u\'{}'.format(PL["XYvPolar"])+'\'  ### xy plot or polar plot\n')
					f.write(u' ,"Grid"                 : u\'{}'.format(PL["Grid"])+'\'                 ### options:  0=no 1=dashedBack 2=solidBack 3=thickSolidBack -1=thinFront -2... -3... \n')
					f.write(u' ,"Border"               : u\'{}'.format(PL["Border"])+'\'              ### options:  1+2+4+8  0+0+0+0   on off for x,y,xTop,yRight border lines \n')
					f.write(u' ,"PlotFileOrVariName"   : u\'{}'.format(PL["PlotFileOrVariName"])+'\'       ### Name of variable of filename if PlotType = dataFromFile or dataFromVariable  \n')
					f.write(u' ,"TitleText"            : u\'{}'.format(PL["TitleText"])+'\'     ### text that goes on the top of the plot\n')
					f.write(u' ,"ExtraText"            : u\'{}'.format(PL["ExtraText"])+'\'     ### Extra text \n')
					f.write(u' ,"ExtraTextXPos"        : u\'{}'.format(PL["ExtraTextXPos"])+'\'     ### x-pos of extra text \n')
					f.write(u' ,"ExtraTextYPos"        : u\'{}'.format(PL["ExtraTextYPos"])+'\'     ### y-pos of extra text \n')
					f.write(u' ,"ExtraTextRotate"      : u\'{}'.format(PL["ExtraTextRotate"])+'\'     ### rotate extra text counter clockwise 0..360  \n')
					f.write(u' ,"ExtraTextFrontBack"   : u\'{}'.format(PL["ExtraTextFrontBack"])+'\'     ### put extra text in "front" or "back" ground  \n')
					f.write(u' ,"ExtraTextSize"        : u\'{}'.format(PL["ExtraTextSize"])+'\'     ### put extra text Size in points  \n')
					f.write(u' ,"ExtraTextColorRGB"    : u\'{}'.format(PL["ExtraTextColorRGB"])+'\'     ### extra text color #RRGGBB format  \n')
					f.write(u' ,"TextSize"             : u\'{}'.format(PL["TextSize"])+'\'                       ### font size  \n')
					f.write(u' ,"TextMATFont"          : u\'{}'.format(PL["TextMATFont"])+'\'             ### if MATPLOT font name:  sans-serif  serif  cursive  fantasy  monospace \n')
					f.write(u' ,"TextFont"             : u\'{}'.format(PL["TextFont"])+'\'         ### if GNUPLOT name of font from  /Library/Fonts/  eg Arial Unicode.ttf \n')
					f.write(u' ,"TextColor"            : u\'{}'.format(PL["TextColor"])+'\'              ## #FFFFFF ... #000000 or 255,255,255 format for RGB color intensities\n')
					f.write(u' ,"enabled"              : u\'{}'.format(PL["enabled"])+'\'              ## enable / disable plot\n')
					if PL["XYvPolar"] =="xy":
						f.write(u' ,"LeftScaleRange"       : u\'{}'.format(PL["LeftScaleRange"])+'\'             ### min:max \n')
						f.write(u' ,"LeftScaleTics"        : u\'{}'.format(PL["LeftScaleTics"])+'\'                ### eg 10,20,30,100 \n')
						f.write(u' ,"LeftLog"              : u\'{}'.format(PL["LeftLog"])+'\'          # linear or log \n')
						f.write(u' ,"LeftScaleDecPoints"   : u\'{}'.format(PL["LeftScaleDecPoints"])+'\'                  ### number of 00 after . \n')
						f.write(u' ,"LeftLabel"            : u\'{}'.format(PL["LeftLabel"])+'\'          ### text on left Y axis\n')
					else:
						f.write(u' ,"LeftLabel"            : u\'{}'.format(PL["LeftLabel"])+'\'          ### text onring aour the polar aixs eg N,E,S,W  or North-0,30,90,E,120,150,S,210,240,W,300,330 \n')

					if PL["XYvPolar"] =="xy":
						f.write(u' ,"RightScaleRange"      : u\'{}'.format(PL["RightScaleRange"])+'\'\n')
						f.write(u' ,"RightScaleTics"       : u\'{}'.format(PL["RightScaleTics"])+'\'\n')
						f.write(u' ,"RightLog"             : u\'{}'.format(PL["RightLog"])+'\'\n')
						f.write(u' ,"RightLabel"           : u\'{}'.format(PL["RightLabel"])+'\'\n')
						f.write(u' ,"RightScaleDecPoints"  : u\'{}'.format(PL["RightScaleDecPoints"])+'\'\n')

					f.write(u' ,"XScaleRange"          : u\'{}'.format(PL["XScaleRange"])+'\'\n')
					f.write(u' ,"XScaleTics"           : u\'{}'.format(PL["XScaleTics"])+'\'\n')
					f.write(u' ,"XLog"                 : u\'{}'.format(PL["XLog"])+'\'\n')
					f.write(u' ,"XLabel"               : u\'{}'.format(PL["XLabel"])+'\'\n')
					f.write(u' ,"XLabelPos"            : u\'{}'.format(PL.get("XLabelPos",emptyPlot["XLabelPos"]))+'\'\n')
					f.write(u' ,"RXNumbers"            : u\'{}'.format(PL.get("RXNumbers",emptyPlot["RXNumbers"]))+'\'\n')
					f.write(u' ,"XScaleDecPoints"      : u\'{}'.format(PL["XScaleDecPoints"])+'\'\n')
					f.write(u' ,"XScaleFormat"         : u\'{}'.format(PL["XScaleFormat"])+'\'           ### python / c .. format string for x axis \n')
					f.write(u' ,"resxy0"               : u\'{}'.format(PL["resxy"][0])+'\'            ### x,y  number of dots in x and y  for plotsize 1\n')
					f.write(u' ,"resxy1"               : u\'{}'.format(PL["resxy"][1])+'\'            ### x,y  number of dots in x and y  for plotsize 2\n')
					f.write(u' ,"MinuteBinNoOfDays"    : u\'{}'.format(PL["MHDDays"][0])+'\'         # number of days for MINUTE size bins 0-14\n')
					f.write(u' ,"HourBinNoOfDays"      : u\'{}'.format(PL["MHDDays"][1])+'\'         ### number of days for HOUR size bins 0-39\n')
					f.write(u' ,"DayBinNoOfDays"       : u\'{}'.format(PL["MHDDays"][2])+'\'      ### number of days for DAY size bins 0-390\n')
					f.write(u' ,"MinuteBinShift"       : u\'{}'.format(PL["MHDShift"][0])+'\'         # number of days for MINUTE to shift left\n')
					f.write(u' ,"HourBinShift"         : u\'{}'.format(PL["MHDShift"][1])+'\'      ### number of days for HOUR to shift left\n')
					f.write(u' ,"DayBinShift"          : u\'{}'.format(PL["MHDShift"][2])+'\'      ### number of days for DAY to shift left\n')
					f.write(u' ,"MinuteXScaleFormat"   : u\'{}'.format(PL["MHDFormat"][0])+'\'     ### xscale format for min \n')
					f.write(u' ,"HourXScaleFormat"     : u\'{}'.format(PL["MHDFormat"][1])+'\'     ### xscale format for hour \n')
					f.write(u' ,"DayXScaleFormat"      : u\'{}'.format(PL["MHDFormat"][2])+'\'     ### xscale format for day \n')
					f.write(u' ,"Background"           : u\'{}'.format(PL["Background"])+'\'            ### #FFFFFF ... #000000 or 255,255,255 format for RGB color intentities\n')
					f.write(u' ,"TransparentBlocks"    : u\'{}'.format(PL["TransparentBlocks"])+'\'          ###  for histogram, set 0= fully transparent ... 1 = not transparent \n')
					f.write(u' ,"TransparentBackground": u\'{}'.format(PL["TransparentBackground"])+'\'           ### 1.0 = not transparent, 0.0 = transparent, No color is used for background; Default=1.0\n')
					f.write(u' ,"dataSource"           : u\'{}'.format(PL["dataSource"])+'\'          ### who created this plot: interactive, import, mini \n')
					f.write(u' ,"ampm"                 : u\'{}'.format(PL["ampm"])+'\'          # am pm  or 24 hour format \n')
					f.write(u' ,"boxWidth"             : u\'{}'.format(PL["boxWidth"])+'\'      #    box width of histogram bars \n')
					f.write(u' ,"Raw"                  : u\'{}'.format(PL["Raw"])+'\'          ### raw Gnuplot command \n')
					f.write(u' ,"drawZeroLine"         : u\'{}'.format(PL["drawZeroLine"])+'\'     ### draw invisible zero line \n')
					f.write(u' ,"compressPNGfile"      : u\'{}'.format(PL["compressPNGfile"])+'\'     ### compress png files futer  true/false\n')
					f.write(u' ,"logLevel"             : u\'1\'          ###  values: ""=of if debug mode on , 0 = error 1 = regular logging\n')
					f.write(u' }\n')

					f.write(u'plug.executeAction("createOrModifyPlot", props =plot'+str(kk)+')\n')
					f.write(u'\n')

					for iLine in range(1,99): # do it in a sorted way, with simply "nLine in ..." its random
						nLine = str(iLine)
						if nLine not in PL["lines"]:continue
						if str(PL["lines"][nLine]["lineToColumnIndexA"]) =="0": continue
						f.write(u'line{}'.format(nLine)+'P{}'.format(kk)+'={\n')
						f.write(u'   "deviceNameOfPlot"                  : u\'{}'.format(PL["DeviceNamePlot"])+'\'\n')
						f.write(u'  ,"lineNumber"                        : u\'{}'.format(nLine)+'\'      ### 1 2 3 4 5 ...\n')
						f.write(u'  ,"lineType"                          : u\'{}'.format(PL["lines"][nLine]["lineType"])+'\'        ###  LineSolid LineDashed DOT(* + v ^ s o .)  Histogram\n')
						f.write(u'  ,"lineKey"                           : u\'{}'.format(PL["lines"][nLine]["lineKey"])+'\'    ## text for line keys in plot \n')
						f.write(u'  ,"lineShift"                         : u\'{}'.format(PL["lines"][nLine]["lineShift"])+'\'    ## text for line keys in plot \n')
						f.write(u'  ,"lineWidth"                         : u\'{}'.format(PL["lines"][nLine]["lineWidth"])+'\'       ###  0 1 2 3 4 5 \n')
						f.write(u'  ,"lineColor"                         : u\'{}'.format(PL["lines"][nLine]["lineColor"])+'\'        ### #FFFFFF ... #000000 or 255,255,255 format for RGB color intentities\n')
						f.write(u'  ,"lineMultiplier"                    : u\'{}'.format(PL["lines"][nLine]["lineMultiplier"])+'\'         ### number to be multiplied with line\n')
						f.write(u'  ,"lineOffset"                        : u\'{}'.format(PL["lines"][nLine]["lineOffset"])+'\'        ###  off of data or shift line up or down\n')
						f.write(u'  ,"lineLeftRight"                     : u\'{}'.format(PL["lines"][nLine]["lineLeftRight"])+'\'        ### use left or right Y scale\n')
						f.write(u'  ,"lineSmooth"                        : u\'{}'.format(PL["lines"][nLine]["lineSmooth"])+'\'       ###  None strong medium week smmoth \n')
						f.write(u'  ,"lineEveryRepeat"                   : u\'{}'.format(PL["lines"][nLine]["lineEveryRepeat"])+'\'      \n')
						f.write(u'  ,"lineFromTo"                        : u\'{}'.format(PL["lines"][nLine]["lineFromTo"])+'\'     ## if not 0 use as x range for THIS line  format= from:to \n')
						f.write(u'  ,"lineNumbersFormat"                 : u\'{}'.format(PL["lines"][nLine]["lineNumbersFormat"])+'\'      \n')
						f.write(u'  ,"lineNumbersOffset"                 : u\'{}'.format(PL["lines"][nLine]["lineNumbersOffset"])+'\'    \n')
						f.write(u'  ,"lineFunc"                          : u\'{}'.format(PL["lines"][nLine]["lineFunc"])+'\'            # the operation to be applied between lineA and lineB   + - * / S E C None\n')
						
						if PL["PlotType"] == "dataFromTimeSeries":
							index =int(PL["lines"][nLine]["lineToColumnIndexA"])
							if index <0:
								f.write(u'  ,"deviceOrVariableToBePlottedLineA"  : u\'{}'.format(PL["lines"][nLine]["lineToColumnIndexA"])+'\'  # options: "-1" for straight line\n')
							elif index>0:
								devNo   = int(self.dataColumnToDevice0Prop1Index[index][0])
								DEV		=	self.DEVICE["{}".format(devNo)]

								stateNo = int(self.dataColumnToDevice0Prop1Index[index][1])
								if DEV["Name"].find("Var-") ==-1:
									f.write(u'  ,"deviceOrVariableToBePlottedLineA"  : u\'{}'.format(DEV["Name"])+'\'  # device name of data source\n')
								else:
									f.write(u'  ,"deviceOrVariableToBePlottedLineA"  : u\'{}'.format(DEV["Name"][4:])+'\'  # device name of data source\n')
								f.write(u'  ,"devOrVarA"                         : u\'{}'.format(DEV["devOrVar"])+'\'  # "Dev-" or "Var-" of data source\n')
								f.write(u'  ,"StateToBePlottedLineA"             : u\'{}'.format(DEV["state"][stateNo])+'\'  # see "list available states" section to pick the right state\n')
								f.write(u'  ,"MeasurementLineA"                  : u\'{}'.format(DEV["measurement"][stateNo])+'\'  # options: average sum min max count eConsumption\n')
								f.write(u'  ,"multiplierA"                       : u\'{}'.format(DEV["multiplier"][stateNo])+'\'  # optional multiply data with value \n')
								f.write(u'  ,"offsetA"                           : u\'{}'.format(DEV["offset"][stateNo])+'\'  # optional add data with value\n')
								f.write(u'  ,"minValueA"                         : u\'{}'.format(DEV["minValue"][stateNo])+'\'  # optional lower cutoff value\n')
								f.write(u'  ,"maxValueA"                         : u\'{}'.format(DEV["maxValue"][stateNo])+'\'  # optional high cutoff value\n')
								f.write(u'  ,"fillGapsA"                         : u\'{}'.format(DEV["fillGaps"][stateNo])+'\'  # optional fill data gaps if no info available with last data point\n')
								f.write(u'  ,"resetTypeA"                        : u\''+json.dumps(DEV["resetType"][stateNo])+'\'  #  options: 0 Period day week month bin PeriodNoCost dayNoCost weekNoCost monthNoCost binNoCost  only for consumption data\n')

								index =int(PL["lines"][nLine]["lineToColumnIndexB"])
								if index >0:
									try:
										devNo   = int(self.dataColumnToDevice0Prop1Index[index][0])  ########## check!!
										DEV		=	self.DEVICE["{}".format(devNo)]
										stateNo = int(self.dataColumnToDevice0Prop1Index[index][1])
										if DEV["Name"].find("Var-") ==-1:
											f.write(u'  ,"deviceOrVariableToBePlottedLineB"  : u\'{}'.format(DEV["Name"])+'\'  # device name of data source\n')
										else:
											f.write(u'  ,"deviceOrVariableToBePlottedLineB"  : u\'{}'.format(DEV["Name"][4:])+'\'  # device name of data source\n')
										f.write(u'  ,"devOrVarB"  : u\'{}'.format(DEV["devOrVar"])+'\'  # "Dev-" or "Var-" of data source\n')
										f.write(u'  ,"StateToBePlottedLineB"             : u\'{}'.format(DEV["state"][stateNo])+'\'  # see "list available states" section to pick the right state\n')
										f.write(u'  ,"MeasurementLineB"                  : u\'{}'.format(DEV["measurement"][stateNo])+'\'  # options: average sum min max count eConsumption\n')
										f.write(u'  ,"multiplierB"                       : u\'{}'.format(DEV["multiplier"][stateNo])+'\'  # optional multiply data with value \n')
										f.write(u'  ,"offsetB"                           : u\'{}'.format(DEV["offset"][stateNo])+'\'  # optional add data with value\n')
										f.write(u'  ,"minValueB"                         : u\'{}'.format(DEV["minValue"][stateNo])+'\'  # optional lower cutoff value\n')
										f.write(u'  ,"maxValueB"                         : u\'{}'.format(DEV["maxValue"][stateNo])+'\'  # optional high cutoff value\n')
										f.write(u'  ,"fillGapsB"                         : u\'{}'.format(DEV["fillGaps"][stateNo])+'\'  # optional fill data gaps if no info available with last data point\n')
										f.write(u'  ,"resetTypeB"                        : u\''+json.dumps(DEV["resetType"][stateNo])+'\'  #options: 0 Period day week month bin PeriodNoCost dayNoCost weekNoCost monthNoCost binNoCost  only for consumption data\n')
									except:
										pass
								else:
									f.write(u'  ,"deviceOrVariableToBePlottedLineB"  : u\'\'\n')
									f.write(u'  ,"StateToBePlottedLineB"             : u\'\'\n')
									f.write(u'  ,"MeasurementLineB"                  : u\'\'\n')
						else:
							if int(PL["lines"][nLine]["lineToColumnIndexA"]) >0:
								f.write(u'  ,"dataColumnForFileOrVariableA"      : u\'{}'.format(PL["lines"][nLine]["lineToColumnIndexA"])+'\'  # data column for data source A\n')
								if PL["PlotType"] == "dataFromTimeSeries":
									f.write(u'  ,"lineFunc"                          : u\'{}'.format(PL["lines"][nLine]["lineFunc"])+'\'            # the operation to be applied between lineA and lineB   + - * / S E C None\n')
								f.write(u'  ,"dataColumnForFileOrVariableB"      : u\'{}'.format(PL["lines"][nLine]["lineToColumnIndexB"])+'\'  # data column for data source B\n')
						
						f.write(u' ,"logLevel"                           : u\'1\'          ###  values: ""=of if debug mode on , 0 = error 1 = regular logging\n')
						f.write(u' }\n')
						f.write(u'plug.executeAction("createOrModifyLine", props =line{}'.format(nLine)+'P{}'.format(kk)+')\n')
						f.write(u'\n')
						

					f.write(u'#plug.executeAction("createPlotPNG"       , props ={{"deviceNameOfPlot": u\'{}'.format(PL["DeviceNamePlot"])+'\'})  ### call to immediately create the PNG file, no 5 minute waiting for next cycle\n')
					f.write(u'#plug.executeAction("showPlotONLY"        , props ={{"deviceNameOfPlot": u\'{}'.format(PL["DeviceNamePlot"])+'\'})  ### call to immediately show the PNG file,\n')
					f.write(u'\n')
					f.write(u'\n')

					f.write(u'##  and here how to delete the plot :\n')
					f.write(u'#plug.executeAction("deletePlot"          , props ={{"deviceNameOfPlot": u\'{}'.format(PL["DeviceNamePlot"])+'\'})\n\n')
					f.write(u'\n')
					f.write(u'##  and here how to delete  lineNumber 1 in the plot :\n')
					f.write(u'#plug.executeAction("deleteLine"          , props ={{"deviceNameOfPlot": u\'{}'.format(PL["DeviceNamePlot"])+'\', "lineNumber":"1"})\n\n')
					f.write(u'\n')
					f.write(u'######### section for {}'.format(PL["DeviceNamePlot"])+'  end-------------------------------------------------------\n')
					f.write(u'\n')
					f.write(u'\n')
					f.write(u'\n')

				f.write(u'\n')
				f.write(u'\n')
				f.write(u'#########------------------------------------------------------------------------------------------------------------------------\n')
				f.write(u'#########------------------------------------------------------------------------------------------------------------------------\n')
				f.write(u'#########------------------------------------------------------------------------------------------------------------------------\n')
				f.write(u'\n')
				f.write(u'######### \n')
				f.write(u'######### section with examples how to list available states of your devices / variables to be plotted (those that have numbers as states) \n')
				f.write(u'######### \n')
				f.write(u'\n')
				for devNo in self.DEVICE:
					DEV= self.DEVICE["{}".format(devNo)]
					if DEV["Name"] =="":		continue
					if DEV["Name"] =="None":	continue
					f.write(u'ppp ={{"deviceOrVariableName": u\'{}'.format(DEV["Name"])+'\',"logLevel": u\'1\'}\n')
					f.write(u'plug.executeAction("showDeviceStates"       , props =ppp)\n')
				f.write(u'#plug.executeAction("showDeviceStates"       , props ={"deviceOrVariableName": u\'***\',"logLevel": u\'1\'})   ### use *** for all eligible devices \n')

				f.write(u'\n')
				f.write(u'\n')
				f.write(u'#########------------------------------------------------------------------------------------------------------------------------\n')
				f.write(u'#########------------------------------------------------------------------------------------------------------------------------\n')
				f.write(u'#########------------------------------------------------------------------------------------------------------------------------\n')

			f.close()
			self.indiLOG.log(10,"command: create Python code for PLOTs in "+self.userIndigoPluginDir+fName+"    DONE")
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			f.close()
			#self.quitNOW = "x"

		return
		
	########################################	data in/out and maintenance 	########################################	########################################	######################################
		
	########################################
	def doInitData(self):
		
		self.initializeData()
		self.putDeviceParametersToFile(calledfrom="doInitData")
		self.devicesAdded		= 2
		if self.sqlDynamic.find("batch") ==0:
			self.sqlNumbOfRecsImported =0
			while True:
				self.setupSQLDataBatch(calledfrom="doInitData")
				if self.originalCopySQLActive =="-1": break
				sleep(60)            
			self.readSQLdataBatch(calledfrom="doInitData")

		if self.gnuORmat =="mat" :
			self.stopMAT()
			self.startMAT()
		
		self.putDiskData(0)
		self.putDiskData(1)
		self.putDiskData(2)
		
		self.consumptionCostData={}
		self.consumedDuringPeriod ={}

		for consumptionType in availConsumptionTypes:			# add emptyCost if cost does not exist
			xxx = []
			for j in range(noOfCostTimePeriods+1):
				xxx.append(copy.deepcopy(emptyCost))
			self.consumptionCostData[consumptionType]=xxx


		self.valuesFromIndigo 	=[[[0 for l in range(noOfValuesMeasured)] for i in range(self.dataColumnCount+1)] for k in range(noOfTimeTypes)]

		self.putConsumptionCostData()
		self.putconsumedDuringPeriod()

		self.indiLOG.log(10,"command: init data done")

		self.sleep(10)


	########################################
	def initializeData(self):
		if self.dataColumnCount <0: self.dataColumnCount=0

		self.noOfTimeBins				=	[int((60*24*self.noOfDays[0])//noOfMinutesInTimeBins[0]), int((60*24*self.noOfDays[1])//noOfMinutesInTimeBins[1]), int((60*24*self.noOfDays[2])//noOfMinutesInTimeBins[2])]
		self.timeDataNumbers			=	[[["" for i in range(self.dataColumnCount+1+dataOffsetInTimeDataNumbers)] for l in range(self.noOfTimeBins[j])]  for j in range(noOfTimeTypes)]
		self.timeBinNumbers				=	[[0 for l in range(self.noOfTimeBins[j])]  for j in range(noOfTimeTypes)]
		self.newVFromIndigo				=	[0.  for i in range(self.dataColumnCount+1+dataOffsetInTimeDataNumbers)]
		self.lastTimeStampOfDevice		=	[[["22001231202122","22001231202122"]for k in range(noOfTimeTypes)] for i in range(self.dataColumnCount+1)]
		self.sqlHistListStatus				=	[10  for i in range(self.dataColumnCount+1)]
		self.sqlColListStatus				=	[10  for i in range(self.dataColumnCount+1)]
		self.sqlColListStatusRedo			=	[0  for i in range(self.dataColumnCount+1)]
		self.sqlHistListStatus[0]			=	0
		self.sqlColListStatus[0]			=	0
		self.timeDataIndex				=	{}  # use to shift data etc
		self.valuesFromIndigo 			=	[[[0 for l in range(noOfValuesMeasured)] for i in range(self.dataColumnCount+1)] for k in range(noOfTimeTypes)]

		self.initMinuteDataData()
		self.initMinuteDataIndex()
		self.initHourDataData()
		self.initHourDataIndex()
		self.initDayDataData()
		self.initDayDataIndex()
		self.fillWithTimeIndicators()
		
		

		return


	#########################################
	def addColumnToData(self):
		self.dataColumnCount+=1
		for TTI in range(0,noOfTimeTypes):
			for TBI in range (0,self.noOfTimeBins[TTI]):
				self.timeDataNumbers[TTI][TBI].append("")
		for TTI in range(0,noOfTimeTypes):
				self.valuesFromIndigo[TTI].append(emptyValues[:])
		
		self.newVFromIndigo.append(0.0)
		self.lastTimeStampOfDevice.append([["22001231202122","22001231202122"]for k in range(noOfTimeTypes)])
		self.sqlHistListStatus.append(10)
		self.sqlColListStatus.append(10)
		self.sqlColListStatusRedo.append(0)
		self.sqlLastID.append("0")
		self.sqlLastImportedDate.append(0)
		self.dataColumnToDevice0Prop1Index.append([0,0])
		return

	########################################
	def doShiftDay(self):
		self.shiftMinuteData() # move " old today" to "old yesterday" and delete "old yesterday"
		self.shiftHourData()
		self.shiftDayData()
		self.fillWithTimeIndicators()
		self.cleanData()
		self.setupGNUPlotFiles(calledfrom="runConcurrentThread3")
		self.indiLOG.log(10,"command: shift day done")
		return



	########################################
#	make number of data columns consistent, ie if there are empty spot filll them up with 0
	########################################
	def cleanData(self):
		try:
	#		d0= datetime.datetime.now()

			for nn in range(0,noOfTimeTypes):
				for TBI in range (0,self.noOfTimeBins[nn]):
					count =0
					for theCol in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount+1+dataOffsetInTimeDataNumbers):
						if self.timeDataNumbers[nn][TBI][theCol] == "" : continue
						count=1
						break
					if count == 0: self.timeDataNumbers[nn][TBI][0] = 0.0
			

			### delete bad data ..
			for devNo in range(1,999):
				keep="no"
				try:
					for stateNo in range (1,noOfStatesPerDeviceG+1):
						if int(self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo]) > 0 : keep = "yes"
					if keep =="no":
						del self.DEVICE["{}".format(devNo)]
				except:
					pass

			if self.redolineDataSource(calledfrom="cleanData") ==-1:
				if self.redolineDataSource(calledfrom="cleanData") ==-1:
					if self.redolineDataSource(calledfrom="cleanData") ==-1:
						if self.redolineDataSource(calledfrom="cleanData") ==-1:
							self.redolineDataSource(calledfrom="cleanData")
			self.putDiskData(0)
			self.putDiskData(1)
			self.putDiskData(2)
			self.putconsumedDuringPeriod()


		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "uknown error cleanData"

		return



	########################################
#	Shift data back (left) one day
	########################################

	########################################
	def shiftMinuteData(self):
		try:
			theIndex =0
			days = self.noOfDays[0]-1
			while days > 0:
				days -=1
				for hh in range(0,24):
					for mm in range(0,60,5):
						self.timeDataNumbers[0][theIndex] = self.timeDataNumbers[0][theIndex+24*(60//5)][:]
						self.timeBinNumbers[0][theIndex] = copy.deepcopy(self.timeBinNumbers[0][theIndex+24*(60//5)])
						theIndex+=1
			zeroNumbers =["" for i in range(0,self.dataColumnCount+1+dataOffsetInTimeDataNumbers)]
			theDay = datetime.date.today()
			dateString = theDay.strftime("%Y%m%d")
			for hh in range(0,24):									## fill up today with datestring and 0 0 0 0 0 ..
				hh0 = self.padzero(hh)
				for mm in range(0,60,5):
					self.timeDataNumbers[0][theIndex]	 = zeroNumbers[:]						## reset Todays bucket, which is "new yesterday"
					self.timeBinNumbers[0][theIndex]	= dateString+hh0+self.padzero(mm)+"00"
					theIndex +=1

			self.initMinuteDataIndex()
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error shiftMinuteData"

		for theCol in range(1,self.dataColumnCount+1):
			self.valuesFromIndigo[0][theCol][4]  -= 24*12
			self.valuesFromIndigo[0][theCol][9]  -= 24*12
			self.valuesFromIndigo[0][theCol][12] -= 24*12

		return
	########################################
	def shiftHourData(self):
		try:
			theIndex =0
			days = self.noOfDays[1]-1
			while days > 0:
				days -=1
				for hh in range(0,24):
					self.timeDataNumbers[1][theIndex] 	 = self.timeDataNumbers[1][theIndex+24][:]
					self.timeBinNumbers[1][theIndex]		 = copy.deepcopy(self.timeBinNumbers[1][theIndex+24])
					theIndex+=1

			zeroNumbers =["" for i in range(0,self.dataColumnCount+1+dataOffsetInTimeDataNumbers)]
			theDay = datetime.date.today()
			dateString = theDay.strftime("%Y%m%d")
			for hh in range(0,24):								## fill up today with datestring and 0 0 0 0 0 ..
					self.timeDataNumbers[1][theIndex]	= zeroNumbers[:]						## reset Todays bucket, which is "new yesterday"
					self.timeBinNumbers[1][theIndex]	= dateString+self.padzero(hh)+"0000"
					theIndex +=1

			self.initHourDataIndex()
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error shiftHourData"
		for theCol in range(1,self.dataColumnCount+1):
			self.valuesFromIndigo[1][theCol][4]  -= 24
			self.valuesFromIndigo[1][theCol][9]  -= 24
			self.valuesFromIndigo[1][theCol][12] -= 24

		return
	########################################
	def shiftDayData(self):
		try:
			# this is called at midnight, so yesterday is in todays bucket..
			# move " old today" to "old yesterday" and delete "old yesterday"

			zeroNumbers =["" for i in range(0,self.dataColumnCount+1+dataOffsetInTimeDataNumbers )]
			for ii in range (0,self.noOfDays[2]-1):
				self.timeDataNumbers[2][ii] = self.timeDataNumbers[2][ii+1][:]
				self.timeBinNumbers[2][ii]		= copy.deepcopy(self.timeBinNumbers[2][ii+1])
			todayString = time.strftime("%Y%m%d",time.localtime())
			self.timeDataNumbers[2][ii+1]	= zeroNumbers[:]						## reset Todays bucket, which is "new yesterday"
			self.timeBinNumbers[2][ii+1]	= todayString+"000000"

			self.initDayDataIndex()
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error shiftDayData"
		for theCol in range(1,self.dataColumnCount+1):
			self.valuesFromIndigo[2][theCol][4]  -= 1
			self.valuesFromIndigo[2][theCol][9]  -= 1
			self.valuesFromIndigo[2][theCol][12] -= 1
		

		return





	########################################
#	reset data
	########################################
	########################################
	def initMinuteDataData(self):
		try:
			days = self.noOfDays[0]
			index=0
			while days > 0:
				days -=1
				theDay = datetime.date.today() - datetime.timedelta(days)
				dateString = theDay.strftime("%Y%m%d")
				for hh in range(0,24):
					hh0 =self.padzero(hh)
					for  mm in range(0,60,5):
						self.timeBinNumbers[0][index]		= dateString+hh0+self.padzero(mm)+"00"
						self.timeDataNumbers[0][index][0]   = 0
	#					for jj in range(2,self.maxColumns+2):
						for jj in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount +1+dataOffsetInTimeDataNumbers):
							self.timeDataNumbers[0][index][jj]= ""
						index +=1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error initMinuteDataData"
		return
	########################################
	def initHourDataData(self):
		try:
			days = self.noOfDays[1]
			index=0
			while days > 0:
				days -=1
				theDay = datetime.date.today() - datetime.timedelta(days)
				dateString = theDay.strftime("%Y%m%d")
				for hh in range(0,24):
					self.timeBinNumbers[1][index]		= dateString+self.padzero(hh)+"0000"
					self.timeDataNumbers[1][index][0]   = 0
					for jj in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount +1+dataOffsetInTimeDataNumbers):
						self.timeDataNumbers[1][index][jj]= ""
					index +=1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW =  "error initHourDataData"
		return
	########################################
	def initDayDataData(self):
		try:
			days = self.noOfDays[2]
			index=0
			while days > 0:
				days -=1
				theDay = datetime.date.today() - datetime.timedelta(days)
				dateString = theDay.strftime("%Y%m%d")
				self.timeBinNumbers[2][index]		= dateString+"000000"
				self.timeDataNumbers[2][index][0]   = 0
				for jj in range(1+dataOffsetInTimeDataNumbers,self.dataColumnCount +1+dataOffsetInTimeDataNumbers):
	#			for jj in range(2,self.maxColumns+2):
					self.timeDataNumbers[2][index][jj]= ""
				index +=1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error initDayDataData"
		return
	########################################


	########################################
	def initMinuteDataIndex(self):
		try:
			self.timeDataIndex[0] ={}
			theIndex = 0
			days = self.noOfDays[0]
			while days > 0:
				days -=1
				theDay = datetime.date.today() - datetime.timedelta(days)
				dateString = theDay.strftime("%Y%m%d")
				for hh in range(0,24):
					hh0 =self.padzero(hh)
					for  mm in range(0,60,5):
						self.timeDataIndex[0][dateString+hh0+self.padzero(mm)+"00"]=theIndex
						theIndex+=1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error initMinuteDataIndex"
		return
	########################################
	def initHourDataIndex(self):
		try:
			self.timeDataIndex[1] ={}
			theIndex = 0
			days = self.noOfDays[1]
			while days > 0:
				days -=1
				theDay = datetime.date.today() - datetime.timedelta(days)
				dateString = theDay.strftime("%Y%m%d")
				for hh in range(0,24):
					hh00=self.padzero(hh)
					self.timeDataIndex[1][dateString+hh00+"0000"]=theIndex
					theIndex+=1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error initHourDataIndex"
		return
	########################################
	def initDayDataIndex(self):
		try:
			self.timeDataIndex[2] ={}
			theIndex = 0
			days = self.noOfDays[2]
			while days > 0:
				days -=1
				theDay = datetime.date.today() - datetime.timedelta(days)
				dateString = theDay.strftime("%Y%m%d")
				self.timeDataIndex[2][dateString+"000000"]=theIndex
				theIndex+=1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.quitNOW = "error initDayDataIndex"
		return

	########################################

	


	########################################
#	read/write existing data from/to file, called at startup and after reset
	########################################

	########################################
	def getDiskData(self,TTI,offset):
		try:

			if os.path.isfile(self.fileData[TTI]):
			
				f=self.openEncoding(self.fileData[TTI], "r")

				f.close()
				f=self.openEncoding(self.fileData[TTI], "r")
				line = f.readline()
				if len(line) < 11+(2-TTI)*2: return  # checking length of first 2 item. its the date string YYYYMMDD +HH + MM so 8 10 12 +";0.0" +4 = 12 14 16
				f.close()

				if line.find(",")>0: sep=","
				else:				 sep=" "
				if line.find(";")>0: sep=";"
				if line.find("*")>0:
					sep="*"

				if len(line.split(sep)[0]) < 8:
					self.indiLOG.log(40," read file "+self.fileData[TTI] +" bad data "+line)
					return # junk data

				f=self.openEncoding( self.fileData[TTI] , "r")
				theIndex=0
				for line in f.readlines():
						test = line.strip("\n").strip(" ").strip(" "+sep).split(sep)
						if len(test[0]) < 13: continue
						try:
							timeIndex = self.timeDataIndex[TTI][test[0]]
							if len(test) < self.dataColumnCount+2+offset:
								for jj in range(self.dataColumnCount+2+offset - len(test)):
									test.append("")
							self.timeDataNumbers[TTI][timeIndex] =test[1:]
							try:
								self.timeDataNumbers[TTI][timeIndex][0] =float(test[1])
							except:
								self.timeDataNumbers[TTI][timeIndex][0] =0.
							self.timeBinNumbers[TTI][timeIndex] =test[0]
							theIndex+=1
						except:
							pass
				f.close()
				self.indiLOG.log(10," read file "+self.fileData[TTI] +" lines: {}".format(theIndex)+"  ok")
			else:
				return
		except  Exception as e:
			self.indiLOG.log(40,"Line '%s' has error='%s' bad datafile,  restarting indigoplotD " % (sys.exc_info()[2].tb_lineno, e))
			self.quitNOW = "error getDiskData"
		return
	########################################
	def putDiskData(self,TTI):
		f=self.openEncoding( self.fileData[TTI] , "w")
		for ii in range (0,self.noOfTimeBins[TTI]):
			# date;#of entries;weekday;lastdayinmonth=1;lastdayinyear=1;0; columns 1...n
			f.write( str(self.timeBinNumbers[TTI][ii])+
				";"+
				(";".join(map(str,self.timeDataNumbers[TTI][ii][0:dataOffsetInTimeDataNumbers+1]))).replace(".0","") +
				";"+
				(";".join(map(str,self.timeDataNumbers[TTI][ii][dataOffsetInTimeDataNumbers+1:]))) +
				"\n")
		f.close()
		return

		####  add write to each data file !! and save line indexes.



	########################################	setup GNU files 	########################################	########################################	######################################

	########################################
	def setupGNUPlotFiles(self,calledfrom="",mPlot=""):
		try:
			if self.gnuORmat !="gnu": return 

			if self.decideMyLog("Plotting") and self.gnuORmat =="gnu": self.indiLOG.log(10," called from:{}".format(calledfrom) )

			self.gnuTime()
		
			for nPlot in self.PLOT:
				if mPlot!="" and mPlot != nPlot: continue
				PLT =self.PLOT[nPlot]
				if PLT["DeviceNamePlot"] =="None": continue
				try: 
					dev = indigo.devices[PLT["DeviceNamePlot"]]
					if not dev.enabled: continue
				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
				weight =[]
				if self.decideMyLog("Plotting") and self.gnuORmat =="gnu": self.indiLOG.log(10,"setup gnu plotfiles for PLOT {}:\n{}".format(PLT["DeviceNamePlot"], PLT) )
				theType = ""					
				# set time window limits
				earliestDay	=["0","0","0"]
				lastDay		=["0","0","0"]
			
				earliestDay[2], lastDay[2] = self.firstLastDayToPlot(int(PLT["MHDDays"][2]), int(PLT["MHDShift"][2]), 2,"%Y%m%d%H%M%S")
				earliestDay[1], lastDay[1] = self.firstLastDayToPlot(int(PLT["MHDDays"][1]), int(PLT["MHDShift"][1]), 1,"%Y%m%d%H%M%S")
				earliestDay[0], lastDay[0] = self.firstLastDayToPlot(int(PLT["MHDDays"][0]), int(PLT["MHDShift"][0]), 0,"%Y%m%d%H%M%S")


				earliestBinsToPlot, noOfBinsToPlot = self.binsToPlot(earliestDay,lastDay)

				if PLT["PlotType"]=="dataFromTimeSeries":
					colOffset0 = 2 + dataOffsetInTimeDataNumbers
				else:
					colOffset0 = 1

	#			prep find what to plot:
				columns    = []
				columnsB   = []
				multFunc   = []
				nLines     = []
				colOffset  = []
				ncols      = 0
				eventIndex = []
				eventType  = []
				for iLine in range(1,99):											# loop though the lines
					nLine = str(iLine)
					if not nLine in PLT["lines"]: continue
					PLTline=PLT["lines"][nLine]
					try:    dataIndex   = int(PLTline["lineToColumnIndexA"])
					except: dataIndex = 0
					try:    dataIndexB  = int(PLTline["lineToColumnIndexB"])
					except: dataIndexB  = 0
					
					if dataIndex != 0:
						if PLT["PlotType"] =="dataFromTimeSeries":
							devNo       = self.dataColumnToDevice0Prop1Index[dataIndex][0]			# for shorter typing
							stateNo     = self.dataColumnToDevice0Prop1Index[dataIndex][1]
							if self.DEVICE["{}".format(devNo)]["measurement"][stateNo].find("event") >-1 and dataIndex > 0: # 
								fn = "{}-{}".format(self.DEVICE["{}".format(devNo)]["Id"], self.DEVICE["{}".format(devNo)]["state"][stateNo])
								eventIndex.append(fn)
								columns.append(3)		
								columnsB.append(0)
								multFunc.append(PLTline["lineFunc"])
								colOffset.append(0)
								eventType.append(self.DEVICE["{}".format(devNo)]["measurement"][stateNo][5:])
								nLines.append(nLine)	
								ncols+=1
							if self.DEVICE["{}".format(devNo)]["measurement"][stateNo].find("event") ==-1:
								eventIndex.append("")
								columns.append(dataIndex)				
								columnsB.append(dataIndexB)					
								multFunc.append(PLTline["lineFunc"])	
								colOffset.append(colOffset0)
								eventType.append("None")
								nLines.append(nLine)	
								ncols+=1
						if PLT["PlotType"] !="dataFromTimeSeries":
							eventIndex.append("")
							columns.append(dataIndex)				
							columnsB.append(dataIndexB)					
							multFunc.append(PLTline["lineFunc"])	
							colOffset.append(colOffset0)
							eventType.append("None")
							nLines.append(nLine)	
							ncols+=1
				if len(PLT["Raw"]) > 1:
					rawcmd = PLT["Raw"]
				else:
					rawcmd = "###  here goes the raw command if entered "
			
	#			prep done, now plot

				if len(str(PLT["resxy"][0])) >6 and len(str(PLT["resxy"][1])) >6:
					textScale = float(PLT["Textscale21"])
				else:
					textScale = 1.
				colorbar=False
				for ss in range(0,2):														# for the 2 sizes
					if len(str(PLT["resxy"][ss])) < 7: continue								# no proper size given skip this plot
					for TTI in range(0,noOfTimeTypes):										# for minute/hour/day TTI =0,1,2
						timeStrLength=12-(TTI)*2
						if int(PLT["MHDDays"][TTI]) !=0 or (TTI ==0 and PLT["PlotType"]!="dataFromTimeSeries"):
							if PLT["PlotType"]!="dataFromTimeSeries": # this is data in special file 
								Fnamegnu= self.userIndigoPluginDir+"gnu/"+PLT["DeviceNamePlot"]+"-"+self.plotSizeNames[ss]+".gnu"
								Fnamepng= self.indigoPNGdir+PLT["DeviceNamePlot"]+"-"+self.plotSizeNames[ss]
								if not PLT["compressPNGfile"] : Fnamepng+= ".png"
								Fnamedata= self.userIndigoPluginDir+"data/"+PLT["PlotFileOrVariName"]
								theType= "Xscale"

							else:
								if int(PLT["MHDDays"][TTI]) ==0: continue
								Fnamegnu= self.userIndigoPluginDir+"gnu/"+PLT["DeviceNamePlot"]+"-"+self.plotTimeNames[TTI]+"-"+self.plotSizeNames[ss]+".gnu"
								Fnamepng= self.indigoPNGdir+PLT["DeviceNamePlot"]+"-"+self.plotTimeNames[TTI]+"-"+self.plotSizeNames[ss]
								if not PLT["compressPNGfile"] : Fnamepng+= ".png"
								Fnamedata= self.fileData[TTI]
								theType= self.plotTimeNames[TTI]
							outLine=[]
							if ncols ==0:
								PLT["errorCount"]+=1
								if PLT["errorCount"] >  1000:	PLT["errorCount"] =0
								if PLT["errorCount"] < 5:		self.indiLOG.log(10,Fnamegnu+" has no lines defined -- dont forget to click CONFIRM before you save the lines and plots, ignore this warning if just created")
							else:
								PLT["errorCount"]=0
							weight=[]
							arrows=[]
							outLine.append("plot \\\n")
							numberCommands=[]
							for ii in range (0,ncols):
								nLine = nLines[ii]
								PLTline=PLT["lines"][nLine]
								lineShift = self.convertVariableOrDeviceStateToText(PLTline["lineShift"])
							
								if eventIndex[ii]!="":
									firstColumn = "2"
									using = ",'"+self.userIndigoPluginDir+"sql/"+ eventIndex[ii]+"' using"
								else:
									firstColumn = "1"
									using = ",'"+Fnamedata+"' using"
								
								cmd = ""
								fixedTime ="";tShift="";timeCondition="";yCondition1="";yCondition2="";yValue1="";yValue3="";yValue2="";theVar="";repeat="";lineType=""; title=" notitle ";axis="";smooth="";condition=[]
								lineWidth = " lw {}".format(float(PLTline["lineWidth"]))
								lineColor = " lc rgb \"{}".format(PLTline["lineColor"])+"\" "
								try:
									ofs = str(self.convertVariableOrDeviceStateToText(PLTline["lineOffset"]))
								except:
									self.indiLOG.log(40," initgnu, not properly defined please define lines etc in the plots section.." )
									return
								minY= "-200000.0"
								minYF =-200000.0
								if str(PLTline["lineLeftRight"]).upper()=="RIGHT":
									try:
										minYF =float(self.convertVariableOrDeviceStateToText(PLT["RightScaleRange"]).split(":")[0])
										minY = str(minYF)
									except:
										pass
								else:
									try:
										minYF =float(self.convertVariableOrDeviceStateToText(PLT["LeftScaleRange"]).split(":")[0])
										minY = str(minYF)
									except:
										pass
								mult = str(self.convertVariableOrDeviceStateToText(PLTline["lineMultiplier"]))
							
 
								if PLT["XYvPolar"] == "xy":
									if columns[ii] >0:

										if eventType[ii] !="None":
												colVar = "((${}".format(columns[ii]+ colOffset[ii])+")"
												if float(mult) !=1.: colVar+= "*(" +mult+")"
												if float(ofs)  !=0.: colVar+= "+(" +ofs+")"
												colVar+=")"
												yValue1 = colVar
												if  eventType[ii].lower() =="up":
													condition.append("("+colVar+" > "+ofs+")")
												elif  eventType[ii].lower() =="down":
													condition.append("("+colVar+" <= "+ofs+"+0.000001)")
													##elif  eventType[ii.lower()] =="change": ## does not work !!
													##    condition.append("("+colVar+" > "+minY+")")
												else: 
													condition.append("("+colVar+" > "+minY+")")
										else:
											if multFunc[ii] =="None":
												colVar = "("
												colVar+= "(${}".format(columns[ii]+ colOffset[ii])+")"
												if float(mult) !=1.: colVar+= "*(" +mult+")"
												if float(ofs)  !=0.: colVar+= "+(" +ofs+")"
												colVar+=")"
												#colVar ="("+coln+")*(" +mult+ ")+(" +ofs+ "))"
												condition.append("("+colVar+" > "+minY+")")
												yValue1 = colVar
		#using 1:( (   (($33)) > -20.0) )?(($33)):1/0 with lines  lt 6   lw 1.0 lc rgb "#000000"  title "Frezer"    axis x1y1\
		
		
											elif multFunc[ii] =="E" : # blob ps variable
												yValue1 = "(${}".format(columns[ii]+ colOffset[ii])+ "*(" +mult+ ")+(" +ofs+ "))"
												colB = str(columnsB[ii]+colOffset[ii])
												weight.append(colB)
												yValue2 = ":($"+colB+"/(max"+colB+"-min"+colB+")*10)"
												lineType= " with points lt 1 pt 6 ps variable"
												linewidth= ""
												if len(PLTline["lineKey"]) >0:
													title = " title \""+PLTline["lineKey"]+"\"  "
											elif multFunc[ii] =="S": # blob ps variable
												yValue1= "(${}".format(columns[ii]+ colOffset[ii])+ "*(" +mult+ ")+(" +ofs+ "))"
												colB = str(columnsB[ii]+colOffset[ii])
												weight.append(colB)
												yValue2 =":($"+colB+"/(max"+colB+"-min"+colB+")*10)"
												lineType=" with points lt 1 pt 7 ps variable"
												linewidth=""
												if len(PLTline["lineKey"]) > 0:
													title = " title \""+PLTline["lineKey"]+"\"  "
											elif multFunc[ii] =="C": # blob color plot
												yValue1 = "(${}".format(columns[ii]+ colOffset[ii])+ "*(" +mult+ ")+(" +ofs+ "))"
												colB = str(columnsB[ii]+colOffset[ii])
												yValue2 = ":"+colB
												lineType= "  with  points pt 7 ps {}".format(float(PLTline["lineWidth"]))+" lt palette"
												lineColor= ""
												if len(PLTline["lineKey"]) >0:
													title = " title \""+PLTline["lineKey"]+"\"  "
												colorbar=True
											else:
												colVar = "((${}".format(columns[ii]+ colOffset[ii])+" {}".format(multFunc[ii])+" ${}".format(columnsB[ii]+colOffset[ii])+")"
												if float(mult) !=1.: colVar+= "*(" +mult+")"
												if float(ofs)  !=0.: colVar+= "+(" +ofs+")"
												colVar+=")"
												condition.append("("+colVar+" > ("+minY+"))")
												yValue1 = colVar
														
										if   lineShift>0: tShift+="+{}".format(lineShift)+"*60*60*24"
										elif lineShift<0: tShift+=str(lineShift)+"*60*60*24"
								

									elif columns[ii] <0 and PLT["PlotType"] == "dataFromTimeSeries": # straight line 
										yValue1 = "(($7-{}".format(earliestBinsToPlot[TTI])+ ")*({}".format( (float(mult)-float(ofs))/max(10., float(noOfBinsToPlot[TTI])) )+ ")+(" +ofs+ ")) "
										condition =[]
										if   lineShift>0: tShift+= "+{}".format(lineShift)+"*60*60*24"
										elif lineShift<0: tShift+=str(lineShift)+"*60*60*24"
		##using="using (timecolumn(1)+{}".format(lineShift)+"*60*60*24):"

								else: # its polar coordinates, use colb for angle and col a for range
						
								#(($1>2014071416?$24:1/0)*1.0+0.0)
									if PLT["PlotType"]== "dataFromTimeSeries":
										fixedTime= str(columnsB[ii]+colOffset[ii])
										condition.append("($"+firstColumn+">="+earliestDay[TTI][:timeStrLength]+".)")
										colVar = "(${}".format(columns[ii]+colOffset[ii])
										if float(mult) !=1.: colVar+= "*(" +mult+")"
										if float(ofs)  !=0.: colVar+= "+(" +ofs+")"
										yValue1= colVar+")"
										#yValue1 = "(($"+firstColumn+">="+earliestDay[TTI][:timeStrLength]+".?$"  +str(columns[ii]+colOffset[ii])+":1/0)*"  +mult+  "+"  +ofs+  ") "
									else:
										colVar = "((${}".format(columns[ii]+colOffset[ii])+")"
										if float(mult) !=1.: colVar+= "*(" +mult+")"
										if float(ofs)  !=0.: colVar+= "+(" +ofs+")"
										yValue1= colVar+")"
										#yValue1 = "(($"                                    +str(columns[ii]+colOffset[ii])+  "*"  +mult+  ")+"  +ofs+  ") "

								fromTo = self.convertVariableOrDeviceStateToText(PLTline["lineFromTo"])
								if len(fromTo) > 2 and  fromTo.find(":") >0 :
										fromTo1, fromTo2 = fromTo.split(":")
										if  len(fromTo1) != timeStrLength: 
											fromTo1+= "000000000000"
											fromTo1 = fromTo1[:timeStrLength] 
										if  len(fromTo2) != timeStrLength: 
											fromTo2+= "000000000000"
											fromTo2 = fromTo2[:timeStrLength]
										condition.append("($"+firstColumn+" >= "+fromTo1+".) && ($"+firstColumn+" <="+fromTo2+".)")
								   

								yval =False
								nCmds= str(len(numberCommands))
								lR = PLTline["lineEveryRepeat"]
								if lR != "1" and PLT["PlotType"] == "dataFromTimeSeries":
							
									if TTI==2 and (lR.find("Hour")> -1 or lR.find("Minute")>-1): 
										outLine.append("#")
										continue
									if TTI==1 and lR.find("Minute")>-1:
										outLine.append("#")
										continue
									
									if    lR =="evenHours":
										condition.append(u'int(substr(strcol(1),10,10)) %2==0')
									elif  lR =="oddHours":
										condition.append(u'int(substr(strcol(1),10,10)) %2==1')
									elif  lR =="evenDays":
										condition.append(u'int(substr(strcol(1),8,8)) %2==0')
									elif  lR =="oddDays":
										condition.append(u'int(substr(strcol(1),8,8)) %2==1')
									elif  lR =="evenMonths":
										condition.append(u'int(substr(strcol(1),8,8)) %2==0')
									elif  lR =="oddMonths":
										condition.append(u'int(substr(strcol(1),8,8)) %2==1')
									elif  lR =="evenMinutes":
										condition.append(u'int(substr(strcol(1),12,12)) %2==0')
									elif  lR =="oddMinutes":
										condition.append(u'int(substr(strcol(1),12,12)) %2==1')
									elif ( lR =="minMinute" or 
										   lR =="maxMinute" or
										   lR =="minDay" or
										   lR =="maxDay" or
										   lR =="maxMonth" or
										   lR =="minMonth" ):
										condition =[]
										yValue2 = ""
										yValue1 = "2"
										yValue3 = "$2"
										using   =  ",'" +self.userIndigoPluginDir+"data/"+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+binTypeFileNames[TTI]+"-"+nLine+".dat'"+" using"
									elif lR == "lastBinOfMonth":
										condition.append("$4==1")
									elif lR == "lastBinOfYear":
										condition.append("$5==1")

									elif  lR.find("weekDay")==0:
										if  lR.find("Last") >-1:
											if   TTI ==0:
												condition.append(u'substr(strcol(1),9,12) eq "2555"')
											elif TTI ==1:    
												condition.append(u'substr(strcol(1),9,10) eq "23"')
										try:
											DD = lR[7:8]
											int(DD)
											condition.append("$3=={}".format(dd))
										except:
											pass    

									elif    lR.find("hour")==0:
										if  lR.find("last") >-1:
												if   TTI ==0:
													condition.append(u'substr(strcol(1),11,12) eq "55"')
												
										try: 
											HH = lR[4:6]
											int(HH)
											condition.appendu('substr(strcol(1),9,10) eq "'+HH+'"')
										except:
											pass
									

									elif lR== "firstBin":
										repeat= " every 20000::{}".format(max(1,earliestBinsToPlot[TTI]))+" "
							
									elif lR== "lastBin":  # curr value at last bin
										repeat=" "
										fixedTime= "(timeNowSec)"
										condition.append("(timecolumn("+firstColumn+") >= (timeNowSec-300)&&  timecolumn("+firstColumn+") < (timeNowSec-300 +binSecs ))")
										condition=[]

									elif lR== "rightY":
										repeat= " "
										fixedTime= "(secsLastBin)"
										condition.append("(timecolumn("+firstColumn+") >= (timeNowSec-300)&&  timecolumn("+firstColumn+") < (timeNowSec-300 +binSecs ))")
										condition=[]

									elif lR== "max":
										cmd= "stats '" + Fnamedata+"'  using  ($0>{}".format(earliestBinsToPlot[TTI])+" && $0 <{}".format(int(earliestBinsToPlot[TTI])+ int(noOfBinsToPlot[TTI])+2)+")?"+yValue1+":(1/0) nooutput \n"
										cmd+= "xval"+nCmds+" = STATS_index_max\n"
										cmd+= "yval"+nCmds+" = STATS_max\n"
										numberCommands.append(cmd)
										repeat= " every 20000::(xval"+nCmds+"+1+{}".format(earliestBinsToPlot[TTI])+")"  # only once
										yval=True
										condition=[]

									elif lR=="min":
										cmd= "stats '" + Fnamedata+"'  using  ($0>{}".format(earliestBinsToPlot[TTI])+" && $0 <{}".format(int(earliestBinsToPlot[TTI])+ int(noOfBinsToPlot[TTI])+2)+")?"+yValue1+":(1/0) nooutput \n"
										cmd+= "xval"+nCmds+" = STATS_index_min\n"
										cmd+= "yval"+nCmds+" = STATS_min\n"
										numberCommands.append(cmd)
										repeat= " every 20000::(xval"+nCmds+"+1+{}".format(earliestBinsToPlot[TTI])+")"  # only once
										yval=True
										condition=[]
									else:
										try: 
											int(lR)
											repeat= " every "+lR+"::{}".format(earliestBinsToPlot[TTI])
											condition=[]
										except:
											pass    
								if yValue3 == "": yValue3 = yValue1
								PLTLtype=PLTline["lineType"]
								if   multFunc[ii] == "E"				:	pass
								elif multFunc[ii] == "S"				:	pass
								elif multFunc[ii] == "C"				:	pass
								elif PLTLtype == "Numbers"			:
										lineWidth = ""
										if PLTline["lineWidth"] != "0": lineWidth = u' font ",{}"'.format(int(int(PLTline["lineWidth"])*2.5+5))
										lineColor= u' textcolor rgb "'+PLTline["lineColor"]+u'"'

										if yval:
											yValue2 =u' (sprintf("'+PLTline["lineNumbersFormat"]+u'",yval{}))'.format(nCmds)
											lineType =u' with labels left offset char {}'.format(PLTline["lineNumbersOffset"])
											title=u' notitle '
											condition=[]
										else:
											lineType =u' with labels left offset char '+PLTline["lineNumbersOffset"]
											yValue2 =u' (sprintf("'+PLTline["lineNumbersFormat"]+u'",'+yValue3+u'))'
											title=u' notitle '
											condition=[]

								else:
						
										if   PLTLtype.find("DOT")>-1:
											lineWidth= " ps {}".format(float(PLTline["lineWidth"]))
										if   PLTLtype == "DOT."			:
											if self.gnuVersion.find("4.") >-1:
												lineType = " with points pt 0"
											else:
												lineType = " with points pt 3"
												lineWidth= " ps 0.1"
								
										elif PLTLtype == "DOT+"			:	lineType = " with points pt 1  "
										elif PLTLtype == "DOTx"			:	lineType = " with points pt 2  "
										elif PLTLtype == "DOT*"			:	lineType = " with points pt 7  "
										elif PLTLtype == "DOTo"			:	lineType = " with points pt 19 "
										elif PLTLtype == "DOTv"			:	lineType = " with points pt 11 "
										elif PLTLtype == "DOT^"			:	lineType = " with points pt 9  "
										elif PLTLtype == "DOTs"			:	lineType = " with points pt 5  "
										elif PLTLtype =="LineDashed"	:	lineType = " with lines  lt 0  "
										elif PLTLtype =="LineSolid"	:	lineType = " with lines  lt 6  "
										elif PLTLtype == "Impulses"		:	lineType = " with impulses  lt 6  "
										elif PLTLtype == "Histogram"	:	lineType = " with boxes fill solid "
										elif PLTLtype == "Histogram0"	:	lineType = " with boxes fill pattern 0 "
										elif PLTLtype == "Histogram1"	:	lineType = " with boxes fill pattern 1 "
										elif PLTLtype == "Histogram2"	:	lineType = " with boxes fill pattern 2 "
										elif PLTLtype == "Histogram4"	:	lineType = " with boxes fill pattern 4 "
										elif PLTLtype == "Histogram5"	:	lineType = " with boxes fill pattern 5 "
										elif PLTLtype == "Histogram"	:	lineType = " with boxes fill solid "
										#elif PLTLtype == "Histogram0"	:	lineType = " with fillsteps fill pattern 0 "
										#elif PLTLtype == "Histogram1"	:	lineType = " with fillsteps fill pattern 1 "
										#elif PLTLtype == "Histogram2"	:	lineType = " with fillsteps fill pattern 2 "
										#elif PLTLtype == "Histogram4"	:	lineType = " with fillsteps fill pattern 4 "
										#elif PLTLtype == "Histogram5"	:	lineType = " with fillsteps fill pattern 5 "
										elif PLTLtype == "FilledCurves"	:	lineType = " with filledcurves x1 "
										elif ( PLTLtype == "averageLeft" or PLTLtype == "averageRight") and PLT["PlotType"] == "dataFromTimeSeries":
											condition = []
											nCmds = str(len(numberCommands))
											cmd = "stats '" + Fnamedata+"'  using  ($0>{}".format(earliestBinsToPlot[TTI])+" && $0 <{}".format(int(earliestBinsToPlot[TTI])+ int(noOfBinsToPlot[TTI])+2)+")?"+yValue1+":(1/0) nooutput \n"
											cmd += "aver"+nCmds+" = STATS_mean\n"
											#outl1 = "using 1:(+yval"+nCmds+") "
											numberCommands.append(cmd)
											nbinsForLine = int(   (time.mktime(datetime.datetime.strptime(lastDay[TTI], "%Y%m%d%H%M%S").timetuple())- time.mktime(datetime.datetime.strptime(earliestDay[TTI], "%Y%m%d%H%M%S").timetuple() ) ) * 0.03   )
									
											if str(PLTline["lineLeftRight"]).upper()== "RIGHT"	: firstSecond = "second"
											elif str(PLTline["lineLeftRight"])== "x1y2"			: firstSecond = "second"
											else:												  firstSecond = ""


											if PLTLtype == "averageLeft"	:
												arrows.append(u'set arrow from '+firstSecond+u' secsFirstBin,aver'+str(nCmds)+u' to '+firstSecond+u' (secsFirstBin+'+str(nbinsForLine)+u'),aver'+str(nCmds)+u' nohead '+lineWidth +lineColor +u' front')  # average Left)
												outLine.append("#")
												continue
												#repeat= " every ::{}".format(earliestBinsToPlot[TTI])+"::{}".format(int(earliestBinsToPlot[TTI])+nbinsForLine)+" "  # short line left
											if PLTLtype =="averageRight"	:
												#repeat = " every ::{}".format(int(earliestBinsToPlot[TTI])+ int(noOfBinsToPlot[TTI])-nbinsForLine)+"::{}".format(self.noOfTimeBins[TTI]+1)+" "  # short line right
												arrows.append(u'set arrow from '+firstSecond+u' secsLastBin,aver'+str(nCmds)+u' to '+firstSecond+u' (secsLastBin-'+str(nbinsForLine)+u'),aver'+str(nCmds)+u' nohead '+lineWidth +lineColor +u' front') # average Left')
												outLine.append("#")
												continue
										
										else:
											lineType = "with lines linetype 6  "
								
										if columns[ii] >0 :
											if len(PLTline["lineKey"]) >0:
												title = " title \""+PLTline["lineKey"]+"\"  "


								if PLTLtype != "averageLeft" and  PLTLtype != "averageRight":
									if str(PLTline["lineLeftRight"]).upper()== "RIGHT":			axis = "  axis x1y2"
									elif str(PLTline["lineLeftRight"])=="x1y2":					axis = "  axis x1y2"
									else:														axis = "  axis x1y1"
									if   PLTline["lineSmooth"].find("soft") >=0    : 			smooth = " smooth csplines"
									elif PLTline["lineSmooth"].find("medium" ) >=0 : 			smooth = " smooth csplines"
									elif PLTline["lineSmooth"].find("strong" ) >=0 : 			smooth = " smooth bezier"
									elif PLTline["lineSmooth"].find("trailingAverage" ) >=0 :
			#									cmd ="samples10(x) = $0 > 9 ? 10 : ($0-{}".format(earliestBinsToPlot[TTI])+"+1)\n"
			#									cmd+="avg10(x) = (shift10(x), (back1+back2+back3+back4+back5+back6+back7+back8+back9+back10)/samples10($0-{}".format(earliestBinsToPlot[TTI])+"))\n"
			#									cmd+="shift10(x) = (back10 = back9,back9 = back8,back8 = back7,back7 = back6,back6 = back5,back5 = back4, back4 = back3, back3 = back2, back2 = back1, back1 = x)\n"
			#									cmd+="init10(x) = (back1 = back2 = back3 = back4 = back5 = back6 = back7 = back8 = back9 = back10 = 0)\n"
												cmd+= "b1 = b2 = b3 = b4 = b5 = 0\n"
												cmd+= "samplesA(x) = $0 > 4 ? 5 : ($0+1)\n"
												cmd+= "avgA(x) = (shiftA(x), (b1+b2+b3+b4+b5)/samplesA($0))\n"
												cmd+= "shiftA(x) = (b5 = b4, b4 = b3, b3 = b2, b2 = b1, b1 = x)\n"
												numberCommands.append(cmd)
												yValue1 = "( avgA("+yValue1+") )"
												condition=[]
											
									elif PLTline["lineSmooth"].find("average3Bins" ) >=0 and PLT["PlotType"] == "dataFromTimeSeries":
												numberCommands.append("Y2=Y1=Y=0\n")
												tShift+= "-{}".format(noOfMinutesInTimeBins[TTI]*60)
												yValue1 = "(  ( Y2 = Y1, Y1 = Y, Y = "+yValue1+"), (Y+Y1+Y2)/3.  )"
												cond1 = ""; cond2 = ""; condition=[]
									elif PLTline["lineSmooth"].find("combine3Bins" ) >=0  and PLT["PlotType"] == "dataFromTimeSeries":
												numberCommands.append("Y4=Y3=Y2=Y1=Y=0\n")
												tShift+= "-{}".format(noOfMinutesInTimeBins[TTI]*60*2)
												yValue1 = "(   (Y4=Y3,Y3=Y2,Y2=Y1,Y1=Y,Y="+yValue1+"), int($0)%3==0 ? (Y2+Y1+Y)/3. :( int($0)%3==1 ?  (Y3+Y2+Y1)/3. : (Y4+Y3+Y2)/3. )   )"
												condition=[]


		#						if columns[ii] <0:
		#							outl = outl+";;"+PLTline["lineKey"] +";;{}".format(columns[ii])       
 
								outl=using
								if fixedTime !="":
									outl+= " "+fixedTime +":"
								elif tShift !="":
									outl+= " (timecolumn("+firstColumn+")"+tShift+"):"
								else:
									outl+= " "+firstColumn+":"

								cond = "&&".join(condition)
								if cond !="":
									outl+= "("+cond+")?"+yValue1+":1/0"
								else:
									outl+= yValue1

								if yValue2 != "":
									outl+= ":"+yValue2
								
								outl+= repeat
								outl+= lineType
								outl+= lineWidth 
								outl+= lineColor 
								outl+= title
								outl+= axis 
								outl+= smooth+"\\\n"
								outLine.append(self.convertVariableOrDeviceStateToText(outl))
	
						try: # if empty set to 10
							if ss == 1:
								textSize = str(int(float(PLT["TextSize"] ) *textScale))
							else:
								textSize = str(PLT["TextSize"] )
						except:
							textSize="10"
						if theType =="" : continue # this is a new one, not ready yet
						self.createGNUfile(nPlot,theType, Fnamegnu,Fnamepng,Fnamedata,
								self.convertVariableOrDeviceStateToText(PLT["TitleText"]), 
								self.convertVariableOrDeviceStateToText(PLT["TextColor"]),
								textSize ,
								PLT["TextFont"],
								self.convertVariableOrDeviceStateToText(PLT["ExtraText"]) ,
								self.convertVariableOrDeviceStateToText(PLT["ExtraTextXPos"]) ,
								self.convertVariableOrDeviceStateToText(PLT["ExtraTextYPos"]) ,
								self.convertVariableOrDeviceStateToText(PLT["ExtraTextRotate"]) ,
								self.convertVariableOrDeviceStateToText(PLT["ExtraTextFrontBack"]) ,
								PLT["ExtraTextSize"] ,
								self.convertVariableOrDeviceStateToText(PLT["ExtraTextColorRGB"]),
								self.convertVariableOrDeviceStateToText(PLT["Grid"]),
								self.convertVariableOrDeviceStateToText(PLT["Border"]) ,
								self.convertVariableOrDeviceStateToText(PLT["resxy"][ss]) ,
								self.convertVariableOrDeviceStateToText(PLT["Background"]),
								self.convertVariableOrDeviceStateToText(PLT["TransparentBackground"]),
								self.convertVariableOrDeviceStateToText(PLT["TransparentBlocks"]),
								str(PLT["ampm"]),
								self.convertVariableOrDeviceStateToText(PLT["LeftScaleRange"]),
								self.convertVariableOrDeviceStateToText(PLT["LeftScaleTics"]), 
								str(PLT["LeftScaleDecPoints"]), 
								self.convertVariableOrDeviceStateToText(PLT["LeftLog"] ), 
								self.convertVariableOrDeviceStateToText(PLT["LeftLabel"]),
								self.convertVariableOrDeviceStateToText(PLT["RightScaleRange"]),
								self.convertVariableOrDeviceStateToText(PLT["RightScaleTics"]),
								str(PLT["RightScaleDecPoints"]),
								self.convertVariableOrDeviceStateToText(PLT["RightLog"] ),
								self.convertVariableOrDeviceStateToText(PLT["RightLabel"]),
								self.convertVariableOrDeviceStateToText(PLT["XScaleRange"]),    
								self.convertVariableOrDeviceStateToText(PLT["XScaleTics"]),    
								self.convertVariableOrDeviceStateToText(PLT["XScaleDecPoints"]),    
								self.convertVariableOrDeviceStateToText(PLT["XLog"]),     
								self.convertVariableOrDeviceStateToText(PLT["XLabel"]), 
								self.convertVariableOrDeviceStateToText(PLT["XLabelPos"]), 
								self.convertVariableOrDeviceStateToText(PLT["XScaleFormat"]), 
								PLT["boxWidth"],
								PLT["XYvPolar"],
								PLT["MHDFormat"][TTI], 
								TTI,earliestDay[TTI], lastDay[TTI], int(PLT["MHDDays"][TTI]),
								weight,colorbar,
								numberCommands,arrows,
								rawcmd,PLT["drawZeroLine"],ncols+1 ,outLine)

		except  Exception as e:
			self.indiLOG.log(40,"Line '%s' has error='%s'error in setupGNUPlotFiles" % (sys.exc_info()[2].tb_lineno, e))


		return

	########################################
	def binsToPlot(self,earliestDay,lastDay):
		earliestBin =[0,0,0]
		numberOfBins =[0,0,0]
		for  TTI in range(noOfTimeTypes):
			try:
				earliestBin[TTI]= self.timeBinNumbers[TTI].index(earliestDay[TTI])
			except:
				earliestBin[TTI]= 0
				pass
			try:
				numberOfBins[TTI]= self.timeBinNumbers[TTI].index(lastDay[TTI])-earliestBin[TTI]
			except:
				numberOfBins[TTI]= self.noOfTimeBins[TTI]-earliestBin[TTI]
		return earliestBin, numberOfBins
	########################################
	def firstLastDayToPlot(self,days, shift, TTI,stTime):

		earliestDay, lastDay=datetime.date.today().strftime(stTime),datetime.date.today().strftime(stTime)

		if days ==0: return earliestDay, lastDay

		if TTI ==2  or TTI ==1 :  ###  for day & hour plot
			if  shift >=0:
				earliestDay		= ( datetime.date.today()+datetime.timedelta(1) - datetime.timedelta( days+ shift) ).strftime(stTime)
				lastDay			= ( datetime.date.today()+datetime.timedelta(1) - datetime.timedelta( shift ) ).strftime(stTime)
				return earliestDay, lastDay
	
		if TTI ==0  :  ###  for minute plot
			if shift>=0:
				YRIGHT 			= datetime.date.today()+datetime.timedelta(1)
				lastDay			= ( YRIGHT - datetime.timedelta( shift)                                       ).strftime(stTime)
				earliestDay		= ( YRIGHT - datetime.timedelta( days+ shift ) ).strftime(stTime)
				return earliestDay, lastDay
				
			elif shift ==-1: # this is for continous shift every hour
				x = datetime.datetime.now()
				YRIGHT0			=	datetime.datetime.now() -datetime.timedelta(minutes=x.minute,seconds=x.second)
				YRIGHT			=	YRIGHT0 + datetime.timedelta( hours=1)
				lastDay			= ( YRIGHT                                       ).strftime(stTime)
				earliestDay		= ( YRIGHT0 - datetime.timedelta( days )).strftime(stTime)
				return earliestDay, lastDay


		curMonth	 = datetime.datetime.now().month
		curWeekday 	 = datetime.datetime.today().weekday()
		curDayOfMonth= datetime.datetime.today().day
		curYear		 =datetime.date.today().year
		if   curMonth < 4:  firstMonth=1
		elif curMonth < 7:  firstMonth=4
		elif curMonth < 10: firstMonth=7
		else:				firstMonth=10

		if   shift ==-10: # this is for one fixed week monday - sunday
			earliestDay 	= (datetime.date.today() - datetime.timedelta( curWeekday ) ).strftime(stTime)
			lastDay 		= (datetime.date.today() + datetime.timedelta( 7-curWeekday ) ).strftime(stTime)

		elif shift ==-11: # this is for TWO fixed week monday - sunday
			earliestDay 	= (datetime.date.today() - datetime.timedelta( 7+curWeekday ) ).strftime(stTime)
			lastDay			= (datetime.date.today() + datetime.timedelta( 7-curWeekday ) ).strftime(stTime)

		elif shift ==-20: # this is for one fixed month
			earliestDay 	= datetime.datetime(curYear, curMonth, 1).strftime(stTime)
			if curMonth <12:
				lastDay 	= datetime.datetime(curYear, curMonth+1, 1).strftime(stTime)
			else:
				lastDay 	= datetime.datetime(curYear+1, 1, 1).strftime(stTime)
	
		elif shift ==-30: # this is for one Fixed Quarter
			earliestDay 	= datetime.datetime(curYear, firstMonth, 1).strftime(stTime)
			if firstMonth < 10:
				lastDay 	= datetime.datetime(curYear, firstMonth+3, 1).strftime(stTime)
			else:
				lastDay 	= datetime.datetime(curYear+1, 1, 1).strftime(stTime)

		elif shift ==-40: # this is for one Fixed Year
			earliestDay 	= datetime.datetime(curYear, 1, 1).strftime(stTime)
			lastDay 		= datetime.datetime(curYear+1, 1, 1).strftime(stTime)


		return earliestDay, lastDay


	########################################
	def createGNUfile(self,nPlot,theType,gnuFile,plotFile,Fnamedata
		,title, textColor,textSize,textFont
		,ExtraText,ExtraTextX,ExtraTextY,ExtraTextRotate,ExtraTextFrontBack,ExtraTextSize,ExtraTextColorRGB
		,grid,Border,res,background,TransparentBackground,TransparentBlocks,am24
		,rangeY, ticsY, LDec,LLog,labelY
		,rangeY2,ticsY2,RDec,RLog,labelY2
		,rangeX, ticsX, XDec, XLog, labelX, XLabelPos, XScaleFormat, boxWidth, XYvPolar # XLabelPos not used 
		,MHDFormat
		,TTI, earliestDay, lastDay, nDays
		,weight, colorbar
		,numberCommands,arrows
		,rawCmd, drawZeroLine, numberOfLines , theLines ):


		if nDays ==0 and theType !="Xscale" : return
		# first part if format, second part is major tick frequency in secs 
		try: # dont use  it if it is a number, then it is meant for matplot  
			int(MHDFormat)
			MHDFormat =""
		except: pass
		xx = MHDFormat.split("+")
		
		if len(xx) == 1: 
			overWriteXFormat = [MHDFormat,""]
		elif len(xx) > 1: 
			overWriteXFormat = xx
		else:
			overWriteXFormat = ["",""]
			
		try:
			
			if self.decideMyLog("Plotting") and self.gnuORmat =="gnu": self.indiLOG.log(10,"lines: {}".format(theLines))
			f=self.openEncoding( gnuFile , "w")
			outGnu = ""
			outGnu += "#!'" + gnuFile+"'   \n"					# just a comment
			outGnu += u'set datafile separator ";" \n'
		
			### calc min and max of weight
			if len(weight)>0:
				outGnu += "### calculate min and max of scatter plot weight\n"
				outGnu += "set yrange [0:1];set output '/dev/null'\n"
				for nn in range(len(weight)):
					WN=weight[nn]
					outGnu += "ismax"+WN+"(x) = (x>max"+WN+")?max"+WN+"=x:0 ;ismin"+WN+"(x) = (x<min"+WN+")?min"+WN+"=x:0;max"+WN+"=-1e38;min"+WN+"=+1e38\n"
					outGnu += "plot '"+Fnamedata+"' u "+WN+":(ismax"+WN+"($"+WN+")*ismin"+WN+"($"+WN+"))\n"
				outGnu += "unset yrange\n"
				outGnu += "###\n"

			if colorbar:
				outGnu += "###  set colorbar size and positions \n"
				outGnu += "set colorbox vertical user origin 0.98, 0.1 size  0.02, .8\n"
				outGnu += "set cbtics axis nomirror out offset -7.5 left\n"
				outGnu += "set rmargin  12\n"
				outGnu += "###\n"

		
			outGnu += "set output '" + plotFile+"'   \n"			# output file

			for cmd in numberCommands: # for min max for numbers lines
				outGnu += cmd
		

	#		outGnu += "#  font selected:"+textFont+" size:"+textSize+" \n"
			if str(TransparentBackground) =="0.0":	TBack ="transparent"
			else:									TBack =""
		
			if len(textFont) <3 or textFont=="System-font":
				outGnu += "set terminal png truecolor enhanced "+TBack+" medium  size " + res+ " dashlength 0.5      background rgb \""+background+"\"\n"
			else:
				if textSize =="0":  	outGnu += "set terminal png truecolor enhanced  "+TBack+" medium  font \""+self.theFontDir+textFont+"\" "                       + res+ " dashlength 0.5     background rgb \""+background+"\"\n"
				else:					outGnu += "set terminal png truecolor enhanced  "+TBack+" medium  font \""+self.theFontDir+textFont+"\" " +textSize + "  size " + res+ " dashlength 0.5     background rgb \""+background+"\"\n"



			## this is for plotting dos and specific times, need current time..

			outGnu += "\n### time now in secs, etc parameters \n"
			outGnu += "binSecs= {}".format(noOfMinutesInTimeBins[TTI]*60)+"\n"
			outGnu += "timeNow=time(0)-({}".format(self.UTCdelta)+") # dif to UTC \n"
			outGnu += "timeNowSec= timeNow/binSecs*binSecs\n"

			secs 	= time.mktime(datetime.datetime.strptime(lastDay, "%Y%m%d%H%M%S").timetuple())
			outGnu += "secsLastBin={}".format(int(secs))+"-({}".format(int(self.gnuOffset))+")-({}".format(self.UTCdelta)+")\n"# for v4 Millenium-epoch seconds\n"
			secs2	= time.mktime(datetime.datetime.strptime(earliestDay, "%Y%m%d%H%M%S").timetuple())
			outGnu += "secsFirstBin={}".format(int(secs2))+"-({}".format(int(self.gnuOffset))+")-({}".format(self.UTCdelta)+")\n" # for v4 Millenium-epoch seconds\n\n"



			if XYvPolar =="polar":
				outGnu += "set key textcolor rgb \""+textColor+"\" \n" 
				if len(title) > 1: outGnu += "set title \""+title+"\" offset 0,0.3  textcolor  rgb \""+textColor+"\" \n"


				if len(ExtraText) > 1:
					if len(textFont) <3 or textFont=="System-font":
						outGnu += "set label \""+ExtraText+"\"  at screen "+ ExtraTextX+", screen "+ExtraTextY+" rotate by "+ExtraTextRotate+"  "+ExtraTextFrontBack+" \n"
					else:
						outGnu += "set label \""+ExtraText+"\"  at screen "+ ExtraTextX+", screen "+ExtraTextY+" rotate by "+ExtraTextRotate+"  "+ExtraTextFrontBack+" font \""+self.theFontDir+textFont+ "," +ExtraTextSize + "\"  textcolor  rgb \""+ExtraTextColorRGB+"\" \n"




		
				outGnu += u'unset xlabel \n'
				outGnu += u'unset ylabel \n'
				outGnu += u'unset ytics \n'
				outGnu += u'unset xtics \n'
				outGnu += u'unset border \n'
				outGnu += u'set polar\n'
				outGnu += u'set angles radian\n'
				outGnu += u'set clip\n'
				outGnu += u'set lmargin 2\n'
				outGnu += u'set rmargin 2\n'
				if len(title) > 1:
					outGnu += 'set tmargin 2.5\n'
				else:
					outGnu += 'set tmargin 2\n'
				outGnu += 'set bmargin 2\n'
				outGnu += 'set size square\n'

				if   str(grid).find("-1")==0:
					outGnu += 'set style line 100 lt 0 lw 1 linecolor rgb "'+textColor+'" \n'
					outGnu += 'set grid polar '+str(math.pi/6.)+'front ls 100 \n'
				elif str(grid).find("-3")==0:
					outGnu += 'set style line 100 lt 6 lw 2 linecolor rgb "'+textColor+'" \n'
					outGnu += 'set grid polar '+str(math.pi/6.)+' front ls 100 \n'
				elif str(grid).find("-2")==0:
					outGnu += 'set style line 100 lt 6 lw 1 linecolor rgb "'+textColor+'" \n'
					outGnu += 'set grid polar '+str(math.pi/6.)+' front ls 100 \n'
				elif str(grid).find("1")==0:
					outGnu += 'set style line 100 lt 0 lw 1 linecolor rgb "'+textColor+'" \n'
					outGnu += 'set grid polar '+str(math.pi/6.)+' back ls 100 \n'
				elif str(grid).find("3")==0:
					outGnu += 'set style line 100 lt 6 lw 2 linecolor rgb "'+textColor+'" \n'
					outGnu += 'set grid polar '+str(math.pi/6.)+' back ls 100 \n'
				elif str(grid).find("2")==0:
					outGnu += 'set style line 100 lt 6 lw 1 linecolor rgb "'+textColor+'" \n'
					outGnu += 'set grid polar '+str(math.pi/6.)+' back ls 100 \n'
				else:
					outGnu += 'unset grid \n'
					if len(ticsX)<3  :
						outGnu += 'unset raxis \n'
						outGnu += 'unset rtics \n'



				if XScaleFormat !="":			outGnu += "set format r \""+XScaleFormat+"\" \n"
				elif XDec !="" and XDec!="-":	outGnu += "set format r \"%."+XDec+"f\"    \n"
				if len(ticsX)  > 2:
					outGnu += "set rtics ("+ticsX+") \n"
				else:
					outGnu += "unset raxis \n"  # no ticks given  then no x-axis if no grid (goes with grid settings)
				if XLog == "1"or XLog.upper()=="LOG":			outGnu += "set logscale r \n"

				if  len(rangeX)> 2 and rangeX.count(":")==1 :
					rrange =rangeX.split(":")
					if float(rrange[1])>0:
				
						outGnu += "set rrange ["+rangeX+"]   \n"
						xx = float(rrange[1])*1.08
						xx1= float(rrange[0])*1.08
						dx = (xx-xx1)/20.
						dxL= (xx-xx1)/50.
						if XLog.upper() =="LOG":
							xx = float(rrange[1])
							xx1= float(rrange[0])
							if rangeX[0] ==0: rangex[0]=1.
							xx = math.log10(xx*1.5)-math.log10(xx1)
							dx = xx/14.
							dxL= xx/30.
					
						if  len(labelY) > 6 and labelY.count(",")==3:	polarLabels=labelY.split(",")
						elif len(labelY) > 21 and labelY.count(",")==11:polarLabels=labelY.split(",")
						else:											polarLabels=["N","E","S","W"]

						if labelY.count(",")==3 or labelY.count(",")==0:  ## North/East/South/West labels
								outGnu += u'set label "'  +polarLabels[0]+  u'" at +(' +str(0)+     u'),+('+str(xx)+   u') center textcolor rgb "'+textColor+u'"\n'
								outGnu += u'set label "'  +polarLabels[1]+  u'" at +(' +str(xx*1.)+ u'),-('  +str(0)+  u') center textcolor rgb "'+textColor+u'"\n'
								outGnu += u'set label "'  +polarLabels[2]+  u'" at -(' +str(0)+     u'),-('  +str(xx)+ u') center textcolor rgb "'+textColor+u'"\n'
								outGnu += u'set label "'  +polarLabels[3]+  u'" at -(' +str(xx*1.)+ u'),+('  +str(0)+  u') center textcolor rgb "'+textColor+u'"\n'
								for i in [30,60,120,150,210,240,300,330]:
									outGnu += 'set label sprintf("%d",'+str(i)+') at '      +str(xx)+  '*cos((450 -'+str(i)+')*'+str(math.pi/180.)+'),  '+str(xx)+  '*sin((450-'+str(i)+')*'+str(math.pi/180.)+') center  textcolor rgb "'+textColor+'"\n'
								#outGnu += 'set for[i=0:330:30] label sprintf("%d",i) at '  +str(xx)+  '*cos((450 -i)*'+str(math.pi/180.)+'),  '         +str(xx)+  '*sin((450-i)*'+str(math.pi/180.)+') center  textcolor rgb "'+textColor+'"\n'
								lOffset= max(  0., (len(labelX)-5)*dxL/10.*float(textSize)  )
								outGnu += u'set label "'  +labelX+  u'" at '  +str(xx-(dxL*(1.+lOffset))*float(textSize)/10.)+  u',' +str(dx*2)+ u' center textcolor rgb "'+textColor+u'"\n'
						elif  len(labelY) > 6 and labelY.count(",")==11:
							for i in range (0,12):
								outGnu += "set label '"+polarLabels[i]+"' at {}".format(xx*math.cos((450 -i*30)*math.pi/180.))+",{}".format(xx*math.sin((450-i*30)*math.pi/180.))+" center  textcolor rgb \""+textColor+"\"\n"

				outGnu += rawCmd+" \n"
				firstL =False
				outGnu += theLines[0]
				for ii in range (1,numberOfLines ):
					if theLines[ii].find("#")!=0:
						if not firstL:
							outGnu += theLines[ii].strip(",")
						else:
							outGnu += theLines[ii]
						firstL = True



			else:  ## not polar but x/y
		
				outGnu += 'set style fill transparent solid '+str(TransparentBlocks)+' \n'
				if theType =="Xscale": ##free defined x scale
					if XScaleFormat.find("%Y")>-1 or XScaleFormat.find("%d")>-1 or XScaleFormat.find("%m")>-1:			# assume it is date format
						xsplit = XScaleFormat.split("+")
						timefmt= XScaleFormat.split("+")[0]
						if len(xsplit) >0:
							format = xsplit[1]
						else:
							format = "%d"
						outGnu += "set xdata time  \n"
						outGnu += "set timefmt \""+timefmt+"\" \n"						# yyyymmdd x axis input data format
						outGnu += "set format x \""+format+"\" \n"							# x axis dat format on plot
						if len(rangeX)> 3 and rangeX.count(":")>0:
							outGnu += "set xrange [\""+rangeX.split(":")[0]+"\":\""+rangeX.split(":")[1]+"\"]   \n"
					else:
						if XScaleFormat !="":				outGnu += "set format x \""+XScaleFormat+"\" \n"
						elif XDec !="" and XDec!="-":		outGnu += "set format x \"%."+XDec+"f\"    \n"
						if len(ticsX)  > 1: 				outGnu += "set xtics ("+ticsX+") \n"
						if len(rangeX)> 3 and rangeX.count(":")>0 :outGnu += "set xrange ["+rangeX+"]   \n"
						if XLog == "1"or XLog.upper()=="LOG":	outGnu += "set logscale x \n"
					if len(labelX) > 1: 					outGnu += "set xlabel \""+labelX+"\"  textcolor rgb \""+textColor+"\"  \n"
			
				else:  ## this is the default y vs time
					outGnu += "set xdata time  \n"
					if am24 =="24": formatH = "%H:%M"
					else:			formatH = "%l:%M%p"

					if theType == "day":
						outGnu += "set timefmt \"%Y%m%d\" \n"						# yyyymmdd x axis input data format
						if int(self.PLOT[nPlot]["MHDDays"][2]) >0:	outGnu += "set xrange[\""+earliestDay+"\":\""+lastDay+"\"]\n"


						if MHDFormat.lower() !="off":
							if len(overWriteXFormat[0]) > 1: 
								outGnu += "set format x \""+ overWriteXFormat[0] +"\"  \n"							# x axis dat format on plot
							else:
								outGnu += "set format x \"%b\" \n"							# x axis date format on plot
							if len(overWriteXFormat[1]) > 0 : 
						
								outGnu += "set xtics "+ overWriteXFormat[1] +" \n"				# x axis dat format on plot


					if theType =="hour":
						outGnu += "set timefmt \"%Y%m%d%H\"    \n"						# yyyymmddhh
						if int(self.PLOT[nPlot]["MHDDays"][1]) >0:	outGnu += "set xrange[\""+earliestDay+"\":\""+lastDay+"\"]\n"
						
						if MHDFormat.lower() !="off":
							if len(overWriteXFormat[0]) > 1 : 
								outGnu += "set format x \""+ overWriteXFormat[0] +"\"  \n"							# x axis dat format on plot
							else:
								if int(self.PLOT[nPlot]["MHDDays"][1]) <7: 	outGnu += "set format x \""+formatH+"\\n%a\"    \n"
								else:										outGnu += "set format x \"%a\"    \n"
						
							if len(overWriteXFormat[1]) > 0 : 
								outGnu += "set xtics "+ overWriteXFormat[1] +" \n"				# x axis dat format on plot



					if theType =="minute":
						outGnu += "set timefmt \"%Y%m%d%H%M\"    \n"					# yyyymmddhhmm
						if int(self.PLOT[nPlot]["MHDDays"][0]) >0: outGnu += "set xrange[\""+earliestDay+"\":\""+lastDay+"\"]\n"
	
						if MHDFormat.lower() !="off":
							if len(overWriteXFormat[0]) > 1: 
								outGnu += "set format x \""+ overWriteXFormat[0] +"\" \n"				# x axis dat format on plot
							
							else:
								if   nDays ==1:								outGnu += "set format x \""+formatH+"\" \n"
								elif nDays ==2 or nDays== 3:				outGnu += "set format x \""+formatH+"\\n%a\"    \n"
								else :										outGnu += "set format x \"%a\"    \n"
							if len(overWriteXFormat[1]) > 0 : 
								outGnu += "set xtics "+ overWriteXFormat[1] +" \n"				# x axis dat format on plot
						



				if len(rangeY) > 1: 		outGnu += "set yrange ["+rangeY+"]   \n"
				if LDec !="" and LDec!="-":	outGnu += "set format y \"%."+LDec+"f\"    \n"
				if len(ticsY)  > 1: 		outGnu += "set ytics ("+ticsY+") nomirror   \n"
				if len(labelY) > 1: 		outGnu += "set ylabel \""+labelY+"\"  textcolor rgb \""+textColor+"\"  \n"
				if LLog == "1"or LLog.upper()=="LOG":     outGnu += "set logscale y \n"

				if RDec !="" and RDec!="-":	outGnu += "set format y2 \"%."+RDec+"f\"    \n"
				if len(rangeY2)> 1: 		outGnu += "set y2range["+rangeY2+"]     \n"
				if len(ticsY2) > 1: 		outGnu += "set y2tics ("+ticsY2+")    \n"
				if len(labelY2)> 1:			outGnu += "set y2label \""+labelY2+"\" textcolor rgb \""+textColor+"\" \n"
				if RLog == "1"or RLog.upper()=="LOG":     outGnu += "set logscale y2 \n"

				outGnu += "set key inside center top horizontal Right noreverse enhanced autotitles nobox\n"

		#		if len(background) > 2: outGnu += "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor "+background+" behind\n"


				if grid.find("0")==-1:
					if   grid.find("only")>-1:
						if   grid.find("onlyy2")>-1:gridxyy2 =" y2tics "
						elif grid.find("onlyy")>-1:	gridxyy2 =" ytics "
						elif grid.find("onlyx")>-1:	gridxyy2 =" xtics "
					else:
						if grid.find("y2")>-1:		gridxyy2 =" xtics y2tics"
						else:						gridxyy2 =" xtics ytics "
					if   str(grid).find("-1")==0:
						outGnu += u'set style line 100 lt 0 lw 1 linecolor rgb "'+textColor+'" \n'
						outGnu += "set grid "+gridxyy2+" front ls 100 \n"
					elif str(grid).find("-2")==0:
						outGnu += u'set style line 100 lt 6 lw 1 linecolor rgb "'+textColor+'" \n'
						outGnu += "set grid "+gridxyy2+" front ls 100 \n"
					elif str(grid).find("-3")==0:
						outGnu += u'set style line 100 lt 6 lw 2 linecolor rgb "'+textColor+'" \n'
						outGnu += "set grid "+gridxyy2+" front ls 100 \n"
					elif str(grid).find("1")==0:
						outGnu += u'set style line 100 lt 0 lw 1 linecolor rgb "'+textColor+'" \n'
						outGnu += "set grid "+gridxyy2+" back ls 100 \n"
					elif str(grid).find("3")==0:
						outGnu += u'set style line 100 lt 6 lw 2 linecolor rgb "'+textColor+'" \n'
						outGnu += "set grid "+gridxyy2+" back ls 100 \n"
					elif str(grid).find("2")==0:
						outGnu += u'set style line 100 lt 6 lw 1 linecolor rgb "'+textColor+'" \n'
						outGnu += "set grid "+gridxyy2+" back ls 100 \n"
				else:
					outGnu += "unset grid \n"
				
				BonOff= Border.split("+")
				if len(BonOff) ==4:
					outGnu += u'set border '+Border+' \n'
					if BonOff[0] =="0":	outGnu += u'unset xtics \n'
					if BonOff[1] =="0":	outGnu += u'unset ytics \n'
					if BonOff[2] =="0":
										outGnu += u'set  xtics nomirror \n'
										outGnu += u'unset x2tics \n'
					if BonOff[3] =="0":	outGnu += u'unset y2tics \n'

				outGnu += "set border linecolor rgb \""+textColor+"\" \n"
				outGnu += "set key textcolor rgb \""+textColor+"\" \n" 
				if len(title) > 1: outGnu += "set title \""+title+"\" textcolor  rgb \""+textColor+"\" \n"
				if len(ExtraText) > 1:
					if len(textFont) <3 or textFont=="System-font":
						outGnu += "set label \""+ExtraText+"\"  at screen "+ ExtraTextX+", screen "+ExtraTextY+" rotate by "+ExtraTextRotate+"  "+ExtraTextFrontBack+ "  textcolor  rgb \""+ExtraTextColorRGB+"\" \n"
					else:
						outGnu += "set label \""+ExtraText+"\"  at screen "+ ExtraTextX+", screen "+ExtraTextY+" rotate by "+ExtraTextRotate+"  "+ExtraTextFrontBack+" font \""+self.theFontDir+textFont+ "," +ExtraTextSize + "\"  textcolor  rgb \""+ExtraTextColorRGB+"\" \n"
		#		outGnu += "set obj 1 rectangle behind from screen -0.01,-0.01 to screen 1.01,1.01 \n"
		#		outGnu += "set obj 1 fillstyle solid 1.0 fillcolor rgb \""+background+"\" \n"
			

				outGnu += "set boxwidth  "+boxWidth+" relative \n"

	#			for ii in range (numberOfLines ):
	#				if theLines[ii].find(";;")>-1:
	#					key = theLines[ii].split(";;")[1]
	#					pos = theLines[ii].split(";;")[2]

				for arrow in arrows:
					outGnu += arrow+" \n"
				

				outGnu += rawCmd+" \n"
				outGnu += theLines[0]
				firstL =False
				for ii in range (1,numberOfLines):
					if theLines[ii].find("#")!=0:
						if not firstL:
							outGnu += theLines[ii].strip(",")
						else:
							outGnu += theLines[ii]
						firstL = True

				if str(drawZeroLine).upper() == "TRUE":


					if len(rangeY) > 1: 		y = rangeY.split(":")[0]
					else: y ="0"
					tx = y+"  with  lines  linetype 0    linewidth 1   linecolor  rgb \""+background+"\"   title \"\"  axis x1y1\n"
					if numberOfLines  !=1:
						outGnu += " , "+tx
					else:
						outGnu += tx
				else:
					outGnu += " ,\n"

			f.write(outGnu)	
			f.close()
		except  Exception as e:
			self.indiLOG.log(40,"Line '{}' has error='{}'".format(sys.exc_info()[2].tb_lineno, e))

	########################################
	def convertVariableOrDeviceStateToText(self,textIn):
		try:
			if not isinstance(textIn, str): return textIn
			oneFound=False
			for ii in range(5):  # safety, no forever loop
				if textIn.find("%%v:") ==-1: break
				oneFound=True
				textIn,rCode = self.convertVariableToText0(textIn)
				if not rCode: break
			for ii in range(5):  # safety, no forever loop
				if textIn.find("%%d:") ==-1: break
				oneFound=True
				textIn,rCode = self.convertDeviceStateToText0(textIn)
				if not rCode: break
			try:
				if oneFound and (textIn.find("+") > -1 or  textIn.find("-") > -1 or textIn.find("/") > -1 or textIn.find("*") > -1):
					textIn = "{}".format(eval(textIn))
			except: pass        
		except  Exception as e:
			if self.decideMyLog("Plotting"): self.indiLOG.log(40,"Line '{}' has error='{}'".format(sys.exc_info()[2].tb_lineno, e))
		return textIn
		
	########################################
	def convertVariableToText0(self,textIn):
		#  converts eg: 
		#"abc%%v:VariName%%xyz"   to abcCONTENTSOFVARIABLExyz
		#"abc%%V:VariNumber%%xyz to abcCONTENTSOFVARIABLExyz
		try:
			try:
				start= textIn.find("%%v:")
			except:
				return textIn, False
		
			if start==-1:
				return textIn, False
			textOut= textIn[start+4:]
			end = textOut.find("%%")
			if end ==-1:
				return textIn, False
			var = textOut[:end]
			try:
				vText= indigo.variables[int(var)].value
			except:
				try:
					vText= indigo.variables[var].value
				except:
					return textIn, False

			try:
				if end+2 >= len(textOut)-1:
					textOut= textIn[:start]+vText
					return textOut, True
				textOut= textIn[:start]+vText+textOut[end+2:]
				return textOut, True
			except:
				return textIn, False
		except  Exception as e:
			if self.decideMyLog("Plotting"): self.indiLOG.log(40,"Line '{}' has error='{}'".format(sys.exc_info()[2].tb_lineno, e))
		return textIn, False


	########################################
	def convertDeviceStateToText0(self,textIn):
		#  converts eg: 
		#"abc%%d:devName:stateName%%xyz"   to abcdevicestatexyz
		#"abc%%V:devId:stateName%%xyz to abcdevicestatexyz
		try:
			try:
				start= textIn.find("%%d:")
			except:
				return textIn, False
			if start==-1:
				return textIn, False
			textOut= textIn[start+4:]

			secondCol = textOut.find(":")
			if secondCol ==-1:
				return textIn, False
			dev     = textOut[:secondCol]
			textOut = textOut[secondCol+1:]
			percent = textOut.find("%%")
	
			if percent ==-1: return textIn, False
			state   = textOut[:percent]
			textOut = textOut[percent+2:]
			try:
				vText= "{}".format(indigo.devices[int(dev)].states[state])
			except:
				try:
					vText= "{}".format(indigo.devices[dev].states[state])
				except:
					return textIn, False
			try:
				if len(textOut)==0:
					textOut= textIn[:start]+vText
					return textOut, True
				textOut= textIn[:start]+vText+textOut
				return textOut, True
			except:
				return textIn, False
		except  Exception as e:
			if self.decideMyLog("Plotting"): self.indiLOG.log(40,"Line '{}' has error='{}'".format(sys.exc_info()[2].tb_lineno, e))
		return textIn, False
	   
		
#### actions ###################################################################################################

	########################################
	def validateActionConfigUi(self, valuesDict, typeId, devId):
		return True, valuesDict


	########################################
	def createOrModifyPlotCALLBACKaction(self, action1):
		self.createOrModifyPlot(self.convertACTION(action1))

	def createOrModifyPlot(self,action):
		logLevel = self.getLogLevel(action)


		if not "deviceNameOfPlot" in action:
			self.responseToActionInVariable(msg="error: no deviceNameOfPlot given")
			return

		theTargetId = -1
		dev =""
		self.indiLOG.log(20,"createOrModifyPlot-- "+json.dumps(action,sort_keys=True, indent=2))


		try:
			dev = indigo.devices[action["deviceNameOfPlot"]]
			if dev.pluginId == self.pluginId:  # if found but not of correct pluginType, exit
				theTargetId =dev.id
				nPlot=str(theTargetId)
			else:
				self.indiLOG.log(30,"createOrModifyPlot-- device already exist, but is not of type "+self.pluginName+" --  "+action["deviceNameOfPlot"])
				self.responseToActionInVariable(msg="error: device already exist, but is not of type "+self.pluginName+" --  "+action["deviceNameOfPlot"] )
				return
		except:  # does not exist yet, thats ok.
			pass

		descriptionText="created by a python script"
		if "dataSource"  in action :
			if action["dataSource"] =="mini": descriptionText="created by miniPlot"
		
		if theTargetId ==-1:
			self.indiLOG.log(30,"createOrModifyPlot-- device not found , creating: "+action["deviceNameOfPlot"])
			self.waitWithPLOTsync =True
			try:
				if self.decideMyLog("Restore"): self.indiLOG.log(10,"createOrModifyPlot-- trying:  "+action["deviceNameOfPlot"])
				indigo.device.create(protocol=indigo.kProtocol.Plugin,
					name=action["deviceNameOfPlot"],
					description=descriptionText,
					pluginId=self.pluginId,
					deviceTypeId="plots",
					configured=True
					 )
			except  Exception as e:
				self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
				self.indiLOG.log(40,"createOrModifyPlot-- device "+action["deviceNameOfPlot"]+" could not be created, unkonow error")
				self.responseToActionInVariable(msg="error: device "+action["deviceNameOfPlot"]+" could not be created, unkonow error" )
				return
			
#				props={"propA":"value","propB":"value"},
	#			folder=1234)
			dev = indigo.devices[action["deviceNameOfPlot"]]
			theTargetId = dev.id
			nPlot=str(theTargetId)
			self.PLOT[nPlot]					= copy.deepcopy(emptyPlot)
			self.PLOT[nPlot]["lines"]["0"]		= copy.deepcopy(emptyLine)
			self.PLOT[nPlot]["DeviceNamePlot"]	= action["deviceNameOfPlot"]

		if self.decideMyLog("Restore"): self.indiLOG.log(10,"createOrModifyPlot-- {}".format(self.PLOT[nPlot]))


# fill props with default or existing numbers if not given

		if "resxy0" in action:				self.PLOT[nPlot]["resxy"][0]	=action["resxy0"]
		else:								action["resxy0"] 				=self.PLOT[nPlot]["resxy"][0]
		if "resxy1" in action:				self.PLOT[nPlot]["resxy"][1]	=action["resxy1"]
		else:								action["resxy1"] 				=self.PLOT[nPlot]["resxy"][1]

		if not "MinuteBinNoOfDays"	in action:	action["MinuteBinNoOfDays"]	= self.PLOT[nPlot]["MHDDays"][0]
		else: 									action["MinuteBinNoOfDays"]	= str(min(int(action["MinuteBinNoOfDays"])	, self.noOfDays[0] ))

		if not "HourBinNoOfDays"	in action:	action["HourBinNoOfDays"]	= self.PLOT[nPlot]["MHDDays"][1]
		else: 									action["HourBinNoOfDays"]	= str(min(int(action["HourBinNoOfDays"])	, self.noOfDays[1] ))

		if not "DayBinNoOfDays"		in action:	action["DayBinNoOfDays"]	= self.PLOT[nPlot]["MHDDays"][2]
		else: 									action["DayBinNoOfDays"]	= str(min(int(action["DayBinNoOfDays"])		, self.noOfDays[2] ))

		if not "MinuteBinShift"		in action:	action["MinuteBinShift"]	= self.PLOT[nPlot]["MHDShift"][0]
		else: 									action["MinuteBinShift"]	= str(min(int(action["MinuteBinShift"])		, self.noOfDays[0]-1 ))

		if not "HourBinShift"		in action:	action["HourBinShift"]		= self.PLOT[nPlot]["MHDShift"][1]
		else:									action["HourBinShift"]		= str(min(int(action["HourBinShift"])		, self.noOfDays[1]-1 ))

		if not "DayBinShift"		in action:	action["DayBinShift"]		= self.PLOT[nPlot]["MHDShift"][2]
		else: 									action["DayBinShift"]		= str(min(int(action["DayBinShift"])		, self.noOfDays[2]-1 ))

		if not "MinuteXScaleFormat"	in action:	action["MinuteXScaleFormat"]= self.PLOT[nPlot]["MHDFormat"][0]
		
		if not "HourXScaleFormat"	in action:	action["HourXScaleFormat"]  = self.PLOT[nPlot]["MHDFormat"][1]
		
		if not "DayXScaleFormat"	in action:	action["DayXScaleFormat"]   = self.PLOT[nPlot]["MHDFormat"][2]

		if not "boxWidth"			in action:	action["boxWidth"]   		= self.PLOT[nPlot]["boxWidth"][2]



		action["NumberIsUsed"]=1
		self.PLOT[nPlot]["NumberIsUsed"]=1
		for key in self.PLOT[nPlot]:
			if key in action: 		continue
			if key == "MHDDays":	continue
			if key == "MHDShift":	continue
			if key == "resxy":		continue
			if key == "lines":		continue
			if key == "errorCount":	continue
			action[key]				=self.PLOT[nPlot][key]

		action, error, xxx,xxx2 = self.buttonConfirmPlotCALLBACKcheck(action, typeId="", targetId=theTargetId,script=True)															# store userinput
		if len(error) > 2: self.indiLOG.log(30,"createOrModifyPlot-- error:  {}".format(error))
		self.indiLOG.log(20,"createOrModifyPlot-- plot({}".format(nPlot)+":  {}".format(self.PLOT[nPlot]))
		if error =="":
			props=dev.pluginProps
			for theProp in self.PLOT[nPlot]:
				if theProp == "resxy":	continue
				if theProp =="lines": 	continue
				if theProp =="MHDDays":	continue
				if theProp =="MHDShift":continue
				props[theProp]= self.PLOT[nPlot][theProp]
			props["resxy0"]= action["resxy0"]
			props["resxy1"]= action["resxy1"]
			props["resxy"]=""
			props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
			dev.replacePluginPropsOnServer(props)
			self.writePlotParameters()
			self.setupGNUPlotFiles(calledfrom="createOrModifyPlotCALLBACKaction")
			if self.decideMyLog("Restore"): self.indiLOG.log(10,"createOrModifyPlot--  plot   {}".format(props))
			self.responseToActionInVariable(msg="ok: plot modified")
		else:
			self.responseToActionInVariable(msg=error)
		self.waitWithPLOTsync =False
		return
		
	########################################
	def deletePlotCALLBACKaction(self, action1):
		self.deletePlot(self.convertACTION(action1))
	
	########################################
	def deletePlot(self, action):
		logLevel= self.getLogLevel(action)

		if not "deviceNameOfPlot" in action:
			self.responseToActionInVariable(msg="error: no deviceNameOfPlot given")
			return


		for nPlot in self.PLOT:
			if action["deviceNameOfPlot"] == self.PLOT[nPlot]["DeviceNamePlot"]:
				dev = indigo.devices[action["deviceNameOfPlot"]]
				theTargetId = dev.id
				if self.decideMyLog("Restore"): self.indiLOG.log(20,"deletePlot--  device name , id: "+action["deviceNameOfPlot"]+"  {}".format(theTargetId))
				indigo.device.delete(theTargetId)
				del self.PLOT[nPlot]
				self.responseToActionInVariable(msg="ok: plot deleted")
				return
		self.responseToActionInVariable(msg="error: plot not found")
		return


	########################################
	def deleteLineCALLBACKaction(self, action1):
		self.deleteLine(self.convertACTION(action1))

	def deleteLine(self, action):
		logLevel= self.getLogLevel(action)

		if not "deviceNameOfPlot" in action:
			self.responseToActionInVariable(msg="error: no deviceNameOfPlot given")
			return
		if not "lineNumber" in action:
			self.responseToActionInVariable(msg="error: no lineNumber given")
			return


		theTargetId = -1
		dev =""
		for nPlot in self.PLOT:
			if action["deviceNameOfPlot"] == self.PLOT[nPlot]["DeviceNamePlot"]:
				dev = indigo.devices[action["deviceNameOfPlot"]]
				theTargetId = dev.id
				break
		if theTargetId ==-1:
			self.responseToActionInVariable(msg="error: device not found")
			return

		nLine=str(action["lineNumber"])
		if not nLine in self.PLOT[nPlot]["lines"]:
			self.responseToActionInVariable(msg="error: line not found")
			return
		del self.PLOT[nPlot]["lines"][nLine]
		self.responseToActionInVariable(msg="ok: line deleted")
		return



	########################################
	def deleteDeviceAndStateFromSelectionListCALLBACKaction(self, action1):
		self.deleteDeviceAndStateFromSelectionList(self.convertACTION(action1))

	def deleteDeviceAndStateFromSelectionList(self, action):
		logLevel = self.getLogLevel(action)

		self.indiLOG.log(30,"deleteDataSource-- {}".format(action))
		if not "deviceOrVariableName" in action:
			self.responseToActionInVariable(msg="error: no deviceOrVariableToBedeleted given")
			return
		if not "measurement" in action:
			self.responseToActionInVariable(msg="error: no measurement given")
			return
		if not "state" in action:
			self.responseToActionInVariable(msg="error: no state given")
			return

		found =False
		for  devNo in  self.DEVICE:
			if devNo =="0": continue
			if  self.DEVICE[devNo]["Name"] != action["deviceOrVariableName"]: continue
			for stateNo in  range(1,noOfStatesPerDeviceG+1):
				if  self.DEVICE[devNo]["state"][stateNo]  		!= action["state"]: 		continue
				if  self.DEVICE[devNo]["measurement"][stateNo] 	!= action["measurement"]: continue
				found =True
				break
			if found: break
			
		if not found:
			self.responseToActionInVariable(msg="error: device/state/measurement does not exist")
			return
		devNo=int(devNo)

		self.removePropFromDevice(devNo,stateNo)

		remDev=True
		for stateNo in  range(1,noOfStatesPerDeviceG+1):
			if  self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo]  	>0:
				self.responseToActionInVariable(msg="ok: device/state/measurement removed")
				remDev=False
				break

		if remDev:
			self.removeThisDevice.append(devNo)
			self.removeDevice()

		self.responseToActionInVariable(msg="ok: device with all its states removed from tracking")
		return



	########################################
	def deleteDeviceFromSelectionListCALLBACKaction(self, action1):
		self.deleteDeviceFromSelectionList(self.convertACTION(action1))

	def deleteDeviceFromSelectionList(self,action):
		logLevel = self.getLogLevel(action)
		
		if self.decideMyLog("Restore"): self.indiLOG.log(10,"deleteDataSource-- {}".format(action))
		if not "deviceOrVariableName" in action:
			self.responseToActionInVariable(msg="error: no deviceOrVariableToBedeleted given")
			return
		oneRemoved=False
		devList=[]
		for  devNo in  self.DEVICE:
			devList.append(devNo)
		for  devNo in  devList:
			self.indiLOG.log(30,"deleteDataSourceCALLBACKaction testing..DEVICE.." +self.DEVICE[devNo]["Name"])
			if  self.DEVICE[devNo]["Name"] != action["deviceOrVariableName"]: continue
			self.removeThisDevice.append(int(devNo))
			self.removeDevice()
			self.responseToActionInVariable(msg="ok: device with all properties removed from tracking")
			oneRemoved=True
			return
			
		self.responseToActionInVariable(msg="error: device does not exist")
		return




	########################################
	def showDeviceStatesCALLBACKaction(self, action1):
		self.showDeviceStates(self.convertACTION(action1))

	def showDeviceStates(self,action):
		logLevel = self.getLogLevel(action)

		if not "deviceOrVariableName" in action:
			self.responseToActionInVariable(msg="error: no deviceOrVariable given")
			self.indiLOG.log(20,"showDeviceStates-- error: no deviceOrVariable given ")
			return

		devID	=-1
		found = False
		reqName= action["deviceOrVariableName"]
		self.indiLOG.log(20,"List Device & Variable States-- that contain numbers")
		for nDev in range(1,len(self.listOfPreselectedDevices)):
			name=self.listOfPreselectedDevices[nDev][1]
			if self.listOfPreselectedDevices[nDev][1].find("Var-") >-1:
				if "Var-"+reqName == name or  reqName=="***":
					name =name[4:]
					self.responseToActionInVariable(msg="ok: available state = value")
					try:
						theValue= indigo.variables[name].value
						xxx= str(GT.getNumber(theValue))
					except:
						self.indiLOG.log(20,name[4:])
						xxx=""
						theValue=" not available"
					
					self.indiLOG.log(20,"variable: "+name[4:].rjust(40)+":   value: "+theValue.ljust(30)+ "; used as:  " +xxx)
					found =True
					if action["deviceOrVariableName"]!="***": return
			elif reqName == name           or   reqName =="***":
				devID = self.listOfPreselectedDevices[nDev][0]
				dev =  indigo.devices[devID]
				theStates = dev.states.keys()
				retList=[]
				count=0
				for test in theStates:
					try:
						if "Mode" in test or "All" in test or ".ui" in test:
							skip= True			# reject fanMode etc
						else:
							skip= False
					except:
						skip=False
					if not skip:	
						val= dev.states[test]
						x = GT.getNumber(val)
						count+=1
						retList.append(test+"(\"{}".format(val)+"\"==>{}".format(x)+"), ")
				found =True
				first= "device  : "+ (name).rjust(40)+":   "
				for ii in range(0,count,5):
					out=""
					for jj in range(ii,min(ii+5,count),1):
						out+=retList[jj]
					self.indiLOG.log(20,first+out)
					first= " ".rjust(50)+":   "
				self.responseToActionInVariable(msg="ok")
				if action["deviceOrVariableName"]!="***": return

		if not found:
			self.responseToActionInVariable(msg="error: device/variable not in eligible list -- might not have  proper numbers")
			self.indiLOG.log(20,"showDeviceStates-- error: device/variable not in eligible list -- might not have  proper numbers "+action["deviceOrVariableName"])
			return

		return

	########################################
	def PrintDeviceStates(self, dev="***"):
		self.showAllDeviceStates()
	
	def showAllDeviceStates(self):
		try:
			out = "\n"
			out += "\nvariables  id ---------------------                      Name   Value                               used as"
			for var in indigo.variables:
				name=var.name
				try:
					val = var.value
					x = str(GT.getNumber(val))
				except:
					x = "not available"
					val =""
				if x == "x": x = "not usable"
				out += "\n{:<15}{:>47}:{:<35}; ==> {} ".format(var.id, name, val[:35], x) 
			out += "\ndevice id --------------------------                     Name State(Value:used as), State(Value:used as), ..."
			for dev in indigo.devices:
				name=dev.name
				id = str(dev.id)
				retList = []
				count = 0
				keylist = dev.states.keys()
				keylist.sort()

				for test in keylist:
					val = dev.states[test]
					x = GT.getNumber(val)
					if x == "x": x = "not usable"
					count+=1
					retList.append("{}(\"{:15}\":{}) ".format(test, val, x) )

				first = name
				for ii in range(0,count,5):
					out2 = ""
					for jj in range(ii,min(ii+5,count),1):
						out2 += retList[jj]
					out += "{:<14} {:>47}:{}\n".format(id, first, out2)
					id   = " "
					first= " "
				self.responseToActionInVariable(msg="ok")
			self.indiLOG.log(10, out)			
			self.indiLOG.log(20,"print dev states: check plugin.log file ")
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return




	########################################
	def setConfigParametersCALLBACKaction(self, action1):
		self.setConfigParameters(self.convertACTION(action1))

	def setConfigParameters(self, action):
		logLevel= self.getLogLevel(action)

		SQLupdatesNeeded=0

		if  "logLevel" 				in action:
			self.debugLevel = [logLevel]
		elif  "debugLevel" 				in action:
			try: self.debugLevel = json.loads(action["debugLevel"])
			except: pass
			self.indiLOG.log(20,"setConfigParameters-- set debugLevel to: {}".format(self.debugLevel ))
			for d in ["Restore","General","Initialize","Plotting","Matplot","SQL","Special","all"]:
				self.pluginPrefs["debug"+d] = d in  self.debugLevel
			
			

		if  "indigoPNGdir" 				in action:
			if len(action["indigoPNGdir"]) > 10:
				self.indigoPNGdir = action["indigoPNGdir"]
				self.pluginPrefs["indigoPNGdir"]=self.indigoPNGdir
				self.indiLOG.log(20,"setConfigParameters-- set indigoPNGdir to: {}".format(self.indigoPNGdir ))

		if  "gnuPlotBin" 				in action:
			if len(action["gnuPlotBin"]) > 10:
				self.gnuPlotBinary = action["gnuPlotBin"]
				self.pluginPrefs["gnuPlotBin"]=self.gnuPlotBinary
				self.indiLOG.log(20,"setConfigParameters-- set gnuPlotBin to: {}".format(self.gnuPlotBinary ))


		if  "sqlDynamic" 		in action:
			xxx									=	action["sqlDynamic"]
			if 	(	(xxx.find("batch")==0 and (self.sqlDynamic == "online" or self.sqlDynamic == "None"))
				 or	(xxx == "online"      and (self.sqlDynamic.find("batch") ==0  or self.sqlDynamic == "None"))):
				self.sqlHistListStatus 			= [10 for i in range(self.dataColumnCount+1)]
				self.sqlColListStatus 				= [10 for i in range(self.dataColumnCount+1)]
				self.sqlColListStatusRedo			= [0  for i in range(self.dataColumnCount+1)]
				self.sqlLastID  				= ["0" for i in range(self.dataColumnCount+1)]
				self.sqlLastImportedDate	= [ "201401010101" for i in range(self.dataColumnCount+1)]
				SQLupdatesNeeded					= 10
				self.devicesAdded 				= 5
			self.sqlDynamic						= xxx
			self.pluginPrefs["sqlDynamic"]		= self.sqlDynamic
			self.indiLOG.log(20,"setConfigParameters-- set sqlDynamic to: {}".format(self.sqlDynamic ))




		if  "gnuORmat" 		in action:
			self.gnuORmat						=	action["gnuORmat"]
			self.pluginPrefs["gnuORmat"]		=	self.gnuORmat
			self.indiLOG.log(20,"setConfigParameters-- set gnuORmat to: {}".format(self.gnuORmat ))

			if  action["gnuORmat"] =="mat":
				self.gnuORmatSET( "mat")
			else:
				self.gnuORmatSET( "gnu")
		



		for consumptionType in availConsumptionTypes:
			for n in range(1,noOfCostTimePeriods+1):
				if consumptionType+str(n) in action:
					xx=action[consumptionType+str(n)]
					try:
						self.consumptionCostData[consumptionType][n]= json.loads(xx)
						try:
							if self.consumptionCostData[consumptionType][n]["Period"] == emptyCost["Period"]: a=1
						except:
							self.consumptionCostData[consumptionType][n]["Period"] = emptyCost["Period"]
						
						if self.consumptionCostData[consumptionType][n]["Period"] < emptyCost["Period"]:	self.periodTypeForConsumptionType[consumptionType] ="Period"
						if self.consumptionCostData[consumptionType][n]["day"] < 9: 						self.periodTypeForConsumptionType[consumptionType] ="WeekDay"
						SQLupdatesNeeded		= 10
					except:
						self.indiLOG.log(40,"consumption import failed or definition wrong or old: "+xx)
						self.indiLOG.log(40,str(self.consumptionCostData[consumptionType][n]))
		
		self.indigoCommand.append("redoParameters")
		self.responseToActionInVariable(msg="ok: parameters set")


		if SQLupdatesNeeded>0:
			for  theCol  in range (1,self.dataColumnCount+1):																# list of dev/props
				devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
				stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
				theMeasurement 	=	self.DEVICE["{}".format(devNo)]["measurement"][stateNo]
				if theMeasurement.find("Consumption") >-1:
					self.sqlHistListStatus[theCol] = 50
					self.devicesAdded = 5
		if self.devicesAdded ==5: self.indiLOG.log(20,"New Consumption Cost parameters.. need to updates data from SQL data base to recalculate Energ costs")

		

		if self.devicesAdded >0 :self.devicesAdded = 2			# set signal at the end when all paramerts are set
		self.waitWithPlotting	= False
		self.newPREFS			=True


		return


	########################################
	def addDeviceAndStateToSelectionListCALLBACKaction(self, action1):
		self.addDeviceAndStateToSelectionList(self.convertACTION(action1))

	def addDeviceAndStateToSelectionList(self, action):
		logLevel= self.getLogLevel(action)

		self.indiLOG.log(30,"createDataSource to be tracked:     ..{}".format(action))
		if not "deviceOrVariableName" in action:
			self.responseToActionInVariable(msg="error: no deviceOrVariable given")
			self.indiLOG.log(30,"createDataSource-- error: no deviceOrVariable given ")
			return 0,0
		if len(action["deviceOrVariableName"])< 3:
			self.responseToActionInVariable(msg="error: empty deviceOrVariable given")
			self.indiLOG.log(30,"createDataSource-- error: empty deviceOrVariable given ")
			return 0,0

		if not "measurement" in action:
			self.responseToActionInVariable(msg="error: no measurement given")
			self.indiLOG.log(30,"createDataSource-- error: no measurement given ")
			return 0,0
		if not action["measurement"] in supportedMeasurements :
			self.responseToActionInVariable(msg="error:  measurement not in list {}".format(supportedMeasurements))
			self.indiLOG.log(30,"createDataSource-- error:  measurement "+ action["measurement"]+"  not in list {}".format(supportedMeasurements))
			return 0,0

		if not "state" in action:
			self.responseToActionInVariable(msg="error: no state given")
			self.indiLOG.log(30,"createDataSource-- error: no state given ")
			return 0,0
		
		if not "offset" in action:		action["offset"]	= copy.deepcopy(emptyDEVICE["offset"][1])
		if not "multiplier" in action:	action["multiplier"]= copy.deepcopy(emptyDEVICE["multiplier"][1])
		if not "minValue" in action:	action["minValue"]	= copy.deepcopy(emptyDEVICE["minValue"][1])
		if not "maxValue" in action:	action["maxValue"]	= copy.deepcopy(emptyDEVICE["maxValue"][1])
		if not "fillGaps" in action:	action["fillGaps"]	= copy.deepcopy(emptyDEVICE["fillGaps"][1])
		if not "resetType" in action:	action["resetType"]	= copy.deepcopy(emptyDEVICE["resetType"][1])
		else:
										action["resetType"]	= json.loads(action["resetType"])
		if action["resetType"] ==0: action["resetType"]="0"
		if (action["resetType"] =="0" and action["measurement"].find("Consumption") >-1) and (action["measurement"]!="integrate"):
			self.responseToActionInVariable(msg="error: resetType given")
			self.indiLOG.log(30,"createDataSource-- error: resetType given ")
			return 0,0
			
		if not "devOrVar" in action:	action["devOrVar"]	= "Dev-"


# check if input data is available in devices or variables that qualify
		self.deviceDevOrVarNew = ""
		devOrVarId	=-1
		nameA= action["deviceOrVariableName"]
		dOv = action["devOrVar"]
		for nDev in range(1,len(self.listOfPreselectedDevices)):
			name=self.listOfPreselectedDevices[nDev][1]
			if self.listOfPreselectedDevices[nDev][1].find("Var-") !=0:
				if nameA.find("Dev-")  ==0:
					if nameA[4:] == name :
						self.deviceDevOrVarNew ="Dev-"
						break
				elif dOv =="Dev-":
					if nameA == name :
						self.deviceDevOrVarNew ="Dev-"
						break
				else:
					if nameA == name :
						self.deviceDevOrVarNew ="Dev-"
						break
			elif self.listOfPreselectedDevices[nDev][1].find("Var-") ==0:
				if nameA.find("Var-")  ==0:
					if nameA == name  or nameA[4:] == name[4:]:
						self.deviceDevOrVarNew ="Var-"
						action["state"]= "value"
						break
				elif dOv =="Var-":
					if nameA == name[4:] or nameA == name:
						self.deviceDevOrVarNew ="Var-"
						action["state"]= "value"
						break
				else:
					if nameA == name :
						self.deviceDevOrVarNew ="Var-"
						action["state"]= "value"
						break

		if self.deviceDevOrVarNew !="":
			devOrVarId = self.listOfPreselectedDevices[nDev][0]
			self.indiLOG.log(20,"createDataSource-- found .." +name+" = "+action["deviceOrVariableName"]+"  {}".format(devOrVarId))

		if devOrVarId == -1:
			self.responseToActionInVariable(msg="error: device not found")
			self.indiLOG.log(30,"createDataSource-- error: device not found "+action["deviceOrVariableName"])
			return 0,0

		propList = self.preSelectStates(devOrVarId)
		self.indiLOG.log(20,"createDataSource .theProp-state.{}".format(propList)+"-"+action["state"])
		foundState= ""
		for theProp in propList:
			if theProp[0] == action["state"]:
				foundState = theProp
				break
			
		if foundState == "":
			self.indiLOG.log(30,"createDataSource-- state of device not found: -"+ action["state"]+"- available states: {}".format(propList))
			self.responseToActionInVariable(msg="error: device/state not found")
			return 0,0


# already in selectable list?
		devNoFound	= 0
		emptySlot	= 0
		devStateFound=False
		for devNo in self.DEVICE:
			if devNo =="0": continue
			DEV = self.DEVICE["{}".format(devNo)]
			if ( DEV["Name"]	!= action["deviceOrVariableName"] and
				 DEV["Name"]	!= action["deviceOrVariableName"][4:]):				continue
			if  DEV["devOrVar"]	!= self.deviceDevOrVarNew:							continue
			devNoFound = int(devNo)
			for stateNo in range(1,noOfStatesPerDeviceG+1):
				if  DEV["state"][stateNo] == "None" and emptySlot ==0:
					emptySlot= stateNo
					continue
				if  DEV["state"][stateNo]			!= action["state"]:				continue
				devStateFound=True
				if  DEV["measurement"][stateNo]		!= action["measurement"]:		continue
				if  DEV["multiplier"][stateNo]		!= float(action["multiplier"]):	continue
				if  float(DEV["minValue"][stateNo]) != float(action["minValue"]):	continue
				if  float(DEV["maxValue"][stateNo]) != float(action["maxValue"]):	continue
				if  action["measurement"].find("Consumption")>-1:
					if  DEV["resetType"][stateNo] 	!= action["resetType"]:			continue
				if  DEV["fillGaps"][stateNo]		!= action["fillGaps"]:			continue
				if  DEV["offset"][stateNo]			!= float(action["offset"]):		continue
				self.responseToActionInVariable(msg="ok: device/state/Measurement already exists")
				self.indiLOG.log(30,"createDataSource-- devNo and state already selected: -{}".format(devNo)+ " {}".format(stateNo))
				return devNo,stateNo

# not found... added to list
# find empty slot in existig DEVICE listing
		if devNoFound !=0 and emptySlot !=0:
			devNo  = devNoFound
			stateNo = emptySlot
		else:
# no empty slot, create a new DEVICE:
			for devNo in range (1,999):		# find first unused slot
				try:
					if self.DEVICE["{}".format(devNo)]["deviceNumberIsUsed"] ==0: break
				except:
					break
			stateNo = 1
			self.DEVICE["{}".format(devNo)] = copy.deepcopy(emptyDEVICE)

		DEV=self.DEVICE["{}".format(devNo)]
		self.indiLOG.log(20,"createDataSource-- adding to selection devNo {}".format(devNo)+ "; stateNo {}".format(stateNo))
		self.waitWithRedoIndex =True


		self.addColumnToData()
		if action["deviceOrVariableName"].find("Var") ==-1:
			DEV["Name"] 			= action["deviceOrVariableName"]
		else:
			DEV["Name"] 			= action["deviceOrVariableName"][4:]
		self.indiLOG.log(20,"createDataSource-- Name -"+ DEV["Name"])
		DEV["deviceNumberIsUsed"]	= 1
		DEV["devOrVar"]				= self.deviceDevOrVarNew


		if self.deviceDevOrVarNew =="Var-":
			self.deviceId = indigo.variables[action["deviceOrVariableName"].replace("Var-","")].id
		else:
			self.deviceId = indigo.devices[action["deviceOrVariableName"]].id
		DEV["Id"]					= self.deviceId
		DEV["state"][stateNo] 		= action["state"]
		DEV["measurement"][stateNo] = action["measurement"]
		DEV["stateToIndex"][stateNo]= self.dataColumnCount
		DEV["offset"][stateNo]		= float(action["offset"])
		DEV["multiplier"][stateNo] 	= float(action["multiplier"])
		DEV["minValue"][stateNo] 	= float(action["minValue"])
		DEV["maxValue"][stateNo] 	= float(action["maxValue"])
		DEV["fillGaps"][stateNo] 	= action["fillGaps"]
		DEV["resetType"][stateNo] 	= action["resetType"]

		if DEV["measurement"][stateNo].find("Consumption") >-1:
			self.consumedDuringPeriod["{}".format(self.dataColumnCount)] = copy.deepcopy(emptyconsumedDuringPeriod)

		if devStateFound :
			self.sqlColListStatus[self.dataColumnCount] = 0
		else:
			self.sqlColListStatus[self.dataColumnCount] = 10
			self.sqlLastID[self.dataColumnCount]	 = 0

		self.sqlHistListStatus[self.dataColumnCount]		= 49
		self.updateALL									= True
		
		self.sqlColListStatus[0]							= 0
		self.sqlHistListStatus[0]							= 0
		
		if DEV["devOrVar"] =="Var-": self.listOfSelectedDataColumnsAndDevPropName.append((self.dataColumnCount,"Var-"+DEV["measurement"][stateNo]+"-"+DEV["Name"]))
		if DEV["devOrVar"] =="Dev-": self.listOfSelectedDataColumnsAndDevPropName.append((self.dataColumnCount,       DEV["measurement"][stateNo]+"-"+DEV["Name"]+"-"+self.tryNiceState(action["state"])))

		self.dataColumnToDevice0Prop1Index[self.dataColumnCount]= [int(devNo),int(stateNo)]
		
		self.indiLOG.log(20," device sql started  with sqlColListStatus={}".format(self.sqlColListStatus[self.dataColumnCount])+"; sqlHistListStatus={}".format(self.sqlHistListStatus[self.dataColumnCount]) +"; devStateFound={}".format(devStateFound))

		if self.redolineDataSource(calledfrom="addDeviceAndStateToSelectionList") ==-1:
			if self.redolineDataSource(calledfrom="addDeviceAndStateToSelectionList") ==-1:
				if self.redolineDataSource(calledfrom="addDeviceAndStateToSelectionList") ==-1:
					self.redolineDataSource(calledfrom="addDeviceAndStateToSelectionList")


		self.putDeviceParametersToFile()
		self.dataColumnCount= len(self.dataColumnToDevice0Prop1Index)-1
		self.devicesAdded =2
		self.scriptNewDevice =2

		self.waitWithRedoIndex =False
		self.redoParameters()
		self.responseToActionInVariable(msg="ok: device/state/measurement added")
		return devNo,stateNo



					
		
	########################################
	def createOrModifyLineCALLBACKaction(self, action1):
		self.createOrModifyLine(self.convertACTION(action1))

	def createOrModifyLine(self, action):
		logLevel= self.getLogLevel(action)

		try:

			self.indiLOG.log(20,"createOrModifyLine-- "+json.dumps(action,sort_keys=True, indent=2))
	#		action = copy.deepcopy(action1.props)
			if not "deviceNameOfPlot" in action:
				self.responseToActionInVariable(msg="error: no deviceNameOfPlot given")
				return

			if not "lineNumber" in action:
				self.responseToActionInVariable(msg="error: no lineNumber given")
				return


	# find PlotType:
			found = False
			for nPlot in self.PLOT:
				if action["deviceNameOfPlot"] == self.PLOT[nPlot]["DeviceNamePlot"]:
					if "PlotType" in self.PLOT[nPlot]:
						action["PlotType"] =self.PLOT[nPlot]["PlotType"]
						found = True
						break
			if not found:
					self.responseToActionInVariable(msg="error:  PlotType not found")
					self.indiLOG.log(20,"createOrModifyLine--  PlotType not found.for action {}".format(action))
					self.indiLOG.log(20,"createOrModifyLine--  PlotType not found.for.nPlot ")
					return

			doB =False
			if action["PlotType"] =="dataFromTimeSeries":

				if not "deviceOrVariableToBePlottedLineA" in action:
					self.responseToActionInVariable(msg="error: no deviceOrVariableToBePlottedLineA given")
					return
				if action["deviceOrVariableToBePlottedLineA"] !="-1":
					if len(action["deviceOrVariableToBePlottedLineA"]) < 3:
						self.responseToActionInVariable(msg="error:  deviceOrVariableToBePlottedLineA is empty")
						return
					
					if not "MeasurementLineA" in action:
						self.responseToActionInVariable(msg="error: no MeasurementLineA given")
						return
					if not "StateToBePlottedLineA" in action:
						self.responseToActionInVariable(msg="error: no StateToBePlottedLineA given")
						return
					if not "offsetA"	in action:		action["offsetA"] = copy.deepcopy(emptyDEVICE["offset"][1])
					if not "multiplierA"in action:		action["multiplierA"] = copy.deepcopy(emptyDEVICE["multiplier"][1])
					if not "minValueA"	in action:		action["minValueA"] = copy.deepcopy(emptyDEVICE["minValue"][1])
					if not "maxValueA"	in action:		action["maxValueA"] = copy.deepcopy(emptyDEVICE["maxValue"][1])
					if not "fillGapsA"	in action:		action["fillGapsA"] = copy.deepcopy(emptyDEVICE["fillGaps"][1])
					if not "resetTypeA" in action:		action["resetTypeA"]= copy.deepcopy(emptyDEVICE["resetType"][1])
					if not "devOrVarA"	in action:		action["devOrVarA"]  = ""
					
					action2={}
					action2["logLevel"]				=  action["logLevel"]
					action2["deviceOrVariableName"]	=  action["deviceOrVariableToBePlottedLineA"]
					action2["measurement"]			=  action["MeasurementLineA"]
					action2["state"]				=  action["StateToBePlottedLineA"]
					action2["offset"]				=  float(action["offsetA"])
					action2["multiplier"]			=  float(action["multiplierA"])
					action2["minValue"]				=  float(action["minValueA"])
					action2["maxValue"]				=  float(action["maxValueA"])
					action2["fillGaps"]				=  action["fillGapsA"]
					action2["resetType"]			=  action["resetTypeA"]
					action2["devOrVar"]				=  action["devOrVarA"]
					devNo,stateNo = self.addDeviceAndStateToSelectionList(action2)
					

					doB=False
					if  "deviceOrVariableToBePlottedLineB" in action:
						if len(action["deviceOrVariableToBePlottedLineB"]) > 3:
							if not "MeasurementLineB" in action:
								self.responseToActionInVariable(msg="error: no MeasurementLineB given")
							else:
								if "StateToBePlottedLineB" in action:
									action2={}
									action2["logLevel"]				=  action["logLevel"]
									action2["deviceOrVariableName"]	= action["deviceOrVariableToBePlottedLineB"]
									action2["measurement"]			= action["MeasurementLineB"]
									action2["state"]				= action["StateToBePlottedLineB"]
									
									if "minValueB" in action:		action2["minValue"]		= float(action["minValueB"])
									else:							action2["minValue"]		= copy.deepcopy(emptyDEVICE["minValue"][1])
									
									if "maxValueB" in action:		action2["maxValue"]		= float(action["maxValueB"])
									else:							action2["maxValue"]		= copy.deepcopy(emptyDEVICE["maxValue"][1])

									if "offsetB" in action:			action2["offset"]		= float(action["offsetB"])
									else:							action2["offset"]		= copy.deepcopy(emptyDEVICE["offset"][1])

									if "multiplierB" in action:		action2["multiplier"]	= float(action["multiplierB"])
									else:							action2["multiplier"]	= copy.deepcopy(emptyDEVICE["multiplier"][1])
									
									if "fillGapsB" in action:		action2["fillGaps"]		= action["fillGapsB"]
									else:							action2["fillGaps"]		= copy.deepcopy(emptyDEVICE["fillGaps"][1])
									
									if "resetTypeB" in action:		action2["resetType"]	= action["resetTypeB"]
									else:							action2["resetType"]	= copy.deepcopy(emptyDEVICE["resetType"][1])
									if "devOrVarB" in action:		action2["devOrVar"]		= action["devOrVarB"]
									else:							action2["devOrVar"]		= ""
									
									devNoB,stateNoB = self.addDeviceAndStateToSelectionList(action2)
									doB=True
			else:
				if not "dataColumnForFileOrVariableA" in action:
					self.responseToActionInVariable(msg="error: no dataColumnForFileOrVariableA given")
					return



			theTargetId = -1
			dev =""
			for nPlot in self.PLOT:
				if action["deviceNameOfPlot"] == self.PLOT[nPlot]["DeviceNamePlot"]:
					dev = indigo.devices[action["deviceNameOfPlot"]]
					theTargetId = dev.id
					break
			if theTargetId ==-1:
				self.indiLOG.log(30,"createOrModifyLine--  device not found")
				self.responseToActionInVariable(msg="error: device not found")
				return

			nLine=str(action["lineNumber"])
			if not nLine in self.PLOT[nPlot]["lines"]:
				self.PLOT[nPlot]["lines"][nLine] = copy.deepcopy(emptyLine)



	# find data source

			if self.PLOT[nPlot]["PlotType"] =="dataFromTimeSeries":
				if action["deviceOrVariableToBePlottedLineA"] !="-1":
					if stateNo ==0:
						self.responseToActionInVariable(msg="error: device/state/measurement not in select list")
						if self.decideMyLog("Restore"): self.indiLOG.log(30," createOrModifyLine--  device/state/measurement not in select list -A-  "
							+" {}".format(action["deviceOrVariableToBePlottedLineA"])
							+"-{}".format(action["StateToBePlottedLineA"])
							+"-{}".format(action["MeasurementLineA"])
							)
						return
					lineToColumnIndexA=int(self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo])
					if self.decideMyLog("Restore"): self.indiLOG.log(20," createOrModifyLine--  found lineToColumnIndexA {}".format(lineToColumnIndexA))
					self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"] = lineToColumnIndexA
					
					if  doB:
						if stateNoB ==0:
							self.responseToActionInVariable(msg="error: device/state/measurement not in select list")
							if self.decideMyLog("Restore"): self.indiLOG.log(30," createOrModifyLine--  device/state/measurement not in select list -A-  "
										+" {}".format(action["deviceOrVariableToBePlottedLineB"])
										+"-{}".format(action["StateToBePlottedLineB"])
										+"-{}".format(action["MeasurementLineB"])
								)
							return
						lineToColumnIndexB=int(self.DEVICE["{}".format(devNoB)]["stateToIndex"][stateNoB])
						if self.decideMyLog("Restore"): self.indiLOG.log(20," createOrModifyLine--  found lineToColumnIndexB {}".format(lineToColumnIndexB))
						self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"] = lineToColumnIndexB
				else:
					self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"] = int(action["deviceOrVariableToBePlottedLineA"])

			elif self.PLOT[nPlot]["PlotType"] =="dataFromFile":
				self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"] =int(action["dataColumnForFileOrVariableA"])
				if  "dataColumnForFileOrVariableB" in action:
					self.indiLOG.log(20,"createOrModifyLine--  action[dataColumnForFileOrVariableB]  {}".format(action["dataColumnForFileOrVariableB"]))
					self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"] =int(action["dataColumnForFileOrVariableB"])

			elif self.PLOT[nPlot]["PlotType"] =="dataFromVariable":
				self.indiLOG.log(20,"createOrModifyLine--  nLine  {}".format(nLine))
				self.indiLOG.log(20,"createOrModifyLine--  action[dataColumnForFileOrVariableA]  {}".format(action["dataColumnForFileOrVariableA"]))
				self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"] =int(action["dataColumnForFileOrVariableA"])
				if  "dataColumnForFileOrVariableB" in action:
					self.indiLOG.log(20,"createOrModifyLine--  action[dataColumnForFileOrVariableB]  {}".format(action["dataColumnForFileOrVariableB"]))
					self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"] =action["dataColumnForFileOrVariableB"]

			else:
				self.responseToActionInVariable(msg="error: no data type defined (eg dataFromTimeSeries)")
				return

			self.CurrentLineNo =nLine
			for key in self.PLOT[nPlot]["lines"][nLine]:
				if key not in action: action[key]	=self.PLOT[nPlot]["lines"][nLine][key]

			valuesDict , error = self.buttonConfirmLinePropsCALLBACKcheck(action,typeId="plot", targetId=theTargetId,script=True)
			if error =="":
				props=dev.pluginProps
				for theProp in self.PLOT[nPlot]:
					if theProp== "resxy": continue
					if theProp== "lines": continue
					if theProp== "MHDDays": continue
					if theProp== "MHDShift": continue
					props[theProp]= self.PLOT[nPlot][theProp]
				props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
				if "resxy" in props: del props["resxy"]
				dev.replacePluginPropsOnServer(props)
				self.writePlotParameters()
				self.setupGNUPlotFiles(calledfrom="createOrModifyLineCALLBACKaction")
				self.responseToActionInVariable(msg="ok")
				return

			self.responseToActionInVariable(msg=error)
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			

		return

############  create / show plot actions ###################

	########################################
	def createPlotPNGCALLBACKaction(self, action1):
		self.createPlotPNG(self.convertACTION(action1))

	def createPlotPNG(self, action):
		logLevel= self.getLogLevel(action)

		self.indiLOG.log(20,"createPlotPNG-- "+action["deviceNameOfPlot"])
		if not "deviceNameOfPlot" in action:
			self.responseToActionInVariable(msg="error: no plotnameToBeCreated given")
			return

		plots=action["deviceNameOfPlot"]
		if plots =="":						self.plotNOWCommand=["all plots",""]
		else:								self.plotNOWCommand=[plots,""]
		self.indigoCommand.append("plotNow")
		self.responseToActionInVariable(msg="ok: being created")
		return

	########################################
	def showPlotONLYCALLBACKaction(self, action1):
		self.showPlotONLY(self.convertACTION(action1))

	def showPlotONLY(self, action):
		logLevel= self.getLogLevel(action)
		
		self.indiLOG.log(20,"showPlotONLY-- action   {}".format(action))
		if not "deviceNameOfPlot" in action:
			self.responseToActionInVariable(msg="error: no plotnameToBeCreated given")
			return
		plots=action["deviceNameOfPlot"]
		self.plotNOWCommand=[plots,plots]
		self.indigoCommand.append("plotNowOnly")
		self.responseToActionInVariable(msg="ok: being plotted")
		return

	########################################
	def showPlotPNGCALLBACKaction(self, action1):
		self.showPlotPNG(self.convertACTION(action1))
	
	def showPlotPNG(self, action):
		logLevel= self.getLogLevel(action)


		self.indiLOG.log(20,"showPlotPNG-- action   {}".format(action))
		if not "deviceNameOfPlot" in action:
			self.responseToActionInVariable(msg="error: no plotnameToBeCreated given")
			return
		plots=action["deviceNameOfPlot"]
		if plots =="":						self.plotNOWCommand=["all plots",""]
		else:								self.plotNOWCommand=[plots,plots]
		self.indigoCommand.append("plotNow")
		self.responseToActionInVariable(msg="ok: being plotted")
		return
############




############  actions  export print ...  ###################

	########################################
	def doExportCALLBACKaction(self, action1):
		self.doExport(self.convertACTION(action1))

	def doExport(self, action):
		logLevel= self.getLogLevel(action)
		self.indiLOG.log(20,"doExport-- action   ")
		self.indigoCommand.append("export")
		self.responseToActionInVariable(msg="ok: exported")
		return
	
	
	########################################
	def doExportMiniCALLBACKaction(self, action1):
		self.doExportMini(self.convertACTION(action1))

	def doExportMini(self, action):
		logLevel= self.getLogLevel(action)
		self.indiLOG.log(20,"doExportmini-- action   ")
		self.indigoCommand.append("exportMini")
		self.responseToActionInVariable(msg="ok: exported")
		return
	

	########################################
	def savePlotCALLBACKaction(self,action1):
		self.savePlot(self.convertACTION(action1))
		
	def savePlot(self,action):
		logLevel= self.getLogLevel(action)
	
		name =action["deviceNameOfPlot"]
		try:
			dev = indigo.devices[name]
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.responseToActionInVariable(msg="error: device  does not exist, can not save  "+action1.props["deviceNameOfPlot"])
			self.indiLOG.log(30,"savePlotCALLBACK--  device  does not exist, can not save  "+action1.props["deviceNameOfPlot"])
			return
			
		nPlot =str(dev.id)
		props=dev.pluginProps
		props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
		dev.replacePluginPropsOnServer(props)
		self.justSaved					= True
		self.newPLOTS					= "allPlots"
		
		self.redoParam()
		
		return
############



############  actions  utility methods  ###################

	########################################
	def convertACTION(self, action1):
		action={}
		for pp in action1.props:
			action[pp]=action1.props[pp]
		return action

	########################################
	def responseToActionInVariable(self, msg=""):
		try:
			indigo.variable.create("INDIGOplotD-Script-Message", msg)
		except:
			indigo.variable.updateValue("INDIGOplotD-Script-Message", msg)
		return

	########################################
	def getLogLevel(self,action):
		try:
			if "logLevel" in  action:
				try: 
					logLevel = int(action["logLevel"])
					if logLevel != 0: return "all"
					else: return "all"
				except: return action["logLevel"]
			else:
				return ""
		except:
			return ""
############





#### actions   end





#### configs  ###################################################################################################


########################################
	def filterListOfPlotDeviceNamesaction(self,  filter="self", valuesDict=None, typeId="", targetId=0):
		retList = []
		for nPlot in self.PLOT:
			retList.append((self.PLOT[nPlot]["DeviceNamePlot"],self.PLOT[nPlot]["DeviceNamePlot"]))
		retList.append((0,"recreate all Plots, but do not display them"))
		return retList
		


#### set visibility in configs

	########################################
	def DevicesOnOffCALLBACK(self, valuesDict=None, typeId="", targetId=0):

		if valuesDict["DefineDevices"]:
			if  not valuesDict["Experts"]:
				valuesDict["ExpertsAndDevices"] = True
			else:
				valuesDict["ExpertsAndDevices"] = False
		else:
			valuesDict["ExpertsAndDevices"] = False

		return self.setViewOnOff(valuesDict)
	########################################
	def ExpertOnOffCALLBACK(self, valuesDict=None, typeId="", targetId=0):

		if  not valuesDict["Experts"]:
			valuesDict["Expexx1rtsAndDevices"] = False
		else:
			if valuesDict["DefineDevices"]:
				valuesDict["ExpertsAndDevices"] = True

		return self.setViewOnOff(valuesDict)
	



	########################################
	def plotDataTypeCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		valuesDict = self.setViewOnOff(valuesDict)
		return valuesDict
	########################################
	def plotXYvPolarCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		valuesDict = self.setViewOnOff(valuesDict)
		return valuesDict


	########################################
	def PlotsOnOffCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		valuesDict = self.setViewOnOff(valuesDict)
		return valuesDict
	########################################
	def LinesOnOffCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		valuesDict = self.setViewOnOff(valuesDict)
		return valuesDict

	######################################
	def ExpertOnOffPlotCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		valuesDict = self.setViewOnOff(valuesDict)
		return valuesDict


	########################################
	def setViewOnOff(self, valuesDict):


		try:
			if valuesDict["DefinePlots"]:
				if valuesDict["PlotType"] =="dataFromTimeSeries":
					valuesDict["TimeseriesAndPlots"] = True
				else:
					valuesDict["TimeseriesAndPlots"] = False

				if valuesDict["XYvPolar"] =="xy" and valuesDict["ExpertsP"] == True and valuesDict["PlotType"] == "dataFromTimeSeries":
					valuesDict["showBinsS"] = True
					valuesDict["amPm"] = True
				else:
					valuesDict["showBinsS"] = False
					valuesDict["amPm"] = False
				
				if valuesDict["PlotType"] =="dataFromTimeSeries" and valuesDict["XYvPolar"] =="polar":
					valuesDict["polarPlotText"] = True
					valuesDict["showBinsS"] = False
				
				if valuesDict["PlotType"] !="dataFromTimeSeries" or valuesDict["XYvPolar"] =="polar":
					valuesDict["showXscale"] = True
					valuesDict["showBinsS"] = False
				else:
					valuesDict["showXscale"] = False

				if valuesDict["XYvPolar"] =="polar":
					valuesDict["showY2scale"] = False
					valuesDict["polarPlotText"] = True
				else:
					valuesDict["showY2scale"] = True
					valuesDict["polarPlotText"] = False

				if valuesDict["ExpertsP"]:
					valuesDict["showRGBBackground"] = True
					valuesDict["showRGBText"] = True
					valuesDict["ExpertsAndPlots"] = True
					valuesDict["showBins"] = True
					valuesDict["showExtraText"] =True

					if  self.gnuORmat == "gnu":
						valuesDict["fontsGNUONOFF"] = True
						valuesDict["fontsMATONOFF"] = False
					else:
						valuesDict["fontsMATONOFF"] = True
						valuesDict["fontsGNUONOFF"] = False
				else:
					valuesDict["fontsGNUONOFF"] = False
					valuesDict["fontsMATONOFF"] = False
					valuesDict["ExpertsAndPlots"] = False
					valuesDict["showBins"] = False
		
				if len(valuesDict["ExtraText"]) >0:
					valuesDict["showExtraText"] =True
			else:
				valuesDict["TimeseriesAndPlots"] = True
				valuesDict["fontsGNUONOFF"] = False
				valuesDict["fontsMATONOFF"] = False
				valuesDict["ExpertsAndPlots"] = False
				valuesDict["showBins"] = False
				valuesDict["showBinsS"] = False
				valuesDict["showRGBBackground"] = False
				valuesDict["showRGBText"] = False
				valuesDict["showXscale"] = False
				valuesDict["showY2scale"] = False
				valuesDict["polarPlotText"] = False
				valuesDict["amPm"] = False
				valuesDict["showExtraText"] =False
				valuesDict["showNotScatter"] =False
				valuesDict["showNotScatterS"] =False
				valuesDict["showNotScatterC"] =False
				valuesDict["showLineShift"] =False


			if valuesDict["DefineLines"]:
				if  valuesDict["ExpertsP"]:
#					valuesDict["showRGBLine"] = True
					if valuesDict["XYvPolar"] =="xy":
						valuesDict["showFunc"] = True
					else:
						valuesDict["showFunc"] = False
					if valuesDict["lineFunc"] =="E" or valuesDict["showFunc"] =="S" or valuesDict["showFunc"] =="C":
						valuesDict["showFunc"] = True
					
					valuesDict["ExpertsAndLines"] = True
					if  valuesDict["lineFunc"] =="E" or valuesDict["lineFunc"] =="S":
						valuesDict["showSmooth"] = False
						valuesDict["showNotScatter"] = False
						valuesDict["showNotScatterS"] = True
					elif valuesDict["lineFunc"] =="C" :
						valuesDict["showSmooth"] = False
						valuesDict["showNotScatter"] = False
						valuesDict["showNotScatterC"] = True
					else:
						valuesDict["showSmooth"] = True
						valuesDict["showNotScatter"] = True
						valuesDict["showNotScatterS"] = True
						valuesDict["showNotScatterC"] = True

					valuesDict["showLineShift"] =True

					if "StraightLine" in  valuesDict and "{}".format(valuesDict["StraightLine"]).upper()=="TRUE" or  valuesDict["selectedLineSourceATEXT"].find("-event") >-1:
						if valuesDict["StraightLine"] :
							valuesDict["showFunc"] = False
							valuesDict["showSmooth"] = False
							valuesDict["showLineShift"] =False
					
					if self.showAB == "SAB":
						valuesDict["DefineLinesASelected"] =True
						valuesDict["DefineLinesANotSelect"] =False
						valuesDict["DefineLinesBSelected"] =True
						valuesDict["DefineLinesBNotSelect"] =False
					if self.showAB == "SA":
						valuesDict["DefineLinesASelected"] =True
						valuesDict["DefineLinesANotSelect"] =False
						valuesDict["DefineLinesBSelected"] =False
						valuesDict["DefineLinesBNotSelect"] =False
					if self.showAB == "NSAB":
						valuesDict["DefineLinesASelected"] =False
						valuesDict["DefineLinesANotSelect"] =True
						valuesDict["DefineLinesBSelected"] =False
						valuesDict["DefineLinesBNotSelect"] =True
					if self.showAB == "NSA":
						valuesDict["DefineLinesASelected"] =False
						valuesDict["DefineLinesANotSelect"] =True
						valuesDict["DefineLinesBSelected"] =False
						valuesDict["DefineLinesBNotSelect"] =False


				else:
					valuesDict["showSmooth"] = False
					valuesDict["ExpertsAndLines"] = False
					valuesDict["DefineLinesBNotSelect"] = False
					valuesDict["DefineLinesBSelected"] = False
					valuesDict["showNotScatter"] = True
					valuesDict["showNotScatterC"] = True
					valuesDict["showNotScatterS"] = True
					if self.showAB == "SAB":
						valuesDict["DefineLinesASelected"] =True
						valuesDict["DefineLinesANotSelect"] =False
					if self.showAB == "SA":
						valuesDict["DefineLinesASelected"] =True
						valuesDict["DefineLinesANotSelect"] =False
					if self.showAB == "NSAB":
						valuesDict["DefineLinesASelected"] =True
						valuesDict["DefineLinesANotSelect"] =True
					if self.showAB == "NSA":
						valuesDict["DefineLinesASelected"] =False
						valuesDict["DefineLinesANotSelect"] =True
					valuesDict["DefineLinesBSelected"] =False
					valuesDict["DefineLinesBNotSelect"] =False
					if str(valuesDict["lineFunc"]) =="E" or str(valuesDict["lineFunc"]) =="S" or str(valuesDict["lineFunc"]) =="C":
						valuesDict["showFunc"] = True
						if self.showAB.find("N")>-1:
							valuesDict["DefineLinesBSelected"] =False
							valuesDict["DefineLinesBNotSelect"] =True
						else:
							valuesDict["DefineLinesBSelected"] =True
							valuesDict["DefineLinesBNotSelect"] =False

					else:
						valuesDict["showFunc"] = False

					
				if valuesDict["XYvPolar"] =="xy":
					valuesDict["leftRight"] = True
				else:
					valuesDict["polarLineText"] = True
					valuesDict["showNotScatter"] = True
					valuesDict["showNotScatterS"] = True
					valuesDict["showNotScatterC"] = True
					valuesDict["textPolarL1"] ="LineA for radius and LineB for angle"
					valuesDict["showFunc"] = False
					valuesDict["leftRight"] = False
					valuesDict["showLineShift"] =False
					if self.showAB == "SAB":
						valuesDict["DefineLinesBSelected"] =True
						valuesDict["DefineLinesBNotSelect"] =False
					if self.showAB == "NSAB":
						valuesDict["DefineLinesBSelected"] =False
						valuesDict["DefineLinesBNotSelect"] =True




			else:
				valuesDict["ExpertsAndLines"] = False
				valuesDict["DefineLinesANotSelect"] = False
				valuesDict["DefineLinesASelected"] = False
				valuesDict["DefineLinesBNotSelect"] = False
				valuesDict["DefineLinesBSelected"] = False
				valuesDict["showRGBLine"] = False
				valuesDict["showFunc"] = False
				valuesDict["leftRight"] = False
				valuesDict["showNotScatter"] = False
				valuesDict["showNotScatterS"] = False
				valuesDict["showLineShift"] =False
				valuesDict["showNotScatterC"] = False
			return valuesDict
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		return valuesDict






	########################################	start / stop matplot vs gnuplot
######################################
	def liteOrPsqlCALLBACK(self, valuesDict, typeId="", targetId=0):

		if  valuesDict["liteOrPsql"] =="psql":
			self.liteOrPsqlString =valuesDict["liteOrPsqlString"]
			if len(self.liteOrPsqlString) < 15 or self.liteOrPsqlString.find("psql") ==-1:
				self.indiLOG.log(40,"postgres psl command string likely wrong, in config \"postgre command string\"\n setting to: /Applications/Postgres.app/Contents/Versions/latest/bin/psql indigo_history -U postgres")
				self.liteOrPsqlString =  "/Applications/Postgres.app/Contents/Versions/latest/bin/psql indigo_history -U postgres"
		else:
			self.liteOrPsqlString =""
		
		return valuesDict

######################################
	def gnuORmatCALLBACK(self, valuesDict, typeId="", targetId=0):

		if  valuesDict["gnuORmat"] =="mat":
			self.gnuORmatSET( "mat")
		else:
			self.gnuORmatSET( "gnu")
		
		return valuesDict

######################################
	def isMATRunning(self):
		oldPID =0
		try:
			pidHandle= self.openEncoding( self.matplotPid , "r")
			oldPID = pidHandle.readline()
			pidHandle.close()
		except:
			if self.decideMyLog("Matplot"): self.indiLOG.log(30,"could not read matplotPID file")
			return False
		try:
			ret, err = self.readPopen("ps -p "+oldPID+" | grep "+oldPID)
			if ret.find("indigoMPplot") < 0: return False
			self.pidMATPLOT = oldPID
			return True
		except:
			self.indiLOG.log(40,"error getting matplot PID ")
			return False
	########################################
	def startMAT(self):
		try:
			self.MPlogfhandle = self.openEncoding(self.MPlogfile,"a")
		except:
			pass
		try:

			data = json.dumps({"indigoDir":self.indigoPath,"logfile":self.PluginLogFile,"prefsDir":self.indigoPreferencesPluginDir,"loglevel":self.decideMyLog("Matplot")})
			cmd = self.pythonPath+ " '"+self.indigoPath+"Plugins/"+self.pluginName+".indigoPlugin/Contents/Server Plugin/indigoMPplot.py' "+json.dumps(data)
			self.pidMATPLOT = "{}".format( subprocess.Popen( cmd, shell=True, stdout=self.MPlogfhandle, stderr=self.MPlogfhandle).pid ) 

			if self.decideMyLog("Matplot") or self.decideMyLog("Plotting"): self.indiLOG.log(30,"(re-)started matplot, PID:{};  cmd:{}".format(self.pidMATPLOT, cmd) )
			pidHandle= self.openEncoding( self.indigoPreferencesPluginDir+"matplot/matplot.pid" , "w")
			pidHandle.write(self.pidMATPLOT)
			pidHandle.close()
			self.plotNow(createNow="",showNow="")
			return True
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			return False

	########################################
	def stopMAT(self):
		if not self.isMATRunning():
			if self.decideMyLog("Matplot"): self.indiLOG.log(30," stop matplot: not active, PID:  {}".format(self.pidMATPLOT))
			return False
		try:
			self.MPlogfhandle.close()
		except:
			if self.decideMyLog("Matplot"): self.indiLOG.log(30,"matplot could not close logfile")
			pass

		try:
			os.kill(int(self.pidMATPLOT), signal.SIGKILL)
			if self.decideMyLog("Matplot"): self.indiLOG.log(30,"matplot stopped PID: {}".format(self.pidMATPLOT))
			return True
		except:
			if self.decideMyLog("Matplot"): self.indiLOG.log(30,"tried to stop matplot PID:  {}".format(self.pidMATPLOT))
			return False
			
	########################################
	def gnuORmatSET(self, setValue):
		if setValue == "gnu":
			if self.isMATRunning():
				if self.decideMyLog("Matplot"): self.indiLOG.log(30,"gnuORmat starting gnuplot, stopping matplot")
				self.stopMAT()
			self.gnuORmat = "gnu"
		else:
			self.gnuORmat = "mat"
			if self.isMATRunning(): return
			self.startMAT()
		return



	########################################	config device section
	
	########################################
	def getLinesForFileOrVariPlot(self,FileOrVariName):				# Select only device/properties that are supported:  numbers, bool, but not props that have "words"
		self.listOfLinesForFileOrVari=[(0,"None")]
		if self.currentPlotType == "dataFromTimeSeries": return -1
		
		if self.currentPlotType =="dataFromFile":
		#format =   x;y1text;y2text\n1,2,3\n4;5;6
			if not os.path.isfile(self.userIndigoPluginDir+"data/"+FileOrVariName):
				self.indiLOG.log(40," getLinesForFileOrVariPlot file does not exist "+ self.userIndigoPluginDir+"data/"+FileOrVariName )
				return -1
			if os.path.getsize(self.userIndigoPluginDir+"data/"+FileOrVariName) ==0:
				self.indiLOG.log(40,"File is empty, needs at least the header line \"#xname;y1 name;y2 Name\". "+ self.userIndigoPluginDir+"data/"+FileOrVariName)
				return -1
			try:
				self.listOfLinesForFileOrVari =[(0,"None")]
				lines =""
				f=self.openEncoding(self.userIndigoPluginDir+"data/"+FileOrVariName,"r")
				buff =f.read()
				f.close()
				
				if buff.find("\r")>-1 or buff.find("\t")>-1:
					f=self.openEncoding(self.userIndigoPluginDir+"data/"+FileOrVariName,"w")
					if buff.find("\t")>-1:
						buff=buff.replace("\t",";")
					if buff.find("\r")>-1:
						buff=buff.replace("\n","")
						lines = buff.split("\r")
					else:
						lines = buff.split("\n")
					for line in lines:
						f.write(line+"\n")
					f.close()
				else:
					lines = buff.split("\n")
				for line in lines:
					xxx= line.strip(" ").split(";")  #  format =   #x;y1text;y2text|1,2,3|4;5;6   --> returns: [#x;y1text;y2text]
					if len(xxx) < 2:
						self.indiLOG.log(40,"File has less than 2 data columns: "+ self.userIndigoPluginDir+"data/"+FileOrVariName )
						return -1
					if xxx[0].find("#") <0:
						self.indiLOG.log(40,"first line in File needs to start with # : " +self.userIndigoPluginDir+"data/"+FileOrVariName  )
						return -1
					xxx[0]= xxx[0].strip("#")
					for ii in range(1,len(xxx)):
						self.listOfLinesForFileOrVari.append((ii,xxx[ii]))
					break
			except  Exception as e:
				self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
				self.indiLOG.log(40," getLinesForFileOrVariPlot  bad data "+ lines )  ## check this out
				return -1
			f.close()
		
		if self.currentPlotType =="dataFromVariable":
			try:
				varidata= indigo.variables[FileOrVariName].value
				xxx= varidata.split("|")[0].split(";")  #  format =   #x;y1text;y2text|1,2,3|4;5;6  --> returns: [#x;y1text;y2text]
				if len(xxx) < 2:
					self.indiLOG.log(40,"Variable has less than 2 data columns: "+FileOrVariName )
					return -1
				if xxx[0].find("#") <0:
					self.indiLOG.log(40,"Variable needs to start with # : "+FileOrVariName )
					return -1

				xxx[0]= xxx[0].strip("#")
				self.listOfLinesForFileOrVari =[(0,"None")]
				for ii in range(1,len(xxx)):
					self.listOfLinesForFileOrVari.append((ii,xxx[ii]))
			except  Exception as e:
				self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
				self.indiLOG.log(40," getLinesForFileOrVariPlot error bad data in variable or variable does not exist  "+ FileOrVariName )
				return -1

		return 0


	########################################
	def preSelectDevices(self):				# Select only device/properties that are supported:  numbers, bool, but not props that have "words"
		self.listOfPreselectedDevices=[]
		self.devIdToTypeandName={}

		for theVar in indigo.variables:
			val = theVar.value
			x = GT.getNumber(val)
			if x !="x":
				try:
					self.listOfPreselectedDevices.append((theVar.id, "Var-{}".format(theVar.name)))
					self.devIdToTypeandName[theVar.id] = "Var-",theVar.name
				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
					self.indiLOG.log(40," listOfPreselectedDevices 2-2 error id, name {}".format(theVar.id) + " {}".format(theVar.name)+" " +  str(self.listOfPreselectedDevices))

		for dev in indigo.devices.iter():
			theStates = dev.states.keys()
			count =0
			for test in theStates:
				try:
					if "Mode" in test or "All" in test or ".ui" in test:
						skip= True
					else:
						skip= False
				except:
					skip=False
				if not skip:	
					val= dev.states[test]
					x = GT.getNumber(val)
					if x!="x" :
						count +=1
			if count>0:													# add to the selection list
				try:
					self.listOfPreselectedDevices.append((dev.id, dev.name))				## give all id's and names of  devices that have at least one of the keys we can track
					self.devIdToTypeandName[dev.id] = "Dev-",dev.name
				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
					self.indiLOG.log(40," listOfPreselectedDevices 2-1 error id, name {}".format(dev.id) + " {}".format(dev.name)+" {}".format(self.listOfPreselectedDevices))

		return

	########################################
	def filterExistingDevice(self,  filter="self", valuesDict=None, typeId="", targetId=0):

		retList = []

		for devNo in self.DEVICE:
			if devNo =="0": continue
			if self.DEVICE[devNo]["Id"] >0:
				retList.append([int(devNo), self.DEVICE["{}".format(devNo)]["devOrVar"]+self.DEVICE[devNo]["Name"]])
		retList = sorted( retList, key=lambda x:(x[1]) )
		retList.append((0,">>>> Pick new Device/Variable"))

		return retList

	########################################
	def pickExistingOrNewDeviceCALLBACK(self, valuesDict=None, typeId="", targetId=0):
	
	
		if typeId =="myFirstPlot":
			valuesDict["selectedDeviceID"]				= valuesDict["selectedDeviceIDMFP"]
			valuesDict["selectedExistingOrNewDevice"]	= valuesDict["selectedExistingOrNewDeviceMFP"]


		self.addNewDevice=False
		devNo = valuesDict["selectedExistingOrNewDevice"]
		selectedDeviceID = valuesDict["selectedDeviceID"]
		if self.decideMyLog("General"): self.indiLOG.log(10,"pickExistingOrNewDeviceCALLBACK    devNo {}".format(devNo) +" old d{}".format(self.oldDevNo) +";;  pickExistingOrNewDeviceCALLBACK-vd {}".format(valuesDict))


		try:
			devNo= int(devNo)
		except:
			devNo=0

		try:

			if devNo ==	self.oldDevNo:
				valuesDict["selectDeviceStatesOK"] = True
			else:
				valuesDict["selectDeviceStatesOK"] = False


			if devNo == 0:
				self.addNewDevice=True
				for devNo in range (1,999):  # find first unused slot
					try:
						if self.DEVICE["{}".format(devNo)]["deviceNumberIsUsed"] >0: continue
						else:
							self.currentDevNo = devNo
							self.DEVICE["{}".format(devNo)]= copy.deepcopy(emptyDEVICE)
							break
					except:
						self.currentDevNo = devNo
						self.DEVICE["{}".format(devNo)]= copy.deepcopy(emptyDEVICE)
						break
				try:
					self.deviceIdNew		= int(selectedDeviceID)
					self.deviceNameNew  	= self.devIdToTypeandName[self.deviceIdNew][1]
					self.deviceDevOrVarNew  = self.devIdToTypeandName[self.deviceIdNew][0]	# "Dev-" or "Var-"
				except:
					self.deviceIdNew		= 0
					self.deviceNameNew  	= 0
					self.deviceDevOrVarNew  = "Dev-"
					pass
				valuesDict["DefineDevicesAndNew"]  = True
				valuesDict["DefineDevicesAndOld"]  = False
				valuesDict["DefineDevicesDummy"]   = False
			

			else:
				self.currentDevNo 		= devNo
				self.deviceIdNew		= self.DEVICE["{}".format(self.currentDevNo)]["Id"]
				self.deviceDevOrVarNew	= self.DEVICE["{}".format(self.currentDevNo)]["devOrVar"]
				if self.DEVICE["{}".format(self.currentDevNo)]["Name"].find("Var") ==-1:
					self.deviceNameNew		= self.DEVICE["{}".format(self.currentDevNo)]["Name"]
				else:
					self.deviceNameNew		= self.DEVICE["{}".format(self.currentDevNo)]["Name"][4:]

				valuesDict["DefineDevicesAndNew"] = False
				valuesDict["DefineDevicesAndOld"] = True
				valuesDict["DefineDevicesDummy"]  = False

			devID= int(self.deviceIdNew)
			if devID !=0:	valuesDict["selectedDeviceID"] = devID
			else:			valuesDict["selectedDeviceID"] = 0


			self.selectableStatesInDevice = self.preSelectStates(self.deviceIdNew)

			valuesDict,two = self.DEVtoValesDict(self.DEVICE["{}".format(self.currentDevNo)],valuesDict)

			if typeId=="defineDataSource":
				valuesDict["text1-2"] = "CONFIRM device/variable first"
			if typeId=="myFirstPlot":
				valuesDict["fistPlotMessageText"] = "CONFIRM device/variable first"

		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		return valuesDict


	########################################
	def filterDevicesThatQualify(self,  filter="",valuesDict="",typeId=""):# Select only device/properties that are supported

		if typeId == "myFirstPlot":
			if self.PLOTlistLast[2] != 0:
				self.currentDevNo = self.PLOTlistLast[2]
			else:
				self.currentDevNo = 0
	
	
		
		if len(self.listOfPreselectedDevices) == 0: 						return [(0,0)]         	# nothing there yet
		retList = self.listOfPreselectedDevices[:]											# make a copy
		if self.currentDevNo ==0: 											return retList			# just making sure
		if not str(self.currentDevNo) in self.DEVICE: 						return retList
		if int(self.DEVICE["{}".format(self.currentDevNo)]["Id"]) == 0:	return retList

		retList.append((0,self.DEVICE["{}".format(self.currentDevNo)]["Name"])) 					# we have a device id already from indigo use that one as first = default pick in list
		
		return retList
	
	########################################
	def pickDevicesThatQualifyCALLBACK(self, valuesDict=None,typeId=""):
		if typeId =="myFirstPlot":
			if valuesDict["selectedDeviceIDMFP"] =="0":  # this is the default device for this plot
				if self.currentDevNo != 0:
					self.currentDeviceId = int(self.DEVICE["{}".format(self.currentDevNo)]["Id"])
					self.deviceDevOrVarNew=self.DEVICE["{}".format(self.currentDevNo)]["devOrVar"]
					stateNo=self.dataColumnToDevice0Prop1Index[self.currentDevNo][1]
					devNo  =self.dataColumnToDevice0Prop1Index[self.currentDevNo][0]
					valuesDict["selDeviceStateMFP"]=self.DEVICE["{}".format(devNo)]["state"][stateNo]
				else:
					valuesDict["fistPlotMessageText"] ="please select device"
				return valuesDict

			## this is not the current device, new setup...
			self.currentDeviceId=int(valuesDict["selectedDeviceIDMFP"])
			valuesDict["selDeviceStateMFP"]="0"
			self.currentDevNo =0

			
			
			try:
				indigo.devices[self.currentDeviceId]
				self.deviceDevOrVarNew="Dev-"
			except:
				try:
					indigo.variables[self.currentDeviceId]
					self.deviceDevOrVarNew="Var-"
				except:
					self.deviceDevOrVarNew=""
					valuesDict["fistPlotMessageText"] ="please select device"

			return valuesDict
		
		
		if self.currentDevNo ==	self.oldDevNo and valuesDict["selectedDeviceID"] == self.deviceIdOld:
			valuesDict["selectDeviceStatesOK"] = True
		else:
			valuesDict["selectDeviceStatesOK"] = False
		return valuesDict
	########################################
	def buttonConfirmDeviceMFPCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		if valuesDict["selectedDeviceIDMFP"] =="0":  # this is the default device for this plot
			if self.currentDevNo != 0:
				self.currentDeviceId = int(self.DEVICE["{}".format(self.currentDevNo)]["Id"])
				self.deviceDevOrVarNew=self.DEVICE["{}".format(self.currentDevNo)]["devOrVar"]
				return valuesDict
			else:
				valuesDict["fistPlotMessageText"] ="please select device"
				return valuesDict

		## this is not the current device, new setup...
		self.currentDeviceId=int(valuesDict["selectedDeviceIDMFP"])
		self.currentDevNo =0

		
		
		try:
			indigo.devices[self.currentDeviceId]
			self.deviceDevOrVarNew="Dev-"
		except:
			try:
				indigo.variables[self.currentDeviceId]
				self.deviceDevOrVarNew="Var-"
			except:
				self.deviceDevOrVarNew=""
				valuesDict["fistPlotMessageText"] ="please select device"

		return valuesDict
	



	########################################
	def buttonConfirmDeviceCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		if typeId == "myFirstPlot":
			valuesDict["selectedDeviceID"]				=valuesDict["selectedDeviceIDMFP"]
			valuesDict["selectedExistingOrNewDevice"]	=valuesDict["selectedDeviceIDMFP"]
			if valuesDict["selectedDeviceID"] =="":
				valuesDict["fistPlotMessageText"] ="please select device"
				return valuesDict
		valuesDict , OK = self.confirmDevice(valuesDict)
		if OK ==0: return valuesDict
		if OK ==1: return valuesDict
		
		valuesDict["selectDeviceStatesOK"] = True
		self.deviceIdOld = self.deviceIdNew
		self.oldselectedExistingOrNewDevice = valuesDict["selectedExistingOrNewDevice"]
		self.oldDevNo = self.currentDevNo
		self.buttonConfirmDevicePressed =True
		valuesDict["text1-1"] = " CONFIRMED/SAVED"		# restore to the old one
		valuesDict["text1-2"] = "  and then confirm !"		# restore to the old one
		
		return valuesDict
	########################################
	def confirmDevice(self, valuesDict):
		newDevice= False
		if self.addNewDevice:
			try:
				if self.decideMyLog("General"): self.indiLOG.log(10," ")
				if self.decideMyLog("General"): self.indiLOG.log(10," confirmDevice 0 adding new device,  currentDevNo:{}".format(self.currentDevNo) +",  selectedDeviceID ="+(valuesDict["selectedDeviceID"]))
				if self.deviceIdNew	!= int(valuesDict["selectedDeviceID"]): newDevice= True
				self.deviceIdNew	= int(valuesDict["selectedDeviceID"])
				if self.decideMyLog("General"): self.indiLOG.log(10," confirmDevice 1 adding new device,  deviceIdNew ={}".format(self.deviceIdNew))
				try:
					self.deviceNameNew      = self.devIdToTypeandName[self.deviceIdNew][1]
					self.deviceDevOrVarNew  = self.devIdToTypeandName[self.deviceIdNew][0]	# "Dev-" or "Var-"
				except  Exception as e:
					self.indiLOG.log(40,"bad input, no device selected (1) Line '%s' has error='%s'" % (sys.exc_info()[2].tb_lineno, e))
					self.indiLOG.log(40," confirmDevice adding new device,  deviceNameNew	error   ="+self.deviceNameNew)
					self.indiLOG.log(40," confirmDevice adding new device,  deviceDevOrVarNew error="+self.deviceDevOrVarNew)
					self.indiLOG.log(40," devIdToTypeandName={}".format(self.devIdToTypeandName))
					valuesDict["text1-1"] = " no device selected"
					return valuesDict, 0
				
				##if self.decideMyLog("General"): self.indiLOG.log(10," self.DEVICE {}".format(self.DEVICE))
				if str(self.currentDevNo) in self.DEVICE:
					if self.decideMyLog("General"): self.indiLOG.log(30," confirmDevice 1.1 already in device {}".format(self.currentDevNo)+" DEVICE{}".format(self.DEVICE["{}".format(self.currentDevNo)]["state"]))
				if newDevice or str(self.currentDevNo) not in self.DEVICE: 
					if newDevice : 
						if self.decideMyLog("General"): self.indiLOG.log(20," confirmDevice 1.1 new ") 
					
					self.DEVICE["{}".format(self.currentDevNo)]         =copy.deepcopy(emptyDEVICE)
				self.DEVICE["{}".format(self.currentDevNo)]["Id"]		= self.deviceIdNew
				self.DEVICE["{}".format(self.currentDevNo)]["devOrVar"]	= self.deviceDevOrVarNew
				if self.deviceNameNew.find("Var") ==-1:
					self.DEVICE["{}".format(self.currentDevNo)]["Name"] = self.deviceNameNew
				else:
					self.DEVICE["{}".format(self.currentDevNo)]["Name"] = self.deviceNameNew[4:]
				if self.decideMyLog("General"): self.indiLOG.log(20,"confirmDevice 1 device DevOrVarNew {}".format(self.DEVICE["{}".format(self.currentDevNo)]["devOrVar"]))
			except  Exception as e:
				self.indiLOG.log(40,"bad input, no device selected (2)  Line '%s' has error='%s'" % (sys.exc_info()[2].tb_lineno, e))
				valuesDict["text1-1"] = " no device selected"
				return valuesDict, 0
		else:
			if valuesDict["DeleteDevice"]:
				self.DeleteDevice(self.currentDevNo,valuesDict)
				valuesDict["text1-1"] = "device deleted"
				valuesDict["DeleteDevice"] = False
				self.currentDevNo =0
				return valuesDict , 1

			self.deviceIdNew		= self.DEVICE["{}".format(self.currentDevNo)]["Id"]
			self.deviceDevOrVarNew	= self.DEVICE["{}".format(self.currentDevNo)]["devOrVar"]
			if self.DEVICE["{}".format(self.currentDevNo)]["Name"].find("Var") ==-1:
				self.deviceNameNew = self.DEVICE["{}".format(self.currentDevNo)]["Name"]
			else:
				self.deviceNameNew = self.DEVICE["{}".format(self.currentDevNo)]["Name"][4:]


		self.selectableStatesInDevice = self.preSelectStates(self.deviceIdNew)
			
		valuesDict, two = self.DEVtoValesDict(self.DEVICE["{}".format(self.currentDevNo)],valuesDict)

		return valuesDict, two


	########################################
	def DEVtoValesDict(self,DEV,valuesDict):

		for stateNo in range(1,noOfStatesPerDeviceG+1):

			if DEV["stateToIndex"][stateNo]> 0:
				valuesDict["selDevicemeasurement{}".format(stateNo)]	= DEV["measurement"][stateNo]
				valuesDict["selDeviceStatea{}".format(stateNo)]		= DEV["state"][stateNo]
				valuesDict["selDeviceoffset{}".format(stateNo)]		= DEV["offset"][stateNo]
				valuesDict["selDevicemultiplier{}".format(stateNo)]	= DEV["multiplier"][stateNo]
				valuesDict["selDeviceminValue{}".format(stateNo)]	= DEV["minValue"][stateNo]
				valuesDict["selDevicemaxValue{}".format(stateNo)]	= DEV["maxValue"][stateNo]
				valuesDict["fillGaps{}".format(stateNo)]				= DEV["fillGaps"][stateNo]
				valuesDict["nickName{}".format(stateNo)]				= DEV["nickName"][stateNo]
				
				if DEV["measurement"][stateNo].find("Consumption") :
					if str(DEV["resetType"][stateNo]).find("Period")>-1:
						if str(DEV["resetType"][stateNo]).find("NoCost")>-1:	VDP="PeriodNoCost"
						else:													VDP="Period"
						vdReturn=""
						try:
							RTP = DEV["resetType"][stateNo][VDP]
						except:
							self.indiLOG.log(40,"error with {}".format(DEV["resetType"][stateNo]))
							break
						noOfPeriods = len(RTP)
						for np in range (noOfPeriods):
							vdReturn+=str(RTP[np])[0:4]+"/{}".format(RTP[np])[4:6]+"/{}".format(RTP[np])[6:8]+"/{}".format(RTP[np])[8:10]+"+"
						valuesDict["resetPeriods{}".format(stateNo)] = vdReturn.strip("+")
						valuesDict["resetType{}".format(stateNo)]	= VDP
					else:
						valuesDict["resetType{}".format(stateNo)]	= DEV["resetType"][stateNo]
						valuesDict["resetPeriods{}".format(stateNo)] = "0"
				elif  DEV["measurement"][stateNo]=="integrate":
						valuesDict["resetType{}".format(stateNo)]	= DEV["resetType"][stateNo]
						valuesDict["resetPeriods{}".format(stateNo)] = "0"
				elif  DEV["measurement"][stateNo]=="eventCOUNT":
						valuesDict["resetType{}".format(stateNo)]	= DEV["resetType"][stateNo]
						valuesDict["resetPeriods{}".format(stateNo)] = "0"
				else:
					valuesDict["resetType{}".format(stateNo)]		= "0"
					valuesDict["resetPeriods{}".format(stateNo)] = "0"
			else:
				valuesDict["selDevicemeasurement{}".format(stateNo)]	= "average"
				valuesDict["selDeviceStatea{}".format(stateNo)]		= 0
				valuesDict["selDeviceoffset{}".format(stateNo)]		= copy.deepcopy(emptyDEVICE["offset"][stateNo])
				valuesDict["selDevicemultiplier{}".format(stateNo)]	= copy.deepcopy(emptyDEVICE["multiplier"][stateNo])
				valuesDict["selDeviceminValue{}".format(stateNo)]	= copy.deepcopy(emptyDEVICE["minValue"][stateNo])
				valuesDict["selDevicemaxValue{}".format(stateNo)]	= copy.deepcopy(emptyDEVICE["maxValue"][stateNo])
				valuesDict["fillGaps{}".format(stateNo)]				= copy.deepcopy(emptyDEVICE["fillGaps"][stateNo])
				valuesDict["resetType{}".format(stateNo)]			= copy.deepcopy(emptyDEVICE["resetType"][stateNo])
				valuesDict["resetPeriods{}".format(stateNo)] 		= "0"
				valuesDict["nickName{}".format(stateNo)]				= ""

		return valuesDict, 2


	########################################
	def preSelectStates(self,devID):				# Select only device/properties that are supported
		if devID ==0: return [(0,0)]
		retList=[]
		
		if self.deviceDevOrVarNew =="Var-":
			retList.append(("value", "value"))

		try:
			if self.deviceDevOrVarNew =="Dev-":
				dev =  indigo.devices[devID]
				theStates = dev.states.keys()
				for test in theStates:
					try:
						if "Mode" in test or "All" in test or ".ui" in test:
							skip= True			# reject fanMode etc
						else:
							skip= False
					except:
						skip=False
					if not skip:	
						val= dev.states[test]
						x = GT.getNumber(val)
						if x !="x" : 	retList.append((test, self.tryNiceState(test)))
		except  Exception as e:
			self.indiLOG.log(40,"Line '{}' has error='{}'".format(sys.exc_info()[2].tb_lineno, e))

		if self.decideMyLog("General"): self.indiLOG.log(10,"preSelectStates   devID: {}".format(devID)+"; deviceDevOrVarNew: {}".format(self.deviceDevOrVarNew) +" retList: {}".format(retList) )

		return retList

	########################################
	def tryNiceState (self, inState):
		try:
			return  stateNiceWords[inState]		# replace property with nice list if available
		except:
			return inState

	########################################
	def filterselDeviceStates1 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,1)
	def filterselDeviceStates2 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,2)
	def filterselDeviceStates3 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,3)
	def filterselDeviceStates4 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,4)
	def filterselDeviceStates5 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,5)
	def filterselDeviceStates6 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,6)
	def filterselDeviceStates7 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,7)
	def filterselDeviceStates8 (self, filter="",  valuesDict=None,typeId=""):
		return self.filterDeviceStatesAll(valuesDict,8)

	########################################
	def filterDeviceStatesAll (self, valuesDict, stateNo):
	
		if self.currentDevNo ==0: return [(0,0)]
#		statePreviouslySelected=  self.DEVICE["{}".format(self.currentDevNo)]["state"][stateNo]									# is there a previously selected dev/property, if yes use it

		retList = self.selectableStatesInDevice[:]																		# make a copy for this property
#		if statePreviouslySelected !="None":																			# use the old one if there
#			retList.append( (0,self.tryNiceState(statePreviouslySelected)) )											# make it the fist to show up (the 0)

		return retList



	########################################
	def consumptionTypeCALLBACK(self,  valuesDict=None):
		self.consumptionPeriodCALLBACK(valuesDict)
		return valuesDict
	########################################
	def consumptionPeriodCALLBACK(self,  valuesDict=None):
		periodNo 				= int(valuesDict["consumptionPeriod"])
		if periodNo ==0: return valuesDict

		consumptionType 		= valuesDict["consumptionType"]
		if consumptionType =="0": return valuesDict
		
		consumptionPeriodType 	= valuesDict["consumptionPeriodType"]

		valuesDict["deleteCRate"] = False
		cCD = self.consumptionCostData[consumptionType][periodNo]
		if consumptionPeriodType =="Period":
			tP=str(cCD["Period"])
			tpText=tP[0:4]+"/"+tP[4:6]+"/"+tP[6:8]+"/"+tP[8:10]
			valuesDict["thisPeriod"]= tpText
		else:
			valuesDict["day"]	= str(cCD["day"])
			valuesDict["hour"]	= str(cCD["hour"])
		
		for n in range (noOfCosts):
			valuesDict["consumed{}".format(n)]= str(cCD["consumed"][n])
			valuesDict["cost{}".format(n)]= str(cCD["cost"][n])
		return valuesDict


	########################################
	def checkIfEventData(self):
		self.eventDataPresent = {}
		for devNo in self.DEVICE:
			if devNo == "0": continue
			if self.DEVICE["{}".format(devNo)]["Id"] == 0: continue
			for stateNo in range (1, noOfStatesPerDeviceG+1):
				if self.DEVICE[devNo]["measurement"][stateNo].find("event") > -1:
					self.eventDataPresent["{}".format(self.DEVICE[devNo]["stateToIndex"][stateNo])] = [devNo,stateNo]


	########################################
	def buttonConfirmDeviceStatesCALLBACK(self,  valuesDict=None,typeId=""):								# thsi will store the selected dev/props
		error = 0
		devNo= self.currentDevNo
		valuesDict["DefineDevicesAndNew"]  = False
		valuesDict["DefineDevicesAndOld"]  = False
		valuesDict["selectDeviceStatesOK"] = False
		
		if str(devNo) not in self.DEVICE:
			self.indiLOG.log(30,"buttonConfirmDeviceStatesCALLBACK:  devNo {}".format(devNo)+" not found in  DEVICE" )
			out="defined DEVICE# are:"
			for devNN in self.DEVICE:
				out+= devNN+" - " + self.DEVICE[devNN]["Name"]+";  "
			self.indiLOG.log(30,"buttonConfirmDeviceStatesCALLBACK: devices defined= "+out )
			self.indiLOG.log(30,"buttonConfirmDeviceStatesCALLBACK: make sure you CONFIRM select a DEVICE first" )
			valuesDict["text1-2"] = "E: DEVICE not selected"
			return valuesDict
			
		if self.decideMyLog("General"): self.indiLOG.log(10,"buttonConfirmDeviceStatesCALLBACK 2 devNo:{}".format(devNo)+"  DEVICE..:{}".format(self.DEVICE["{}".format(devNo)]["state"]))

		if self.DEVICE["{}".format(devNo)]["Name"] !="":
			DEV=self.DEVICE["{}".format(devNo)]
			devName=DEV["Name"]
			devOrVar=DEV["devOrVar"]

			for stateNo in range (1, noOfStatesPerDeviceG+1):
				state				= valuesDict["selDeviceStatea{}".format(stateNo)]
				measurement			= valuesDict["selDevicemeasurement{}".format(stateNo)]
				offset				 = float(valuesDict["selDeviceoffset{}".format(stateNo)])
				multiplier			 = float(valuesDict["selDevicemultiplier{}".format(stateNo)])
				minValue			 = float(valuesDict["selDeviceminValue{}".format(stateNo)])
				maxValue			 = float(valuesDict["selDevicemaxValue{}".format(stateNo)])
				fillGaps			 = str(valuesDict["fillGaps{}".format(stateNo)])
				resetPeriods		 = valuesDict["resetPeriods{}".format(stateNo)]
				resetTypeVD			 = valuesDict["resetType{}".format(stateNo)]
				resetType			 = valuesDict["resetType{}".format(stateNo)]
				nickName			 = valuesDict["nickName{}".format(stateNo)][:50]
				
				if measurement =="delete":
					if self.decideMyLog("General"): self.indiLOG.log(30,"buttonConfirmDeviceStatesCALLBACK deleting device/state..:"+DEV["Name"]+ " {}".format(state)+ " {}".format(devNo)+ " {}".format(stateNo))
					self.removePropFromDevice(devNo,stateNo)
					valuesDict["selDeviceStatea{}".format(stateNo)] =""
					valuesDict["selDevicemeasurement{}".format(stateNo)] ="average"
					continue

				if state ==0:      continue																				# if == 0 still empty
				if state =="":     continue																				# if == 0 still empty
				if state =="None": continue																				# if == 0 still empty

				if measurement.find("Consumption")>-1 or measurement== "integrate":
					if str(resetTypeVD)  != "0":  
						if self.decideMyLog("General"): self.indiLOG.log(30," resetTypeVD resetPeriods {}".format(resetTypeVD)+" {}".format(resetPeriods))
					resetType ="0"
					if resetTypeVD=="0" :
						resetPeriods ="0"
					elif measurement== "integrate":
						if resetTypeVD.find("Period") >-1 or resetTypeVD.find("NoCost") ==-1:
							valuesDict["text1-2"]= "chose reset period cost=1 for integrate"
							return valuesDict
						valuesDict["resetPeriods{}".format(stateNo)] ="0000000000"
						resetType =resetTypeVD
					elif resetTypeVD.find("Period") >-1:
						pList=[]
						# parse first into "+"
						if self.decideMyLog("General"): self.indiLOG.log(20," parsing {}".format(resetPeriods))
						parsedPeriods1= resetPeriods.split("+")
						noP =len(parsedPeriods1)
						for np in range (noP):
							parsedPeriods2 = parsedPeriods1[np].split("/")
							ll= len(parsedPeriods2)
							if ll ==4:
								if len(parsedPeriods2[0]) ==2:	parsedPeriods2[0] = "20"+parsedPeriods2[0]
								if len(parsedPeriods2[0]) ==0:	parsedPeriods2[0] =time.strftime("%Y")
								if len(parsedPeriods2[1]) ==0:	parsedPeriods2[1] =time.strftime("%m")
								if len(parsedPeriods2[1]) <2:	parsedPeriods2[1] ="0"+parsedPeriods2[1]
								if len(parsedPeriods2[2]) ==0:	parsedPeriods2[2] ="01"
								if len(parsedPeriods2[2]) <2:	parsedPeriods2[2] ="0"+parsedPeriods2[2]
								if len(parsedPeriods2[3]) ==0:	parsedPeriods2[3] ="01"
								if len(parsedPeriods2[3]) <2:	parsedPeriods2[3] ="0"+parsedPeriods2[3]
							if ll ==3:
								if len(parsedPeriods2[0]) ==2:	parsedPeriods2[0] ="20"+parsedPeriods2[0]
								if len(parsedPeriods2[0]) ==0:	parsedPeriods2[0] =time.strftime("%Y")
								if len(parsedPeriods2[1]) ==0:	parsedPeriods2[1] =time.strftime("%m")
								if len(parsedPeriods2[1]) <2:	parsedPeriods2[1] ="0"+parsedPeriods2[1]
								if len(parsedPeriods2[2]) ==0:	parsedPeriods2[2] ="01"
								if len(parsedPeriods2[2]) <2:	parsedPeriods2[2] ="0"+parsedPeriods2[2]
								parsedPeriods2.append("00")
							if ll ==2:
								if len(parsedPeriods2[0]) ==2:	parsedPeriods2[0] ="20"+parsedPeriods2[0]
								if len(parsedPeriods2[0]) ==0:	parsedPeriods2[0] =time.strftime("%Y")
								if len(parsedPeriods2[1]) ==0:	parsedPeriods2[1] =time.strftime("%m")
								if len(parsedPeriods2[1]) <2:	parsedPeriods2[1] ="01"
								parsedPeriods2.append("01")
								parsedPeriods2.append("00")
							if ll <2 or ll>4:
								valuesDict["la{}".format(stateNo)]= "bad format time for # {}".format(np)+": "+parsedPeriods1[np]
								return valuesDict
							valuesDict["text1-2"]= "enter data then click CONFIRM"
							try:
								for n2 in range(4):
									if int(parsedPeriods2[n2]) >0: continue
							except:
								valuesDict["text1-2"]= "bad date: {}".format(n2)+": "+parsedPeriods1[n2]
								self.indiLOG.log(40," non numerical dates entered {}".format(n2)+": "+parsedPeriods1[n2])
								return valuesDict
							pList.append(parsedPeriods2[0]+parsedPeriods2[1]+parsedPeriods2[2]+parsedPeriods2[3])
						for np in range(1,noP):
							try:
								if int(pList[np]) > int(pList[np-1]): continue
								valuesDict["text1-2"]= "not seq.: {}".format(np-1)+"/{}".format(np)+": "+parsedPeriods1[np-1]+"-"+parsedPeriods1[np]
								self.indiLOG.log(40," time stamps for resetPeriods not in sequence: {}".format(np-1)+"/{}".format(np)+": "+parsedPeriods1[np-1]+"-"+parsedPeriods1[np])
								return valuesDict
							except:
								valuesDict["text1-2"]= "bad date: {}".format(np)+"/{}".format(np)
								self.indiLOG.log(40," bad  dates: {}".format(np)+"/{}".format(np))
								return valuesDict
							
						if self.decideMyLog("General"): self.indiLOG.log(20," pList {}".format(pList))
						valuesDict["resetType{}".format(stateNo)] = resetType
						vdReturn=""
						for np in range (len(pList)):
							vdReturn+=pList[np][0:4]+"/"+pList[np][4:6]+"/"+pList[np][6:8]+"/"+pList[np][8:10]+"+"
						valuesDict["resetPeriods{}".format(stateNo)] = vdReturn.strip("+")
						resetType = {resetTypeVD:pList}
					else:
						valuesDict["resetPeriods{}".format(stateNo)] ="0000000000"
						resetType =resetTypeVD
			
#				## nickname changed?

				valuesDict["nickName{}".format(stateNo)] = self.getNickName(devNo,stateNo,nickNameN=nickName,devNameN=devName, stateN=state, measurementN=measurement,fillGapsN=fillGaps, resetTypeN=resetType)
				DEV["nickName"][stateNo] = valuesDict["nickName{}".format(stateNo)]
				theCol = DEV["stateToIndex"][stateNo]

				## SAME?
				if ( DEV["state"][stateNo] 			== state and
					 DEV["measurement"][stateNo] 	== measurement and
					 DEV["offset"][stateNo] 		== offset and
					 DEV["multiplier"][stateNo] 	== multiplier and
					 DEV["fillGaps"][stateNo] 		== fillGaps and
					 ((str(DEV["resetType"][stateNo])== resetType) or (DEV["resetType"][stateNo] == "0" and (resetType=="" or resetType=="0" ) ) )):
					
					if ( DEV["minValue"][stateNo] 		== minValue and
						 DEV["maxValue"][stateNo] 		== maxValue):
						self.sqlColListStatus[theCol] = 0
						self.sqlHistListStatus[theCol]= 0
						if self.decideMyLog("General"): self.indiLOG.log(20,"same state "+state+ " DEV:{}".format(DEV))
						continue
					DEV["minValue"][stateNo]		= float(valuesDict["selDeviceminValue{}".format(stateNo)])
					DEV["maxValue"][stateNo]		= float(valuesDict["selDevicemaxValue{}".format(stateNo)])
					self.sqlHistListStatus[theCol]=45		# tell sql import to read, dont wait
					self.updateALL=True
					if self.decideMyLog("General"): self.indiLOG.log(20,"same state2  "+state+ " DEV:{}".format(DEV))
					continue  # everything is the same no action neeed
				## NEW?
				elif DEV["state"][stateNo]			== "None":	#new device / state added
					self.addColumnToData()
					DEV["deviceNumberIsUsed"]		=1		# at least one accepcted property
					DEV["state"][stateNo]			= state										# = "property value"
					DEV["measurement"][stateNo]		= measurement									# = "average/sum/count/min/max"
					DEV["stateToIndex"][stateNo]	= self.dataColumnCount								# = "line index"
					DEV["offset"][stateNo]			= float(valuesDict["selDeviceoffset{}".format(stateNo)])
					DEV["multiplier"][stateNo]		= float(valuesDict["selDevicemultiplier{}".format(stateNo)])
					DEV["minValue"][stateNo]		= float(valuesDict["selDeviceminValue{}".format(stateNo)])
					DEV["maxValue"][stateNo]		= float(valuesDict["selDevicemaxValue{}".format(stateNo)])
					DEV["fillGaps"][stateNo]		= str(fillGaps)
					DEV["resetType"][stateNo]		= str(resetType)
					DEV["nickName"][stateNo]		= nickName

					if DEV["measurement"][stateNo].find("Consumption") >-1 or measurement== "integrate":
						self.consumedDuringPeriod["{}".format(self.dataColumnCount)] = copy.deepcopy(emptyconsumedDuringPeriod)
						self.putconsumedDuringPeriod()
						
					self.devicesAdded =1
					self.sqlColListStatus[self.dataColumnCount]=10
					self.sqlHistListStatus[self.dataColumnCount]=50
					self.sqlLastID[self.dataColumnCount]="0"
					self.sqlLastImportedDate[self.dataColumnCount]="201301010101"
					self.listOfSelectedDataColumnsAndDevPropName.append((  self.dataColumnCount,self.getNickName(devNo,stateNo,nickNameN=nickName,devNameN=devName, stateN=state, measurementN=measurement,fillGapsN=fillGaps, resetTypeN=resetType  )))
						
					self.dataColumnToDevice0Prop1Index[self.dataColumnCount]= [int(devNo),int(stateNo)]							# used later by plot/line slection to pick the index
					continue
			
				# MUST BE CHANGED
				else:												# changed..
					if DEV["state"][stateNo]		== state:
						self.sqlColListStatus[theCol]=0			# dont need to generate SQL only refill histogram
						self.sqlHistListStatus[theCol]=45			# read all data, dont wait for sql.done file
						self.updateALL = True
						self.devicesAdded = 1
					else:
						self.sqlColListStatus[theCol]=10			# need to generate SQL
						self.sqlHistListStatus[theCol]=50			# read all data
						self.updateALL = True
						self.devicesAdded = 1
					self.devicesAdded = 1
					DEV["state"][stateNo]			= state
					DEV["measurement"][stateNo]		= measurement									# = "average/sum/count/min/max/...."
					if DEV["measurement"][stateNo].find("Consumption") ==-1:
						if str(theCol) in self.consumedDuringPeriod:
							del self.consumedDuringPeriod["{}".format(theCol)]
					else:
						if not str(theCol) in self.consumedDuringPeriod:
							self.consumedDuringPeriod["{}".format(theCol)] = copy.deepcopy(emptyconsumedDuringPeriod)
							self.putconsumedDuringPeriod()
							
					DEV["offset"][stateNo]			= float(valuesDict["selDeviceoffset{}".format(stateNo)])
					DEV["multiplier"][stateNo]		= float(valuesDict["selDevicemultiplier{}".format(stateNo)])
					DEV["minValue"][stateNo]		= float(valuesDict["selDeviceminValue{}".format(stateNo)])
					DEV["maxValue"][stateNo]		= float(valuesDict["selDevicemaxValue{}".format(stateNo)])
					DEV["fillGaps"][stateNo]		= str(fillGaps)
					DEV["resetType"][stateNo]		= str(resetType)
					continue


		if max(self.sqlColListStatus) >10: self.updateALL= True
		if max(self.sqlHistListStatus) >10: self.updateALL= True
		if error > 0:
			valuesDict["text1-2"] = "..property {}".format(error)+" already used.."		# restore to the old one
		else:
			valuesDict["text1-2"] = "CONFIRMED & SAVED"		# restore to the old one

		if self.devicesAdded == 1 :
			self.devicesAdded =2  # now signal that new data import should start

		valuesDict["selectDeviceStatesOK"] = False
		self.buttonConfirmDevicePressed =False


		self.redoParam()
		if self.devicesAdded >0 or self.updateALL:
			self.newPREFS=True

		return valuesDict

	########################################
	def getNickName(self,devNo,stateNo,devNameN="",nickNameN="", stateN="", measurementN="",fillGapsN="", resetTypeN=""):
		DEV=self.DEVICE["{}".format(devNo)]
		state		=DEV["state"][stateNo]
		if state==	"None": return ""
		devName 	=DEV["Name"]
		if devName=="": return ""
		state		=self.tryNiceState(state)
		measurement =DEV["measurement"][stateNo]
		fillGaps 	=DEV["fillGaps"][stateNo]
		resetType 	=DEV["resetType"][stateNo]
		devOrVar 	=DEV["devOrVar"]
		nickNameO	= DEV["nickName"][stateNo]
		
		ok = 0
		if len(nickNameN)<3: 							ok=1
		else: return nickNameN
		if nickNameO.count("+") > 2: 					ok=2  ## old version change to "-"
		else:
			if len(nickNameO)<3: 						ok=3
			else: return nickNameO
		if measurementN	!= measurement:					ok=4
		if stateN		!= state:						ok=5
		if resetTypeN	!= resetType:					ok=6
		if fillGapsN	!= fillGaps:					ok=7
		if ok==0:
			if len(nickNameN) >2: return nickNameN
			if len(nickNameO) >2: return nickNameO
		
		resetType=str(resetType).replace(" ","").replace("[","").replace("]","").replace("{","").replace("}","")
		if resetType=="0": resetType=""
		if len(resetType)> 0:
			resetType ="-"+resetType[:10]
		
		lenName									=len(devName)
		if state.find("emperat")>-1:			state="Temp"
		if state.find("Setp")>-1:
							state				= "SP"+state[-4:]

		state									= "-"+state[:7]
		lenState								=len(state)
		if measurement.find("Direction")>-1:	measurement= "Dir"+measurement[-6:]
		if measurement.find("elta")>-1:
			if measurement.find("Norm")>-1:
				measurement= "D-NHour"
			else:
				measurement= "Delt"
		if measurement.find("Consum")>-1:
							measurement			= measurement[:5]
		if measurement.find("Setp")>-1:
							measurement			= "SP"+measurement[-3:]
		measurement								= "-"+measurement
		lenMeasurement							=len(measurement)
		
		lenresetType							=len(resetType)
		if str(fillGaps) !="1":
								lenfillGaps 	= 5
								fillGaps		="-NFGap"
		else:
								fillGaps		=""
								lenfillGaps 	= 0
		if devOrVar =="Var-":
								devOrVar		="Var-"
								lenDevVar		=4
								lenState		=0
								state			=""
		else:
								lenDevVar		=0
								devOrVar		=""
		
		totalLen= lenState+lenMeasurement+lenresetType+lenfillGaps+lenDevVar
		leftForName = max(6, 51-totalLen)
		devName=devName[:leftForName]
		stringToShow= devOrVar+devName+state+measurement+resetType+fillGaps

		nickName= (stringToShow.replace(" ","").replace("[","").replace("]","").replace("{","").replace("}",""))[:50]


		return nickName


	########################################
	def buttonConfirmRatesCALLBACK(self,  valuesDict=None):								# thsi will store the selected dev/props
		eDict= valuesDict
		
		consumptionType 			= valuesDict["consumptionType"]			# eConsumption  gConsumption  wConsumption
		if consumptionType =="0":
			self.indiLOG.log(30,"Configuration: no  consumptionType selected")
			return valuesDict
		consumptionPeriodType 	= valuesDict["consumptionPeriodType"]	# WeekDay / Period
		consumptionPeriod 		= int(valuesDict["consumptionPeriod"])	# 1...30
		
		cCDD =self.consumptionCostData[consumptionType]
		cCD = cCDD[consumptionPeriod]
		
		if valuesDict["deleteCRate"]:
			for key in emptyCost:
				for nc in (consumptionPeriod,noOfCostTimePeriods-1):
					cCDD[nc][key]=cCDD[nc+1][key]
				cCDD[noOfCostTimePeriods-1][key] = emptyCost[key]

			valuesDict["day"]	= str(cCD["day"])
			valuesDict["hour"]	= str(cCD["hour"])
			valuesDict["thisPeriod"]= str(cCD["Period"])
			for n in range (noOfCosts):
				valuesDict["consumed{}".format(n)]= str(cCD["consumed"][n])
				valuesDict["cost{}".format(n)]= str(cCD["cost"][n])
			valuesDict["deleteCRate"] = False
			self.newConsumptionParams+=consumptionType+","
			return valuesDict


		if consumptionPeriodType != self.periodTypeForConsumptionType[consumptionType]:
			self.periodTypeForConsumptionType[consumptionType] = consumptionPeriodType
			self.newConsumptionParams+=consumptionType+","

		if consumptionPeriodType == "Period":
			parsedPeriods2 = valuesDict["thisPeriod"].split("/")
			ll= len(parsedPeriods2)
			if ll ==4:
				if len(parsedPeriods2[0]) ==2:	parsedPeriods2[0] = "20"+parsedPeriods2[0]
				if len(parsedPeriods2[0]) ==0:	parsedPeriods2[0] =time.strftime("%Y")
				if len(parsedPeriods2[1]) ==0:	parsedPeriods2[1] =time.strftime("%m")
				if len(parsedPeriods2[1]) <2:	parsedPeriods2[1] ="0"+parsedPeriods2[1]
				if len(parsedPeriods2[2]) ==0:	parsedPeriods2[2] ="01"
				if len(parsedPeriods2[2]) <2:	parsedPeriods2[2] ="0"+parsedPeriods2[2]
				if len(parsedPeriods2[3]) ==0:	parsedPeriods2[3] ="01"
				if len(parsedPeriods2[3]) <2:	parsedPeriods2[3] ="0"+parsedPeriods2[3]
			if ll ==3:
				if len(parsedPeriods2[0]) ==2:	parsedPeriods2[0] ="20"+parsedPeriods2[0]
				if len(parsedPeriods2[0]) ==0:	parsedPeriods2[0] =time.strftime("%Y")
				if len(parsedPeriods2[1]) ==0:	parsedPeriods2[1] =time.strftime("%m")
				if len(parsedPeriods2[1]) <2:	parsedPeriods2[1] ="0"+parsedPeriods2[1]
				if len(parsedPeriods2[2]) ==0:	parsedPeriods2[2] ="01"
				if len(parsedPeriods2[2]) <2:	parsedPeriods2[2] ="0"+parsedPeriods2[2]
				parsedPeriods2.append("00")
			if ll ==2:
				if len(parsedPeriods2[0]) ==2:	parsedPeriods2[0] ="20"+parsedPeriods2[0]
				if len(parsedPeriods2[0]) ==0:	parsedPeriods2[0] =time.strftime("%Y")
				if len(parsedPeriods2[1]) ==0:	parsedPeriods2[1] =time.strftime("%m")
				if len(parsedPeriods2[1]) <2:	parsedPeriods2[1] ="01"
				parsedPeriods2.append("01")
				parsedPeriods2.append("00")
			if len(parsedPeriods2) !=4:
				valuesDict["thisPeriod"]= valuesDict["thisPeriod"]+"/bad time format"
				self.indiLOG.log(40,"bad time format :" +valuesDict["thisPeriod"])
				return valuesDict
			try:
				for n2 in range(4):
					if int(parsedPeriods2[n2]) >0: continue
			except:
				valuesDict["thisPeriod"]=  valuesDict["thisPeriod"]+"/bad time format"
				self.indiLOG.log(40,"bad time format :" +valuesDict["thisPeriod"])
				return valuesDict
			if consumptionPeriod > 2:
				if int(("").join(parsedPeriods2)) < self.consumptionCostData[consumptionType][consumptionPeriod-1]["Period"]:
					self.indiLOG.log(40,"time periods for costing not in sequence :" +("").join(parsedPeriods2)+" last period is: {}".format(self.consumptionCostData[consumptionType][consumptionPeriod-1]["Period"]))
					valuesDict["thisPeriod"]=  valuesDict["thisPeriod"]+"/not in sequence"
					return valuesDict
			
			cCD["Period"]=(("").join(parsedPeriods2))
			valuesDict["thisPeriod"]=parsedPeriods2[0]+"/"+parsedPeriods2[1]+"/"+parsedPeriods2[2]+"/"+parsedPeriods2[3]

		else:
			try:
				hour	= int(valuesDict["hour"])
				day		= int(valuesDict["day"])
			except:
				return valuesDict

			if cCD["day"] 	!= day:	self.newConsumptionParams+=consumptionType+","
			if cCD["hour"] 	!= hour: self.newConsumptionParams+=consumptionType+","
			cCD["day"]	=day
			cCD["hour"]	=hour



		for n in range (noOfCosts):
			try:
				consumed = float(valuesDict["consumed{}".format(n)])
			except:
				consumed = 0.
			try:
				cost= float(valuesDict["cost{}".format(n)])
			except:
				cost = 0.
			
			if cost >0. and n> 0:
				if cCD["cost"][n-1] == 0.:
					self.indiLOG.log(40,"cost of schedule: {}".format(n-1)+" =0; first define cost of schedule {}".format(n-1)+" then schedule {}".format(n))
					return valueaDict


			valuesDict["consumed{}".format(n)] =str(consumed)
			valuesDict["cost{}".format(n)] =str(cost)

			if cCD["consumed"][n] !=consumed or cCD["cost"][n] != cost :
				self.newConsumptionParams+=consumptionType+","
			cCD["consumed"][n] = consumed
			cCD["cost"][n] = cost

		self.periodTypeForConsumptionType[consumptionType]=consumptionPeriodType

		self.getLastConsumptionyCostPeriodBinWithData()
		
		return valuesDict

	########################################	config plot section
	

	########################################
	## called just before editor gets opened, check if existing duplicate or new device/Plot
	def getDeviceConfigUiValues(self, devPluginProps, typeId, devId):

		try:

			if self.decideMyLog("General"): self.indiLOG.log(20,"getDeviceConfigUiValues  start")

			valuesDict = indigo.Dict(devPluginProps)   # Important to initialize default to devPluginProps


			dev = indigo.devices[devId]
			if "ExpertsP" in dev.pluginProps:
				valuesDict["ExpertsP"]				= dev.pluginProps["ExpertsP"]
			else:
				valuesDict["ExpertsP"]				= False
		
			if self.decideMyLog("General"): self.indiLOG.log(20,"getDeviceConfigUiValues... devId:{}".format(devId))

			valuesDict["DefinePlots"]			= True
			valuesDict["DefineLines"]			= False
	#		valuesDict["ExpertsAndPlots"]		= False
	#		valuesDict["ExpertsAndLines"]		= False
			valuesDict["selectLinesOK"]			= False
			valuesDict["DefineLinesANotSelect"]	= True
			valuesDict["DefineLinesASelected"]	= True
			valuesDict["DefineLinesBNotSelect"]	= True
			valuesDict["DefineLinesBSelected"]	= True
			valuesDict["fontsGNUONOFF"]			= False
			valuesDict["fontsMATONOFF"]			= False
			valuesDict["TimeseriesAndPlots"]	= True
			valuesDict["showBins"]				= False
			valuesDict["showBinsS"]				= False
	#		valuesDict=self.setViewOnOff(valuesDict)

			thePlot	= indigo.devices[devId]
			found	=0

			for nPlot in self.PLOT:
				if nPlot == str(devId):
					found =1
					self.PLOT[nPlot]["DeviceNamePlot"] 			= thePlot.name
					valuesDict["DefinePlots"]			= True
					valuesDict["text2-1"]				= "Configuring "+self.PLOT[nPlot]["DeviceNamePlot"]
					valuesDict["text3-1"]				= "first confirm Plot, then select Line"
					self.currentPlotType 				= self.PLOT[nPlot]["PlotType"]
					valuesDict["PlotType"]				= self.currentPlotType
					if self.currentPlotType != "dataFromTimeSeries": self.getLinesForFileOrVariPlot(self.PLOT[nPlot]["PlotFileOrVariName"])
					valuesDict							=self.plotDataTypeCALLBACK(valuesDict)
					break
		
			if found ==0:	# new device, check if brand new or duplicate from old device
				for nPlot in self.PLOT:
					if self.PLOT[nPlot]["DeviceNamePlot"]+" copy" == thePlot.name or self.PLOT[nPlot]["DeviceNamePlot"]+" copy 1" == thePlot.name:
						self.PLOT["{}".format(thePlot.id)] = copy.deepcopy(self.PLOT[nPlot])
						self.PLOT["{}".format(thePlot.id)]["DeviceNamePlot"] = thePlot.name
						valuesDict["text2-1"]				= "Configuring "+self.PLOT[nPlot]["DeviceNamePlot"]
						valuesDict["text3-1"]				= "first confirm Plot, then select Line"
						found =2
						break

			if  found == 0 :	# new device,  brand new
				nPlot=str(thePlot.id)
				self.PLOT[nPlot]					= copy.deepcopy(emptyPlot)
				self.PLOT[nPlot]["DeviceNamePlot"]	= thePlot.name
				self.PLOT[nPlot]["lines"]["0"]		= copy.deepcopy(emptyLine)


			if   self.PLOT[nPlot]["LeftLog"]=="0" :	self.PLOT[nPlot]["LeftLog"] = "linear"
			elif self.PLOT[nPlot]["LeftLog"]=="1" :	self.PLOT[nPlot]["LeftLog"] = "log"
			valuesDict["LeftLog"]			= self.PLOT[nPlot]["LeftLog"]
		
			if   self.PLOT[nPlot]["RightLog"]=="0" :self.PLOT[nPlot]["RightLog"] = "linear"
			elif self.PLOT[nPlot]["RightLog"]=="1" :self.PLOT[nPlot]["RightLog"] = "log"
			valuesDict["RightLog"]			= self.PLOT[nPlot]["RightLog"]
		
			if   self.PLOT[nPlot]["XLog"]=="0" :	self.PLOT[nPlot]["XLog"] = "linear"
			elif self.PLOT[nPlot]["XLog"]=="1" :	self.PLOT[nPlot]["XLog"] = "log"
			valuesDict["XLog"]				= self.PLOT[nPlot]["XLog"]

			valuesDict["PlotType"]			= self.PLOT[nPlot]["PlotType"]
			valuesDict["XYvPolar"]			= self.PLOT[nPlot]["XYvPolar"]

			valuesDict["LeftLabel"]			= self.PLOT[nPlot]["LeftLabel"]
			valuesDict["RightLabel"]		= self.PLOT[nPlot]["RightLabel"]
			valuesDict["XLabel"]			= self.PLOT[nPlot]["XLabel"]
			valuesDict["XLabelPos"]			= self.PLOT[nPlot].get("XLabelPos",emptyPlot["XLabelPos"])
			valuesDict["RXNumbers"]			= self.PLOT[nPlot].get("RXNumbers",emptyPlot["RXNumbers"])

			valuesDict["Grid"]				= self.PLOT[nPlot]["Grid"]
			valuesDict["Border"]			= self.PLOT[nPlot]["Border"]

			valuesDict["LeftScaleRange"]	= self.PLOT[nPlot]["LeftScaleRange"]
			valuesDict["RightScaleRange"]	= self.PLOT[nPlot]["RightScaleRange"]
			valuesDict["XScaleRange"]		= self.PLOT[nPlot]["XScaleRange"]

			valuesDict["LeftScaleTics"]		= self.PLOT[nPlot]["LeftScaleTics"]
			valuesDict["RightScaleTics"]	= self.PLOT[nPlot]["RightScaleTics"]
			valuesDict["XScaleTics"]		= self.PLOT[nPlot]["XScaleTics"]

			valuesDict["LeftScaleDecPoints"]= self.PLOT[nPlot]["LeftScaleDecPoints"]
			valuesDict["RightScaleDecPoints"]= self.PLOT[nPlot]["RightScaleDecPoints"]
			valuesDict["XScaleDecPoints"]	= self.PLOT[nPlot]["XScaleDecPoints"]

			valuesDict["XScaleFormat"]		= self.PLOT[nPlot]["XScaleFormat"]

			valuesDict["resxy0"]			= self.PLOT[nPlot]["resxy"][0]
			valuesDict["resxy1"]			= self.PLOT[nPlot]["resxy"][1]
			valuesDict["Textscale21"]		= self.PLOT[nPlot]["Textscale21"]
			valuesDict["MinuteBinNoOfDays"]	= self.PLOT[nPlot]["MHDDays"][0]
			valuesDict["HourBinNoOfDays"]	= self.PLOT[nPlot]["MHDDays"][1]
			valuesDict["DayBinNoOfDays"]	= self.PLOT[nPlot]["MHDDays"][2]
			valuesDict["MinuteBinShift"]	= self.PLOT[nPlot]["MHDShift"][0]
			valuesDict["HourBinShift"]		= self.PLOT[nPlot]["MHDShift"][1]
			valuesDict["DayBinShift"]		= self.PLOT[nPlot]["MHDShift"][2]

			valuesDict["MinuteXScaleFormat"]= self.PLOT[nPlot]["MHDFormat"][0]
			valuesDict["HourXScaleFormat"]  = self.PLOT[nPlot]["MHDFormat"][1]
			valuesDict["DayXScaleFormat"]   = self.PLOT[nPlot]["MHDFormat"][2]
		


		
		
			valuesDict["Raw"]				= self.PLOT[nPlot]["Raw"]
			valuesDict["drawZeroLine"]		= self.PLOT[nPlot]["drawZeroLine"]
			valuesDict["compressPNGfile"]	= self.PLOT[nPlot]["compressPNGfile"]
			valuesDict["TitleText"]			= self.PLOT[nPlot]["TitleText"]
			valuesDict["ExtraText"]			= self.PLOT[nPlot]["ExtraText"]
			valuesDict["ExtraTextXPos"]		= self.PLOT[nPlot]["ExtraTextXPos"]
			valuesDict["ExtraTextYPos"]		= self.PLOT[nPlot]["ExtraTextYPos"]
			valuesDict["ExtraTextRotate"]	= self.PLOT[nPlot]["ExtraTextRotate"]
			valuesDict["ExtraTextFrontBack"]= self.PLOT[nPlot]["ExtraTextFrontBack"]
			valuesDict["ExtraTextSize"]		= self.PLOT[nPlot]["ExtraTextSize"]
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(self.PLOT[nPlot]["ExtraTextColorRGB"],defColor="#000000")
			valuesDict["ExtraTextColorRGB"]	= rgbINT
			valuesDict["TextSize"]			= self.PLOT[nPlot]["TextSize"]
			valuesDict["TextFont"]			= "0"
			valuesDict["TextMATFont"]		= self.PLOT[nPlot]["TextMATFont"]
			valuesDict["Background"]		= self.PLOT[nPlot]["Background"].upper()
			valuesDict["TransparentBlocks"]	= self.PLOT[nPlot]["TransparentBlocks"]
			valuesDict["ampm"]				= self.PLOT[nPlot]["ampm"]
			valuesDict["boxWidth"]			= self.PLOT[nPlot]["boxWidth"]
			valuesDict["text2-1"]			= "Configuring "+self.PLOT[nPlot]["DeviceNamePlot"]
			valuesDict["text3-1"]			= "first confirm Plot, then select Line"
			valuesDict["TransparentBackground"]	= self.PLOT[nPlot]["TransparentBackground"]


			rgbINT, rgbHEX, error = self.convertoIntAndHexRGB(self.PLOT[nPlot]["Background"],defColor="#FFFFFF")

			valuesDict["BackgroundColorRGB"]		= rgbINT
			if rgbHEX in stdColors:
				valuesDict["Background"]			= self.PLOT[nPlot]["Background"]
				if valuesDict["ExpertsP"]:		valuesDict["showRGBBackground"] 	= True
				else:							valuesDict["showRGBBackground"] 	= False
			else:
				valuesDict["Background"]			= "0"
				valuesDict["showRGBBackground"]		= True


			rgbINT, rgbHEX, error = self.convertoIntAndHexRGB(self.PLOT[nPlot]["TextColor"],defColor="#000000")
			valuesDict["TextColorRGB"] 				= rgbINT
			if rgbHEX in stdColors:
				valuesDict["TextColor"]				= self.PLOT[nPlot]["TextColor"]
				if valuesDict["ExpertsP"]:			valuesDict["showRGBText"] 		= True
				else:								valuesDict["showRGBText"] 		= False
			else:
				valuesDict["TextColor"]				= "0"
				valuesDict["showRGBText"] 			= True


			valuesDict["selectedLineSourceA"]		= 0
			valuesDict["selectedLineSourceB"]		= 0

			valuesDict = self.setViewOnOff( valuesDict)

		except  Exception as e:
			self.indiLOG.log(40,"Line '{}' has error='{}'".format(sys.exc_info()[2].tb_lineno, e))

		return valuesDict


	########################################
	def filterFont(self,  filter="self", valuesDict=None, typeId="", targetId=0):                                                               # this will offer the available dev/properties for this plot/line
		if 	self.gnuORmat =="mat" : return []
		nPlot = "{}".format(targetId)
		defFont = self.PLOT[nPlot]["TextFont"]
		retList = self.fontNames[:]
		retList.append([0,defFont])
		self.fontNames2[0]=defFont
		return retList

	########################################
	def plotBackgroundColorCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		if valuesDict["Background"] !="0":
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["Background"],defColor="#000000")
		else:
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["BackgroundColorRGB"],defColor="#000000")
		valuesDict["BackgroundColorRGB"]= rgbINT
		return valuesDict
		
	########################################
	def plotTextColorRGBCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		if valuesDict["TextColor"] !="0":
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["TextColor"],defColor="#000000")
		else:
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["TextColorRGB"],defColor="#000000")
		valuesDict["TextColorRGB"]= rgbINT
		return valuesDict
	########################################
	def plotLineColorRGBCALLBACK(self, valuesDict=None, typeId="", targetId=0):
		if valuesDict["lineColor"] !="0":
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["lineColor"],defColor="#000000")
		else:
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["lineColorRGB"],defColor="#000000")
		valuesDict["lineColorRGB"]= rgbINT
		return valuesDict



	########################################
	def buttonConfirmPlotCALLBACK(self,  valuesDict=None, typeId="", targetId=0):															# store userinput

		valuesDict, Error, nPlot,fName= self.buttonConfirmPlotCALLBACKcheck(valuesDict, typeId=typeId, targetId=targetId,script=False)															# store userinput

		if Error =="":
			self.PLOT[nPlot]["NumberIsUsed"]	= 1
			valuesDict["text2-1"]               = "CONFIRMED/SAVED Plot: "+fName
			valuesDict["text3-1"]               = "Select Line action"
			valuesDict["lineNumberInList"]      = 1
			valuesDict["selectedExistingOrNewPlot"] =0
			valuesDict["selectLinesOK"]	= True
			valuesDict["DefineLines"]	= True
			valuesDict["DefinePlots"]	= False
			valuesDict= self.setViewOnOff(valuesDict)
			self.PLOT[nPlot]["dataSource"] =emptyPlot["dataSource"] # once edited remove the mini(plot) assignment
		else:
			valuesDict["text2-1"]               = Error+" Plot:"+fName
			valuesDict["text3-1"]               = "finish entering Plot"
			valuesDict["DefinePlots"]	= True
			valuesDict["selectLinesOK"]	= False
			valuesDict["DefineLines"]	= False
			valuesDict= self.setViewOnOff(valuesDict)

		self.waitWithPlotting =True
		self.lineAlreadySelected = False



		return valuesDict
		

	########################################
	def buttonConfirmPlotCALLBACKcheck(self,  valuesDict=None, typeId="", targetId=0,script=False):															# store userinput
		Error = ""
		fName								=indigo.devices[targetId].name
		nPlot								= "{}".format(targetId)

		self.currentPlotType=valuesDict["PlotType"]
		if self.currentPlotType != "dataFromTimeSeries":
			if  self.getLinesForFileOrVariPlot(valuesDict["PlotFileOrVariName"]) ==-1:
				Error= "error: bad Variable or filename "
				return valuesDict, Error,0,""

		self.PLOT[nPlot]["PlotType"] 			= valuesDict["PlotType"]
		self.PLOT[nPlot]["XYvPolar"] 			= valuesDict["XYvPolar"]
		self.PLOT[nPlot]["TextSize"] 			= valuesDict["TextSize"]
		self.PLOT[nPlot]["PlotFileOrVariName"] 	= valuesDict["PlotFileOrVariName"]
		try:
			nfont 									= int(valuesDict["TextFont"])
			fontName = self.fontNames2[nfont]
			if fontName =="System-font": fontName ="0"
			self.PLOT[nPlot]["TextFont"]			= fontName
		except:
			self.PLOT[nPlot]["TextFont"]			= "0"

		self.PLOT[nPlot]["TextMATFont"]			= valuesDict["TextMATFont"]
		self.PLOT[nPlot]["TitleText"] 			= valuesDict["TitleText"]
		self.PLOT[nPlot]["ExtraText"] 			= valuesDict["ExtraText"]
		if "dataSource" in valuesDict:
			self.PLOT[nPlot]["dataSource"] 			= valuesDict["dataSource"]
		else:
			self.PLOT[nPlot]["dataSource"] 			= "interactive"

		if len(self.PLOT[nPlot]["ExtraText"]) >0:
			Pos										= valuesDict["ExtraTextXPos"]
			try:
				Pos = float(Pos)
				if Pos == 0.0: Pos = 0.01
				Pos = str(Pos)
			except:
				Pos = "0.0"
			self.PLOT[nPlot]["ExtraTextXPos"] 		= Pos
			
			Pos										= valuesDict["ExtraTextYPos"]
			try:
				Pos = float(Pos)
				if Pos ==0.0: Pos = 0.01
				Pos = str(Pos)
			except:
				Pos = "0.0"
			self.PLOT[nPlot]["ExtraTextYPos"] 		= Pos
			
			Pos										= valuesDict["ExtraTextRotate"]
			try:
				Pos = float(Pos)
				Pos = str(Pos)
			except:
				Pos = "0.0"
			self.PLOT[nPlot]["ExtraTextRotate"]		= Pos
			
			if valuesDict["ExtraTextFrontBack"]=="back":
				self.PLOT[nPlot]["ExtraTextFrontBack"] = "back"
			else:
				self.PLOT[nPlot]["ExtraTextFrontBack"] = "front"
			
			self.PLOT[nPlot]["ExtraTextSize"] = valuesDict["ExtraTextSize"]

			if not script:
				rgbNew = valuesDict["ExtraTextColorRGB"]
				rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(rgbNew,defColor="#000000")
				self.PLOT[nPlot]["ExtraTextColorRGB"]		= rgbHEX
				valuesDict["ExtraTextColorRGB"]				= rgbINT
			else:
				rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["ExtraTextColorRGB"],defColor="#000000")
				valuesDict["ExtraTextColorRGB"]				= rgbINT
				self.PLOT[nPlot]["ExtraTextColorRGB"]		= rgbHEX
		

		else:
			self.PLOT[nPlot]["ExtraTextXPos"] 		= "0.0"
			self.PLOT[nPlot]["ExtraTextYPos"] 		= "0.0"
			self.PLOT[nPlot]["ExtraTextRotate"] 	= "0.0"
			self.PLOT[nPlot]["ExtraTextFrontBack"] 	= "front"
			self.PLOT[nPlot]["ExtraTextSize"] 		=self.PLOT[nPlot]["TextSize"]
			self.PLOT[nPlot]["ExtraTextColorRGB"]	= "#000000"

		self.PLOT[nPlot]["Grid"]				= valuesDict["Grid"]
		self.PLOT[nPlot]["Border"]				= valuesDict["Border"]

		self.PLOT[nPlot]["LeftLabel"] 			= valuesDict["LeftLabel"]
		self.PLOT[nPlot]["RightLabel"]			= valuesDict["RightLabel"]
		self.PLOT[nPlot]["XLabel"]				= valuesDict["XLabel"]
		self.PLOT[nPlot]["XLabelPos"]			= valuesDict["XLabelPos"]
		self.PLOT[nPlot]["RXNumbers"]			= valuesDict["RXNumbers"]

		self.PLOT[nPlot]["LeftScaleTics"]		= valuesDict["LeftScaleTics"]
		self.PLOT[nPlot]["RightScaleTics"]		= valuesDict["RightScaleTics"]
		self.PLOT[nPlot]["XScaleTics"]			= valuesDict["XScaleTics"]

		self.PLOT[nPlot]["RightScaleDecPoints"]	= valuesDict["RightScaleDecPoints"]
		self.PLOT[nPlot]["LeftScaleDecPoints"]	= valuesDict["LeftScaleDecPoints"]
		self.PLOT[nPlot]["XScaleDecPoints"]		= valuesDict["XScaleDecPoints"]
		test 									= valuesDict["XScaleFormat"]
		if test.find("%Y")>-1 or test.find("%d")>-1 or test.find("%H")>-1:## this is a date format, need a second part to describe the diplay format
			if test.find("+")==-1:
				Error= "error: XFormat: +%x  + sign missing"
			else:
				self.PLOT[nPlot]["XScaleFormat"]		= test
		else:
				self.PLOT[nPlot]["XScaleFormat"]		= test

		self.PLOT[nPlot]["RightLog"] 			= valuesDict["RightLog"]
		self.PLOT[nPlot]["LeftLog"] 			= valuesDict["LeftLog"]
		self.PLOT[nPlot]["XLog"]	 			= valuesDict["XLog"]


		try: 	float(valuesDict["boxWidth"])
		except: valuesDict["boxWidth"]  = "0.5"
		self.PLOT[nPlot]["boxWidth"]			= valuesDict["boxWidth"]
		self.PLOT[nPlot]["ampm"]				= valuesDict["ampm"]
		self.PLOT[nPlot]["Raw"]					= valuesDict["Raw"]
		self.PLOT[nPlot]["drawZeroLine"]		= valuesDict["drawZeroLine"]
		self.PLOT[nPlot]["compressPNGfile"]		= str(valuesDict["compressPNGfile"]).upper()=="TRUE"

		self.PLOT[nPlot]["MHDShift"][2]			= int(valuesDict["DayBinShift"])
		if   self.PLOT[nPlot]["MHDShift"][2] ==-20: self.PLOT[nPlot]["MHDDays"][2] =31
		elif self.PLOT[nPlot]["MHDShift"][2] ==-30: self.PLOT[nPlot]["MHDDays"][2] =92
		elif self.PLOT[nPlot]["MHDShift"][2] ==-40: self.PLOT[nPlot]["MHDDays"][2] =365
		else: 										self.PLOT[nPlot]["MHDDays"][2] =int(valuesDict["DayBinNoOfDays"])
		valuesDict["DayBinNoOfDays"] 			  = self.PLOT[nPlot]["MHDDays"][2]

		self.PLOT[nPlot]["MHDShift"][1]			= int(valuesDict["HourBinShift"])
		if   self.PLOT[nPlot]["MHDShift"][1] ==-10: self.PLOT[nPlot]["MHDDays"][1] =7
		elif self.PLOT[nPlot]["MHDShift"][1] ==-11: self.PLOT[nPlot]["MHDDays"][1] =14
		elif self.PLOT[nPlot]["MHDShift"][1] ==-20: self.PLOT[nPlot]["MHDDays"][1] =31
		elif self.PLOT[nPlot]["MHDShift"][1] ==-30: self.PLOT[nPlot]["MHDDays"][1] =92
		else: 										self.PLOT[nPlot]["MHDDays"][1] =	int(valuesDict["HourBinNoOfDays"])
		valuesDict["HourBinNoOfDays"] 			   = self.PLOT[nPlot]["MHDDays"][1]

		self.PLOT[nPlot]["MHDShift"][0]			= int(valuesDict["MinuteBinShift"])
		if   self.PLOT[nPlot]["MHDShift"][0] ==-10: self.PLOT[nPlot]["MHDDays"][0] =7
		elif self.PLOT[nPlot]["MHDShift"][0] ==-11: self.PLOT[nPlot]["MHDDays"][0] =14
		elif self.PLOT[nPlot]["MHDShift"][0] ==-20: self.PLOT[nPlot]["MHDDays"][0] =31
		else: 										self.PLOT[nPlot]["MHDDays"][0] =int(valuesDict["MinuteBinNoOfDays"])
		valuesDict["MinuteBinNoOfDays"] 		   = self.PLOT[nPlot]["MHDDays"][0]


		self.PLOT[nPlot]["MHDFormat"][0] = valuesDict["MinuteXScaleFormat"] 
		self.PLOT[nPlot]["MHDFormat"][1] = valuesDict["HourXScaleFormat"]  
		self.PLOT[nPlot]["MHDFormat"][2] = valuesDict["DayXScaleFormat"]   




		xx									= valuesDict["LeftScaleRange"]
		if xx.find(":") <1 and len(xx)>0 :
			Error= "error: L-Scale wrong, eg:  0:250"
			valuesDict["LeftScaleRange"] ="0:250"
		else:
			self.PLOT[nPlot]["LeftScaleRange"]	=xx
		xx										= valuesDict["RightScaleRange"]
		if xx.find(":") <1 and len(xx)>0 :
			Error= "error: R-Scale wrong, eg:  0:250"
			valuesDict["RightScaleRange"] ="0:250"
		else:
			self.PLOT[nPlot]["RightScaleRange"]	=xx

		if self.currentPlotType !="dataFromTimeSeries" or self.PLOT[nPlot]["XYvPolar"] =="polar":
			xx									= valuesDict["XScaleRange"]
			if xx.count(":") !=1 and len(xx)>0 :
				Error= "error: X-Scale wrong, eg:  0:250"
				valuesDict["XScaleRange"] ="0:250"
			else:
				self.PLOT[nPlot]["XScaleRange"]	=xx
		

		xx										= valuesDict["resxy0"]
		if xx.count(",") !=1:
			valuesDict["resxy0"]				=""
			self.PLOT[nPlot]["resxy"][0]		=""
		else:
			if xx.find(",") <2 :
				Error= "Resolution -1 wrong, eg: 800,350"
				valuesDict["resxy0"] ="800,350"
				return valuesDict, Error,0,""
			else:
				self.PLOT[nPlot]["resxy"][0]	=xx

		xx										= valuesDict["resxy1"]
		if xx.count(",") !=1:
			valuesDict["resxy1"]				=""
			self.PLOT[nPlot]["resxy"][1]		=""
		else:
			if xx.find(",") <2 :
				Error= "Resolution -2 wrong, eg: 800,350"
				valuesDict["resxy1"] ="800,350"
				return valuesDict, Error,0,""
			else:
				self.PLOT[nPlot]["resxy"][1]	=xx

		
		xx										= GT.getNumber(valuesDict["Textscale21"])
		if xx=="x" :valuesDict["Textscale21"] 		="1.0"
		else: 		self.PLOT[nPlot]["Textscale21"]	=str(xx)


		if not script:
			rgb = valuesDict["Background"]
			if rgb == self.PLOT[nPlot]["Background"]:
				rgb =valuesDict["BackgroundColorRGB"]
			elif rgb == "" or rgb == "None" or rgb == "0": 	rgb		= valuesDict["BackgroundColorRGB"]

			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(rgb,defColor="#FFFFFF")
			self.PLOT[nPlot]["Background"]			= rgbHEX
			valuesDict["BackgroundColorRGB"]		= rgbINT
			valuesDict["Background"]				= rgbHEX
			if not rgbHEX in stdColors: valuesDict["showRGBBackground"] 	= True
		else:
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["Background"],defColor="#FFFFFF")
			valuesDict["Background"]				= rgbHEX
			self.PLOT[nPlot]["Background"]			= rgbHEX

		self.PLOT[nPlot]["TransparentBackground"]= valuesDict["TransparentBackground"]
		
		xxx = valuesDict["TransparentBlocks"]
		try:
			xxx = float(xxx)
			if xxx >1: xxx =1.0
			if xxx <0: xxx =0.0
			xxx=str(xxx)
		except:
			xxx="1.0"
		self.PLOT[nPlot]["TransparentBlocks"]	= xxx

		if not script:
			rgb = valuesDict["TextColor"]
			if rgb == self.PLOT[nPlot]["TextColor"]:
				rgb =valuesDict["TextColorRGB"]
			elif rgb == "" or rgb == "None" or rgb == "0": 	rgb		= valuesDict["TextColorRGB"]

			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(rgb,defColor="#000000")
			self.PLOT[nPlot]["TextColor"]			= rgbHEX
			valuesDict["TextColorRGB"]				= rgbINT
			valuesDict["TextColor"]					= rgbHEX

			if not rgbHEX in stdColors: valuesDict["showRGBText"] 	= True
		else:
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(valuesDict["TextColor"],defColor="#000000")
			valuesDict["TextColor"]					= rgbHEX
			self.PLOT[nPlot]["TextColor"]			= rgbHEX

		return valuesDict, Error,nPlot, fName
		


	########################################
	def convertoIntAndHexRGB(self,value,defColor="#FFFFFF"):


		rgbINT = str(int(defColor[1:3],16))+",{}".format(int(defColor[3:5],16))+",{}".format(int(defColor[5:7],16))
		rgbHEX = defColor
		
		if len(value) <5 :
			return rgbINT,rgbHEX,""

		if value.find("#")>-1:
			if len(value) <7: 		return rgbINT,rgbHEX,"error: enter proper color {}".format(value)
			if value.find(",")>-1: 	return rgbINT,rgbHEX,"error: enter proper color {}".format(value)
			if value.find(".")>-1: 	return rgbINT,rgbHEX,"error: enter proper color {}".format(value)
			rgbHEX= value.upper()
			rgbINT = str(int(value[1:3],16))+",{}".format(int(value[3:5],16))+",{}".format(int(value[5:7],16))
		elif value.count(",") == 2:
			if len(value) >4:  # must be this format 123,222,111 numbers 0<=x<256
				rgbINT= value
				rgb = value.split(",")
				if len(rgb) ==  3  :
					if rgb[0].isdigit and rgb[1].isdigit and rgb[2].isdigit:
						rgb[0]=int(rgb[0]); rgb[1]=int(rgb[1]); rgb[2]=int(rgb[2])
						if rgb[0] <256 and rgb[1] <256 and rgb[2] <256:
							rgbHEX = "#"+self.padzero(str(hex(rgb[0])[2:])) +self.padzero(str(hex(rgb[1])[2:]))+self.padzero(str(hex(rgb[2])[2:])).upper()
						else:
							return rgbINT,rgbHEX,"error: enter propper color {}".format(value)
					else:
						return rgbINT,rgbHEX,"error: enter propper color {}".format(value)
				else:
					return rgbINT,rgbHEX,"error: enter propper color {}".format(value)
			else:
				return rgbINT,rgbHEX,"error: enter propper color {}".format(value)
		else:return rgbINT,rgbHEX,"error: enter propper color {}".format(value)

		return rgbINT,rgbHEX.upper(),""



	########################################
	def filterExistingLine(self,  filter="self", valuesDict=None, typeId="", targetId=-1):
		try:
			if self.decideMyLog("General"): self.indiLOG.log(20,"filterExistingLine targetId {}".format(targetId))


			retList = []
			nPlot = str(targetId)
			for nLine in self.PLOT[nPlot]["lines"]:
				theCol = int(self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"])
				if theCol >0:
					if self.currentPlotType=="dataFromTimeSeries":
						if theCol >= len(self.listOfSelectedDataColumnsAndDevPropName):
							continue
						if self.PLOT[nPlot]["lines"][nLine]["lineKey"] =="":
							retList.append((int(nLine)," -"+self.listOfSelectedDataColumnsAndDevPropName[theCol][1]))
						else:
							retList.append((int(nLine), self.PLOT[nPlot]["lines"][nLine]["lineKey"]+"-"+self.listOfSelectedDataColumnsAndDevPropName[theCol][1]))
					else:
						if theCol > len(self.listOfLinesForFileOrVari):
							self.indiLOG.log(40," please configure Plot correctly variable or file name or lines not correct, theCol, list: {}".format(theCol)+" {}".format(len(self.listOfLinesForFileOrVari))+" {}".format(self.listOfLinesForFileOrVari) )
							self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]=0
							continue
						if self.PLOT[nPlot]["lines"][nLine]["lineKey"] =="":
							retList.append((int(nLine)," -"+self.listOfLinesForFileOrVari[theCol][1]))
						else:
							retList.append((int(nLine), self.PLOT[nPlot]["lines"][nLine]["lineKey"]+"-"+self.listOfLinesForFileOrVari[theCol][1]))
				elif theCol ==-1:
					if self.currentPlotType=="dataFromTimeSeries":
						if self.PLOT[nPlot]["lines"][nLine]["lineKey"] =="":
							retList.append((int(nLine),"-StraightLine"))
						else:
							retList.append((int(nLine), self.PLOT[nPlot]["lines"][nLine]["lineKey"]+"-StraightLine"))
		


			retList.append(("99","Add New Line"))
			if not self.lineAlreadySelected:  retList.append(("0","Select action"))

			if self.decideMyLog("General"): 
				self.indiLOG.log(20,"filterExistingLine retList {}".format(retList))

		except:
			return [(0,0)]
			self.indiLOG.log(30,"filterExistingLine no lines in data ")
		

		return retList


	########################################
	def selectedLineSourceACALLBACK(self,  valuesDict=None, typeId="", targetId=0):			# store user input and set other parameters used later
		if int(valuesDict["selectedLineSourceA"])<0:
			valuesDict["StraightLine"] = True
			self.showAB= "SA"
		else:
			valuesDict["StraightLine"] = False
		return self.setViewOnOff(valuesDict)


	########################################
	def pickExistingOrNewLineCALLBACK(self,  valuesDict=None, typeId="", targetId=0):			# store user input and set other parameters used later
		self.CurrentLineNo	= "0"
		self.addLine		= False
		nPlot				= str(indigo.devices[targetId].id)
		theLine				= valuesDict["selectedExistingOrNewLine"]
		if theLine =="0":
			self.addLine =False
			valuesDict["text3-1"] = "Error, select action "
			return valuesDict
		if theLine =="99":
			self.addLine =True
			iLine = 0
			while True:
				iLine +=1
				nLine=str(iLine)
				try:
					if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]==0:
						self.setLineToDefault(nPlot,nLine)
						break
				except:
					self.setLineToDefault(nPlot,nLine)
					break
		else:
			nLine=theLine


		if self.decideMyLog("General"): self.indiLOG.log(20," pickExistingOrNewLineCALLBACK  nLine nPlot vDictLine"+nLine + " " + nPlot +" {}".format(theLine))


		self.CurrentLineNo					= nLine
		valuesDict["newLine"]				= nLine
		valuesDict["lineFunc"]				= self.PLOT[nPlot]["lines"][nLine]["lineFunc"]
		valuesDict["lineSmooth"]			= self.PLOT[nPlot]["lines"][nLine]["lineSmooth"]
		valuesDict["lineMultiplier"]		= str(self.PLOT[nPlot]["lines"][nLine]["lineMultiplier"])
		valuesDict["lineOffset"]			= str(self.PLOT[nPlot]["lines"][nLine]["lineOffset"])
		rgbINT ,rgbHEX, Error 				= self.convertoIntAndHexRGB(self.PLOT[nPlot]["lines"][nLine]["lineColor"],defColor="#000000")
		valuesDict["lineColor"]				= rgbHEX
		valuesDict["lineColorRGB"]			= rgbINT
		valuesDict["lineType"]				= self.PLOT[nPlot]["lines"][nLine]["lineType"]
		valuesDict["lineWidth"]				= self.PLOT[nPlot]["lines"][nLine]["lineWidth"]
		valuesDict["lineLeftRight"]			= self.PLOT[nPlot]["lines"][nLine]["lineLeftRight"]
		valuesDict["lineKey"]				= self.PLOT[nPlot]["lines"][nLine]["lineKey"]
		valuesDict["lineShift"]				= str(self.PLOT[nPlot]["lines"][nLine]["lineShift"])
		valuesDict["lineNumbersFormat"]		= str(self.PLOT[nPlot]["lines"][nLine]["lineNumbersFormat"])
		valuesDict["lineNumbersOffset"]		= str(self.PLOT[nPlot]["lines"][nLine]["lineNumbersOffset"])
		valuesDict["lineEveryRepeat"]		= str(self.PLOT[nPlot]["lines"][nLine]["lineEveryRepeat"])
		valuesDict["lineFromTo"]		    = str(self.PLOT[nPlot]["lines"][nLine]["lineFromTo"])
		valuesDict["DefineLinesBSelected"]	=False
		valuesDict["DefineLinesBNotSelect"] =False
		valuesDict["DefineLinesASelected"]	=False
		valuesDict["DefineLinesANotSelect"] =True

		if theLine !="99" :  # existing line
			theDefaultColNumber =int(self.PLOT[nPlot]["lines"][self.CurrentLineNo]["lineToColumnIndexA"])					# get the last entry
			if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]>0:
				valuesDict["StraightLine"] = False
				valuesDict["lineOffsetMultHelp"] = "value*mult+offset"
				if self.currentPlotType =="dataFromTimeSeries": 	valuesDict["selectedLineSourceATEXT"]= self.listOfSelectedDataColumnsAndDevPropName[theDefaultColNumber][1]
				else:												valuesDict["selectedLineSourceATEXT"]= self.listOfLinesForFileOrVari[theDefaultColNumber][1]
			elif self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]<0:
				if self.currentPlotType =="dataFromTimeSeries": 	valuesDict["selectedLineSourceATEXT"]= "StraightLine"
				valuesDict["StraightLine"] = True
				valuesDict["lineOffsetMultHelp"] = "offset=leftValue, mult=rightValue"
		
			self.showAB= 	 "SA"


			if  self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]>0:

				theDefaultColNumber =int(self.PLOT[nPlot]["lines"][self.CurrentLineNo]["lineToColumnIndexB"])					# get the last entry
				if theDefaultColNumber >0:
					self.showAB= 	 "SAB"
					if self.currentPlotType =="dataFromTimeSeries":
						valuesDict["selectedLineSourceBTEXT"]	= self.listOfSelectedDataColumnsAndDevPropName[theDefaultColNumber][1]
						valuesDict["selectedLineSourceB"] 		= self.listOfSelectedDataColumnsAndDevPropName[theDefaultColNumber][0]
					else:
						valuesDict["selectedLineSourceBTEXT"]	= self.listOfLinesForFileOrVari[theDefaultColNumber][1]
						valuesDict["selectedLineSourceB"] 		= self.listOfLinesForFileOrVari[theDefaultColNumber][0]
				else:
					self.showAB= 	 "SA"

		else: #new line
			if valuesDict["ExpertsAndLines"]:
				self.showAB= 	 "NSAB"
			else:
				self.showAB= 	 "NSA"

		valuesDict =self.setViewOnOff(valuesDict)

		valuesDict["text3-1"] = "configure Line# {}".format(nLine)
		self.lineAlreadySelected = True

		return valuesDict

	########################################
	def filterSelectedLinesA(self,  filter="self", valuesDict=None, typeId="", targetId=0):                            # this will offer the available dev/properties for this plot/line
		try:
			if self.decideMyLog("General"): self.indiLOG.log(20," filterSelectedLinesA  nline {}".format(self.CurrentLineNo))

			nPlot = str(targetId)
			

			if self.CurrentLineNo=="0":																#  nothing there return empty selection
				retList =[(0,"None")]
				return retList

			try:
				theDefaultColNumber =int(self.PLOT[nPlot]["lines"][self.CurrentLineNo]["lineToColumnIndexA"])					# get the last entry
			except:
				return [(0,"None")]
			if self.decideMyLog("General"): self.indiLOG.log(20," filterSelectedLinesA  nPlot and def line#  "+ nPlot +" {}".format(theDefaultColNumber) )
			if self.decideMyLog("General"): self.indiLOG.log(20," filterSelectedLinesA  currentPlotType "+ self.currentPlotType)
			if theDefaultColNumber >0:																					# if there was a last entry make it the default
				if self.currentPlotType =="dataFromTimeSeries": 			retList= [(0,self.listOfSelectedDataColumnsAndDevPropName[theDefaultColNumber][1])]
				else:
					retList= [(0,self.listOfLinesForFileOrVari[theDefaultColNumber][1])]
					if self.decideMyLog("General"): self.indiLOG.log(20," filterSelectedLinesA  retList self.listOfLinesForFileOrVari {}".format(self.listOfLinesForFileOrVari[theDefaultColNumber][1]))
				
				if self.decideMyLog("General"): self.indiLOG.log(20," filterSelectedLinesA  retList "+  str(retList))
				return retList
			elif theDefaultColNumber <0:
				retList= [(0,"StraightLine")]
				return retList

			if self.currentPlotType =="dataFromTimeSeries":
				retList =  self.listOfSelectedDataColumnsAndDevPropNameSORTED[:]
			else:
				retList = self.listOfLinesForFileOrVari[:]
			if self.decideMyLog("General"): self.indiLOG.log(20," filterSelectedLinesA  retlist {}".format(retList))
		except  Exception as e:
			self.indiLOG.log(40,"filterSelectedLinesA  Line '%s' has error='%s'" % (sys.exc_info()[2].tb_lineno, e))
			return [(0,0)]
		return retList

	########################################
	def filterSelectedLinesB(self,  filter="self", valuesDict=None, typeId="", targetId=0):                            # this will offer the available dev/properties for this plot/line

		try:

			nPlot = str(targetId)

			if  self.CurrentLineNo=="0":																#  nothing there return empty selection
				retList =[(0,"None")]
				return retList

			try:
				theDefaultColNumber =int(self.PLOT[nPlot]["lines"][self.CurrentLineNo]["lineToColumnIndexB"])					# get the last entry
			except:
				return [(0,"None")]
			
			if theDefaultColNumber >0:																					# if there was a last entry make it the default
				if self.currentPlotType =="dataFromTimeSeries": 	retList= [(0,self.listOfSelectedDataColumnsAndDevPropName[theDefaultColNumber][1])]
				else:												retList= [(0,self.listOfLinesForFileOrVari[theDefaultColNumber][1])]
				
				return retList

			if self.currentPlotType =="dataFromTimeSeries":
				retList =  self.listOfSelectedDataColumnsAndDevPropNameSORTED[:]
			else:
				retList = self.listOfLinesForFileOrVari[:]


			if self.decideMyLog("General"): self.indiLOG.log(20," filterSelectedLinesB  retlist {}".format(retList))
			return retList
		except:
			return [(0,"None")]



	########################################
	def lineFuncCALLBACK(self,  valuesDict=None, typeId="", targetId=0):			# store user input and set other parameters used later
		if valuesDict["lineFunc"] =="S" or valuesDict["lineFunc"] =="E" or valuesDict["lineFunc"] =="C": valuesDict["lineType"]= "DOT."
	
		return self.setViewOnOff(valuesDict)

	########################################
	def buttonUpdatePlotCALLBACK(self, valuesDict=None, typeId="", targetId=0):														# store user input
		if not self.indigoInitialized:
			valuesDict["text3-1"] = "no lines defined "		# restore to the old one
			return valuesDict
			
		nPlot = str(targetId)
		self.redoParam()
		xxx = self.waitWithPlotting
		self.waitWithPlotting = False
		plot = self.PLOT[nPlot]["DeviceNamePlot"]
		self.plotNow(createNow=plot,showNow="",ShowOnly="")
		if plot !="" : self.indigoCommand.append("CheckIfPlotOK+++"+plot)
		self.waitWithPlotting = xxx
		return valuesDict

	########################################
	def buttonDrawPlotCALLBACK(self, valuesDict=None, typeId="", targetId=0):														# store user input
		if not self.indigoInitialized:
			valuesDict["text3-1"] = "no lines defined "		# restore to the old one
			return valuesDict
			
		nPlot = str(targetId)
		xxx=self.waitWithPlotting
		self.waitWithPlotting =False
		self.plotNow(createNow="",showNow=self.PLOT[nPlot]["DeviceNamePlot"],ShowOnly="yes")
		self.waitWithPlotting =xxx
		return valuesDict

	########################################
	def doplotNOWCommand(self):

		if self.decideMyLog("Plotting"): self.indiLOG.log(20,"doplotNOWCommand-- {}".format(self.plotNOWCommand))
		if self.plotNOWCommand[0]=="": return
		xxx=self.waitWithPlotting
		self.waitWithPlotting = False
		if self.plotNOWCommand[0]==	"all plots": 							self.plotNow(createNow="",showNow="")
		else:
			if self.plotNOWCommand[0]!="" and self.plotNOWCommand[1]=="":   self.plotNow(createNow=self.plotNOWCommand[0],showNow="")
			if self.plotNOWCommand[0]!="" and self.plotNOWCommand[1]!="":   self.plotNow(createNow=self.plotNOWCommand[0],showNow=self.plotNOWCommand[1])
		self.plotNOWCommand =["",""]
		self.waitWithPlotting =xxx
		return
	########################################
	def doplotNOWOnlyCommand(self):
		
		if self.plotNOWCommand[0]=="": return
		xxx=self.waitWithPlotting
		self.waitWithPlotting =False
		if self.plotNOWCommand[0]!="" and self.plotNOWCommand[1]!="":   self.plotNow(createNow=self.plotNOWCommand[0],showNow=self.plotNOWCommand[1],ShowOnly="yes")
		self.plotNOWCommand =["",""]
		self.waitWithPlotting =xxx
		return

	########################################
	def buttonConfirmLinePropsCALLBACK(self, valuesDict=None, thetypeId="", thetargetId=0):

		if self.CurrentLineNo =="0":
			valuesDict["text3-1"] = "no Line selected, nothing saved "		# restore to the old one
			return valuesDict

		valuesDict , error = self.buttonConfirmLinePropsCALLBACKcheck(valuesDict, typeId=thetypeId, targetId=thetargetId, script=False)
		valuesDict["text3-1"] = error
		if error =="":
			nPlot	=	str(targetId)
			self.PLOT[nPlot]["dataSource"] =emptyPlot["dataSource"] # once edited remove the mini(plot) assignment

		self.redoParam()
		return valuesDict

	########################################
	def buttonConfirmLinePropsCALLBACKcheck(self, valuesDict=None, typeId="", targetId=0,script=False):

		if self.CurrentLineNo =="0":
			return valuesDict, "error: no Line selected, nothing saved "

		nPlot	=	str(targetId)
		nLine	=	str(self.CurrentLineNo)
		valuesDict["newLine"] = str(nLine)

		if nLine not in self.PLOT[nPlot]["lines"]:
			self.indiLOG.log(30," ConfirmLineProps  line: "+nLine+"   not completely defined, ie line type , please finish selection of parameters ..")
			return valuesDict, "error: line not completely defined"

		if not script:
			if valuesDict["DeleteLine"]:
				del self.PLOT[nPlot]["lines"][nLine]
				valuesDict["DeleteLine"] = False
				valuesDict["DuplicateLine"] = False
				self.CurrentLineNo = "0"
				valuesDict["selectedExistingOrNewLine"]	= 0
				valuesDict["selectedLineSourceATEXT"]	= ""
				valuesDict["selectedLineSourceBTEXT"]	= ""
				valuesDict["lineKey"]					= ""
				valuesDict["lineShift"]					= str(emptyLine["lineShift"])
				return valuesDict, "Line deleted"

			if valuesDict["DuplicateLine"]:
				valuesDict["DuplicateLine"] = False
				iLine = 0
				while True:
					iLine +=1
					try:
						if self.PLOT[nPlot]["lines"]["{}".format(iLine)]["lineToColumnIndexA"]==0:
							break
					except:
						break
				self.CurrentLineNo = iLine
				self.PLOT[nPlot]["lines"]["{}".format(iLine)] = copy.deepcopy(self.PLOT[nPlot]["lines"][nLine])
				valuesDict["newLine"] = str(iLine)
				return valuesDict, "Line duplicated"


		if ( valuesDict["lineWidth"]		=="" ): return valuesDict, "error: LineWidth"
		if ( valuesDict["lineType"]			=="" ): return valuesDict, "error: lineType"
		if ( valuesDict["lineLeftRight"]	=="" ): return valuesDict, "error: lineLeftRight"

		if availableSmoothTypes.find(valuesDict["lineSmooth"])==-1:
			self.indiLOG.log(30," buttonConfirmLinePropsCALLBACKcheck smoothType "+ valuesDict["lineSmooth"] +" wrong, available: "+ availableSmoothTypes)
			self.PLOT[nPlot]["lines"][nLine]["lineSmooth"] = "None"
		else:
			self.PLOT[nPlot]["lines"][nLine]["lineSmooth"]		=	valuesDict["lineSmooth"]
		
		if availableFuncTypes.find(valuesDict["lineFunc"]) ==-1:
			self.indiLOG.log(30,"buttonConfirmLinePropsCALLBACKcheck lineFunc "+ valuesDict["lineFunc"] +" wrong, available: "+availableFuncTypes)
			self.PLOT[nPlot]["lines"][nLine]["lineFunc"] = "None"
		else:
			self.PLOT[nPlot]["lines"][nLine]["lineFunc"]		=	valuesDict["lineFunc"]
		
		try:
			if valuesDict["lineMultiplier"].find("%%v")> -1:
				self.PLOT[nPlot]["lines"][nLine]["lineMultiplier"] = valuesDict["lineMultiplier"]
			else:
				self.PLOT[nPlot]["lines"][nLine]["lineMultiplier"]	=	float(valuesDict["lineMultiplier"])
		except:
			self.PLOT[nPlot]["lines"][nLine]["lineMultiplier"]	=	1.0
			
		try:
			if valuesDict["lineOffset"].find("%%v")> -1:
				self.PLOT[nPlot]["lines"][nLine]["lineOffset"] = valuesDict["lineOffset"]
			else:
				self.PLOT[nPlot]["lines"][nLine]["lineOffset"]		=	float(valuesDict["lineOffset"])
		except:
			self.PLOT[nPlot]["lines"][nLine]["lineOffset"]		=	0.0

		if not script:
			rgb = valuesDict["lineColor"]
			if rgb == self.PLOT[nPlot]["lines"][nLine]["lineColor"]:
				rgb =valuesDict["lineColorRGB"]
			elif rgb == "" or rgb == "None" or rgb == "0": rgb	= valuesDict["lineColorRGB"]

			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(rgb,defColor="#000000")
			self.PLOT[nPlot]["lines"][nLine]["lineColor"]	= rgbHEX
			valuesDict["lineColorRGB"]						= rgbINT
			valuesDict["lineColor"]							= rgbHEX
			if not rgbHEX in stdColors:	valuesDict["showRGBLine"] =True
		else:
			lineColor									=	valuesDict["lineColor"]
			rgbINT ,rgbHEX, Error = self.convertoIntAndHexRGB(lineColor,"#000000")
			valuesDict["lineColor"]             		= rgbHEX
		self.PLOT[nPlot]["lines"][nLine]["lineColor"]	= rgbHEX

		if not script:
			theLineSource												= int(valuesDict["selectedLineSourceA"])
			if theLineSource !=0:
				self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]	= theLineSource

		lineType = valuesDict["lineType"]
		if lineType == "0":		lineType = "LineDashed"
		if lineType == "6":		lineType = "LineSolid"
		if lineType == "solid":	lineType = "Histogram"
		if availableLineTypes.find(lineType) ==-1:
			self.indiLOG.log(30," buttonConfirmLinePropsCALLBACKcheck linetype "+ lineType +" wrong,  available: "+availableLineTypes)
			lineType = "LineSolid"
		self.PLOT[nPlot]["lines"][nLine]["lineType"]			=	lineType

		self.PLOT[nPlot]["lines"][nLine]["lineWidth"]			=	valuesDict["lineWidth"]
		self.PLOT[nPlot]["lines"][nLine]["lineLeftRight"]		=	valuesDict["lineLeftRight"]
		self.PLOT[nPlot]["lines"][nLine]["lineKey"]				=	valuesDict["lineKey"]
		self.PLOT[nPlot]["lines"][nLine]["lineShift"]			=	int(valuesDict["lineShift"])
		self.PLOT[nPlot]["lines"][nLine]["lineEveryRepeat"]		=	str(valuesDict["lineEveryRepeat"])
		self.PLOT[nPlot]["lines"][nLine]["lineFromTo"]	        =	str(valuesDict["lineFromTo"])
			
		if lineType !="Numbers":
			valuesDict["lineNumbersFormat"]							=	""
			valuesDict["lineNumbersOffset"]							=	""
		else:  
			if valuesDict["lineNumbersFormat"] =="":
				valuesDict["lineNumbersFormat"]							=	"%4.1f"
			if valuesDict["lineNumbersOffset"] =="":
				valuesDict["lineNumbersOffset"]							=	"0,0"
		self.PLOT[nPlot]["lines"][nLine]["lineNumbersFormat"]	=	str(valuesDict["lineNumbersFormat"])
		self.PLOT[nPlot]["lines"][nLine]["lineNumbersOffset"]	=	str(valuesDict["lineNumbersOffset"])
		
		if not script:
			if self.PLOT[nPlot]["lines"][nLine]["lineFunc"] =="None" and self.PLOT[nPlot]["XYvPolar"] =="xy": 		valuesDict["selectedLineSourceB"] =0
			theLineSource											=	int(valuesDict["selectedLineSourceB"])
			if theLineSource !=0 and theLineSource !=999999:			self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"]	= theLineSource
			if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"] == 0:
				valuesDict["lineFunc"]				="None"
				self.PLOT[nPlot]["lines"][nLine]["lineFunc"]		="None"

		elif self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"]== 0 and self.PLOT[nPlot]["XYvPolar"] =="xy":	self.PLOT[nPlot]["lines"][nLine]["lineFunc"]		="None"
			

		if not script:
			pass
			valuesDict["selectedExistingOrNewLine"] =0
			valuesDict["newLine"] = str(nLine)

		if not script: 	return valuesDict,"CONFIRMED/SAVED  line# {}".format(self.CurrentLineNo)
		return valuesDict,""
	
	########################################
	def filterZorder(self,  filter="self", valuesDict=None, typeId="", targetId=0):                            # this will offer the available dev/properties for this plot/line
		retList =[]


		nPlot = str(targetId)
		if nPlot =="0": return retList
		lastLine=0
		for nL in self.PLOT[nPlot]["lines"]:
			if nL in self.PLOT[nPlot]["lines"]:
				if int(nL)> lastLine: lastLine =int(nL)

		for iLine in range(1,lastLine+1):
			nLine=str(iLine)
			retList.append((nLine,nLine))
		return retList

	########################################
	def zorderCALLBACK(self, valuesDict=None, typeId="", targetId=0):

		nPlot = str(targetId)
		if nPlot =="0": return valuesDict
		PLT=self.PLOT[nPlot]["lines"]
		if self.decideMyLog("General"): self.indiLOG.log(20,str(PLT))
		
		oldLine=	int(self.CurrentLineNo)
		if oldLine ==0: return valuesDict
		if oldLine ==99: return valuesDict
		
		newLine=	int(valuesDict["newLine"])
		if oldLine==newLine: return valuesDict
		
		nLines=len(PLT)
		if self.decideMyLog("General"): self.indiLOG.log(20," zorderCALLBACK  CurrentLineNo {}".format(self.CurrentLineNo)+" newL:{}".format(newLine)+" nLines:{}".format(len(PLT)))

		if str(oldLine) not in PLT: return valuesDict


		PLT["9999"] =copy.deepcopy(PLT["{}".format(oldLine)])
		
		if oldLine < newLine:
			for nl in range(oldLine,newLine):
				if str(nl+1) in PLT:
					PLT["{}".format(nl)] =copy.deepcopy(PLT["{}".format(nl+1)])
				else:
					try:
						del PLT["{}".format(nl)]
					except:
						if self.decideMyLog("General"): self.indiLOG.log(20," zorderCALLBACK error  nl {}".format(nl)+" newL:{}".format(newLine)+" nLines:{}".format(len(PLT)))
		else:
			for nl in range(oldLine,newLine,-1):
				if str(nl-1) in PLT:
					PLT["{}".format(nl)] =copy.deepcopy(PLT["{}".format(nl-1)])
				else:
					try:
						del PLT["{}".format(nl)]
					except:
						if self.decideMyLog("General"): self.indiLOG.log(20," zorderCALLBACK error  nl {}".format(nl)+" newL:{}".format(newLine)+" nLines:{}".format(len(PLT)))
		
		PLT["{}".format(newLine)] =copy.deepcopy(PLT["9999"])
		del PLT["9999"]
		if self.decideMyLog("General"): self.indiLOG.log(20,str(PLT))

		self.CurrentLineNo =str(newLine)
		
		
		self.redoParam()
		return valuesDict


		########################################	config exit



	########################################
####
	def getPrefsConfigUiValues(self):

		valuesDict = self.pluginPrefs

		self.preSelectDevices()
		
#		try:
#			f =open(self.userIndigoPluginDir+"data/configPrefs","r")
#			valuesDict= f.read()
#			f.close()
#		except:
		valuesDict["expertONOFF"]			= self.expertONOFF
		valuesDict["showExpertParameters"]	= self.showExpertParameters
		valuesDict["indigoPNGdir"]			= self.indigoPNGdir
		valuesDict["gnuORmat"]				= self.gnuORmat
		valuesDict["gnuPlotBin"]			= self.gnuPlotBinary

		valuesDict["samplingPeriod"]		= self.samplingPeriod
		if self.sqlDynamic.find("-resetTo-") >-1:
			self.sqlDynamic = "batch2Days" #set back to default mode
		valuesDict["sqlDynamic"]			= self.sqlDynamic

		valuesDict["noOfDays"]				= json.dumps(self.noOfDays)
		valuesDict["liteOrPsqlString"]		= self.liteOrPsqlString
		valuesDict["liteOrPsql"]			= self.liteOrPsql
		valuesDict["originalCopySQL"]		= self.originalCopySQL
		if self.liteOrPsql	 == "psql":
			if len(self.liteOrPsqlString) < 15 or self.liteOrPsqlString.find("psql") ==-1:
				valuesDict["liteOrPsqlString"] =  "/Applications/Postgres.app/Contents/Versions/latest/bin/psql indigo_history -U postgres"

		for d in ["Restore","General","Initialize","Plotting","Matplot","SQL","Special","all"]:
			if d in self.debugLevel : 	valuesDict["debug"+d]  = True
			else:						valuesDict["debug"+d]  = False

		valuesDict["supressGnuWarnings"]   = self.supressGnuWarnings

		return valuesDict


####
	########################################
	def validatePrefsConfigUi(self,  valuesDict=None):
#		if len(self.removeThisDevice) > 0: self.removeDevice()
		SQLupdatesNeeded								 =0
		
		self.indigoCommand.append("redoParameters")
		self.supressGnuWarnings                     = valuesDict["supressGnuWarnings"]
		self.gnuPlotBinary							= valuesDict["gnuPlotBin"]
		self.liteOrPsqlString						= valuesDict["liteOrPsqlString"]
		self.liteOrPsql								= valuesDict["liteOrPsql"]

		if self.liteOrPsql	 == "psql":
			if len(self.liteOrPsqlString) < 15 or self.liteOrPsqlString.find("psql") ==-1:
				self.indiLOG.log(40,"postgres psl command string likely wrong, in config \"postgre command string\"\n setting to: /Applications/Postgres.app/Contents/Versions/latest/bin/psql indigo_history -U postgres")
				self.liteOrPsqlString =  "/Applications/Postgres.app/Contents/Versions/latest/bin/psql indigo_history -U postgres"
		self.originalCopySQL                        = valuesDict["originalCopySQL"]


		self.debugLevel             = []
		for d in ["Restore","General","Initialize","Plotting","Matplot","SQL","Special","all"]:
			if valuesDict["debug"+d]: self.debugLevel.append(d)

		ndays = json.loads(valuesDict["noOfDays"])
		if ndays != self.noOfDays:
			self.noOfDays	= copy.deepcopy(ndays)
			self.quitNOW = "error validatePrefsConfigUi 1"
			self.indiLOG.log(30," need to restart plugin, data structure has changed to: {} days for the [minute, hour, day] data".format(nDays))
			self.indigoCommand=["quitNow"]
			return True, valuesDict



		if self.indigoPNGdir != valuesDict["indigoPNGdir"]:
			self.indigoPNGdir						= valuesDict["indigoPNGdir"]
			if self.indigoPNGdir[len(self.indigoPNGdir)-1]!="/":
				self.indigoPNGdir+="/"
			valuesDict["indigoPNGdir"] = self.indigoPNGdir
			try:
				ret = os.makedirs(self.indigoPNGdir )  # make the data dir if it does not exist yet
			except:
				pass
			if not os.path.isdir( self.indigoPNGdir ):
				self.indiLOG.log(40," Fatal error could not create indigoplot PNG file Directory ")
				self.quitNOW = "error Fatal error could not create indigoplot PNG file Directory"
				return (False, valuesDict)
			else:
				self.writePlotParameters()


		self.gnuORmat =	valuesDict["gnuORmat"]
		if  valuesDict["gnuORmat"] =="mat":
			self.gnuORmatSET( "mat")
		else:
			self.gnuORmatSET( "gnu")

		self.samplingPeriod						= 	int(valuesDict["samplingPeriod"])
#		self.createAndShowPlots					= 	valuesDict["createAndShowPlots"]

		self.expertONOFF						= valuesDict["expertONOFF"]
		self.showExpertParameters				= valuesDict["showExpertParameters"]



		xxx 										= valuesDict["sqlDynamic"]
		if (	(xxx == "batch"  and (self.sqlDynamic == "online" or self.sqlDynamic == "None"))
			or	(xxx == "online" and (self.sqlDynamic == "batch"  or self.sqlDynamic == "None"))):
			self.sqlColListStatus 				= [10 for i in range(self.dataColumnCount+1)]
			self.sqlLastID  				= ["0" for i in range(self.dataColumnCount+1)]
			self.sqlLastImportedDate	= ["201401010101" for i in range(self.dataColumnCount+1)]
			SQLupdatesNeeded					= 1
		self.sqlDynamic						= xxx
		self.pluginPrefs["sqlDynamic"]		=	self.sqlDynamic

		if len(self.newConsumptionParams)>5 :
			for  theCol  in range (1,self.dataColumnCount+1):																# list of dev/props
				devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
				stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
				measurement 	=	self.DEVICE["{}".format(devNo)]["measurement"][stateNo]
				resetType 		=	self.DEVICE["{}".format(devNo)]["resetType"][stateNo]
				if self.newConsumptionParams.find(measurement) >-1 :
					self.sqlColListStatus[theCol] = 10
					self.sqlHistListStatus[theCol] = 50
					self.devicesAdded = 5
					self.newPREFS			=True

		self.newConsumptionParams =""
		if self.devicesAdded ==5: self.indiLOG.log(30,"New Consumption Cost parameters.. need to updates data from SQL data base to recalculate Energy costs")

		self.indigoInitialized						= True
		valuesDict["text1-1"]						= " "
		valuesDict["selectedExistingOrNewDevice"]	= 0
		valuesDict["selectDeviceStatesOK"]			= False
		valuesDict["ExpertsAndDevices"]				= False
		valuesDict["DefineDevicesAndNew"]			= False
		valuesDict["DefineDevicesAndOld"]			= False
		valuesDict["DefineDevicesDummy"]			= True



		self.putDeviceParametersToFile()
		self.putConsumptionCostData()
		
		if self.devicesAdded >0 :
			self.devicesAdded = 2			# set signal at the end when all paramerts are set
			self.newPREFS			=True
		self.waitWithPlotting	= False
		valuesDict["DeleteDevice"]=False


		return (True, valuesDict)


	########################################
	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		self.newPREFS=False
		self.waitWithPlotting =False


	########################################
	def validateDeviceConfigUi(self,  valuesDict=None, typeId="", targetId=0):
		
		if str(targetId) !="":
			nPlot	=	str(targetId)
			self.PLOT[nPlot]["dataSource"] =emptyPlot["dataSource"] # once edited remove the mini(plot) assignment

		## save the data in indogo:
		devName= indigo.devices[targetId].name
		self.indigoCommand.append("redoParam")
		
		self.waitWithPlotting			= False
		valuesDict["PLOTindigo"]		= json.dumps(self.PLOT["{}".format(targetId)])
		self.justSaved					= True
		self.newPLOTS					= devName
		try:
			self.FnameToLog(devName)
		except:
			pass
		return (True, valuesDict)

	########################################
	def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId="", targetId=0):
		self.newPLOTS=""
		self.waitWithPlotting =False



	########################################	after config redo parameters 		######################################

	#########################################
	def redoParameters(self):
# plot stuff
		self.redoParam()
# data stuff
		self.cleanData()  ## this takes 2.5 seconds
# redu gnu parameters
		if not self.indigoInitialized: self.sleep(5)
		self.indigoInitialized =True

	#########################################
	def redoParam(self):
# plot stuff
		if self.redolineDataSource(calledfrom="redoParam") ==-1:
			if self.redolineDataSource(calledfrom="redoParam") ==-1:
				if self.redolineDataSource(calledfrom="redoParam") ==-1:
					self.redolineDataSource(calledfrom="redoParam")
		self.writePlotParameters()
		self.putDeviceParametersToFile(calledfrom="redoParam ")
		self.setupGNUPlotFiles(calledfrom="redoParam")



	#########################################
	def checkForNewDeviceNames(self):
		anyChange=""
		for devNo in self.DEVICE:
			if self.DEVICE[devNo]["devOrVar"] =="Dev-":
				try:
					dev= indigo.devices[self.DEVICE[devNo]["Id"]]
				except:
					continue
				if self.DEVICE["{}".format(devNo)]["Name"] == dev.name: continue
				anyChange += "\nold: "+self.DEVICE["{}".format(devNo)]["Name"]+";   new: "+dev.name+ ";   #={}".format(devNo)+"; ID: {}".format(self.DEVICE[devNo]["Id"])
				self.DEVICE["{}".format(devNo)]["Name"] = dev.name
			else:
				try:
					var=indigo.variables[self.DEVICE[devNo]["Id"]]
				except:
					pass
				if self.DEVICE["{}".format(devNo)]["Name"] == var.name: continue
				anyChange += "\nold: "+self.DEVICE["{}".format(devNo)]["Name"]+";   new: "+var.name+ ";   #={}".format(devNo)+"; ID: {}".format(self.DEVICE[devNo]["Id"])
				self.DEVICE["{}".format(devNo)]["Name"] = var.name

		if len(anyChange) >0:
			self.putDeviceParametersToFile()
			self.indiLOG.log(30,"device(s) / variable(s) have been renamed: "+anyChange)
	

#### configs  ###################################################################################################


	########################################	recompile the indices 	########################################	########################################
	########################################
	def redolineDataSource(self,calledfrom=""):
		try:
			self.listOfSelectedDataColumnsAndDevPropName =[(0,"None")]
			devName			="x"
			theState		="y"
			theMeasurement	="z"
			if self.decideMyLog("General"): self.indiLOG.log(10," redolineDataSource  called from : "+calledfrom)
			if self.waitWithRedoIndex:
				if self.decideMyLog("General"): self.indiLOG.log(30," redolineDataSource  skipped due to wait-request ")
				return 0

			## add elemenets if they are missing
			if self.dataColumnCount+1 > len(self.sqlLastID):
				for n in range(self.dataColumnCount+1 -len(self.sqlLastID)):
					self.sqlLastID.append("0")
			if self.dataColumnCount+1 > len(self.sqlLastImportedDate):
				for n in range(self.dataColumnCount+1 -len(self.sqlLastImportedDate)):
					self.sqlLastImportedDate.append("201401010101")
			if self.dataColumnCount+1 > len(self.sqlColListStatus):
				for n in range(self.dataColumnCount+1 -len(self.sqlColListStatus)):
					self.sqlColListStatus.append(0)
			if self.dataColumnCount+1 > len(self.sqlColListStatusRedo):
				for n in range(self.dataColumnCount+1 -len(self.sqlColListStatusRedo)):
					self.sqlColListStatusRedo.append(0)
			if self.dataColumnCount+1 > len(self.sqlHistListStatus):
				for n in range(self.dataColumnCount+1 -len(self.sqlHistListStatus)):
					self.sqlHistListStatus.append(0)

			try:
				lN = len(self.timeDataNumbers[0][0])
				if lN != self.dataColumnCount +1+dataOffsetInTimeDataNumbers:
					self.indiLOG.log(40," self.timeDataNumbers wrong number of columns: {}".format(self.dataColumnCount)+"/{}".format(len(self.timeDataNumbers[0][0])-dataOffsetInTimeDataNumbers)+"trying to fix")
					if lN >self.dataColumnCount +1+dataOffsetInTimeDataNumbers:
						for NT in range(noOfTimeTypes):
							for NTB in range (self.noOfTimeBins[NT]):
								del self.timeDataNumbers[NT][NTB][self.dataColumnCount+dataOffsetInTimeDataNumbers]
					if lN < self.dataColumnCount +1+dataOffsetInTimeDataNumbers:
						for NT in range(noOfTimeTypes):
							for NTB in range (self.noOfTimeBins[NT]):
								self.timeDataNumbers[NT][NTB].append("")
			except  Exception as e:
				self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
				self.indiLOG.log(40," self.timeDataNumbers: {}".format(self.dataColumnCount)+"/{}".format(len(self.timeDataNumbers))+"/{}".format(len(self.timeDataNumbers[0]))+"/{}".format(len(self.timeDataNumbers[0][0])))



			for theCol in range(1,self.dataColumnCount+1):
				try:
					devNo= self.dataColumnToDevice0Prop1Index[theCol][0]																			# for shorter typing
					stateNo=self.dataColumnToDevice0Prop1Index[theCol][1]
				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
					self.indiLOG.log(40,"redolineDataSource called from: "+calledfrom+ " -- dataColumnToDevice0Prop1Index {}".format(self.dataColumnToDevice0Prop1Index) +"-- theCol: {}".format(theCol)+" >  dataColumnCount-1: {}".format(self.dataColumnCount-1))
					break
				devID = "--"
				
				## check for basic errors
				if devNo ==0 or stateNo == 0:
					self.indiLOG.log(30,"redolineDataSource devNo or stateNo = 0  for lineDatasourceIndex {}".format(theCol)+" has no device/state associated, deleting "  +str(devNo)+"[{}".format(stateNo)+"] ")
					self.removeColumnFromData(theCol)
					self.removeColumnFromIndexes(theCol)
					self.putDeviceParametersToFile(calledfrom="redolineDataSource")
					return -1
				try:
					if self.DEVICE["{}".format(devNo)]["Name"] == "None":
						self.indiLOG.log(30,"redolineDataSource , lineDatasourceIndex {}".format(theCol)+" and  deviceName number {}".format(devNo)+" is None "  )
						self.removeColumnFromData(theCol)
						self.removeColumnFromIndexes(theCol)
						self.putDeviceParametersToFile(calledfrom="redolineDat+aSource")
						return -1
				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
					self.indiLOG.log(40,"redolineDataSource error, deviceName error bad index devNo / lineDatasourceIndex  {}".format(devNo)+" /  {}".format(theCol))
					self.indiLOG.log(40,"device:{}".format(self.DEVICE))
					self.removeColumnFromData(theCol)
					self.removeColumnFromIndexes(theCol)
					self.putDeviceParametersToFile(calledfrom="redolineDataSource -2")
					return -1  # need to be called again
				
				## we have data, check details
				if devNo > 0 and stateNo > 0:
					self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo]= theCol																	# = "line index"
					theresetType	= self.tryNiceState(self.DEVICE["{}".format(devNo)]["resetType"][stateNo])
					if theresetType =="0" or len(str(theresetType))< 3:	theresetType=""
					else:					theresetType="+{}".format(theresetType).split(":")[0].replace("{u'","").replace(" ","").replace("[","").replace("]","").replace("{","").replace("}","").replace("NoCost","NoC")[:10]
					theState		= self.tryNiceState(self.DEVICE["{}".format(devNo)]["state"][stateNo])
					theMeasurement	= self.DEVICE["{}".format(devNo)]["measurement"][stateNo]
					theName			= self.DEVICE["{}".format(devNo)]["Name"]
					fillGaps		= self.DEVICE["{}".format(devNo)]["fillGaps"][stateNo]
					if 	theMeasurement =="None":
						self.indiLOG.log(30,"redolineDataSource,  for " +theName+"["+ theState+"] {}".format(devID)+"[{}".format(devNo)+"]  index {}".format(theCol) +" theMeasurement is None \n removing device")
						self.removeThisDevice.append(int(devNo))
						self.removeDevice0(reDo=False)
						self.putDeviceParametersToFile(calledfrom="redolineDataSource -2")
						return -1  # need to be called again
					if 	theState 		=="None":
						self.indiLOG.log(30,"redolineDataSource  for " +theName+"["+ theState+"] {}".format(devID)+"[{}".format(devNo)+"]  index {}".format(theCol) +"   theState is None  \n removing device")
						self.removeThisDevice.append(int(devNo))
						self.removeDevice0(reDo=False)
						self.putDeviceParametersToFile(calledfrom="redolineDataSource -2")
						return -1  # need to be called again
					devID			="--"
					if self.DEVICE["{}".format(devNo)]["devOrVar"]=="Dev-":
						try:
							devID			= self.DEVICE["{}".format(devNo)]["Id"]
							devName			= indigo.devices[devID].name
						except:
							self.indiLOG.log(30,"redolineDataSource error,  deviceId[devNo] does not exist in indigo "  +str(devID)+"[{}".format(devNo)+"]  index {}".format(theCol))
							self.removeThisDevice.append(int(devNo))
							self.removeDevice0(reDo=False)
							self.putDeviceParametersToFile(calledfrom="redolineDataSource -2")
							return -1  # need to be called again
					if self.DEVICE["{}".format(devNo)]["devOrVar"]=="Var-":
						try:
							devID			= self.DEVICE["{}".format(devNo)]["Id"]
							devName			= indigo.variables[devID].name
						except:
							self.indiLOG.log(30,"redolineDataSource error,  variableId[devNo] does not exist in indigo  {}".format(devID)+"[{}".format(devNo)+"]  index {}".format(theCol))
							self.removeThisDevice.append(int(devNo))
							self.removeDevice0(reDo=False)
							self.putDeviceParametersToFile(calledfrom="redolineDataSource -2")
							return -1  # need to be called again
							
					## all check ok, rebuild the list of selected devces
					self.listOfSelectedDataColumnsAndDevPropName.append( (  theCol , self.getNickName(devNo,stateNo) ))

			self.listOfSelectedDataColumnsAndDevPropNameSORTED=copy.deepcopy(self.listOfSelectedDataColumnsAndDevPropName)
			self.listOfSelectedDataColumnsAndDevPropNameSORTED.append( (-1, "StraightLine"))
			
			self.listOfSelectedDataColumnsAndDevPropNameSORTED.sort(key=lambda x:x[1])


			## check if DEVICE is ok
			try:
				for devNo in self.DEVICE:
					nonStateUsed = True
					for stateNo in range(1,noOfStatesPerDeviceG+1):
						col = int(self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo])
						if col > 0:
							if col > int(self.dataColumnCount):
								self.indiLOG.log(40,"redolineDataSource: removing  devName  devNo/stateNo/nCols/index: "+self.DEVICE["{}".format(devNo)]["Name"] +"  {}".format(devNo)+"/{}".format(stateNo)+"/{}".format(self.DEVICE["{}".format(devNo)]["stateToIndex"])+"/{}".format(self.dataColumnCount)+" , not in database")
								self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo] =0
								self.removeColumnFromData(col)
								self.removeColumnFromIndexes(col)
								self.putDeviceParametersToFile(calledfrom="redolineDataSource -2")
								self.quitNOW = "error bad index"
								return 0
							if	(int(devNo) != self.dataColumnToDevice0Prop1Index[col][0] or
								 stateNo 	!=self.dataColumnToDevice0Prop1Index[col][1]):
								self.indiLOG.log(40,"redolineDataSource: removing  devName  devNo/stateNo/nCols/index: "+self.DEVICE["{}".format(devNo)]["Name"] +"  {}".format(devNo)+"/{}".format(stateNo)+"/{}".format(col)+"/{}".format(self.DEVICE["{}".format(devNo)]["stateToIndex"])+" not in index: {}".format(self.dataColumnToDevice0Prop1Index[col]))
								self.resetDeviceStateNo(devNo,stateNo)
								self.removeColumnFromData(col)
								self.removeColumnFromIndexes(col)
								self.putDeviceParametersToFile(calledfrom="redolineDataSource -3")
								self.quitNOW = "error bad index"
								return 0
							nonStateUsed = False
						else:
							self.resetDeviceStateNo(devNo,stateNo)
					if nonStateUsed : self.DEVICE["{}".format(devNo)]["deviceNumberIsUsed"]=0
			except  Exception as e:
				self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
				try:
					self.indiLOG.log(40,"devNo {}".format(str(devNo))+"  {}".format(self.DEVICE["{}".format(devNo)]))
				except:
					self.indiLOG.log(40,"devNo {}".format(str(devNo))+"  {}".format(self.DEVICE))
					
	


			# check if values measured are ok
			if self.dataColumnCount >0:
				for TTI in range( noOfTimeTypes):
					if len(self.valuesFromIndigo[TTI]) < self.dataColumnCount+1:
						self.indiLOG.log(30,"redolineDataSource: valuesFromIndigo is too SHORT, ncols/valuesFromIndigo correcting{}".format(self.dataColumnCount)+"/{}".format(len(self.valuesFromIndigo[TTI])))
						for i in range(self.dataColumnCount+1 - len(self.valuesFromIndigo[TTI])):
							self.valuesFromIndigo[TTI].append(emptyValues)
						return -1 # need to redo this
					if len(self.valuesFromIndigo[TTI]) > self.dataColumnCount+1:
						self.indiLOG.log(30,"redolineDataSource: valuesFromIndigo is too LONG,  ncols/valuesFromIndigo .. correcting{}".format(self.dataColumnCount)+"/{}".format(len(self.valuesFromIndigo[TTI][theCol])))
						for theCol in range(len(self.valuesFromIndigo[TTI])-self.dataColumnCount+1):
							del self.valuesFromIndigo[TTI][theCol]
							return -1 # need to redo this



			if self.decideMyLog("General"): self.indiLOG.log(10,"redolineDataSource: listOfSelectedDataColumnsAndDevPropName{}".format(self.listOfSelectedDataColumnsAndDevPropName)+" calledfrom :"+calledfrom)
			self.putDeviceParametersToFile()
			
			changed = False
			
			for nPlot in self.PLOT:
				nLines =[]
				devID = int(nPlot)
				for nLine in self.PLOT[nPlot]["lines"]:
					nLines.append(nLine)

				if self.PLOT[nPlot]["PlotType"] != "dataFromTimeSeries":
					for nLine in nLines:
						lineToColumnIndexA =int(self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"])
						if lineToColumnIndexA==0:
							del self.PLOT[nPlot]["lines"][nLine]
							if self.decideMyLog("General"): self.indiLOG.log(30,"redolineDataSource: plot#: {}".format(nPlot)+"  deleting empty line, index =0")
							changed =True
							dev =indigo.devices[devID]
							props=dev.pluginProps
							props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
							dev.replacePluginPropsOnServer(props)
							continue
					continue


				for nLine in nLines:

					lineToColumnIndexA =int(self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"])
					DeviceNamePlot=self.PLOT[nPlot]["DeviceNamePlot"]
					theKey = self.PLOT[nPlot]["lines"][nLine]["lineKey"]
					if lineToColumnIndexA <0: continue
					try:
						if lineToColumnIndexA==0:
							del self.PLOT[nPlot]["lines"][nLine]
							if self.decideMyLog("General"): self.indiLOG.log(30,"redolineDataSource: plot " +DeviceNamePlot+" " + theKey+"-"+nLine+" deleting empty line, index =0")
							changed =True
							dev =indigo.devices[devID]
							props=dev.pluginProps
							props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
							dev.replacePluginPropsOnServer(props)
							continue
						if lineToColumnIndexA>0:
							devNo =self.dataColumnToDevice0Prop1Index[lineToColumnIndexA][0]
					except:
						del self.PLOT[nPlot]["lines"][nLine]
						self.indiLOG.log(30,"redolineDataSource: devNo not exist deleting plot/line")
						changed =True
						dev =indigo.devices[devID]
						props=dev.pluginProps
						props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
						dev.replacePluginPropsOnServer(props)
						continue
					try:
						lineToColumnIndexB =self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"]
						if lineToColumnIndexB>0:
							devNoB =self.dataColumnToDevice0Prop1Index[lineToColumnIndexB][0]
					except:
						self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"]=0
						self.indiLOG.log(30,"redolineDataSource: devNo not exist deleting plot/lineB: {}".format(nLine))
						changed =True
						dev =indigo.devices[devID]
						props=dev.pluginProps
						props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
						dev.replacePluginPropsOnServer(props)
						continue
					if devNo ==0:
						del self.PLOT[nPlot]["lines"][nLine]
						self.indiLOG.log(30,"redolineDataSource:  devices not completely defined,... devNo=0 deleting plot/line")
						changed =True
						dev =indigo.devices[devID]
						props=dev.pluginProps
						props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
						dev.replacePluginPropsOnServer(props)
						continue
					if not(str(devNo) in self.DEVICE):
						del self.PLOT[nPlot]["lines"][nLine]
						self.indiLOG.log(30,"redolineDataSource: devNo not in DEVICE deleting plot/line")
						changed =True
						dev =indigo.devices[devID]
						props=dev.pluginProps
						props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
						dev.replacePluginPropsOnServer(props)
						continue
					found =0
					stateNo =self.dataColumnToDevice0Prop1Index[lineToColumnIndexA][1]
					for nprops in range(1,noOfStatesPerDeviceG+1):
						if stateNo == nprops:
							found =1
							break
					if found ==0:
						changed =True
						self.indiLOG.log(30,"redolineDataSource: stateNo not found deleting plot " +self.PLOT[nPlot]["DeviceNamePlot"] +"  line#{}".format(nLine) )
						del self.PLOT[nPlot]["lines"][nLine]
						dev =indigo.devices[devID]
						props=dev.pluginProps
						props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
						dev.replacePluginPropsOnServer(props)


			if changed:
				self.writePlotParameters()
	
			# check consumption data
			for n in availConsumptionTypes:
				for i in range(noOfCostTimePeriods+1):
					if "hour" not in self.consumptionCostData[n][i]: self.consumptionCostData[n][i]["hour"]=0
	
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		
		return 0

	########################################	remove data , device propsdata columns, plotline	########################################	########################################
	def resetDeviceStateNo(self,devNo,stateNo):
			DEV= self.DEVICE["{}".format(devNo)]
			DEV["state"][stateNo]		=copy.deepcopy(emptyDEVICE["state"][stateNo])
			DEV["measurement"][stateNo] =copy.deepcopy(emptyDEVICE["measurement"][stateNo])
			DEV["fillGaps"][stateNo] 	=copy.deepcopy(emptyDEVICE["fillGaps"][stateNo])
			DEV["minValue"][stateNo] 	=copy.deepcopy(emptyDEVICE["minValue"][stateNo])
			DEV["maxValue"][stateNo] 	=copy.deepcopy(emptyDEVICE["maxValue"][stateNo])
			DEV["offset"][stateNo] 		=copy.deepcopy(emptyDEVICE["offset"][stateNo])
			DEV["multiplier"][stateNo] 	=copy.deepcopy(emptyDEVICE["multiplier"][stateNo])
			DEV["resetType"][stateNo] 	=copy.deepcopy(emptyDEVICE["resetType"][stateNo])


	########################################
	def DeleteDevice(self,devNo,valuesDict):
		self.removeThisDevice.append(int(devNo))
		self.removeDevice()
		valuesDict["text1-1"] = " deleted"
		return valuesDict

	########################################
	def removeDevice(self):

		self.removeDevice0(reDo=False)
		self.redoParameters()
		self.putDeviceParametersToFile()

	########################################
	def removeDevice0(self,reDo=True):
		if len(self.removeThisDevice)==0: return

		self.indigoCommand.append("PauseDataCollection")
		if self.decideMyLog("General"): self.indiLOG.log(30,"removeDevice #s: "  + str(self.removeThisDevice))
		self.deviceIdNew		= 0
		self.deviceDevOrVarNew	= "Dev-"
		self.deviceNameNew		= "None"
		
		for idev in range(len(self.removeThisDevice)):
			remDev= int(self.removeThisDevice[idev])
			if remDev==0: continue
			for stateNo  in range (1, noOfStatesPerDeviceG+1):
				self.removePropFromDevice(remDev,stateNo,writeD=False,reDo=reDo)
			if str(remDev) in self.DEVICE:
				del self.DEVICE["{}".format(remDev)]
		self.putDeviceParametersToFile()
		self.removeThisDevice=[]
		self.indigoCommand.append("ContinueDataCollection")


	######################################## do this last
	def removePropFromDevice(self,devNo,stateNo,writeD=True,reDo=True):
		if int(stateNo)==0: return
		if int(devNo) ==0: return
		if str(devNo) in self.DEVICE:
			columnToRemove = self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo]
			if columnToRemove == 0: return
			if self.decideMyLog("General"): self.indiLOG.log(30, "removePropFromDevice columnToRemove {}".format(columnToRemove))
			self.DEVICE["{}".format(devNo)]["state"][stateNo]="None"
			self.DEVICE["{}".format(devNo)]["stateToIndex"][stateNo]=0
			self.DEVICE["{}".format(devNo)]["measurement"][stateNo]="average"
			self.removeColumnFromData(columnToRemove)
			self.removeColumnFromIndexes(columnToRemove)
		if reDo:
			if self.redolineDataSource(calledfrom="removePropFromDevice") ==-1 :
				if self.redolineDataSource(calledfrom="removePropFromDevice") ==-1:
					if self.redolineDataSource(calledfrom="removePropFromDevice")==-1:
						self.redolineDataSource(calledfrom="removePropFromDevice")  # do it again to clean up
		if writeD: self.putDeviceParametersToFile()

		return

	######################################## do this second to last, fist data, then plotlines then indexes
	def removeColumnFromIndexes(self,columnToRemove):
		if columnToRemove ==0: return
		if self.decideMyLog("General"): self.indiLOG.log(30, "removeColumnFromIndexes col {}".format(columnToRemove))
		if self.decideMyLog("General"): self.indiLOG.log(30, "removeColumnFromIndexes ncols {}".format(len(self.dataColumnToDevice0Prop1Index)-1) )
		if self.decideMyLog("General"): self.indiLOG.log(30, "removeColumnFromIndexes index list {}".format(self.dataColumnToDevice0Prop1Index) )

		plotsToupdates=[]
		for nPlot in self.PLOT:
			anyChange=False
			if self.PLOT[nPlot]["PlotType"] != emptyPlot["PlotType"]: continue
			for iLine in range(1,99):
				nLine = str(iLine)
				if nLine in self.PLOT[nPlot]["lines"]:
					try:
						if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]		==columnToRemove:
							anyChange=True
							del self.PLOT[nPlot]["lines"][nLine]
							continue
						if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"]		> columnToRemove:
							anyChange=True
							self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"] -=1
						if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"]		==columnToRemove:
							anyChange=True
							del self.PLOT[nPlot]["lines"][nLine]
							continue
						if self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"]		> columnToRemove:
							anyChange=True
							self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"] -=1
							continue
					except  Exception as e:
						self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
						self.indiLOG.log(40,nLine+": {}".format(self.PLOT[nPlot]["lines"][nLine]))
				if anyChange: plotsToupdates.append(nPlot)
		for devNo in self.DEVICE:
			for stateNo in range(1,noOfStatesPerDeviceG+1):
				if self.DEVICE[devNo]["stateToIndex"][stateNo] > columnToRemove:
					self.DEVICE[devNo]["stateToIndex"][stateNo] -=1


		if len(self.listOfSelectedDataColumnsAndDevPropName) > columnToRemove:
			del self.listOfSelectedDataColumnsAndDevPropName[columnToRemove]
		del self.dataColumnToDevice0Prop1Index[columnToRemove]
		del self.sqlLastID[columnToRemove]
		del self.sqlLastImportedDate[columnToRemove]

		if str(columnToRemove) in self.consumedDuringPeriod:
			del self.consumedDuringPeriod["{}".format(columnToRemove)]
		for theCol in range(columnToRemove, self.dataColumnCount):
				if str(theCol+1) in self.consumedDuringPeriod:
					self.consumedDuringPeriod["{}".format(theCol)] = copy.deepcopy(self.consumedDuringPeriod["{}".format(theCol+1)])
					del self.consumedDuringPeriod["{}".format(theCol+1)]

		self.dataColumnCount -=1

		for nPlot in plotsToupdates:
			devID = int(nPlot)
			try:
				dev =indigo.devices[devID]
				props=dev.pluginProps
				props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
				dev.replacePluginPropsOnServer(props)
			except:
				if self.decideMyLog("General"): self.indiLOG.log(40,"nPlot/deviceID already deleted: " + nPLot)

		self.checkIfEventData()
		

	########################################
	def removeThisPlotFile(self, nPlot):

		try:
			for ss in range(0,2):
				if self.PLOT[nPlot]["PlotType"] =="dataFromTimeSeries":
					for tt in range(0,noOfTimeTypes):
						Fname= "{}gnu/{}-{}-{}.gnu".format(self.userIndigoPluginDir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotTimeNames[tt], self.plotSizeNames[ss])
						ret, err = self.readPopen(" rm '{}'  2>&1 &".format(Fname))
						Fname= "{}gnu/{}-{}-{}.png".format(self.userIndigoPluginDir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotTimeNames[tt], self.plotSizeNames[ss])
						ret, err = self.readPopen(" rm '{}'  2>&1 &".format(Fname))
				else:
					Fname= "{}gnu/{}-{}.gnu".format(self.userIndigoPluginDir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotSizeNames[ss])
					ret, err = self.readPopen(" rm '{}'  2>&1 &".format(Fname))
					Fname= "{}gnu/{}-{}.png".format(self.userIndigoPluginDir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotSizeNames[ss])
					ret, err = self.readPopen(" rm '{}'  2>&1 &".format(Fname))
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.indiLOG.log(40,"... plot files already removed")


	########################################
	def removeThisPlot(self, nPlot):

		self.removeThisPlotFile(nPlot)

		self.CurrentLineNo					= "0"
		try:
			del self.PLOT[nPlot]
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		self.writePlotParameters()
		return
		
	#########################################
	def removeColumnFromData(self,colToRemove):
		self.indiLOG.log(30,"removeColumnFromData colToRemove {}".format(colToRemove) +" from number of columns: {}".format(self.dataColumnCount))
		try:
			for TTI in range(0,noOfTimeTypes):
				for NTB in range (self.noOfTimeBins[TTI]):
					if self.timeDataNumbers[TTI][NTB][0] !=0.0:
						for theCol in range(colToRemove, self.dataColumnCount):
							self.timeDataNumbers[TTI][NTB][theCol+dataOffsetInTimeDataNumbers]  = self.timeDataNumbers[TTI][NTB][theCol+1+dataOffsetInTimeDataNumbers]
					del self.timeDataNumbers[TTI][NTB][self.dataColumnCount+dataOffsetInTimeDataNumbers]
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.indiLOG.log(40," self.timeDataNumbers: {}".format(self.dataColumnCount)+"/{}".format(len(self.timeDataNumbers[0][0])))
		


		try:
			for TTI in range (noOfTimeTypes):
				del self.valuesFromIndigo[TTI][colToRemove]
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		del self.newVFromIndigo[colToRemove]
		del self.lastTimeStampOfDevice[colToRemove]
		
		del self.sqlColListStatus[colToRemove]
		del self.sqlHistListStatus[colToRemove]
		
		return


	########################################	set config defaults	########################################	########################################	######################################


	########################################
	def setPlotToDefault(self,nPlot):
		self.PLOT[nPlot]=copy.deepcopy(emptyPlot)
		return

	#######################################   	# do this 2.
	def setLineToDefault(self, nPlot,nLine):
		self.PLOT[nPlot]["lines"][nLine]=copy.deepcopy(emptyLine)
		return


	###########################	   cProfile stuff   ############################ START
	####-----------------  ---------
	def getcProfileVariable(self):

		try:
			if self.timeTrVarName in indigo.variables:
				xx = (indigo.variables[self.timeTrVarName].value).strip().lower().split("-")
				if len(xx) ==1: 
					cmd = xx[0]
					pri = ""
				elif len(xx) == 2:
					cmd = xx[0]
					pri = xx[1]
				else:
					cmd = "off"
					pri  = ""
				self.timeTrackWaitTime = 20
				return cmd, pri
		except	Exception as e:
			pass

		self.timeTrackWaitTime = 60
		return "off",""

	####-----------------            ---------
	def printcProfileStats(self,pri=""):
		try:
			if pri !="": pick = pri
			else:		 pick = 'cumtime'
			outFile		= self.userIndigoPluginDir+"timeStats"
			self.indiLOG.log(20," print time track stats to: "+outFile+".dump / txt  with option: "+pick)
			self.pr.dump_stats(outFile+".dump")
			sys.stdout 	= self.openEncoding(outFile+".txt", "w")
			stats 		= pstats.Stats(outFile+".dump")
			stats.strip_dirs()
			stats.sort_stats(pick)
			stats.print_stats()
			sys.stdout = sys.__stdout__
		except: pass
		"""
		'calls'			call count
		'cumtime'		cumulative time
		'file'			file name
		'filename'		file name
		'module'		file name
		'pcalls'		primitive call count
		'line'			line number
		'name'			function name
		'nfl'			name/file/line
		'stdname'		standard name
		'time'			internal time
		"""

	####-----------------            ---------
	def checkcProfile(self):
		try: 
			if time.time() - self.lastTimegetcProfileVariable < self.timeTrackWaitTime: 
				return 
		except: 
			self.cProfileVariableLoaded = 0
			self.do_cProfile  			= "x"
			self.timeTrVarName 			= "enableTimeTracking_"+self.pluginName
			self.indiLOG.log(10,"testing if variable {} is == on/off/print-option to enable/end/print time tracking of all functions and methods (option:'',calls,cumtime,pcalls,time)".format(self.timeTrVarName))

		self.lastTimegetcProfileVariable = time.time()

		cmd, pri = self.getcProfileVariable()
		if self.do_cProfile != cmd:
			if cmd == "on": 
				if  self.cProfileVariableLoaded ==0:
					self.indiLOG.log(10,"======>>>>   loading cProfile & pstats libs for time tracking;  starting w cProfile ")
					self.pr = cProfile.Profile()
					self.pr.enable()
					self.cProfileVariableLoaded = 2
				elif  self.cProfileVariableLoaded >1:
					self.quitNow = " restart due to change  ON  requested for print cProfile timers"
			elif cmd == "off" and self.cProfileVariableLoaded >0:
					self.pr.disable()
					self.quitNow = " restart due to  OFF  request for print cProfile timers "
		if cmd == "print"  and self.cProfileVariableLoaded >0:
				self.pr.disable()
				self.printcProfileStats(pri=pri)
				self.pr.enable()
				indigo.variable.updateValue(self.timeTrVarName,"done")

		self.do_cProfile = cmd
		return 

	####-----------------            ---------
	def checkcProfileEND(self):
		if self.do_cProfile in["on","print"] and self.cProfileVariableLoaded >0:
			self.printcProfileStats(pri="")
		return
	###########################	   cProfile stuff   ############################ END


	########################################	Main loop 	########################################	########################################	######################################

	########################################
	def runConcurrentThread(self):


		self.dorunConcurrentThread()
		self.checkcProfileEND()

		self.sleep(1)
		if self.quitNow !="":
			self.indiLOG.log(20,"runConcurrentThread stopping plugin due to:  ::::: {}".format(self.quitNow) + " :::::")
			serverPlugin = indigo.server.getPlugin(self.pluginId)
			serverPlugin.restart(waitUntilDone=False)
		return

		
####-----------------   main loop          ---------
	def dorunConcurrentThread(self):
# reset variables just to make sure..
		self.indigoCommand =[]

		self.checkPlotsEnable=False
		self.checkIfEventData()
		

		theDayS                     = time.strftime("%d", time.localtime())
		theHourS                    = time.strftime("%H", time.localtime())
		theMinuteS                  = time.strftime("%M", time.localtime())
		theMinute                   = int(theMinuteS)
		theMinuteToCheckEvents      = -1
		theSecond                   = time.strftime("%S", time.localtime())
		lastDayS                    = theDayS
		lastHourS                   = theHourS
		lastSecond                  = theSecond
		lastMinute                  = int(theMinute)
		lastMinutex					= 0
		theMinute5                  = (theMinute//5)*5
		lastMinute5                 = theMinute5
		lastMinute5P                = theMinute5
		lastDaycheckS               = " "
		theDayIndex                 = time.strftime("%Y%m%d", time.localtime())
		theHourIndex                = time.strftime("%Y%m%d%H", time.localtime())
		theMinuteIndex              = time.strftime("%Y%m%d%H", time.localtime())+self.padzero(theMinute5)
		self.pauseTimer             = 200
		self.histupdatesWaitCount   = 0
		self.histupdatesWaitCount1  = 0

# do we have ny real day, if yes ==> initialized
		if self.dataColumnCount > 0 :
			self.indigoInitialized = True	# if there is any data this number is > 0 ie we asume we have a valid configuration and can start collecting data

# setup gnu files and redo parameters after data read from indigo
		self.removeDeletedIndigoPlots() # remove deleted files "while we were out"
		self.writePlotParameters()  # for matplot
		self.setupGNUPlotFiles(calledfrom="runConcurrentThread1")



# check if all configuration is deone, if not, wait until its configured
		try:
			sleepTime =10
			msgCount =0
			while msgCount < 5 and self.indigoInitialized == False:
				if msgCount ==0: self.indiLOG.log(30," not  configured yet, please select menue:  Indigo /plugins/"+self.pluginName+"/Configure...")
				msgCount +=1
				self.sleep (sleepTime)
				sleepTime =1
				
		except self.StopThread:
			self.quitNOW =  "self.StopThread"

		theDayIndex = time.strftime("%Y%m%d", time.localtime())+"000000"			# check if there is index information and if correct, ie does today exist in the index?
		try:
			theIndex = self.timeDataIndex[2][theDayIndex]			#if there is today's bin we are ok
		except:													# todays data is missing, inititalize today and shift left
			
			self.indiLOG.log(30," index data for today (INDIGOplot was not running over midnight), will initialize data   "+theDayIndex +"  "+self.timeDataIndex[2][980:])
			self.doShiftDay()
			lastDayS = theDayS

#		self.getDeviceParametersFromFile(calledfrom="runConcurrentThread")

		self.checkFileExistsErrorMessageCounter =99						## wait the first successfull plot or after 5 minutes to cehck if plots are being created
		self.pause = False
		lastTimeTest="-1"
		self.indigoInitializedMainLoop  =   True
		redoData = False
		if datetime.datetime.now().hour ==0: self.createPy()  #do this only at midnight

		if self.devicesAdded ==0:  self.indiLOG.log(20,"initialized")
# main loop check for comamnds and gather data and create plots
		self.getLastConsumptionyCostPeriodBinWithData()  # set it to 0


		try:
			while  self.quitNOW == "":
				self.checkcProfile()
				if self.gnuORmat == "mat" and not self.isMATRunning(): self.startMAT()  # make sure matplot is running if needed
				#########################################################  start quick check loop               
				if not redoData:
					while True:
						ret =  self.doCHECKcommands()
						if   ret==1: continue
						elif ret==2: break
							
						theSec= int(time.localtime()[5])
						if theMinute == theMinute5 and theSec < 2: waitSecs = 3  # in the first 2 secs after plot time  all kinds of things are going onwait max time..
						else: waitSecs =2
							
						if theSec>57	: break
						if ((60-theSec)%self.samplingPeriod	) < waitSecs : break
						self.sleep( 1 )
						
						self.checkVariableData(testNew=True)
						self.checkFileData()
						
						theMinute = int(time.strftime("%M", time.localtime()))
						theHour   = int(time.strftime("%H", time.localtime()))

						if  len(self.eventDataPresent)>0:############## check if EVENT  measures in data requested:
							if  theMinuteToCheckEvents != theMinute:
								if theMinute%5 == 3:
									theMinuteToCheckEvents = theMinute
									self.getLastSQLforEventdata(self.eventDataPresent) # start sql job to the the events
								
						### VS.versionCheck(self.pluginId,self.pluginVersion,indigo,13,10,printToLog="log")

						self.checkSQLdata()

						if self.checkPLOTSandConsumption(): break
				#########################################################  end quick check loop               



				################################ this is the data check loop once a minute ~ 3 secs after full  START
				if max(self.sqlColListStatus) ==0 and max(self.sqlHistListStatus) == 0:
					if self.initBy =="SQLstart":
						self.initBy =""

				theDayS 		= time.strftime("%d", time.localtime())  ## "S" for string otherwise integer
				theHourS 		= time.strftime("%H", time.localtime())
				theMinuteS		= time.strftime("%M", time.localtime())
				theMinute		= int(theMinuteS)
				theMinute5		= (theMinute//5)*5
				theSecond		= int(time.strftime("%S", time.localtime()))
				theDayIndex		= time.strftime("%Y%m%d", time.localtime())+"000000"
				theHourIndex	= time.strftime("%Y%m%d%H", time.localtime())+"0000"
				theMinuteIndex	= time.strftime("%Y%m%d%H", time.localtime())+self.padzero(theMinute5)+"00"
				

				if (60-theSecond)%self.samplingPeriod	<3 :
					if theMinute != lastMinute:
						lastMinute = theMinute
						self.preSelectDevices()										# redo device list
						self.putconsumedDuringPeriod()
						if self.syncPlotsWithIndigo() ==-1: break
						if theMinute5 != lastMinute5:									# new 5 minute bin	after 5 minutes average the5 minutes bin ..
							lastMinute5 = theMinute5
							if theDayS != lastDayS:									# new Day bin
								self.doShiftDay()
								lastDayS		= theDayS
								theDayIndex		= time.strftime("%Y%m%d", time.localtime())+"000000"
								theHourIndex	= time.strftime("%Y%m%d%H", time.localtime())+"0000"
								theMinuteIndex	= time.strftime("%Y%m%d%H", time.localtime())+self.padzero(theMinute5)+"00"
								self.acummulateValues("init",  2,self.timeDataIndex[2][theDayIndex])
							if theHourS != lastHourS:										# new Hour bin
								self.acummulateValues("init",  1,self.timeDataIndex[1][theHourIndex])
								lastHourS 	= theHourS
								intHourMin	= int(theHourS+theMinuteS)
								self.putConsumptionCostData()
								self.setupGNUPlotFiles(calledfrom="runConcurrentThread shiftday")
							self.checkPlotsEnable =True
							self.checkFileExistsErrorMessageCounter =0
							self.acummulateValues("init", 0,self.timeDataIndex[0][theMinuteIndex])


						if len(self.removeThisDevice) > 0:
							self.removeDevice()				# device not available anymore delete from data and indexes
							redoData =True
							lastMinute=-1
							continue
						redoData = False
						self.checkVariableData(testNew=False)

					## get new values once a minute
					self.getIndigoData()

					
				## updates Day count
					try:
						theIndex = self.timeDataIndex[2][theDayIndex]						# get the bin
					except:
						self.indiLOG.log(20," missed shift data at midnight, will try again ")
						self.doShiftDay()
						lastDayS		= time.strftime("%d", time.localtime())
						theDayIndex		= time.strftime("%Y%m%d", time.localtime())+"000000"
						theHourIndex	= time.strftime("%Y%m%d%H", time.localtime())+"0000"
						theMinuteIndex	= time.strftime("%Y%m%d%H", time.localtime())+self.padzero(theMinute5)+"00"
					
					#self.indiLOG.log(20," main loop  day:{}, hour:{}, minute:{},  theMinute5:{}".format(theDayIndex,theHourIndex, theMinuteIndex, theMinute5 ))
					#self.indiLOG.log(20," main loop  timeDataIndex:{}".format(self.timeDataIndex[0]))
					self.acummulateValues("finish", 2, self.timeDataIndex[2][theDayIndex])
					self.putDiskData(2)								# save it to disk for gnuplot
				## updates hourly count
					self.acummulateValues("finish", 1, self.timeDataIndex[1][theHourIndex])
					self.putDiskData(1)
				## updates minute(5 minutes bin)
					self.acummulateValues("finish", 0, self.timeDataIndex[0][theMinuteIndex])
					self.putDiskData(0)
					self.sleep(3)
				   

				## do plots every 5 minutes, just after 5 minute intervall has changed so that the next bin is  filled with one entry
				if theMinute5 != lastMinute5P:
					self.checkIfEventData()
					self.mkCopyOfDB() # check if we need a new copy of the DB
					lastMinute5P = theMinute5
					self.plotNow()
					self.sleep(1)
				if theMinute5 == lastMinute5P and theMinute == theMinute5 +1:  # check at the next minute after plot time
					self.CheckIfPlotOK(wait=False)
											
				if theDayS != lastDaycheckS:									# new Day checks at 16 after midnight
					if theHourS =="00" and theMinuteS =="15" :
						lastDaycheckS =theDayS
						self.doAfterMidnight()
				self.checkForNewDeviceNames()
				self.sleep(0.5)  ## wait for right time
				################################ this is the data check loop once a minute ~ 3 secs after full  END




		except self.StopThread:
			# do any cleanup here
			pass
		self.stopMAT()
			
		self.indiLOG.log(30," main loop stopped")


	########################################
	def doAfterMidnight(self):
		try:
			self.createPy()
			if self.sqlDynamic.find("batch2Day")==0:
				for i in range(1,len(self.sqlColListStatus)):
					self.sqlColListStatus[i]=10
					self.sqlHistListStatus[i]=10
				self.devicesAdded =2
				while True:
					self.setupSQLDataBatch(calledfrom="midnight")
					if self.originalCopySQLActive =="-1": break
					sleep(60)            
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return


	########################################
	def checkPLOTSandConsumption(self):
		try:

			if  self.newPLOTS!="":
				if self.syncPlotsWithIndigo(Force=True) ==-1: return True
				self.plotNow(createNow=self.newPLOTS)
				self.newPLOTS =""
				self.newPREFS=False
			else:
				if self.newPREFS :
					self.putConsumptionCostData()
					self.startColumnData()
					if self.syncPlotsWithIndigo(Force=True) ==-1: return True
					self.newPREFS=False
					self.plotNow()
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return False


	########################################
	def checkSQLdata(self):
		try:

			if not self.waitWithSQL and (sum(self.sqlHistListStatus) >0 or sum(self.sqlColListStatus) >0 ) and self.sqlDynamic !="None":
				if self.devicesAdded >1 or self.scriptNewDevice >0:
					self.putDeviceParametersToFile()
					self.devicesAdded =2
					if self.sqlDynamic.find("batch") ==0:
						while True:
							self.setupSQLDataBatch(calledfrom="runConcurrentThread")
							if self.originalCopySQLActive =="-1": break
							sleep(60)            
				if self.sqlDynamic.find("batch") ==0:
							self.sleep(1)
							self.readSQLdataBatch(calledfrom="runConcurrentThread")

				if self.histupdatesWaitCount1 == sum(self.sqlHistListStatus) and self.histupdatesWaitCount1 >0:
					self.histupdatesWaitCount +=1
					if self.histupdatesWaitCount > 199:				## this is for safety if it hangs redo the sql import after 200 loops waiting for successful import.
						for n in range(len(self.sqlHistListStatus)):
							if self.sqlHistListStatus[n]>0:
								self.sqlColListStatus[n]	=10
								self.sqlHistListStatus[n]	= 50
						while True:
							self.setupSQLDataBatch(calledfrom="runConcurrentThread re-read due to hang")
							if self.originalCopySQLActive =="-1": break
							self.sleep(60)            
						if self.sqlDynamic.find("-resetTo-") >-1:
							self.sqlDynamic = "batch2Days" #set back to default mode
						self.sqlDynamic="batch-resetTo-"+self.sqlDynamic
						self.devicesAdded =2
						self.indiLOG.log(40,"restarting SQL import,    it seems to hang. If this happens several times reload INDIGOplotD : ")
						self.histupdatesWaitCount =0
				self.histupdatesWaitCount1=sum(self.sqlHistListStatus)

		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return 



	########################################
	def doCHECKcommands(self):
		try:
			self.pauseTimer +=1
			if self.pauseTimer > 100:
				self.pause = False
				self.pauseTimer = 0

			if len(self.indigoCommand) >0:
				if self.indigoCommand[0] != "" and self.indigoCommand[0].find("redoParam")==-1:
																				self.indiLOG.log(30,"pending indigoCommands: {}".format(self.indigoCommand))
				if self.indigoCommand[0] == "PauseDataCollection":
																				self.pause = True
																				self.pauseTimer = 0
				if self.indigoCommand[0] == "ContinueDataCollection":
																				self.pause =False
				if self.indigoCommand[0] == "redoParameters":
																				self.redoParameters()
																				self.indigoCommand=[""]
				if self.indigoCommand[0] == "redoParam":
																				self.redoParam()
																				self.indigoCommand=[""]
				if self.indigoCommand[0] == "plotNow":
																				self.syncPlotsWithIndigo()
																				self.doplotNOWCommand()
				if self.indigoCommand[0] == "plotNowOnly":
																				self.syncPlotsWithIndigo()
																				self.doplotNOWOnlyCommand()
				if self.indigoCommand[0] == "initData":
																				self.initData()
																				self.indigoCommand=[""]
				if self.indigoCommand[0] == "resetDevParams":
																				self.doResetDevParams()
																				self.indigoCommand=[""]
				if self.indigoCommand[0] == "fNameToLog":						self.FnameToLog()
				if self.indigoCommand[0] == "InstallGnuplot":					self.doInstallGnuplot()
				if self.indigoCommand[0] == "ReloadSQL":						self.ReloadSQL()
				if self.indigoCommand[0] == "ReloadSQL2Days":					self.ReloadSQL2Days()
				if self.indigoCommand[0] == "PrintDeviceData":					self.PrintDeviceData()
				if self.indigoCommand[0].find("PrintPlotData")>-1:				self.PrintPlotData(self.indigoCommand[0].split(":")[1])
				if self.indigoCommand[0] == "PrintData":						self.PrintData()
				if self.indigoCommand[0] == "PrintDevStates":					self.PrintDeviceStates()
				if self.indigoCommand[0] == "PlotALL":
																				self.syncPlotsWithIndigo()
																				self.plotNow()
				if self.indigoCommand[0] == "inpSavePy":						self.createPy(aType="manual")
				if self.indigoCommand[0] == "export":							self.createPy(aType="export")
				if self.indigoCommand[0] == "exportMini":						self.createPy(aType="exportMini")
				if self.indigoCommand[0].find("CheckIfPlotOK")>-1:				self.CheckIfPlotOK(checkOnlyThisOne=self.indigoCommand[0].split("+++")[1])
				if self.indigoCommand[0] == "quitNOW":
																				return 2
			if len(self.indigoCommand) >0: del self.indigoCommand[0]

			if self.pause:
				self.sleep(1)
				return 1
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return 0


	########################################
	def syncPlotsWithIndigo(self, Force=False):
		changed = False
		if self.waitWithPLOTsync: self.sleep(0.5)
		for dev in indigo.devices.iter("self"):

			### if this happens we can not handle this automatically!!!
			if dev.name.find("/") >-1:
				self.indiLOG.log(40,"plot device name MUST NOT contain a / "+ dev.name)
				self.indiLOG.log(40,"stopping INDIGOPLOTD , please rename plot device manually and restart INDIGOPLOTD")
				self.quitNOW = "plot device name MUST NOT contain a /"
				return -1
			### if this happens we can not handle this automatically!!!
			nPlot=str(dev.id)
			if nPlot in self.PLOT:  # it is present
				if self.PLOT[nPlot]["DeviceNamePlot"] == dev.name:
					if Force: # fill PLOT with  keys if missing
						somethingAdded= self.fnameToDeviceNamePlot(nPlot)
						for  theKey in emptyPlot:
							if not theKey in self.PLOT[nPlot] :
								self.PLOT[nPlot][theKey] =emptyPlot[theKey]
								somethingAdded = True
								changed =True
						for  theKey in emptyLine:
							for  line in self.PLOT[nPlot]["lines"]:
								if not theKey in self.PLOT[nPlot]["lines"][line]:
									self.PLOT[nPlot]["lines"][line][theKey]= emptyLine[theKey]
									somethingAdded = True
									self.indiLOG.log(10,"syncPlotsWithIndigo adding missing keys to PLOT line "+ dev.name+" id"+ nPlot+" DeviceNamePlot:{}".format(self.PLOT[nPlot])+ " key:"+theKey)
						for  line in self.PLOT[nPlot]["lines"]:
							kList=[]
							for k in self.PLOT[nPlot]["lines"][line]:
								if k not in emptyLine:
									kList.append(k)
							for k in kList:
								del self.PLOT[nPlot]["lines"][line][k]
								changed =True
								somethingAdded = True
						if str(dev.enabled) != self.PLOT[nPlot]["enabled"] :
							self.PLOT[nPlot]["enabled"] = str(dev.enabled)
							changed = True

						if somethingAdded:
							if self.decideMyLog("General"): self.indiLOG.log(10,"syncPlotsWithIndigo adding missing keys to PLOT "+ dev.name+" id"+ nPlot+" DeviceNamePlot:{}".format(self.PLOT[nPlot]) )
							props=dev.pluginProps
							dev.configured = True
							props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
							dev.replacePluginPropsOnServer(props)
							dev.configured = True
							dev.replaceOnServer()

					else:
						if str(dev.enabled) != self.PLOT[nPlot]["enabled"] :
							self.PLOT[nPlot]["enabled"] = str(dev.enabled)
							changed = True

					continue

				else:  # device name has changed
					self.removeThisPlotFile(nPlot)  # remove the gnu png files etc
#					try:
					self.indiLOG.log(20,"syncPlotsWithIndigo device name has changed    devName: old/new "+self.PLOT[nPlot]["DeviceNamePlot"]+"/"+ dev.name+" id:"+ nPlot)
					self.PLOT[nPlot]["DeviceNamePlot"] = dev.name
					props=dev.pluginProps
					props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
					dev.replacePluginPropsOnServer(props)
					changed=True
					continue


			else:  # this either new  plot or call at start up when we read the data copy info from device into PLOT
				if self.decideMyLog("General"): self.indiLOG.log(10,"syncPlotsWithIndigo copying PLOT using "+ dev.name+" id:"+ nPlot)
				try:
					try: self.PLOT[nPlot]=json.loads(dev.pluginProps["PLOTindigo"])
					except: pass
					if nPlot in self.PLOT and  self.PLOT[nPlot] !={}:
						self.fnameToDeviceNamePlot(nPlot)
						for nLine in self.PLOT[nPlot]["lines"]:
								lr = self.PLOT[nPlot]["lines"][nLine]["lineLeftRight"]
								if 		lr =="x1y2":	lr = "Right"
								elif	lr =="Right":	lr = "Right"
								else:					lr = "Left"
								self.PLOT[nPlot]["lines"][nLine]["lineLeftRight"] = lr
								try: # if new  it not there yet..
									if self.PLOT[nPlot]["lines"][nLine]["lineType"] !="Numbers":
										self.PLOT[nPlot]["lines"][nLine]["lineNumbersFormat"]	=	""
										self.PLOT[nPlot]["lines"][nLine]["lineNumbersOffset"]	=	""
								except:
									pass
						if self.PLOT[nPlot]["DeviceNamePlot"] 	!= dev.name: self.removeThisPlotFile(nPlot)
						self.PLOT[nPlot]["DeviceNamePlot"] 		=  dev.name
						for  theKey in emptyPlot:
							if not theKey in self.PLOT[nPlot] : self.PLOT[nPlot][theKey] =emptyPlot[theKey]
						for  theKey in emptyLine:
							for  line in self.PLOT[nPlot]["lines"]:
								if not theKey in self.PLOT[nPlot]["lines"][line]:
									self.PLOT[nPlot]["lines"][line][theKey]= emptyLine[theKey]
									somethingAdded = True
								if str(type(self.PLOT[nPlot]["lines"][line]["lineToColumnIndexA"])) !="int":
									somethingAdded = True
									try:
										self.PLOT[nPlot]["lines"][line]["lineToColumnIndexA"] = int(self.PLOT[nPlot]["lines"][line]["lineToColumnIndexA"])
									except:
										self.PLOT[nPlot]["lines"][line]["lineToColumnIndexA"]=0
								if str(type(self.PLOT[nPlot]["lines"][line]["lineToColumnIndexB"])) !="int":
									somethingAdded = True
									try:
										self.PLOT[nPlot]["lines"][line]["lineToColumnIndexB"] = int(self.PLOT[nPlot]["lines"][line]["lineToColumnIndexB"])
									except:
										self.PLOT[nPlot]["lines"][line]["lineToColumnIndexB"]=0
						props=dev.pluginProps
						props["PLOTindigo"]= json.dumps(self.PLOT[nPlot])
						dev.replacePluginPropsOnServer(props)
						dev.configured = True
						dev.replaceOnServer()
						if self.decideMyLog("General"): self.indiLOG.log(10,"syncPlotsWithIndigo found new  PLOT ... syncing 2 "+ dev.name+" id"+ nPlot+" fname:" +self.PLOT[nPlot]["DeviceNamePlot"] )
						changed=True
						continue
				except:
					continue # not created yet, wait one more round
 

		if self.checkForVariables(mPlot=""): changed=True
		
		if Force or changed:
			self.writePlotParameters()
			self.setupGNUPlotFiles(calledfrom="syncPlotsWithIndigo")
		return 0

	########################################
	def checkForVariables(self,mPlot):  ## just in case, shoulkd never happen...

		for nPlot in self.PLOT:
			if mPlot !="" and mPlot != nPlot: continue
			self.PLOT[nPlot]["variableinPlot"]=""
			for key in self.PLOT[nPlot]:
				try:
					if key =="lines":
						for line in self.PLOT[nPlot][key]:
							for key2 in self.PLOT[nPlot][key][line]:
								if self.PLOT[nPlot][key][line][key2].find("%%v:"):
									self.PLOT[nPlot]["variableInText"]="yes"
									return True   
					else:
						if self.PLOT[nPlot][key].find("%%v:")>-1: 
							self.PLOT[nPlot]["variableInText"]="yes"
							return True 
				except:
					pass
		return False


	########################################
	def fnameToDeviceNamePlot (self,nPlot):  ## just in case, shoulkd never happen...

		if nPlot not in self.PLOT: return False

		if "Fname" not in self.PLOT[nPlot]: return False
		if self.decideMyLog("General"): self.indiLOG.log(20,"fnameToDeviceNamePlot 1: {}".format(nPlot)+ " {}".format(self.PLOT[nPlot]))
		self.PLOT[nPlot]["DeviceNamePlot"]		= self.PLOT[nPlot]["Fname"]
		del self.PLOT[nPlot]["Fname"]

		if "Type" in self.PLOT[nPlot]:
			self.PLOT[nPlot]["devOrVar"]		= self.PLOT[nPlot]["Type"]
			del self.PLOT[nPlot]["Type"]
			
		for nLine in self.PLOT[nPlot]["lines"]:

			if "Type" in self.PLOT[nPlot]["lines"][nLine]:
				lineType = self.PLOT[nPlot]["lines"][nLine]["Type"]
				if lineType == "0":		lineType = "LineDashed"
				if lineType == "6":		lineType = "LineSolid"
				if lineType == "solid":	lineType = "Histogram"
				del self.PLOT[nPlot]["lines"][nLine]["Type"]
				self.PLOT[nPlot]["lines"][nLine]["lineType"]			= lineType

			if "Width" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineWidth"] 			= self.PLOT[nPlot]["lines"][nLine]["Width"]
				del self.PLOT[nPlot]["lines"][nLine]["Width"]

			if "Color" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineColor"] 			= self.PLOT[nPlot]["lines"][nLine]["Color"]
				del self.PLOT[nPlot]["lines"][nLine]["Color"]

			if "Func" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineFunc"] 			= self.PLOT[nPlot]["lines"][nLine]["Func"]
				del self.PLOT[nPlot]["lines"][nLine]["Func"]

			if "Smooth" in self.PLOT[nPlot]["lines"][nLine]:
				lineSmooth = self.PLOT[nPlot]["lines"][nLine]["Smooth"]
				if lineSmooth == "bezier":		lineSmooth = "strong"
				if lineSmooth == "cspline2":	lineSmooth = "medium"
				if lineSmooth == "csplines":	lineSmooth = "soft"
				self.PLOT[nPlot]["lines"][nLine]["lineSmooth"] 			= lineSmooth
				del self.PLOT[nPlot]["lines"][nLine]["Smooth"]

			if "Multiplier" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineMultiplier"] 		= self.PLOT[nPlot]["lines"][nLine]["Multiplier"]
				del self.PLOT[nPlot]["lines"][nLine]["Multiplier"]

			if "Offset" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineOffset"] 			= self.PLOT[nPlot]["lines"][nLine]["Offset"]
				del self.PLOT[nPlot]["lines"][nLine]["Offset"]

			if "leftRight" in self.PLOT[nPlot]["lines"][nLine]:
				lr 														= self.PLOT[nPlot]["lines"][nLine]["leftRight"]
				if 		lr =="x1y2":	lr = "Right"
				elif	lr =="Right":	lr = "Right"
				else:					lr = "Left"
				self.PLOT[nPlot]["lines"][nLine]["lineLeftRight"] 		= lr
				del self.PLOT[nPlot]["lines"][nLine]["leftRight"]

			if "Key" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineKey"] 			= self.PLOT[nPlot]["lines"][nLine]["Key"]
				del self.PLOT[nPlot]["lines"][nLine]["Key"]

			if "ToColumnIndex" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexA"] 	= self.PLOT[nPlot]["lines"][nLine]["ToColumnIndex"]
				del self.PLOT[nPlot]["lines"][nLine]["ToColumnIndex"]

			if "ToColumnIndexB" in self.PLOT[nPlot]["lines"][nLine]:
				self.PLOT[nPlot]["lines"][nLine]["lineToColumnIndexB"] 	= self.PLOT[nPlot]["lines"][nLine]["ToColumnIndexB"]
				del self.PLOT[nPlot]["lines"][nLine]["ToColumnIndexB"]

		if self.decideMyLog("General"): self.indiLOG.log(20,"fnameToDeviceNamePlot after: {}".format(nPlot)+ " {}".format(self.PLOT[nPlot]))

		return True


	########################################
	def removeDeletedIndigoPlots(self):  ## just in case, should never happen...

		# make a list of all indigopltD devices
		plotsToDelete =[]
		devlist =[]
		for dev in indigo.devices.iter():
			if  dev.pluginId.find(self.pluginId) > -1:
				devlist.append(dev)
		ndevs= len(devlist)

		# check if the PLOTs are in the list found
		for nPlot in self.PLOT:
			found = False
			ID = int(nPlot)
			for ii in range(ndevs):
				if ID == devlist[ii].id:
					found =True
					break
			if found: continue
			plotsToDelete.append(nPlot)

		if len(plotsToDelete) >0:
			self.indiLOG.log(30,"removeDeletedIndigoPlots remove device from PLOT: {}".format(plotsToDelete))
			for ii in range(len(plotsToDelete)):
				nPlot = plotsToDelete[ii]
				self.removeThisPlotFile(nPlot)  # remove the gnu png files etc
				del self.PLOT[nPlot]  # not found, remove from PLOTs
		plotsToDelete =[]
		devlist=[]




	########################################
	def checkMinMaxFiles(self):
		try:
			files = os.listdir( self.userIndigoPluginDir+"data/" )
			for ff in files: 
				for TTI in range(noOfTimeTypes):
					if ff.find("-"+binTypeFileNames[TTI]+"-") >-1:
						try:
							xx=os.remove(self.userIndigoPluginDir+"data/"+ff)
						except:
							self.indiLOG.log(30,"failed to delete file "+self.userIndigoPluginDir+"data/"+ff+"  error: {}".format(xx))    
						
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))



	########################################
	def plotNow(self, createNow="", showNow="",ShowOnly=""):
		if self.waitWithPlotting: return
		self.checkPlot1 = False
		
		########## matplot  ########
		if self.gnuORmat == "mat":
			
			if ShowOnly == "":
				f=self.openEncoding( self.matplotcommand , "w")
				if createNow == "":	f.write(json.dumps("do all plots"))
				else:				f.write(json.dumps(createNow))
				f.close()

				if showNow   == "": return
				if createNow == "": return
				self.sleep(2)
			
				for ii in range(10):  # wait until matplot is finished, max 4+2 seconds
					self.sleep(0.4)
					if os.path.isfile(self.matplotcommand): continue  # file still there, wait more
					break

			for nPlot in self.PLOT:
				if self.PLOT[nPlot]["DeviceNamePlot"]  == "None": continue
				if self.PLOT[nPlot]["NumberIsUsed"] == 0: continue
				if "enabled" in self.PLOT[nPlot] and self.PLOT[nPlot]["enabled"] != "True": continue
				if self.PLOT[nPlot]["DeviceNamePlot"] != showNow: continue
				if self.PLOT[nPlot]["PlotType"] =="dataFromTimeSeries":
					for tt in range(noOfTimeTypes):					# this is for the day/hour/minute names
						if int(self.PLOT[nPlot]["MHDDays"][tt]) == 0: continue
						for ss in range(2):									# this is for s1 / s2 size names
							if len(str(self.PLOT[nPlot]["resxy"][ss])) < 6: continue	# no proper size given skip this plot
							PNGname= "{}{}-{}-{}.png".format(self.indigoPNGdir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotTimeNames[tt], self.plotSizeNames[ss])
							if os.path.isfile(PNGname): os.system("open '{}'".format(PNGname).encode('utf-8')) 
				else:
					for ss in range(2):									# this is for s1 / s2 size names
						if len(str(self.PLOT[nPlot]["resxy"][ss])) < 6: continue	# no proper size given skip this plot
						PNGname= "{}{}-{}.png".format(self.indigoPNGdir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotSizeNames[ss])

						if os.path.isfile(PNGname.encode('utf8')): os.system("open '{}'".format(PNGname).encode('utf-8')) 

		########## GNUPLOT  #########
		else:
			if not os.path.isfile(self.gnuPlotBinary):
				self.indiLOG.log(40,"GNUPLOT is not installed, can not use it ")
				return
			for nPlot in self.PLOT:							#this can be 6 per plot definition
				if self.PLOT[nPlot]["DeviceNamePlot"]  == "None": continue
				if self.PLOT[nPlot]["NumberIsUsed"] ==0: continue
				if "enabled" in self.PLOT[nPlot] and self.PLOT[nPlot]["enabled"] !="True": continue
				if not( createNow == "" or self.PLOT[nPlot]["DeviceNamePlot"] == createNow) : continue
				if self.PLOT[nPlot]["PlotType"] =="dataFromTimeSeries":
					for tt in range(noOfTimeTypes):					# this is for the day/hour/minute names
						if int(self.PLOT[nPlot]["MHDDays"][tt]) ==0: continue
						self.checkExtraData(nPlot,tt)
						for ss in range(2):									# this is for s1 / s2 size names
							if len(str(self.PLOT[nPlot]["resxy"][ss])) < 6: continue			# no proper size given skip this plot
							if ShowOnly =="":
								Fname= self.userIndigoPluginDir+"gnu/"+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotTimeNames[tt]+"-"+self.plotSizeNames[ss]
								cmd="'"+self.gnuPlotBinary+"'  '"+Fname+".gnu'  2> '"+Fname+".err'  1>'"+Fname+".ok'   && echo up >'"+Fname+".done' "
								PNGname= "{}{}-{}-{}.png".format(self.indigoPNGdir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotTimeNames[tt], self.plotSizeNames[ss])
								self.callGnu(Fname,PNGname,cmd,self.PLOT[nPlot]["compressPNGfile"])
							if self.PLOT[nPlot]["DeviceNamePlot"] == showNow:
								self.sleep(0.05)
								PNGname= self.indigoPNGdir+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotTimeNames[tt]+"-"+self.plotSizeNames[ss]+".png"
								if ShowOnly =="yes" or self.CheckIfPlotdone(Fname,PNGname,wait=True) ==0:
									if os.path.isfile(PNGname.encode('utf8')):
										os.system("open '{}'".format(PNGname).encode('utf-8'))  # show plot
				else:
						for ss in range(2):									# this is for s1 / s2 size names
							if len(str(self.PLOT[nPlot]["resxy"][ss])) < 6: continue			# no proper size given skip this plot
							if ShowOnly =="":
								Fname= self.userIndigoPluginDir+"gnu/"+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotSizeNames[ss]
								cmd="'"+self.gnuPlotBinary+"'  '"+Fname+".gnu'  2> '"+Fname+".err'  1>'"+Fname+".ok'   && echo up >'"+Fname+".done' "
								PNGname= "{}{}-{}.png".format(self.indigoPNGdir, self.PLOT[nPlot]["DeviceNamePlot"], self.plotSizeNames[ss])
								PNGname= self.indigoPNGdir+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotSizeNames[ss]
								self.callGnu(Fname,PNGname,cmd,self.PLOT[nPlot]["compressPNGfile"])
							if self.PLOT[nPlot]["DeviceNamePlot"] == showNow :
								self.sleep(0.05)
								PNGname= self.indigoPNGdir+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotSizeNames[ss]+".png"
								if ShowOnly =="yes" or self.CheckIfPlotdone(Fname,PNGname,wait=True) ==0:
									if os.path.isfile(PNGname.encode('utf8')):
										os.system("open '{}'".format(PNGname))  # show plot

		return 
	########################################
	def checkExtraData(self,nPlot,TTI):
		#return
		######### to be written
		# need 
		# 1. time select from to for graph 
		# 2. shift by
		# time select for line
		# mult, offset
		# calc min/ mac per month day/hour
		# write file
		if self.decideMyLog("special"): self.indiLOG.log(20, self.PLOT[nPlot]["DeviceNamePlot"]+"  min-max calcs........................")
		try:
			PLT=self.PLOT[nPlot]
			if PLT["XYvPolar"] != "xy":
				return
			if PLT["PlotType"]=="dataFromTimeSeries":
				colOffset = dataOffsetInTimeDataNumbers
			else:
				colOffset = 0

			earliestDay	=["0","0","0"]
			lastDay		=["0","0","0"]
		
			earliestDay[2], lastDay[2] = self.firstLastDayToPlot(int(PLT["MHDDays"][2]), int(PLT["MHDShift"][2]), 2,"%Y%m%d%H%M")
			earliestDay[1], lastDay[1] = self.firstLastDayToPlot(int(PLT["MHDDays"][1]), int(PLT["MHDShift"][1]), 1,"%Y%m%d%H%M")
			earliestDay[0], lastDay[0] = self.firstLastDayToPlot(int(PLT["MHDDays"][0]), int(PLT["MHDShift"][0]), 0,"%Y%m%d%H%M")


			earliestsBinsToPlot	=[0,0,0]
			noOfBinsToPlot		=[0,0,0]
			earliestBinsToPlot, noOfBinsToPlot = self.binsToPlot(earliestDay,lastDay)
			timeStrLength=14



			for iLine in range(1,99):											# loop though the number of plots
				nLine = "{}".format(iLine)
				if not nLine in PLT["lines"]: continue
				PLTline=PLT["lines"][nLine]
				lR = PLTline["lineEveryRepeat"]
				if not( lR.find("maxHour")  == 0 or 
						lR.find("minHour")  == 0 or
						lR.find("maxDay")   == 0 or
						lR.find("minDay")   == 0 or
						lR.find("maxMonth") == 0 or
						lR.find("minMonth") == 0 ):
						continue
				column  = int(PLTline["lineToColumnIndexA"])
				columnB = int(PLTline["lineToColumnIndexB"])
				if column != 0:
					multFunc = PLTline["lineFunc"]											# this line will be plotted using std commands
					try:     ofs  = float(self.convertVariableOrDeviceStateToText(PLTline["lineOffset"]))
					except:  ofs  = 0.0
					try:     mult = float(self.convertVariableOrDeviceStateToText(PLTline["lineMultiplier"]))
					except:  mult = 1.0
					COLa= column  + colOffset
					COLb= columnB + colOffset
					out=[]
					fromTo = self.convertVariableOrDeviceStateToText(PLTline["lineFromTo"])
					if len(fromTo) > 2 and  fromTo.find(":") >0 :
							fromTo1, fromTo2 = fromTo.split(":")
					else:        
						fromTo1= "000000000000"
						fromTo2= "999999999999"

					if  len(fromTo1) != timeStrLength: 
						fromTo1+= "000000000000"
						fromTo1 = fromTo1[:timeStrLength] 
					if  len(fromTo2) != timeStrLength: 
						fromTo2+= "000000000000"
						fromTo2 = fromTo2[:timeStrLength]
					try: lineShift = int(PLTline["lineShift"]) #  # of day this lines is shifted
					except: lineShift = 0 
					datefmt = "%Y%m%d%H%M%S"
					

					for timeIndex in range(earliestBinsToPlot[TTI], earliestBinsToPlot[TTI]+ noOfBinsToPlot[TTI]):
						if float(self.timeDataNumbers[TTI][timeIndex][0]) == 0.: continue
						if float(self.timeDataNumbers[TTI][timeIndex][0]) == 0.: continue
						timeString = str(self.timeBinNumbers[TTI][timeIndex])
						if lineShift !=0: 
							timeString0 = (  datetime.datetime.strptime(timeString,datefmt) + datetime.timedelta(lineShift*24*60*60)  ).strftime(datefmt)
							self.indiLOG.log(20, timeString +"  "+ timeString0)
							timeString = timeString0
						
						if (timeString < fromTo1 or
							timeString > fromTo2 ): continue
						
						try:     Y = float(self.timeDataNumbers[TTI][timeIndex][COLa])
						except:  continue

						if multFunc !="None":
							try:    
								Yb = float(self.timeDataNumbers[TTI][timeIndex][COLb])
								if   multFunc == "+":
									Y = Y + Yb
								elif multFunc == "-":
									Y = Y - Yb
								elif multFunc == "*":
									Y = Y * Yb
								elif multFunc == "/" and Yb !=0. :
									Y = Y / Yb
							except: 
								pass
							
						if float(mult) !=1.: Y *= mult
						if float(ofs)  !=0.: Y += ofs
						out.append([timeString,Y])


					out2=""
					#if self.decideMyLog("special"): self.indiLOG.log(20,"===== out:{}".format(out) )
					if     lR.find("maxMonth")  == 0:
						out2 = self.calcMinMax(4,6, out, 1)
						
					elif   lR.find("minMonth")  == 0:
						out2 = self.calcMinMax(4,6, out, -1)
						
					elif   lR.find("maxDay")    == 0 and TTI < 2:
						out2 = self.calcMinMax(6,8, out, 1)
						
					elif   lR.find("minDay")    == 0 and TTI < 2:
						out2 = self.calcMinMax(6,8, out, -1)
						
					elif   lR.find("maxHour")   == 0 and TTI < 1:
						out2 = self.calcMinMax(8,10, out, 1)
						
					elif   lR.find("minHour")  == 0 and TTI  < 1:
						out2 = self.calcMinMax(8,10, out, -1)
						
					if len(out2) > 0:
						f=self.openEncoding("{}data/{}-{}-{}.dat".format(self.userIndigoPluginDir, self.PLOT[nPlot]["DeviceNamePlot"], binTypeFileNames[TTI], nLine),"w")
						f.write(out2)
					try:    f.close()
					except: pass

		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

	def calcMinMax(self,frDate,toDate, out, minMAX):
		try:
			out2=""
			m=""
			new = False
			X=""
			Y=""
			for ii in range(len(out)):
				MM= out[ii][0][frDate:toDate]
				if m != MM:
					if m!="":
						out2+=(str(X)+";{}".format(Y)+"\n")
					Y = minMAX*-1*99999999999999
					X = ""
					m= MM
					new = False
				if (minMAX ==1 and Y  < out[ii][1])  or  (minMAX == -1 and Y  > out[ii][1]):
					Y = out[ii][1]
					X = out[ii][0]
					new = True
			if new:
				out2+=(str(X)+";{}".format(Y)+"\n")            
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return out2

	########################################
	def callGnu(self,Fname,PNGname,cmd,compressPNGfile):
		if os.path.isfile((Fname+'.err').encode('utf8')): os.remove((Fname+'.err').encode('utf8'))
		if os.path.isfile((Fname+'.ok').encode('utf8')): os.remove((Fname+'.ok').encode('utf8'))
		if os.path.isfile((Fname+'.done').encode('utf8')): os.remove((Fname+'.done').encode('utf8'))
		ret, err = self.readPopen(cmd)
		if not compressPNGfile : return
		
		## now compress png file
		cmd = "'"+self.indigoPath+"Plugins/"+self.pluginName+".indigoPlugin/Contents/Server Plugin/pngquant' --force --ext .png '"+PNGname+"'"
		ret, err = self.readPopen(cmd)
		if os.path.isfile((PNGname).encode('utf8')): os.remove((PNGname).encode('utf8'))
	


	########################################
	def CheckIfPlotdone(self,Fname,PNGname,wait=False,checkOnlyThisOne=""):
		if not self.checkPlotsEnable and checkOnlyThisOne =="": return 0
		for i in range(20):
			if self.gnuORmat == "gnu":
				if os.path.isfile((Fname+'.err').encode('utf8')):
					if os.path.getsize((Fname+'.err').encode('utf8')) >0:
						f=self.openEncoding(Fname+'.err',"r")
						lines = f.read()
						f.close()
						if len(lines) >0:
							self.checkFileExistsErrorMessageCounter +=1
							if self.checkPlotsEnable and self.checkFileExistsErrorMessageCounter > 3 and self.checkFileExistsErrorMessageCounter < 10 or  checkOnlyThisOne !="":
								if not self.supressGnuWarnings: 
									self.indiLOG.log(30,"plotting  GNUPLOT error/warning for "+Fname)
									self.indiLOG.log(30,lines)
				
					os.remove((Fname+'.err').encode('utf8'))
				if os.path.isfile((Fname+'.done').encode('utf8')):
					if os.path.isfile((Fname+'.ok').encode('utf8')): os.remove((Fname+'.ok').encode('utf8'))
					if os.path.getsize((Fname+'.done').encode('utf8')) >0:
						return 0
				if not wait: return -1
				self.sleep(0.1)
			else:
				try:
					if ( time() - os.path.getmtime(PNGname.encode('utf8')) ) < 60.:
						return 0
				except:
					pass
				if not wait: return -1
				self.sleep(0.1)

	
		if self.checkPlotsEnable: 
			if self.decideMyLog("General"): self.indiLOG.log(30,"plotting  gnu not finished " +Fname)
		return -1

	########################################
	def CheckIfPlotOK(self,wait=True,checkOnlyThisOne=""):
		if checkOnlyThisOne !="": 
			if self.decideMyLog("General"): self.indiLOG.log(20," checking if plot was done successfully: "+ checkOnlyThisOne)
		if not self.checkPlotsEnable and checkOnlyThisOne =="": return
		if self.waitWithPlotting and checkOnlyThisOne =="": return
		if self.checkPlot1 and checkOnlyThisOne =="": return
		if self.gnuORmat == "mat" and wait: self.sleep(4)
		if self.checkFileExistsErrorMessageCounter > 50: self.checkFileExistsErrorMessageCounter =0
		allDone=True
		for nPlot in self.PLOT:							#
			if self.PLOT[nPlot]["DeviceNamePlot"]  == "None": continue
			if self.PLOT[nPlot]["DeviceNamePlot"] != checkOnlyThisOne and checkOnlyThisOne !="": continue
			if self.PLOT[nPlot]["NumberIsUsed"] ==0: continue
			if self.PLOT[nPlot]["PlotType"] =="dataFromTimeSeries":
				for tt in range(noOfTimeTypes):					#
					if int(self.PLOT[nPlot]["MHDDays"][tt]) ==0: continue
					for ss in range(2):									#
						if len(str(self.PLOT[nPlot]["resxy"][ss])) > 3:			#
							PNGname= self.indigoPNGdir+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotTimeNames[tt]+"-"+self.plotSizeNames[ss]+".png"
							Fname= self.userIndigoPluginDir+"gnu/"+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotTimeNames[tt]+"-"+self.plotSizeNames[ss]
							if self.CheckIfPlotdone(Fname,PNGname,wait=False,checkOnlyThisOne=checkOnlyThisOne) ==0:
								self.checkFileExistsErrorMessageCounter +=1
								if os.path.isfile(PNGname.encode('utf8')):
									if (os.path.getsize(PNGname.encode('utf8')))==0:
										allDone=False
										if self.checkFileExistsErrorMessageCounter > 5 and self.checkFileExistsErrorMessageCounter < 20 or checkOnlyThisOne !="":
													self.indiLOG.log(40," file:" +PNGname + " is empty,..likely wrong plot parameters or plot is just being created")
								else:
									allDone=False
									if self.checkFileExistsErrorMessageCounter > 3 and self.checkFileExistsErrorMessageCounter < 20 or checkOnlyThisOne !="":
										self.indiLOG.log(40," file:" +PNGname + " not created, check plot parameters")

			else:
				for ss in range(2):									#
					if len(str(self.PLOT[nPlot]["resxy"][ss])) > 3:			#
						PNGname= self.indigoPNGdir+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotSizeNames[ss]+".png"
						Fname= self.userIndigoPluginDir+"gnu/"+self.PLOT[nPlot]["DeviceNamePlot"]+"-"+self.plotSizeNames[ss]
						if  self.CheckIfPlotdone(Fname,PNGname,wait=False) ==0:
							self.checkFileExistsErrorMessageCounter +=1
							if os.path.isfile(PNGname.encode('utf8')):
								if (os.path.getsize(PNGname.encode('utf8')))==0:
									allDone=False
									if self.checkFileExistsErrorMessageCounter > 5 and self.checkFileExistsErrorMessageCounter < 20 or checkOnlyThisOne !="":
										self.indiLOG.log(40," file:" +PNGname + " is empty,..likely wrong plot parameters or plot is just being created")
						
							else:
								allDone=False
								if self.checkFileExistsErrorMessageCounter > 5 and self.checkFileExistsErrorMessageCounter < 20 or checkOnlyThisOne !="":
									self.indiLOG.log(40," file:" +PNGname + " not created, check plot parameters")
		if allDone: self.triggerEvent("PlotsRefreshed")

	########################################							########################################	########################################	######################################
	########################################	main program  -- end	########################################	########################################	######################################
	########################################							########################################	########################################	######################################




	########################################	online  collection	########################################	########################################	######################################

	########################################
	def checkVariableData(self,testNew=False):																							# get measurement data

		for nPlot in self.PLOT:
			if self.PLOT[nPlot]["PlotType"] =="dataFromVariable":
				try:
					theValue	=	indigo.variables[self.PLOT[nPlot]["PlotFileOrVariName"]].value
					self.PLOT[nPlot]["errorCount"] = 0
				except:
					self.PLOT[nPlot]["errorCount"]+=1
					if self.PLOT[nPlot]["errorCount"] >  1000: 	self.PLOT[nPlot]["errorCount"] =0
					if self.PLOT[nPlot]["errorCount"] < 5: 		self.indiLOG.log(40,"Variable does not exist: "+self.PLOT[nPlot]["PlotFileOrVariName"])
					return
					
				if testNew:  # if nothing new, do not write to file
					if theValue == self.PLOT[nPlot]["PlotFileLastupdates"]: continue
					self.PLOT[nPlot]["PlotFileLastupdates"] = theValue
							# write it anyway
				f=self.openEncoding(self.userIndigoPluginDir+"data/"+self.PLOT[nPlot]["PlotFileOrVariName"],"w")
				f.write(theValue.replace("|","\n")+"\n")
				f.close()
				if testNew:self.plotNow(createNow=self.PLOT[nPlot]["DeviceNamePlot"])

		return
	########################################
	def checkFileData(self):
		for nPlot in self.PLOT:
			if self.PLOT[nPlot]["PlotType"] =="dataFromFile":
				try:
					#self.indiLOG.log(20,"check if data file is there {}data/{}".format(self.userIndigoPluginDir, self.PLOT[nPlot]["PlotFileOrVariName"]))
					newTime = os.path.getmtime("{}data/{}".format(self.userIndigoPluginDir, self.PLOT[nPlot]["PlotFileOrVariName"]))

				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
					self.PLOT[nPlot]["errorCount"] +=1
					if self.PLOT[nPlot]["errorCount"] >  1000:	self.PLOT[nPlot]["errorCount"] =0
					if self.PLOT[nPlot]["errorCount"]< 5:		self.indiLOG.log(40,"File  does not exist: {}".format(self.PLOT[nPlot]["PlotFileOrVariName"]))
					return
				if newTime == self.PLOT[nPlot]["PlotFileLastupdates"]: continue
				self.PLOT[nPlot]["PlotFileLastupdates"]= newTime
				self.plotNow(createNow=self.PLOT[nPlot]["DeviceNamePlot"])
				self.PLOT[nPlot]["errorCount"] = 0

		return

	########################################
	def getIndigoData(self):


		lastdevNo		=	0
		for  theCol  in range (1,self.dataColumnCount+1):																# list of dev/props
			self.newVFromIndigo[theCol]	= ""
			

			x				=	"x"
			devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
			stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
			DEV				=	self.DEVICE["{}".format(devNo)]
			if not str(devNo) in self.DEVICE:
				self.sqlColListStatus[theCol]=0
				self.sqlHistListStatus[theCol]=0
				continue
			theDeviceID		=	int(DEV["Id"])
			if DEV["Name"].find("Var-") ==-1:
				theDeviceName = DEV["Name"]
			else:
				theDeviceName = DEV["Name"][4:]

			theDeviceState	=	DEV["state"][stateNo]
			theMeasurement	=	DEV["measurement"][stateNo]
			offset			=	float(DEV["offset"][stateNo])
			multiplier		=	float(DEV["multiplier"][stateNo])
			minValue		=	float(DEV["minValue"][stateNo])
			maxValue		=	float(DEV["maxValue"][stateNo])
			
			if  DEV["devOrVar"] == "Var-":
				useID =True
				try:
					theVariable	=	indigo.variables[theDeviceID]														# this is the pointer to the device, reuse if the device is the same for other props
				except:
					self.indiLOG.log(30,"getIndigoData, variable ID does not exist {}".format(theDeviceID)+ "; will be removed at next cycle")
					self.removeThisDevice.append(devNo)
					useID = False
				if useID:
					x = GT.getNumber(theVariable.value)
					timeNow  = time.strftime("%Y%m%d%H%M%s", time.localtime())
					self.lastTimeStampOfDevice[theCol] =[[timeNow,"0"]for k in range(noOfTimeTypes)]
	
			if  DEV["devOrVar"] == "Dev-":
				if theDeviceState != "None" and theDeviceState != "0":																					# only for real ones
					if devNo	!= lastdevNo:
						useID = True
						try:
							theDevice	=	indigo.devices[theDeviceID]														# this is the pointer to the device, reuse if the device is the same for other props
						except:
							self.indiLOG.log(30,"getIndigoData, device ID does not exist {}".format(theDeviceID)+" ; will be removed at next cycle")
							self.removeThisDevice.append(devNo)
							useID = False
						lastdevNo = devNo
					if useID:
						try:
							x = GT.getNumber(theDevice.states[theDeviceState])																# get the actual value
							try:
								for TTI in range(noOfTimeTypes):
									self.lastTimeStampOfDevice[theCol][TTI][1] = self.lastTimeStampOfDevice[theCol][TTI][0]
									self.lastTimeStampOfDevice[theCol][TTI][0] = theDevice.lastChanged.strftime("%Y%m%d%H%M%S")		# is YYYYMMDDHHMM

							except  Exception as e:
								self.indiLOG.log(40,"lastTimeStampOfDevice bad {}".format(theDeviceID)+" \nLine '%s' has error='%s'" % (sys.exc_info()[2].tb_lineno, e))
						except  Exception as e:
							self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
							self.indiLOG.log(40," getIndigoData, device state does not exist {} {}, plotdev:{}, devNo:{}; stateNo:{}".format(theDeviceID, theDeviceState, DEV, devNo, stateNo) )


			if x !="x":
				if  x < minValue  or (x > maxValue ):
					if self.decideMyLog("General"): self.indiLOG.log(30,"getIndigoData  "+theDeviceName+"/"+theDeviceState+"  out of min/max range: {}".format(minValue)+ "< {}".format(x)+ "< {}".format(maxValue))
				else:
					self.newVFromIndigo[theCol]= (x+offset)*multiplier
		return


	########################################
	def acummulateValues(self,action,TTI,TBI):	
		try:														# add up values, make averages or initialize
			if self.decideMyLog("General"): self.indiLOG.log(10," action:{}".format(action) +";  init:{}".format(self.initBy)+ "; TTI: {}".format(TTI)+"; TBI:  {}".format(TBI) +"  \n sqlColListStatus:{}".format(self.sqlColListStatus))
			if self.initBy == "SQLstart" :return
			if self.dataColumnCount <1: return
		
			if action =="init":
				self.timeDataNumbers[TTI][TBI][0]=0

				try:
					for theCol in range(1,self.dataColumnCount+1):
						devNo 			=	self.dataColumnToDevice0Prop1Index[theCol][0]
						stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
						DEV				=	self.DEVICE["{}".format(devNo)]
						theMeasurement	=	DEV["measurement"][stateNo]
						resetTypeIN 	=	str(DEV["resetType"][stateNo])
						fillGaps 		=	str(DEV["fillGaps"][stateNo])
						vFI				=	self.newVFromIndigo[theCol]
						VFItc			=	self.valuesFromIndigo[TTI][theCol]
					
						if theMeasurement=="integrate":
							VFItc[1]	= VFItc[0]
							VFItc[3]	= 0.
							VFItc[2] 	= 0.
							resetType 	=	resetTypeIN
						
							if self.timeBinNumbers[TTI][TBI][6:8] !=self.timeBinNumbers[TTI][max(TBI-1,0)][6:8]:
								if resetType.find("day") >-1:
									VFItc[1]	= 0.
								else:
									dd = datetime.datetime.strptime(self.timeBinNumbers[TTI][TBI][:8],'%Y%m%d')
									if resetType.find("week") >-1:
										if dd.weekday() ==0:	# its monday and a new day
											VFItc[1]	= 0.
									elif resetType.find("month") >-1:
										if dd.day ==1:	# its first day in new month
											VFItc[1]	= 0.
									elif resetType.find("year") >-1:
										if dd.day ==1 and dd.month ==1:	# its first day in new month
											VFItc[1]	= 0.




						elif theMeasurement =="deltaNormHour":
							if TBI != VFItc[4]:	# is this the next bin?
								if  VFItc[2] >0:	# is there data in the last bin, if yes shift, if no keep values of bin with last entries
									VFItc[10]	= VFItc[7]
									VFItc[11]	= VFItc[8]
									VFItc[12]	= VFItc[9]
									VFItc[5]	= VFItc[0]
									VFItc[6]	= VFItc[1]
									VFItc[7]	= VFItc[2]
									VFItc[8]	= VFItc[3]
									VFItc[9]	= VFItc[4]
								VFItc[0]	= 0
								VFItc[1]	= 0
								VFItc[3]	= 0
								VFItc[4]	= 0
								VFItc[5]	= 0
							VFItc[4]	= TBI
							self.timeDataNumbers[TTI][TBI][0]	= max(1,self.timeDataNumbers[TTI][TBI][0])
				
						elif theMeasurement=="delta":
							if TBI != VFItc[4]:	# is this the next bin?
								if (fillGaps =="1" and VFItc[2] >0) or (fillGaps =="0"):
									VFItc[3]	= VFItc[2]
									VFItc[1]	= VFItc[0]
								VFItc[4]	= TBI
								VFItc[0]	= 0
								VFItc[2]	= 0

				
						elif theMeasurement=="deltaMax":
							if TBI != VFItc[4]:	# is this the next bin?
								if (fillGaps =="1" and VFItc[2] >0) or (fillGaps =="0"):
									VFItc[3]	= VFItc[2]
									VFItc[1]	= VFItc[0]
								VFItc[4]	= TBI
								VFItc[0]	= 0
								VFItc[2]	= 0




						elif theMeasurement.find("Consumption") >-1 :
								VFItc[4]	= TBI
								try:
									if resetTypeIN =="0":						resetType="0"
									elif str(resetTypeIN).find("day")>-1:		resetType="day"
									elif str(resetTypeIN).find("week")>-1:		resetType="week"
									elif str(resetTypeIN).find("month")>-1:		resetType="month"
									elif str(resetTypeIN).find("year")>-1:		resetType="year"
									elif str(resetTypeIN).find("Period")>-1:	resetType="Period"
									if str(resetTypeIN).find("NoCost")>-1:		resetType+="NoCost"
								except:
																				resetType="0"

								self.dd=datetime.datetime.now()
								for tti in range(noOfTimeTypes):
									cDPC= self.consumedDuringPeriod["{}".format(theCol)][tti]
									VFItci			=	self.valuesFromIndigo[tti][theCol]
									
									if resetType.find("NoCost")==-1:
										cDPC["currentCostTimeBin"], cDPC["lastCostBinWithData"] = self.getCurrentCostTimeBin("0",theMeasurement)
										if cDPC["currentCostTimeBin"] != cDPC["lastCostTimeBin"]:
											cDPC["valueAtStartOfCostBin"]	= VFItci[1]	# offset for price calc
											cDPC["costAtLastCostBracket"]	= VFItci[0]	# current cost
											cDPC["lastCostTimeBin"] 		= cDPC["currentCostTimeBin"]
									cDPC["valueAtStartOfTimeBin"] = VFItci[1]

									if resetType !="0":
											if resetType.find("Period") >-1:
												xxx= self.getCurrentResetPeriod("0",resetTypeIN[resetType],cDPC["lastResetBin"])
												if xxx != cDPC["lastResetBin"]:
													cDPC["lastResetBin"] =xxx
													cDPC["valueAtStartOfCostBin"]= VFItci[1]	# offset for price calc
													cDPC["costAtLastCostBracket"] 	= 0	# last cost
											else:
												if cDPC["lastDay"] != self.dd.strftime("%d"):
													cDPC["lastDay"] = self.dd.strftime("%d")
												
													if resetType.find("day") >-1:
														cDPC["valueAtStartOfCostBin"]		= VFItci[1]
														cDPC["costAtLastCostBracket"] 		= 0.
													if resetType.find("week") >-1:
														if self.dd.weekday() ==0:	# its monday and a new day
															cDPC["valueAtStartOfCostBin"]	= VFItci[1]
															cDPC["costAtLastCostBracket"] 	= 0.
													if resetType.find("month") >-1:
														if self.dd.day ==1:	# its first day in new month
															cDPC["valueAtStartOfCostBin"]	= VFItci[1]
															cDPC["costAtLastCostBracket"] 	= 0.
													if resetType.find("year") >-1:
														if self.dd.day ==1 and  self.dd.month ==1:	# it is first day in  month 1
															cDPC["valueAtStartOfCostBin"]	= VFItci[1]
															cDPC["costAtLastCostBracket"] 	= 0
									else:
															cDPC["valueAtStartOfCostBin"]	= VFItci[1]	# offset for price calc
															cDPC["costAtLastCostBracket"]	= 0		# last cost
	

						else:
								if TBI != VFItc[4]:	# is this the next bin?
									VFItc[4]	= TBI
									if (theMeasurement.find("average")>-1	or
										theMeasurement.find("sum")>-1		or
										theMeasurement.find("count")>-1		or
										theMeasurement.find("min")>-1		or
										theMeasurement.find("max")>-1		or
										theMeasurement.find("Direction")>-1	):
										VFItc[0]		= 0.
										VFItc[1]		= 0.
										VFItc[2] 		= 0.
										VFItc[3] 		= 0.
									if (theMeasurement.find("first")>-1	or
										theMeasurement.find("last")>-1):
										VFItc[0]		= ""
										VFItc[1]		= 0.
										VFItc[2] 		= 0.
										VFItc[3] 		= 0.
				except  Exception as e:
					self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

				return


			try:
				theCol=0
				self.timeDataNumbers[TTI][TBI][0]+=1
				for  theCol in range(1,self.dataColumnCount+1):
					vFI				=	self.newVFromIndigo[theCol]
					try:
						vFI+=0.
					except:
						continue  # ignore if junk data
					devNo 			=	self.dataColumnToDevice0Prop1Index[theCol][0]
					stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
					DEV				=	self.DEVICE["{}".format(devNo)]
					theMeasurement	=	DEV["measurement"][stateNo]
					theState		=	DEV["state"][stateNo]
					fillGaps 		=	str(DEV["fillGaps"][stateNo])
					resetType 		=	str(DEV["resetType"][stateNo])
					if fillGaps =="0":
						try:
							timeStr=self.lastTimeStampOfDevice[theCol][TTI][0] # drop /-/minutes/hours if needed
							if int(timeStr) - int(self.timeBinNumbers[TTI][TBI])<0:
								#if self.decideMyLog("General"): self.indiLOG.log(20,"  theCol {}".format(theCol)+"    lastTimeStampOfDevice "+timeStr+"    timeBinStart "+ self.timeBinNumbers[TTI][TBI] )
								continue
						except  Exception as e:
							self.indiLOG.log(40,"lastTimeStampOfDevice comparison bad Line '%s' has error='%s'" % (sys.exc_info()[2].tb_lineno, e))
					VFItc = self.valuesFromIndigo[TTI][theCol]
					if theMeasurement == "average" :
						if VFItc[0] =="": VFItc[0]=0.
						VFItc[0] += vFI			# sum of measured values
						VFItc[2] +=1.														# number of measurements
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = VFItc[0]/max(VFItc[2],1.) # here we calculate the average
						VFItc[1] = float(vFI)
						continue

					if theMeasurement == "sum":
						if VFItc[0] =="": VFItc[0]=0.
						VFItc[0] += vFI			# sum of measured values
						VFItc[2] +=1.														# number of measurements
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = VFItc[0]
						VFItc[1] = float(vFI)
						continue

					if theMeasurement == "integrate":
						try:
							VFItc[1] +1.
						except:
							VFItc[1] = 0.
						VFItc[2] +=1.														# number of measurements
						VFItc[3] += vFI
						VFItc[0] = VFItc[3]/VFItc[2] * integrateConstantMinuteHourDay[TTI] + VFItc[1]
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = VFItc[0]								# do not devide by # of measurements
						continue

					if theMeasurement == "count":
						if vFI > 0:
							if int(self.lastTimeStampOfDevice[theCol][TTI][0])  > int(self.timeBinNumbers[TTI][TBI]):				# only count if the event happened in this time period to not count twice if ON was just measured twice
								if VFItc[0] =="": VFItc[0]=0.
								VFItc[0] += 1
								VFItc[2] +=1.
								self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]= VFItc[0]
						VFItc[1]	= vFI
						continue
					
					if theMeasurement == "min":
						if  VFItc[2] == 0.  or VFItc[0] >= vFI :
							VFItc[0]  = vFI
							VFItc[2] +=1.
							self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = VFItc[0]
						continue
					
					if theMeasurement == "max":
						if  VFItc[2] == 0.  or VFItc[0] <= vFI :
							VFItc[0]  = vFI
							VFItc[2] +=1.
							self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]= VFItc[0]
						continue


					
					if theMeasurement == "first":
						if  VFItc[0] == "":
							VFItc[0]  = vFI
							VFItc[2] +=1.
							self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]= VFItc[0]
						continue
					
					if theMeasurement == "last":
						VFItc[0]  = vFI
						VFItc[2] +=1.
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]= VFItc[0]
						continue
				
				

					if theMeasurement== "delta":
						if VFItc[0] =="": VFItc[0]=0.
						VFItc[0] += vFI			# sum of measured values
						VFItc[2] +=1.														# number of measurements
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = VFItc[0]/max(VFItc[2],1.) - VFItc[1]/max(VFItc[3],1) # this value - last value
						continue
				
				
				

					if theMeasurement== "deltaMax":
						if VFItc[0] =="": VFItc[0]=0.
						VFItc[0] += vFI			# sum of measured values
						VFItc[2] +=1.														# number of measurements
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = VFItc[0] - VFItc[1] # this value - last value
						continue
				
				
				
				
					if theMeasurement== "deltaNormHour":
						if self.lastTimeStampOfDevice[theCol][TTI][1] == self.lastTimeStampOfDevice[theCol][TTI][0]: continue
						if self.lastTimeStampOfDevice[theCol][TTI][0] < self.timeBinNumbers[TTI][TBI]: continue
						ttt =self.lastTimeStampOfDevice[theCol][TTI][0]
						if  VFItc[1] == 0 :
							# firs measurement in bin
							VFItc[0] = vFI
							VFItc[1] = time.mktime(time.struct_time((int(ttt[0:4]),int(ttt[4:6]),int(ttt[6:8]),int(ttt[8:10]),int(ttt[10:12]),int(ttt[12:14]),0,0,0)))
							VFItc[4] =TBI
						#last measuremernt in bin
						VFItc[3] = time.mktime(time.struct_time((int(ttt[0:4]),int(ttt[4:6]),int(ttt[6:8]),int(ttt[8:10]),int(ttt[10:12]),int(ttt[12:14]),0,0,0)))
						VFItc[2] =vFI
						slope= 0
						dTime= TBI-VFItc[12]
						if dTime > 0 :
							ddy= VFItc[0]	- VFItc[10]
							ddx= VFItc[1]	- VFItc[11]
							slope=ddy/(max(ddx,0.5))*DeltaNormHOURFactor
							for ii in range(VFItc[12]+1,TBI):
									self.timeDataNumbers[TTI][ii][theCol+dataOffsetInTimeDataNumbers]  = slope
						else:
									self.timeDataNumbers[TTI][max(TBI-1,0)][theCol+dataOffsetInTimeDataNumbers]	= self.timeDataNumbers[TTI][max(TBI-2,0)][theCol+dataOffsetInTimeDataNumbers]
						continue


					if theMeasurement.find("Direction") >-1:
						if theMeasurement.find("North") >-1:
							offset= math.pi/2.
							flip=True  # oregon scientific is clockwise, need to flip the angle (theta =360-theta)
						else:
							offset= 0
							flip=False
						if theMeasurement.find("360") >-1:
							mult=math.pi/180.
						else:
							mult=1.
						theta = self.aveAngle(vFI*mult,VFItc[0],VFItc[2],offset=offset,flip=flip)
						VFItc[2] +=1.
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = theta
						VFItc[0] = theta
						VFItc[1] = vFI
						continue

					
					if (theMeasurement.find("Consumption") >-1 and str(resetType) !="0") :
						VFItc[2] +=1.
						cDPC= self.consumedDuringPeriod["{}".format(theCol)][TTI]
						try:
							if str(resetType).find("NoCost") >-1 :
								VFItc[0] = vFI - cDPC["valueAtStartOfCostBin"] ##+ cDPC["costAtLastCostBracket"]
							else:
								deltaCost, costAtLastCostBracket= self.calcConsumptionCostValue(vFI,cDPC["currentCostTimeBin"],cDPC["valueAtStartOfCostBin"],cDPC["lastCostBinWithData"],VFItc[1],theMeasurement,doPrint=False)
								cDPC["costAtLastCostBracket"] += costAtLastCostBracket
								VFItc[0] = deltaCost+cDPC["costAtLastCostBracket"]
							self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]= VFItc[0]  ## current + lastCost
							VFItc[1] = vFI
						except  Exception as e:
							self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

						continue
		
					self.lastTimeStampOfDevice[theCol][TTI][1]= self.lastTimeStampOfDevice[theCol][TTI][0]
			except  Exception as e:
				self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		return



	########################################	data import 	########################################	########################################	######################################
	########################################	data import 	########################################	########################################	######################################
	########################################	data import 	########################################	########################################	######################################
	########################################	data import 	########################################	########################################	######################################
	########################################	data import 	########################################	########################################	######################################
 
 
	########################################
	def mkCopyOfDB(self):
		if self.liteOrPsql	== "sqlite" and self.originalCopySQL == "copy":
			if self.decideMyLog("SQL"): self.indiLOG.log(20," in mkCopy DB pid={}".format(self.originalCopySQLActive) +"=   flag= {}".format(self.originalCopySQL))
			
			ret, err = self.readPopen("ps -ef | grep indigo_history.sqlite | grep historycp.sqlite | grep -v grep")
			if self.decideMyLog("SQL"): self.indiLOG.log(20," in mkCopy DB xx pid={}".format(ret))
			try:
				if len(x) > 10:
					self.originalCopySQLActive =ret.split(" ")[1]
					return  ## still running
			except:
				pass        
			# is not running, check if there there, now check if too old
			ok=True
			try:
				dt=time.time() - os.path.getmtime(self.indigoSQLliteLogsPath+"indigo_historycp.sqlite")   ## is it older than 2 hours?
				if dt > 60*60*2: ok=False  ## is it older than 2 hours?
				if self.decideMyLog("SQL"): self.indiLOG.log(20," in mkCopy dt={}".format(dt))
			except:    
				ok=False
			if not ok:
				cmd="cp '"+self.indigoSQLliteLogsPath+"indigo_history.sqlite' '"+self.indigoSQLliteLogsPath+"indigo_historycp.sqlite'"
				if self.decideMyLog("SQL"): self.indiLOG.log(20,"cp cmd:" +cmd)
				self.originalCopySQLActive = str(subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).pid)
				if self.decideMyLog("SQL"): self.indiLOG.log(20," in mkCopy DB self.originalCopySQLActive pid={}".format(self.originalCopySQLActive))
				return # too old, create new and wait 
		# finished nothing to do          
		self.originalCopySQLActive = "-1"

	########################################
	def setupSQLDataBatch(self,calledfrom=""):
		##self.sleep(2)
		if self.sqlDynamic.find("batch") !=0: return -1
		if self.dataColumnCount == 0:
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"Updating device/prop from SQL db: no device or variable defined.. skipping updates   ...")
			self.sqlColListStatus = [0]
			self.sqlHistListStatus = [0]
			self.scriptNewDevice  = 0
			self.devicesAdded  = 0
			return 0
		if max(self.sqlColListStatus) == 0:
			self.devicesAdded=0
			self.scriptNewDevice  = 0
			return 0
		if max(self.sqlColListStatus) == 5: return 0


		if not indigo.server.getPlugin("com.perceptiveautomation.indigoplugin.sql-logger").isEnabled():
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql-logger not enabled  disabling calls to SQL-Logger")
			self.sqlDynamic =""
			self.devicesAdded  = 0
			self.scriptNewDevice  = 0
			self.sqlColListStatus = [0 for i in range(self.dataColumnCount+1)]
			return -1

		### check if we need to make a copy of the sqlite db,  only for slow computer where query = regular indigoplot creates blocks
		self.mkCopyOfDB()
		if  (max(self.sqlColListStatus) == 49  or  max(self.sqlColListStatus) ==0)  and self.originalCopySQLActive !="-1": # it is active or not ready
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql import still running  - 1")
			return 0 # still running

		ret, err = self.readPopen("ps -p "+self.pidSQL)
		if ret.find("sqlcmd") > 0:
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql import still running  - 2" )
			return 0

		self.initBy		="SQLstart"
		outCMD = ""
		outCMD += "# start sql {}\n".format(datetime.datetime.now())
		if self.liteOrPsql	 == "psql":
			outCMD += "cd '"+self.indigoSQLliteLogsPath+"' \n"
		else:
			outCMD += "cd '"+self.indigoSQLliteLogsPath+"' \n"
		sqlID  = 0

		maxNumberOfRecords = 10000000
		oldDeviceId =-1
		lastDeviceId =""
		lastProperty =""
		anythingToupdates =0
		devStateList=[]

		if self.dataColumnCount+1 > len(self.sqlLastID):
			for n in range(self.dataColumnCount+1 -len(self.sqlLastID)):
				self.sqlLastID.append("0")
		if self.dataColumnCount+1 > len(self.sqlLastImportedDate):
			for n in range(self.dataColumnCount+1 -len(self.sqlLastImportedDate)):
				self.sqlLastImportedDate.append("201401010101")
		if self.dataColumnCount+1 > len(self.sqlColListStatus):
			for n in range(self.dataColumnCount+1 -len(self.sqlColListStatus)):
				self.sqlColListStatus.append(0)
		if self.dataColumnCount+1 > len(self.sqlColListStatusRedo):
			for n in range(self.dataColumnCount+1 -len(self.sqlColListStatusRedo)):
				self.sqlColListStatusRedo.append(0)

		if self.decideMyLog("SQL"): self.indiLOG.log(10,"setupSQLDataBatch 2 updateslist:{}".format(self.sqlColListStatus))

		for theCol in range (1,self.dataColumnCount+1):
			if self.sqlLastID[theCol] =="": self.sqlLastID[theCol] ="0"
			if self.sqlLastImportedDate[theCol] =="": self.sqlLastImportedDate[theCol] ="201401010101"
			if  self.sqlColListStatus[theCol] <10: 
				continue		# if < 10 either already underway and waiting, or no updates

			
			devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
			stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
			DEV				=	self.DEVICE["{}".format(devNo)]
			theDeviceId		=	str(DEV["Id"])
			theDeviceName	=	DEV["Name"]
			theState		=	DEV["state"][stateNo]
			theMeasurement	=	DEV["measurement"][stateNo]

			if theDeviceId+theState  not in self.sqlImportControl:
				self.sqlImportControl[theDeviceId+theState]= {}
			if str(theCol) not in self.sqlImportControl[theDeviceId+theState]:
				self.sqlImportControl[theDeviceId+theState]["{}".format(theCol)]="x"

			if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done"):
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"setupSQLDataBatch  "+theDeviceId+"-"+theState+".done exists; skip ")
				continue

			if  self.sqlColListStatus[theCol] ==0: 
				for cc in self.sqlImportControl[theDeviceId+theState]:
					try:
						self.sqlColListStatus[int(cc)]=0
					except:
						pass


			if  self.sqlColListStatus[theCol] <10: 
				continue		# if < 10 either already underway and waiting, or no updates

				if self.sqlColListStatus[theCol] == 0 and theDeviceId+theState in self.sqlImportControl:
					for cc in self.sqlImportControl[theDeviceId+theState]:
						try:
							self.sqlColListStatus[int(cc)]=0
						except:
							pass
					del self.sqlImportControl[theDeviceId+theState]




			if self.sqlColListStatusRedo[theCol]	>3:  
				continue # if we have tried it several times, do not do it again.
			
			   
			anythingToupdates +=1

			if  DEV["devOrVar"] == "Dev-":
				tableName = "device_history_"+theDeviceId
				property = theState
				if self.liteOrPsql == "sqlite":
					propertySQL = '['+property.lower()+']'
				else:
					propertySQL = '\\"'+property.lower()+'\\"'

			if  DEV["devOrVar"] == "Var-":
				tableName = "variable_history_"+theDeviceId
				property = "value"
				theState = "value"
				propertySQL = property
			sqlID =0
			if self.sqlColListStatus[theCol] != 50:# this is the force indicator if we submit a new device in config

						# skip this one, if file already "done".
						foundDevProp=0
						for nCol in range(1,theCol):
							if self.sqlColListStatus[nCol] ==0: continue  # skip this one, not done yet, not eligible 
							devNoN			=	self.dataColumnToDevice0Prop1Index[nCol][0]
							stateNoN		=	self.dataColumnToDevice0Prop1Index[nCol][1]
							theDeviceIdN    =   str(self.DEVICE["{}".format(devNoN)]["Id"])
							theDeviceNameN	=	self.DEVICE["{}".format(devNoN)]["Name"]
							theStateN		=	self.DEVICE["{}".format(devNoN)]["state"][stateNoN]

							if theDeviceId == theDeviceIdN and theState == theStateN:
								#if self.sqlColListStatus[nCol] > 0:
									self.sqlLastImportedDate[theCol] 	= self.sqlLastImportedDate[nCol]
									self.sqlLastID[theCol] 				= self.sqlLastID[nCol]
									foundDevProp = 10
									if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState):
										if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql command for col:{}".format(nCol)+"  theCol:{}".format(theCol)+" name-state:"+(theDeviceName+"-"+theState).ljust(50)+" already submitted current file size:  {}".format(os.path.getsize(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState)))
										break
									if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql command for "+(theDeviceName+"-"+theState).ljust(50)+" already submitted")



						if self.sqlColListStatus[theCol] > 100: self.indiLOG.log(10,"sql commands "+theDeviceName+ "[" + theState+"] {}".format(self.sqlColListStatus[theCol]-10)+ " waits")
						if self.sqlColListStatus[theCol] > 600:  #### this is a back stop, in case it hangs.  its a bad situation, need to handle better
							self.indiLOG.log(10,"sql commands waited 10 minutes for "+theDeviceName+ "[" + theState+"] not received yet, re-issuing sql command, if it re-occurs, use SQL-ONLINE/ notify programmer")
							self.sqlColListStatus[theCol] =0
							foundDevProp =0
							if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done")	:	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done")
							if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState) 			:	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState)

						
						if foundDevProp ==10: 
							continue
						
						if self.sqlColListStatus[theCol] >10 and  self.sqlLastID[theCol] !="0":
							if self.decideMyLog("SQL"): self.indiLOG.log(10,"sqlColListStatus > 10, delete  sql/"+theDeviceId+"-"+theState)
							if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done")	:	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done")
							if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState) 			:	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState)
							self.sqlLastID[theCol] ="0"
							for cc in self.sqlImportControl[theDeviceId+theState]:
								self.sqlLastID[int(cc)]=0
					

						# get sqlID  = first number in last line  if it exists and last day
						theTailS = "no SQL file generated yet"
						if os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState ):
							cmd =  "tail -n 1 '"+self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+"'"
							theTailS, err = self.readPopen("ps -p "+self.pidSQL)
							theTail  = theTailS.strip("\n").split(";")
							if self.decideMyLog("SQL"): self.indiLOG.log(10," sql import  devID:{}; state:{}; col:{}; cmd:{};   tails:{}; tail:{}; len(sqlLastImportedDate):{}; sqlLastImportedDate: {} ".format(theDeviceId, theState, theCol, cmd,  theTailS, theTail, len(self.sqlLastImportedDate), self.sqlLastImportedDate) )
							if len(theTail) > 1:												# does it have id and date field?
								self.sqlLastImportedDate[theCol] =theTail[1][:-6]+"000000" 	# replace HH MM with 00 00
								self.sqlLastID[theCol]= theTail[0]							  	# get last sqlid = first word in line
							else:
								theTailS =" nothing exported from SQL  yet"
								self.sqlLastImportedDate[theCol] 	="00000000"+"000000"		# replace HH MM with 00 and drop seconds  set to 0 if nothing found
								self.sqlLastID[theCol] 					="0"					# get last sqlid = first word in line
								if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql importfile file does not have a valid last record: "+ self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+" " + theTailS.strip("\n"))
						else:
							if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql importfile file not created yet, resetting import parameters: "+ self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState)
							self.sqlLastImportedDate[theCol] 	="00000000"+"000000"		# replace HH MM with 00 and drop seconds  set to 0 if nothing found
							self.sqlLastID[theCol] 					="0"					# get last sqlid = first word in line
				

			else:
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"sqlColListStatus ==50, delete  sql/"+theDeviceId+"-"+theState)
				if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done"):	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done") # delete "ready" flag file
				if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState):			os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState) # 
				self.sqlLastID[theCol] ="0"
				theTailS =" no SQL file generated yet"



			self.sqlColListStatus[theCol] =5  #  == sql statement to be added to .sh file
			sqlID = str(self.sqlLastID[theCol])

			if sqlID =="0":
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"sqlID ==0, delete  col:{} sql/{}-{}".format(theDeviceId, theState, theCol))
				if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState) : os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState)


				
			if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done"):	os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done") # delete "ready" flag file
			lout    = "date +\"%H:%M:%S starting      "+theDeviceName+"-"+property+"\":  >>'"+self.userIndigoPluginDir+"sql/sqlcmd.log' \n"
			outCMD += (lout)  # time stamp of sql start

			if self.liteOrPsql !="sqlite":
				select1 = self.liteOrPsqlString +" -t -A -F ';' -c "
				timestamp = " to_char(ts,'YYYYmmddHH24MIss'),  "
				orderby   = " order by id "
			else:  # sqlite
				orderby   = " "
				if self.originalCopySQL =="copy" and sqlID =="0":
					select1 = "/usr/bin/sqlite3 -separator \";\" indigo_historycp.sqlite "
				else:
					select1 = "/usr/bin/sqlite3 -separator \";\" indigo_history.sqlite "
				timestamp= "strftime('%Y%m%d%H%M%S',ts,'localtime') ,"
			sqlCommandText =  "rm '"+self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+property+".done' ;"
			sqlCommandText+=  select1
			sqlCommandText+=  "\" SELECT id, "+ timestamp +propertySQL+" from " + tableName
			sqlCommandText+=  " WHERE "+propertySQL+" IS NOT NULL  AND  ID > {}".format(sqlID) + orderby
			sqlCommandText+=  " LIMIT {}".format(maxNumberOfRecords)+";\""


			postProcessing =  " "
			postProcessing+=  " 2>'"+self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".error'"
			postProcessing+=  " | awk -F';' 'NF>2 && !/data unavailable/ {print}' "  # >=3 parameters only, and skip id no data indicator  ... faster than  than py code
			postProcessing+=  " > '"+self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+property+".sqlOut'"
			postProcessing+=  " && "
			postProcessing+=  self.pythonPath+" '"+self.indigoPath+"Plugins/"+self.pluginName+".indigoPlugin/Contents/Server Plugin/fixSQLoutput.py' " 
			postProcessing+=  "'"+json.dumps( {"fileDir":self.userIndigoPluginDir+"sql/","inputFile":theDeviceId+"-"+property+".sqlout", "outputFile":theDeviceId+"-"+property,"logFile":"sqlFix","startID":str(sqlID)})+"' "
			outCMD += ((sqlCommandText+postProcessing)) # this is the sqllite command
			if self.decideMyLog("SQL"): self.indiLOG.log(10, sqlCommandText+postProcessing) # this is the sql command

			#outCMD += ((" && ls -l -T  '"+self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+property+"' | awk '{print   $5 $8 $10 }' >> '"+self.userIndigoPluginDir+"sql/sqlcmd.log'")) # time stamp and file size  awk removes unwanted columns
			outCMD += ((" && ls -l -T  '"+self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+property+"'  | sed 's%/% %g' | awk '{print $8 \" ended, bytes:\"  $5 \"  id-state:\"  $NF}' >> '"+self.userIndigoPluginDir+"sql/sqlcmd.log'")) # time stamp and file size  awk removes unwanted columns

			outCMD += ((" && echo finished > '"+self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+property+".done' \n\n")) # create sql command finished flag file

			if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql command for col:{}".format(theCol)+"  name-state:"+(theDeviceName+"-"+property).ljust(50)+" starting at record:{}".format(sqlID).rjust(8)+" added; last existing record is: "+ theTailS.strip("\n"))

		if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql commands launched sqlID anythingToupdates {} {}".format(sqlID, anythingToupdates))

		if anythingToupdates ==0:
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql commands ..  nothing to update ...  sqlID: {} anythingToupdates: {}".format(sqlID, anythingToupdates))
			return 0



		
		outCMD += ("echo finished > '"+self.userIndigoPluginDir+"sql/sqlcmd.done' \n")  # all sql commands finished

		ff = self.userIndigoPluginDir+"sql/sqlcmd.sh" 
		f = self.openEncoding(ff,"w")
		f.write(outCMD)
		f.close()
		if self.decideMyLog("SQL"): self.indiLOG.log(10,"\n\n==================\n\n{}\n\n==================\n\n".format(outCMD)) 
		self.sqlNumbOfRecsRead  = 0
		#xx = subprocess.Popen( "sh '"+self.userIndigoPluginDir+"sql/sqlcmd.sh' ", shell=True).pid
		#self.indiLOG.log(10,"pid {}".format(xx, ))
		self.pidSQL = str( subprocess.Popen( "sh '"+self.userIndigoPluginDir+"sql/sqlcmd.sh' ", shell=True).pid )
		self.checkFileExistsErrorMessageCounter =99
		if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql commands launched {} waiting for SQL tasks to end to read data into {} pid={}".format(datetime.datetime.now(), self.pluginName, self.pidSQL))
		return 0

	########################################
	def fixSQLFiles(self,wait=True):
		try:
		#remove doublicates, ie same SQL ID    &     samedate and same value
			d0 = time.time()
			f=self.openEncoding( self.userIndigoPluginDir+"sql/fixSQL.sh" , "w")

			f.write("echo ' '  >> '"+ self.userIndigoPluginDir+"sql/sqlFix.log' \n")  # all sql commands finished
			f.write("echo 'post import fixSQLFiles started at'  >> '"+ self.userIndigoPluginDir+"sql/sqlFix.log' \n")  # all sql commands finished
			f.write("date >> '"+ self.userIndigoPluginDir+"sql/sqlFix.log'  \n")  # all sql commands finished
			for theCol in range (1,self.dataColumnCount+1):
				devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
				stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
				DEV				=	self.DEVICE["{}".format(devNo)]
				theDeviceId		=	str(DEV["Id"])
				theDeviceName	=	DEV["Name"]
				theState		=	DEV["state"][stateNo]
				if  DEV["devOrVar"] == "Dev-":
					property = theState
				if  DEV["devOrVar"] == "Var-":
					property = "value"

				foundDevProp=0
				for nCol in range(1,theCol):
					devNoN			=	self.dataColumnToDevice0Prop1Index[nCol][0]
					stateNoN		=	self.dataColumnToDevice0Prop1Index[nCol][1]
					theDeviceNameN	=	self.DEVICE["{}".format(devNoN)]["Name"]
					theStateN		=	self.DEVICE["{}".format(devNoN)]["state"][stateNoN]
					if theDeviceName == theDeviceNameN and theState == theStateN:
							foundDevProp = 10
							break
				if foundDevProp >0: continue  # skip this one

				if  os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState):
					cmd = self.pythonPath+" '"+self.indigoPath+"Plugins/"+self.pluginName+".indigoPlugin/Contents/Server Plugin/fixSQLoutput.py'  "
					cmd += json.dumps( {"fileDir":self.userIndigoPluginDir+"sql/","inputFile":theDeviceId+"-"+property, "outputFile":theDeviceId+"-"+property,"logFile":"sqlFix"})
					f.write(cmd+" \n")  # all sql commands finished
	
	
			f.write("echo 'post import fixSQLFiles finished  at' >> '"+ self.userIndigoPluginDir+"sql/sqlFix.log' \n")  # all sql commands finished
			f.write("date >> '"+ self.userIndigoPluginDir+"sql/sqlFix.log'  \n")  # all sql commands finished
			f.write("echo 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'  >> '"+ self.userIndigoPluginDir+"sql/sqlFix.log' \n")  # all sql commands finished
			f.close()
			thePID = str(subprocess.Popen( "sh "+self.userIndigoPluginDir+"sql/fixSQL.sh ", shell=True).pid)

			if not wait: return


			for i in range(55): # wait for max 55 seconds before we return or if finished earlier
				self.sleep(1)
				ret, err = self.readPopen("ps -p "+self.pidSQL)
				if ret.find("sql/fixSQL.sh") ==-1:
					if self.decideMyLog("SQL"): self.indiLOG.log(10,"fixSQL import data is finished after: {} seconds".format(time.time()-d0))
					return

			if self.decideMyLog("SQL"): self.indiLOG.log(10,"fixSQL import data  is still running {} seconds".format(time.time()-d0))
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return
	

	########################################
	def readSQLdataBatch(self,calledfrom=""):
		if 	(self.sqlDynamic.find("batch") !=0): return
		
		try:
	
		
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"readSQLdataBatch calledfrom    ..."+calledfrom+ "  sqlHistListStatus{}".format(self.sqlHistListStatus))
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"                               ..."+calledfrom+ "  sqlColListStatus {}".format(self.sqlColListStatus))
			if self.dataColumnCount ==0:
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"Updating device/prop from SQL db: no device or variable defined.. skipping updates   ...")
				self.sqlColListStatus = [0]
				self.sqlHistListStatus = [0]
				self.scriptNewDevice  = 0
				self.devicesAdded  = 0
				return

			self.sqlColListStatus[0] = 0
			self.sqlHistListStatus[0] = 0
			if max(self.sqlColListStatus) ==0 and max(self.sqlHistListStatus) == 0:
				self.initBy ="SQLdone"
				self.scriptNewDevice  = 0
				self.devicesAdded =0
				if self.decideMyLog("SQL"): self.indiLOG.log(10," sql and hist ==0 ...")
				return
			timeNow  = [time.strftime("%Y%m%d%H%M", time.localtime())+"00", time.strftime("%Y%m%d%H", time.localtime())+"0000", time.strftime("%Y%m%d", time.localtime())+"000000"]
			if timeNow[0][11] <"5":
				timeNow[0] =timeNow[0][:11]+"0"+timeNow[0][12:] # replace min digit with 0 if < 5
			else:
				timeNow[0] =timeNow[0][:11]+"5"+timeNow[0][12:]  #   otherwise with 5
		

			foundfirst = 0
			d0 = datetime.datetime.now()
			oldDeviceId =-1
			lastDeviceId =""
			lastProperty =""
			# make a sorted list of files increasing with file size do the smaller ones first save ~ 30% if same device/state is used in different ways
			colSequence=[]

			for theCol in range (1,self.dataColumnCount+1):
				devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
				stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
				DEV				=	self.DEVICE["{}".format(devNo)]
				theDeviceId		=	str(DEV["Id"])
				theState		=	DEV["state"][stateNo]
			   
				if self.sqlColListStatus[theCol] == 0 and theDeviceId+theState in self.sqlImportControl:
					for cc in self.sqlImportControl[theDeviceId+theState]:
						try:
							self.sqlColListStatus[int(cc)]=0
						except:
							pass
					self.sqlImportControl[theDeviceId+theState]={}

				
				if self.sqlColListStatus[theCol] == 0 and self.sqlHistListStatus[theCol] ==0: continue
			
				######### this is the probelm when we have the same import twice,   sqlColListStatus  might  not be set to 0 
				if  self.sqlColListStatus[theCol] >0 and os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done"):
					self.sqlColListStatus[theCol] =0
					if theDeviceId+theState in self.sqlImportControl:
						for cc in self.sqlImportControl[theDeviceId+theState]:
							self.sqlColListStatus[int(cc)] =0
						self.sqlImportControl[theDeviceId+theState]={}
						
					os.remove(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done")

				if self.sqlHistListStatus[theCol] ==0: continue

				if 	DEV["devOrVar"] == "Var-":theState="value"
				if self.sqlColListStatus[theCol] >0:
					if not os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done") and self.sqlHistListStatus[theCol] !=45 : continue
					if not os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState):
						if theDeviceId+"-"+theState in self.sqlErrorCount: 		self.sqlErrorCount[theDeviceId+"-"+theState] +=1
						else:													self.sqlErrorCount[theDeviceId+"-"+theState] =1
						if (self.sqlErrorCount[theDeviceId+"-"+theState])%4 ==0:
							self.indiLOG.log(10,"sql file "+theDeviceId+"-"+theState+".done exist but SQL final output file not created, no data or error (check .. /indigoPlotD/sql/sqlFix.log for errors)  will wait")
						if self.sqlErrorCount[theDeviceId+"-"+theState] >19:
							self.indiLOG.log(10,"sql file "+theDeviceId+"-"+theState+".done exist but SQL final output file not created, does not work, stopping import for that device/state")
							self.sqlColListStatus[theCol]  =0
							self.sqlHistListStatus[theCol] =0
							del self.sqlErrorCount[theDeviceId+"-"+theState]
						continue

				try:
					colSequence.append([theCol, int(os.path.getsize(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState))])
				except:
					colSequence.append([theCol,0])

				if theDeviceId+"-"+theState in self.sqlErrorCount:
					if self.sqlErrorCount[theDeviceId+"-"+theState] >4:
						if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql file "+theDeviceId+"-"+theState+".done  recovered, was finished")
					del self.sqlErrorCount[theDeviceId+"-"+theState]

			if len(colSequence) <1:
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql files .done not found.. still waiting ")
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"{}".format(colSequence))
				return
			colSequence.sort(key=lambda x:x[1])
		
			theDeviceIdOld	=	-1
			theStateOld		=	"x"


			if self.decideMyLog("SQL"): self.indiLOG.log(10,"sql file if done, now reading  it {} {}".format(self.devicesAdded, self.sqlHistListStatus))
	#		for theCol in range (1,self.dataColumnCount+1):
			for ii in range (len(colSequence)):
				theCol =colSequence[ii][0]
				reject2days=0
				if self.sqlColListStatus[theCol] == 0 and self.sqlHistListStatus[theCol] ==0: continue
				atLeastOneRecord =0
				devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
				stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
				DEV				=	self.DEVICE["{}".format(devNo)]
				theDeviceId		=	str(DEV["Id"])
				theDeviceName	=	DEV["Name"]
				theState		=	DEV["state"][stateNo]
				theMeasurement	=	DEV["measurement"][stateNo]
				offset			=	float(DEV["offset"][stateNo])
				multiplier		=	float(DEV["multiplier"][stateNo])
				minValue		=	float(DEV["minValue"][stateNo])
				maxValue		=	float(DEV["maxValue"][stateNo])
				fillGaps		=	str(DEV["fillGaps"][stateNo])
				resetType		=	str(DEV["resetType"][stateNo])
				if resetType.find("0")>-1 or resetType.find("day")>-1: resetTypeX="short"
				else: resetTypeX="long"

				if 	DEV["devOrVar"] == "Var-":theState="value"
				if self.sqlColListStatus[theCol] >0 and not os.path.isfile(self.userIndigoPluginDir+"sql/"+theDeviceId+"-"+theState+".done"):
					if self.decideMyLog("SQL"): self.indiLOG.log(10,"Reading SQL files,col .. not done yet")
					continue
				d1 = datetime.datetime.now()
				SQLHeader = time.time()
				if SQLHeader - self.lastSQLHeader > 60:
					self.indiLOG.log(10,"Reading SQL files,filtering,converting")
					self.indiLOG.log(10,"Elapsed time   Device----- State name-------------------------------   records read/imported/  LastID/  F size--Rej: ValueRng/  Number/ TimeSeq/timeWind/  Data/   col#")
					self.lastSQLHeader = SQLHeader

	#			if len(self.firstBinToFillFromSQL) < theCol:
	#				for ii in range(len(self.firstBinToFillFromSQL), theCol):
	#					self.firstBinToFillFromSQL.append([0 for k in range(noOfTimeTypes)])
			
	#			if len(self.FirstBinDate) < theCol:
	#				for ii in range(len(self.FirstBinDate), theCol):
	#					self.FirstBindatetime.date.append("0000"+"00"+"00"+"0000")  ## YYYY mm dd HHMM

				FirstBinDateX ="0000"+"00"+"00"+"00"+"00"+"00"
				if self.decideMyLog("SQL"): self.indiLOG.log(10," theCol:{}".format(theCol)+"; updatesALL:{}; sqlDynamic:{}; sqlHistListStatus:{}".format(self.updateALL, self.sqlDynamic, self.sqlHistListStatus))
				if  not self.updateALL and self.sqlHistListStatus[theCol] <45  and resetTypeX =="short":		## this mode will only read the last 2 days and leave the other info in day hour min files as they are,
				
					if (self.sqlDynamic.find("batch2Days") ==0):
	#				if (self.sqlDynamic.find("batch2Days") ==0 and (self.sqlLastID[theCol] >0)):
						FirstBinDateY = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y%m%d")+"000000"
	#					if FirstBinDateY > self.sqlLastImportedDate[theCol][:-6] : FirstBinDateY = self.sqlLastImportedDate[theCol][:-6]
						self.FirstBinDate = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y%m%d")+"000000"
						for i in range(noOfTimeTypes):
							FirstBinDateX=FirstBinDateY
							for j in range(self.noOfTimeBins[i]):
								if self.timeBinNumbers[i][j] == FirstBinDateX:
	#							if self.timeDataNumbers[i][j][0] == FirstBinDateX:
									self.firstBinToFillFromSQL[i] = j
									break
						if FirstBinDateX < self.FirstBinDate: self.FirstBinDate=FirstBinDateX
					else:
						self.firstBinToFillFromSQL	=[0 for k in range(noOfTimeTypes)]
						self.FirstBinDate			= self.timeBinNumbers[noOfTimeTypes-1][0]
				else:
					self.firstBinToFillFromSQL	=[0 for k in range(noOfTimeTypes)]
					self.FirstBinDate			= self.timeBinNumbers[noOfTimeTypes-1][0]





				# get data from sql database
			

				if theDeviceIdOld !=theDeviceId or theStateOld != theState or theMeasurement.find("Consumption") >-1:  # not rereading saves ~ 30% if same device/state is used in different ways
					try:
						ignoreSQL =False
						badDataCount=0
						if self.sqlColListStatus[theCol] ==0: ignoreSQL =True
						sqlData ,nrecs, rejectTimeStamp,foundfirst,fSize, atLeastOneRecord,reject2days,badDataCount= self.getsqldataFromFile(theDeviceId,theState,theDeviceName,theMeasurement,theCol,foundfirst,d0,atLeastOneRecord,reject2days,ignoreSQL)
						nRecsInSqlData =len(sqlData)
					except:
						if self.decideMyLog("SQL"): self.indiLOG.log(10,"Convert no records found, try later 1" )
						nRecsInSqlData =0
				
					if nRecsInSqlData ==0 or nrecs==0:
						if self.decideMyLog("SQL"): self.indiLOG.log(10,"Convert no records found, try later 2" )
						continue
				
					# check for bad data, out of range etc:
					sqlData ,rejectNumber ,rejectRange= self.checkSQLData(sqlData,theMeasurement,theState,minValue,maxValue)

				theDeviceIdOld	=	theDeviceId
				theStateOld		=	theState


				self.sqlNumbOfRecsRead += nrecs

				nRecsInSqlData =len(sqlData)
				if nRecsInSqlData ==0:
					if atLeastOneRecord ==1:
						self.sqlColListStatus[theCol]  = 0
						self.sqlHistListStatus[theCol]  = 0
					continue
				self.sqlNumbOfRecsImported += nRecsInSqlData
			
				self.fillHistogramFromSQL(sqlData,1,theCol,theState,fillGaps,resetType,theMeasurement,offset,multiplier,timeNow,d0)

				self.sqlColListStatus[theCol]  = 0
				self.sqlHistListStatus[theCol]  = 0
			
				exeTime = time.strftime("%H:%M:%S", time.localtime())
				if resetType =="0":	xType = ""
				else:				xType = "-{}".format(resetType)[:15].strip("{u':[ ")[:12]
				self.indiLOG.log(10, str(datetime.datetime.now()-d0)+ " "+(theDeviceName+"-"+theState+"-"+theMeasurement+xType).ljust(60)+
					str(nrecs).rjust(8)+"/{}".format(nRecsInSqlData).rjust(8)+"/{}".format(self.sqlLastID[theCol]).rjust(8)+"/{}".format(fSize).rjust(8)+
					"-rejec:{}".format(rejectRange).rjust(8)+"/{}".format(rejectNumber).rjust(8)+"/{}".format(rejectTimeStamp).rjust(8)+"/{}".format(reject2days).rjust(8)+"/{}".format(badDataCount).rjust(6)+"/{}".format(theCol).rjust(6))



			self.cleanData()
			self.clearSqlData(False)
			if self.decideMyLog("SQL"): self.indiLOG.log(10,"SQL imp. {} ... sqlColListStatus: {}".format(datetime.datetime.now(), self.sqlColListStatus) )
			if max(self.sqlColListStatus) == 0 and max(self.sqlHistListStatus) == 0:
				self.updateALL=False

				self.indiLOG.log(10,"SQL imp.  ... finished, total number of records read/imported:             {:>}/{:>}".format(self.sqlNumbOfRecsRead, self.sqlNumbOfRecsImported ) )
				self.sqlNumbOfRecsImported =0
				self.fixSQLFiles(wait=False)
				self.initBy ="SQLdone"
				self.PrintData()
				if self.sqlDynamic.find("-resetTo-") >-1:
					xx=self.sqlDynamic.split("-resetTo-")
					if len(xx)>1:
						self.sqlDynamic = xx[1] #set back to last mode
					else:
						self.sqlDynamic = "batch2Days" #set back to default mode
	

			self.putDeviceParametersToFile(calledfrom="readSQLdataBatch")
		except  Exception as e:
			self.indiLOG.log(10,"Line '{}' has error='{}'".format(sys.exc_info()[2].tb_lineno, e))
		return




	########################################
	def getsqldataFromFile(self, theDeviceId, theState, theDeviceName, theMeasurement, theCol, foundfirst, d0, atLeastOneRecord, reject2days, ignoreSQL):


		sqlData			=[]
		nrecs 			=0
		rejectTimeStamp	=0
		fSize			=0
		atLeastOneRecord =0
		if not (self.sqlDynamic == "online" or self.sqlDynamic.find("batch") ==0):
			return [0, 0], 0, rejectTimeStamp, foundfirst, fSize, atLeastOneRecord
		
		sqlfile = "{}sql/{}-{}".format(self.userIndigoPluginDir, theDeviceId, theState)
		donefile = "{}.done".format(sqlfile)
		errfile = "{}.error".format(sqlfile)
		if ignoreSQL :
			if not os.path.isfile(sqlfile):
				return [0, 0], 0,  rejectTimeStamp, 0, 0, 0, 0
			
			fSize = os.path.getsize(sqlfile)
			foundfirst =1
			if fSize ==0:
				return [0, 0], 0,  rejectTimeStamp, foundfirst, 0, 0, 0
		
		else:
			if os.path.isfile(errfile):
				if os.path.getsize(errfile) == 0:
					os.remove(errfile)
				else:
					msg, err = self.readPopen("cat '"+errfile+"'")
					self.indiLOG.log(10," clearSqlData resetting sql import for {}-{}- Col#={} will retry ... error message is:{}".format(theDeviceName, theState, theCol, msg) )
					if os.path.isfile(donefile): os.remove(donefile)
					self.sqlColListStatus[theCol]=10
					return [0,0],0,rejectTimeStamp,foundfirst,fSize,atLeastOneRecord


			if not os.path.isfile(donefile):
				self.indiLOG.log(10," clearSqlData not done yet:"+theDeviceName+"-"+theState)
				return [0,0] ,0, rejectTimeStamp,foundfirst,0,0,0

			if not os.path.isfile(sqlfile):
				ret, err = self.readPopen("ps -p "+self.pidSQL)
				if ret.find("sqlcmd") > 0:
					self.indiLOG.log(10," SQL still running will just have to wait ")
					return [0,0] ,0, rejectTimeStamp,foundfirst,fSize,0,0
				if self.sqlColListStatus[theCol] > 8: self.indiLOG.log(10,"reading Device/State from SQL db:  {} {}-{} does not exist forcing redo .. ".format(theDeviceName, theDeviceId, theState))
				self.sqlColListStatus[theCol] +=1
				return  [0,0] ,0, rejectTimeStamp,foundfirst,0,0,0

			fSize = os.path.getsize(sqlfile)
			if fSize ==0:
				if subprocess.Popen("ps -p "+self.pidSQL,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0].find("sqlcmd") > 0:
					return [0,0] ,0, rejectTimeStamp,foundfirst,fSize,atLeastOneRecord,0
				if self.sqlColListStatus[theCol] > 8: self.indiLOG.log(10,"reading Device/State from SQL db:  {}-{}-{} is empty       forcing redo  .. ".format(theDeviceName, theState, theMeasurement))
				self.sqlColListStatus[theCol] +=1
				self.indiLOG.log(10,"sql produced file is empty ")
				return  [0,0] ,0, rejectTimeStamp,foundfirst,0,0,0

			foundfirst +=1
			if foundfirst ==1:
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"SQL Data arrived      {} {}-{}-{} sql output file created".format(datetime.datetime.now(), theDeviceName, theState, theMeasurement))

		try:

			reject2days		= 0
			rejectRange 	= 0
			badDataCount=0
		
			# check if file is compleye by checking file size, if it does not change over time it is done ... dont know ho else to check
			self.sleep(0.1)
			nSleep = 0
			for ii in range(100):
				fSize2 = os.path.getsize(sqlfile)
				if fSize2 == fSize:
					if nSleep >0: 
						if self.decideMyLog("SQL"): self.indiLOG.log(10,"SQL Data arrived, file  ready for: {};  file size:  now: {}".format(theCol, fSize2) )
					break  
				nSleep+=1
				self.indiLOG.log(10,"SQL Data arrived, file not ready yet for: {};  file size:  now: {};   was: {}".format(theCol, fSize2, fSize) )

				# file actually not ready still writing ... 
				self.sleep(0.2) 
				fSize = fSize2

			f=self.openEncoding(sqlfile, "r")
			recId = -1
			for line  in f.readlines():
				sqlHistoryData = line.strip("\n").strip(" ").split(";")

				nrecs +=1
				if len(sqlHistoryData)!=3: continue
				lastLine = sqlHistoryData
				try:    newSQLid = int(sqlHistoryData[0])
				except: continue 
				if recId > newSQLid: continue
				recId = newSQLid
				if atLeastOneRecord == 0: atLeastOneRecord =1
				if sqlHistoryData[1] >= self.FirstBinDate:  ## this works with strings as they all have the same length!! and 9>8>7> ...>0
					try:
						sqlData.append([sqlHistoryData[1],float(sqlHistoryData[-1])])# take date field and data field ignore other fields (0=id, 2...x = day/week .. fields last one is data field
						atLeastOneRecord = 2
					except  Exception as e:
						self.indiLOG.log(30,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
						self.indiLOG.log(30,"sql produced file with bad datan dev:{}; state:{}; recs:{};  line:{}".format(theDeviceName, theState, nrecs, line))
				else:
					reject2days +=1
			if atLeastOneRecord ==2:
				self.sqlLastID[theCol]=sqlHistoryData[0]
			if atLeastOneRecord ==1:
				sqlData.append(["20140101010100","0"])
				self.sqlLastID[theCol]=sqlHistoryData[0]
			if atLeastOneRecord ==0:
				sqlData.append(["20140101010100","0"])
				nrecs =0
			f.close()
			
			return sqlData ,nrecs, rejectTimeStamp,foundfirst,fSize,atLeastOneRecord,reject2days,badDataCount

		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
			self.indiLOG.log(40,"sql produced file with bad data ")
			try:    f.close()
			except: pass
			return  [0,0] ,0, rejectTimeStamp,0,0,0,0
		

	
	########################################
	def clearSqlData(self,empty):

		if self.decideMyLog("SQL"): self.indiLOG.log(10," clearSqlData sqlupdates: {}".format(self.sqlColListStatus))

# clean up parameter at end
		if max(self.sqlColListStatus) == 0 or empty:
			self.devicesAdded  = 0
			self.scriptNewDevice  = 0
			
			if  os.path.isfile(self.userIndigoPluginDir+"sql/sqlcmd.done"): 		os.remove(self.userIndigoPluginDir+"sql/sqlcmd.done")
#			if  os.path.isfile(self.userIndigoPluginDir+"sql/sqlcmd.sh"): 		os.remove(self.userIndigoPluginDir+"sql/sqlcmd.sh")
			
			for theCol in range (1,self.dataColumnCount+1):
				devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
				if devNo == 0: continue
				DEV				=	self.DEVICE["{}".format(devNo)]
				stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
				theDeviceId		=	str(DEV["Id"])
				theDeviceName	=	DEV["Name"]
				if 	DEV["devOrVar"] == "Var-":	theState		= "value"
				else: 							theState		= DEV["state"][stateNo]
				if self.sqlColListStatus[theCol] == 0 or empty :
					sqlfile = "{}sql/{}-{}".format(self.userIndigoPluginDir, theDeviceId, theState)
					donefile = "{}.done".format(sqlfile)
					errfile = "{}.error".format(sqlfile)
					if  os.path.isfile(donefile):	os.remove(donefile)
					if  os.path.isfile(errfile):	os.remove(errfile)
					if  os.path.isfile(sqlfile) and empty:	os.remove(sqlfile)


# fix if sql was hanging ...   ie .done was created, and .error was not empty
		for theCol in range (1,self.dataColumnCount+1):
			if self.sqlColListStatus[theCol]!=0 :

				devNo			=	self.dataColumnToDevice0Prop1Index[theCol][0]
				if devNo == 0: continue
				DEV				=	self.DEVICE["{}".format(devNo)]
				stateNo			=	self.dataColumnToDevice0Prop1Index[theCol][1]
				theDeviceId		=	str(DEV["Id"])
				theDeviceName	=	DEV["Name"]
				if 	DEV["devOrVar"] == "Var-":	theState		= "value"
				else: 							theState		= DEV["state"][stateNo]
				sqlfile = "{}sql/{}-{}".format(self.userIndigoPluginDir, theDeviceId, theState)
				donefile = "{}.done".format(sqlfile)
				errfile = "{}.error".format(sqlfile)

				if self.sqlColListStatus[theCol] == 0 and theDeviceId+theState in self.sqlImportControl:
					for cc in self.sqlImportControl[theDeviceId+theState]:
						try:
							self.sqlColListStatus[int(cc)]=0
						except:
							pass
					self.sqlImportControl[theDeviceId+theState]={}


				if  os.path.isfile(donefile)	or os.path.isfile(errfile):
					if os.path.isfile(errfile):
						if os.path.getsize(errfile)>0:
							msg, err = self.readPopen("cat '"+errfile+".error'")
							self.indiLOG.log(10," clearSqlData resetting sql import for "+theDeviceName+"-"+theState+"- Col#={}".format(theCol)+" will retry, error message is:"+msg)
							self.sqlColListStatus[theCol] =10
							if os.path.isfile(donefile) : os.remove(donefile)
						if os.path.isfile(errfile):os.remove(errfile)
					
					if os.path.isfile(donefile):
						if os.path.isfile(sqlfile):
							if os.path.getsize( sqlfile)==0:
								self.indiLOG.log(10," clearSqlData resetting sql import for "+theDeviceName+"-"+theState+"- Col#={}".format(theCol)+" done but no file created, ignoring this device/state")
								if os.path.isfile(donefile) : os.remove(donefile)
								self.sqlColListStatus[theCol] =0



	########################################
	def fillHistogramFromSQL(self,sqlDataIn,sqlIndex, theCol, theState,fillGaps,resetTypeIN,theMeasurement,offsetD,multiplierD,timeNow,d0):
		timetest=[0. for k in range(10)]
		timetest[0] = time.time()
		timetest[1] = time.time()
		try:
			nRecsInSqlData =len(sqlDataIn)
			if theMeasurement.find("Direction") >-1:
				if theMeasurement.find("North") >-1:
					offset= math.pi/2.
					flip=True  # oregon scientific is clockwise, need to flip the angle (theta =360-theta)
				else:
					offset= 0
					flip=False
				if theMeasurement.find("360") >-1:
					mult=math.pi/180.
				else:
					mult=1.


			if nRecsInSqlData > 0:
				try:
					for TTI in range(noOfTimeTypes):
						self.lastTimeStampOfDevice[theCol][TTI][1] = sqlDataIn[nRecsInSqlData-2][0]
						self.lastTimeStampOfDevice[theCol][TTI][0] = sqlDataIn[nRecsInSqlData-1][0]
				except:
					self.lastTimeStampOfDevice[theCol][0][1]="22001231202122"  # this is for 00000000 records
					self.lastTimeStampOfDevice[theCol][0][0]="22001231202122"  # this is for 00000000 records
			try:
				if resetTypeIN =="0": 						resetType="0"
				elif str(resetTypeIN).find("day")>-1:		resetType="day"
				elif str(resetTypeIN).find("week")>-1:		resetType="week"
				elif str(resetTypeIN).find("month")>-1:		resetType="month"
				elif str(resetTypeIN).find("year")>-1:		resetType="year"
				elif str(resetTypeIN).find("Period")>-1:	resetType="Period"
				if   str(resetTypeIN).find("NoCost")>-1:	resetType+="NoCost"
			except:
				resetType="0"


	#		reduce number of bins searched, save ~ 10% of time
			firstRec=[0,0,0]
			firstR=0
			for TTI in range(noOfTimeTypes-1,-1,-1):
				frec = (datetime.date.today() - datetime.timedelta(self.noOfDays[TTI])).strftime("%Y%m%d")
				if  frec < sqlDataIn[0][0][:8]: continue
				for ii in range(firstR, nRecsInSqlData):
					if frec > sqlDataIn[ii][0][:8]: continue
					firstR = ii
					firstRec[TTI] = max(ii-20,0)
					break

			if offsetD==0. and multiplierD ==1.:
				sqlData = sqlDataIn
			else:
				sqlData=[]  ##do this once instead of 3 times save ~ 0.5 seconds for each column
				for nRec in range(nRecsInSqlData):
					sqlData.append(  [sqlDataIn[nRec][0],  (float(sqlDataIn[nRec][sqlIndex])+offsetD)*multiplierD]  )

			sqlIndex =1


			# loop over bin time types (min/hour/day)
			for TTI in range (noOfTimeTypes):					# now fill existing data bins with sql data if exists, do for all three time series(minutes, hours, days)
				
				timetest[3] = time.time()
				timetest[4] = time.time()
				if self.timeBinNumbers[TTI][0] =="" or self.timeBinNumbers[TTI][0] ==" ":
					if self.decideMyLog("SQL"): self.indiLOG.log(30, "timeDataNumbers date field is empty  {}".format(TTI))
					break
				## add starting bin here
				
				if   theMeasurement.find("max") >-1: defValue = -9999999
				elif theMeasurement.find("min") >-1: defValue = +9999999
				else:                                defValue = 0
				
				tempXl				=	[0 for ll in range(self.noOfTimeBins[TTI]+2)]
				tempDatal			=	[defValue for ll in range(self.noOfTimeBins[TTI]+2)]
				tempData 			=	[defValue for ll in range(self.noOfTimeBins[TTI]+2)]
				tempCount			=	[0 for ll in range(self.noOfTimeBins[TTI]+2)]
				lastTBI				=	max(self.firstBinToFillFromSQL[TTI]-22,0)
				errCount 			=	0
				lastValue			=	-999999991.
				firstC 				=	True
				TLast				=	-1
				lastResetBin 		=	-1
				lastDelta			=	-11111111111.
				lastMeasuredValue	=	-1
				TBI					=	0
				if   TTI == 0: subStr=12
				elif TTI == 1: subStr=10			# hours data has 2 less and days has 4 less digits drop last 2 or 4 digits
				elif TTI == 2: subStr=8			# ....
	
				sqlX 				=	sqlData[max(firstRec[TTI]-1,0)][sqlIndex]
				sqlX1				=	sqlX
				sqlX2				=	sqlX1
				lastSQLD			=	"0"

				for nRecordSQL in range(firstRec[TTI],nRecsInSqlData):
					sqlX2 =sqlX1
					sqlX1 =sqlX
					sqlX = sqlData[nRecordSQL][sqlIndex]
					sqlD = sqlData[nRecordSQL][0]
					sqlbin0 = sqlD[:subStrForTimeString[TTI]]
					if sqlbin0  <  self.timeBinNumbers[TTI][0]:
						lastValue = sqlX
						continue

					if sqlbin0 <   (self.timeBinNumbers[TTI][lastTBI])  : continue  # before first timebin


					if sqlbin0 > timeNow[TTI]: # data at NOW date/time? if yes end import
						break
					
				
					self.lastTimeStampOfDevice[theCol][TTI][1] = self.lastTimeStampOfDevice[theCol][TTI][0]
					self.lastTimeStampOfDevice[theCol][TTI][0] = sqlD



######## average, sum
					if theMeasurement =="average" or theMeasurement=="sum":
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if tempCount[TBI] ==0:
								tempData[TBI] 		 =sqlX
							else:
								tempData[TBI] 		+=sqlX
							tempCount[TBI] 	+=1
							lastTBI = TBI
							break
						continue

######## min
					if theMeasurement.find("min")>-1:
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if  tempCount[TBI] == 0: # == empty, always use this value
								tempData[TBI]  = sqlX
							elif sqlX < tempData[TBI]:	## == normal check
								tempData[TBI]  = sqlX
							tempCount[TBI] 	+=1
							lastTBI = TBI
							break
						continue

######## max
					if theMeasurement.find("max")>-1:
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if  tempCount[TBI] == 0: # == empty, always use this value
								tempData[TBI]  = sqlX
							elif sqlX > tempData[TBI]:		 # == normal check
								tempData[TBI]  = sqlX
							tempCount[TBI] 	+=1
							lastTBI = TBI
							break
						continue
######## count
					if theMeasurement.find("count")>-1:
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if sqlX > 0:
								if tempCount[TBI] ==0:
									tempData[TBI] 		=1.0
								else:
									tempData[TBI] 		+=1.0
							tempCount[TBI] 	+=1
							lastTBI = TBI
							break
						continue

### first
					if theMeasurement.find("first")>-1:
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if  tempCount[TBI] == 0: # == empty, always use this value
								tempData[TBI]  = sqlX
							tempCount[TBI] 	+=1
							lastTBI = TBI
							break
						continue

### last
					if theMeasurement.find("last")>-1:
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							tempData[TBI]  = sqlX
							tempCount[TBI] 	+=1
							lastTBI = TBI
							break
						continue

######

######## Direction
					if theMeasurement.find("Direction")>-1:
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if sqlX > +360.: break # junk data
							if sqlX < -180.  :break # junk data
							theta = self.aveAngle(sqlX*mult,tempData[TBI],tempCount[TBI],offset=offset,flip=flip)
							tempCount[TBI] +=1
							tempData[TBI]  = theta
							lastTBI = TBI
							break
						continue

######## Delta
					if theMeasurement== "deltaNormHour":
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							#ttt=time.mktime(strptime(sqlD[:14],"%Y%m%d%H%M%S"))			# this is 50% slower than the next lines..
							if lastSQLD[:8] == sqlD[:8]: # same day?
								ttt = lastttt+int(sqlD[8:10])*3600 +int(sqlD[10:12])*60 +int(sqlD[12:14])-secLast
							else:
								ttt 		= time.mktime(time.struct_time((int(sqlD[0:4]),int(sqlD[4:6]),int(sqlD[6:8]),int(sqlD[8:10]),int(sqlD[10:12]),int(sqlD[12:14]),0,0,0)))
								lastttt		= ttt
								secLast		= int(sqlD[8:10])*3600 +int(sqlD[10:12])*60 +int(sqlD[12:14])
								lastSQLD	= sqlD
							if  tempCount[TBI]	== 0: # == empty, always use this value
								tempData[TBI]	 = sqlX
								tempCount[TBI]	 = ttt
							tempDatal[TBI]		 = sqlX
							tempXl[TBI]			 = ttt
							lastTBI = TBI
							break
						continue


					if theMeasurement=="delta":
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if tempCount[TBI] ==0:
								tempData[TBI] 		 =sqlX
							else:
								tempData[TBI] 		+=sqlX
							tempCount[TBI] 	+=1
							lastTBI = TBI
							break
						continue


					if theMeasurement=="deltaMax":
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							tempCount[TBI] =1
							tempData[TBI]  =sqlX
							lastTBI = TBI
							break
						continue


########  integrate
					if  theMeasurement =="integrate":
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if  tempCount[TBI] 		==0:
								tempData[TBI]  		= sqlX
							else:
								tempData[TBI] 		+=sqlX
							tempCount[TBI] 			+=1
							lastTBI 				= TBI
							break
					
					if  theMeasurement =="integrate1":
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TTI]:	break # this is tommorow bin we are at the end
							if TLast ==-1:
								sql0 = 	sqlData[max(nRecordSQL-1,0)][0]
								Tlast=time.mktime(time.struct_time((int(sql0[0:4]),int(sql0[4:6]),int(sql0[6:8]),int(sql0[8:10]),int(sql0[10:12]),int(sql0[12:14]),0,0,0)))

							ttt=time.mktime(time.struct_time((int(sqlD[0:4]),int(sqlD[4:6]),int(sqlD[6:8]),int(sqlD[8:10]),int(sqlD[10:12]),int(sqlD[12:14]),0,0,0)))
							tempData[TBI]  		+= sqlX * (ttt-Tlast)
							tempCount[TBI] 		+=1
							Tlast				= ttt
							lastTBI 			= TBI
							break




######## Consumption
					if (theMeasurement.find("Consumption")>-1 and str(resetType) !="0") :
						for TBI in range  (lastTBI , self.noOfTimeBins[TTI]):
							try:
								if sqlbin0 >=  (self.timeBinNumbers[TTI][TBI+1]): continue  # after this timebin
							except:
								if TBI  >= self.noOfTimeBins[TBI]:	break # this is tommorow bin we are at the end
							tempCount[TBI] 	+=1
							cDPC= self.consumedDuringPeriod["{}".format(theCol)][TTI]
							if firstC:
								firstC = False
								cDPC["valueAtStartOfTimeBin"]	= sqlX1
								cDPC["valueAtStartOfCostBin"]	= sqlX1
								cDPC["costAtLastCostBracket"]	= 0
								cDPC["testDayHour"]				= "0000"
								cDPC["lastResetBin"]			=-1
								cDPC["currentCostTimeBin"]		= 0
								cDPC["lastCostTimeBin"]			=-2
								cDPC["lastDay"]					="-2"
								cDPC["lastCostBinWithData"]		= 0

							if lastTBI != TBI:
								cDPC["valueAtStartOfTimeBin"] = sqlX1

							if (sqlD[6:10]) !=cDPC["testDayHour"]:	# quick check if we should do anything
								cDPC["testDayHour"] = (sqlD[6:10])	# yes it is possible should reduce the number of test by factor of 100
								if resetType.find("NoCost") ==-1:
									cDPC["currentCostTimeBin"], cDPC["lastCostBinWithData"] = self.getCurrentCostTimeBin(sqlD,theMeasurement)
									
									if cDPC["currentCostTimeBin"] 	!= cDPC["lastCostTimeBin"]:
									### works										if theCol == 9 and TTI ==1: self.indiLOG.log(30," changing cost data "+sqlD+" {}".format(theCol)+"   {}".format(TTI)+"   {}".format(cDPC["currentCostTimeBin"])+"--{}".format(cDPC["lastCostTimeBin"]))
										cDPC["lastCostTimeBin"] 	= cDPC["currentCostTimeBin"]
										cDPC["valueAtStartOfCostBin"]= sqlX1	# offset for price calc
										if tempData[lastTBI] =="": tempData[lastTBI]=0.
										cDPC["costAtLastCostBracket"]= tempData[lastTBI]	# current cost


								if resetType.find("Period")>-1:
									try:
										xxx= self.getCurrentResetPeriod(sqlD,resetTypeIN[resetType],cDPC["lastResetBin"])
										if xxx != cDPC["lastResetBin"]:
											cDPC["lastResetBin"] =xxx
											cDPC["valueAtStartOfCostBin"]= sqlX1	# offset for price calc
											cDPC["costAtLastCostBracket"]= 0	# last cost
									except  Exception as e:
										self.indiLOG.log(40,"Exception: Line '%s' has error='%s'" % (sys.exc_info()[2].tb_lineno, e))
										break
								else:
									if (sqlD[6:8]) !=cDPC["lastDay"]:
										cDPC["lastDay"]= (sqlD[6:8])
										if resetType.find("day") >-1:
												cDPC["valueAtStartOfCostBin"]= sqlX1	# offset for price calc
												cDPC["costAtLastCostBracket"]= 0		# last cost
										else:
											self.dd = datetime.datetime.strptime(sqlD[:10],'%Y%m%d%H')
											if resetType.find("week") >-1:
												if self.dd.weekday() ==0:	# its monday and a new day
													cDPC["valueAtStartOfCostBin"]= sqlX1	# offset for price calc
													cDPC["costAtLastCostBracket"]= 0		# last cost
											elif resetType.find("month") >-1:
												if self.dd.day ==1:	# its first day in new month
													cDPC["valueAtStartOfCostBin"]= sqlX1	# offset for price calc
													cDPC["costAtLastCostBracket"]= 0		# last cost
											elif resetType.find("year") >-1:
												if self.dd.day ==1 and self.dd.month ==1:	# its first day in new month
													cDPC["valueAtStartOfCostBin"]= sqlX1	# offset for price calc
													cDPC["costAtLastCostBracket"]= 0		# last cost


							if resetType.find("NoCost") >-1 :
								tempData[TBI] = sqlX - cDPC["valueAtStartOfCostBin"]
							else:
								xxxx=False
#									if theCol==8 and TTI ==1: xxxx=True
								deltaCost, costAtLastCostBracket= self.calcConsumptionCostValue(sqlX,cDPC["currentCostTimeBin"],cDPC["valueAtStartOfCostBin"],cDPC["lastCostBinWithData"],sqlX1,theMeasurement,doPrint=xxxx)
								cDPC["costAtLastCostBracket"] += costAtLastCostBracket
								tempData[TBI] = deltaCost+cDPC["costAtLastCostBracket"]
					

							if cDPC["valueAtStartOfTimeBin"]*0.9 > sqlX : ## a manual reset seemed to have happened..
								cDPC["valueAtStartOfCostBin"]= sqlX1	# offset for price calc
								cDPC["valueAtStartOfTimeBin"]= sqlX1	# offset for price calc
							lastTBI = TBI
							break
							#### end of consumption

							
							
					lastTBI = TBI
					continue
					##### end of timbinindex loop


				### end loop over sql input


# build averages  and fill holes copy to timeDataNumbers
				#  find last bin..
				lastTimeBin=self.noOfTimeBins[TTI]
				for TBI in range  (self.noOfTimeBins[TTI]-1, self.firstBinToFillFromSQL[TTI]-1,-1):
					if ((self.timeBinNumbers[TTI][TBI])) <= timeNow[TTI]:
						lastTimeBin=min(TBI+1,self.noOfTimeBins[TTI])
						break
				VFItc = self.valuesFromIndigo[TTI][theCol]
				
				if  theMeasurement.find("average") >-1  :
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tN1 = tN
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]	= tD/max(tN,1)
						VFItc[0]			= tD
						VFItc[1]			= tD1
						VFItc[2]			= tN
						self.timeDataNumbers[TTI][TBI][0]				= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[4] = TBI
					continue

				elif  theMeasurement.find("Direction") >-1  :
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tN1 = tN
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]			= tD/max(tN,1)
						VFItc[0]			= tD
						VFItc[1]			= tD1
						VFItc[2]			= tN
						self.timeDataNumbers[TTI][TBI][0]				= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[4] = TBI
					continue

				elif theMeasurement.find("sum") >-1  :
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tN1 = tN
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]			= tD
						VFItc[0]			= tD
						VFItc[1]			= tD1
						VFItc[2]			= tN
						self.timeDataNumbers[TTI][TBI][0]				= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[4] = TBI
					continue


				elif theMeasurement.find("first") >-1  :
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tN1 = tN
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]			= tD
						VFItc[0]			= tD
						VFItc[1]			= tD1
						VFItc[2]			= tN
						self.timeDataNumbers[TTI][TBI][0]				= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[4] = TBI
					continue


				elif theMeasurement.find("last") >-1  :
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tN1 = tN
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]			= tD
						VFItc[0]			= tD
						VFItc[1]			= tD1
						VFItc[2]			= tN
						self.timeDataNumbers[TTI][TBI][0]				= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[4] = TBI
					continue



				elif theMeasurement.find("min") >-1 or theMeasurement.find("max") >-1   :
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tN1 = tN
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]			= tD
						VFItc[0]			= tD
						VFItc[1]			= tD1
						VFItc[2]			= tN
						self.timeDataNumbers[TTI][TBI][0]				= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[4] = TBI
					continue


				elif  theMeasurement.find("count") >-1  :
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tN1 = tN
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]			= tD
						VFItc[0]			= tD
						VFItc[1]			= tD1
						VFItc[2]			= tN
						self.timeDataNumbers[TTI][TBI][0]				= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[4] = TBI
					continue


				elif theMeasurement == "delta":
					tN1	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tD1	= tempData[self.firstBinToFillFromSQL[TTI]]
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tN	= tempCount[TBI]
						tD	= tempData[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]	= tD/ max(tN,1) - tD1/max(tN1,1)
						self.timeDataNumbers[TTI][TBI][0]		= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[0]	= tD
					VFItc[1]	= tD1
					VFItc[2]	= tN
					VFItc[3]	= tN1
					VFItc[4]	= TBI
					continue

				elif theMeasurement == "deltaMax":
					tN1	= tempCount[self.firstBinToFillFromSQL[TTI]]
					tD1	= tempData[self.firstBinToFillFromSQL[TTI]]
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tN	= tempCount[TBI]
						tD	= tempData[TBI]
						if fillGaps=="1" and tN ==0: tD = tD1;tN=tN1
						self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]	= tD/ max(tN,1) - tD1/max(tN1,1)
						self.timeDataNumbers[TTI][TBI][0]		= max(tN,self.timeDataNumbers[TTI][TBI][0])
						tD1	= tD
						tN1 = tN
					VFItc[0]	= tD
					VFItc[1]	= tD1
					VFItc[2]	= tN
					VFItc[3]	= tN1
					VFItc[4]	= TBI
					continue


				elif theMeasurement == "deltaNormHour":
					fBin= self.firstBinToFillFromSQL[TTI]
					VFItc[5] = tempData [max(fBin-1,0)]
					VFItc[6] = tempCount[max(fBin-1,0)]
					VFItc[7] = tempDatal[max(fBin-1,0)]
					VFItc[8] = tempXl  [max(fBin-1,0)]
					VFItc[9]= max(fBin-1,0)

					VFItc[10] = tempData [max(fBin-2,0)]
					VFItc[11] = tempCount[max(fBin-2,0)]
					VFItc[12] = max(fBin-2,0)

					for TBI in range  (fBin,lastTimeBin):
						if tempCount[TBI]>0 :
							dTime= TBI-VFItc[12]
							if dTime > 0 :
								ddy= tempData [TBI] - VFItc[10]  # for max
								ddx= tempCount[TBI] - VFItc[11]
								slope=ddy/(max(ddx,0.5))*DeltaNormHOURFactor
								for ii in range(VFItc[12]+1,TBI):
									self.timeDataNumbers[TTI][ii][theCol+dataOffsetInTimeDataNumbers]  = slope
							
								VFItc[12] = VFItc[9]
								VFItc[11] = VFItc[8]
								VFItc[10] = VFItc[7]
								
								VFItc[5] = tempData [TBI]
								VFItc[6] = tempCount[TBI]
								VFItc[7] = tempDatal[TBI]
								VFItc[8] = tempXl   [TBI]
								VFItc[9] = TBI
							else:
								self.timeDataNumbers[TTI][max(TBI-1,0)][theCol+dataOffsetInTimeDataNumbers]	= self.timeDataNumbers[TTI][max(TBI-2,0)][theCol+dataOffsetInTimeDataNumbers]
							
							self.timeDataNumbers[TTI][TBI][0]					= max(1,self.timeDataNumbers[TTI][TBI][0])
					VFItc[0] = tempData [TBI]
					VFItc[1] = tempCount[TBI]
					VFItc[2] = tempDatal[TBI]
					VFItc[3] = tempXl   [TBI]
					VFItc[4] = TBI
					self.lastTimeStampOfDevice[theCol][TTI][0]					= sqlD[:14]
					self.lastTimeStampOfDevice[theCol][TTI][1]					= sqlD[:14]
#									+ "   lastTimeBin: {}".format(lastTimeBin)
#									+"   noOfTimeBins:"+  str(self.noOfTimeBins[TTI])
#									+"  1: {}".format(VFItc[1])
#									+"  2: {}".format(VFItc[2])
#									+"  3: {}".format(VFItc[3])
#									+"  4: {}".format(VFItc[4])
#									+"  5: {}".format(VFItc[5])
#									+"  6: {}".format(VFItc[6])
#									+"  7: {}".format(VFItc[7]),1)
					continue




				elif theMeasurement=="integrate":
					TBI = self.firstBinToFillFromSQL[TTI]
					TBI1 = max(TBI-1,0)
					VFItc[0] = self.timeDataNumbers[TTI][TBI1][theCol+dataOffsetInTimeDataNumbers]
					VFItc[2] = 0
					VFItc[3] = 0
					VFItc[1]  = self.timeDataNumbers[TTI][TBI1][theCol+dataOffsetInTimeDataNumbers]
					lastDay = self.timeBinNumbers[TTI][TBI1][:8]
					tD	= tempData[self.firstBinToFillFromSQL[TTI]]
					tD1	= tD
					tN	= tempCount[self.firstBinToFillFromSQL[TTI]]
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						VFItc[2] = tN
						VFItc[3] = tD
						if self.timeBinNumbers[TTI][TBI][6:8] !=lastDay:
							lastDay= self.timeBinNumbers[TTI][TBI][6:8]
							if resetType.find("day") >-1:
								VFItc[1]=0
							else:
								dd = datetime.datetime.strptime(self.timeBinNumbers[TTI][TBI][:8],'%Y%m%d')
								if resetType.find("week") >-1:
									if dd.weekday() ==0:	# its monday and a new day
										VFItc[1] =0
								elif resetType.find("month") >-1:
									if dd.day ==1:	# its first day in new month
										VFItc[1] =0
								elif resetType.find("year") >-1:
									if dd.day ==1 and dd.month ==1:	# its first day in new month
										VFItc[1] =0
					
						if tN >0:
							self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = (tD/tN)*(TBI - TBI1)  * integrateConstantMinuteHourDay[TTI] + VFItc[1]
							TBI1 = TBI
						else:
							self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = VFItc[1]
							VFItc[3] =0.
						VFItc[1] = self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]
						VFItc[0] = self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers]
						self.timeDataNumbers[TTI][TBI][0]	   = max(tempCount[TBI],self.timeDataNumbers[TTI][TBI][0])
					VFItc[4] = TBI
					continue

				elif theMeasurement=="integrate1":
					TBI = self.firstBinToFillFromSQL[TTI]
					TBI1 = max(TBI-1,0)
					self.timeDataNumbers[TTI][TBI1][theCol+dataOffsetInTimeDataNumbers] = self.timeDataNumbers[TTI][max(TBI1-1,0)][theCol+dataOffsetInTimeDataNumbers]
					try:
						self.timeDataNumbers[TTI][TBI1][theCol+dataOffsetInTimeDataNumbers] = float( self.timeDataNumbers[TTI][TBI1][theCol+dataOffsetInTimeDataNumbers] )
					except:
						self.timeDataNumbers[TTI][TBI1][theCol+dataOffsetInTimeDataNumbers] = 0.
					lastDay = self.timeBinNumbers[TTI][TBI1][:8]
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						tD	= tempData[TBI]
						tN	= tempCount[TBI]
						yLast= float(self.timeDataNumbers[TTI][TBI1][theCol+dataOffsetInTimeDataNumbers])
						if self.timeBinNumbers[TTI][TBI][6:8] !=lastDay:
							lastDay= self.timeBinNumbers[TTI][TBI][6:8]
							if resetType.find("day") >-1:
								yLast=0.
							else:
								dd = datetime.datetime.strptime(self.timeBinNumbers[TTI][TBI][:8],'%Y%m%d')
								if resetType.find("week") >-1:
									if dd.weekday() ==0:	# its monday and a new day
										yLast =0.
								elif resetType.find("month") >-1:
									if dd.day ==1:	# its first day in new month
										yLast =0.
								elif resetType.find("year") >-1:
									if dd.day ==1 and dd.month ==1:	# its first day in new month
										yLast =0.
					
						if tN >0:
							self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = tD  * integrateConstantMinuteHourDay[TTI] + yLast
							TBI1 = TBI
						self.timeDataNumbers[TTI][TBI][0]	   = max(tN,self.timeDataNumbers[TTI][TBI][0])
					VFItc[4] = TBI
					continue

				elif theMeasurement.find("Consumption") >-1 :
					self.timeDataNumbers[TTI][TBI][theCol+dataOffsetInTimeDataNumbers] = tempData[:]
					for TBI in range  (self.firstBinToFillFromSQL[TTI],lastTimeBin):
						self.timeDataNumbers[TTI][TBI][0]	= max(tempCount[TBI],self.timeDataNumbers[TTI][TBI][0])
					VFItc[4] = TBI
					continue

# exception from very start
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

		return


	########################################
	def aveAngle(self,thetaNewMeasurement,thetaCurrentAverage,nMeasurement,offset=0.,flip=False):
		if thetaCurrentAverage =="": thetaCurrentAverage=0.
		if flip :
			thetaNewMeasurement= math.pi*2.-thetaNewMeasurement
		if offset !=0.:
			thetaNewMeasurement=thetaNewMeasurement+offset
			if thetaNewMeasurement >= math.pi*2.: thetaNewMeasurement =thetaNewMeasurement-math.pi*2.
		if nMeasurement ==0:	return thetaNewMeasurement
		n=nMeasurement+1.
		d = thetaNewMeasurement - thetaCurrentAverage
		if d == 0.: return thetaNewMeasurement
		if d>=0:
			if d <= math.pi:		thetaResult = thetaCurrentAverage +  (thetaNewMeasurement -thetaCurrentAverage) /n
			else:			thetaResult = thetaCurrentAverage -  ((math.pi*2.+thetaCurrentAverage)-thetaNewMeasurement)/n
			if thetaResult < 0:	thetaResult = thetaResult +math.pi*2.
		if d < 0:
			if d >= -math.pi:	thetaResult = thetaCurrentAverage +  (thetaNewMeasurement -thetaCurrentAverage) /n
			else:			thetaResult = thetaCurrentAverage +  ((math.pi*2.+thetaNewMeasurement)-thetaCurrentAverage)/n
			if thetaResult < 0:	thetaResult = thetaResult +math.pi*2.
		if thetaResult >= math.pi*2.:	return thetaResult-math.pi*2.
		return thetaResult

	########################################
	def checkSQLData (self, SQLtemp,theMeasurement,theState,minValue,maxValue):


		sqlData = []
		sqlData.append(SQLtemp[0])
		nrecs 		= len(SQLtemp)
		
		rejectRange	= 0
		blibCount 	= 0
		lastData	= 0
		rejectNumber= 0

		if nrecs <2 :return sqlData, rejectNumber, rejectRange

		for nSQL in range (1,nrecs-1):
			nSQLm1= max(nSQL-1,1)
			nSQLm2= max(nSQL-2,1)
			nSQLp1= min(nSQL+1,nrecs-1)
			nSQLp2= min(nSQL+2,nrecs-1)
			x = SQLtemp[nSQL][1]
			if theState == "curEnergyLevel"or (theState == "accumEnergyTotal"):
				if (                 (x < 0.) or  (abs(x  - SQLtemp[nSQLm1][1]) > self.DATAlimitseConsumption)) :
					#if self.decideMyLog("SQL"): self.indiLOG.log(30," bad data ... Timestamp " + SQLtemp[nSQL][0].rjust(10) +" data:{}".format(x).rjust(18)+ " last:{}".format(SQLtemp[nSQLm1][1]).rjust(18))
					SQLtemp[nSQL][1] = SQLtemp[nSQLm1][1]
					rejectRange +=1
					continue
					
			if  (x < minValue) or ( x> maxValue)   :
				rejectRange +=1
				SQLtemp[nSQL][1] = SQLtemp[nSQLm1][1]
				if self.decideMyLog("SQL"): self.indiLOG.log(10,"                                    data out of min/max range: " + SQLtemp[nSQL][0] +" {}".format(x))
				continue


		
			if theState != "accumEnergyTotal":
				sqlData.append(SQLtemp[nSQL])
				continue
				
			# energy reset or bad dat?
			# more than 10% down, must be 3 in a row and less than 5
			else:
				if SQLtemp[nSQL][1] < SQLtemp[nSQLm1][1]:
					if SQLtemp[nSQL][1] < 5 :
						if SQLtemp[min(nrecs-1,nSQL+1)][1] < SQLtemp[nSQLm1][1]:
							if SQLtemp[min(nrecs-1,nSQL+2)][1] < SQLtemp[nSQLm1][1]:
								if SQLtemp[min(nrecs-1,nSQL+3)][1] < SQLtemp[nSQLm1][1]:  # use min() to not go beyond end of data
									#if self.decideMyLog("SQL"): self.indiLOG.log(30, "1-consumption reset  Timestamp " + SQLtemp[nSQL][0].rjust(10) +" state"+ theState+" nSQL/nrecs{}".format(nSQL)+"/{}".format(nrecs) +" data:{}".format(SQLtemp[nSQL][1]).rjust(15)+" data-1:{}".format(SQLtemp[nSQLm1][1]).rjust(15)+ " data+1:{}".format(SQLtemp[nSQLp1][1]).rjust(15)+" data+2:{}".format(SQLtemp[nSQLp2][1]).rjust(15))
									sqlData.append(SQLtemp[nSQL])
									continue

					if SQLtemp[nSQL][1] > 0.9 * SQLtemp[nSQLm1][1]:
						SQLtemp[nSQL][1]=SQLtemp[nSQLm1][1] # set to last number
						sqlData.append(SQLtemp[nSQL])
						blibCount =0
						continue


					blibCount +=1
					if blibCount > 3:
						blibCount =0
						sqlData.append(SQLtemp[nSQL])
						continue
					else:
						SQLtemp[nSQL][1]=SQLtemp[nSQLm1][1] # set to last number
						rejectNumber +=1
						continue

			
				# next value > last, good data?
				else :
					if SQLtemp[nSQL][1] < 1.05 * SQLtemp[nSQLm1][1]:
						sqlData.append(SQLtemp[nSQL])
						blibCount =0
						continue
						
					if SQLtemp[nSQL][1] > 1.5 * SQLtemp[nSQLm1][1] and blibCount < 3 and SQLtemp[nSQLm1][1] > 0.5:
						SQLtemp[nSQL][1]=SQLtemp[nSQLm1][1] # set to last number
						blibCount +=1
						rejectNumber +=1
						continue
						
					if SQLtemp[nSQL+1][1] <= SQLtemp[nSQLm1][1]:
						SQLtemp[nSQL][1]=SQLtemp[nSQLm1][1] # set to last number
						rejectNumber +=1
						continue

					sqlData.append(SQLtemp[nSQL])
					blibCount = 0
					continue

		sqlData.append(SQLtemp[nrecs-1])

		if self.decideMyLog("SQL"): self.indiLOG.log(10, "nrec out of  check {}".format(nrecs+1).rjust(5) + " rejects{}".format(rejectNumber).rjust(5) )

		return sqlData, rejectNumber, rejectRange
	
	

	########################################	utilities   	########################################	########################################	######################################
	####################  utilities -- end #######################
	

	########################################
	def padzero(self,instring):   #   integer/string 2 --> string  "02" ...   integer/string 10 -->  string "10"
		instring= str(instring)
		if len(instring)<2: 	return "0"+instring			# one digit, add 0
		if instring[0:1] ==" ":	return "0"+instring[1:]		# 1 digit return 0 and 2. letter
		return							   instring			#already 2 digits

	########################################
	def testFonts(self):

		#get gnuPlotVersion
		cmd="'"+self.gnuPlotBinary+"' --version"
		ret, err = self.readPopen(cmd)
		self.gnuVersion=""
		if ret.find("patchlevel") > -1:
			try:
				self.gnuVersion= ret.split()[1]
			except:
				self.indiLOG.log(30,' gnuplot is not installed '+ret)
				return
		else:
			self.indiLOG.log(30,' gnuplot is not installed '+ret)
			return
		

		try:
			f=self.openEncoding( self.userIndigoPluginDir+"temp/test.gnu", "w")
			ret=f.write('set terminal png enhanced medium  font "/Library/Fonts/Arial Unicode.ttf" 12   size 800,350 dashlength 0.5 \n')
			f.close()
		except:
			self.indiLOG.log(40,"fatal error, can not create files in indigoplot directory, stopping ")
			self.quitNOW = "fatal error, can not create files in indigoplot directory, stopping"
			return
		if self.gnuORmat =="mat": return  # no more if we do matplot
		cmd="'"+self.gnuPlotBinary+"'  '"+self.userIndigoPluginDir+"temp/test.gnu'"
		ret, err = self.readPopen(cmd)
		if len(err) > 10:
			self.indiLOG.log(40,' gnuplot is not (yet) installed with proper font support, please select option "(re)INSTALL gnuplot.. or TrueTypeFonts will not be available or wait until install is finished"')

		try:
			os.remove(self.userIndigoPluginDir+"temp/test.gnu")  # and clean up
		except:
			pass
		return

	########################################
	def procUPtime(self,process):

		CPUtime, err = self.readPopen("ps -ef | grep '"+process+"' | grep -v grep | awk '{print $7}'")
		#501   672   655   0 12:04PM ??         1:27.53 /Library/Application Support/Perceptive Automation/Indigo 6/IndigoPluginHost.app/Contents/MacOS/IndigoPluginHost -p1176 -fSQL Logger.indigoPlugin
		if len(CPUtime) < 4 or len(CPUtime) > 10: return -1 # not found
		else:
			temp=CPUtime.strip("\n").split(":")
			try:
				if len(temp) ==3: CPUtime = float(temp[0])*60*60 + float(temp[1])*60 +float(temp[2]) # hours:minutes:seconds.milsecs
				if len(temp) ==2: CPUtime =                        float(temp[0])*60 +float(temp[1]) # minutes:seconds.milsecs
				if len(temp) ==1: CPUtime =                                           float(temp[0]) # seconds:milsecs
			except:
				CPUtime =0.
			## cputime in seconds.. require 100 seconds cpu consumption to be up long enough
		self.indiLOG.log(10,"sql logger used {}".format(CPUtime)+" secs CPU so far")
		return CPUtime




##### execute triggers:

######################################################################################
# Indigo Trigger Start/Stop
######################################################################################

	def triggerStartProcessing(self, trigger):
		self.triggerList.append(trigger.id)
	
	def triggerStopProcessing(self, trigger):
			if trigger.id in self.triggerList:
				self.triggerList.remove(trigger.id)

	#def triggerupdatesd(self, origDev, newDev):
	#	self.logger.log(2, "<<-- entering triggerupdatesd: %s" % origDev.name)
	#	self.triggerStopProcessing(origDev)
	#	self.triggerStartProcessing(newDev)


######################################################################################
# Indigo Trigger Firing
######################################################################################

	def triggerEvent(self, eventId):
		for trigId in self.triggerList:
			trigger = indigo.triggers[trigId]
			if trigger.pluginTypeId == eventId:
				indigo.trigger.execute(trigger)
		return


####-------------------------------------------------------------------------####
	def readPopen(self, cmd):
		try:
			ret, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
			return ret.decode('utf_8'), err.decode('utf_8')
		except Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))

####-------------------------------------------------------------------------####
	def openEncoding(self, ff, readOrWrite):
		try:
			if sys.version_info[0]  > 2:
				return open( ff, readOrWrite, encoding="utf-8")
			else:
				return codecs.open( ff ,readOrWrite, "utf-8")
		except	Exception as e:
			self.indiLOG.log(40,"decideMyLog in Line '%s' has error='%s'" % (sys.exc_info()[2].tb_lineno, e))
		return ""

	####-----------------	 ---------
	def completePath(self,inPath):
		if len(inPath) == 0: return ""
		if inPath == " ":	 return ""
		if inPath[-1] !="/": inPath +="/"
		return inPath


########################################
########################################
####-----------------  logging ---------
########################################
########################################

			
	####-----------------	 ---------
	def decideMyLog(self, msgLevel):
		try:
			if msgLevel	 == "all" or "all" in self.debugLevel:	 return True
			if msgLevel	 == ""	 and "all" not in self.debugLevel:	 return False
			if msgLevel in self.debugLevel:							 return True
			return False
		except  Exception as e:
			self.indiLOG.log(40,"{}line#,Module,Statement:{}".format(e, traceback.extract_tb(sys.exc_info()[2])[-1][1:]))
		return False


##################################################################################################################
####-----------------  valiable formatter for differnt log levels ---------
# call with: 
# formatter = LevelFormatter(fmt='<default log format>', level_fmts={logging.INFO: '<format string for info>'})
# handler.setFormatter(formatter)
class LevelFormatter(logging.Formatter):
	def __init__(self, fmt=None, datefmt=None, level_fmts={}, level_date={}):
		self._level_formatters = {}
		self._level_date_format = {}
		for level, format in level_fmts.items():
			# Could optionally support level names too
			self._level_formatters[level] = logging.Formatter(fmt=format, datefmt=level_date[level])
		# self._fmt will be the default format
		super(LevelFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

	def format(self, record):
		if record.levelno in self._level_formatters:
			return self._level_formatters[record.levelno].format(record)

		return super(LevelFormatter, self).format(record)



