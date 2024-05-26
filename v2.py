import requests
from requests.exceptions import MissingSchema, ConnectionError
import urllib.parse
from collections import deque
import re
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

# Pre-compile email regex
email_regex = re.compile(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", re.I)

def process_url(url, base_url, path, scraped_urls, emails, session):
    try:
        response = session.get(url)
    except (MissingSchema, ConnectionError):
        return

    new_emails = set(email_regex.findall(response.text))
    emails.update(new_emails)

    soup = BeautifulSoup(response.text, features="lxml")
    new_urls = set()

    for anchor in soup.find_all("a"):
        link = anchor.get('href', '')
        if link.startswith('/'):
            link = base_url + link
        elif not link.startswith('http'):
            link = path + link
        if link not in scraped_urls:
            new_urls.add(link)

    return new_urls

def main():
    user_url = input('[+] Enter Target URL To Scan: ')
    urls = deque([user_url])
    scraped_urls = set()
    emails = set()

    count = 0
    max_urls = 100

    with requests.Session() as session, ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        while urls and count < max_urls:
            url = urls.popleft()
            if url in scraped_urls:
                continue

            count += 1
            print(f'[{count}] Processing {url}')
            scraped_urls.add(url)

            parts = urllib.parse.urlsplit(url)
            base_url = '{0.scheme}://{0.netloc}'.format(parts)
            path = url[:url.rfind('/')+1] if '/' in parts.path else url

            future = executor.submit(process_url, url, base_url, path, scraped_urls, emails, session)
            futures.append(future)

        for future in futures:
            result = future.result()
            if result:
                urls.extend(result)

    for mail in emails:
        print(mail)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('[-] Closing!')
