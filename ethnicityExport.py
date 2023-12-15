"""Script to pull ethnicity and race data, re-format to Clever's specifications and export to a txt file for re-upload into custom fields in PowerSchool.

https://github.com/Philip-Greyson/D118-CleverRaceEthnicityLEP

Takes the race codes from PowerSchool and maps them to their equivalent characters for Clever
Also maps the limited english proficiency (LEP) and ethnicity flags to Y/N from the 1/0 of PowerSchool
"""

# importing module
import os  # needed to get system variables which have the PS IP and password in them

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

# Dicitonary to match the numeric race codes from PowerSchool to letter race abbreviations of Clever
races = {12:'I', 13:'A', 14:'B', 15:'I', 16:'W', 17:'M'}

if __name__ == '__main__':  # main file execution
    with oracledb.connect(user=un, password=pw, dsn=cs) as con:  # create the connecton to the database
        with con.cursor() as cur:  # start an entry cursor
            with open('raceethnicity.txt', 'w') as outputfile:
                print("Connection established: " + con.version)
                # print('ID,Ethnicity,Race,LEP', file=outputfile) #print header row to output file
                try:
                    cur = con.cursor()
                    cur.execute('SELECT students.student_number, students.FedEthnicity, s_il_stu_demographics_x.fer, students.dcid, students.first_name, students.last_name FROM students LEFT JOIN s_il_stu_demographics_x ON students.dcid = s_il_stu_demographics_x.studentsdcid WHERE students.enroll_status = 0 ORDER BY student_number DESC')
                    students = cur.fetchall()  # fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
                    for student in students:  # go through each student's data one at a time
                        try:  # do each student in a try/except block so if one throws an error we can skip to the next
                            # print(student)  # debug
                            if not str(student[4]).lower() in badnames and not str(student[5]).lower() in badnames:  # check first and last name against array of bad names, only print if both come back not in it
                                # what we would refer to as their "ID Number" aka 6 digit number starting with 22xxxx or 21xxxx
                                idNum = int(student[0])
                                stuDCID = str(student[3])
                                ethnicity_flag = int(student[1]) if student[1] else None  # get their ethnicity flag as 1 or 0
                                raceNum = int(student[2]) if student[2] else None  # get the race code (12-17)
                                raceChar = races.get(raceNum, 'unknown') if raceNum else 'unknown'  # get the matching character for the code, return "unknown" if code does not exist or they have no race code
                                # print(raceChar)
                                ethnicity = "Y" if (ethnicity_flag == 1) else "N"  # set the ethnicty y/n based on if the flag was 1/0
                                #print(str(idNum) + "," + ethnicity + "," + race) #debug
                                cur.execute('SELECT lep FROM S_IL_STU_X WHERE studentsdcid = ' + stuDCID)  # get the limited english proficient flag from powerschool
                                lepResults = cur.fetchall()
                                lep = "Y" if (str(lepResults[0][0]) == '1') else "N"

                                print(f'DBUG: Found student {idNum} with race {raceNum} - {raceChar}, ethnicity: {ethnicity_flag}, LEP: {lepResults[0][0]}')  # print out raw race num, ethnicity and lep flag values for debug
                                print(f'{idNum},{ethnicity},{raceChar},{lep}', file=outputfile)  # do our output to the file for each student

                        except Exception as err:
                            print('Unknown Error on ' + str(student[0]) + ': ' + str(err))

                except Exception as er:
                    print('Unknown Error: '+str(er))
    print('')  # just forces a new line to be printed since the system stdout does not
    #after all the files are done writing and now closed, open an sftp connection to the server and place the file on there
    with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
        print('SFTP connection established')
        # print(sftp.pwd)  # debug, show what folder we connected to
        # print(sftp.listdir())  # debug, show what other files/folders are in the current directory
        sftp.chdir('./sftp/clever')
        # print(sftp.pwd)  # debug, make sure out changedir worked
        # print(sftp.listdir())
        sftp.put('raceethnicity.txt')  # upload the file onto the sftp server
        print("Race & ethnicity file placed on remote server")
