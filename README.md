# Jobs in Larnaca

## CS50 Intro
>This was my final project to conclude the CS50x course "Introduction to Computer Science", at the end of 2022.

>Technologies used: Python, Flask, Jinja (templating), jQuery, Bootstrap, JavaScript, HTML, CSS, Beautiful Soup (Web Scraping for LinkedIn Jobs), MySQL

Link to the app: https://jobsinlarnaca.pythonanywhere.com/

## Technologies used

- [Flask](https://flask.palletsprojects.com/en/2.2.x/)
- [Jinja template engine](https://jinja.palletsprojects.com/en/3.1.x/)
- [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/)

For hosting my project, I decided to go with the free version of python anywhere. Unfortunately the free version is restricted, for example you can't access the database from outside python anywhere, you can only connect to certain domains on a whitelist and I can't use a custom domain. But since it's free, it's totally fine. The only problem for me was that I wrote some web scraping code for 2 additional local job listing platforms, but since these are not included in the whitelist, I had to stick with LinkedIn only as an external source.

[Python Anywhere](https://www.pythonanywhere.com/)

For my backend I chose Flask (Python) as a web framework, for the database I've used MySQL and the frontend is a mix of HTML/CSS/JavaScript with Bootstrap and jQuery as additional libraries, for the template engine I've used Jinja because of the easy to use Python like syntax.


## Explaining the project and the database
My final project is a web app, where you can find job offers in Larnaca, Cyprus. Anyone can see job listings, whereas registered users can also publish and remove their own listings. A scheduled worker script is running 1/day and is also checking any new job listings on LinkedIn for Cyprus and updates the database accordingly if new listings are found. The database has been filled at the beginning with all jobs from LinkedIn, and now everyday the worker script is updating the database.

The project consists of 4 parts: Frontend, Backend, Database, Cronjob script

The directory looks like this:

1. Root Directory: 

- flask_app.py: The controller script, using Flask with all configuration and route settings 
- helpers.py: Some additional helper functions, used in the main flask_app.py
- .env: Storing 1 environment variable (MySQL password) and used via the dotenv module in the main flask_app.py
- cronjobscript.py: The cronjob which crawls LinkedIn jobs on a daily basis and updates the database

2. "Static" Directory:

- favicon.ico
- a logo image for "Jobs in Larnaca" which I quickly created with Canva (not too fancy)
- styles.css for some basic styling

3. "Templates" Directory:

All templates are based on the main layout.html file, where the basic structure with menu, body and footer are defined.

With the Jinja templating engine, other pages are derived from this layout file. All templates are loaded via specific routes in the main flask_app.py

- apology.html: Error page, in case something goes wrong, this file will be sent to the visitor
- getjobs.html: Using [datatables.js](https://datatables.net/), all Jobs from the database are listed here which is also the default route /. 
- job.html: For jobs published on the web app (through a user profile), all details are listed here for each job
- layout.html: This is the main layout file, from which all other files are derived
- login.html: A login page which checks if the user and password exists in the database. Passwords are hashed and encrypted.
- postjob.html: After logging in, users can publish a new job. For now only a title and job description is implemented, additionally the user id together with the current date will be added to the database.
- private_profile.html: A profile page, where the user can see their own posted jobs, remove them and update the user profile.
- public_profile.html: A public profile, where user/company information will be shown.
- register.html: Register page, where a user can register a new account. On the backend, the data will be validated.

A scraped job is linked to the LinkedIn Job description page, a job posted on the web app itself is linked to the job.html page.

## MySQL with the Python MySQL Connector

I used 2 tables for the database:

#### Table "users"
```sql
CREATE TABLE users (
userid int NOT NULL AUTO_INCREMENT,
username varchar(20) NOT NULL,
email varchar(30) NOT NULL,
companyname varchar(80),
address varchar(255),
websitelink varchar (180),
password varchar (255) NOT NULL,
logolink varchar (180),
createdtime date,
PRIMARY KEY (userid)
);
```

#### Table "jobs"
```sql
CREATE TABLE jobs (
jobid int NOT NULL AUTO_INCREMENT,
category varchar(40),
userid int NOT NULL, 
refid varchar(10), 
title varchar(100) NOT NULL, 
sdescription varchar(255), 
companyname varchar(160), 
link varchar(250), 
longdescription varchar(3200), 
dateposted date, 
platform varchar(100) NOT NULL,
PRIMARY KEY (jobid),
FOREIGN KEY (userid) REFERENCES users(userid)
);
```
For both tables, there are more columns than used, as I'm still planning to extend this project in the future where I need additional information. The jobs table uses 1 Foreign key (userid) to link a job to a specific user. Since many jobs are coming from LinkedIn where the respective user profile doesn't exist though on the web app, I had to use some workaround. For scraped jobs, the company name will be added to the companyname field of the jobs table and all associated to the user with the userid 1 (admin). Jobs posted on the web app itself will have an empty companyname in the jobs table, and use the userid+companyname from the user table. This is a bit messy, but will improve this in the future.


### Cronjob Script
I have a cronjob running 1/day which scrapes LinkedIn Jobs in Larnaca and keeps updating the jobs table in the database.


There are 3 main parts in this script:

1. First of all I need to check how many jobs are available in total, to know how many times I need to run the for loop later on. The total count of all jobs I scrape from the default LinkedIn Jobs page for Larnaca.
```python
try:
    source = requests.get("https://www.linkedin.com/jobs/search/?geoId=100932107&location=Larnaca%2C%20Cyprus&refresh=true&position=1&pageNum=0", headers).content
except requests.exceptions.RequestException as e:
    print("Crawl Error")
    raise SystemExit(e)
soup = BeautifulSoup(source, "lxml")
totalresults = soup.select_one('span.results-context-header__job-count').text
companiecount = 0
``` 

2. Next I'm scraping all jobs from all pages, using now the api URL (which I found out through developer tools), as it's easier like this instead of using the default Job page with less noise. If the job is not in the existing job listing array (this was done at the beginning, just an array of all the current jobs in the database), then it will get added to a list called "resultlist".

```python
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
```

3. Finally the "resultlist" will get added to the database (jobs table).

```python
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
``` 


## Youtube video
For the CS50 final project you had to create a screencast of the project. You can find my one here: [My Final project presentation](https://youtu.be/gEMHPsPNw0I)

## Documentation for core technologies used
https://flask.palletsprojects.com/en/2.2.x/

https://beautiful-soup-4.readthedocs.io/en/latest/

https://dev.mysql.com/doc/

## About CS50
"CS50x , Harvard University's introduction to the intellectual enterprises of computer science and the art of programming for majors and non-majors alike, with or without prior programming experience. An entry-level course taught by David J. Malan, CS50x teaches students how to think algorithmically and solve problems efficiently. Topics include abstraction, algorithms, data structures, encapsulation, resource management, security, software engineering, and web development. Languages include C, Python, SQL, and JavaScript plus CSS and HTML. Problem sets inspired by real-world domains of biology, cryptography, finance, forensics, and gaming. The on-campus version of CS50x , CS50, is Harvard's largest course.

Students who earn a satisfactory score on 9 problem sets (i.e., programming assignments) and a final project are eligible for a certificate. This is a self-paced course–you may take CS50x on your own schedule."

You can find more information here: https://pll.harvard.edu/course/cs50-introduction-computer-science

Thank you for everything, CS50, especially @dmalan, @dlloyd09, and @brianyu28!

If you want to connect with me, please add me on LinkedIn: 
[Christian Schuster on LinkedIn](https://www.linkedin.com/in/t3zc4t/)

