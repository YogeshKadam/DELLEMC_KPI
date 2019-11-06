
from jira import JIRA
import datetime
import psycopg2
import logging

# Setting loggers
logger= logging.getLogger("EE_SLA_Postgres")

logger.setLevel(logging.INFO)

formatter=logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler=logging.FileHandler("/home/kpi_scripts/SLA_logs/loggers_EESLAPostgres.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Jira server authentication
try:
    jira_server = "https://jira.cec.lab.emc.com:8443/"
    jira_user = "######"     #NTID
    jira_password = "######"       #Password
    jira_server = {'server': jira_server, 'verify': False}
    jira = JIRA(options=jira_server, basic_auth=(jira_user, jira_password))
except:
    logger.exception ('Error with JIRA Authentication')

todays_date=str(datetime.date.today())

tomorrows_date=str(datetime.date.today()+datetime.timedelta(days=1))

# Jira Query for getting Sev1 incidents
query='project = VPLEX AND issuetype = Incident AND Severity = 1-Critical AND "Assigned Group" = vplex-ee AND "First Encountered By" in (proactive_customer, customer) AND created >= ' + todays_date + ' AND created < ' + tomorrows_date

list_of_issues_per_day=[]

# Searching Jira Query and calculating time taken for Sev1 incidents to get assignee
try:
    issues_sev1 = jira.search_issues(query)
    for issue in issues_sev1:
        createdDate=str(issue.fields.created)
        issue = jira.issue(str(issue.key), expand='changelog')
        changelog = issue.changelog
        list_of_statuses=[]
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'assignee':
                    list_of_statuses.append(history.created)
        start=createdDate.split('.')[0].replace('T', ' ')
        inprogress_date=list_of_statuses[0]
        end=inprogress_date.split('.')[0].replace('T', ' ')
        start1 = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end1 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        diff=end1-start1
        if str(diff).find('day') > -1:
            days=int(str(diff).split(',')[0].replace('days','').replace('day','').replace(' ',''))
            time_str=str(diff).split(',')[1].replace(' ','')
            minutes=(int(str(time_str).split(':')[0]) * 60) + int(str(time_str).split(':')[1])
            minutes=(days * 24 * 60) + minutes
        else:
            minutes=(int(str(diff).split(':')[0]) * 60) + int(str(diff).split(':')[1])
        list_of_issues_per_day.append((str(issue.key), start, end, minutes))
except:
    logger.exception ('Error while searching JIRA query/ Calculating InProgress time.')

# Connection to postgresql instance and pushing data
if list_of_issues_per_day:
    try:
        connection = psycopg2.connect(user = "####", password = "####", host = "0.0.0.0", port = "5432", database = "kpi_analytics")
        cursor = connection.cursor()
        sql = """insert into sla_sev1_new (incidentnumber, creationdate_est, triagingdate_est, triagingminutes) values (%s, %s, %s, %s);"""
        cursor.executemany(sql, list_of_issues_per_day)
        connection.commit()
        count = cursor.rowcount
        logger.info ('Record inserted successfully, SLA_Sev1_Incidents => {}'.format(count))
    except (Exception, psycopg2.Error) as error :
        logger.exception ('Error with PostgreSQL connection')
    finally:
        #closing database connection.
        if connection:
            cursor.close()
            connection.close()
else:
    logger.info ('No Sev1 issues found!!!!!')