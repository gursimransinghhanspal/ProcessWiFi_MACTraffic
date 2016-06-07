#!/bin/sh
fileToProcess=$1
outputFolder=$2
denominator=$3
home_dir=`eval echo ~$USER/`
codePath=$home_dir"/Scripts/CausalAnalysis/FindAllTrafficDetails/"

$codePath/FilterFrameDetails.sh $fileToProcess $outputFolder
inputFolder=$outputFolder
$codePath/ProcessForCDF.sh $inputFolder $denominator
