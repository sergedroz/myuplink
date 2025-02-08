#!/usr/bin/env python3

import datetime
import json
import httpx
import getpass
import os
from random import randrange

def mk_state(l=3):
    """
    Create some sort of unique identification string that's human readable from l number of words.
    """            
    wordlist = ["window", "previous","bite","sisters","brawny", "return","uncle",
                "elbow", "queen", "desert", "rose", "suffer" ]
    return "-".join([ wordlist[randrange(len(wordlist))] for i in range(l) ])


class MyUplink(object):

    def __init__(self, client_id, client_secret, redirect_url,  scope = "READSYSTEM offline_access", token_file="~/.myuplink-token" ):
        """
        config: Path to a yaml file containing the lines:
        myuplink:
            cient-id: client id as configured on dev.myuplink.com
            client-secret: the coresponding secret
        redirect_url: URL where the oauth answer will be sent to
        uuid: unique string
        token_file: where the token is saved

        The first time a token is created human intervention is necessary. At this point a helper function
        mk_state(l) where l is the number of words used. The function should return a random human
        readable string.
        """
        
        self.client_id     = client_id
        self.client_secret = client_secret
        self.redirect_url  = redirect_url
        self.token_file    = token_file
        
        self.scope         = scope
        try:
            with open( os.path.expanduser(self.token_file), "r" ) as fp:
                self.token = json.load( fp )
            self.expires_at = datetime.datetime.fromtimestamp( self.token['expires_at'] )
        except:
             self.create_token()
        self.session = httpx.Client( )
        self.refresh_token()
    
    def token_saver(self ):
        """
        Save token
        """
        with open( os.path.expanduser(self.token_file), "w" ) as fp:
            json.dump(self.token, fp )
    
    def create_token(self):
        """
        Get a new token. This requires user interaction.
        """
        state = mk_state(3)
        data = {
            "response_type": 	"code",
            "client_id":  	    self.client_id,
            "Scope": 	        self.scope,
            "redirect_uri": 	self.redirect_url,
            "state":            state
        }
        authorize_url = 'https://api.myuplink.com/oauth/authorize?{}'.format( "&".join( "{}={}".format(k,v) for k,v in data.items() ).replace(' ','%20') )
        print( "Please go to: {} in you browser and enter the code below.\n\nCompare the state to {}".format(authorize_url, state))
        code = getpass.getpass("Code: ")

        data = {   
            "grant_type": 	"authorization_code",
            "client_id": 	 self.client_id,
            "client_secret": self.client_secret,
            "code": 	     code,
            "redirect_uri":  self.redirect_url
        }
        r = httpx.post( "https://api.myuplink.com/oauth/token", data=data)
        self.token = r.json()
        # = datetime.datetime.now() + datetime.timedelta(seconds=self.token['expires_in'])
        self.expires_at = datetime.datetime.now() + datetime.timedelta(seconds=self.token['expires_in'])
        self.token['expires_at'] = int( self.expires_at.timestamp() ) 
        self.token_saver()

    def refresh_token(self):
        data = {
            "grant_type": 	    "refresh_token",
            "client_id": 	    self.client_id,
            "client_secret": 	self.client_secret,
            "refresh_token": 	self.token['refresh_token']
        }

        r = httpx.post( "https://api.myuplink.com/oauth/token", data=data)
        self.token = r.json()
        print(self.token)
        self.expires_at = datetime.datetime.now() + datetime.timedelta(seconds=self.token['expires_in'])
        self.token['expires_at'] = int( self.expires_at.timestamp() ) 
        self.token_saver()
        self.session.headers['Authorization'] = 'Bearer {}'.format( self.token['access_token'])


    def request(self, request='get', *args, **kwargs):
        """
        Do a webrequest. 
        """
        if datetime.datetime.now() > self.expires_at:
            self.refresh_token()
        if request == 'get':
             return self.session.get(*args, **kwargs)
        elif request == 'put':
             return self.session.put(*args, **kwargs)
        elif request == 'post':
             return self.session.post(*args, **kwargs)
        elif request == 'patch':
               return self.session.patch(*args, **kwargs)
        elif request == 'delete':
            return self.session.delete(*args, **kwargs)
    
    def get(self,*args, **kwargs):
        return self.request('get', *args, **kwargs)
    
    def put(self,*args, **kwargs):
        return self.request('put', *args, **kwargs)
    
    def post(self,*args, **kwargs):
        return self.request('post', *args, **kwargs)

    def patch(self,*args, **kwargs):
        return self.request('patch', *args, **kwargs)

    def delete(self,*args, **kwargs):
        return self.request('delete', *args, **kwargs)

    def get_systems(self):
        """
        Return all systems you have access to
        Todo: Add iteration over pages to get all systems, not onlyy the first 10
        """
        return self.session.get( "https://api.myuplink.com/v2/systems/me").json()
        
    def get_device_points(self, device_id):
        """
        Get data for a specific device
        """
        return self.session.get( "https://api.myuplink.com/v3/devices/{}/points".format(device_id)).json()

if __name__ == "__main__":
    
  
    import argparse
    
    
    parser = argparse.ArgumentParser(
                    prog='myuplink.py',
                    description='Query myuplink API')
    
    parser.add_argument('-l', '--list', action='store_true', help="List available devices")      # option that takes a value
    parser.add_argument('-r', '--read', help="Read out device given by id" )
    args = parser.parse_args()

    client_id     = "client_id"
    client_secret = "client_password"
    redirect_url  = "https://example.comh/myuplink-p.php" 
    

    ms2 = MyUplink( client_id, client_secret, redirect_url )
    
    # get my systems:
    if args.list:
        r = ms2.get_systems()
        for i in r['systems']:
            print( "Sytem {}\nDevices".format(i['name']))
            for j in i['devices']:
                  print( "{}: {}".format( j['product']['name'], j['id'], j['connectionState'] ) )
    
    # Show settings:
    if args.read:
        for i in ms2.get_device_points(args.read):
            print( "{}: {} {}".format( i['parameterName'],i['value'], i['parameterUnit'] ))
