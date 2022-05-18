import sys,os
from datetime import datetime
try:
	unicode("x")
except:
	unicode = str


#print "hello"
fileDir = sys.argv[1]
logFile = fileDir+"fixpy"
logF=open(logFile+".log","a")


logF.seek(0,2)
size = logF.tell()
#print " size "+str(size)


if size > 500000:
	try:
		logF.close()
		try:			# error if it does not exit
			os.remove( logFile+".1.log" )
		except:
			pass
		try:			# error if it does not exit
			os.rename( logFile+".log", logFile+".1.log")
		except:
			pass
		logF= open( logFile+".log" , "a")
	except:
		pass


logF.write(u"\nchecking py-restore files in"+fileDir+" "+str(datetime.now())+"\n")

for fname in os.listdir(fileDir):
	logF.write(fname+ u"  "+str(datetime.now())+"\n")
	parsed= fname.split("-")
	if len(parsed)>1:
		if len(parsed[1])>5:
#			logF.write(str(parsed)+"\n")
			if parsed[1][0] =="2":  #this is date stamp
				MMnow = int(datetime.now().strftime("%m"))
				MMfil = int(parsed[1][4:6])
#				logF.write(str(MMnow)+"   "+str(MMfil)+"\n")
				if MMfil > MMnow: MMnow+=12
				if MMnow-MMfil > 1:  # keep 4-8 weeks of backup, leave rest to system backup
					logF.write(u"  === deleteing file "+fname+"\n\n")
					os.remove( fileDir+fname )
					continue
	
	f=open(fileDir+fname,"r")
	logF.write(fname+ u"  "+str(datetime.now())+"\n")
	
	
	pyFile=""
	addB=False
	for line in f.readlines():
		if line.find(": '") >-1:
			line= line.replace(": '",": u'",1)		# fix old version that does not treat unicode correctly
		if line.find("TimeBeginHour") >-1: continue
		if line.find("eEnergyCost") >-1: continue
		if line.find("DATAlimitsM") >-1: continue
#		logF.write(line)
		if line.find("nickName") >-1:
			if line.find(' n     ') >-1:				line =line.replace(" n     ",'      ',1)
		if line.find("ExtraText") >-1:
			# add missing " after "ExtraText ..
			if line.find('"ExtraText ') >-1:			line =line.replace("Text ",'Text" ',1)
			if line.find('"ExtraTextXPos ') >-1:		line =line.replace("XPos ",'XPos" ',1)
			if line.find('"ExtraTextYPos ') >-1:		line =line.replace("YPos ",'YPos" ',1)
			if line.find('"ExtraTextRotate ') >-1:		line =line.replace("Rotate ",'Rotate" ',1)
			if line.find('"ExtraTextFrontBack ') >-1:	line =line.replace("FrontBack ",'FrontBack" ',1)
			if line.find('"ExtraTextSize ') >-1:		line =line.replace("Size ",'Size" ',1)
			if line.find('"ExtraTextColorRGB ') >-1:	line =line.replace("ColorRGB ",'ColorRGB" ',1)
#     ,"resetType":        u'{u'Period': [u'2014010101', u'2014020100', u'2014030101', u'2014111001', u'2014113000', u'2014120301', u'2014120501', u'2014120801']}'  # options: 0 Period day week
#     ,"resetType":        u'{"Period": ["2014010101", "2014020100", "2014030101", "2014111001", "2014113000", "2014120301", "2014120501", "2014120801"]}'  # options: 0 Period day week month bin
		if line.find('"resetType') >-1:
			if line.find("u'{u'") >-1:
				line =line.replace("'",'"')
				line =line.replace('u"{',"u'{")
				line =line.replace(']}"',"]}'")
			if line.find("'day'") >-1: 	line =line.replace("day",'"day"')
			if line.find("'week'") >-1: line =line.replace("week",'"week"')
			if line.find("'month'") >-1:line =line.replace("month",'"month"')
			if line.find("'year'") >-1: line =line.replace("year",'"year"')

		if line.find('Consumption') >-1:
			if line.find('hour') ==-1:
				line =line.replace(',"Period',',"hour":0,"Period',1)
		if line.find('"deviceOrVariable"')>-1:
			line =line.replace("deviceOrVariable",'deviceOrVariableName',1)
		if line.find('showDeviceStates"')>-1:
			if line.find('"deviceOrVariable"')>-1:
				line =line.replace("deviceOrVariable",'deviceOrVariableName',1)
		if line.find('plug.executeAction("setConfigParameters"')>-1:
			if line.find('props')>-1:
				if line.find('={')>-1:
					addB=True
		if addB:
			if line.find('logLevel')>-1:
				if line.find(')')==-1:
					logF.write(line)
					line=line.strip("\n")
					line+=")\n"
					addB=False
		pyFile+=line
	f.close()
	f=open(fileDir+fname,"w")
	f.write(pyFile)
	f.close()
logF.close()


