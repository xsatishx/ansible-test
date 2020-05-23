#!/bin/bash
 
NOW=$(date +%s)
for i in $(egrep ^[^:]+:[^\!*] /etc/shadow | cut -d: -f1 ); do
        UPA=$(chage --list $i | grep "Last password change" | cut -d: -f2)
        EPOCH=$(date -d "$UPA" +%s 2> /dev/null)

        if [[ $EPOCH =~ ^[+-]?[0-9]+$ && $EPOCH -gt $NOW ]]; then
                echo "$i"
        fi
done