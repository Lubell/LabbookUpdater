"""
This script holds the code for updating links in the CFIN/MIB wiki-pages when moving to Labbook.

- Make sure to run the download_attachments_old_wiki.py if you want to update attachments
- Create user_mapping.csv with usernames from the old wiki in the first column and AU-IDs in the second column

"""
from pathlib import Path
from atlassian import Confluence
from bs4 import BeautifulSoup
import pandas as pd
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type = str, default="282463220")

    return parser.parse_args()


def read_token():
    token_path = Path(__file__).parents[0] / "token.txt"

    if not token_path.exists():
        raise FileNotFoundError("Make sure token.txt exists and fill in your Labbook bearer token")
    
    with open(Path(__file__).parents[0] / "token.txt", "r") as f:
        token = f.read()
    
    return token
        

def get_page_body(confluence, page_id, version = None):
    page_content = confluence.get_page_by_id(page_id, expand='space,body.storage,version', version = version)

    return page_content['body']['storage']['value'], page_content["title"]

def parse_as_html(page_body):
    return BeautifulSoup(page_body, 'html.parser')

def log_missing_pages(title):
    logging_path = Path(__file__).parent / "missing_pages.txt"

    if not logging_path.exists():
        with open(logging_path , "x") as f:
            f.write(title)

    else:
        with open(logging_path , "a") as f:
            f.write("\n" + title)

def update_page_title(title):
    """
    updates the page title, both for pages that do exist, and redlinks from old wiki   
    """
    if "redlink" in title:  # redlinks, get everything between title= and &
        title = title.split("title=")[-1]
        title = title.split("&")[0]

    return title.replace("_"," ")


def format_attachment_links(filename):
    template = None
    fn_lower = filename.lower()
    if fn_lower.endswith(".png") or fn_lower.endswith(".jpg"):
        template = (
            '<p><ac:image ac:thumbnail="true" ac:height="250"><ri:attachment ri:filename="{filename}" /></ac:image></p>'
        )

    elif fn_lower.endswith(".pdf"):
        template = (
            '<p><span class="mw-headline"><ac:link><ri:attachment ri:filename="{filename}" /></ac:link></span></p>'
        )
    elif fn_lower.endswith(".docx") or fn_lower.endswith(".zip") or fn_lower.endswith(".dmg") or fn_lower.endswith(".doc") or fn_lower.endswith(".xlsx") or fn_lower.endswith(".pptx"):
        template = (
            '<p><ac:link><ri:attachment ri:filename="{filename}" /></ac:link></p>'
        )

    if template:
        return template.format(filename = filename)
    else:
        print(f"file ending {filename.split('.')[-1]} not supported")
        return None



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


def update_page(body:str, title:str, page_id:str, confluence:Confluence, labels:list = []):

    if len(labels) > 0:
        confluence = add_page_labels(labels, confluence, page_id)
    
    status = confluence.update_page(
        parent_id=None,
        page_id=page_id,
        title=title,
        body=body
    )


    print(f"status page update {status}.")


def update_links_to_old_wiki(soup, page_body, page_id):
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
        
        new_title = update_page_title(title)

        # ATTACHMENTS
        if "File:" in title or "Media:" in title or "mediawiki" in url:
            if "File:" in title:
                filename = title[len("File:"):]
            elif "Media:" in title:
                filename = title[len("Media:"):]
            else:
                filename = url.split("/")[-1]

            file_path = Path(__file__).parent / "attachments" / filename
            # see if file exists in attachment folder
            if not file_path.exists():
                print(f"cannot find file {file_path}")
                continue

            confluence.attach_file(file_path, page_id = page_id)
            new_text_tmp = format_attachment_links(filename)

            if new_text_tmp == None:
                continue

        # CATEGORIES -> now labels
        elif "Category:" in new_title:
            label = new_title[len("Category:"):]

            # labels cannot contain spaces, therefore replace spaces with _
            label = label.replace(" ", "_")

            labels.append(label)

            new_text_tmp = f'<p><a href="https://labbook.au.dk/label/CW/{label}">{label}</a></p>'
        
        elif "Special:Categories" in new_title: 
            new_text_tmp = '<a href="https://labbook.au.dk/labels/listlabels-alphaview.action?key=CW">Categories</a>'
        

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
                new_text_tmp = f"https://labbook.au.dk/display/~{labbook_user}" # linking to peoples profiles    
            else:
                continue
        
        # ANCHOR LINKS
        elif "#" in new_title:
            main_page, anchor = new_title.split("#")
            new_text_tmp = format_internal_anchor_links(page_title=main_page, anchor=anchor, text=a.text)
            
            # check if page exists
            if not confluence.page_exists(space="CW", title=new_title, type=None):
                log_missing_pages(new_title)

        # THE REST
        else:
            new_text_tmp = format_internal_links(page_title=new_title, text=a.text)
            
            # check if page exists
            if not confluence.page_exists(space="CW", title=new_title, type=None):
                log_missing_pages(new_title)

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


def single_page_update(confluence, page_id:str):

    page_body, page_title = get_page_body(confluence, page_id)
    soup = parse_as_html(page_body)
    

    new_page_body, labels = update_links_to_old_wiki(soup, page_body, page_id)
    if new_page_body == None:# if no links needing updates were found
        
        return False
    else:
        new_page_body = new_page_body.replace('/li>','</li>')
        new_page_body = new_page_body.replace('<</li>','</li>')
        new_page_body = new_page_body.replace('/p>','</p>')
        new_page_body = new_page_body.replace('<</p>','</p>')

        update_page(body=new_page_body, title=page_title, page_id=page_id, confluence=confluence, labels = labels)
        return True


def all_pages_update(confluence, spacekey = "CW", version_control = True):
    if version_control:
        df = pd.DataFrame()

    for i in range(0, 500, 100): # looping over pages from space
       
        # limit at 100 # limit will only return what is needed and not error if and excess is called
        pages = confluence.get_all_pages_from_space(spacekey, start=i, limit=100, status=None, expand="version", content_type='page')
        
        # loop through and get each page
        for pg in pages:
            page_id = pg['id']

            if version_control:
                version_before_update = pg["version"]["number"]
                print(version_before_update)
            
            update = single_page_update(confluence, page_id=page_id)

            if not update:
                print(f"No links needing update found - labbook page {page_id} not updated")
                continue

            if version_control:
                new_dat = pd.DataFrame.from_dict({"page_id": [page_id], "v_pre_update": [version_before_update], "v_after_update": [version_before_update+1]})
                df = pd.concat([df, new_dat])

    if version_control:
        df.to_csv(Path(__file__).parent / "versions.csv", index=False)



if __name__ in "__main__":
    args = parse_args()
  
    token = read_token()
    
    confluence = Confluence(
        url='https://labbook.au.dk/',
        token=token
        )
    
    if args.page == "all":
        all_pages_update(confluence)

    else:
        single_page_update(confluence, page_id = args.page)