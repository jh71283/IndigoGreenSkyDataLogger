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
			sock = socket.socket()
			try:
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
			
			
	def variableUpdated(self, origVar, newVar):
		
		
		vmessage=''
		if newVar.name.startswith('Graphite') == True:
			vmessage = '%s %s %d\n' % ('indigo.' + newVar.name, newVar.value, int(time.time()))
			sock = socket.socket()
			sock.connect((self.CARBON_SERVER, self.CARBON_PORT))
			sock.sendall(vmessage)
			sock.close()
			
	def startup(self):
		self.debugLog("startup called")
		indigo.devices.subscribeToChanges()
		#indigo.variables.subscribeToChanges()
 
	def shutdown(self):
		self.debugLog("shutdown called")


	def deviceCreated(self, device):
		self.debugLog("logger device created")
		
	def deviceUpdated(self, origDev, newDev):
		#self.debugLog("logger device updated")
		self.dd(origDev.states, newDev.states, newDev.name.replace(" ",""));
		
	def deviceDeleted(self, device):
		self.debugLog("logger device deleted")
	def dateDiff(self,d1,d2):
		diff = d1-d2
		
		return (diff.days * 86400) + diff.seconds
	
	
	def dd(self, d1, d2, ctx=""):
		#self.debugLog( "Changes in " + ctx)
	
		#self.debugLog(unicode(d1))
		for k in d1:
			if k not in d2:
				self.debugLog( k + " removed from d2")
		for k in d2:
			if k.endswith(".ui"):
				continue #self.debugLog( "2")
			if k not in d1:
				self.debugLog( k + " added in d2")
				continue
			if d2[k] != d1[k]:
				if k.endswith(".ui"):
					continue
				if type(d2[k]) not in (dict, list):
					#self.debugLog(ctx + "." + k  + " changed to " + unicode(d2[k]))
					#self.debugLog("Sending to Graphite")
					
					timestamp = int(time.time())
					message = '%s %s %d\n' % (ctx + "." + k, unicode(d2[k]), timestamp)
					self.debugLog(message)
					try:
						sock = socket.socket()
						sock.connect((self.CARBON_SERVER, self.CARBON_PORT))
						sock.sendall(message)
						sock.close()
					except:
						if self.dateDiff(datetime.datetime.now(),self.LastConnectionWarning) > 30:
							self.LastConnectionWarning = datetime.datetime.now()
							indigo.server.log('Error connecting to Carbon server. Please check configuration!')
			
				else:
					if type(d1[k]) != type(d2[k]):
						self.debugLog(	ctx+ "." + k + " changed to 2 " + unicode(d2[k]))
						
						continue
					else:
						if type(d2[k]) == dict:
							dd(d1[k], d2[k], k)
							continue
							
		#self.debugLog( "Done with changes in " + ctx)
		

		
		