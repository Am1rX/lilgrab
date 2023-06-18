import requests
import time
from bs4 import BeautifulSoup

def Default(a):
    req = requests.get(a)
    soup = BeautifulSoup(req.content,'html.parser')
    links = soup.find_all()
    for link in links:
        b = link.get('href')
        if b != None :
            print("├ "+b)
        elif b == '#':
            pass

def full(a):
    print("\n├───────────────────────────── Scan started ─────────────────────────────┤ \n ")
    crwl = []
    js = []
    backup = []
    req = requests.get(a)
    soup = BeautifulSoup(req.content,'html.parser')
    links = soup.find_all()
    for link in links:
        b = link.get('href')
        try:
            if b != None :
                if 'ttps' and 'ttp' in b:
                    pass
                elif '#' in b:
                    pass
                else:
                    if b[0] != '/':
                        b = ('/'+b)
                        test = (a+b)
                        testreq = requests.get(test)
                        stut = testreq.status_code
                        if stut == 200:
                            if test != a:
                                print('├ '+test)
                                crwl.append(str(test))
                    else: 
                        test = (a+b[1:])
                        testreq = requests.get(test)
                        stut = testreq.status_code
                        if stut == 200:
                            if test != a:
                                print('├ '+test)
                                crwl.append(str(test))
        except:
            pass
    js = crwl
    print("\n├───────────────────────────── check started ─────────────────────────────┤ \n ")
    backup = crwl
    for lvl2 in crwl:
        if lvl2[-1] == '/':
            try:
                testreq = requests.get(lvl2)
                stut = testreq.status_code
                if stut == 200:
                    soup = BeautifulSoup(req.content,'html.parser')
                    links = soup.find_all()
                for link in links:
                    b = link.get('href')
                    if b not in backup: 
                        print('lvl 2 ├ '+b)
                else:
                    pass
            except:
                pass
        else: 
            try:
                lvl2 = (lvl2+"/")
                testreq = requests.get(lvl2)
                stut = testreq.status_code
                if stut == 200:
                    soup = BeautifulSoup(req.content,'html.parser')
                    links = soup.find_all()
                    for link in links:
                        b = link.get('href')
                        if b not in backup: 
                            print('lvl 2 ├ '+b)
                else: 
                    pass
            except:
                pass
    print("\n├───────────────────────────── check has ended ─────────────────────────────┤ \n ")
    print("\n├───────────────────────────── code checker started ─────────────────────────────┤ \n ")
    codes = ['css','js','json']
    codenocheck = []
    for test in js:
        check = test.split(".")
        if check[-1] in codes:
            print("lvl 3 ├ "+test)
            codenocheck.append(str(test))
        else:
            pass
    print("\n├───────────────────────────── code checker has ended ─────────────────────────────┤ \n ")
    print("\n├───────────────────────────── input finder started ─────────────────────────────┤ \n ")
    login = '<input'
    for checkb in backup:
        if checkb not in codenocheck:
            req = requests.get(checkb)
            if login in req.text:
                print("input found ├ "+checkb)
        else:
            pass
    print("\n├───────────────────────────── input finder ended ─────────────────────────────┤ \n ")
    try:
        if backup[0] == '':
            print("use number 1")
    except IndexError:
        print("use number 1")

print('''
[Welcome to AMIRX Link Grabber ! ]
         _____        [1] Default (links from main page {like site.com/} )
        /     \\    0  [2] full scan (links from all pages i w'll found} )
       / @   @ \\ 0    [3] exit
      /\   w   /\\                          ( put link then use numbers ! )
     /   || ||   \\
    /    || ||    \\
         \/ \/
''')
while True:
    urltest = "on"

    while urltest == 'on':
        try:
            url = input("url >>> ")
            if '://' not in url:
                print("please enter an url !")
            else:
                urltest = 'off'
        except:
            print("!")

    time.sleep(0.4)
    print("\nTarget Set => ",url)

    option = input("\n[AMIRX] Select an option >> ")

    if option == '1':
        try:
            print('\n')
            Default(url)
        except:
            print("Connection Error")
    elif option == '2':
            print('\n')
            full(url)
    elif option == '3':
        exit()
    else:
        option = input("\n[AMIRX] Select an option >> ")

#Created by AMIRX
