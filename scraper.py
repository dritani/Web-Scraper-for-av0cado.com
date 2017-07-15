import csv
import requests
import random
import bs4
import string
import re
import time
import threading
import datetime
import os

# Limit the number of threads.
pool = threading.BoundedSemaphore(10)
results = open("index.html",'w+')
includedWords = ["ios","mobile","app developer"]
excludedWords = ["senior","mechanic","repair","mobile marketing","intern"]
timeLimit = datetime.datetime.now() - datetime.timedelta(days=7)
currentYear = str(datetime.datetime.now().year)
currentMonth = datetime.datetime.now().month
done = False
rez = []

class Result(object):

     def __init__(self, title, hyperlink, date):
         self.title = title
         self.hyperlink = hyperlink
         self.date = date

     def __lt__(self, other):
         return self.date < other.date


def getProxiesFromWebsite():

	r = requests.get("http://www.us-proxy.org/")

	soup = bs4.BeautifulSoup(r.content)
	extracted = []
	table = soup.find('table', attrs={'id':'proxylisttable'})
	table_body = table.find('tbody')

	rows = table_body.find_all('tr')
	for row in rows:
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		extracted.append([ele for ele in cols if ele]) # Get rid of empty values
	
	proxies = []
	for i in range(20):
		proxy = {'http':str(extracted[i][0]+":"+extracted[i][1])}
		proxies.append(proxy)

	return proxies

def getUserAgentsFromFile(uafile="user_agents.txt"):
	"""
	uafile : string
		path to text file of user agents, one per line
	"""
	uas = []
	with open(uafile, 'rb') as uaf:
		for ua in uaf.readlines():
			if ua:
				uas.append(ua.strip()[1:-1-1])
	random.shuffle(uas)
	return uas

def worker(url,section="",proxy=None,headers=None):
	r = requests.get(url+section,proxies=proxy,headers=headers)

	#r = requests.get("https://newyork.craigslist.org/search/sof")

	soup = bs4.BeautifulSoup(r.content)

	links = soup.find_all('a', {"class" : "result-title hdrlnk" }, href=True)
	dates = soup.find_all('time',{"class":"result-date"})

	for (i,a) in enumerate(links):
		if a['href'][:2]!="//":

			date = dates[i]['title']
			date2 = date[4:].split(" ")
			dateString = " ".join([date2[0],date2[1], currentYear if currentMonth - int(datetime.datetime.strptime('Feb','%b').month) >= 0 else currentYear-1,date2[2],date2[3]])
			dateDate = datetime.datetime.strptime(dateString, "%d %b %Y %I:%M:%S %p")

			if dateDate<timeLimit:
				break
			
			include = False
			exclude = False

			for word in includedWords:
				include = len(re.findall('\\b%s\\b' % word, a.text.lower())) > 0 or include

			for word in excludedWords:
				exclude = len(re.findall('\\b%s\\b' % word, a.text.lower())) > 0 or exclude

			if include and not exclude:

				title = re.sub('[,]', '', a.text)
				hyperlink = url + a['href']	
				rez.append(Result(title,hyperlink,dateDate))

				#result = re.sub('[,]', '', a.text) + "," + url + a['href']+ '\n'

	# Release lock for other threads.
	pool.release()



def main():
	
	proxies = getProxiesFromWebsite()
	uas = getUserAgentsFromFile()

	results.write('<html xmlns="http://www.w3.org/1999/xhtml"><head>')
	results.write('<link rel=stylesheet type="text/css" href="index2.css">')
	results.write('<link rel="shortcut icon" href="favicon.ico"></head>')
	results.write('<body><img src="logo.png" style="width:200;height:78;">')
	results.write('<br><br>')

	sections = ['/search/sof','/search/eng']#'/search/cpg'
	
	#i = 0

	with open("craigslist.txt",'rb') as crg:
		for url in crg.readlines():
			if url:
				for section in sections:

					proxy = random.choice(proxies)

					ua = random.choice(uas)
					headers = {
					"Connection" : "close",
					"User-Agent" : ua}

					print("Scanning " + url[:-1] + section + " with proxy: " + proxy['http'])

					# Thread pool.
					# Blocks other threads (more than the set limit).
					pool.acquire(blocking=True)
					# Create a new thread.
					# Pass each URL (i.e. u parameter) to the worker function.
					t = threading.Thread(target=worker, args=(url[:-1],section,proxy,headers))
					# Start the newly created thread.
					t.start()
						
						#i+=1
	

	while 1:
		if threading.active_count()<=1:
			allowedChars = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-+!?(#).=_ ')
				
			for r in sorted(rez,reverse=True):
				newTitle = ""
				for letter in r.title:
					if letter in allowedChars:
						newTitle += letter
				print(newTitle)
				results.write('<time class="result-date" >' + r.date.strftime('%b')+" " +r.date.strftime('%d') + '</time>')
				results.write('<span style="display:inline-block; width: 10;"></span>')
				results.write('<a href='+'"'+r.hyperlink+'"' + 'class="result-title hdrlnk" style="color:green">' + newTitle + '</a>')
				results.write('<span style="display:inline-block; width: 10;"></span>')
				right = r.hyperlink[8:]
				dot = right.find(".")
				results.write("Craigslist " + right[:dot])
				results.write('<br><br>')
				
			results.write('</body></html>')
			results.close()

			exit()


main()


# TODO
# =========
# european craigslist
# add kijiji.ca
# gumtree? uk
# https://www.quoka.de/ germany
# https://www.leboncoin.fr/ france
# upwork?

# SOURCES
# =======
# http://willdrevo.com/using-a-proxy-with-a-randomized-user-agent-in-python-requests/
# http://jakeaustwick.me/python-web-scraping-resource/
# https://firebase.googleblog.com/2017/03/how-to-schedule-cron-jobs-with-cloud.html
# https://firebase.googleblog.com/2014/01/queries-part-2-advanced-searches-with.html
# http://leighappel.com/tor-the-onion-router-hidden-services.html
# https://www.google.com/search?q=Flask+AJAX+jQuery&oq=Flask+AJAX+jQuery&aqs=chrome..69i57&sourceid=chrome&ie=UTF-8




