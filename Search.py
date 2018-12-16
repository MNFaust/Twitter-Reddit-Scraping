#==========================#
# by: @jfaust0             #
#==========================#

import praw
import sqlite3
import twitter
import random
import datetime, time
from twilio.rest import Client
from colorama import Fore, init
init()

# Subreddits to search
SUBREDDITS = ["netsec", "hacking", "oscp", "netsecstudents", "pentesting", "ITCareerQuestions", "security", "Infosec"]


# -------------------------------------------------------------------------------#
# Service Connection Functions:                                                  #
# -------------------------------------------------------------------------------#

def twilioCon():                                                        # Start a connection to our Twilio service API
    global client
    ACCOUNT_SID = ''
    AUTH_TOKEN = ''
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

def redditCon():                                                        # Start a connection to the Reddit API
    # Reddit Variables
    CLIENT_ID = ""
    SECRETKEY = ""
    USER = "-1"
    PASS = ""

    global reddit
    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=SECRETKEY,
                         user_agent='test',
                         username=USER,
                         password=PASS)

def sqlCon():                                                           # Connect to the Sqlite3 Database to store results
    '''CREATE TABLE vouchers (
id integer PRIMARY KEY,
source VARCHAR(50) NOT NULL,
post_id VARCHAR(30) NOT NULL,
post_date DATE NOT NULL,
author VARCHAR(50) NOT NULL,
url VARCHAR(500) NOT NULL,
sub_text VARCHAR(3000) NOT NULL
);'''
    # Sqlite3 Variables
    DATABASE = "reddit_vouchers.db"
    global conn, c
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

def twitterCon():
    global twit
    twit = twitter.Api(consumer_key='',
                      consumer_secret='',
                      access_token_key='',
                      access_token_secret='')


# -------------------------------------------------------------------------------#
# Searching Functions:                                                           #
# -------------------------------------------------------------------------------#

def redditSearch():                                                     # Search Reddit for voucher codes
    print(Fore.CYAN + "[+] Starting Reddit Search" + Fore.RESET)
    redditCon()                                                         # Connect to Reddit API

    for i in range(0, len(SUBREDDITS)):                                 # Loop throught SUBREDDITS array
        print(Fore.LIGHTWHITE_EX + "[+] Searching %s"
              % str(SUBREDDITS[i]) + Fore.RESET)

        for submission in reddit.subreddit(SUBREDDITS[i]).new(limit=100):
            keywords = ['voucher', 'coupon',
                        'promo', 'promotion', 'discount']               # Look for these keywords within the user submission
            source = "reddit"
            post_id = submission.id                                     # Get the submission ID for SQLite3 to store and reference
            date = submission.created                                   # Get date of submission
            date = str(datetime.datetime.fromtimestamp(date))[:-9]      # Change the integer date/time object to standard US
            author = submission.author                                  # Get the Authors username
            url = submission.url                                        # Get the submission URL
            sub_text = submission.selftext                              # Get the submission body (i.e., the post's text)
            title = submission.title                                    # Get the submissions title

            for j in range(0, len(keywords)):                           # Start a loop through the keywords array
                if keywords[j].strip() in sub_text:                     # if Keyword is in the post body:

                    # Check to see if ID is already in the database:
                    sql = "select * from vouchers where post_id = '%s'" % str(post_id)
                    c.execute(sql)
                    check = c.fetchone()

                    if (check == None):                                 # if Check is None, that means it's new content.

                        before_keyword, keyword, after_keyword = sub_text.partition(keywords[j])
                        clean_text = (keyword + after_keyword)          # Grab text starting at the Keyword only
                        print(Fore.GREEN + ("[+] Found A Voucher Code at %s"
                                            % str(url)) + Fore.RESET)

                        sql_data = (source, str(post_id), str(date), str(author),
                                str(url), str(clean_text))              # Data to be inserted into the Sqlite3 DB
                        sqlInsert(sql_data)


                        # Send a Text Message:
                        start = ("-" * 3 + "START" + "-" * 3 + "\n")
                        end = ("-" * 3 + "END" + "-" * 3)
                        message = ("%s Reddit Voucher Code: %s\n TITLE: %s\n URL: %s\n %s"
                                   % (start, str(clean_text)[:550], str(title), str(url), end))
                        sendText(message)
                        break                                           # If there's more than 1 keyword present, we
                                                                        # will takeup CPU cycles for nothing. Break after
                                                                        # the first instance.

                    else:                                               # if check != none, we have a duplicate record.
                        print(Fore.RED + "[!] Duplicate Record" + Fore.RESET)
                        break


