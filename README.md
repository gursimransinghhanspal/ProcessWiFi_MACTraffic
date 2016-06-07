# CausalAnalysis
This code should be placed in home folder
Folder structure required $HOME/Scripts/CausalAnalysis/
This code process packet captures (PCAPs) to analyze the cause of active scanning in WiFi networks.
It converts PCAPs to CSVs.

Main File to execute: CodeFlow.sh
#./CodeFlow.sh

It will ask for following details:
	1. Name of dataset to be processed
	2. EDCA Enabled
	3. Header - Radiotap or Prism
	4. Convert PCAP to CSV required 
		[PCAPs should be placed at $HOME/Datasets_PCAPs/<Name of dataset>/Date/<PCAPs>]
		[CSVs should be placed at $HOME/Datasets_CSVs/<Name of dataset>/Day#_Merged.csv]
	5. What do you want to process?
		a. APs and Clients
		b. Filter Traffic
		c. Frame Details
		d. Airtime Utilization
		e. Useless Probe Traffic
		f. Quantify Causes

Output Path of processed result: $HOME/DataAnalysis/<Name of dataset>/Day#, One folder for each of the above will be created:
		a. APs-Clients  
		b. FindNumberofFrames  
		c. FindAllTrafficDetails  
		d. ATU  
		e. UselessProbeTraffic
		f. CausalAnalysis-Datasets  



