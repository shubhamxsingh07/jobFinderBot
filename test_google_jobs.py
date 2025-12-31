import requests

def test_google_rss():
    # Searching for pages from greenhouse.io (common ATS) with "India" and "Software Engineer"
    url = 'https://news.google.com/rss/search?q=site:greenhouse.io+software+engineer+india&hl=en-IN&gl=IN&ceid=IN:en'
    
    headers = {'User-Agent': 'Mozilla/5.0'}

    print(f"Testing: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Success! Content length: {len(resp.content)}")
            print(f"First 200 chars: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_google_rss()
