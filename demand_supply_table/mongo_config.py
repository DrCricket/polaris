from pymongo import *

analytics_con = MongoClient('mongodb://write:write@10.1.10.14:27017/new_analytics', read_preference = ReadPreference.SECONDARY)
analytics_db = 'new_analytics'

trackeasy_con = MongoClient(host = 'localhost', port = 27017)
trackeasy_db = 'vasu'
trackeasy_coll = trackeasy_con[trackeasy_db]['tracking_events_log']
trackeasy_audit_coll = trackeasy_con[trackeasy_db]['tracking_events_audit']
trackeasy_alert_coll = trackeasy_con[trackeasy_db]['tracking_events_alert']
trackeasy_update_coll = trackeasy_con[trackeasy_db]['trackeasy_update_details']