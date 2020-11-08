# open-web-analytics-api-wrapper
Python wrapper for self hosted Open Web Analytics data access API

I wrote this to use with my web app scaffolding templating system. My primary use case is exampled below, but the other methods >from the api have been included. Some functions aren't working - anything making a DELETE request returns a 405.

Open Web Analytics API docs: https://github.com/Open-Web-Analytics/Open-Web-Analytics/wiki/REST-API

My Docs: https://amir-almusawi.github.io/owa_wrapper/owa.html


```python
from owa_wrapper import Owa

analytics = Owa()
tracking_code = analytics.add_site('https://www.example.com,
                                   name='Example Site',
                                   description='A short example description',
                                   site_family='example sites',
                                   return_tracking_code=True)

add_analytics_to_project(tracking_code)
'''
