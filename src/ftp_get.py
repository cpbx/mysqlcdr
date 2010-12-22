#!/usr/bin/env python

"""
 fpt_get.py is part of mysql_cdr

 Copyright (C) 2010 CPBX "Patrick C. Engel <engel@cpbx.eu>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
 @package       mysqlcdr
 @brief         fpt_get.py - to download call records
 @author        Patrick C. Engel <engel@cpbx.eu>
 @copyright     2010 Patrick C. Engel <engel@cpbx.eu>
 @license       GNU GPL v3.
    
"""

import os
import sys
import cgi
import ftplib
import ConfigParser

# ********************** debug **********************

# show errors in browser
import cgitb
cgitb.enable()
sys.stderr = sys.stdout


def download(filename):
	config = ConfigParser.ConfigParser()
	config.read('cdr_mysql.cfg')
	section = 'ftp'
	ftp_host = config.get(section, 'host')
	ftp_user = config.get(section, 'user')
	ftp_pass = config.get(section, 'passwd')

	try:
		ftp = ftplib.FTP(ftp_host)
		ftp.login(ftp_user, ftp_pass)
	except:
		print "Unexpected error:", sys.exc_info()[0]

	# ftp.retrlines('LIST')
	tempfilename = '/tmp/mysqlcdr_.%s.tmp' % os.getpid()
	# tempfilename = './temp/mysqlcdr_.%s.tmp' % os.getpid()
	
	try:
	   	temp = open(tempfilename, 'w+b')
	except:
		error_html("Unexpected error:", sys.exc_info()[0])

	try:
		ftp.retrbinary('RETR ' + filename, temp.write)
	except (ftplib.error_perm,ftplib.error_temp),resp:
		error_html("FTP Error", "File not Found.")
	except:
		error_html("Unexpected error:", sys.exc_info()[0])
		
	temp.close()
	ftp.close()

	print 'Content-Type: audio/x-wav'
	print
	print file(tempfilename, "rb").read()

	os.remove(tempfilename)



def error_html(err_type, err_msg):
	print "Content-type: text/html"
	print
	print """<html><head><title>error</title><style></style></head>
	<body><h1>%s</h1><p>%s</p></body></html>""" % (err_type, err_msg)
	sys.exit()


def is_valid_file():
	return True	


def has_config():
	config = ConfigParser.ConfigParser()
	config.read('cdr_mysql.cfg')
	section = 'ftp'

	if not config.has_section(section):
		return False
	return True

"""	
	ftp_host = config.get(section, 'host')
	ftp_user = config.get(section, 'user')
	ftp_pass = config.get(section, 'passwd')
"""

if __name__ == "__main__":
	params = cgi.FieldStorage()
	try:
		filename = params["file"].value
	except:
		error_html("Unexpected error", "required parameter missing.")

	if has_config() and is_valid_file():
		download(filename)
	else:
		error_html("Unexpected error", "No input file given or config error")
