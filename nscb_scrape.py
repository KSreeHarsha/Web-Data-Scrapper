#!/usr/bin/env python

"""
@package css
@file css/municp_utils.py
@author K Sree Harsha
@author Edward Hunter
@brief Utility module for scraping Philippines municipality records from
http://www.nscb.gov.ph.
"""

# Standard imports.
import optparse
import time
import urllib
import datetime

# 3rd party imports.
from bs4 import BeautifulSoup

# Globals.
SLEEP_TIME = 5
MAX_TRIES = 10
BASE_URL = 'http://www.nscb.gov.ph/activestats/psgc'


def download_muni_data(first_page=1,last_page=1):
    """
    Download municipality records over range of pages and
    write records to municipality and barangay files.
    @param first_page First page of municipalities list.
    @param last_page Last page of municipalities list.
    """

    ########################################################################
    # Step one: Setup.
    ########################################################################

    # The html client.
    client = urllib.FancyURLopener({})

    # Dictionary of municipality metadata. Populated First.
    muni_metadata = {}

    # Dictonary of barangay data. Populated second.
    barangay_data = {}

    # Record full start time.
    start_time = time.time()

    ########################################################################
    # Step two: Download each municipality list page and extract metadata.
    ########################################################################

    # Announcement.
    print '='*80
    print 'Downloading Municipality Metadata'

    # Make municipality url list.
    url_list = [BASE_URL + '/listmun.asp?whichpage=%i' % page for page in
                range(first_page, last_page+1)]

    # Extract municipality metadata.
    extract_data(url_list, client, muni_metadata)

    ########################################################################
    # Step three: Download each municipality page and extract barangay data.
    ########################################################################

    # Announcement.
    print '='*80
    print 'Downloading Barangay Data'

    # Make muni_name, barangay url tuple list.
    url_list = [(key, muni_metadata[key]['name'], BASE_URL + '/' + muni_metadata[key]['href']) for
        key in muni_metadata.keys()]

    # Extract barangay data.
    extract_data(url_list, client, barangay_data)

    ########################################################################
    # Step four: write out data files.
    ########################################################################

    # Create timestamp and pages strings.
    ts = datetime.datetime.now()
    ts_string = '_%i-%i-%i__%i-%i-%i' % \
                 (ts.month, ts.day, ts.year, ts.hour, ts.minute, ts.second)
    pages_string = '_%i_%i_' % (first_page, last_page)

    # Create filenames.
    muni_fname = 'muni_metadata' + pages_string + ts_string + '.txt'
    barangay_fanme = 'barangay_data' + pages_string + ts_string + '.txt'

    # Open files.
    muni_file = open(muni_fname,'w')
    barangay_file = open(barangay_fanme,'w')

    # Write out data.
    muni_keys = muni_metadata.keys()
    muni_keys.sort()
    for muni_key in muni_keys:
        muni_val = muni_metadata[muni_key]
        muni_line = '%-50s %-15s %-50s %-10s %-15s %-15s %-25s\n' % \
            (muni_val['name']+',', muni_val['code']+',', muni_val['province']+',',
             muni_val['income_class']+',', muni_val['registered_voters']+',',
             muni_val['population']+',',  muni_val['land_area'])
        muni_file.write(muni_line)

        barangay_keys = barangay_data[muni_key].keys()
        barangay_keys.sort()
        for barangay_key in barangay_keys:
            barangay_vals = barangay_data[muni_key][barangay_key]
            barangay_line = '%-50s %-50s %-15s %-15s %-15s\n' % \
                (barangay_vals['muni_name']+',', barangay_vals['name']+',', barangay_vals['code']+',',
                 barangay_vals['urban_rural']+',',barangay_vals['population'])
            barangay_file.write(barangay_line)

    # Close files.
    muni_file.close()
    barangay_file.close()

    # Announcement.
    delta = time.time() - start_time
    print '='*80
    print 'Done. All data downloaded in %f minutes.' % (delta/60.0)
    print '='*80


