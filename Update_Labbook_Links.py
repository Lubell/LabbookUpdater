from bs4 import BeautifulSoup
from atlassian import Confluence

# first define some things
# spacekey CFIN Wiki = CW
spaceKey = "CW"
# my token
bearer_token = "XXX"
# confuelence instance
confluence = Confluence(
    url='https://labbook.au.dk/',
    token=bearer_token
)
# This is just one page
page_key = "274708006" # Analyzing functional MRI data
# if we want all the pages we can ask for that using pagenation
# to then unpack more we loop.  limit is 100 a pop
# limit will only return what is needed and not error if and excess is called
for i in range(0,400,100):

    pgs = confluence.get_all_pages_from_space(spaceKey, start=i, limit=100, status=None, expand=None, content_type='page')
    # loop through and get each page
    for i in range(len(pgs)):
        print(pgs[i]['id'])
        content2 = confluence.get_page_by_id(page_id=pgs[i]['id'], expand='space,body.storage,version')







pageBody = content2['body']['storage']['value']
soup = BeautifulSoup(pageBody, 'html.parser')
newText = []
places = []
for a in soup.findAll('a'):
    # confirm that it is a wiki link
    wikiURL = a['href'].find('wiki.pet.auh.dk')
    ipURL = a['href'].find('10.3.148.104')
    if wikiURL != -1:
        baseURL = "http://wiki.pet.auh.dk/wiki/"
    elif ipURL != -1:
        baseURL = "http://10.3.148.104/wiki/"
    else:
        continue
    # first we remove the wiki part
    oldURL = a['href']
    oldTitle = oldURL[len(baseURL):]
    if "Category:" in oldTitle:
        #this is a label now
        label = oldTitle[len("Category:"):]
        confluence.set_page_label(page_key, label)

    # replace the underscores
    newTitle = oldTitle.replace("_"," ")
    # check exist
    #content1 = confluence.get_page_by_title(space=spaceKey, title=newTitle)
    content1 = confluence.page_exists(space=spaceKey, title=newTitle, type=None)

    if content1 == False:
        continue

    tmpNewText = "<ac:link><ri:page ri:space-key=\"CW\" ri:content-title=3*ER" + newTitle + "3*ER /><ac:plain-text-link-body><![CDATA[" + a.text + "]]></ac:plain-text-link-body></ac:link>"

    newText.append(tmpNewText.replace("3*ER",'"'))
    print(tmpNewText.replace("3*ER",'"'))
    places.append(a.sourcepos)

properTags = 0
newBody = pageBody[0:places[properTags]]
while properTags != len(newText):
    postcursor = pageBody.find('</a>',places[properTags])+len('</a>')
    print(pageBody[places[properTags]:postcursor])
    if properTags == len(newText)-1:
        newBody = newBody + newText[properTags] + pageBody[postcursor+1:]
    else:
        newBody = newBody + newText[properTags] + pageBody[postcursor:places[properTags+1]]
    properTags += 1



zoot = newBody.replace('/li>','</li>')
zoot = zoot.replace('<</li>','</li>')

status = confluence.update_page(
    parent_id=None,
    page_id=page_key,
    title=content2['title'],
    body=zoot
)

# content2 = confluence.get_page_by_id(page_id=pageId, expand='space,body.view,version')

# # print(content2['body']['view']['value'])

# newText="[This is an internal Link|CW:CFIN-a-thon]"

# newText = "<ac:link><ri:page ri:space-key=\"CW\" ri:content-title=\"CFIN-a-thon\" /><ac:link-body>This is an internal link to another space</ac:link-body></ac:link>"
# soupier = BeautifulSoup(newText, 'html.parser')
# for a in soupier.findAll('ac:link'):
#     print(a)

# # newText = "<p><br/></p><p><br/></p><p><a href='/display/CW/CFIN-a-thon'>This is an internal link</a></p><p><br/></p><p><a class='\"internal-link\"' href='/display/CW/CFIN-a-thon\' rel='\"nofollow\"'>This is an external link</a></p>"
# status = confluence.update_page(
#     parent_id=None,
#     page_id=pageId,
#     title=pageTitle,
#     body=newText
# )
# #print(result)
# #print(status)