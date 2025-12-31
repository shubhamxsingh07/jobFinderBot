import requests
import json
import os
import datetime
from datetime import timedelta, timezone
import time
from bs4 import BeautifulSoup
import html
from email.utils import parsedate_to_datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
SEEN_JOBS_PATH = os.path.join(BASE_DIR, 'seen_jobs.json')
LOG_PATH = os.path.join(BASE_DIR, 'bot.log')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def log(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {message}\n')

# --- DATA STORAGE ---
def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_PATH):
        try:
            with open(SEEN_JOBS_PATH, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen_jobs(seen_jobs):
    seen_list = list(seen_jobs)[-1000:]
    with open(SEEN_JOBS_PATH, 'w') as f:
        json.dump(seen_list, f)

# --- FILTERING LOGIC ---
def is_usa_location(location):
    if not location:
        return True # specific USA scrapers might not have location data, assume True
    loc_lower = location.lower()
    usa_locations = ['usa', 'united states', 'us', 'remote', 'new york', 'san francisco', 'austin', 'seattle', 'boston', 'los angeles', 'chicago', 'denver', 'washington', 'california', 'texas', 'florida']
    return any(city in loc_lower for city in usa_locations)

def is_relevant(title, location, config):
    title_lower = title.lower()
    
    # Check Location (USA)
    if location and location != 'Remote':
        if not is_usa_location(location) and 'remote' not in location.lower():
             pass

    # Check Roles
    role_match = any(role in title_lower for role in config['roles'])
    if not role_match:
        return False

    # Check Excludes
    for kw in config['keywords_exclude']:
        if kw in title_lower:
            return False

    # Check Includes
    include_match = any(kw in title_lower for kw in config['keywords_include'])
    return include_match

def is_recent(date_obj):
    if not date_obj:
        return False
    # Ensure date_obj is timezone-aware (assume UTC if not)
    if date_obj.tzinfo is None:
        date_obj = date_obj.replace(tzinfo=timezone.utc)
    
    now = datetime.datetime.now(timezone.utc)
    # Check if within last 24 hours
    return (now - date_obj) <= timedelta(hours=24)

# --- SCRAPERS ---
def fetch_google_jobs(config, region='USA'):
    # Define location specific parameters
    if region == 'India':
        location_term = 'India'
        gl_param = 'IN'
        ceid_param = 'IN:en'
    else: # Default to USA
        location_term = 'USA'
        gl_param = 'US'
        ceid_param = 'US:en'

    # Dynamic Experience Query
    exp_keywords = config.get('keywords_include', ["entry level"])
    # Use first few keywords for the query to keep it valid
    query_keywords = exp_keywords[:3] 
    exp_query = "(" + " OR ".join([f'"{k}"' for k in query_keywords]) + ")"

    # Added "when:1d" to queries for Google Search time filtering
    queries = [
        f'site:greenhouse.io (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:lever.co (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:workday.com (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:linkedin.com/jobs (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:indeed.com (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:glassdoor.com (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:monster.com (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:dice.com (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:ziprecruiter.com (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:simplyhired.com (software engineer OR developer) {location_term} {exp_query} when:1d',
        f'site:careerbuilder.com (software engineer OR developer) {location_term} {exp_query} when:1d'
    ]
    
    jobs = []
    base_url = 'https://news.google.com/rss/search'
    
    for q in queries:
        try:
            params = {'q': q, 'hl': 'en-US', 'gl': gl_param, 'ceid': ceid_param}
            resp = requests.get(base_url, params=params, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'xml')
                items = soup.find_all('item')
                for item in items:
                    # Date Check
                    pub_date_str = item.pubDate.text if item.pubDate else None
                    posted_date = "N/A"
                    if pub_date_str:
                        try:
                            pub_date = parsedate_to_datetime(pub_date_str)
                            posted_date = pub_date.strftime('%Y-%m-%d %H:%M')
                            if not is_recent(pub_date):
                                continue
                        except:
                            pass

                    raw_title = item.title.text
                    link = item.link.text
                    guid = item.guid.text if item.guid else link
                    
                    # Parsing: "Job Application for [Role] at [Company] - [Source]"
                    clean_title = raw_title.split(' - ')[0]
                    role = clean_title
                    company = 'Career Page'
                    
                    if ' at ' in clean_title:
                        parts = clean_title.split(' at ')
                        company = parts[-1].strip()
                        role = parts[0].replace('Job Application for ', '').strip()

                    # Use location_term for relevance check, but allow some flexibility
                    if is_relevant(role, location_term, config):
                        jobs.append({
                            'id': guid,
                            'role': role,
                            'company': company,
                            'location': location_term,
                            'link': link,
                            'posted_date': posted_date
                        })
            time.sleep(1)
        except Exception as e:
            log(f'Error fetching Google Jobs ({q}): {e}')
    return jobs

def fetch_remoteok(config):
    url = 'https://remoteok.com/api'
    headers = {'User-Agent': 'Mozilla/5.0'}
    jobs = []
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data[1:]:
                # Date Check
                date_str = item.get('date')
                posted_date = "N/A"
                if date_str:
                    try:
                        job_date = datetime.datetime.fromisoformat(date_str)
                        posted_date = job_date.strftime('%Y-%m-%d %H:%M')
                        if not is_recent(job_date):
                            continue 
                    except:
                        pass

                title = item.get('position', '')
                company = item.get('company', '')
                location = item.get('location', '')
                link = item.get('url', '')
                job_id = item.get('id', link)

                if is_relevant(title, location, config):
                    jobs.append({
                        'id': str(job_id),
                        'role': title,
                        'company': company,
                        'location': location,
                        'link': link,
                        'posted_date': posted_date
                    })
    except Exception as e:
        log(f'Error fetching RemoteOK: {e}')
    return jobs

def fetch_weworkremotely(config):
    url = 'https://weworkremotely.com/remote-jobs.rss'
    jobs = []
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'xml')
            items = soup.find_all('item')
            for item in items:
                # Date Check
                pub_date_str = item.pubDate.text if item.pubDate else None
                posted_date = "N/A"
                if pub_date_str:
                    try:
                        pub_date = parsedate_to_datetime(pub_date_str)
                        posted_date = pub_date.strftime('%Y-%m-%d %H:%M')
                        if not is_recent(pub_date):
                            continue
                    except:
                        pass

                raw_title = item.title.text
                link = item.link.text
                guid = item.guid.text
                
                # WWR titles are often "Company: Role"
                company = 'See Link'
                role = raw_title
                if ': ' in raw_title:
                    parts = raw_title.split(': ')
                    company = parts[0].strip()
                    role = parts[1].strip()

                if is_relevant(role, 'Remote', config):
                    jobs.append({
                        'id': guid,
                        'role': role,
                        'company': company,
                        'location': 'Remote',
                        'link': link,
                        'posted_date': posted_date
                    })
    except Exception as e:
        log(f'Error fetching WWR: {e}')
    return jobs

