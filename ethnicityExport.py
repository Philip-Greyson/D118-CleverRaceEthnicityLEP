#Program to pull ethnicity and race data from PowerSchool and export it in a format for upload to Clever
#Maps the different race codes in PS to their equivalent string letters for Clever
#Additionally maps the 1/0 of Limited English Proficiency to Y/N

# importing module
import os  # needed to get system variables which have the PS IP and password in them
import sys
import oracledb #needed to connect to PS database (oracle database)
import pysftp # needed to connect to sftp server

un = 'PSNavigator'  # PSNavigator is read only, PS is read/write
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD') #the password for the PSNavigator account
cs = os.environ.get('POWERSCHOOL_PROD_DB') #the IP address, port, and database name to connect to

#set up sftp login info, stored as environment variables on system
sftpUN = os.environ.get('D118_SFTP_USERNAME')
sftpPW = os.environ.get('D118_SFTP_PASSWORD')
sftpHOST = os.environ.get('D118_SFTP_ADDRESS')
# connection options to use the known_hosts file for key validation
cnopts = pysftp.CnOpts(knownhosts='known_hosts')

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
print("SFTP Username: " + str(sftpUN) + " |SFTP Password: " + str(sftpPW) + " |SFTP Server: " + str(sftpHOST)) #debug so we can see what sft info is being used
badnames = ['USE', 'Training1', 'Trianing2', 'Trianing3', 'Trianing4', 'PLANNING', 'ADMIN', 'NURSE', 'USER',
            'use ', 'PAYROLL', 'HUMAN', "BENEFITS", 'TEST', 'TESTSTUDENT', 'TEST STUDENT', 'TESTTT', 'TESTTEST']

with oracledb.connect(user=un, password=pw, dsn=cs) as con: # create the connecton to the database
    with con.cursor() as cur:  # start an entry cursor
        with open('raceethnicity.txt', 'w') as outputfile:
            print("Connection established: " + con.version)
			# print('ID,Ethnicity,Race,LEP', file=outputfile) #print header row to output file
            try:
                cur = con.cursor()
                cur.execute('SELECT students.student_number, students.FedEthnicity, s_il_stu_demographics_x.fer, students.dcid FROM students LEFT JOIN s_il_stu_demographics_x ON students.dcid = s_il_stu_demographics_x.studentsdcid ORDER BY student_number DESC')
                rows = cur.fetchall() #fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
				# go through each entry (which is a tuple) in rows. Each entrytuple is a single student's data
                for count, entrytuple in enumerate(rows):
                    try: #do each student in a try/except block so if one throws an error we can skip to the next
                        sys.stdout.write('\rProccessing student entry %i' % count) # sort of fancy text to display progress of how many students are being processed without making newlines
                        sys.stdout.flush()
                        # print(entrytuple)  # debug
                        entry = list(entrytuple) #convert the tuple which is immutable to a list which we can edit. Now entry[] is an array/list of the student data
                        if not str(entry[1]) in badnames and not str(entry[2]) in badnames: #check first and last name against array of bad names, only print if both come back not in it
							# what we would refer to as their "ID Number" aka 6 digit number starting with 22xxxx or 21xxxx
                            idNum = int(entry[0])
                            stuDCID = str(entry[3])
                            ethnicity_flag = str(entry[1]) if entry[1] else "" # get their ethnicity flag as 1 or 0
                            race_code = str(entry[2]) if entry[2] else ""  # get the race code (12-17)
                            match race_code:  # do a case-match with the options for race_codes and map them to the correct string
                                case "12":
                                    race = 'I'
                                case "13":
                                    race = 'A'
                                case "14":
                                    race = 'B'
                                case "15":
                                    race = 'I'
                                case "16":
                                    race = 'W'
                                case "17":
                                    race = 'M'
                                case other:
                                    race = 'unknown'
                            # print(race)
                            # set the ethnicty y/n based on if the flag was 1/0
                            ethnicity = "Y" if (ethnicity_flag == "1") else "N"
                            #print(str(idNum) + "," + ethnicity + "," + race) #debug
                            cur.execute('SELECT lep FROM S_IL_STU_X WHERE studentsdcid = ' + stuDCID) #get the limited english proficient flag from powerschool
                            lepResults = cur.fetchall()
                            if lepResults: #if there are results from our query
                                lep = "Y" if (str(lepResults[0][0]) == "1") else "N"
                            else: #if we didnt get results for some reason just assume its a N
                                lep = "N"
                            print(str(idNum) + ',' + ethnicity + ',' + race + ',' + lep, file=outputfile) #do our output to the file for each student

                    except Exception as err:
                        print('Unknown Error on ' + str(entrytuple[0]) + ': ' + str(err))

            except Exception as er:
                print('Unknown Error: '+str(er))
print('') # just forces a new line to be printed since the system stdout does not
#after all the files are done writing and now closed, open an sftp connection to the server and place the file on there
with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
	print('SFTP connection established')
	print(sftp.pwd) # debug, show what folder we connected to
	# print(sftp.listdir())  # debug, show what other files/folders are in the current directory
	sftp.chdir('./sftp/clever')
	print(sftp.pwd) # debug, make sure out changedir worked
	# print(sftp.listdir())
	sftp.put('raceethnicity.txt')  # upload the file onto the sftp server
	print("Race & ethnicity file placed on remote server")