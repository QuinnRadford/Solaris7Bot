#!/usr/bin/python3
import socket
import re
import time
HOST = "irc.twitch.tv"              # the Twitch IRC server
PORT = 6667                         # always use port 6667!
NICK = "solaris7bot"            # your Twitch username, lowercase
PASS = "oauth:in4huo5y2erbpkzjbi79d8q0tmxak0" # your Twitch OAuth token
CHAN = "#k1ttykat"                   # the channel you want to join
CHAT_MSG=re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
RATE = (100/30) # messages per second

users = {}
bets = {}

isBetting = False

def chat(sock, msg):
    data = "PRIVMSG " + CHAN + " :" + msg + "\r\n"
    print(data)
    sock.send(data.encode())

def timeout(sock, user, secs=600):
    chat(sock, ".timeout {}".format(user, secs))


s = socket.socket()
s.connect((HOST, PORT))
s.send("PASS {}\r\n".format(PASS).encode("utf-8"))
s.send("NICK {}\r\n".format(NICK).encode("utf-8"))
s.send("JOIN {}\r\n".format(CHAN).encode("utf-8"))

while True:
    response = s.recv(1024).decode("utf-8")
    if response == "PING :tmi.twitch.tv\r\n":
        s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    else:
        username = re.search(r"\w+", response).group(0) # return the entire match
        message = CHAT_MSG.sub("", response)
        print(username + ": " + message)
        if re.match(r"!s7\sstart", message):
            if not isBetting:
                bets = {}
                chat(s, "Place your bets..")
                isBetting = True
            else:
                chat(s, "Already in progress")
        elif re.match(r"!s7\sstop", message):
            if isBetting:
                chat(s, "Bets closed")
                isBetting = False
            else:
                chat(s, "Already closed")
        elif re.match(r"!s7\sbet\s", message):
            if isBetting:
                matches = re.search(r"(?<=!s7\sbet\s)([A-z\s\!\@\#\$\%\^\&\*\(\)]*)", message)
                bets[username] = matches.group(0)
            else:
                chat(s, "Betting is closed")
        elif re.match(r"!s7\sresult", message):
            if isBetting:
                isBetting = False
            matches = re.search(r"(?<=!s7\sresult\s)([A-z\s\!\@\#\$\%\^\&\*\(\)]*)", message)
            finalResults = "Winners:"
            result = matches.group(0)
            for user,bet in bets.items():
                if bet == result:
                    if user in users:
                        users[user] = users[user] + 1
                    else:
                        users[user] = 1
                    finalResults += " " + user + " "
            chat(s, finalResults)
        elif re.match(r"!s7\sscore", message):
            scoreboard = ""
            scoreIndex = 1
            sorted_u = sorted(users, key=users.get)
            for user in sorted_u:
                scoreboard =scoreboard + " " + str(scoreIndex) + ". " + user + " with " + str(users[user]) + " points"
                scoreIndex += 1
            chat(s, "Hi-Score List")
            chat(s, "---------------")
            chat(s, scoreboard)
            
        time.sleep(1 / RATE)
