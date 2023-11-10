#!/bin/bash
#cp -rf /var/www/html/wp-content/plugins/ApiCount/includes/eco /var/www/html/result 
cd /var/www/html/result
#/usr/bin/python3.5 /var/www/html/wp-content/plugins/0misspelling-checker/includes/misspelling.py -i input.csv -o output.csv -l output.log
/usr/bin/python3.5 $1 -T $2 -O $3 -L $4 -M $5 -d $6 -b $7
#sudo ./start.sh /var/www/html/wp-content/plugins/0misspelling-checker/includes/misspelling.py "" /var/www/html/result/output.csv. /var/www/html/result/output.log https://aws.amazon.com/freertos
