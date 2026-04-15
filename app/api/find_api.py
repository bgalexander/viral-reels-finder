import requests
import json

key = "1fbdbc3795msh0eac6fabad71ee3p170a89jsnf8f2e835d6b9"

apis = [
    {
        "name": "instagram-scraper-api2",
        "host": "instagram-scraper-api2.p.rapidapi.com",
        "url": "https://instagram-scraper-api2.p.rapidapi.com/v1/hashtag",
        "params": {"hashtag": "fitness"}
    },
    {
        "name": "instagram-scraper-2022",
        "host": "instagram-scraper-2022.p.rapidapi.com",
        "url": "https://instagram-scraper-2022.p.rapidapi.com/ig/hashtag/",
        "params": {"hashtag": "fitness"}
    },
    {
        "name": "instagram28",
        "host": "instagram28.p.rapidapi.com",
        "url": "https://instagram28.p.rapidapi.com/tag_feed",
        "params": {"tag": "fitness"}
    },
    {
        "name": "instagram-bulk-scraper",
        "host": "instagram-bulk-profile-scrapper.p.rapidapi.com",
        "url": "https://instagram-bulk-profile-scrapper.p.rapidapi.com/clients/api/ig/hashtag",
        "params": {"hashtag": "fitness", "feed_type": "recent"}
    },
    {
        "name": "real-time-instagram",
        "host": "real-time-instagram-scraper-api.p.rapidapi.com",
        "url": "https://real-time-instagram-scraper-api.p.rapidapi.com/v1/hashtag_posts",
        "params": {"hashtag": "fitness"}
    },
]

for api in apis:
    headers = {
        "x-rapidapi-host": api["host"],
        "x-rapidapi-key": key
    }
    try:
        r = requests.get(api["url"], headers=headers, params=api["params"], timeout=15)
        print(f'{api["name"]}: {r.status_code}')
        print(f'  {r.text[:300]}')
    except Exception as e:
        print(f'{api["name"]}: ERROR - {e}')
    print("===")