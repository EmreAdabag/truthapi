import requests as rq
import json

class TruthAPI:
    client_info_url = 'https://truthsocial.com/packs/js/application-a21b98576366c231407a.js'
    access_token_url = 'https://truthsocial.com/oauth/token'
    trump_acc_url = 'https://truthsocial.com/api/v1/accounts/107780257626128497/statuses'
    post_truth_url = 'https://truthsocial.com/api/v1/statuses'
    stock_headers = { 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0' }
    
    
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        
        self.access_token = None
    
    
    # logs into truth social, i.e. gets access tokens and whatever
    def login(self, username, password):
        resp_getclientinfo = rq.get(TruthAPI.client_info_url)
        if resp_getclientinfo.ok == False:
            print(f'client info request failed')
            return
        
        self.client_id, self.client_secret, self.redirect_uri = self._extract_client_info(resp_getclientinfo)
        
        access_token_payload = self._generate_access_token_payload(username, password)
        
        resp_login = rq.post(
            TruthAPI.access_token_url, 
            json=access_token_payload, 
            headers=TruthAPI.stock_headers
        )
        if resp_login.ok == False:
            print(f'login request failed')
            return
        
        self.access_token = self._extract_access_token(resp_login)
    
    
    # returns a list of the 10 most recent trump truths along with IDs so u can reply
    def get_trump_truths(self):
        if self.access_token is None:
            print(f'missing access token')
            return
        
        cookies = { 'authBearer': 'Bearer+' + self.access_token }
        
        resp_gettruths = rq.get(
            TruthAPI.trump_acc_url,
            headers=TruthAPI.stock_headers,
            cookies=cookies
        )
        if resp_gettruths.ok == False:
            print(f'failed to get truths')
            return
        
        truths = self._extract_truths(resp_gettruths)
        return truths
    
    
    # reply to a truth, recipient is the username of the original truther
    def truth_reply(self, truth_id, recipient, reply):
        if self.access_token is None:
            print(f'missing access token')
            return
        
        headers = TruthAPI.stock_headers
        headers['Authorization'] = 'Bearer ' + self.access_token
        
        payload = self._generate_post_truth_payload(
            truth_id,
            recipient,
            reply
        )
        
        resp_posttruth = rq.post(
            url=TruthAPI.post_truth_url,
            json=payload,
            headers=headers
        )
        
        if resp_posttruth.ok == False:
            print(f'failed to post truth')
            return
    
    
    
    ##########################################
    # Internal methods for parsing and stuff #
    ##########################################    
    def _generate_access_token_payload(self, username, password):
        if self.client_id is None or self.client_secret is None or self.redirect_uri is None:
            print(f'missing client information')
            return None
        
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': "password",
            'password': password,
            'redirect_uri': self.redirect_uri,
            'scope': 'read write follow push',
            'username': username
        }    
        return payload


    def _generate_post_truth_payload(self, truth_id, recipient, message):
        payload = {
            "content_type":"text/plain",
            "in_reply_to_id":truth_id,
            "media_ids":[],
            "poll":None,
            "quote_id":"",
            "status":message,
            "to":[recipient],
            "visibility":"public",
            "group_timeline_visible":False
        }
        return payload
    
    
    def _extract_client_info(self, r):
        client_id = r.text.split('client_id":"')[1].split('","')[0]
        client_secret = r.text.split('client_secret":"')[1].split('","')[0]
        redirect_uri = r.text.split('redirect_uris:"')[1].split('"')[0]
        return (client_id, client_secret, redirect_uri)
    
    
    def _extract_access_token(self, r):
        r_dict = json.loads(r.text)
        access_token = r_dict['access_token']
        return access_token
    
    
    def _extract_truths(self, r):
        truth_dict = json.loads(r.text)
        truths = [ { 'id': t['id'], 'user': t['account']['username'], 'content': t['content'] } for t in truth_dict]
        return truths