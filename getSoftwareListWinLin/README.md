A simple script used to get a list of software installed in windows server as well as linux servers and the push them to a central repository or central server

Example
Server A - Windows
Server B - Linux
Server C - Central repo

The script copies a powershell script that gets the list of installed software in windows using the registry values and for rhel it relies on yum. These two files  from Server A ( windows ) and Server ( Linux, rhel) are then pushed to a Server C (Central repository / this can be amazon s3 as well).
