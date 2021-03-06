#!/usr/bin/python
import sys
import csv
import pdb
import os
import numpy
from numpy import loadtxt
from numpy import genfromtxt

########################################################################################################################################
#################################################****MAC Frame Signatures****##########################################################
#Cause 1 --Periodic: 
#	(S1.1)Precondition: Screen On and State Associated
#	Frame Sequence: Null Data Frame with PS = 1 -> Ack Frame -> Probe Requests with either Empty or Non-Empty SSID -> Null Data Frame with PS = 0 -> Ack Frame
#	(S1.2)Precondition: Screen Off and State Associated
#	Frame Sequence: Null Data Frame or PS-Poll Frame with PS = 1 -> Ack Frame -> Probe Requests with SSID=Associated SSID -> Null Data Frame or PS-Poll Frame with PS = 1 -> Ack Frame
#Cause 2 --Beacon Losses
#	(S2.1)Precondition: Screen Off/On and State Associated
#	Frame Sequence: Null Data Frame with PS = 0 -> No Ack Frame -> Probe Requests with SSID=Associated SSID -> Probe Requests with SSID=EMPTY
#Cause 3 --Signal Strength
#	(S3.1)Precondition: Screen On and State Associated
#	Frame Sequence: Null Data Frame with PS = 1 -> Ack Frame -> Probe Requests with SSID=EMPTY -> Null Data Frame with PS = 0 -> Ack Frame
#	(S3.2)Precondition: Screen Off and State Associated
#	Frame Sequence: Null Data Frame with PS = 1 -> Ack Frame -> Probe Requests with SSID=EMPTY -> Null Data Frame with PS = 1 -> Ack Frame
#Cause 4 --Power Management
#	(S4.1)Precondition: Screen Off and State Associated
#	(S4.1.1)Frame Sequence: Client sends Deauth/Disassoc Frame -> Ack Frame -> Probe Requests with either Empty or Non-Empty SSID 
#	(S4.1.2)Frame Sequence: Client sends PS-Poll Frame with PS = 1 -> Ack Frame -> AP sends Null Data Frame with PS = 0 or RTS Frames -> Probe Requests with SSID=Associated SSID
#	(S4.2)Precondition: Screen transitions from Off to On and State Associated
#	Frame Sequence: PS-Poll frame with PS = 1 -> Ack Frame -> At least one of these (Null Data Frame with PS = 0 -> Ack Frame or
#											 Data Frame with PS = 1 -> Ack Frame or
#											 Null Data Frame with PS = 1 -> Ack Frame) ->
#											 Probe Requests with either Empty or Non-Empty SSID
#Cause 5 --AP Station Mangement
#	(S3.1)Precondition: Screen On/Off and State Associated
#	Frame Sequence: Deauth/Disassoc Frame From AP -> Ack Frame -> Probe Requests with SSID either EMPTY/Non-Empty 
########################################################################################################################################

pcap_csv=sys.argv[1]
beacon_csv=sys.argv[2]
mac=sys.argv[3]
ssids_file=sys.argv[4]
availableSSIDs=""
#clients=sys.argv[2]

if os.path.isfile(pcap_csv) and os.path.getsize(pcap_csv) == 0:
	 sys.exit(0)
	 
if os.path.isfile(beacon_csv) and os.path.getsize(beacon_csv) == 0:
	 sys.exit(0)

if os.path.isfile(ssids_file) and os.path.getsize(ssids_file) == 0:
	 sys.exit(0)		 

frames = open( pcap_csv, "r" ) 
beacons = open( beacon_csv, "r" ) 
ssids = open( ssids_file, "r" ) 

#macs = open(clients, "r")

#clientsTable = []

#for line in macs:
#   clientsTable.append(line)

#clients_count= len(clientsTable)
#clients_details= len(clientsTable[0])


framesTable = []
for line in frames:
   row = line.rstrip().split(',')  
   framesTable.append(row)
#framesTable = genfromtxt(pcap_csv, delimiter=',')

