#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 mysql_cdr - browse MySQL Calldetails. 

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
    
 @package		mysqlcdr
 @brief			mysqlcdr is a simple Script to browse Calldetails
 @author		Patrick C. Engel <engel@cpbx.eu>
 @copyright		2010 Patrick C. Engel <engel@cpbx.eu>
 @license		GNU GPL v3.
    
"""

import sys
import os
import cgi
import MySQLdb
import ConfigParser

from datetime import datetime, date, time

# ********************** debug **********************

# show errors in browser
import cgitb
cgitb.enable()
sys.stderr=sys.stdout

# ********************** config **********************

__revision__ = (1,0)

config = ConfigParser.ConfigParser()
config.read('cdr_mysql.cfg')

def get_default_confval(section, key, default):
  try:
    ret = config.get(section, key)
  except (ConfigParser.NoSectionError,ConfigParser.NoOptionError), e:
    ret = default
  return ret


# ********************** i18n **********************

lang= get_default_confval('general', 'lang', 'de')

t9n = {'de':{'Number':'Nummer',
  'Order':	'Sortierung',
  'offset':	'Start',
  'row count':	'Anzahl',
  'status':	'Status',
  'calldate':	'Datum', 
  'clid':	'Anruferinfo',
  'src': 	'A-Nummer', 
  'dst': 	'B-Nummer',
  'dcontext': 	'Kontext',
  'channel': 	'Channel',
  'billsec':	'Sek.',
  'accountcode':'Nebenstelle',
  'Next': 'Vorw&auml;rts',
  'Previous': 'Zur&uuml;ck'}
}


def t(msgid):
	try:
		msg = t9n[lang][msgid]
	except KeyError:
		msg = msgid
	return msg	


def find_protocol(str):
  if (str.find('mISDN') != -1): return 'mISDN'
  if (str.find('SIP') != -1): return 'SIP'
  if (str.find('IAX2') != -1): return 'IAX2'
  return 'default'


# ********************** header **********************

theme_light = """body {
    font-family: sans-serif;
    font-size: 100%;
    background-color:#eee;
    color:#00303d;
    margin: 0;
    padding: 0;
  }

  table {
    background-color:#fff;
    color:#333;
    border:4px solid #fff;
  }
  
  td {
    background-color:#E0E1E4;
    padding: 3px;
    color:#001;
  }
  
  thead td {
    background-color:#fff;
  }
  tr:hover td,tr:hover th{background:#ddf;}
  #body {
    padding: 0 20px 30px 20px;
  }
  
  #results {
    width:100%;
    background-color:#fff;
    border-top:10px solid #cdc;
    overflow:auto;
  }
 #paginate {
    background-color:#bcb;
    height:1.5em;
 }

 #paginate a {
    color:#fff;
    font-size: 90%;
    font-family: monospace;
    background-color:#466;
    /* width:2.4em; */
    margin-left:4px;
    border:2px solid #466;
    text-decoration:none;
    /* css3 */
    border-radius:8px;
    -moz-border-radius:8px;
    -webkit-border-radius:8px;
    -khtml-border-radius:8px;
 }

 #paginate a:hover {
    background-color:#363;
    border:2px solid #363;
 }

 #searchform {
    background-color:#bbb;
    color:#1c4e63;
    padding: 10px 20px 30px 20px;
    /* css3 */
    border-top-right-radius:8px;
    border-top-left-radius:8px;
    -moz-border-radius-topleft:8px;
    -webkit-border-top-left-radius:8px;
    -khtml-border-top-left-radius:8px;
    -moz-border-radius-topright:8px;
    -webkit-border-top-right-radius:8px;
    -khtml-border-top-right-radius:8px;
  }

  #footer {
    padding: 4px;
    font-size:0.7em;
    color:#bbb;
  }
  .mISDN { background-color:#eef;}
  .SIP { background-color:#efe;}
  .IAX2 { background-color:#fee;}
  /* #E0E1E4;*/"""

	 
# **********************************************************************

class Cdr:
	html = ""
	def header_html(self, theme_light):
  		print """Content-type: text/html\n
<!DOCTYPE html><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><style>%s</style><title>CPBX.Calldetails</title>
</head><body><div id=body><div id=header><h1>CPBX Calldetails</h1></div>\n""" %   theme_light

	def footer_html(self):
		dt = datetime.now()
		print """\n<div id=footer>%s""" % (dt.strftime("%A, %d. %B %Y %I:%M%p"))
		print """ generated by mysqlcdr Version %d.%d CPBX (c) 2010 """ % (__revision__[0], __revision__[1])
		print "</div>\n</div></body>"

	def searchform_html(self):
		formaction = 'action="'+os.path.basename(sys.argv[0])+'"'
		print "<div id=searchform><form method=get ",formaction,">"
		print "<label>"+t('Number')+":</label>&nbsp;"
		if form.has_key('num'):
			print "<input size=14 name=num value=",cgi.escape(form["num"].value),">&nbsp;"
		else:
			print "<input size=14 name=num >&nbsp;"
		print "<select name=type><option value=src>Source</option><option value=dst>Destination</option><option value=accountcode>Account</option></select>&nbsp;"
		# ORDER
		print "<label>"+t('Order')+":</label>&nbsp;<select name=o>"
		print "<option value=desc>newest</option>"
		if form.has_key('o'):
			if (form["o"].value == "asc"):
				print "<option value=asc selected>oldest</option>"
			else:
				print "<option value=asc>oldest</option>"
		print "</select>&nbsp;"
		# LIMIT offset rowcount
		print "<label>offset:</label>"
		if form.has_key('os'):
			print "<input size=5 name=os value=",cgi.escape(form["os"].value),">&nbsp;"
		else:
			print "<input size=5 name=os value=0>&nbsp;"
		print "<label>row count:</label>"
		if form.has_key('rc'):
			print "<input size=5 name=rc value=",cgi.escape(form["rc"].value),">&nbsp;"
		else:
			print "<input name=rc value=50 size=5>&nbsp;"
		print "<input type=submit value=show></form></div>"


	def paginate_html(self, page, offset, rowcount):
		print "<div id=paginate>"
		if(int(page)>=1):
			p = int(page)-1	  
			ofs = int(p) * int(rowcount)
			href = 'href="'+os.path.basename(sys.argv[0])+'?p=%s&amp;o=%s&amp;os=%d&amp;rc=%s"' % (p, order, ofs, rowcount)
			print "<a ", href, "> " + t('Previous') + " </a>"
		p = int(page)+1
		ofs = int(p) * int(rowcount)
		href = 'href="'+os.path.basename(sys.argv[0])+'?p=%s&amp;o=%s&amp;os=%d&amp;rc=%s"' % (p, order, ofs, rowcount)
		print "<a ",href,"> " + t('Next') + " </a>"
		print "</div>"
		return

		
	def results_html(self, query_result):
		print "<div id=results><table>"
		print "<thead><tr><td>"+t('status')+"</td><td>"+t('calldate')+"</td><td>"+t('clid')+"</td><td>"+t('src')+"</td><td>"
		print t('dst')+"</td><td>"+t('dcontext')+"</td><td>"+t('channel')+"</td><td>"+t('billsec')+"</td><td>"+t('accountcode')+"</td></thead><tbody>"
 
		for calldate, clid, src, dst, dcontext, channel, dstchannel, lastapp, lastdata, duration, billsec, disposition, amaflags, accountcode, userfield in query_result:
			print "<tr><td>"
			if (lastapp == 'Busy'):
				print "<img src=http://cpbx.eu/images/cdr/telephone_busy.png title=Busy>"
			elif (lastapp == 'VoiceMail'):
				print "<img src=http://cpbx.eu/images/cdr/voicemail.png title=VoiceMail>"
			elif (lastapp == 'Dial' and disposition == 'ANSWERED'):
				print "<img src=http://cpbx.eu/images/cdr/telephone.png title=busy>"
			else:
				print "<img src=http://cpbx.eu/images/cdr/telephone_noanswer.png title=noanswer>"
			print "</td><td>",calldate,"</td><td>", cgi.escape(clid),"</td><td>",cgi.escape(src),"</td><td>",cgi.escape(dst),"</td>"
			print "<td>",cgi.escape(dcontext),"</td>"
			print "<td class=",find_protocol(channel),">",cgi.escape(channel),"</td>"
			print "<td>",billsec,"</td>"
			print "<td><b>",cgi.escape(accountcode),"</b></td>"
			print "</tr>"
			  
		print "</tbody></table></div>"


# ********************** cgi.main **********************

form=cgi.FieldStorage()

# **************** set defaults for the query  ********************

if form.has_key('o'):
  order=form["o"].value
else:
  order="desc"

if form.has_key('os'):
  offset=form["os"].value
else:
  offset="0"

# items per page
if form.has_key('rc'):
  rowcount=form["rc"].value
else:
  rowcount="50"

# **************** display  ********************

cdr = Cdr()

cdr.header_html(theme_light)
cdr.searchform_html()

# connect to MySQL Database
try:
  dbh = MySQLdb.Connect(host=config.get("mysql", "host"),
                        user=config.get("mysql", "user"),
                        passwd=config.get("mysql", "passwd"),
                        db=config.get("mysql", "db"))

except MySQLdb.Error, e:
  print "Error %d: %s" % (e.args[0], e.args[1])
  sys.exit (1)

cursor = dbh.cursor()

# "dispatch" and parameterize query
if form.has_key('p'): page = form["p"].value
else: page = 0

cdr.paginate_html(page, offset, rowcount)

# search query
if form.has_key('num') and not (form["num"].value==""):
  query = """select * from cdr where %s = %s order by calldate %s limit %s,%s""" % (dbh.escape_string(form["type"].value), 
                                                                                    dbh.escape_string(form["num"].value), 
                                                                                    dbh.escape_string(order), 
                                                                                    dbh.escape_string(offset), 
                                                                                    dbh.escape_string(rowcount))
  cursor.execute(query)
else:
  # defaultquery
  query = """select * from cdr order by calldate %s limit %s,%s""" % (dbh.escape_string(order), 
                                                                      dbh.escape_string(offset), 
                                                                      dbh.escape_string(rowcount))
  cursor.execute(query)

query_result = cursor.fetchall()
cursor.close()

cdr.results_html(query_result)
cdr.footer_html()
