
#----Import Statements-------------
import psycopg2
from pymongo import MongoClient, ReadPreference
from bson.objectid import ObjectId
import datetime
import time
import ast
import json
import collections
from collections import defaultdict
import csv
import re
from mongoengine import *
from mongo_orm_polygon_demand_supply import *
#--------------------


#-----------establishing psql and mongo connections for getting in data----------
polygons_conn=psycopg2.connect("dbname=housing_analytics host=127.0.0.1 port=5434 user=dsl_readonly password=dsl")
analytics_db = MongoClient('mongodb://dsl_read:dsl@localhost:3338/analytics',read_preference = ReadPreference.SECONDARY).analytics
flats_conn=psycopg2.connect("dbname=housing_analytics host=127.0.0.1 port=5434 user=dsl_readonly password=dsl")
#------------------------------


#-------------- psql queries-----------------
polygons_hierarchy_query = polygons_conn.cursor()
polygons_name_query = polygons_conn.cursor()
rent_flats_query = flats_conn.cursor()
buy_flats_query = flats_conn.cursor()

polygons_hierarchy_query.execute("SELECT polygon_id,parent_polygon_id,intersecting_area FROM polygon_hierarchy;")
polygons_name_query.execute("SELECT uuid,name,feature_type FROM polygons")
rent_flats_query.execute("SELECT id,unnest(polygons) from rent_flats where status=2")
buy_flats_query.execute("SELECT id,unnest(polygons) from buy_flats where status_id=2")
#--------------------------------------


#------------processing psql fetched data, maintain polygon name, feature_type 
#----and parent map, supply for polygons--------------
polygons_name_data = polygons_name_query.fetchall()
polygons_hierarchy_data = polygons_hierarchy_query.fetchall()
rent_flats_data = rent_flats_query.fetchall()
buy_flats_data = buy_flats_query.fetchall()

polygon_parent_map = {}
polygon_name_map = {}
polygon_feature_type_map = {}

for i in polygons_name_data:
	if i[0] and i[1] and i[2]:
		polygon_name_map[i[0]] = i[1]
		polygon_feature_type_map[i[0]] = i[2]

for i in polygons_hierarchy_data:
	if i[0] and i[1] and i[2]:
		if i[0] in polygon_parent_map:
			if polygon_parent_map[i[0]][1]<i[2]:
				polygon_parent_map[i[0]]=[i[1],i[2]]
		else:
			polygon_parent_map[i[0]]=[i[1],i[2]]

bad_polys_in_parent_map = [p for p in polygon_parent_map if p not in polygon_feature_type_map]
bad_polys_in_parent_map.extend([p for p in polygon_parent_map if p not in polygon_name_map])
bad_polys_in_parent_map = list(set(bad_polys_in_parent_map))
for bp in bad_polys_in_parent_map:
	polygon_parent_map.pop(bp)

polygon_rent_flat_list = defaultdict(lambda:{},{})
for i in rent_flats_data:
	if i[0] and i[1] and i[1] in polygon_parent_map:
		polygon_rent_flat_list[i[1]][i[0]]=1
		polygon_rent_flat_list[polygon_parent_map[i[1]][0]][i[0]]=1

polygon_buy_flat_list = defaultdict(lambda:{},{})
for i in buy_flats_data:
	if i[0] and i[1] and i[1] in polygon_parent_map:
		polygon_buy_flat_list[i[1]][i[0]]=1
		polygon_buy_flat_list[polygon_parent_map[i[1]][0]][i[0]]=1		


polygons_name_data = None
polygons_hierarchy_data = None
rent_flats_data = None
buy_flats_data = None
#----------------------------------------------------------------------


polygon_users = defaultdict(lambda:defaultdict(lambda:defaultdict()))
polygon_leads = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:defaultdict())))
polygon_total_leads = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:defaultdict())))

