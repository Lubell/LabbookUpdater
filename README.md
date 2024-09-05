# LabbookUpdater
Confluence Labbook rest api code for updating wiki


## 👩‍💻 Usage

1. Create a personal Labbook access token and put it in a file named `token.txt` (see repository structure). Make sure you **do not** share your token! 
2. Install required python packages
```
pip install -r requirements.txt
```
3. Download attachments from old wiki (except for files larger than 40 mb as they exceed the file size limit for Labbook)
```
python download_attachments_old_wiki.py
```

4. Update labbook page(s)

If you want to update a specific page, run the script and parse the page id
```
python update_labbook_links_lp.py --page 123451234
```

If you want to loop over all pages (NOT IMPLEMENTED YET)
```
python update_labbook_links_lp.py --page all
```

*Note:* If you want to update user links while running, make sure to create a csv file named `user_mapping.csv` which contains old wiki users in the first column and auIDs for labbook in the second column. 


## 🗂️ Repository structure
```
├── README.md
├── token.txt                 <- add your personal labbook access token
├── user_mapping.csv          <- mapping between old wiki users (first column) and auIDs for labbook (second column)
├── .gitignore
├── requirements.txt
└── update_labbook_links_lp.py
```


## Notes
* Instead of linking to a page with user information, we link to the labbook profile of the user
* Previous category pages are turned into labels -> the in-text references to the categories are still kept, but the link goes to a page showing all pages with that label
    * Some categories contain spaces, which is not allowed for labels (they will be split into two e.g., "project" "initiation"). Therefore, we update the label to be "project_initiation"
