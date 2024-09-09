"""
This script can be run to return all pages to the previous version after running update_labbook_links.py
"""
from pathlib import Path
import pandas as pd
from update_labbook_links import read_token, get_page_body, update_page
from atlassian import Confluence


if __name__ in "__main__":
    df = pd.read_csv(Path(__file__).parent / "versions.csv")
    df = df[:3]


    token = read_token()

    confluence = Confluence(
        url='https://labbook.au.dk/',
        token=token
        )

    for index, row in df.iterrows():
        page_id, previous_version = row["page_id"], row["v_pre_update"]
        body, title  = get_page_body(confluence, page_id, version = previous_version)

        update_page(body, title, page_id, confluence)
        
