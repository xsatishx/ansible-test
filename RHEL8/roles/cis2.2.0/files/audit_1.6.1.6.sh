#!/bin/bash

out=$(ps -eZ | egrep "initrc" | egrep -vw "tr|ps|egrep|bash|awk" | tr ':' ' ' | awk '{ print $NF }')
if [[ $out ]]; then
  echo "Investigate any unconfined daemons found during the audit action. They may need to have an existing security context assigned to them or a policy built for them."
  echo $out
fi