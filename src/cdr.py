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
  return t9n[lang][msgid]


def find_protocol(str):
  if (str.find('mISDN') != -1): return 'mISDN'
  if (str.find('SIP') != -1): return 'SIP'
  if (str.find('IAX2') != -1): return 'IAX2'
  return 'default'


# **********************************************************************

class Cdr:
	html = ""
	def header_html(self):
		try:
			style = open(get_default_confval('general', 'theme', 'theme_light.css'), 'r').read() 
		except (IOError), e:
			style = "/* default theme `theme_light.css' not found */"
		vars = {"style": style, "title": "CPBX Calldetails"}
  		print "Content-type: text/html"
  		print
		print "<!DOCTYPE html><html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">"
		print "<style>%(style)s</style><title>%(title)s</title></head><body><div id=body><div id=header><h1>%(title)s</h1></div>\n" % vars

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


	def paginate_html(self):
		page = self.page
		offset = self.offset
		rowcount = self.rowcount
		order = self.order
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

	
	def action_list(self):
		self.header_html()
		self.searchform_html()

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

		self.paginate_html()

		# search query
		if form.has_key('num') and not (form["num"].value==""):
		  query = """select * from cdr where %s = %s order by calldate %s limit %s,%s""" % (dbh.escape_string(form["type"].value), 
																							dbh.escape_string(form["num"].value), 
																							dbh.escape_string(self.order), 
																							dbh.escape_string(self.offset), 
																							dbh.escape_string(self.rowcount))
		  cursor.execute(query)
		else:
		  # defaultquery
		  query = """select * from cdr order by calldate %s limit %s,%s""" % (dbh.escape_string(self.order), 
																			  dbh.escape_string(self.offset), 
																			  dbh.escape_string(self.rowcount))
		  cursor.execute(query)

		query_result = cursor.fetchall()
		cursor.close()
		cdr.results_html(query_result)
		cdr.footer_html()

	
	def evaluate_params(self):
		""" self.order, self.offset, self.rowcount, self.page """
		# order
		if form.has_key('o'):
  			self.order=form["o"].value
		else:
		  self.order="desc"
		# offset
		if form.has_key('os'):
		  self.offset=form["os"].value
		else:
		  self.offset="0"
		# items per page
		if form.has_key('rc'):
		  self.rowcount=form["rc"].value
		else:
		  self.rowcount="50"
		# page	  
		if form.has_key('p'): 
			self.page = form["p"].value
		else: 
			self.page = 0
		# action
		if form.has_key('a'): 
			self.action = "action_" + form["a"].value
		else: 
			self.action = "action_list"

	def dispatch(self):
		if hasattr(self, self.action):
			_action = getattr(self, self.action)()

	def run(self):
		self.dispatch()

	def __init__(self):
		self.evaluate_params()

		
# **********************************************************************

form = cgi.FieldStorage()

cdr = Cdr()
if __name__ == '__main__':
    cdr.run()
