#!/usr/bin/python
import TSAlert as Teamspeak
import time
import urllib2
import hashlib
import re
import pyttsx
engine = pyttsx.init()

ReplyFlagsRE = re.compile('<INPUT NAME=(.+?) TYPE=(.+?) VALUE="(.*?)">', re.IGNORECASE | re.MULTILINE)

class Session(object):
        keylist=['stimulus','start','sessionid','vText8','vText7','vText6','vText5','vText4','vText3','vText2','icognoid','icognocheck','prevref','emotionaloutput','emotionalhistory','asbotname','ttsvoice','typing','lineref','fno','sub','islearning','cleanslate']
        headers={}
        headers['User-Agent']='Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0'
        headers['Accept']='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        headers['Accept-Language']='en-us;q=0.8,en;q=0.5'
        headers['X-Moz']='prefetch'
        headers['Accept-Charset']='ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        headers['Referer']='http://www.cleverbot.com'
        headers['Cache-Control']='no-cache, no-cache'
        headers['Pragma']='no-cache'

        def __init__(self):
                self.arglist=['','y','','','','','','','','','wsf','','','','','','','','','0','Say','1','false']
                self.MsgList=[]

        def Send(self):
                data=encode(self.keylist,self.arglist)
                digest_txt=data[9:29]
                hash=hashlib.md5(digest_txt).hexdigest()
                self.arglist[self.keylist.index('icognocheck')]=hash
                data=encode(self.keylist,self.arglist)
                req=urllib2.Request("http://www.cleverbot.com/webservicemin",data,self.headers)
                f=urllib2.urlopen(req)
                reply=f.read()
                return reply

        def Ask(self,q):
                self.arglist[self.keylist.index('stimulus')]=q
                if self.MsgList: self.arglist[self.keylist.index('lineref')]='!0'+str(len(self.MsgList)/2)
                asw=self.Send()
                self.MsgList.append(q)
                answer = parseAnswers(asw)
                for k,v in answer.iteritems():
                        try:
                                self.arglist[self.keylist.index(k)] = v
                        except ValueError:
                                pass
                self.arglist[self.keylist.index('emotionaloutput')]=''
                text = answer['ttsText']
                self.MsgList.append(text)
                return text

def parseAnswers(text):
        d = {}
        keys = ["text", "sessionid", "logurl", "vText8", "vText7", "vText6", "vText5", "vText4", "vText3",
                        "vText2", "prevref", "foo", "emotionalhistory", "ttsLocMP3", "ttsLocTXT",
                        "ttsLocTXT3", "ttsText", "lineRef", "lineURL", "linePOST", "lineChoices",
                        "lineChoicesAbbrev", "typingData", "divert"]
        values = text.split("\r")
        i = 0
        for key in keys:
                d[key] = values[i]
                i += 1
        return d

def encode(keylist,arglist):
        text=''
        for i in range(len(keylist)):
                k=keylist[i]; v=quote(arglist[i])
                text+='&'+k+'='+v
        text=text[1:]
        return text

always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789' '_.-')
def quote(s, safe = '/'):   #quote('abc def') -> 'abc%20def'
        safe += always_safe
        safe_map = {}
        for i in range(256):
                c = chr(i)
                safe_map[c] = (c in safe) and c or  ('%%%02X' % i)
        res = map(safe_map.__getitem__, s)
        return ''.join(res)

class ChatBack(object):
    ts = Teamspeak.TeamSpeak()
    def __init__(self, ts, nick, mode, cid):
        self.ts = ts
        self.mode = mode
        self.cid = cid
        self.cb = Session()
        self.nick = nick
        self.event = str(Teamspeak.EventMode(mode)).split(".")[-1]

        self.reconnect()

    def reconnect(self):
        self.ts.connect()
        self.changeName(self.nick)
        self.registerevent()

    def reply(self, msg):
        print("%s: %s" % (self.nick, msg))
        if self.mode == 1:
            self.ts.sendClientText(msg, self.cid)
        elif self.mode == 2:
            self.ts.sendChannelText(msg, self.cid)
        elif self.mode == 3:
            self.ts.sendServerText(msg, self.cid)

        engine.say(msg)
        engine.runAndWait()

    def registerevent(self):
        self.ts.servernotifyregister(self.event, self.cid)

    def callback(self, raw):
        message = self.ts.decode(raw)
        print("%s: %s" % (message['invokername'], message['msg']))

        if message['invokername'] == self.nick:
            return None

        if  message['msg'].startswith("speak:"):
            self.reply(message['msg'].replace("speak:",""))
            return None

        if message['msg'] == "hi bot":
            msg = "hello there %s, my name is %s" % (message['invokername'], nick)
            self.reply(msg)
            return None

        if message['msg'] == 'go away bot':
            msg = 'Mkay '+message['invokername']+'. I\'ll be back in 1 minutes.'
            self.reply(msg)
            time.sleep(60*1)
            msg = 'I\'m back bitchez!'                                                                                                                                                           
            self.reply(msg)
            return None

        dumb = self.cb.Ask(message['msg'])
        if dumb:
            self.reply(dumb)
            return None

    def changeName(self, nickname):
        if self.ts.whoami()["client_nickname"] == nickname:
            return

        self.nick = nickname
        data, _ = self.ts.sendCommand('clientupdate '+ts3.encode({'client_nickname':nick}))
        if type(data) == dict and data["id"] != '0':
            raise Teamspeak.TS3Error(data["id"], data["msg"])

if __name__ == "__main__":
    #host = raw_input('host: ')
    host = "198.199.86.84"
    #port = raw_input('port: ')
    #nick = raw_input('nickname: ')
    nick = "SirBot-O"
    username = "KigenTheGreat" #"admin"
    password = "IOf0zLjM" #"Ad+9Pmcb"

    for i in Teamspeak.TextMessageTargetMode:
        print("[%s]\t%s"%(i.value, i))

    mode = raw_input("mode: ")
    mode = int(mode)

    print '\nconnecting...'
    ts3 = Teamspeak.TeamSpeak(host, username=username, password=password)
    ts3.connect()
    if ts3.connected():
        if mode == Teamspeak.TextMessageTargetMode.SERVER.value:
            print 'getting Servers'
            #items = ts3.getServers()
            items = []
            name = 'virtualserver_id'
            cid = 'sid'
        elif mode == Teamspeak.TextMessageTargetMode.CHANNEL.value:
            print 'getting Channels'
            items = ts3.getChannels()
            name = 'channel_name'
            cid = "cid"
        elif mode == Teamspeak.TextMessageTargetMode.CLIENT.value:
            print 'getting Clients'
            items = ts3.getClients()
            name = 'client_nickname'
            cid = "clid"
        else:
            print("%s is invalid" % connectto)
            ts3.disconnect()
            exit()

        for item in items:
            print '['+item[cid]+']\t'+item[name]

        cid = raw_input('cid: ')
        print '\nstarting session'
        
        chatback = ChatBack(ts3, nick, int(mode), int(cid))

        if mode == Teamspeak.TextMessageTargetMode.CLIENT.value:
            chatback.ts.sendClientText("hello there!", int(cid))
        elif mode == Teamspeak.TextMessageTargetMode.CHANNEL.value:
            chatback.ts.sendChannelText("hello there channel!", int(cid))
        elif mode == Teamspeak.TextMessageTargetMode.SERVER.value:
            chatback.ts.sendServerText("hello there server!", int(cid))

        ts3.registerEvent(callback=chatback, mode=int(mode), cid=int(cid))
