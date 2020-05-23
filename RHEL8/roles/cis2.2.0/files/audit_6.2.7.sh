#!/bin/bash

## TESTING ##
# vi /etc/passwd
# admin1:x:1000:1000:admin:/home/admin1:/bin/bash
#  ! -z "$user"
cat /etc/passwd | egrep -v '^(root|halt|sync|shutdown)' | awk -F: '($7 != "/sbin/nologin" && $7 != "/bin/false") { print $1 " " $6 }' | while read user dir; do
  if [ ! -d "$dir" ]; then
    echo "$user:$dir"
  fi
done