frames_count= len(framesTable)
frame_details= len(framesTable[0])

##print ("Loading Beacons")

beaconsTable = []
for line in beacons:
   row = line.rstrip().split(',')  
   beaconsTable.append(row)
#framesTable = genfromtxt(pcap_csv, delimiter=',')

beacons_count= len(beaconsTable)
beacons_details= len(beaconsTable[0])

##print ("Loading SSIDs")
#ssidTable = []
#for line in ssids:
#   ssidTable.append(line)
   

#ssids_count= len(ssidTable)
#ssid_details= len(ssidTable[0])
ssidreader=csv.reader(ssids,delimiter=',')
for row in ssidreader:
	availableSSIDs=availableSSIDs.join(','.join(row))	

current=-1
mac_state=0 #0-unassociated 1-associated
mac_bssid="EMPTY" #"28:c6:8e:db:08:a5" #no bssid
mac_ssid="EMPTY" #"AP_5"
prev_ssid="EMPTY" #"AP_5"
prev_bssid="EMPTY" #"28:c6:8e:db:08:a5"

class3Frames="0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2e,0x2f,0x1a,0x18,0x19,0x0d,0x0e"
probeRequestCount = []
###################SSID: [Total, Hit, Miss, Empty, NE-Present, NE-Absent]
probeRequestCount.append([0,0,0,0,0,0]) #Row 1 -  Periodic - Screen On
probeRequestCount.append([0,0,0,0,0,0]) #Row 2 -  Periodic - Screen Off
probeRequestCount.append([0,0,0,0,0,0]) #Row 3 -  Beacon Loss
probeRequestCount.append([0,0,0,0,0,0]) #Row 4 -  Signal Strength - Screen On
probeRequestCount.append([0,0,0,0,0,0]) #Row 5 -  Signal Strength - Screen Off 
probeRequestCount.append([0,0,0,0,0,0]) #Row 6 -  Power Management - Screen Off to On
probeRequestCount.append([0,0,0,0,0,0]) #Row 7 -  Power Management - Screen Off Signature 1
probeRequestCount.append([0,0,0,0,0,0]) #Row 8 -  Power Management - Screen Off Signature 2
probeRequestCount.append([0,0,0,0,0,0]) #Row 9 -  AP STA Management
probeRequestCount.append([0,0,0,0,0,0]) #Row 10 - Associated and Uncategorized
probeRequestCount.append([0,0,0,0,0,0]) #Row 11 - Unassociated and Uncategorized




pRC=0
beacon_ts_prev=-1
beacon_ts_curr=-1
ndf_recvd=0
ndf_ackd=0
disassoc_deauth_recvd=0
disassoc_deauth_ackd=0
waiting_for_probe=-1 #This is used as index for probeRequestCount table, 0 -> pm, 1-> bl, 2->state0, 3->state1, 4->ui/misc
expectedFrameSubType=""
cause_rowID=-1 #can take value from 0 to 10

hit_cause_1=0
miss_cause_1=0
total_cause_1=0

hit_cause_2=0
miss_cause_2=0
total_cause_2=0

hit_cause_3=0
miss_cause_3=0
total_cause_3=0

hit_cause_4=0
miss_cause_4=0
total_cause_4=0

hit_cause_5=0
miss_cause_5=0
total_cause_5=0

probeReqFound=0
empty=0
non_empty=0
associated_ssid=0

uncategorized_associated = 0
uncategorized_unassociated = 0

