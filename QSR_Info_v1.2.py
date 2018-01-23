#! /usr/bin/python

###Version 1.2
## included support for non root login
## Fix for registered user
## included ESUs
import os
import sys
import subprocess
import smtplib
import getopt
import re
from time import ctime
import time
import datetime
import signal

Backup_folder= "/opt/NetScout/rtm/database/config-backup"
Login        = "netscout"
def main(argv):
   
   User_List=[]
   GPM=0
   LPM=0
   Server_Storage=0
   Total_Pkt_Store=0
   Total_HDD=0
   Total_Interfaces=0
   Total_ESUs=0
   try:
      opts, args = getopt.getopt(argv,"f:i:")
   except getopt.GetoptError:
      print './QSR_Info_v1.2.py -f <PMs IP file> -i < IS IP file>'
      sys.exit()
   for opt, arg in opts:
      if opt == '-f':
         pmip = arg
      elif opt== '-i':
         is_ip = arg
      
   pm = open( pmip , "r")
   pm_list= [i.rstrip() for i in pm]
   for PM in pm_list:
       if re.search('GPM',PM):
          GPM+=1
          Users, disk_size=PM_info(PM)
          Users=Users.split("\n")
          for user in Users:
            if user not in User_List:
                User_List.append(user)
          Server_Storage=Server_Storage+float(disk_size)
       else: 
          LPM+=1
          disk_size=PM_info(PM) 
          Server_Storage=Server_Storage+float(disk_size)
     
       
   
   is1 = open( is_ip , "r")
   is_list=[i.rstrip() for i in is1]
   for IS in is_list:
     #Packetstore,HDD,Interfaces=('','','')
     Packetstore,HDD,Interfaces,ESUs=IS_info(IS)
     if Packetstore:
        Total_Pkt_Store=Total_Pkt_Store+int(Packetstore)
     if HDD:
        Total_HDD=Total_HDD+int(HDD)
     if Interfaces:
        Total_Interfaces=Total_Interfaces+int(Interfaces)
     if ESUs:
        Total_ESUs=Total_ESUs+ESUs
     
   
   print 'Global Servers <=====> %s'%GPM
   print 'Local Servers <=====> %s'%LPM
   print 'Total Infinistreams <=====> %s'%len(is_list)
   print 'Total Server Storage <=====> %f TB' %Server_Storage
   print 'Total IS Packet Storage <=====> %f TB'%float(Total_Pkt_Store*0.001)
   print 'Total Global Users <======> %s' %len(User_List)
   print 'Total IS HDD <=====> %d' %Total_HDD
   print 'Total ESUs <========> %d' %Total_ESUs
   print 'Total Active Monitoring Interfaces(Logical) <=====> %d'%Total_Interfaces
   
   
def PM_info(IP_List):
  global Backup_folder
  IP=IP_List.split(",")
  print "collecting %s data" %IP[0]
  if IP[1] =="GPM":
     ###Getting the User data from GPM
     User_Comm= """ sudo ls -Art %s/|tail -n 1|xargs -i sudo cat %s/{}/USERS.dat|grep ".*@"| awk '{print $2}'|uniq"""%(Backup_folder, Backup_folder)
     User_Data,err1=ssh_command(IP[0],User_Comm)
     #print User_Data
     ### Getting opt Disk Size from GPM
     Disk_comm= """ df -h |grep opt|awk '{print $2}'|sed -n 's/\\(.*\\)T/\\1/p'"""
     Disk_Size,err2=ssh_command(IP[0],Disk_comm)
     return User_Data,Disk_Size
  else:
     
     ### Getting opt Disk Size from Local PM
     Disk_comm= """ df -h |grep opt|awk '{print $2}'|sed -n 's/\\(.*\\)T/\\1/p'"""
     
     Disk_Size,err2=ssh_command(IP[0],Disk_comm)     
     
     return Disk_Size


def IS_info(IS):
    print "collecting %s data"%IS
    IS_command= """ echo `sudo /opt/NetScout/rtm/tools/printva |grep DataSize|cut -d: -f3|sed -n 's/\\(.*\\)GB.*/\\1/p';echo ","; ls -Art /opt/platform/nshwmon/log/nshwmon-logfiles/nshwmon* | tail -n 2 | head -n 1 |xargs cat|grep Disk| sort|uniq|wc -l ;echo ",";pkill -9 localconsole;echo -e  "11\\n get table_size_allocation \\nexit\\n" |sudo /opt/NetScout/rtm/bin/localconsole| grep -A11 "Percentage"| grep [0-9]|wc -l; echo ",";
                 ls -Art /opt/platform/nshwmon/log/nshwmon-logfiles/nshwmon* | tail -n 2 | head -n 1 |xargs cat|grep "Data.*Array"|sort|uniq|wc -l`"""
    IS_output,err=ssh_command(IS,IS_command) 
    if IS_output:
        Output_List=IS_output.split(",")
        Packetstore=Output_List[0]
        HDD= Output_List[1]
        Interfaces= Output_List[2] 
        if (int(Output_List[3])-1)>0:
           ESUs=int(Output_List[3])-1
        else:
           ESUs=0
        return Packetstore,HDD,Interfaces,ESUs
    else: 
        return ('','','','')
        


def ssh_command(IP, command):
    output=''
    err=''
    if re.search('.*\..*\..*\..*',IP):
       if int(os.popen('ping -c 2 %s|grep received | cut -d, -f2 |grep -o [0-9]'%IP).read().rstrip()) > 0:
                 
                 p= subprocess.Popen(["ssh","-t","-t",Login+'@'+IP,command], stdout=subprocess.PIPE)
                 output,err= p.communicate()
    elif re.search('.*:.*:.*:.*:.*:.*:.*:.*',IP):
         if int(os.popen('ping6 -c 2 %s|grep received | cut -d, -f2 |grep -o [0-9]'%IP).read().rstrip()) > 0:
                
                 p= subprocess.Popen(["ssh","-6","-t","-t",Login+'@'+IP,command], stdout=subprocess.PIPE)
                 output,err= p.communicate()
    
    return output,err            
    
if __name__ == "__main__":
   main(sys.argv[1:])