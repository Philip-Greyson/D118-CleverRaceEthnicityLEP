
# D118-CleverRaceEthnicityLEP

Gets the race, ethnicity and limited english proficiency data for students in PowerSchool, re-formats it to the format Clever wants, and exports it to a .txt file that is placed on our SFTP server for re-upload into PowerSchool.

## Overview

The script first does a query for all active students in PowerSchool getting their basic information, ethnicity federal flag, and the race code from the the Illinois demographics table.
The students are then processed one at a time, the race codes are converted to the characters Clever expects, and the ethnicity flag is converted from 0/1 to N/Y.
A second query is done on each student to get their limited English proficiency (LEP) flag from another state table, and converts it to a N/Y similar to the ethnicity flag.

Then it takes the data and exports it to a tab delimited .txt file which is then uploaded via SFTP to our local server where it will be imported into PowerSchool custom fields from.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- D118_SFTP_USERNAME - *This can be replaced with an environment variable of the username of your specific SFTP server*
- D118_SFTP_PASSWORD - *This can be replaced with an environment variable of the password of your specific SFTP server*
- D118_SFTP_ADDRESS - *This can be replaced with an environment variable of the host address of your specific SFTP server*

These are fairly self explanatory, and just relate to the usernames, passwords, and host IP/URLs for PowerSchool and the output SFTP server. If you wish to directly edit the script and include these credentials, you can.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

**As part of the pysftp connection to the output SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

You will also need a SFTP server running and accessible that is able to have files written to it in the directory /sftp/clever/ or you will need to customize the script (see below). That setup is a bit out of the scope of this readme.
In order to import the information into PowerSchool, a scheduled AutoComm job should be setup, that uses the managed connection to your SFTP server, and imports into student_number, and whichever custom fields you need based on the data, using tab as a field delimiter, LF as the record delimiter with the UTF-8 character set.

## Customization

This script is fairly customized to school districts in Illinois where D118 resides as it uses some state reporting tables that (I assume) are unique to Illinois. If you are in the state, it should just work and you can change the filename and output SFTP directory by editing `OUTPUT_FILE_NAME` and `OUTPUT_FILE_DIRECTORY`, and then setup PowerSchool for the import.

If you are not in the state and need to pull the race, ethnicity, LEP data from other tables, you will need to edit the two SQL queries lines that begin with `cur.execute(...)` to match the correct tables and field names. You will then need to change the `races = {...}` dictionary to have the correct mappings between race codes and the characters that Clever expects.
