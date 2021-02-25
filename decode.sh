#!/bin/bash  



gzip -d $1
base64 -d $2 > $2.jpg