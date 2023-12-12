from flask import Flask, render_template, jsonify, request
import pyrebase, datetime, calendar, pytz, requests, time, random, keys, logging
import datetime
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from cachelib import SimpleCache

app = Flask(__name__)
Config = {"apiKey": "AIzaSyCCTeiCYTB_npcWKKxl-Oj0StQLTmaFOaE",
          "authDomain": "marketing-data-d141d.firebaseapp.com",
          "databaseURL": "https://marketing-data-d141d-default-rtdb.firebaseio.com/",
          "storageBucket": "marketing-data-d141d.appspot.com",}
firebase = pyrebase.initialize_app(Config)
db = firebase.database()
my_app_id = '622623732603375'
my_app_secret = '0137ae3314de2038f8984483045eeae4'
my_access_token = keys.facebook_acces_token
ad_acc_id = "act_407900737581426"
FacebookAdsApi.init(my_app_id, my_app_secret, my_access_token)
cache = SimpleCache()
    
@app.route('/')
def home():    
           try:
                ad_account = AdAccount(ad_acc_id)
                fields = [
                    AdsInsights.Field.ad_name,
                    AdsInsights.Field.actions,
                ]
                params = {
                    'level': 'ad',
                    'date_preset': 'today',
                    'action_breakdowns': ['action_type'],
                    'filtering': [
                        {
                            'field': 'ad.effective_status',
                            'operator': 'IN',
                            'value': ['ACTIVE']
                        },
                    ],
                }
                
                try:
                    insights = get_insights(ad_account, fields, params)
                except FacebookRequestError as e:
                    print(f"Failed to retrieve insights: {e}")
                    exit(1)
                
                facebookleads = []
                totaladleads = 0
                for insight in insights:
                    lead_count = 0
                    if 'actions' in insight:
                        for action in insight['actions']:
                            if action['action_type'] == 'lead':
                                lead_count = int(action['value'])
                                break
                    facebookleads.append({
                        'ad_name': insight['ad_name'],
                        'lead_count': lead_count,
                    })
                    totaladleads += lead_count
                
                leaddata = {
                    "totaladleads": totaladleads,
                    "facebooklead": facebookleads
                }

                dtNow = datetime.datetime.now()
                curr_day = int(dtNow.strftime("%d"))
                curr_year = dtNow.year
                current_month = dtNow.month
                current_month_name = calendar.month_name[dtNow.month]
                curr_month = str(dtNow.month).zfill(2)
                curr_date=dtNow.strftime("%d-%m-%Y")
                year = dtNow.isocalendar()[0]
                curr_week = dtNow.isocalendar()[1]
                allDataBase = db.get().val()
                PRpoints = allDataBase["PRPoints"]
                month_dates=(curr_year,current_month) 
                user_data = []  
        
                for uid, user_info in PRpoints.items():
                    name = user_info.get("name", "")
                    target = user_info.get("target", {}).get("points", 0)
                    achieved = user_info.get("achieved", {}).get("points", 0)
                    salescount = user_info.get("salescount", {}).get("count", 0)
                    visits = user_info.get("visits", {}).get("count", 0)
                    percent = (int(achieved) / int(target) * 100) if target else 0                    
                    user_data.append({"name": name,"target": target,"achieved": achieved,"percent": round(percent, 2),"salescount": salescount,"visits": visits})
        
                achieved1 = allDataBase["PRDashboard"]["prtarget"]["totalprgettarget"]
                target1 = allDataBase["PRDashboard"]["prtarget"]["totalprtarget"]
                percentage = (int(achieved1) / int(target1)) * 100
                progress = allDataBase["PRDashboard"]["progress"]
                current_month = datetime.datetime.now().strftime("%Y-%m")
                daily_sales_data = db.child("PRDashboard").child("daily_sales_report").child(current_month).get().val()

                data = []
                if daily_sales_data:
                    for i in range(1, 7):
                        day = (datetime.datetime.now() - datetime.timedelta(days=i)).day
                        day_data = daily_sales_data.get(str(day).zfill(2))
        
                        if day_data:
                            day_data['date'] = f"{current_month}-{str(day).zfill(2)}"
                            data.append(day_data)
                       
                employee_of_week_uid=allDataBase["PRDashboard"]["employee_of_week"]["person"]
                employee_of_week_reason=allDataBase["PRDashboard"]["employee_of_week"]["reason"]
                employee_of_week_name=allDataBase["staff"][employee_of_week_uid]["name"]
                employee_of_week_profile=allDataBase["staff"][employee_of_week_uid]["profileImage"]
        
                current_date = datetime.datetime.now()
                year = current_date.year
                month = current_date.month
                last_day_of_month = (datetime.datetime(year, month + 1 if month < 12 else 1, 1) - datetime.timedelta(days=1))
                
                while last_day_of_month.month != current_date.month:
                    last_day_of_month -= timedelta(days=1)
                
                remaining_days = (last_day_of_month - current_date).days + 1
                formatted_last_day = last_day_of_month.strftime("%Y-%m-%d")
                
                remaining_days = f"{formatted_last_day}T00:00:00"
                percentageround = int(percentage)
                                
                absentCount = cache.get('absentCount')
                presentCount = cache.get('presentCount')
                totalstaff = cache.get('totalstaff')
                try:
                    absentees_response = requests.get('http://3.110.161.248:9000/Absent_Staff_Name')
                    absentees_response.raise_for_status()
                    absentees_data = absentees_response.json()
                    absentCount = int(absentees_data[0].split("=")[1].strip())
                except Exception as e:
                                    print(e)
                                    absentCount = 0
                try:
                    present_response = requests.get('http://3.110.161.248:9000/Present_Staff_Name')
                    present_response.raise_for_status()
                    present_data = present_response.json()
                    presentCount = int(present_data[0].split("=")[1].strip())
                except Exception as e:
                                    print(e)
                
                totalstaff = (absentCount)+(presentCount)
                        
                cache.set('absentCount', absentCount, 300)
                cache.set('presentCount', presentCount, 300)
                cache.set('totalstaff', totalstaff, 300)

                context={
                    "data": data,
                    "user_data":user_data,
                    "employee_of_week_name":employee_of_week_name,
                    "employee_of_week_profile":employee_of_week_profile,
                    "employee_of_week_reason":employee_of_week_reason,
                    "presentCount":presentCount,
                    "absentCount":absentCount,
                    "totalstaff":totalstaff,
                    "curr_year":curr_year,
                    "curr_week":curr_week,
                    "curr_date":curr_date,
                    "curr_month":current_month_name,
                    "achieved1":achieved1,
                    "target1":target1,
                    "percentage":percentage,
                    "percentageround":percentageround,
                    "month":remaining_days,
                    "last_date":formatted_last_day
                }
                return render_template('dashboard.html', **context, leaddata=leaddata)
           except Exception as e:
                    return handle_error(e)

def get_insights(ad_account, fields, params, retries=5):
    for i in range(retries):
        try:
            insights = ad_account.get_insights(fields=fields, params=params)
            return insights
        except FacebookRequestError as e:
            print(f"An error occurred: {e}")
            delay = 2
            if e.api_error_code() == 80000 and i < retries - 1:
                print(f"Rate limited. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
                delay += random.uniform(1, 3)
            else:
                raise
            
logging.basicConfig(level=logging.INFO)            
@app.errorhandler(Exception)
def handle_error(e):
    error_message = f"An error occurred: {str(e)}"
    return render_template('dashboard.html', error_message=error_message)

@app.errorhandler(Exception)
def error_handler(e):
    return handle_error(e)
                
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
