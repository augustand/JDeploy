#!/bin/bash

#ssh barry@192.168.101.237 << EOF
#        echo -----------------------------Before Restart---------------------------------
#		ls
#        exit
#EOF

while read f; do
  echo "file=${f}"
done << (ls -l /tmp)