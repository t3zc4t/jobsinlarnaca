from datetime import datetime
from bs4 import BeautifulSoup
import requests

import mysql.connector

mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "3eT^b4$Jj1J$", database = "jobsinlarnaca$default")

mycursor = mydb.cursor()

headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'}
resultlist = []
try:
    source = requests.get("https://www.linkedin.com/jobs/search/?geoId=100932107&location=Larnaca%2C%20Cyprus&refresh=true&position=1&pageNum=0", headers).content
except requests.exceptions.RequestException as e:
    print("Crawl Error")
    raise SystemExit(e)
soup = BeautifulSoup(source, "lxml")
totalresults = soup.select_one('span.results-context-header__job-count').text
companiecount = 0

cursor=mydb.cursor(dictionary = True)

# Check all jobs and store in variable
cursor.execute("SELECT userid, companyname, title, link, platform FROM jobs")
existingcompanies = cursor.fetchall()


try:
    source = requests.get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?geoId=100932107&location=Larnaca%2C%20Cyprus&refresh=true&position=1&pageNum=0&start=0", headers).content
except requests.exceptions.RequestException as e:
    print("Crawl Error")
    raise SystemExit(e)
soup = BeautifulSoup(source, "lxml")
allsearchresults = soup.select_one('body')
while int(totalresults) > companiecount:
    for li in allsearchresults.select('li'):
        companiecount += 1
        link = li.select("a")[0].get('href').split("?")[0]
        description = ""
        if {"userid":1, "companyname":li.select('h4.base-search-card__subtitle')[0].get_text().strip(), "title": li.select('h3.base-search-card__title')[0].get_text().strip(), "link": link, "platform": "LinkedIn" } not in existingcompanies:
            resultlist.append({"date":li.select('time')[0].get('datetime'), "description":description, "platform":"LinkedIn", "title":li.select('h3.base-search-card__title')[0].get_text().strip(),"company":li.select('h4.base-search-card__subtitle')[0].get_text().strip(), "link":link})
    try:
        source = requests.get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?geoId=100932107&location=Larnaca%2C%20Cyprus&refresh=true&position=1&pageNum=0&start=" + str(companiecount)).content
    except requests.exceptions.RequestException as e:
        print("Crawl Error")
        raise SystemExit(e)
    soup = BeautifulSoup(source, "lxml")
    allsearchresults = soup.select_one('body')

for li in resultlist:
    if "date" not in li:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    else:
        date = li['date']
    try:
        sql = "INSERT INTO jobs (userid, refid, companyname, title, link, dateposted, platform) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (1, "LI"+date, li['company'], li['title'], li['link'], date, "LinkedIn")
        mycursor.execute(sql, val)
        mydb.commit()
    except mysql.connector.Error as err:
            print("MySQL Error %s",err)
mycursor.close()
mydb.close()
"""
     Scrape Sykes
        source = requests.get("https://jobs.emea.sykes.com/Search.aspx?ClassifierItem=2b4d6ec9-7b36-4746-9bc4-c6e9253b11b8&lang=en", headers).content
        soup = BeautifulSoup(source, "lxml")
        allsearchresults = soup.select_one('table#MainPlaceholder_VacancyList_SearchableDataTable_DataGrid_DataGrid')
        for tr in allsearchresults.select('tr'):
            companiecount += 1
            currdate = datetime.utcnow().strftime("%Y-%m-%d")
            sykestitle = tr.select('td:nth-child(2)>a')
            if len(sykestitle) > 0:
                resultlist.append({"platform":"Sykes", "company":"Sykes", "date":currdate, "title":tr.select('td:nth-child(2)>a')[0].get_text().strip(), "link":tr.select('td:nth-child(2)> a')[0].get('href')})

        # Scrape GRS
        source = requests.get("https://www.grsrecruitment.com/vacancies/jobs-in-larnaca/", headers).content
        soup = BeautifulSoup(source, "lxml")
        allsearchresults = soup.select_one('div.jobs-list')
        for tr in allsearchresults.select('div.vacancy'):
            companiecount += 1
            date_object = datetime.strptime(tr.select("div.meta>ul>li.date>span")[0].get_text(), '%d %B %Y').date()
            resultlist.append({"platform":"GRS Recruitment", "company":"GRS Recruitment", "title":tr.select("a")[0].get_text().strip(), "date":date_object, "link":tr.select("a")[0].get('href')})"""
