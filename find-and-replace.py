import praw
import re
import os
import random
import socket
import sys

"""
#Example: Convert links like "/r/Spacex/ikfxn6/" to "/r/SpaceX/comments/ikfxn6/"
search: (r\/spacex\/)([a-zA-Z0-9]{6}[\/)])
replace (adv.):  match.group(1) + "comments/" + match.group(2)
"""

def strip(page):
    return str(page).split("/",1)[1]


def replace(text, string, replacement, margin=5, ignorecase=False, risky=False):
    changes_made = 0
    matches = re.finditer(".{0," + str(margin) + "}" + string + ".{0," + str(margin) + "}", text, flags=(re.I if ignorecase else 0))
    for m in matches:
        print(m.group())
        if risky or input().lower() == "y":
            changes_made += 1
            text = text[:m.start()] + re.sub(string, replacement, text[m.start():], count=1, flags=(re.I if ignorecase else 0))
    return text, changes_made


if __name__=="__main__":
    #Header
    print("-=-=-=-=-=-=-=-=-=-=-")
    print("  find-and-replace")
    print("   /u/thatnerdguy1")
    print("-=-=-=-=-=-=-=-=-=-=-\n")
    
    
    #Authorize
    reddit = praw.Reddit(user_agent="find-and-replace by thatnerdguy1",
                         client_id="LCLvKNitX8kktQ", client_secret=None,
                         redirect_uri="http://localhost:8080")
    state = str(random.randint(0, 65000))
    print("Complete the authorization that opened in your browser.")
    os.startfile(reddit.auth.url(["wikiread","wikiedit"], state, "temporary"))
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8080))
    server.listen(1)
    client = server.accept()[0]
    server.close()
    
    data = client.recv(1024).decode("utf-8")
    param_tokens = data.split(" ", 2)[1].split("?", 1)[1].split("&")
    params = {key: value for (key, value) in [token.split("=") for token in param_tokens]}

    if state != params["state"]:
        raise Exception(f"State mismatch while processing authorization. Expected: {state} Received: {params['state']}")
    elif "error" in params:
        raise Exception("Error when processing authorization: " + params["error"])

    refresh_token = reddit.auth.authorize(params["code"])
    print("Authorization successful.\n(you can close the browser tab that opened)\n")
    
    
    #Input
    subreddit = input("Enter the name of the subreddit: ").split("/")[-1]
    
    print("Enter the pages to be edited, separated by spaces.")
    print("To list all pages, enter \"pages\".")
    print("To edit all pages, enter \"all\".")
    
    pages = input().split()
    while (not pages) or ("pages" in pages): 
        if "pages" in pages:
            print(f"--- All pages in /r/{subreddit}: ---")
            for p in reddit.subreddit(subreddit).wiki:
                print(strip(p))
        pages = input("Enter the pages to be edited. ").split()
    if "all" in pages:
        pages = reddit.subreddit(subreddit).wiki
    else:
        pages = [reddit.subreddit.wiki[p] for p in pages]
        
    search = input("Enter the string to search (regex syntax is valid!): ")
    
    ignorecase = input("Ignore case? (\"y\"/\"n\"): ") == "y"
    
    while True:
        new = input("Enter the string to replace each instance with. For advanced functionality, enter \"!ADV!\": ")
        if new == "!ADV!":
             func_in = input("Complete the lambda function, which takes a single match object as input, and outputs the replacement string: (or, enter \"X\" to return to the simple functionality)\nlambda match: ")
             if func_in != "X":
                 exec("new = lambda match: " + func_in)
                 break
        else:
            break
        
    if input("The current view margin is 6. Do you want to adjust it? (\"y\"/\"n\"): ") == "y":
        margin = int(input("Enter a new view margin: "))
    else:
        margin = 6
        
    risky = input("Would you like to skip confirmation of each replacement? This is risky. (\"y\"/\"n\"): ") == "y"
    
    
    #Main loop through pages
    total = 0
    print("\nEach match will be shown. Enter \"y\" to replace, or anything else to skip replacement.")
    for page in pages:
        if not page.may_revise:
            print(f"\nYou do not have permission to edit {strip(page)}. Proceeding.")
            continue
        print(f"\nPage {strip(page)}:\n")
        
        new_text, changes_made = replace(page.content_md, search, new, margin, ignorecase, risky)
        
        if changes_made:
            if input(f"\nAll matches checked.\nConfirm {changes_made} change{'s' if total != 1 else ''} for {strip(page)}? (\"y\"/\"n\"): ") == "y":
                page.edit(new_text, f"find and replace {search} with {new if isinstance(new,str) else '<function>'}")
        total += changes_made
        print(f"Finished page {strip(page)}.")
        
    print(f"\nAll selected pages complete. {total} total change{'s' if total != 1 else ''} made.")