y = datetime.datetime.now().date() - datetime.timedelta(days = 1)
t = datetime.datetime.now().date() - datetime.timedelta(days = 0)
print y.day,y.month,y.year
ts_y =  int(time.mktime(y.timetuple())*1000)
ts_t =  int(time.mktime(t.timetuple())*1000)
yutcd = datetime.datetime.utcfromtimestamp(ts_y/1000)
tutcd = datetime.datetime.utcfromtimestamp(ts_t/1000)

yutcoid = ObjectId.from_datetime(yutcd) 
tutcoid = ObjectId.from_datetime(tutcd)



data_filters_rent = analytics_db['Filters_rent'].find({'_id':{'$gte':yutcoid,'$lte':tutcoid}},{'uid':1,'action':1,'polygon_id':1, 'timeStamp':1})
ticker=0
for obj in data_filters_rent:
	ticker+=1
	if 'uid' in obj and 'action' in obj and 'polygon_id' in obj and 'timeStamp' in obj:
		if obj['action'] in ['locality','locality_home_page','search_click']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
				polygon_users['rent'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp']))
				polygon_users['rent'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
del data_filters_rent		

data_infowindows_rent = analytics_db['Infowindow_rent'].find({'_id':{'$gte':yutcoid,'$lte':tutcoid}},{'uid':1,'action':1,'polygon_id':1, 'timeStamp':1})
ticker = 0
for obj in data_infowindows_rent:
	ticker+=1
	if 'uid' in obj and 'action' in obj and 'polygon_id' in obj and 'timeStamp' in obj:
		if obj['action'] in ['opened from map','opened from list']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
				polygon_users['rent'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp'])) 
				polygon_users['rent'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
del data_infowindows_rent

data_ocrf_rent = analytics_db['Form'].find({'_id':{'$gte':yutcoid,'$lte':tutcoid}, 'service':'rent'} ,{'uid':1,'action':1,'polygon_id':1, 'device':1, 'timeStamp':1})
ticker = 0
for obj in data_ocrf_rent:
	ticker+=1
	if 'uid' in obj and 'action' in obj and 'polygon_id' in obj and 'device' in obj and 'timeStamp' in obj:
		if obj['action'] in ['open_crf','filled_crf', 'submitted_crf'] and 'desktop' in obj['device']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
					polygon_leads['rent']['desktop'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp'])) 
					polygon_leads['rent']['desktop'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
					polygon_total_leads['rent']['desktop'][obj['polygon_id']][str(int(obj['timeStamp']))]=1 
					polygon_total_leads['rent']['desktop'][polygon_parent_map[obj['polygon_id']][0]][str(int(obj['timeStamp']))]=1
		if obj['action'] in ['call','filled_crf'] and 'mobile' in obj['device']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
					polygon_leads['rent']['mobile_web'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp'])) 
					polygon_leads['rent']['mobile_web'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
					polygon_total_leads['rent']['mobile_web'][obj['polygon_id']][str(int(obj['timeStamp']))]=1
					polygon_total_leads['rent']['mobile_web'][polygon_parent_map[obj['polygon_id']][0]][str(int(obj['timeStamp']))]=1
del data_ocrf_rent

data_filters_buy = analytics_db['Filters_buy'].find({'_id':{'$gte':yutcoid,'$lte':tutcoid}},{'uid':1,'action':1,'polygon_id':1, 'timeStamp':1})
ticker=0
for obj in data_filters_buy:
	ticker+=1
	if 'uid' in obj and 'action' in obj and 'polygon_id' in obj and 'timeStamp' in obj:
		if obj['action'] in ['locality','locality_home_page','search_click']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
				polygon_users['buy'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp']))
				polygon_users['buy'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
del data_filters_buy


data_infowindows_buy = analytics_db['Infowindow_buy'].find({'_id':{'$gte':yutcoid,'$lte':tutcoid}},{'uid':1,'action':1,'polygon_id':1, 'timeStamp':1})
ticker = 0
for obj in data_infowindows_buy:
	ticker+=1
	if 'uid' in obj and 'action' in obj and 'polygon_id' in obj and 'timeStamp' in obj:
		if obj['action'] in ['opened from map','opened from list']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
					polygon_users['buy'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp'])) 
					polygon_users['buy'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
del data_infowindows_buy


data_ocrf_buy = analytics_db['Form'].find({'_id':{'$gte':yutcoid,'$lte':tutcoid}, 'service':'buy'} ,{'uid':1,'action':1,'polygon_id':1, 'device':1, 'timeStamp':1})
ticker = 0
for obj in data_ocrf_buy:
	ticker+=1
	if 'uid' in obj and 'action' in obj and 'polygon_id' in obj and 'device' in obj and 'timeStamp' in obj:
		if obj['action'] in ['open_crf','filled_crf', 'submitted_crf'] and 'desktop' in obj['device']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
					polygon_leads['buy']['desktop'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp'])) 
					polygon_leads['buy']['desktop'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
					polygon_total_leads['buy']['desktop'][obj['polygon_id']][str(int(obj['timeStamp']))]=1
					polygon_total_leads['buy']['desktop'][polygon_parent_map[obj['polygon_id']][0]][str(int(obj['timeStamp']))]=1
		if obj['action'] in ['call','filled_crf'] and 'mobile' in obj['device']:
			if obj['uid']!=None and type(obj['polygon_id']) is not dict and str(obj['polygon_id'])!='' and obj['polygon_id'] in polygon_parent_map and obj['timeStamp']:
					polygon_leads['buy']['mobile_web'][obj['polygon_id']][obj['uid']]=str(int(obj['timeStamp'])) 
					polygon_leads['buy']['mobile_web'][polygon_parent_map[obj['polygon_id']][0]][obj['uid']]=str(int(obj['timeStamp']))
					polygon_total_leads['buy']['mobile_web'][obj['polygon_id']][str(int(obj['timeStamp']))]=1
					polygon_total_leads['buy']['mobile_web'][polygon_parent_map[obj['polygon_id']][0]][str(int(obj['timeStamp']))]=1
del data_ocrf_buy
	

# for key,value in polygons_map.iteritems():
# 	print type(key),key
for i in range(9):
	for key,value in polygon_parent_map.iteritems():
		polygon_rent_flat_list[value[0]].update(polygon_rent_flat_list[key]) 
		polygon_buy_flat_list[value[0]].update(polygon_buy_flat_list[key]) 
		polygon_users['rent'][value[0]].update(polygon_users['rent'][key]) 
		polygon_leads['rent']['desktop'][value[0]].update(polygon_leads['rent']['desktop'][key])
		polygon_leads['rent']['mobile_web'][value[0]].update(polygon_leads['rent']['mobile_web'][key])
		polygon_total_leads['rent']['desktop'][value[0]].update(polygon_total_leads['rent']['desktop'][key])
		polygon_total_leads['rent']['mobile_web'][value[0]].update(polygon_total_leads['rent']['mobile_web'][key])
		polygon_users['buy'][value[0]].update(polygon_users['buy'][key]) 
		polygon_leads['buy']['desktop'][value[0]].update(polygon_leads['buy']['desktop'][key])
		polygon_leads['buy']['mobile_web'][value[0]].update(polygon_leads['buy']['mobile_web'][key])
		polygon_total_leads['buy']['desktop'][value[0]].update(polygon_total_leads['buy']['desktop'][key])
		polygon_total_leads['buy']['mobile_web'][value[0]].update(polygon_total_leads['buy']['mobile_web'][key])


connect('vasu')




for poly_ds_doc in polygon_demand_supply_data.objects():
	
	temp=None
	temp = {uid:ts for uid,ts in poly_ds_doc.rent_service_data.unique_uids.iteritems() if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)}
	temp.update(polygon_users['rent'][poly_ds_doc.polygon_uuid])
	poly_ds_doc.rent_service_data.unique_uids = temp
	poly_ds_doc.rent_service_data.unique_uids_count = len(temp)
	temp=None
	temp = {uid:ts for uid,ts in poly_ds_doc.buy_service_data.unique_uids.iteritems() if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)}
	temp.update(polygon_users['buy'][poly_ds_doc.polygon_uuid])
	poly_ds_doc.buy_service_data.unique_uids = temp
	poly_ds_doc.buy_service_data.unique_uids_count = len(temp)

	
	temp=None
	temp = {uid:ts for uid,ts in poly_ds_doc.rent_service_data.unique_desktop_ocrf_uids.iteritems() if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)}
	temp.update(polygon_leads['rent']['desktop'][poly_ds_doc.polygon_uuid])
	poly_ds_doc.rent_service_data.unique_desktop_ocrf_uids = temp
	poly_ds_doc.rent_service_data.unique_desktop_ocrf_uids_count = len(temp)
	temp=None
	temp = {uid:ts for uid,ts in poly_ds_doc.buy_service_data.unique_desktop_ocrf_uids.iteritems() if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)}
	temp.update(polygon_leads['buy']['desktop'][poly_ds_doc.polygon_uuid])
	poly_ds_doc.buy_service_data.unique_desktop_ocrf_uids = temp
	poly_ds_doc.buy_service_data.unique_desktop_ocrf_uids_count = len(temp)
		
	
	temp=None
	temp = {uid:ts for uid,ts in poly_ds_doc.rent_service_data.unique_mobileweb_call_fcrf_uids.iteritems() if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)}
	temp.update(polygon_leads['rent']['mobile_web'][poly_ds_doc][polygon_uuid])
	poly_ds_doc.rent_service_data.unique_mobileweb_call_fcrf_uids = temp
	poly_ds_doc.rent_service_data.unique_mobileweb_call_fcrf_uids_count = len(temp)
	temp=None
	temp = {uid:ts for uid,ts in poly_ds_doc.buy_service_data.unique_mobileweb_call_fcrf_uids.iteritems() if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)}
	temp.update(polygon_leads['buy']['mobile_web'][poly_ds_doc][polygon_uuid])
	poly_ds_doc.buy_service_data.unique_mobileweb_call_fcrf_uids = temp
	poly_ds_doc.buy_service_data.unique_mobileweb_call_fcrf_uids_count = len(temp)
	
	
	temp=None
	temp = [ts for ts in poly_ds_doc.rent_service_data.total_desktop_ocrf_timestamps if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)]
	temp.extend(polygon_total_leads['rent']['desktop'][poly_ds_doc.polygon_uuid].keys())
	poly_ds_doc.rent_service_data.total_desktop_ocrf_timestamps = temp
	poly_ds_doc.rent_service_data.total_desktop_ocrf_timestamps_count = len(temp)
	temp=None
	temp = [ts for ts in poly_ds_doc.buy_service_data.total_desktop_ocrf_timestamps if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)]
	temp.extend(polygon_total_leads['buy']['desktop'][poly_ds_doc.polygon_uuid].keys())
	poly_ds_doc.buy_service_data.total_desktop_ocrf_timestamps = temp
	poly_ds_doc.buy_service_data.total_desktop_ocrf_timestamps_count = len(temp)
	
	
	temp=None
	temp = [ts for ts in poly_ds_doc.rent_service_data.total_mobileweb_call_fcrf_timestamps if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)]
	temp.extend(polygon_total_leads['rent']['desktop'][poly_ds_doc.polygon_uuid].keys())
	poly_ds_doc.rent_service_data.total_mobileweb_call_fcrf_timestamps = temp
	poly_ds_doc.rent_service_data.total_mobileweb_call_fcrf_timestamps_count = len(temp)
	temp=None
	temp = [ts for ts in poly_ds_doc.buy_service_data.total_mobileweb_call_fcrf_timestamps if datetime.datetime.fromtimestamp(int(ts)/1000).date()>datetime.datetime.now().date()-datetime.timedelta(days=31)]
	temp.extend(polygon_total_leads['buy']['desktop'][poly_ds_doc.polygon_uuid].keys())
	poly_ds_doc.buy_service_data.total_mobileweb_call_fcrf_timestamps = temp
	poly_ds_doc.buy_service_data.total_mobileweb_call_fcrf_timestamps_count = len(temp)

	poly_ds_doc.save()