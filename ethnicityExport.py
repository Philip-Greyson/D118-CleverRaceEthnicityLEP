"""Script to pull ethnicity and race data, re-format to Clever's specifications and export to a txt file for re-upload into custom fields in PowerSchool.

https://github.com/Philip-Greyson/D118-CleverRaceEthnicityLEP

Takes the race codes from PowerSchool and maps them to their equivalent characters for Clever
Also maps the limited english proficiency (LEP) and ethnicity flags to Y/N from the 1/0 of PowerSchool
"""

# importing module
import datetime  # only needed for logging purposes
import os  # needed to get system variables which have the PS IP and password in them
from datetime import *

import oracledb  # needed to connect to PS database (oracle database)
import pysftp  # needed to connect to sftp server

un = os.environ.get('POWERSCHOOL_READ_USER')  # username for read-only database user
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD')  # the password for the database account
cs = os.environ.get('POWERSCHOOL_PROD_DB')  # the IP address, port, and database name to connect to

#set up sftp login info, stored as environment variables on system
sftpUN = os.environ.get('D118_SFTP_USERNAME')
sftpPW = os.environ.get('D118_SFTP_PASSWORD')
sftpHOST = os.environ.get('D118_SFTP_ADDRESS')
cnopts = pysftp.CnOpts(knownhosts='known_hosts')  # connection options to use the known_hosts file for key validation

print(f"Username: {un} |Password: {pw} |Server: {cs}")  # debug so we can see where oracle is trying to connect to/with
print(f"SFTP Username: {sftpUN} |SFTP Password: {sftpPW} |SFTP Server: {sftpHOST}")  # debug so we can see what sftp info is being used for connection
badnames = ['use', 'user', 'teststudent', 'test student', 'testtt', 'testtest', 'karentest', 'tester']

OUTPUT_FILE_NAME = 'raceethnicity.txt'
OUTPUT_FILE_DIRECTORY = './sftp/clever'
# Dicitonary to match the numeric race codes from PowerSchool to letter race abbreviations of Clever
races = {12:'I', 13:'A', 14:'B', 15:'I', 16:'W', 17:'M'}

