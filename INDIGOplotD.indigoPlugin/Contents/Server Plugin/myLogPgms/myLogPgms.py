######################################################################################
# .logfile handling 
######################################################################################
import indigo
import os 
import sys
import datetime
import time



class MLX():

    def __init__(self):
        self.logFile        = ""
        self.logFileActive  = False
        self.debugLevel     = "all"
        self.maxFileSize    = 10000000
        self.lastCheck      = time.time()


####-----------------  set paramete rs ---------
    def myLogSet(self, **kwargs ):# eg (debugLevel = "abc",logFileActive=True/False ,logFile = "pathToLogFile",  maxFileSize = 10000000)
        for key, value in kwargs.iteritems():
            try:
                if key == "logFileActive":
                    self.logFileActive    = value
            
                elif key == "logFile":
                    self.logFile    = value
            
                elif key == "debugLevel":
                    self.debugLevel     = value

                elif key == "maxFileSize" :
                    self.maxFileSize     = int(value)
                    
            except  Exception, e:
                if len(unicode(e)) > 5:
                    indigo.server.log(u"in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))


####-----------------  check logfile sizes ---------
    def checkLogFiles(self):
        try:
            self.lastCheck = time.time()
            if not self.logFileActive: return 
            
            fn = self.logFile.split(".log")[0]
            if os.path.isfile(fn + ".log"):
                fs = os.path.getsize(fn + ".log")
                self.myLog("Restore", "checking logfile size ...")
                if fs > self.maxFileSize:  # 30 Mbyte
                    self.myLog("Restore", "     ... reset logfile due to size")
                    if os.path.isfile(fn + "-1.log"):
                        os.remove(fn + "-1.log")
                    os.rename(fn + ".log", fn + "-1.log")
                else:
                    self.myLog("Restore", "     ...  size ok")
        except  Exception, e:
            if len(unicode(e)) > 5:
                indigo.server.log( u"in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
            
            
####-----------------  print to logfile or indigo log  ---------
    def myLog(self, msgLevel, text, type="",showDate=True):
    
        if msgLevel == "" and self.debugLevel != "all": return
    
        if  time.time() - self.lastCheck > 100:
             self.checkLogFiles()

        try:
            if not self.logFileActive:
                if msgLevel == "smallErr":
                    indigo.server.log(u"------------------------------------------------------------------------------")
                    indigo.server.log(text)
                    indigo.server.log(u"------------------------------------------------------------------------------")
                    return

                if msgLevel == "bigErr":
                    self.errorLog(u"==================================================================================")
                    self.errorLog(text)
                    self.errorLog(u"==================================================================================")
                    return

                if msgLevel == "all" or self.debugLevel.find("all") > -1 or self.debugLevel.find(msgLevel) >-1:
                    if type == "":
                        indigo.server.log(text)
                    else:
                        indigo.server.log(text, type=type)
                    return

                return


            else: # print to external logfile

                try:
                    if len(self.logFile) < 3: return # not properly defined
                    f =  open(self.logFile,"a")
                except  Exception, e:
                    indigo.server.log(u"in Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e))
                    try:
                        f.close()
                    except:
                        pass
                    return
                if msgLevel == "smallErr":
                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    f.write(u"----------------------------------------------------------------------------------\n")
                    f.write((ts+u" ".ljust(12)+u"-"+text+u"\n").encode("utf8"))
                    f.write(u"----------------------------------------------------------------------------------\n")
                    f.close()
                    return

                if msgLevel == "bigErr":
                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    f.write(u"==================================================================================\n")
                    f.write((ts+u" "+u" ".ljust(12)+u"-"+text+u"\n").encode("utf8"))
                    f.write(u"==================================================================================\n")
                    f.close()
                    return

                if msgLevel == "all" or self.debugLevel.find("all") > -1 or self.debugLevel.find(msgLevel) >-1:
                    
                    if showDate : 
                        type = datetime.datetime.now().strftime("%H:%M:%S")+" "+ str(type)
                    if type =="": type=" "

                    f.write((str(type).ljust(20)+u"-" + text + u"\n").encode("utf8"))
                    f.close()
                    return
                return

        except  Exception, e:
                indigo.server.log("Line '%s' has error='%s'" % (sys.exc_traceback.tb_lineno, e)) 
                indigo.server.log(text)
                try: f.close()
                except: pass


