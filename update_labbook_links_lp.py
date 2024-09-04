"""
This script holds the code for updating links in the CFIN/MIB wiki-pages when moving to Labbook.

TODO:
- [ ] make sure missing pages are logged
- [ ] add status checker when updating page
- [x] seems like labels can only be one word - e.g. no spaces? deal with this. CURRENT SOLUTION = replace spaces with underscores
- [x] update anchor links
- [x] figure out what to do with special pages (e.g. old categories that turned into labels now)
- [x] update links to users (mapping between users on the old wiki and the new wiki are to made)
    - [ ] Question: do we want to link to labbook account page or rather a CFIN/MIB page where the user is described?
- [ ] templates?
- [ ] attachments
- [ ] loop over pages instead of providing page_id
- [ ] document code
    - [ ] doc strings
    - [ ] usage guide in README
"""
from pathlib import Path
from atlassian import Confluence
from bs4 import BeautifulSoup
import pandas as pd
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type = str, default="282463945")

    return parser.parse_args()


def read_token():
    token_path = Path(__file__).parents[0] / "token.txt"

    if not token_path.exists():
        raise FileNotFoundError("Make sure token.txt and fill in your Labbook bearer token")
    
    with open(Path(__file__).parents[0] / "token.txt", "r") as f:
        token = f.read()
    
    return token
        

def get_page_body(confluence, page_id):
    page_content = confluence.get_page_by_id(page_id, expand='space,body.storage,version')

    return page_content['body']['storage']['value'], page_content["title"]

def parse_as_html(page_body):
    return BeautifulSoup(page_body, 'html.parser')

def log_missing_pages():
    pass

def check_status():
    # 200 is good
    pass

def update_page_title(title):
    """
    updates the page title, both for pages that do exist, and redlinks from old wiki   
    """
    if "redlink" in title:  # redlinks, get everything between title= and &
        title = title.split("title=")[-1]
        title = title.split("&")[0]

    return title.replace("_"," ")


def update_links_to_old_wiki(soup, page_body):
    """
    parameters
    ----------
    soup: 

    page_body:

    """

    indices = []
    new_text = []
    labels = []

    for a in soup.findAll('a'): # find all "a" tags (links)

        url = a['href']

        if url.find("http://wiki.pet.auh.dk/wiki/") != -1: # if the specified url exists (-1 = not found)
            base_url = "http://wiki.pet.auh.dk/wiki/"
        elif url.find("http://10.3.148.104/wiki/")!= -1:
            base_url = "http://10.3.148.104/wiki/"
        else: 
            continue # move on to next link if none of the links exists
        title = url[len(base_url):]
        
        new_title = update_page_title(title)


        # CATEGORIES -> now labels
        if "Category:" in new_title:
            label = new_title[len("Category:"):]

            # labels cannot contain spaces, therefore replace spaces with _
            label = label.replace(" ", "_")

            labels.append(label)

            new_text_tmp = f'<p><a href="https://labbook.au.dk/label/CW/{label}">{label}</a></p>'
        
        elif "Special:Categories" in new_title: 
            new_text_tmp = '<p><a href="https://labbook.au.dk/labels/listlabels-alphaview.action?key=CW">Categories</a></p>'
        

        # USER PAGES
        elif "User:" in new_title: 
            user = new_title.split("User:")[-1]
            try: 
                user_mapping = pd.read_csv(Path(__file__).parent / "user_mapping.csv", names = ["wiki_user", "labbook_user"])
            except(FileNotFoundError):
                print("No user-mapping file found, ignoring user link.")
                continue
            
            labbook_user = user_mapping.loc[user_mapping["wiki_user"] == user]["labbook_user"]
            
            if len(labbook_user) != 0:
                new_text_tmp = f"https://labbook.au.dk/display/~{labbook_user}" #if we want to link to peoples own profiles. Or would we rather link to a page about each person in the wiki?      
            else:
                continue
        
        # ANCHOR LINKS
        elif "#" in new_title:
            main_page, anchor = new_title.split("#")
            new_text_tmp = format_internal_anchor_links(page_title=main_page, anchor=anchor, text=a.text)

        # THE REST
        else:
            new_text_tmp = format_internal_links(page_title=new_title, text=a.text)

        indices.append(a.sourcepos)
        new_text.append(new_text_tmp)

    if len(indices) == 0: # if no links are to be updated, return None instead of new page body and labels
        return None, None

    counter = 0
    new_body = page_body[:indices[counter]]

    while counter < len(new_text):
        # find the position just after the closing `</a>` tag
        postcursor = page_body.find('</a>', indices[counter]) + len('</a>')
        
        # determine the appropriate slice to append
        if counter == len(new_text) - 1:
            # if this is the last tag, append the remaining page body after postcursor
            new_body += new_text[counter] + page_body[postcursor + 1:]
        else:
            # otherwise, append up to the next tag location
            new_body += new_text[counter] + page_body[postcursor:indices[counter + 1]]
        
        # increment the counter
        counter += 1

    return new_body, labels



def format_internal_anchor_links(page_title, anchor, text):
    link_template = (
        '<ac:link ac:anchor="{anchor}"><ri:page ri:space-key="CW" ri:content-title="{title}" />'
        '<ac:plain-text-link-body><![CDATA[{text}]]></ac:plain-text-link-body></ac:link>'
        )
    return link_template.format(anchor = anchor, title=page_title, text=text)

def format_internal_links(page_title, text):
    link_template = (
                '<ac:link><ri:page ri:space-key="CW" ri:content-title="{title}" />'
                '<ac:plain-text-link-body><![CDATA[{text}]]></ac:plain-text-link-body></ac:link>'
            )
    return link_template.format(title=page_title, text=text)


def add_page_labels(labels, confluence, page_id):
    for label in labels:
        confluence.set_page_label(page_id, label)
    
    return confluence


def update_page(body:str, title:str, page_id:str, confluence:Confluence, labels:list):

    if len(labels) > 0:
        confluence = add_page_labels(labels, confluence, page_id)
    
    status = confluence.update_page(
        parent_id=None,
        page_id=page_id,
        title=title,
        body=body
    )


    print(f"status page update {status}.")


def single_page_update(page_id:str):
    
    token = read_token()
    
    confluence = Confluence(
        url='https://labbook.au.dk/',
        token=token
        )
    
    page_body, page_title = get_page_body(confluence, page_id)
    soup = parse_as_html(page_body)
    

    new_page_body, labels = update_links_to_old_wiki(soup, page_body)
    if new_page_body == None:# if no links needing updates were found
        print(f"No links needing update found - labbook page {page_id} not updated")
    else:
        new_page_body = new_page_body.replace('/li>','</li>')
        new_page_body = new_page_body.replace('<</li>','</li>')

        #update_page(body=new_page_body, title=page_title, page_id=page_id, confluence=confluence, labels = labels)


def all_pages_update():
    pass

if __name__ in "__main__":
    args = parse_args()
    print(args)
    

    if args.page == "all":
        pass
        # MAKE SURE EVERYTHING IS TESTED THROUGHLY BEFORE RUNNING LINE BELOW!
        # all_pages_update()

    else:
        single_page_update(page_id = args.page)