def extract_data(url_list, client, data):
    """
    Open and read URLs. Parse HTML. Extract data from soup.
    Populate data dictionary. Populates municipality metadata if url_list
    is a list of url strings, or barangay data if url_list is a list of
    (muni_name, url) tuples.
    @param url_list List of urls or (muni_name, url) tuples.
    @param client Html client.
    @param data Data dictionary to populate.
    """

    # Download pages one at a time.
    # Get url or url and muni_name from url_list.
    for x in url_list:
        if isinstance(x,tuple):
            muni_key = x[0]
            muni_name = x[1]
            url = x[2]
        else:
            muni_key = None
            muni_name = None
            url = x

        # Record start time, set tries to 0.
        start_time = time.time()
        no_tries = 0

        # Catch IO errors and retry as necessary.
        while True:
            try:

                # Open url.
                html = client.open(url)

                # Parse html into navigable soup.
                soup = BeautifulSoup(html)

                # Locate the table rows containing data.
                body = soup.find_all('div', id='pageBody')
                tables = body[0].find_all('table')

                ########################################################################
                # Extract municipality metadata if muni_name not specified.
                ########################################################################
                if not muni_name:

                    # Extract the muni metadata from cells in table 1 onward.
                    rows = tables[1].find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        name = cells[0].get_text().encode('ascii','ignore').strip()
                        code = cells[1].get_text().encode('ascii','ignore').strip()
                        muni_key = '%s-%s' % (name, code)
                        data[muni_key] = {}
                        data[muni_key]['href'] = cells[0].p.a['href']
                        data[muni_key]['name'] = name
                        data[muni_key]['code'] = code
                        data[muni_key]['province'] = cells[2].get_text().encode('ascii','ignore').strip()
                        data[muni_key]['income_class'] = cells[3].get_text().encode('ascii','ignore').strip()
                        data[muni_key]['registered_voters'] = cells[4].get_text().encode('ascii','ignore').strip().replace(',','')
                        data[muni_key]['population'] = cells[5].get_text().encode('ascii','ignore').strip().replace(',','')
                        data[muni_key]['land_area'] = cells[6].get_text().encode('ascii','ignore').strip().replace(',','')

                ########################################################################
                # Extract Barangay data if muni_name specified with url list.
                ########################################################################
                else:

                    # Extract baragay data from cells in table 3 onward.
                    for i in range(3, len(tables)):
                        cells = tables[i].find_all('td')
                        name = cells[0].get_text().encode('ascii','ignore').strip()
                        code = cells[1].get_text().encode('ascii','ignore').strip()
                        barangay_key = '%s-%s' % (name, code)
                        if not muni_key in data:
                            data[muni_key] = {}
                        data[muni_key][barangay_key] = {}
                        data[muni_key][barangay_key]['muni_name'] = muni_name
                        data[muni_key][barangay_key]['name'] = name
                        data[muni_key][barangay_key]['code'] = code
                        data[muni_key][barangay_key]['urban_rural'] = cells[2].get_text().encode('ascii','ignore').strip().split()[0]
                        data[muni_key][barangay_key]['population'] = cells[3].get_text().encode('ascii','ignore').strip().replace(',','')

                # Done. Move on to next page.
                break

            # Catch IO errors and retry after brief wait.
            except IOError as ex:
                print 'IOError reading: %s, %s' % (url, ex)
                no_tries += 1
                if no_tries >= MAX_TRIES:
                    print 'Exceeded max tries for page, giving up.'
                    continue
                time.sleep(SLEEP_TIME)

        # Success, report download and parse time.
        delta = time.time() - start_time
        if not muni_name:
            print 'Downloaded and parsed %s in %f seconds.' % (url, delta)
        else:
            print 'Downloaded and parsed %s for %s in %f seconds.' % (url, muni_name, delta)


if __name__=='__main__':

	 # Parse command line arguments and options.
    usage = 'usage: %prog [options]'
    description = 'Download Philippines municipality records from http://www.nscb.gov.ph.'
    p = optparse.OptionParser(usage=usage, description=description)
    p.add_option('-f','--first_page', action='store', dest='first_page',
                 type='int',help='First page to download')
    p.add_option('-l','--last_page', action='store', dest='last_page',
                 type='int', help='Last page to download')
    p.set_defaults(first_page=1, last_page=1)

    (opts, args) = p.parse_args()
    first_page=opts.first_page
    last_page=opts.last_page

    # Download and store data.
    download_muni_data(first_page,last_page)
