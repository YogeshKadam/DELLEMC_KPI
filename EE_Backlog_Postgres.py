
import os
from jira import JIRA
import datetime
import psycopg2
import logging

# Setting loggers
logger= logging.getLogger("EE_Backlog_Postgres")

logger.setLevel(logging.INFO)

formatter=logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler=logging.FileHandler("/home/kpi_scripts/BACKLOG_logs/loggers_EEBacklogPostgres.log")
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

# Jira Queries for getting Sev1, Sev2, Sev3 and Sev4 incidents
query1='project = VPLEX AND issuetype = Incident AND status was in ("In Progress", New, Returned, "On Hold") ON ' +todays_date+ ' AND "Assigned Group" = vplex-ee AND "First Encountered By" in (proactive_customer, customer) AND Severity = 1-Critical'
query2='project = VPLEX AND issuetype = Incident AND status was in ("In Progress", New, Returned, "On Hold") ON ' +todays_date+ ' AND "Assigned Group" = vplex-ee AND "First Encountered By" in (proactive_customer, customer) AND Severity = 2-High'
query3='project = VPLEX AND issuetype = Incident AND status was in ("In Progress", New, Returned, "On Hold") ON ' +todays_date+ ' AND "Assigned Group" = vplex-ee AND "First Encountered By" in (proactive_customer, customer) AND Severity = 3-Moderate'
query4='project = VPLEX AND issuetype = Incident AND status was in ("In Progress", New, Returned, "On Hold") ON ' +todays_date+ ' AND "Assigned Group" = vplex-ee AND "First Encountered By" in (proactive_customer, customer) AND Severity = 4-Enhancement'

# Searching Jira Queries
try:
    issues_sev1 = jira.search_issues(query1)
    sev1_count=len(issues_sev1)
    issues_sev2 = jira.search_issues(query2)
    sev2_count=len(issues_sev2)
    issues_sev3 = jira.search_issues(query3)
    sev3_count=len(issues_sev3)
    issues_sev4 = jira.search_issues(query4)
    sev4_count=len(issues_sev4)
    total_count= sev1_count+sev2_count+sev3_count+sev4_count
except:
    logger.exception ('Error while searching JIRA query')

# Connection to postgresql instance and pushing data
try:
    connection = psycopg2.connect(user = "####", password = "####", host = "0.0.0.0", port = "5432", database = "kpi_analytics")
    cursor = connection.cursor()
    sql = """INSERT INTO ee_backlog (date, activeincidents, sev1critical, sev2high, sev3moderate, sev4enhancement) VALUES (%s, %s, %s, %s, %s, %s);"""
    cursor.execute(sql, (todays_date, total_count, sev1_count, sev2_count, sev3_count, sev4_count))
    connection.commit()
    count = cursor.rowcount
    logger.info ('Record inserted successfully, ActiveIncidents => {}'.format(total_count))
except (Exception, psycopg2.Error) as error :
    logger.exception ('Error with PostgreSQL connection')
finally:
    if connection:
        cursor.close()
        connection.close()