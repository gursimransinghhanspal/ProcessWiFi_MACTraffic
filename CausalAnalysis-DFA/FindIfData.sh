#!/bin/bash
mac_file=$1
pcap_file=$2
totalMAC=`cat $mac_file|wc -l`
i=1
while [ $i -le $totalMAC ]; do
SA=`head -n $i $mac_file|tail -1`
echo "Processing [$i/$totalMAC]: $SA"
`awk -F"," -v SA=$SA 'BEGIN{OFS=",";} {if ($19 == SA || $18 == SA ) print $7}' $pcap_file > /tmp/count_if_data.txt`
echo $SA >> /home/dherytaj/IfData.txt
`cat /tmp/count_if_data.txt | sort | uniq -c >> /home/dherytaj/IfData.txt`
i=`expr $i + 1`
done