def twitterSearch():
    twitterCon()
    print(Fore.CYAN + "[+] Starting Twitter Search" + Fore.RESET)
    keywords = ['voucher', 'coupon', 'free',
                'promo', 'promotion', 'discount']
    users = ['eLearnSecurity', 'offsectraining', 'CompTIA', 'ECCOUNCIL']

    for user in users:                                                  # Start a loop through twitter users
        print(Fore.LIGHTWHITE_EX + "[+] Searching %s"
              % str(user) + Fore.RESET)
        timeline = twit.GetUserTimeline(screen_name=user, count=20)     # Get the users last 15 tweets
        tweets = [i.AsDict() for i in timeline]                         # Create a dictionary object
        for tweet in tweets:
            source = "twitter"
            id = tweet['id']                                            # Get the Tweet ID for SQL Reference
            date = tweet['created_at']                                  # Get timestamp
            time_struct = time.strptime(date, "%a %b %d %H:%M:%S +0000 %Y")
            date = datetime.datetime.fromtimestamp(time.mktime(time_struct))
            date = str(date)[:-9]

            t_data = tweet['text']                                      # Get actual tweet data
            userdata = tweet['user']                                    # User data is a sub-dict object

            url = ('https://twitter.com/statuses/%s' % id)              # Get URL of the tweet
            username = userdata.get('screen_name')

            for keyword in keywords:
                if keyword in t_data:
                    sql = "select * from vouchers where post_id = '%s'" % str(id)
                    c.execute(sql)
                    check = c.fetchone()

                    if (check == None):
                        message = ("[+] Found a Mathcing Tweet\n"
                                           "FROM: %s\n"
                                           "URL: %s\n"
                                           "TWEET: %s"
                              %(str(username), str(url), str(t_data)))
                        print(Fore.GREEN + message + Fore.RESET)
                        sql_data = (source, str(id), str(date), str(username),
                                    str(url), str(t_data))  # Data to be inserted into the Sqlite3 DB
                        sqlInsert(sql_data)

                        start = ("-" * 3 + "START" + "-" * 3 + "\n")
                        end = ("-" * 3 + "END" + "-" * 3)
                        sendText(start+"\n"+message+"\n"+end)

                    else:                                               # if check != none, we have a duplicate record.
                        print(Fore.RED + "[!] Duplicate Record" + Fore.RESET)
                        break



# -------------------------------------------------------------------------------#
# Special purpose Functions:                                                     #
# -------------------------------------------------------------------------------#

def sendText(message):
    client.messages.create(body=message,
                           from_='+NUMBER',
                           to='+NUMBER')
    time.sleep(5)  # Sleep for 5 seconds after message send.

def sqlInsert(data):
    sql = '''INSERT INTO vouchers(source, post_id, post_date, author, url, sub_text) VALUES (?,?,?,?,?,?)'''
    c.execute(sql, data)
    conn.commit()                                                       # commit the sql insert command

def dict2list(dict_input):
    dictlist = []
    for key,vlaue in dict_input.items():
        temp = [key,vlaue]
        dictlist.append(temp)
    return dictlist


# -------------------------------------------------------------------------------#
# MAIN:                                                                          #
# -------------------------------------------------------------------------------#
if __name__ == "__main__":
    sqlCon()
    twilioCon()
    while True:
        redditSearch()
        twitterSearch()
        print(Fore.CYAN + "[+] Sleeping for 30 Minutes" + Fore.RESET)
        sleep_time = random.randint(900,1800)
        time.sleep(sleep_time)

