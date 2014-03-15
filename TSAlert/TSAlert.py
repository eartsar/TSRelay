#!/usr/bin/python

import telnetlib
import thread
from enum import Enum
from datetime import datetime
from threading import Lock
from time import sleep

class TextMessageTargetMode(Enum):
     CLIENT = 1 #target is a client 
     CHANNEL = 2 #target is a channel 
     SERVER = 3  #target is a virtual server 

class EventMode(Enum):
    #server|channel|textserver|textchannel|textprivate
    textserver = 3
    textchannel = 2
    textprivate = 1

class TS3Error(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        self.time = datetime.now()

    def __str__(self):
        return "TS3ERROR %s: %s" % (self.code, self.msg)

class TeamSpeak:
    def __init__(self, host='localhost', portQuery=10011, portVOIP=9987, portFTP=30033, username=None, password=None):
        self.host     = host
        self.queryPort= portQuery
        self.timeout  = 5.0
        self.username = username
        self.password = password
        self.__ioLock = Lock()
        self.listenThread = None
        self.encoding = {
            "\\":"\\\\", "/":"\\/",
            " ":"\\s", "|":"\\p",
            "\a":"\\a", "\b":"\\b",
            "\f":"\\f", "\n":"\\n",
            "\r":"\\r", "\t":"\\t",
            "\v":"\\v"
         }
        self.connection = None
        self.logged_in = False
        self.virtualserver = None

    def connected(self):
        if not self.connection:
            return False

        try:
            self.connection.write('\n\r')
            return True
        except:
            return False

    def decode(self, result):
        """
        Decodes the result
        """
        if '|' in result:
            decodable = result.split('|')
            decoded = []
            for d in decodable:
                decoded.append(self.__decodeSingle(d))
            return decoded
        return self.__decodeSingle(result)

    def __decodeSingle(self, result):
        if type(result) == str:
            decodable = result.split()
        elif type(result) == list:
            decoded = []
            for i in result:
                decoded.append(self.__decodeSingle(i))
            return decoded
        elif type(result) == dict:
            return result
        else:
            raise Exception("Type %s is unrecognized" % type(result))

        decoded = {}
        for decodeme in decodable:
            expl = decodeme.split('=',1)
            if len(expl) != 2:
                decoded[decodeme]=''
                continue
            for o,r in self.encoding.iteritems():
                expl[0] = expl[0].replace(r,o)
                expl[1] = expl[1].replace(r,o)
            decoded[expl[0]]=expl[1]
        return decoded

    def encode(self, args={}):
        """
        Encodes the arguments
        """
        if isinstance(args,int): args = str(args)
        if isinstance(args,str):
            for r,o in self.encoding.iteritems():
                args = args.replace(r,o)
            return args
        encoded = ''
        for k,v in args.iteritems():
            if not isinstance(v,int):
                for r,o in self.encoding.iteritems():
                    v = v.replace(r,o)
                encoded += ' '+k
                if v != '': encoded += '='+v
            else:
                encoded += ' '+k+'='+str(v)
        return encoded.strip()

    def sendCommand(self, command, preRead=0, postRead=0):
        if not self.connected():
            raise Exception('Not connected to a TeamSpeak server')

        if self.logged_in == False: 
            if command.startswith("login") or \
                command.startswith("use") or \
                command in ["quit", "logout"]:
                    pass
            else:
                raise Exception("Not logged in!")

        #sleep(0.1)

        #print("*"+command)

        try:
            return self._sendCommand(command, preRead, postRead)
        except EOFError as e:
            print(e)
            while not self.connected():
                print("Reconnect attempt...")
                self.connect()
                if hasattr(self, "callback"):
                    self.callback.reconnect()
                sleep(1)
            self.sendCommand(command, preRead, postRead)

    def _sendCommand(self, command, preRead=0, postRead=0, timeout=None):
        """
        Send a command to the server and receive the output
        """

        print("*"+command)

        if timeout == None:
            timeout = self.timeout

        with self.__ioLock:
            self.connection.write(command+'\n\r')
            if command == "quit":
                return

            for i in range(preRead): 
                self.connection.read_until("\n\r", timeout)

            data = self.connection.read_until('\n\r',timeout)
            data = self.decode(data)

            data2 = None

            if type(data) == dict:
                if data.keys() != ["msg", "id", "error"]:
                    data2 = self.connection.read_until('\n\r',timeout)
                    data2 = self.decode(data2)
            else:
                data2 = self.connection.read_until('\n\r',timeout)
                data2 = self.decode(data2)
            
            for i in range(postRead): 
                self.connection.read_until("\n\r", timeout)

        return data, data2

    def registerEvent(self, **args):
        """
        Creates a listener that will be destroyed once the callback returns false
        Make sure that the permissions are set properly

        The username and password must be set if used becuase the listener session has to log in again if the server disconnects the client
        """
        # Parse ALL the arguments!
        # Todo: clean this shit up
        callback = None
        event='textchannel'
        mode=None
        cid=None
        username=None
        password=None

        if args.has_key("callback"): 
            callback = args['callback']
        elif args.has_key("callback") and not hasattr(args['callback'], '__call__'): 
            raise Exception('callback is not a function')
        
        if args.has_key("channel") and isinstance(args['channel'],int): cid = args['channel']
        elif args.has_key("channel") and not isinstance(args['channel'],int): raise Exception('channel is not a integer')

        if args.has_key("username") and isinstance(args['username'],str): username = args['username']
        elif args.has_key("username") and not isinstance(args['username'],str): raise Exception('username is not a string')

        if args.has_key("password") and isinstance(args['password'],str): username = args['password']
        elif args.has_key("password") and not isinstance(args['password'],str): raise Exception('password is not a string')

        if args.has_key("mode") and isinstance(args['mode'],int):
            mode = args['mode']
            event = str(EventMode(mode)).split(".")[-1]
        elif args.has_key("mode") and not isinstance(args['password'],int):
            raise Exception('mode is not an int')

        self.callback = callback
        if not self.connected():
            self.callback.reconnect()

        if not self.connected():
            raise Exception('Not connected to a TeamSpeak server')

        if username != None and password != None:
            self.login(usernamer, password)

        if cid:
            if mode == Teamspeak.TextMessageTargetMode.CHANNEL.value:
                self.moveMe(cid)
                self.servernotifyregister(event, cid)
            elif mode == Teamspeak.TextMessageTargetMode.CLIENT.value:
                self.servernotifyregister(event, cid)
            else:
                self.servernotifyregister(event)

        while True:
            try:
                message = self.connection.read_until('\n\r', 30)
                try:
                    self.decode(message)['invokername']
                except: 
                    if message:
                        print("HUH!?: %s" % message )
                    continue

                if callback != None:
                    if self.callback.callback(message) == False: 
                        return
                else: # Default callback
                    print self.decode(message)['invokername']+': '+self.decode(message)['msg']
            except Exception as e:
                #import traceback
                #traceback.print_exc()
                print("[ERROR]: %s" % e)

                self.callback.reconnect()

                if cid:
                    if mode == Teamspeak.TextMessageTargetMode.CHANNEL.value:
                        self.moveMe(cid)
                        self.servernotifyregister(event, cid)
                    elif mode == Teamspeak.TextMessageTargetMode.CLIENT.value:
                        self.servernotifyregister(event, cid)
                    else:
                        self.servernotifyregister(event)

    def connect(self, server=1):
        """
        Open a link to the Teamspeak 3 query port
        @return: A tulpe with a error code. Example: ('error', 0, 'ok')
        """

        #if self.connected() and self.virtualserver == server:
        #    return

        #Create new connection
        with self.__ioLock:            
            try:
                self.connection = telnetlib.Telnet(self.host, self.queryPort, None)
            except telnetlib.socket.error:
                raise TS3Error(10, 'Can not open a link on the port or IP')

            output = self.connection.read_until('TS3', self.timeout)
            if output.endswith('TS3') == False:
                raise TS3Error(20, 'This is not a Teamspeak 3 Server')
            self.connection.read_until("command.\n\r", self.timeout)

            self.virtualserver = None
            self.logged_in = False

        if self.virtualserver != server:
            #connect to the Virtual Server
            data, _ = self.sendCommand('use sid='+str(server))
            if type(data) != dict:
                raise Exception('invalid resonse')
           
            if data['id'] != '0':
                raise TS3Error(data['id'], data['msg'])
            elif data["id"] == '3329': #handle banned for X seconds
                timeout = int(data["extra_msg"].split()[-2])
                timeout_sleeps = int( timeout / 30 ) + 1
            
                for i in xrange(timeout_sleeps):
                    print("Banned for %s seconds." % timeout)
                    if timeout > 30:
                        timeout = timeout - 30
                        sleep(30)
                    elif timeout > 1:
                        timeout = 0
                        sleep(timeout)
                    else:
                        sleep(1)

                self.connect(server=server)
            elif data['id'] == '0':
                self.virtualserver = server

        if self.logged_in == False:
           self.login()

    def disconnect(self):
        if self.logged_in:
            self.logout()

        self.sendCommand("quit")
        self.connection.close()

    def login(self, username=None, password=None):
        if not self.connected():
            raise Exception('Not connected to a TeamSpeak server')

        if not username:
            username = self.username

        if not password:
            password = self.password

        if username == None or password == None:
            #print("user: %s pass:%s" % (username, password))
            raise Exception("User or pass is null")

        if self.logged_in == False:
            reply, _ = self.sendCommand('login %s %s' % (self.encode(username), self.encode(password)))

            if type(reply) == dict and reply["id"] == '0':
                self.logged_in = True
            elif type(reply) == dict and reply.has_key("msg"):
                raise Exception('Login refused (%s)' % reply["msg"])
            else:
                raise Exception("Reply is %s" % reply)

    def logout(self):
        if not self.connected():
            raise Exception('Not connected to a TeamSpeak server')

        if self.logged_in:
            reply, _ = self.sendCommand("logout")
            if type(reply) == dict and reply["id"] in ['0', '518']:
                self.logged_in = False
            elif type(reply) == dict and reply.has_key("msg"):
                raise Exception('Login refused (%s)' % reply["msg"])
            else:
                raise Exception("Reply is %s" % reply)

    def whoami(self):
        data, _ =  self.sendCommand("whoami")
        return data

    def servernotifyregister(self, event, cid=None):
        #servernotifyregister event={server|channel|textserver|textchannel|textprivate} [id={channelID}]
        command = 'servernotifyregister event='+self.encode(event)
        if cid: 
            command = 'servernotifyregister '+self.encode({'event':event,'id': cid})

        data, reply = self.sendCommand(command)
        if data['id'] != '0':
            raise TS3Error(data['id'], data['msg'])

    def getServers(self):
        data, reply = self.sendCommand('serverlist')
        if type(data) is dict and data.has_key("msg"):
            raise Exception(data)
        return data

    def getChannels(self):
        data, reply = self.sendCommand('channellist')
        if type(data) is dict and data.has_key("msg"):
            raise Exception(data)
        return data

    def getClients(self):
        data, reply = self.sendCommand('clientlist')
        if type(data) is dict and data.has_key("msg"):
            raise Exception(data)
        return data

    def moveMe(self, cid):
        whoami = self.whoami()
        data, _ = self.sendCommand('clientmove clid=%s cid=%s' % (whoami["client_id"], cid))
        if data['id'] not in ['0', '770']:
            raise Exception('Could not move client: '+data['msg'])
        return data

    def sendtextmessage(self, msg, targetmode, target):
        for key in self.encoding.keys():
            msg = msg.replace(key, self.encoding[key])

        reply, _ = self.sendCommand('sendtextmessage targetmode=%s target=%s msg=%s' % (targetmode, target, msg))
        if reply.has_key("id") and reply["id"] != '0':
            raise TS3Error(reply["id"], reply["msg"])

    def sendClientText(self, msg, client_id):
        self.sendtextmessage(msg, TextMessageTargetMode.CLIENT.value, client_id)

    def sendChannelText(self, msg, channel_id):
        self.moveMe(channel_id)
        self.sendtextmessage(msg, TextMessageTargetMode.CHANNEL.value, channel_id)

    def sendServerText(self, msg, server_id):
        self.sendtextmessage(msg, TextMessageTargetMode.SERVER.value, server_id)