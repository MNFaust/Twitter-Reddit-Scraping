from urllib.request import Request, urlopen
import urllib.parse
from bs4 import BeautifulSoup
import sqlite3
import time
import datetime
import random
from colorama import init, Fore
init()


def SQLconnect():
    '''
    create table [listings] (
    [ID] INTEGER NOT NULL PRIMARY KEY,
    [CL_ID] NVARCHAR(100) NOT NULL,
    [DATE] DATE NOT NULL,
    [TITLE] NVARCHAR(600) NOT NULL,
    [COST] NVARCHAR(15) NOT NULL,
    [LINK] NVARCHAR(600) NOT NULL
    );
    '''
    global c, conn
    conn = sqlite3.connect('H:/Python/CL/lathe.db')
    c = conn.cursor()


def getCost(link):
    try:
        url = link
        page = urlopen(url)
        soup = BeautifulSoup(page, 'html.parser')
        data = soup.find("span", {"class": "price"})
        price = str(data.text)
        page.close()
    except Exception as e:
        price = "?"
    return price

def search(): 
    global new
    new = 0                                                                 # Indexing variable to check if new data was found
    
    url = 'https://minneapolis.craigslist.org/search/tla?query=lathe'       # URL of the MN CL Search Page
    page = urlopen(url)                                                     # Urllib must reopen the webpage during each new search
    soup = BeautifulSoup(page, 'html.parser')                               # Start the BS4 html parser
    data = soup.find_all("li", {"class": "result-row"})                     # Find all listings on the craigslist page
    
    for result in data:
        cl_id = result.find("a", {"class": "result-title hdrlnk"})          # Get the CL ID of the post
        cl_id = cl_id['data-id']
        cl_id = str(cl_id)
 
        posted_date = result.find("p", {"class": "result-info"})            # Parse original post date by first getting the result info
        dt = posted_date.find("time", {"class": "result-date"})             # Parse the result-date html header
        date = dt['datetime']                                               # Grab the integer date/time value from result-date
        date = str(date)[:-6]                                               # Type cast posted date to string and remove bad characters
        
        title = result.find("a", {"class": "result-title hdrlnk"})          # Parse the post title
        title = title.text                                                  # Obtain the text value (title) from the HTML string
        title = title.replace('"', "")

        link = result.find("a", {"class": "result-title hdrlnk"})           # Get the http:// linking to the post
        link = link['href']
        link = str(link)
        

        # Check to see if listing is in the DB already:
        try:
            c.execute('select cl_id from listings where cl_id = "' 
                      + cl_id +'"')
            rows = c.fetchone()
        except:
            rows = None
            
        if (rows == None):                                                  # If the rows = None then it's a new listing as sqlite3 did not find a record. 
            new += 1                                                        # Interate the new indexing variable 1 value
            cost = getCost(link)                                            # Get the cost of the item if it's new
            
            print(Fore.GREEN + "[+] New Listing Found, Adding to Database" 
                  + Fore.RESET) 
            print(Fore.GREEN + date + " " + title + " " + cost 
                  + Fore.RESET) 
            try:                                                            # Add the new post information the sqlite3 DB
                c.execute('INSERT INTO listings(CL_ID, DATE, TITLE, COST, LINK) VALUES' 
                          + '('"'%s'"','"'%s'"','"'%s'"','"'%s'"','"'%s'"');' 
                          % (cl_id, date, title, cost, link))
                conn.commit()
                print("[+] Log Entry Successfully Added")
            except:
                print("[!] Error - Log Entry Not Added") 
    page.close()                                                            # Close the urlib pageopen instance

    if ( new <= 0):
        print(Fore.RED + "[+] No new listings found" + Fore.RESET)          # If no new records were found, tell the user


if __name__ == "__main__":
    SQLconnect()
    scan_index = 0
    while True:                                                             # Continual while loop to search every 30min to 1 hour (random)
        date = datetime.datetime.now()                                      # Get the current date and time
        sleep_time = random.randint(1800,3600)                              # Get a random integer value between 1800 & 3600 (seconds) for sleep time
        print(Fore.LIGHTCYAN_EX + ("[+] Starting Scan %s at %s" 
                                   % (str(scan_index), str(date)))
              +Fore.RESET) 
        search()                                                            # Start the Craigslist search function
        print("[+] Sleeping for %s minutes" 
              % str(sleep_time/60) + Fore.RESET)
        time.sleep(sleep_time)                                              # Sleep the program 
        new = 0                                                             # Set the new indexing value back to zero
        scan_index += 1                                                     # Set the scan number indexing value +1
    conn.close()


