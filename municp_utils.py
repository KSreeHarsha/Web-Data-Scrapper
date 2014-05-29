#!/usr/bin/env python

"""
@package css
@file css/municp_utils.py
@author K Sree Harsha
@brief Utility module for retrieving congress.gov data.
"""

from mechanize import Browser
from BeautifulSoup import BeautifulSoup
import re
import urllib
import csv
import optparse

def download_municipality_by_page(first_page,last_page):
	for page_no in range(first_page,(last_page+1)):
		
		mech = Browser()
		url = "http://www.nscb.gov.ph/activestats/psgc/listmun.asp?whichpage=%i"%(page_no)
		print url
		page = mech.open(url)

		count=0
		NO_TRIES=10
		pattern1='municipality.asp'
		expr1 = re.compile(pattern1)
		MunicipalityList=[]

		while True:
		        try:
			    html = page.read()
			    soup = BeautifulSoup(html)
		            tags1 = soup.findAll(href=expr1)
		            tableMunicipality=soup.findAll("table",{'width':'550'})
		            tries = 0
		            break
		
		        except IOError as ex:
		            print 'ERROR: ' + str(ex)
		            tries += 1
		            if tries > NO_TRIES:
		                raise
		            time.sleep(SLEEP_TIME)


		for t in tableMunicipality:
			row=t.findAll('tr')
			for r in row:
		             col = r.findAll('td')
		             C0=col[0].findAll('a')
		             for c in C0:
		            	 MunicipalityName=c.getText()
		            	 MunicipalityList.append(MunicipalityName)

		print 'Municipalities on this page'
		for m in MunicipalityList:
			print m
		BASE_URL='http://www.nscb.gov.ph/activestats/psgc/'

		for tag in tags1:
		    count += 1
	        # Construct the daily congress url.
		    municipality_url = BASE_URL + tag['href']
		    print '-'*80
		    print 'Extracting: %s' % municipality_url
		    municipality_page=mech.open(municipality_url)
		    html = municipality_page.read()
		    municipalitySoup = BeautifulSoup(html)
		    tables = municipalitySoup.findAll("table",{'width':'500','cellpadding':'3'})
	

		    skip=0
		    path=MunicipalityList[count-1]+".csv"
		    print "Writting File:",path
		    with open(path, "wb") as csv_file:
		    	writer = csv.writer(csv_file, delimiter=',')
	   
		    	for t in tables:
		        	if(skip<1):
		    	    		skip=1
			    		continue
		        	row=t.find('tr')
		        	col = row.findAll('td')
		        	Name = col[0].string
		        	Code = col[1].string
		        	U_R = col[2].string
		        	Population = col[3].string
		        	record = (Name, Code,U_R.strip(),Population)
		        	record= "|".join(record)
		        	try:
		        		writer.writerow(record.split("|"))
		        	except (UnicodeEncodeError, UnicodeDecodeError):
		   			print "Caught unicode error, could not save record",record
		   			Name="MISSING NAME(ERROR)"
		   			record = (Name, Code,U_R.strip(),Population)
		   			record= "|".join(record)
		   			writer.writerow(record.split("|"))
    
    

if __name__=='__main__':

	 # Parse command line arguments and options.
    usage = 'usage: %prog [options]'
    description = 'Download municipality records.'
    p = optparse.OptionParser(usage=usage, description=description)
    p.add_option('-f','--first_page', action='store', dest='first_page',
                 type='int',help='First Page to download')
    p.add_option('-l','--last_page', action='store', dest='last_page',
                 type='int', help='Last Page to download')
    p.set_defaults(first_page=1, last_page=1)

    (opts, args) = p.parse_args()
    first_page=opts.first_page
    last_page=opts.last_page

    print "Downloading pages from ",first_page," to ",last_page

    download_municipality_by_page(first_page,last_page)