# --- NOTIFICATION ---
def send_telegram(job, config, job_type="Job"):
    token = config['telegram_bot_token']
    chat_id = config['telegram_chat_id']
    
    if 'YOUR_' in token:
        log('Telegram token not set.')
        return

    msg = (
        f'🆕 <b>{job_type} Alert</b>\n\n'
        f'<b>Role:</b> {html.escape(job["role"])}\n'
        f'<b>Company:</b> {html.escape(job["company"])}\n'
        f'<b>Location:</b> {html.escape(job["location"])}\n'
        f'<b>Posted:</b> {job.get("posted_date", "N/A")}\n'
        f'Apply 👉 {job["link"]}'
    )
    
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'}
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        log(f'Error sending TG: {e}')

def send_telegram_summary(count, interval, config):
    token = config['telegram_bot_token']
    chat_id = config['telegram_chat_id']
    
    msg = (
        f"✅ <b>Scan Complete</b>\n"
        f"Found {count} new jobs.\n\n"
        f"😴 <b>Sleeping for {interval} minutes...</b>\n"
        f"I will be back with more jobs soon! 👋"
    )
    
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'}
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        log(f'Error sending TG summary: {e}')

def process_and_send_jobs(jobs, seen_jobs, config, job_type="Job"):
    new_jobs = [j for j in jobs if j['id'] not in seen_jobs]
    sent_count = 0
    
    chunk_size = 10
    for i in range(0, len(new_jobs), chunk_size):
        chunk = new_jobs[i:i + chunk_size]
        for job in chunk:
            send_telegram(job, config, job_type)
            seen_jobs.add(job['id'])
            sent_count += 1
            time.sleep(1) # Small delay to avoid hitting rate limits instantly
        
        # If there are more chunks coming, wait 1 minute
        if i + chunk_size < len(new_jobs):
            log(f'Sent {len(chunk)} jobs. Waiting 1 minute before next batch...')
            time.sleep(60)
            
    return sent_count

