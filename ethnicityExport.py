#Program to pull ethnicity and race data from PowerSchool and export it in a format for upload to Clever
#Maps the different race codes in PS to their equivalent string letters for Clever
#Additionally maps the 1/0 of Limited English Proficiency to Y/N

# importing module
import sys
import os  # needed to get system variables which have the PS IP and password in them
import oracledb

un = 'PSNavigator'  # PSNavigator is read only, PS is read/write
# the password for the PSNavigator account
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD')
# the IP address, port, and database name to connect to
cs = os.environ.get('POWERSCHOOL_PROD_DB')

badnames = ['USE', 'training1', 'trianing2', 'trianing3', 'trianing4', 'planning', 'admin', 'nurse', 'user',
            'use ', 'payroll', 'human', "benefits", 'test', 'teststudent', 'test student', 'testtt', 'testtest']

# create the connecton to the database
with oracledb.connect(user=un, password=pw, dsn=cs) as con:
	with con.cursor() as cur:  # start an entry cursor
		with open('raceethnicity.txt', 'w') as outputfile:
			print("Connection established: " + con.version)
			# print header row to output file
			print('ID,Ethnicity,Race,LEP', file=outputfile)
			try:
				cur = con.cursor()
				cur.execute('SELECT students.student_number, students.FedEthnicity, s_il_stu_demographics_x.fer, students.dcid FROM students LEFT JOIN s_il_stu_demographics_x ON students.dcid = s_il_stu_demographics_x.studentsdcid ORDER BY student_number DESC')
				rows = cur.fetchall()  # fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
				# go through each entry (which is a tuple) in rows. Each entrytuple is a single student's data
				for entrytuple in rows:
					try:  # do each student in a try/except block so if one throws an error we can skip to the next
						print(entrytuple)  # debug
						# convert the tuple which is immutable to a list which we can edit. Now entry[] is an array/list of the student data
						entry = list(entrytuple)
						# check first and last name against array of bad names, only print if both come back not in it
						if not str(entry[1]) in badnames and not str(entry[2]) in badnames:
							# what we would refer to as their "ID Number" aka 6 digit number starting with 22xxxx or 21xxxx
							idNum = int(entry[0])
							stuDCID = str(entry[3])
							# get their ethnicity flag as 1 or 0
							ethnicity_flag = str(entry[1]) if entry[1] else ""
							# get the race code (12-17)
							race_code = str(entry[2]) if entry[2] else ""
							match race_code:  # do a case-match with the options for race_codes and map them to the correct string
								case "12":
									race = "I"
								case "13":
									race = "A"
								case "14":
									race = "B"
								case "15":
									race = "I"
								case "16":
									race = "W"
								case "17":
									race = "M"
								case other:
									race = "unknown"
							# print(race)
							# set the ethnicty y/n based on if the flag was 1/0
							ethnicity = "Y" if (ethnicity_flag == "1") else "N"
							#print(str(idNum) + "," + ethnicity + "," + race) #debug
							# get the limited english proficient flag from powerschool
							cur.execute(
								'SELECT lep FROM S_IL_STU_X WHERE studentsdcid = ' + stuDCID)
							lepResults = cur.fetchall()
							if lepResults:  # if there are results from our query
								lep = "Y" if (str(lepResults[0][0]) == "1") else "N"
							else:  # if we didnt get results for some reason just assume its a N
								lep = "N"
							print(str(idNum) + "," + ethnicity + "," + race + ',' + lep,
							      file=outputfile)  # do our output to the file for each student
					except Exception as err:
						print('Unknown Error on ' + str(entrytuple[0]) + ': ' + str(err))

			except Exception as er:
				print('Unknown Error: '+str(er))