if __name__ == '__main__':  # main file execution
    with open('raceEthnicityLog.txt', 'w') as log:
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with oracledb.connect(user=un, password=pw, dsn=cs) as con:  # create the connecton to the database
            with con.cursor() as cur:  # start an entry cursor
                print(f'INFO: Connection established to PS database on version: {con.version}')
                print(f'INFO: Connection established to PS database on version: {con.version}', file=log)
                with open(OUTPUT_FILE_NAME, 'w') as outputfile:
                    try:
                        cur = con.cursor()
                        cur.execute('SELECT students.student_number, students.FedEthnicity, s_il_stu_demographics_x.fer, students.dcid, students.first_name, students.last_name, u_def_ext_students0.custom_ethnicity, u_def_ext_students0.custom_race, u_def_ext_students0.custom_lep FROM students LEFT JOIN s_il_stu_demographics_x ON students.dcid = s_il_stu_demographics_x.studentsdcid LEFT JOIN u_def_ext_students0 ON students.dcid = u_def_ext_students0.studentsdcid WHERE students.enroll_status = 0 ORDER BY student_number DESC')
                        students = cur.fetchall()  # fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
                        for student in students:  # go through each student's data one at a time
                            try:  # do each student in a try/except block so if one throws an error we can skip to the next
                                # print(student)  # debug
                                if not str(student[4]).lower() in badnames and not str(student[5]).lower() in badnames:  # check first and last name against array of bad names, only print if both come back not in it
                                    changed = False
                                    # what we would refer to as their "ID Number" aka 6 digit number starting with 22xxxx or 21xxxx
                                    idNum = int(student[0])
                                    stuDCID = str(student[3])
                                    ethnicity_flag = int(student[1]) if student[1] else None  # get their ethnicity flag as 1 or 0
                                    raceNum = int(student[2]) if student[2] else None  # get the race code (12-17)
                                    currentEthnicity = str(student[6]) if student[6] else ''
                                    currentRace = str(student[7]) if student[7] else ''
                                    currentLep = str(student[8]) if student[8] else ''
                                    raceChar = races.get(raceNum, '') if raceNum else ''  # get the matching character for the code, return empty string if code does not exist or they have no race code
                                    # print(raceChar)
                                    ethnicity = "Y" if (ethnicity_flag == 1) else "N"  # set the ethnicty y/n based on if the flag was 1/0
                                    #print(str(idNum) + "," + ethnicity + "," + race) # debug
                                    cur.execute('SELECT lep FROM S_IL_STU_X WHERE studentsdcid = :dcid', dcid=stuDCID)  # get the limited english proficient flag from powerschool
                                    lepResults = cur.fetchall()
                                    if lepResults:
                                        rawLep = str(lepResults[0][0])  # used for debugging output, not strictly neccessary
                                        lep = "Y" if rawLep == '1' else "N"
                                    else:  # if there are no results from the student's IL demographics table, set lep to "N" and our raw lep for debugging to None
                                        rawLep = None
                                        lep = "N"

                                    print(f'DBUG: Found student {idNum} with race {raceNum} - {raceChar}, ethnicity: {ethnicity_flag}, LEP: {rawLep}')  # print out raw race num, ethnicity and lep flag values for debug
                                    print(f'DBUG: Found student {idNum} with race {raceNum} - {raceChar}, ethnicity: {ethnicity_flag}, LEP: {rawLep}', file=log)
                                    if (currentEthnicity != ethnicity):
                                        print(f'ACTION: Ethnicity flag for {idNum} is changing from {currentEthnicity} to {ethnicity}', file=log)
                                        changed = True
                                    if (currentRace != raceChar):
                                        print(f'ACTION: Race character for {idNum} is changing from {currentRace} to {raceChar}', file=log)
                                        changed = True
                                    if (currentLep != lep):  # only print out the student to the file if they have a different value than whats currently in PS
                                        print(f'ACTION: LEP indicator for {idNum} is changing from {currentLep} to {lep}', file=log)
                                        changed = True
                                    if changed:
                                        print(f'{idNum}\t{ethnicity}\t{raceChar}\t{lep}', file=outputfile)  # do our output to the file for each student

                            except Exception as er:
                                print(f'ERROR while processing student {student[0]} : {er}')
                                print(f'ERROR while processing student {student[0]} : {er}', file=log)

                    except Exception as er:
                        print(f'ERROR while doing PowerSchool query: {er}')
                        print(f'ERROR while doing PowerSchool query: {er}', file=log)

        # after all the files are done writing and now closed, open an sftp connection to the server and place the file on there
        try:
            with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
                print(f'INFO" SFTP connection established to {sftpHOST}')
                print(f'INFO" SFTP connection established to {sftpHOST}', file=log)
                # print(sftp.pwd)  # debug, show what folder we connected to
                # print(sftp.listdir())  # debug, show what other files/folders are in the current directory
                sftp.chdir(OUTPUT_FILE_DIRECTORY)
                # print(sftp.pwd)  # debug, make sure out changedir worked
                # print(sftp.listdir())
                sftp.put(OUTPUT_FILE_NAME)  # upload the file onto the sftp server
                print("INFO: Race & ethnicity file placed on remote server")
                print("INFO: Race & ethnicity file placed on remote server", file=log)
        except Exception as er:
            print(f'ERROR during SFTP upload: {er}')
            print(f'ERROR during SFTP upload: {er}', file=log)

        endTime = datetime.now()
        endTime = endTime.strftime('%H:%M:%S')
        print(f'INFO: Execution ended at {endTime}')
        print(f'INFO: Execution ended at {endTime}', file=log)
