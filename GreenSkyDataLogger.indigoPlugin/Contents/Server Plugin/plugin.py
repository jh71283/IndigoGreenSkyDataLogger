#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Indigo Copyright (c) 2013, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomotics.com


import indigo

import os
import sys
import signal
import Queue
import threading
import subprocess
import exceptions
import argparse
import socket
import time
import datetime

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.


class Plugin(indigo.PluginBase):
	########################################
	# Main Functions
	######################

	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.CARBON_SERVER = ''
		self.CARBON_PORT = 0
		self.updatePrefs(pluginPrefs)
		self.LastConnectionWarning = datetime.datetime.now()-datetime.timedelta(days=1)
	

	def __del__(self):
		indigo.PluginBase.__del__(self)


	def updatePrefs(self, prefs):
		self.debug = prefs.get("showDebugInfo", False)
		self.CARBON_SERVER = prefs.get("serverAddress", 'localhost')
		self.CARBON_PORT = int(prefs.get("serverPort", 2003))
		self.VariablesToLog = prefs.get("variablesToLog",[])
		if self.debug == True:
			self.debugLog("logger debugging enabled")
		else:
			self.debugLog("logger debugging disabled")
			
		self.debugLog(str(self.VariablesToLog))
	
	def variablesList(self, filter="", valuesDict=None, typeId="", targetId=0):
	# From the example above, filter = “stuff”
	# You can pass anything you want in the filter for any purpose
	# Create an array where each entry is a list - the first item is
	# the value attribute and last is the display string that will 
	# show up in the control. All parameters are read-only.
	#return myArray
		returnListA = []
		returnListB = []
		for var in indigo.variables:
			if var.folderId == 0:
				returnListA.append((var.id,self.getFullyQualifiedVariableName(var.id)))
			else:
				returnListB.append((var.id,self.getFullyQualifiedVariableName(var.id)))
				
		returnListA = sorted(returnListA,key=lambda var: var[1])
		returnListB = sorted(returnListB,key=lambda var: var[1])
		
		return returnListA + returnListB
	
	def getFullyQualifiedVariableName(self, variableID):
		var = indigo.variables[variableID]
		if var.folderId == 0:
			return   var.name
		else:
			folder = indigo.variables.folders[var.folderId]
			return  folder.name + '.' + var.name
		 
	def transformValue(self, value):
		if value=='true':
			return '1'
		elif value=='false':
			return '0'
		else:
			return value
		
	def runConcurrentThread(self):
		vmessage = ''
		while True:
			#self.debugLog("RCT")
			sock = socket.socket()
			try:
				#self.debugLog('Connecting to Carbon Server ' + self.CARBON_SERVER + ':' + str(self.CARBON_PORT))
				sock.connect((self.CARBON_SERVER, self.CARBON_PORT))
				for vtl in self.VariablesToLog:
					var = indigo.variables[int(vtl)]
					vmessage = '%s %s %d\n' % ('indigo.' + self.getFullyQualifiedVariableName(var.id), self.transformValue(var.value), int(time.time()))
					sock.sendall(vmessage)
					self.debugLog(vmessage)
						
			
				sock.close()
			except:
				if self.dateDiff(datetime.datetime.now(),self.LastConnectionWarning) > 30:
					self.LastConnectionWarning = datetime.datetime.now()
					indigo.server.log('Error connecting to Carbon server ' + self.CARBON_SERVER + ':' + str(self.CARBON_PORT) +'  Please check configuration! (This warning will only appear at most every 30s)')
					
			self.sleep(1)
	
	########################################
	# Prefs dialog methods
	########################################
	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		# Since the dialog closed we want to set the debug flag - if you don't directly use
		# a plugin's properties (and for debugLog we don't) you'll want to translate it to
		# the appropriate stuff here. 
		if not userCancelled:
			self.debug = valuesDict.get("showDebugInfo", False)
			self.CARBON_SERVER = valuesDict.get("serverAddress", 'localhost')
			self.CARBON_PORT = int(valuesDict.get("serverPort", 2003))
			self.VariablesToLog = prefs.get("variablesToLog",[])
			if self.debug:
				indigo.server.log("Debug logging enabled")
			else:
				indigo.server.log("Debug logging disabled")
	
			self.LastConnectionWarning = datetime.datetime.now()-datetime.timedelta(days=1)
			
			

			
	def startup(self):
		self.debugLog("startup called")
	
	def shutdown(self):
		self.debugLog("shutdown called")

	def dateDiff(self,d1,d2):
		diff = d1-d2
		
		return (diff.days * 86400) + diff.seconds
	


		
		