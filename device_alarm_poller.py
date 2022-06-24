#!/bin/python3

import mysql.connector
import sys
import os
from datetime import datetime
import argparse
import dotenv

now = datetime.now()

##config section

###update config_poller_id with the id of the poller this script is running on this is used to find the status of the poller
config_poller_id = "1"

#### Notification settings ###

###Script execution ###
execute_script = "n"
path_to_script = ""

## You can pass the following variables to scripts 
#device_name           
#device_hostname           
#device_id
## For down events you can pass fail_reason  
##i.e "/tmp/notify_script device_name device_hostname"


### emil notification settings ###
email_enabled = "n"
admin_email=""

##slack notification settings (Not tested yet) ###
slack_enabled = "n"
slack_webhook_url=""


##syslog logging settings ###
syslog_enabled = "y"
syslog_server="127.0.0.1"
syslog_program="alarm_poller"


### end notification settings ###


### connect to mysql database

## get the database credentials from .env file
dotenv.load_dotenv()

##check if the file exists
if not os.path.exists('.env'):
    print('found .env file' +  (os.path.abspath('.env')))
    print('could not find .env file')
    print('please create a .env file with the following contents:')
    print('DB_USER=<your_db_user>')
    print('DB_PASSW=<mysql_password>')
    print('DB=<database_name>')
    sys.exit()



##connect to mysql database
try:
    mydb = mysql.connector.connect(
        host="localhost",
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASS'),
        database=os.getenv('DB')

        )
except mysql.connector.Error as err:
    print("Something went wrong: {}".format(err))
    sys.exit()



##create cursor
mycursor = mydb.cursor()


### Check Cacti DB for poller  settings

poller_interveral = "select value  from settings where name = 'poller_interval'"
mycursor.execute(poller_interveral)
poller_interveral = mycursor.fetchone()
str(poller_interveral)

###based on the poller interval we adjust our checks 2 mins for 1 min and 10 mins for 5 mins in the sql statement

if poller_interveral[0] == "60":
    time_interveral = "2"
elif poller_interveral[0] == "300":
    time_interveral = "10"


## If cacti poller is disabled then exit the script
poller_disabled = "select disabled from poller where id = '" + config_poller_id + "'"
mycursor.execute(poller_disabled)
poller_enabled = mycursor.fetchone()

###If global polling is disabled dont run alarm checks
global_poller_disabled = "select value  from settings where name = 'poller_enabled' "
mycursor.execute(global_poller_disabled)
global_poller_disabled = mycursor.fetchone()



### check cacti db for log file path
log_file_path = "select value  from settings where name = 'path_cactilog'"
mycursor.execute(log_file_path)
log_file_path = mycursor.fetchone()
str(log_file_path)




###Sanity Checks###

if execute_script == "y":
    if not os.path.isfile(path_to_script):
        print("script not found")
        sys.exit()

if execute_script == "y":
    if not os.access(path_to_script, os.X_OK):
        print("script not executable")
        sys.exit()

if execute_script == "y":
    if path_to_script == "":
        print("you have enabled script executtion but have not specified a script path ")
        sys.exit()

if email_enabled == "y":
    if admin_email == "":
        print("you have enabled email notification but have not specified an email address ")
        sys.exit()

if slack_enabled == "y":
    if slack_webhook_url == "":
        print("you have enabled slack notification but have not specified a webhook url ")
        sys.exit()


if syslog_enabled == "y":
    if syslog_server == "":
        print("you have enabled syslog logging but have not specified a syslog server ")
        sys.exit()


if poller_enabled[0] == "on":
    print(str(now) + " " + "ERROR: Cacti Poller is disabled Alarm checking will not be performed")
    os.system("echo " +  str(now) + " " + "'ERROR: Cacti Poller is disabled Alarm checking will not be performed' >> " + log_file_path[0])
    sys.exit()

if global_poller_disabled[0] == '':
    print(str(now) + " " + "ERROR: Cacti global polling is disabled Alarm checking will not be perfromed")
    os.system("echo " +  str(now) + " " + "'ERROR: Cacti global polling is disabled Alarm checking will not be perfromed' >> " + log_file_path[0])
    sys.exit()



### End Sanity Checks ###



##find down devices 

###since the primary poller has the full host table we dont want the script on the primary poller pulling
##the same data as the remote pollers would so if the script is running on poller1 we limit our search to just devices
###asociated to poller 1 since remote pollers host tables only contain devices asociated to the poller we dont need the poller_id where clause

