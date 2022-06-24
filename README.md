### Not sure what the final name will be but here is the jist of it

 Cacti sends alerts from the primary poller this script aims to distribute this job to all pollers
 Cacti remote pollers all have their own host table with a list of devices asociated to the respective poller

 If the primary poller were to go down you would not see any device down notification or other alerts

 This script can be run via cron for now systemd later to check the host table for recent down devices

 then execute a command to a ticketing system for a device device or send a email (As a last resort hopefully)


The script is able to be shutdown via the Cacti GUI by disabling the Cacti Poller which can come in handy for maitanece work
The script checks the poller enabled status upon startup if the poller is disabled in gui the script will exi



Current Notification capabilities foe device UP/DOWN events

- Email Notification ( Using the mail command but I plan to add smtp)
- Script execution
- Slack Webhook
- Syslog ( Using Logger command instead of using yet another library)


TODO
Add Twillo support


### This a work in progress and is currently not prod ready ###

 

