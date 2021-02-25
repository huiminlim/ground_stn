#!/bin/bash  



gzip -d $1.gz
base64 -d $2 > $2.jpg