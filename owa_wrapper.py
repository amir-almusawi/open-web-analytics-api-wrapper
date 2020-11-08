#!/usr/bin/python3.7
from urllib.parse import urlencode, quote_plus
import time

import requests
from pprint import pprint

from . import config

"""
TODO:
[ ] delete_site() returns 405
[ ] delete_user() returns 405
[ ] add_user() returns 422
[ ] get_latest_actions() returns 422
[ ] get_reports() needs work
"""



class OwaWrapper():
    """Wrapper for Open Web Analytics - Data Access Api"""
    
    def __init__(self, base_url=None, apikey=None, version="v1", module="base"):
        """

        :param base_url: url of owa install or use config file, defaults to None
        :type base_url: str, optional
        :param apikey: apikey or use config file, defaults to None
        :type apikey: str, optional
        :param version: version, defaults to "v1"
        :type version: str, optional
        :param module: module, defaults to "base"
        :type module: str, optional
        """
        self._base_url = base_url or config.base_url
        self.apikey = apikey or config.apikey
        self.module = module
        self.version = version
        self._s = requests.Session()
        
        if not (self.apikey and self._base_url):
            exit('base_url and apikey required. Set in config.py or as kwargs')
                
        if not self._base_url.endswith('/'):
            self._base_url += '/'
        self._url = self._base_url.rstrip('/') + '/api/?'
        
    def _api(self, method, *args, **kwargs):
        data = {
            "owa_module": self.module,
            "owa_version": self.version,
            "owa_apiKey": self.apikey,
            }
        data.update(kwargs)
        url = self._url + urlencode(data)
        while True:
            try:                    
                r = self._s.request(method, url, data=data, timeout=10)
                r.raise_for_status()
                # print(method, r.status_code, url)
                
                r = r.json()                
                return r.get('error') or r.get('data')   
                                
            except (requests.exceptions.InvalidURL,
                    requests.exceptions.HTTPError) as e:
                print(e)
                return               
            
            except Exception as e:
                print(e)
                time.sleep(1)
        
    def get_sites(self, full_data=False):             
        """Get list of sites

        :param full_data: include db schema in return data, defaults to False
        :type full_data: bool, optional
        :return: list of sites or dict if full_data is True
        :rtype: list or dict
        """
        data = self._api('GET', owa_do='sites')
        
        if full_data:
            return data
        
        return [{
            "id":k,
            "name": data[k]['properties']['name']['value'],
            "description": data[k]['properties']['description']['value'],
            "domain": data[k]['properties']['domain']['value'],
            "site_family": data[k]['properties']['site_family']['value'],
            "settings": data[k]['properties']['settings']['value']
            } for k in data]       
  
    def add_site(self, domain, name=None, description=None, site_family=None,
                 return_id=False, return_tracking_code=False):
        """Add new website to tracking roster

        :param domain: full url icluding protocol
        :type domain: str
        :param name: name of site, defaults to None
        :type name: str, optional
        :param description: short description of site, defaults to None
        :type description: str, optional
        :param site_family: site family for UI sorting, defaults to None
        :type site_family: str, optional
        :param return_id: Lookup and return newly created siteid, defaults to False
        :type return_id: bool, optional
        :param return_tracking_code: Return full tracking code, defaults to False
        :type return_tracking_code: bool, optional
        :return: tracking code, siteid, or None
        :rtype: str or None
        """
        r = self._api('POST', owa_do='sites', owa_domain=domain, owa_name=name,
                      owa_description=description, owa_site_family=site_family)
        
        if not (return_id or return_tracking_code):
            return r
        
        site_id = self.get_siteid(domain)
        if return_tracking_code:
            return self.get_tracking_code(site_id)
        return site_id

    def get_tracking_code(self, site_id):
        """Return tracking code

        :param site_id: site id to insert into tracking code
        :type site_id: str
        :return: tracking code to embed in html
        :rtype: str
        """
        return config.tracking_code.replace(
            '{url}', self._base_url).replace('{site_id}', site_id).strip()
       
    def get_siteid(self, name_or_url):
        """Return siteId by name or url

        :param name_or_url: name or url of site to lookup
        :type name_or_url: str
        :return: siteid
        :rtype: str or None
        """
        site = [x['id'] for x in self.get_sites()
                if x['name']==name_or_url or x['domain']==name_or_url]
        if site:
            return site[0]
    
    def delete_site(self, siteId):
        """Delete site

        :param siteId: site id to delete from tracking
        :type siteId: str
        :return: None
        :rtype: None
        """
        return self._api('DELETE', owa_do='sites', owa_siteId=siteId)
    
    def get_users(self):
        """Get all users

        :return: List of users and their roles
        :rtype: list
        """
        return self._api('GET', owa_do='users')

    def add_user(self, user_id, email=None, real_name=None, role='admin'):
        """Add New User

        :param user_id: a new unique user id
        :type user_id: str
        :param email: full email address, defaults to None
        :type email: str, optional
        :param real_name: full name, defaults to None
        :type real_name: str, optional
        :param role: role - must be admin?, defaults to 'admin'
        :type role: str, optional
        :return: None
        :rtype: None
        """
        return self._api('POST', owa_do='users', owa_email_address=email,
                         owa_real_name=real_name, owa_role=role)
    
    def add_site_user(self, user_id, site_id):
        """Add user to site

        :param user_id: user id to add to site
        :type user_id: str
        :param site_id: site_id to add user to
        :type site_id: str
        :return: None
        :rtype: None
        """
        return self._api('POST', owa_user_id=user_id, owa_site_id=site_id,
                         owa_do='siteUsers')
    
    def delete_user(self, user_id):
        """Delete a user

        :param user_id: user_id to delete
        :type user_id: str
        :return: None
        :rtype: None
        """
        return self._api('DELETE', owa_user_id=user_id)
    
    def get_report(self, **kwargs):
        """Return custom report

        :return: custom report
        :rtype: dict
        """
        return self._api('GET', owa_do='reports', **kwargs)
       
    def get_latest_visits(self, siteId, **kwargs):
        """Return latest visits

        :param siteId: site Id
        :type siteId: str
        :param startDate: a yyyymmdd data string (e.g. 20200415)
        :type startDate: str
        :param endDate: a yyyymmdd data string (e.g. 20200415)
        :type endDate: str        
        :return: list of visits
        :rtype: list
        """
        return self._api('GET', owa_do='reports', owa_siteId=siteId,
                         owa_report_name='latest_visits', **kwargs)
    
    def get_visit(self, sessionId):
        """Return info on visit

        :param sessionId: session Id
        :type sessionId: str
        :return: visit info
        :rtype: list
        """
        return self._api('GET', owa_do='reports',
                         owa_report_name='visit', owa_sessionId=sessionId)
    
    def get_latest_actions(self, siteId, **kwargs):
        """Return latest actions for site

        :param siteId: site id
        :type siteId: str
        :param startDate: a yyyymmdd data string (e.g. 20200415)
        :type startDate: str
        :param endDate: a yyyymmdd data string (e.g. 20200415)
        :type endDate: str
        :return: list of latest actions
        :rtype: list
        """
        return self._api('GET', owa_do='reports', owa_siteId=siteId,
                         owa_report_name='latest_actions', **kwargs)
    
    def get_clickstream(self, sessionId):
        """Return clickstream of a specific session
        (time ordered list of pages viewed)

        :param sessionId: sessionId to get stream for
        :type sessionId: str
        :return: list of clicks
        :rtype: list
        """
        return self._api('GET', owa_do='reports', owa_report_name='clickstream',
                         owa_sessionId=sessionId)
    
    def get_clicks(self, page_url, document_id=None):
        """Return clicks from page

        :param page_url: full url of page
        :type page_url: str
        :param document_id: document_id?, defaults to None
        :type document_id: str, optional
        :return: List of clicks
        :rtype: list
        """
        return self._api('GET', owa_do='reports', owa_report_name='clicks',
                         owa_pageUrl=page_url, owa_document_id=document_id)    
 
