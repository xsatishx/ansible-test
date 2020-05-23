#!/bin/bash

## TESTING ##
# vi /etc/passwd
# admin1:x:1000:1000:admin:/home/admin1:/bin/bash
#  mkdir /home/admin1
# chmod +777 /home/admin1/

#ownership of any home directories that are not owned by the defined user to the correct user
cat /etc/passwd | egrep -v '^(root|halt|sync|shutdown)' | awk -F: '($7 != "/sbin/nologin" && $7 != "/bin/false") { print $1 " " $3 " " $6 }' | while read user uid dir; do
  if [ ! -d "$dir" ]; then
    echo "FAILED: The home directory ($dir) of user $user does not exist."
  else
    owner=$(stat -L -c "%U" "$dir")
    if [ "$owner" != "$user" ]; then
      echo "$dir:$user:$owner"
    fi
  fi
done