goBack=0
'''
Check the state of MAC address
If associated then 
	match pattern
else
   count probe requests
'''
while (current < frames_count-1):
	
	current=current + 1
	#print "Main While", current
	if (current > frames_count - 1):
		break;

    	currentFrameTime=framesTable[current][0]
	currentFrameSubType=framesTable[current][1]
	currentFrameSSID=framesTable[current][2]
	currentFrameBSSID=framesTable[current][3]
	currentFramePM=framesTable[current][4]
	currentFrameRA=framesTable[current][5]
	currentFrameTA=framesTable[current][6]
	currentFrameSA=framesTable[current][7]
	currentFrameDA=framesTable[current][8]
	currentFrameReasonCode=framesTable[current][9]
	currentFrameDS=framesTable[current][10]
	
	next=current + 1
	if (next > frames_count - 1):
		break;
	nextFrameTime=framesTable[next][0]
	nextFrameSubType=framesTable[next][1]
	nextFrameSSID=framesTable[next][2]
	nextFrameBSSID=framesTable[next][3]
	nextFramePM=framesTable[next][4]
	nextFrameRA=framesTable[next][5]
	nextFrameTA=framesTable[next][6]
	nextFrameSA=framesTable[next][7]
	nextFrameDA=framesTable[next][8]
	nextFrameReasonCode=framesTable[next][9]
	nextFrameDS=framesTable[next][10]


	previous=current - 1
	if (previous >= 0):
		previousFrameTime=framesTable[previous][0]
		previousFrameSubType=framesTable[previous][1]
		previousFrameSSID=framesTable[previous][2]
		previousFrameBSSID=framesTable[previous][3]
		previousFramePM=framesTable[previous][4]
		previousFrameRA=framesTable[previous][5]
		previousFrameTA=framesTable[previous][6]
		previousFrameSA=framesTable[previous][7]
		previousFrameDA=framesTable[previous][8]
		previousFrameReasonCode=framesTable[previous][9]
		previousFrameDS=framesTable[previous][10]		
	

	#if currentFrameSubType == "0x0a":
	#	pdb.set_trace()
	#Reset flags if 1) source of current frame is different from previous frame's MAC and it is different from what we are considering here 2) source of current frame is same from previous frame's MAC but a different than expected frame comes
	'''	
	if (current > 0):
		if (( previousFrameSA != currentFrameSA or previousFrameTA != currentFrameTA) and ( previousFrameSA == mac or previousFrameTA == mac)) or (( previousFrameSA == currentFrameSA or previousFrameTA == currentFrameTA) and ( previousFrameSA == mac or previousFrameTA == mac) and ((currentFrameSubType not in expectedFrameSubType) or (currentFramePM==1 and previousFramePM==1))) :
			ndf_recvd=0
			ndf_ackd=0
			disassoc_deauth_recvd=0
			waiting_for_probe=-1
			expectedFrameSubType=""
	'''

	#State Change U -> A
	if (mac_state == 0) and (currentFrameSubType in class3Frames) and ((currentFrameSA == mac) or (currentFrameTA == mac)):
		mac_state=1
		mac_bssid=currentFrameBSSID
	
		#Find SSID of BSSID
		i=0
		while(mac_state == 1 and i < beacons_count and mac_ssid == "EMPTY"):
			cFrameSSID=beaconsTable[i][0]
			cFrameBSSID=beaconsTable[i][1]
			
			if (cFrameBSSID == mac_bssid):
				mac_ssid=cFrameSSID
			i=i+1


	#State Change A -> U
	if (mac_state == 1) and (currentFrameSubType=="0x0a" or currentFrameSubType=="0x0c") and ((currentFrameSA == mac) or (currentFrameTA == mac)):
		prev_ssid=mac_ssid
		prev_bssid=mac_bssid
		mac_state=0
		mac_bssid="EMPTY"
		mac_ssid="EMPTY"

	#Next If statements are checking the signature of probe requests due to PM in smartphones
	#Found a NDF from the client in consideration (currentFrameSubType == "0x24" or currentFrameSubType == "0x2c") and 
	#print(currentFramePM , currentFrameSA , currentFrameTA, mac, currentFrameBSSID , mac_bssid)

	#If A found and B found then Hit++, else Miss ++, Total++
    
	#Cause 1 Row 1: Periodic - Screen ON
	#A=(ACKd NDF PS=1 -> Count Probe Requests), B=(ACKd NDF PS=0) 
	#pdb.set_trace()
	if (mac_state == 1 and (currentFrameTA == mac or currentFrameSA == mac) and ( currentFrameSubType == "0x2c" or currentFrameSubType == "0x24") and (currentFramePM == "1") ) and (nextFrameSubType == "0x1d" and nextFrameRA == mac):
		goBack = 0
		current = next + 1
		if (current > frames_count - 1):
			break;

		currentFrameTime=framesTable[current][0]
		currentFrameSubType=framesTable[current][1]
		currentFrameSSID=framesTable[current][2]
		currentFrameBSSID=framesTable[current][3]
		currentFramePM=framesTable[current][4]
		currentFrameRA=framesTable[current][5]
		currentFrameTA=framesTable[current][6]
		currentFrameSA=framesTable[current][7]
		currentFrameDA=framesTable[current][8]
		currentFrameReasonCode=framesTable[current][9]
		currentFrameDS=framesTable[current][10]

		probeReqFound=0
		empty=0
		non_empty=0
		associated_ssid=0
		while (currentFrameSubType == "0x04" and currentFrameSA == mac):
			#print "289", current
			goBack = goBack + 1
			probeReqFound=1

			if (currentFrameSSID == mac_ssid):
				associated_ssid = associated_ssid + 1
			elif (currentFrameSSID == "EMPTY"):
				empty = empty + 1
			else:
				non_empty = non_empty + 1
			
			current = current + 1
			if (current > frames_count - 1):
				break;

			currentFrameTime=framesTable[current][0]
			currentFrameSubType=framesTable[current][1]
			currentFrameSSID=framesTable[current][2]
			currentFrameBSSID=framesTable[current][3]
			currentFramePM=framesTable[current][4]
			currentFrameRA=framesTable[current][5]
			currentFrameTA=framesTable[current][6]
			currentFrameSA=framesTable[current][7]
			currentFrameDA=framesTable[current][8]
			currentFrameReasonCode=framesTable[current][9]
			currentFrameDS=framesTable[current][10]
			
		if (probeReqFound == 1):
			goBack = goBack + 1
			next=current + 1

			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]

			current = next
			if (current > frames_count - 1):
				break;
			#case 1) all probe requests with SSID empty 
			if (empty > 0 and non_empty == 0 and associated_ssid == 0):
				#case 1) next frame is NDF with PS=0 then Row 4 Hit Cause 3
				#case 2) next frame is NDF with PS=1 then Row 5 Hit Cause 3
				if ((nextFrameSubType == "0x24" or nextFrameSubType=="0x2c") and nextFramePM == "0" and (nextFrameSA == mac or nextFrameTA == mac)) or ((nextFrameSubType == "0x24" or nextFrameSubType=="0x2c") and nextFramePM == "1" and (nextFrameSA == mac or nextFrameTA == mac)):
					next=current + 1
					goBack = goBack + 1
					if (next > frames_count - 1):
						break;
					nextFrameTime=framesTable[next][0]
					nextFrameSubType=framesTable[next][1]
					nextFrameSSID=framesTable[next][2]
					nextFrameBSSID=framesTable[next][3]
					nextFramePM=framesTable[next][4]
					nextFrameRA=framesTable[next][5]
					nextFrameTA=framesTable[next][6]
					nextFrameSA=framesTable[next][7]
					nextFrameDA=framesTable[next][8]
					nextFrameReasonCode=framesTable[next][9]
					nextFrameDS=framesTable[next][10]

					current = next
					if nextFrameSubType == "0x1d" and nextFrameRA == mac:
						hit_cause_3 = hit_cause_3 + 1				
					else:
						miss_cause_3 = miss_cause_3 + 1
						current = current + 1
						if (current > frames_count - 1):
							break;

						currentFrameTime=framesTable[current][0]
						currentFrameSubType=framesTable[current][1]
						currentFrameSSID=framesTable[current][2]
						currentFrameBSSID=framesTable[current][3]
						currentFramePM=framesTable[current][4]
						currentFrameRA=framesTable[current][5]
						currentFrameTA=framesTable[current][6]
						currentFrameSA=framesTable[current][7]
						currentFrameDA=framesTable[current][8]
						currentFrameReasonCode=framesTable[current][9]
						currentFrameDS=framesTable[current][10]

						#This is a possiblitity of beacon loss if the following frame is directed probe request
						if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac) and (nextFrameSSID == mac_ssid)):				
							hit_cause_2 = hit_cause_2 + 1
						else:
							miss_cause_2 = miss_cause_2 + 1			


				else:
				#case 3) I do not know Miss Cause 3					
					miss_cause_3 = miss_cause_3 + 1


			#case 2) all probe requests with SSID associated ssid
			if (empty == 0 and non_empty == 0 and associated_ssid > 0):
				#case 1) next frame is NDF with PS=1 then Row 2 Hit Cause 1
				#case 2) next frame is PS-Poll with PS=1 then Row 2 Hit Cause 1
				if ((nextFrameSubType == "0x24" or nextFrameSubType=="0x2c") and nextFramePM == "1" and (nextFrameSA == mac or nextFrameTA == mac)) or (nextFrameSubType == "0x1a" and nextFramePM == "1" and (nextFrameSA == mac or nextFrameTA == mac)):
					next=current + 1
					goBack = goBack + 1
					if (next > frames_count - 1):
						break;
					nextFrameTime=framesTable[next][0]
					nextFrameSubType=framesTable[next][1]
					nextFrameSSID=framesTable[next][2]
					nextFrameBSSID=framesTable[next][3]
					nextFramePM=framesTable[next][4]
					nextFrameRA=framesTable[next][5]
					nextFrameTA=framesTable[next][6]
					nextFrameSA=framesTable[next][7]
					nextFrameDA=framesTable[next][8]
					nextFrameReasonCode=framesTable[next][9]
					nextFrameDS=framesTable[next][10]

					current = next
					if nextFrameSubType == "0x1d" and nextFrameRA == mac:
						hit_cause_1 = hit_cause_1 + 1
					else:
						miss_cause_1 = miss_cause_1 + 1
				else:				
				#case 3) I do not know Miss Cause 1
					miss_cause_1 = miss_cause_1 + 1
			#case 3) mixed probe requests
			if (empty > 0 and non_empty > 0 and associated_ssid > 0):
				#case 1) next frame is NDF with PS=0 then Row 1 Hit Cause 1
				if ((nextFrameSubType == "0x24" or nextFrameSubType=="0x2c") and nextFramePM == "0" and (nextFrameSA == mac or nextFrameTA == mac)) :
					next=current + 1
					goBack = goBack + 1
					if (next > frames_count - 1):
						break;
					nextFrameTime=framesTable[next][0]
					nextFrameSubType=framesTable[next][1]
					nextFrameSSID=framesTable[next][2]
					nextFrameBSSID=framesTable[next][3]
					nextFramePM=framesTable[next][4]
					nextFrameRA=framesTable[next][5]
					nextFrameTA=framesTable[next][6]
					nextFrameSA=framesTable[next][7]
					nextFrameDA=framesTable[next][8]
					nextFrameReasonCode=framesTable[next][9]
					nextFrameDS=framesTable[next][10]

					current = next
					if nextFrameSubType == "0x1d" and nextFrameRA == mac:
						hit_cause_1 = hit_cause_1 + 1
					else:
						miss_cause_1 = miss_cause_1 + 1						
				else:
				#case 2) I do not know Miss Cause 1
					miss_cause_1 = miss_cause_1 + 1


	#if current frame is PS-Poll with PS=1
	elif (mac_state == 1 and (currentFrameTA == mac or currentFrameSA == mac) and (currentFrameSubType == "0x1a") and (currentFramePM == "1") ) and (nextFrameSubType == "0x1d" and nextFrameRA == mac):
		goBack = 0
		current = next + 1
		if (current > frames_count - 1):
			break;

		currentFrameTime=framesTable[current][0]
		currentFrameSubType=framesTable[current][1]
		currentFrameSSID=framesTable[current][2]
		currentFrameBSSID=framesTable[current][3]
		currentFramePM=framesTable[current][4]
		currentFrameRA=framesTable[current][5]
		currentFrameTA=framesTable[current][6]
		currentFrameSA=framesTable[current][7]
		currentFrameDA=framesTable[current][8]
		currentFrameReasonCode=framesTable[current][9]
		currentFrameDS=framesTable[current][10]

		next=current + 1
		if (next > frames_count - 1):
			break;
		nextFrameTime=framesTable[next][0]
		nextFrameSubType=framesTable[next][1]
		nextFrameSSID=framesTable[next][2]
		nextFrameBSSID=framesTable[next][3]
		nextFramePM=framesTable[next][4]
		nextFrameRA=framesTable[next][5]
		nextFrameTA=framesTable[next][6]
		nextFrameSA=framesTable[next][7]
		nextFrameDA=framesTable[next][8]
		nextFrameReasonCode=framesTable[next][9]
		nextFrameDS=framesTable[next][10]

		
		#Parse all frames
		#case 1) probe requests with ssid = associated ssid
			#case 1) Next frame is PS-Poll with PS=1 then Row 2 Hit Cause 1
			#case 2) Next frame is NDF with PS=1 then Row 2 Hit Cause 1
			#case 3) I do not know Miss Cause 1
		while currentFrameSubType == "0x04" and currentFrameSSID == mac_ssid and (currentFrameSA == mac or currentFrameTA == mac):
			#print "407", current
			goBack = goBack + 1			
			current = current + 1
	
			if (current > frames_count - 1): 
				break;

			currentFrameTime=framesTable[current][0]
			currentFrameSubType=framesTable[current][1]
			currentFrameSSID=framesTable[current][2]
			currentFrameBSSID=framesTable[current][3]
			currentFramePM=framesTable[current][4]
			currentFrameRA=framesTable[current][5]
			currentFrameTA=framesTable[current][6]
			currentFrameSA=framesTable[current][7]
			currentFrameDA=framesTable[current][8]
			currentFrameReasonCode=framesTable[current][9]
			currentFrameDS=framesTable[current][10]

		next=current + 1
		goBack = goBack + 1
		if (next > frames_count - 1):
			break;
		nextFrameTime=framesTable[next][0]
		nextFrameSubType=framesTable[next][1]
		nextFrameSSID=framesTable[next][2]
		nextFrameBSSID=framesTable[next][3]
		nextFramePM=framesTable[next][4]
		nextFrameRA=framesTable[next][5]
		nextFrameTA=framesTable[next][6]
		nextFrameSA=framesTable[next][7]
		nextFrameDA=framesTable[next][8]
		nextFrameReasonCode=framesTable[next][9]
		nextFrameDS=framesTable[next][10]

		current = next


		if (currentFrameSubType == "0x1a" and (currentFrameSA == mac or currentFrameTA == mac) and currentFramePM == "1") or ( (currentFrameSubType == "0x24" or currentFrameSubType == "0x2c") and currentFramePM == "1"):
			if nextFrameSubType == "0x1d" and nextFrameRA == mac:
				hit_cause_1 = hit_cause_1 + 1
			else:
				#current = current - goBack
				miss_cause_1 = miss_cause_1 + 1
		else:
			current = current - goBack
			miss_cause_1 = miss_cause_1 + 1

		goBack = 0
		series_found = 0
		#case 2) Series of mix of U(ACKd NDF PS=0, ACKd DF PS=1, ACKd NDF PS=1))
		while ((currentFrameSubType == "0x24" or currentFrameSubType == "0x2c") or (currentFramePM == "1" and (currentFrameSubType == "0x20" or currentFrameSubType == "0x28")) and (currentFrameSA == mac or currentFrameTA == mac) and (nextFrameSubType == "0x1d" and nextFrameRA == mac)):
			series_found = 1
			#print 437, current			
			previousFrameTime=framesTable[current][0]
			previousFrameSubType=framesTable[current][1]
			previousFrameSSID=framesTable[current][2]
			previousFrameBSSID=framesTable[current][3]
			previousFramePM=framesTable[current][4]
			previousFrameRA=framesTable[current][5]
			previousFrameTA=framesTable[current][6]
			previousFrameSA=framesTable[current][7]
			previousFrameDA=framesTable[current][8]
			previousFrameReasonCode=framesTable[current][9]
			previousFrameDS=framesTable[current][10]		


			current = current + 1

			goBack = goBack + 1
			if (current > frames_count - 1): 
				break;

			currentFrameTime=framesTable[current][0]
			currentFrameSubType=framesTable[current][1]
			currentFrameSSID=framesTable[current][2]
			currentFrameBSSID=framesTable[current][3]
			currentFramePM=framesTable[current][4]
			currentFrameRA=framesTable[current][5]
			currentFrameTA=framesTable[current][6]
			currentFrameSA=framesTable[current][7]
			currentFrameDA=framesTable[current][8]
			currentFrameReasonCode=framesTable[current][9]
			currentFrameDS=framesTable[current][10]		

			next=current + 1
			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]

		#case 1) Next are probe requests then Row 6 Hit Cause 4
		if (series_found == 1 and previousFrameRA == mac and nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac)):
			hit_cause_4 = hit_cause_4 + 1

		#case 2) I do not know Miss Cause 4, it could be cause 2
		else:			
			miss_cause_4 = miss_cause_4 + 1
			current = current + 1
			if (current > frames_count - 1):
				break;

			currentFrameTime=framesTable[current][0]
			currentFrameSubType=framesTable[current][1]
			currentFrameSSID=framesTable[current][2]
			currentFrameBSSID=framesTable[current][3]
			currentFramePM=framesTable[current][4]
			currentFrameRA=framesTable[current][5]
			currentFrameTA=framesTable[current][6]
			currentFrameSA=framesTable[current][7]
			currentFrameDA=framesTable[current][8]
			currentFrameReasonCode=framesTable[current][9]
			currentFrameDS=framesTable[current][10]

			#This is a possiblitity of beacon loss if the following frame is directed probe request
			if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac) and (nextFrameSSID == mac_ssid)):				
				hit_cause_2 = hit_cause_2 + 1
			else:
				miss_cause_2 = miss_cause_2 + 1			

			
	
		
		#case 3) Series of NDF with PS=0 from AP, RTS from AP
		while (currentFrameSubType == "0x24" or currentFrameSubType == "0x2c" or currentFrameSubType == "0x1b") or (currentFramePM == "0" and (currentFrameSubType == "0x20" or currentFrameSubType == "0x28")) and (currentFrameSA == mac_bssid or currentFrameTA == mac_bssid) :
			goBack = goBack + 1
			current = current + 1
			#print "500", current
			if (current > frames_count - 1): 
				break;

			currentFrameTime=framesTable[current][0]
			currentFrameSubType=framesTable[current][1]
			currentFrameSSID=framesTable[current][2]
			currentFrameBSSID=framesTable[current][3]
			currentFramePM=framesTable[current][4]
			currentFrameRA=framesTable[current][5]
			currentFrameTA=framesTable[current][6]
			currentFrameSA=framesTable[current][7]
			currentFrameDA=framesTable[current][8]
			currentFrameReasonCode=framesTable[current][9]
			currentFrameDS=framesTable[current][10]		

			next=current + 1
			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]

		#case 1) Probe Requests with SSID=Associated SSID then Row 8 Hit Cause 4
		if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac) and (nextFrameSSID == mac_ssid)):
			hit_cause_4 = hit_cause_4 + 1
 
		#case 2) I do not know Miss Cause 4
		else:
			current = next - goBack
			miss_cause_4 = miss_cause_4 + 1

	#Cause 2 Row 3: Beacon Loss - Screen ON/OFF
	#A=(UnACKd NDF PS=0) -> B=(Count Probe Requests with SSID=Associated SSID) Hit Cause 2, Miss Cause 2			
	elif ((currentFrameTA == mac or currentFrameSA == mac) and ( currentFrameSubType == "0x2c" or currentFrameSubType == "0x24") and (currentFramePM == "0") and not (nextFrameSubType == 0x1d and nextFrameRA == mac)):
			goBack = 0
			next=current + 1

			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]
			
			if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac) and (nextFrameSSID == mac_ssid)):				
				hit_cause_2 = hit_cause_2 + 1
			else:
				miss_cause_2 = miss_cause_2 + 1			

	#Cause 4 Row 7: Power Management - Screen OFF 
	#A=(ACKd Client Sends Deauth/Disassoc) -> B=(Count Probe Requests) Hit Cause 4, Miss Cause 4
	elif (( currentFrameSubType == "0x0a" or currentFrameSubType == "0x0c") and (currentFrameSA == mac or currentFrameTA == mac) ):
			goBack = 0
			next=current + 1 #1 should be ack
			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]
			c1=0
			if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac)):
				c1=1


			next=current + 2 #1 should be ack
			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]
			c2=0
			if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac)):
				c2=1
			if c1 == 1 or c2 == 1:
				hit_cause_4 = hit_cause_4 + 1
			else:
				miss_cause_4 = miss_cause_4 + 1			

	#Cause 5 Row 9: AP STA Management - Screen ON/OFF
	#A=(ACKd AP Sends Deauth/Disassoc), B=(Count Probe Requests) Hit Cause 5, Miss Cause 5
	elif ((currentFrameTA == prev_bssid or currentFrameSA == prev_bssid) and ( currentFrameSubType == "0x0c" or currentFrameSubType == "0x0a") ):
			goBack = 0
			next=current + 1 #1 should be ack
			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]
			c1=0
			if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac)):
				c1=1


			next=current + 2 #1 should be ack
			if (next > frames_count - 1):
				break;
			nextFrameTime=framesTable[next][0]
			nextFrameSubType=framesTable[next][1]
			nextFrameSSID=framesTable[next][2]
			nextFrameBSSID=framesTable[next][3]
			nextFramePM=framesTable[next][4]
			nextFrameRA=framesTable[next][5]
			nextFrameTA=framesTable[next][6]
			nextFrameSA=framesTable[next][7]
			nextFrameDA=framesTable[next][8]
			nextFrameReasonCode=framesTable[next][9]
			nextFrameDS=framesTable[next][10]
			c2=0
			if (nextFrameSubType == "0x04" and (nextFrameSA == mac or nextFrameTA == mac)):
				c2=1
			if c1 == 1 or c2 == 1:
				hit_cause_5 = hit_cause_5 + 1
			else:
				miss_cause_5 = miss_cause_5 + 1			

	#Cause 6 Row 10: Associated and Uncategorised
	#If associated and does not fall into any of the cases
	elif (mac_state == 1):
		uncategorized_associated = uncategorized_associated + 1
	else:
		uncategorized_unassociated = uncategorized_unassociated + 1
			


#print "MAC", mac
#print "Periodic Hit/Miss:", hit_cause_1, "/" ,miss_cause_1
#print "Beacon Loss Hit/Miss:", hit_cause_2, "/" ,miss_cause_2
#print "Signal Strength Hit/Miss:", hit_cause_3, "/" ,miss_cause_3
#print "Power Management Hit/Miss:", hit_cause_4, "/" ,miss_cause_4
#print "AP State Mgmt Hit/Miss:", hit_cause_5, "/" ,miss_cause_5
#print "uncategorized_associated", uncategorized_associated, "uncategorized_unassociated", uncategorized_unassociated
print mac, ", ", hit_cause_1, ", " ,miss_cause_1, ", ", hit_cause_2, ", " ,miss_cause_2, ", ", hit_cause_3, ", " ,miss_cause_3, ", ",  hit_cause_4, ", " ,miss_cause_4, ", ",  hit_cause_5, ", " ,miss_cause_5, ", ", uncategorized_associated, ", ", uncategorized_unassociated

