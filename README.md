# LabbookUpdater
Confluence Labbook rest api code for updating wiki


## 👩‍💻 Usage

1. Create a personal Labbook access token and put it in a file named `token.txt` (see repository structure). Make sure you **do not** share your token! 
2. Install required python packages
```
pip install -r requirements.txt
```
3. something
```
something
```
*Note:* If you want to update user links while running, make sure to create a csv file named `user_mapping.csv` which contains old wiki users in the first column and auIDs for labbook in the second column. 


optional:


## 🗂️ Repository structure
```
├── README.md
├── token.txt                 <- add your personal labbook access token
├── user_mapping.csv          <- mapping between old wiki users (first column) and auIDs for labbook (second column)
├── .gitignore
├── requirements.txt
└── update_labbook_links_lp.py
```