if config_poller_id == "1":
 device_down = "select id,hostname,description,status,status_last_error from host where status = 1 and poller_id = 1 and disabled = '' and status_fail_date  > NOW() - INTERVAL " + time_interveral + " MINUTE"
 
device_up = "select id,hostname,description,status from host where status = 3 and poller_id = 1 and disabled = '' and status_rec_date  > NOW() - INTERVAL " + time_interveral + " MINUTE"


if config_poller_id != "1":
 device_down = "select id,hostname,description,status,status_last_error from host where status = 1 and disabled = '' and status_fail_date  > NOW() - INTERVAL " + time_interveral + " MINUTE"
 device_up = "select id,hostname,description,status from host where status = 3  and disabled = '' and status_rec_date  > NOW() - INTERVAL  " + time_interveral + " MINUTE"



##execute query

mycursor.execute(device_up)
up_data = mycursor.fetchall()

down_data = mycursor.execute(device_down)
down_data = mycursor.fetchall()


###loop over dowwn and up devices


###Down device processing
for device in down_data:
    ##print device is down to log_path file
    with open(log_file_path[0] , 'a') as log_file:
        log_file.write(" ERROR: Device Name: " + " " +  device[2] + "Device ID "  + str(device[0])  + " is DOWN\n")

    ###lets make the variables a bit easier to work with
    fail_reason = device[4]
    device_name = device[2]
    device_hostname = device[1]
    device_id = device[0]
    
    print("Device: " + device_name +  " " + " AT IP " + device_hostname + " " + " is down due to " + fail_reason )


    if execute_script == "y":
        os.system(path_to_script)

    if email_enabled == "y":
        os.system("echo ERROR: Device Name: " + " " +  device_name + "Device ID "  + str(device_id)  + " Is DOWN!" " | mail -s 'Device: " + device[2] + " is DOWN!' " + admin_email)


    if slack_enabled == "y":
        os.system("curl -X POST --data 'payload=%7B%22text%22%3A%22WARNING: Device Name: " + " " +  device[2] + "Device ID "  + str(device[0])  + " is DOWN!' " + slack_webhook_url)

    if syslog_enabled == "y":
        os.system("echo WARNING: Device Name: " + " " +  device_name + "Device ID "  + str(device_id)  + "Is Down" " | logger -n " + syslog_server +  "-p "  + syslog_priority )





###up device processing
for device in up_data:
    
    device_name = device[2]
    device_hostname = device[1]
    device_id = device[0]

    print("Device Name " + device_name + "Device IP" + device_hostname + " is up")

    device_name = device[2]
    device_hostname = device[1]
    device_id = device[0]


    ##print device is down to log_path file
    with open(log_file_path[0] , 'a') as log_file:
        log_file.write(" WARNING: Device Name: " + " " +  device[2] + "Device ID "  + str(device[0])  + " Has Restored\n")

    if execute_script == "y":
        os.system(path_to_script)
    
    if email_enabled == "y":
        os.system("echo WARNING: Device Name: " + " " +  device[2] + "Device ID "  + str(device[0])  + " Has Restored" " | mail -s 'Device: " + device[2] + " is up' " + admin_email)

    if slack_enabled == "y":
        os.system("curl -X POST --data 'payload=%7B%22text%22%3A%22WARNING: Device Name: " + " " +  device[2] + "Device ID "  + str(device[0])  + " Has Restored%22%7D' " + slack_webhook_url)
    if syslog_enabled == "y":
        os.system("echo WARNING: Device Name: " + " " +  device[2] + "Device ID "  + str(device[0])  + " Has Restored" " | logger -n " + syslog_server +  " -p 5 -t "  + syslog_pogram )


##write status to log_path file
with open(log_file_path[0] , 'a') as log_file:
    log_file.write(str(now) + " " +  "STATS: Alarm Poller ran  " +  "\n" )

if syslog_enabled == "y":
    os.system("echo Alarm Poller ran at: " + str(now)  + " | logger -n " + syslog_server +  " -p 5 -t  "  + syslog_program )
    

###accept arguments for debug
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="debug mode", action="store_true")

##check if debug mode is enabled
if parser.parse_args().debug:
    
    print("\n")
    print("Poller is running in debug mode")
    print("Script is configured to run on poller id " + config_poller_id)
    print("Poller interval is: " + str(poller_interveral))
    print("\n")

    print("SQL query run for Down Device: " + device_down)
    print("\n")
    print("down_data: " + str(down_data))
    print("\n")
    print("\n")

    print("SQL query run for Up Device: " + device_up)
    print("\n")
    print("up_data: " + str(up_data))



#close connection
mydb.close()
