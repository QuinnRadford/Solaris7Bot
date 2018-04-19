#!/usr/bin/python3
import socket
import re
import time
import msvcrt
import datetime
import math

HOST = "irc.twitch.tv"              # the Twitch IRC server
PORT = 6667                         # always use port 6667!
NICK = "solaris7bot"            # your Twitch username, lowercase
PASS = "oauth:in4huo5y2erbpkzjbi79d8q0tmxak0" # your Twitch OAuth token
CHAN = "#k1ttykat"                   # the channel you want to join
CHAT_MSG=re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
RATE = (100/30) # messages per second

users = {}
bets = {}
delegates = ["k1ttykat"]

isBetting = False
bettingTime = time.time()

def chat(sock, msg):
    data = "PRIVMSG " + CHAN + " :" + msg + "\r\n"
    print(data)
    sock.send(data.encode())


s = socket.socket()
s.connect((HOST, PORT))
s.send("PASS {}\r\n".format(PASS).encode("utf-8"))
s.send("NICK {}\r\n".format(NICK).encode("utf-8"))
s.send("JOIN {}\r\n".format(CHAN).encode("utf-8"))
chat(s, "Bot Online Register with !reg to begin")
while True:
    #close after betting window expired
    if isBetting and bettingTime < time.time():
        chat(s, "Bets closed")
        isBetting = False
    
    response = s.recv(1024).decode("utf-8")
    if response == "PING :tmi.twitch.tv\r\n":
        s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    else:
        username = re.search(r"\w+", response).group(0) # return the entire match
        message = CHAT_MSG.sub("", response)
        print(username + ": " + message)
        if re.match(r"^!start", message) and username in delegates:
            if not isBetting:
                bets = {}
                chat(s, "Place your bets, you have 30 seconds..")
                isBetting = True
                bettingTime = time.time() + 30
            else:
                chat(s, "Already in progress")
        elif re.match(r"^!stop", message) and username in delegates:
            if isBetting:
                chat(s, "Bets closed")
                isBetting = False
            else:
                chat(s, "Already closed")
        elif re.match(r"^!bet\s", message):
            if isBetting and username in users:
                matches = message.split(" ")
                print(str(len(matches))+ " matches found " + str(matches[1].isalpha) + " " + str(matches[2].replace('\r\n', '').isdigit()))
                if len(matches) == 3 and matches[1].isalpha() and matches[2].replace('\r\n', '').isdigit():
                    if  int(matches[2]) < 100:
                        chat(s, username + " you need to bet at least 100 boops")
                    elif int(users[username]) < int(matches[2]):
                        chat(s, username + " not enough boops")
                    else:
                        bets[username] = {"bet":matches[1], "amt":matches[2]}
                else:
                    chat(s, "include a bet and an amount in that order")
            elif isBetting and username not in users:#if they are not in the users array
                chat(s, username + " needs to register with !reg")
            else:
                chat(s, "Betting is closed")
        elif re.match(r"^!result", message) and username in delegates:
            if isBetting:
                isBetting = False
            matches = message.split(' ')
            finalResults = "Winners:"
            loserCash = 0
            winnerCash = 0
            winningPlayers = {}
            result = matches[1]
            for user,bet in bets.items():#figure out who won and lost
                thisGuess = str(bet["bet"])
                if re.match(bet["bet"], result):
                    winningPlayers[user] = bet
                    winnerCash += int(bet["amt"])
                    print(user + " won")
                else:
                    loserCash += int(bet["amt"])
                    users[user] = users[user] - int(bet["amt"])#set new balance of losers
                    print(user + " lost")
            for winuser,bet in winningPlayers.items():#divy up the winnings
                thiswinning = math.floor(loserCash * (int(bet["amt"]) / winnerCash)) + 100
                users[winuser] = int(users[winuser]) + thiswinning
                finalResults += " " + winuser + " won " + str(thiswinning) + " extra boops "
            chat(s, finalResults)
        elif re.match(r"^!hiscore", message):
            scoreboard = ""
            scoreIndex = 1
            sorted_u = sorted(users, key=users.get, reverse=True)
            chat(s, "Hi-Score List")
            time.sleep(1 / RATE)
            chat(s, "---------------")
            time.sleep(1 / RATE)
            for user in sorted_u:
                chat(s, str(scoreIndex) + ". " + user + " with " + str(users[user]) + " boops")
                time.sleep(1 / RATE)
                if scoreIndex == 10:
                    break
                scoreIndex += 1

            
            chat(s, scoreboard)
        elif re.match(r"^!score", message):
            if username in users:
                chat(s, username + " has " + str(users[username]) + " boops")
            else:
                chat(s, username + " has 0 boops")
        elif re.match(r"^!help", message):
            chat(s,'Use the commands "!reg" to register "!bet win/lose amount" to place a bet, "!score" to check your score, and "!hiscore" to display the top 10')
        elif re.match(r"^!exit", message) and username in delegates:
            chat(s, "It's so cold..")
            exit()
        elif re.match(r"^!reg", message):
            if username in users:
                chat(s, "User already registered")
            else:
                users[username] = 1000
                chat(s, username + " has 1000 boops, good luck")
        elif re.match(r"^!delegate\s", message) and username in delegates:
             matches = message.split(' ')
             delegates.append(matches[1].replace('\r\n', ''))
             chat(s, matches[1].replace('\r\n', '') + " now has The Power")


        time.sleep(1 / RATE)
