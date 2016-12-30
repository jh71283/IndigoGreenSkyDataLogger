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
		if self.debug == True:
			self.debugLog("logger debugging enabled")
		else:
			self.debugLog("logger debugging disabled")
	
	def runConcurrentThread(self):
		GraphiteFolderID = indigo.variables.folders.getId("Graphite")
		vmessage = ''
		while True:
			self.debugLog("RCT")
			sock = socket.socket()
			try:
				self.debugLog('Connecting to Carbon Server ' + self.CARBON_SERVER + ':' + str(self.CARBON_PORT))
				sock.connect((self.CARBON_SERVER, self.CARBON_PORT))
				for var in indigo.variables:
					if var.folderId == GraphiteFolderID:
						vmessage = '%s %s %d\n' % ('indigo.' + var.name, var.value, int(time.time()))
						sock.sendall(vmessage)
						self.debugLog(vmessage)
						
			
				sock.close()
			except:
				if self.dateDiff(datetime.datetime.now(),self.LastConnectionWarning) > 30:
					self.LastConnectionWarning = datetime.datetime.now()
					indigo.server.log('Error connecting to Carbon server. Please check configuration! (This warning will only appear at most every 30s)')
					
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
	


		
		