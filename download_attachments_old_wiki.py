# REMEMBER TO ADD CHECKER FOR FILE SIZE!!

"""
ADD CHECKER FOR FILE SIZE!!!
"""
from pathlib import Path
from atlassian import Confluence
from bs4 import BeautifulSoup
import pandas as pd
import argparse
import requests


def read_token():
    token_path = Path(__file__).parents[0] / "token.txt"

    if not token_path.exists():
        raise FileNotFoundError("Make sure token.txt exists and fill in your Labbook bearer token")
    
    with open(Path(__file__).parents[0] / "token.txt", "r") as f:
        token = f.read()
    
    return token
        

def get_page_body(confluence, page_id):
    page_content = confluence.get_page_by_id(page_id, expand='space,body.storage,version')

    return page_content['body']['storage']['value'], page_content["title"]

def parse_as_html(page_body):
    return BeautifulSoup(page_body, 'html.parser')

def check_for_media(title):

    types = ["File:", "Media:"]

    for t in types:
        if t in title:
            return t

    return False

def check_attachments(soup):

    for a in soup.findAll('a'): # find all "a" tags (links)
        try:
            url = a['href']
        except:
            continue

        if url.find("http://wiki.pet.auh.dk/wiki/") != -1: # if the specified url exists (-1 = not found)
            base_url = "http://wiki.pet.auh.dk/wiki/"
        elif url.find("http://10.3.148.104/wiki/")!= -1:
            base_url = "http://10.3.148.104/wiki/"
        elif url.find("http://10.3.148.104/mediawiki/")!= -1:
            base_url = "http://10.3.148.104/mediawiki/"
        else: 
            continue # move on to next link if none of the links exists
        title = url[len(base_url):]
        media = check_for_media(title)

        if base_url == "http://10.3.148.104/mediawiki/" or media:
            if "redlink" in url:
                continue
            
            if media:
                filename = title[len(media):]
            else: 
                filename = url.split("/")[-1]
            
            file_path = Path(__file__).parent / "attachments" / filename
            
            if not file_path.exists():
                if media:
                    try:
                        r = requests.get(url, allow_redirects=True)
                        soup = BeautifulSoup(r.content, 'html.parser')
                        div = soup.find("div", {"class": "fullImageLink"})
                        a_tag = div.find('a')
                        # Get the 'href' attribute
                        href = a_tag['href']
                        r = requests.get("http://10.3.148.104/" + href, allow_redirects=True)
                    except:
                        print(f"failed to download file: {filename}")
                    
                else:
                    r = requests.get(url, allow_redirects=True)

                MAX_SIZE = 42 * 1000000 # testing with smaller files for now (42 normally)
                try:
                    if int(r.headers.get("Content-length")) < MAX_SIZE:
                        with open(file_path, "wb") as f:
                            f.write(r.content)
                    else:
                        print(f"Not downloading {filename} - exceeding limit of Labbook attachments")
                except:
                    print(f"failed to download file: {filename}")
                    

                

def check_single_page_for_attachments(confluence, page_id:str):

    page_body, _ = get_page_body(confluence, page_id)
    soup = parse_as_html(page_body)
    
    check_attachments(soup)


def check_all_pages_for_attachments(confluence, loopover = range(0, 500, 100), limit = 100,  spacekey = "CW"):
    # limit at 100 # limit will only return what is needed and not error if and excess is called
    
    for i in loopover: # looping over pages from space

        pages = confluence.get_all_pages_from_space(spacekey, start=i, limit=limit, status=None, expand=None, content_type='page')
        
        # loop through and get each page
        for pg in pages:
            check_single_page_for_attachments(confluence, page_id=pg['id'])


if __name__ in "__main__":

    # create attachment folder if it does not exists
    output_path = Path(__file__).parent / "attachments" 
    if not output_path.exists():
        output_path.mkdir(parents=True)
  
    token = read_token()
    
    confluence = Confluence(
        url='https://labbook.au.dk/',
        token=token
        )

    check_all_pages_for_attachments(confluence)




                   