# --- INTERACTION ---
def get_updates(token, offset=None):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {'timeout': 100}
    if offset:
        params['offset'] = offset
    try:
        resp = requests.get(url, params=params, timeout=110)
        return resp.json()
    except Exception as e:
        log(f"Error getting updates: {e}")
        return None

def ask_user_experience(config):
    token = config['telegram_bot_token']
    chat_id = config['telegram_chat_id']
    
    # Send Question
    question = "🤖 <b>Setup:</b> Are you looking for <b>Fresher</b> or <b>Experienced</b> jobs?\n\nPlease reply with 'Fresher' or 'Experienced'."
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': question, 'parse_mode': 'HTML'}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        log(f"Error sending question: {e}")
        return 'fresher' # Default fallback
    
    # Poll for Answer
    log("Waiting for user input...")
    offset = None
    
    # Get initial offset
    initial_updates = get_updates(token)
    if initial_updates and initial_updates.get('ok'):
        result = initial_updates['result']
        if result:
            offset = result[-1]['update_id'] + 1
            
    while True:
        updates = get_updates(token, offset)
        if updates and updates.get('ok'):
            for update in updates['result']:
                offset = update['update_id'] + 1
                message = update.get('message')
                if message and str(message.get('chat', {}).get('id')) == str(chat_id):
                    text = message.get('text', '').lower().strip()
                    if 'fresher' in text:
                        return 'fresher'
                    elif 'experienced' in text or 'experience' in text:
                        return 'experienced'
                    else:
                        requests.post(url, json={'chat_id': chat_id, 'text': "Please reply with 'Fresher' or 'Experienced'."})
        time.sleep(1)

# --- MAIN ---
def main():
    try:
        log('Initializing Bot...')
        config = load_config()
        
        # Ask User Preference
        user_choice = ask_user_experience(config)
        
        if user_choice == 'fresher':
            config['keywords_include'] = ["fresher", "entry level", "junior", "0-1 year", "intern", "graduate", "trainee"]
            config['keywords_exclude'] = ["senior", "lead", "manager", "principal", "3+ years", "5+ years", "experienced"]
            job_type_label = "Fresher Job"
        else:
            config['keywords_include'] = ["senior", "lead", "manager", "principal", "3+ years", "5+ years", "experienced"]
            config['keywords_exclude'] = ["fresher", "entry level", "junior", "intern", "trainee"]
            job_type_label = "Experienced Job"
            
        msg = f"✅ Preference set to: <b>{user_choice.capitalize()}</b>. Starting scan..."
        token = config['telegram_bot_token']
        chat_id = config['telegram_chat_id']
        requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'})
        
        while True:
            try:
                log('Starting scan...')
                interval_mins = config.get('scan_interval_minutes', 30)
                seen_jobs = load_seen_jobs()
                
                total_new_jobs = 0

                # --- PHASE 1: INDIA ---
                log('Fetching India jobs...')
                india_jobs = fetch_google_jobs(config, region='India')
                total_new_jobs += process_and_send_jobs(india_jobs, seen_jobs, config, job_type_label)

                # --- PHASE 2: INTERNATIONAL ---
                log('Fetching International jobs...')
                intl_jobs = []
                intl_jobs.extend(fetch_remoteok(config))
                intl_jobs.extend(fetch_weworkremotely(config))
                intl_jobs.extend(fetch_google_jobs(config, region='USA'))
                
                total_new_jobs += process_and_send_jobs(intl_jobs, seen_jobs, config, job_type_label)
                        
                save_seen_jobs(seen_jobs)
                log(f'Scan complete. Found {total_new_jobs} new jobs in total.')
                
                # Send summary to Telegram
                if total_new_jobs > 0:
                    send_telegram_summary(total_new_jobs, interval_mins, config)
                else:
                    log("No new jobs found this cycle.")
                
                log(f'Sleeping for {interval_mins} minutes...')
                time.sleep(interval_mins * 60)

            except Exception as e:
                log(f'Error in scan loop: {e}')
                time.sleep(60)

    except KeyboardInterrupt:
        log('Bot stopped by user.')
    except Exception as e:
        log(f'Error in main: {e}')
        time.sleep(60)

if __name__ == '__main__':
    main()
