from __future__ import print_function
import praw
import re
import urllib.request
import json
from praw.models import MoreComments

import sys
test = False
if len(sys.argv) > 1 and sys.argv[1] == "test":
    test=True
    print("TEST MODE")

class FoundOne(BaseException):
    pass


def read_url(url):
    with urllib.request.urlopen(url) as r:
        data = r.read()
    return data.decode('utf-8')


def save_list(seen, _id):
    print(seen)
    with open("/home/pi/OEISbot/seen/"+_id, "w") as f:
        return json.dump(seen, f)

def open_list(_id):
    try:
        with open("/home/pi/OEISbot/seen/" + _id) as f:
            return json.load(f)
    except:
        return []

def escape(text):
    text = "\\^".join(text.split("^"))
    text = "\\*".join(text.split("*"))
    return text

def deduplicate(target_list):
    unique_values = []
    [unique_values.append(x) for x in target_list if x not in unique_values]
    return unique_values

def a_numbers_in_text(body):
    valid_prefix            = "(?:[\s\/'\"\-\+\*]|^)"
    optional_opening_parens = "[\[\(\{]*"
    a_number                = "A(\d{6})"
    valid_suffix            = "(?:[\s\(\)\[\]]|$)"
    a_number_regex_pattern = valid_prefix + optional_opening_parens + a_number + valid_suffix
    all_matches = re.findall(a_number_regex_pattern, body)
    return deduplicate(all_matches)

def look_for_A(id_, text, comment):
    seen = open_list(id_)
    re_s = a_numbers_in_text(text)
    if test:
        print(re_s)
    post_me = []
    for seq_n in re_s:
        if seq_n not in seen:
            post_me.append(markup(seq_n))
            seen.append(seq_n)
    if len(post_me) > 0:
        post_me.append(me())
        comment(escape(joiner().join(post_me)))
        save_list(seen, id_)
        raise FoundOne

def load_search(terms):
    src = read_url("http://oeis.org/search?fmt=data&q="+terms)
    ls = re.findall("href=(?:'|\")/A([0-9]{6})(?:'|\")", src)
    try:
        tot = int(re.findall("of ([0-9]+) results found", src)[0])
    except:
        tot = 0
    return ls, tot

def markup(seq_n):
    pattern = re.compile("%N (.*?)<", re.DOTALL|re.M)
    desc = read_url("http://oeis.org/A" + seq_n + "/internal")
    desc = pattern.findall(desc)[0].strip("\n")
    pattern = re.compile("%S (.*?)<", re.DOTALL|re.M)
    seq = read_url("http://oeis.org/A" + seq_n + "/internal")
    seq = pattern.findall(seq)[0].strip("\n")
    new_com = "[A" + seq_n + "](http://oeis.org/A" + seq_n + "/): "
    new_com += desc + "\n\n"
    new_com += seq + "..."
    return new_com

def me():
    return "I am OEISbot. I was programmed by /u/mscroggs. " \
           "[How I work](http://mscroggs.co.uk/blog/20). " \
           "You can test me and suggest new features at /r/TestingOEISbot/."

def joiner():
    return "\n\n- - - -\n\n"

r = praw.Reddit("DEFAULT", user_agent="OEIS sequence poster")

#access_i = r.refresh_access_information(refresh_token=r.refresh_token)
#r.set_access_credentials(**access_i)

auth = r.user

subs = ["TestingOEISbot","math","mathpuzzles","casualmath","theydidthemath",
        "learnmath","mathbooks","cheatatmathhomework","matheducation",
        "puremathematics","mathpics","mathriddles","askmath",
        "recreationalmath","OEIS","mathclubs","maths"]

if test:
    subs = ["TestingOEISbot"]

try:
    for sub in subs:
        print(sub)
        subreddit = r.subreddit(sub)
        for submission in subreddit.hot(limit = 10):
            if test:
                print(submission.title)
            look_for_A(submission.id,
                       submission.title + "|" + submission.selftext,
                       submission.url,
                       submission.reply)

            for comment in submission.comments:
                if ( not isinstance(comment, MoreComments)
                     and comment.author is not None
                     and comment.author.name != "OEISbot" ):
                    look_for_A(submission.id,
                               comment.body,
                               comment.reply)

except FoundOne:
    pass
