# Create your views here.
from django.shortcuts import render
from models import *
from django.shortcuts import render_to_response,redirect
from django.shortcuts import render
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
import json
import datetime
import time
from forms import UploadForm
import collections
from collections import defaultdict

@csrf_exempt
def ds_table_app(request):

	if request.is_ajax() and request.GET:
		
		if request.GET['name']=='getCities':
			data=[]
			print 'this is GET request for getting cities data',request.GET
			
			if request.GET['service']=='rent':
				polys = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				if polys:
					for p in polys[0:200]:
						data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			elif request.GET['service']=='buy':
				polys = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				if polys:
					for p in polys[0:200]:
						data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			return HttpResponse(json.dumps(data), content_type="application/json")

		
		if request.GET['name']=='getLocalities':
			data=[]
			print 'this is GET request for getting localities data',request.GET
			
			if request.GET['service']=='rent':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['city_id']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				if polys:
					for p in polys[0:100]:
						data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			elif request.GET['service']=='buy':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['city_id']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				if polys:
					for p in polys[0:100]:
						data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		if request.GET['name']=='getSublocalities':
			data=[]
			print 'this is GET request for getting sublocalities data',request.GET
			
			if request.GET['service']=='rent':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['locality_id']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				if polys:
					for p in polys[0:100]:
						data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			elif request.GET['service']=='buy':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['locality_id']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				if polys:
					for p in polys[0:100]:
						data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		if request.GET['name']=='ds_data_granular_to_sublocality':
			print 'this is GET request for getting ds data granular to sublocalities ',request.GET
			
			data=[]
			if request.GET['service']=='rent':

				if request.GET['city']=='0' and request.GET['locality']=='0' and request.GET['sublocality']=='0':
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if cities:
						c_ticker=0
						for c in cities[0:100]:
							c_ticker+=1
							print 'city ticker ', c_ticker
							print c.to_json()
							localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
							if localities:
								l_ticker=0
								for l in localities[0:100]:
									l_ticker+=1
									print 'locality ticker ', l_ticker
									print l.to_json()
									sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
									if sublocalities:
										s_ticker=0
										for s in sublocalities[0:100]:
											s_ticker+=1
											print 'sublocality ticker ', s_ticker
											print s.to_json()
											ds_gap = s.rent_service_data.unique_uids_count - s.rent_service_data.polygon_current_live_listings_count
											conversions = int(s.rent_service_data.unique_desktop_ocrf_count + 1.67*s.rent_service_data.unique_mobileweb_call_fcrf_count)
											try:
												leads_per_user = round(conversions/float(s.rent_service_data.unique_uids_count),2)
											except ZeroDivisionError:
												leads_per_user = 0

											data.append({
												'city' : c.polygon_name,
												'locality' : l.polygon_name,
												'sublocality' : s.polygon_name,
												'demand' : s.rent_service_data.unique_uids_count,
												'supply' : s.rent_service_data.polygon_current_live_listings_count,
												'ds_gap' : ds_gap,
												'conversions' : conversions,
												'leads_per_user' : round(conversions,2)
												})
									else:
										temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
										temp_pds_obj = temp_pds_obj[0]
										ds_gap = temp_pds_obj.rent_service_data.unique_uids_count - temp_pds_obj.rent_service_data.polygon_current_live_listings_count
										conversions = int(temp_pds_obj.rent_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.rent_service_data.unique_mobileweb_call_fcrf_count)
										try:
											leads_per_user = round(conversions/float(temp_pds_obj.rent_service_data.unique_uids_count),2)
										except ZeroDivisionError:
											leads_per_user = 0

										data.append({
											'city' : c.polygon_name,
											'locality' : temp_pds_obj.polygon_name,
											'sublocality' : 'None',
											'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
											'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
											'ds_gap' : ds_gap,
											'conversions' : conversions,
											'leads_per_user' : round(conversions,2)
											})
							else:
								temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
								temp_pds_obj = temp_pds_obj[0]
								ds_gap = temp_pds_obj.rent_service_data.unique_uids_count - temp_pds_obj.rent_service_data.polygon_current_live_listings_count
								conversions = int(temp_pds_obj.rent_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.rent_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(temp_pds_obj.rent_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : temp_pds_obj.polygon_name,
									'locality' : temp_pds_obj.polygon_name,
									'sublocality' : 'None',
									'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
									'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : round(conversions,2)
									})
					else:
						pass


				if request.GET['city']!='0' and request.GET['locality']=='0' and request.GET['sublocality']=='0':
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if cities:
						c_ticker=0
						for c in cities[0:100]:
							c_ticker+=1
							print 'city ticker ', c_ticker
							print c.to_json()
							localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
							if localities:
								l_ticker=0
								for l in localities[0:100]:
									l_ticker+=1
									print 'locality ticker ', l_ticker
									print l.to_json()
									sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
									if sublocalities:
										s_ticker=0
										for s in sublocalities[0:100]:
											s_ticker+=1
											print 'sublocality ticker ', s_ticker
											print s.to_json()
											ds_gap = s.rent_service_data.unique_uids_count - s.rent_service_data.polygon_current_live_listings_count
											conversions = int(s.rent_service_data.unique_desktop_ocrf_count + 1.67*s.rent_service_data.unique_mobileweb_call_fcrf_count)
											try:
												leads_per_user = round(conversions/float(s.rent_service_data.unique_uids_count),2)
											except ZeroDivisionError:
												leads_per_user = 0

											data.append({
												'city' : c.polygon_name,
												'locality' : l.polygon_name,
												'sublocality' : s.polygon_name,
												'demand' : s.rent_service_data.unique_uids_count,
												'supply' : s.rent_service_data.polygon_current_live_listings_count,
												'ds_gap' : ds_gap,
												'conversions' : conversions,
												'leads_per_user' : round(conversions,2)
												})
									else:
										temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
										temp_pds_obj = temp_pds_obj[0]
										ds_gap = temp_pds_obj.rent_service_data.unique_uids_count - temp_pds_obj.rent_service_data.polygon_current_live_listings_count
										conversions = int(temp_pds_obj.rent_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.rent_service_data.unique_mobileweb_call_fcrf_count)
										try:
											leads_per_user = round(conversions/float(temp_pds_obj.rent_service_data.unique_uids_count),2)
										except ZeroDivisionError:
											leads_per_user = 0

										data.append({
											'city' : c.polygon_name,
											'locality' : temp_pds_obj.polygon_name,
											'sublocality' : 'None',
											'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
											'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
											'ds_gap' : ds_gap,
											'conversions' : conversions,
											'leads_per_user' : round(conversions,2)
											})
							else:
								temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
								temp_pds_obj = temp_pds_obj[0]
								ds_gap = temp_pds_obj.rent_service_data.unique_uids_count - temp_pds_obj.rent_service_data.polygon_current_live_listings_count
								conversions = int(temp_pds_obj.rent_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.rent_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(temp_pds_obj.rent_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : temp_pds_obj.polygon_name,
									'locality' : temp_pds_obj.polygon_name,
									'sublocality' : 'None',
									'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
									'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : round(conversions,2)
									})
					else:
						pass
			
			
			elif request.GET['service']=='buy':

				if request.GET['city']=='0' and request.GET['locality']=='0' and request.GET['sublocality']=='0':
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if cities:
						for c in cities[0:100]:
							localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
							if localities:
								for l in localities[0:100]:
									sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
									if sublocalities:
										for s in sublocalities[0:100]:
											ds_gap = s.buy_service_data.unique_uids_count - s.buy_service_data.polygon_current_live_listings_count
											conversions = int(s.buy_service_data.unique_desktop_ocrf_count + 1.67*s.buy_service_data.unique_mobileweb_call_fcrf_count)
											leads_per_user = round(conversions/float(s.buy_service_data.unique_uids_count),2)
											data.append({
												'city' : c.polygon_name,
												'locality' : l.polygon_name,
												'sublocality' : s.polygon_name,
												'demand' : s.buy_service_data.unique_uids_count,
												'supply' : s.buy_service_data.polygon_current_live_listings_count,
												'ds_gap' : ds_gap,
												'conversions' : conversions,
												'leads_per_user' : round(conversions,2)
												})
									else:
										ds_gap = l.buy_service_data.unique_uids_count - l.buy_service_data.polygon_current_live_listings_count
										conversions = int(l.buy_service_data.unique_desktop_ocrf_count + 1.67*l.buy_service_data.unique_mobileweb_call_fcrf_count)
										leads_per_user = round(conversions/float(l.buy_service_data.unique_uids_count),2)
										data.append({
											'city' : c.polygon_name,
											'locality' : l.polygon_name,
											'sublocality' : 'None',
											'demand' : l.buy_service_data.unique_uids_count,
											'supply' : l.buy_service_data.polygon_current_live_listings_count,
											'ds_gap' : ds_gap,
											'conversions' : conversions,
											'leads_per_user' : round(conversions,2)
											})
							else:
								ds_gap = c.buy_service_data.unique_uids_count - c.buy_service_data.polygon_current_live_listings_count
								conversions = int(c.buy_service_data.unique_desktop_ocrf_count + 1.67*c.buy_service_data.unique_mobileweb_call_fcrf_count)
								leads_per_user = round(conversions/float(c.buy_service_data.unique_uids_count),2)
								data.append({
									'city' : c.polygon_name,
									'locality' : c.polygon_name,
									'sublocality' : 'None',
									'demand' : c.buy_service_data.unique_uids_count,
									'supply' : c.buy_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : round(conversions,2)
									})
					else:
						pass
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		if request.GET['name']=='ds_data_granular_to_locality':
			data=[]
			print 'this is GET request for getting ds data granular to sublocalities ',request.GET
			
			if request.GET['service']=='rent':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['locality_id']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				for p in polys[0:100]:
					data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			elif request.GET['service']=='buy':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['locality_id']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				for p in polys[0:100]:
					data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		if request.GET['name']=='ds_data_granular_to_city':
			data=[]
			print 'this is GET request for getting ds data granular to sublocalities ',request.GET
			
			if request.GET['service']=='rent':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['locality_id']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				for p in polys[0:100]:
					data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			elif request.GET['service']=='buy':
				polys = polygon_demand_supply_data.objects(parent_polygon_uuid=request.GET['locality_id']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
				for p in polys[0:100]:
					data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
			return HttpResponse(json.dumps(data), content_type="application/json")
	
	return render_to_response('demand_supply_table/index.html', context_instance=RequestContext(request))