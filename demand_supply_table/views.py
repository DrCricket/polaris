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

def leads(conversions,count):
	try:
		return round(conversions/float(count),2)
	except ZeroDivisionError:
		return 0


def non_granular(request_type,service_type,id=id):
	data=[]
	n = 0
	polys = []
	if request_type == "getCities":
		polys = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")[:200]	
		n = 200
	elif request_type == "getLocalities":
		polys = polygon_demand_supply_data.objects(parent_polygon_uuid=id).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
		n = 100
	elif request_type == "getSublocalities":
		polys = polygon_demand_supply_data.objects(parent_polygon_uuid=id).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
		n = 100
	if polys:
		for p in polys[:n]:
			data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
	return HttpResponse(json.dumps(data), content_type="application/json")




@csrf_exempt
def ds_table_app(request):

	if request.is_ajax() and request.GET:
		
		if request.GET['name']=='getCities':
			return non_granular(request.GET['name'],request.GET['service'],id=None)
		
		elif request.GET['name']=='getLocalities':
			return non_granular(request.GET['name'],request.GET['service'],id=request.GET['city_id'])

		elif request.GET['name']=='getSublocalities':
			return non_granular(request.GET['name'],request.GET['service'],id=request.GET['locality_id'])

		elif request.GET['name']=='ds_data_granular_to_sublocality':
			print 'this is GET request for getting ds data granular to sublocalities ',request.GET
			
			data=[]

			service_type = request.GET['service']
			var_city = request.GET['city']
			var_locality = request.GET['locality']
			var_sublocality = request.GET['sublocality']


			if var_city == "0":
				cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
			else:
				cities = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
			
			if cities:
				c_= 100 if var_city == "0" else 1
				
				for c in cities[:c_]:

					if var_locality == "0":
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					else:
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid, polygon_uuid=request.GET['locality']).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					
					if localities:
						l_ = 100 if var_locality == "0" else 1

						for l in localities[:l_]:
							

							if var_sublocality == "0":
								sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
							else:
								sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid, polygon_uuid=request.GET['sublocality']).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
							
							if sublocalities:
								sb_ = 100 if var_sublocality == "0" else 1

								for s in sublocalities[:sb_]:
									
									if service_type == "rent":

										ds_gap = s.rent_service_data.unique_uids_count - s.rent_service_data.polygon_current_live_listings_count
										conversions = int(s.rent_service_data.unique_desktop_ocrf_count + 1.67*s.rent_service_data.unique_mobileweb_call_fcrf_count)
										leads_per_user = leads(conversions,s.rent_service_data.unique_uids_count)
										de = s.rent_service_data.unique_uids_count
										sp = s.rent_service_data.polygon_current_live_listings_count

									else:

										ds_gap = s.buy_service_data.unique_uids_count - s.buy_service_data.polygon_current_live_listings_count
										conversions = int(s.buy_service_data.unique_desktop_ocrf_count + 1.67*s.buy_service_data.unique_mobileweb_call_fcrf_count)
										leads_per_user = leads(conversions,s.buy_service_data.unique_uids_count)
										de = s.buy_service_data.unique_uids_count
										sp = s.buy_service_data.polygon_current_live_listings_count
									
									data.append({
										'city' : c.polygon_name,
										'locality' : l.polygon_name,
										'sublocality' : s.polygon_name,
										'demand' : de,
										'supply' : sp,
										'ds_gap' : ds_gap,
										'conversions' : conversions,
										'leads_per_user' : leads_per_user
										})
							else:

								temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
								temp_pds_obj = temp_pds_obj[0]

								if service_type == "rent":

									ds_gap = temp_pds_obj.rent_service_data.unique_uids_count - temp_pds_obj.rent_service_data.polygon_current_live_listings_count
									conversions = int(temp_pds_obj.rent_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.rent_service_data.unique_mobileweb_call_fcrf_count)
									leads_per_user = leads(conversions,temp_pds_obj.rent_service_data.unique_uids_count)
									de = temp_pds_obj.rent_service_data.unique_uids_count
									sp = temp_pds_obj.rent_service_data.polygon_current_live_listings_count
								
								else:

									ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
									conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
									leads_per_user = leads(conversions,temp_pds_obj.buy_service_data.unique_uids_count)
									de = temp_pds_obj.buy_service_data.unique_uids_count
									sp = temp_pds_obj.buy_service_data.polygon_current_live_listings_count

								
								data.append({
									'city' : c.polygon_name,
									'locality' : temp_pds_obj.polygon_name,
									'sublocality' : 'None',
									'demand' : de,
									'supply' : sp,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
					else:
						temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
						temp_pds_obj = temp_pds_obj[0]

						if service_type == "rent":
							ds_gap = temp_pds_obj.rent_service_data.unique_uids_count - temp_pds_obj.rent_service_data.polygon_current_live_listings_count
							conversions = int(temp_pds_obj.rent_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.rent_service_data.unique_mobileweb_call_fcrf_count)
							leads_per_user = leads(conversions,temp_pds_obj.rent_service_data.unique_uids_count)
							de = temp_pds_obj.rent_service_data.unique_uids_count
							sp = temp_pds_obj.rent_service_data.polygon_current_live_listings_count
						else:
							ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
							conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
							leads_per_user = leads(conversions,temp_pds_obj.buy_service_data.unique_uids_count)
							de = temp_pds_obj.buy_service_data.unique_uids_count
							sp = temp_pds_obj.buy_service_data.polygon_current_live_listings_count


						data.append({
							'city' : temp_pds_obj.polygon_name,
							'locality' : 'None',
							'sublocality' : 'None',
							'demand' : de,
							'supply' : sp,
							'ds_gap' : ds_gap,
							'conversions' : conversions,
							'leads_per_user' : leads_per_user
							})
			else:
				pass
		
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		elif request.GET['name']=='ds_data_granular_to_locality':
			print 'this is GET request for getting ds data granular to localities ',request.GET
			
			data = []
			service_type = request.GET['service']
			var_city = request.GET['city']
			var_locality = request.GET['locality']

			if var_city == "0":
				cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
			else:
				cities = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=var_city).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")

				
			if cities:

				c_ = 100 if var_city == "0" else 1

				for c in cities[:c_]:
					if var_locality == "0":
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
					else:
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid,polygon_uuid=var_locality).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")


					if localities:
						l_ = 100 if var_locality == "0" else 1

						for l in localities[:l_]:
							
							if service_type == "rent":
								ds_gap = l.rent_service_data.unique_uids_count - l.rent_service_data.polygon_current_live_listings_count
								conversions = int(l.rent_service_data.unique_desktop_ocrf_count + 1.67*l.rent_service_data.unique_mobileweb_call_fcrf_count)
								leads_per_user = leads(conversions,l.rent_service_data.unique_uids_count)
								de = l.rent_service_data.unique_uids_count
								sp = l.rent_service_data.polygon_current_live_listings_count

							else:
								ds_gap = l.buy_service_data.unique_uids_count - l.buy_service_data.polygon_current_live_listings_count
								conversions = int(l.buy_service_data.unique_desktop_ocrf_count + 1.67*l.buy_service_data.unique_mobileweb_call_fcrf_count)
								leads_per_user = leads(conversions,l.buy_service_data.unique_uids_count)
								de = l.buy_service_data.unique_uids_count
								sp = l.buy_service_data.polygon_current_live_listings_count

							data.append({
								'city' : c.polygon_name,
								'locality' : l.polygon_name,
								'demand' : de,
								'supply' : sp,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:

						temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
						temp_pds_obj = temp_pds_obj[0]
						ds_gap = temp_pds_obj.rent_service_data.unique_uids_count - temp_pds_obj.rent_service_data.polygon_current_live_listings_count
						conversions = int(temp_pds_obj.rent_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.rent_service_data.unique_mobileweb_call_fcrf_count)
						leads_per_user = leads(conversions,temp_pds_obj.rent_service_data.unique_uids_count)

						data.append({
							'city' : temp_pds_obj.polygon_name,
							'locality' : 'None',
							'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
							'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
							'ds_gap' : ds_gap,
							'conversions' : conversions,
							'leads_per_user' : leads_per_user
							})
			else:
				pass
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		elif request.GET['name']=='ds_data_granular_to_city':
			print 'this is GET request for getting ds data granular to cities ',request.GET
			
			data=[]
			var_city = request.GET['city']
			service_type = request.GET['service']

			if var_city=='0':
				cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name", service_type+"_service_data")
			else:
				cities = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=var_city).order_by("-"+service_type+"_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name", service_type+"_service_data")

			if cities:
				c_ = 100 if var_city == "0" else 1
				
				for c in cities[:c_]:
					
					if service_type == "rent":
						ds_gap = c.rent_service_data.unique_uids_count - c.rent_service_data.polygon_current_live_listings_count
						conversions = int(c.rent_service_data.unique_desktop_ocrf_count + 1.67*c.rent_service_data.unique_mobileweb_call_fcrf_count)
						leads_per_user = leads(conversions,c.rent_service_data.unique_uids_count)
						de = c.rent_service_data.unique_uids_count
						sp = c.rent_service_data.polygon_current_live_listings_count

					else:
						ds_gap = c.buy_service_data.unique_uids_count - c.buy_service_data.polygon_current_live_listings_count
						conversions = int(c.buy_service_data.unique_desktop_ocrf_count + 1.67*c.buy_service_data.unique_mobileweb_call_fcrf_count)
						leads_per_user = leads(conversions,c.buy_service_data.unique_uids_count)
						de = c.buy_service_data.unique_uids_count
						sp = c.buy_service_data.polygon_current_live_listings_count

					data.append({
						'city' : c.polygon_name,
						'demand' : de,
						'supply' : sp,
						'ds_gap' : ds_gap,
						'conversions' : conversions,
						'leads_per_user' : leads_per_user
						})
			else:
				pass
			
			return HttpResponse(json.dumps(data), content_type="application/json")
	

		elif request.GET['name']=='export_ds_data_granular_to_sublocality':
			print 'this is GET request for exporting ds data granular to sublocalities ',request.GET
			
			data=[]
			if request.GET['service']=='rent':

				if request.GET['city']=='0' and request.GET['locality']=='0' and request.GET['sublocality']=='0':
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if cities:
						c_ticker=0
						for c in cities:
							c_ticker+=1
							print 'city ticker ', c_ticker
							# print c.to_json()
							localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
							if localities:
								l_ticker=0
								for l in localities:
									l_ticker+=1
									print 'locality ticker ', l_ticker
									# print l.to_json()
									sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
									if sublocalities:
										s_ticker=0
										for s in sublocalities:
											s_ticker+=1
											print 'sublocality ticker ', s_ticker
											# print s.to_json()
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
												'leads_per_user' : leads_per_user
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
											'leads_per_user' : leads_per_user
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
									'locality' : 'None',
									'sublocality' : 'None',
									'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
									'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']=='0' and request.GET['sublocality']=='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
						if localities:
							l_ticker=0
							for l in localities:
								l_ticker+=1
								print 'locality ticker ', l_ticker
								# print l.to_json()
								sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
								if sublocalities:
									s_ticker=0
									for s in sublocalities:
										s_ticker+=1
										print 'sublocality ticker ', s_ticker
										# print s.to_json()
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
											'leads_per_user' : leads_per_user
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
										'leads_per_user' : leads_per_user
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
								'locality' : 'None',
								'sublocality' : 'None',
								'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
								'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']!='0' and request.GET['sublocality']=='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						locality = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid, polygon_uuid=request.GET['locality']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
						if locality:
							l_ticker=0
							l=locality[0]
							l_ticker+=1
							print 'locality ticker ', l_ticker
							# print l.to_json()
							sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
							if sublocalities:
								s_ticker=0
								for s in sublocalities:
									s_ticker+=1
									print 'sublocality ticker ', s_ticker
									# print s.to_json()
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
										'leads_per_user' : leads_per_user
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
									'leads_per_user' : leads_per_user
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
								'locality' : 'None',
								'sublocality' : 'None',
								'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
								'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass
			
				
				elif request.GET['city']!='0' and request.GET['locality']!='0' and request.GET['sublocality']!='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						locality = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid, polygon_uuid=request.GET['locality']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
						if locality:
							l_ticker=0
							l=locality[0]
							l_ticker+=1
							print 'locality ticker ', l_ticker
							# print l.to_json()
							sublocality = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid, polygon_uuid=request.GET['sublocality']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
							if sublocality:
								s_ticker=0
								s=sublocality[0]
								s_ticker+=1
								print 'sublocality ticker ', s_ticker
								# print s.to_json()
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
									'leads_per_user' : leads_per_user
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
									'leads_per_user' : leads_per_user
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
								'locality' : 'None',
								'sublocality' : 'None',
								'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
								'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass
							
			elif request.GET['service']=='buy':

				if request.GET['city']=='0' and request.GET['locality']=='0' and request.GET['sublocality']=='0':
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if cities:
						c_ticker=0
						for c in cities:
							c_ticker+=1
							print 'city ticker ', c_ticker
							# print c.to_json()
							localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
							if localities:
								l_ticker=0
								for l in localities:
									l_ticker+=1
									print 'locality ticker ', l_ticker
									# print l.to_json()
									sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
									if sublocalities:
										s_ticker=0
										for s in sublocalities:
											s_ticker+=1
											print 'sublocality ticker ', s_ticker
											# print s.to_json()
											ds_gap = s.buy_service_data.unique_uids_count - s.buy_service_data.polygon_current_live_listings_count
											conversions = int(s.buy_service_data.unique_desktop_ocrf_count + 1.67*s.buy_service_data.unique_mobileweb_call_fcrf_count)
											try:
												leads_per_user = round(conversions/float(s.buy_service_data.unique_uids_count),2)
											except ZeroDivisionError:
												leads_per_user = 0

											data.append({
												'city' : c.polygon_name,
												'locality' : l.polygon_name,
												'sublocality' : s.polygon_name,
												'demand' : s.buy_service_data.unique_uids_count,
												'supply' : s.buy_service_data.polygon_current_live_listings_count,
												'ds_gap' : ds_gap,
												'conversions' : conversions,
												'leads_per_user' : leads_per_user
												})
									else:
										temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
										temp_pds_obj = temp_pds_obj[0]
										ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
										conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
										try:
											leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
										except ZeroDivisionError:
											leads_per_user = 0

										data.append({
											'city' : c.polygon_name,
											'locality' : temp_pds_obj.polygon_name,
											'sublocality' : 'None',
											'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
											'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
											'ds_gap' : ds_gap,
											'conversions' : conversions,
											'leads_per_user' : leads_per_user
											})
							else:
								temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
								temp_pds_obj = temp_pds_obj[0]
								ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
								conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : temp_pds_obj.polygon_name,
									'locality' : 'None',
									'sublocality' : 'None',
									'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
									'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']=='0' and request.GET['sublocality']=='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
						if localities:
							l_ticker=0
							for l in localities:
								l_ticker+=1
								print 'locality ticker ', l_ticker
								# print l.to_json()
								sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
								if sublocalities:
									s_ticker=0
									for s in sublocalities:
										s_ticker+=1
										print 'sublocality ticker ', s_ticker
										# print s.to_json()
										ds_gap = s.buy_service_data.unique_uids_count - s.buy_service_data.polygon_current_live_listings_count
										conversions = int(s.buy_service_data.unique_desktop_ocrf_count + 1.67*s.buy_service_data.unique_mobileweb_call_fcrf_count)
										try:
											leads_per_user = round(conversions/float(s.buy_service_data.unique_uids_count),2)
										except ZeroDivisionError:
											leads_per_user = 0

										data.append({
											'city' : c.polygon_name,
											'locality' : l.polygon_name,
											'sublocality' : s.polygon_name,
											'demand' : s.buy_service_data.unique_uids_count,
											'supply' : s.buy_service_data.polygon_current_live_listings_count,
											'ds_gap' : ds_gap,
											'conversions' : conversions,
											'leads_per_user' : leads_per_user
											})
								else:
									temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
									temp_pds_obj = temp_pds_obj[0]
									ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
									conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
									try:
										leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
									except ZeroDivisionError:
										leads_per_user = 0

									data.append({
										'city' : c.polygon_name,
										'locality' : temp_pds_obj.polygon_name,
										'sublocality' : 'None',
										'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
										'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
										'ds_gap' : ds_gap,
										'conversions' : conversions,
										'leads_per_user' : leads_per_user
										})
						else:
							temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							temp_pds_obj = temp_pds_obj[0]
							ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
							conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : temp_pds_obj.polygon_name,
								'locality' : 'None',
								'sublocality' : 'None',
								'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
								'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']!='0' and request.GET['sublocality']=='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						locality = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid, polygon_uuid=request.GET['locality']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
						if locality:
							l_ticker=0
							l=locality[0]
							l_ticker+=1
							print 'locality ticker ', l_ticker
							# print l.to_json()
							sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							if sublocalities:
								s_ticker=0
								for s in sublocalities:
									s_ticker+=1
									print 'sublocality ticker ', s_ticker
									# print s.to_json()
									ds_gap = s.buy_service_data.unique_uids_count - s.buy_service_data.polygon_current_live_listings_count
									conversions = int(s.buy_service_data.unique_desktop_ocrf_count + 1.67*s.buy_service_data.unique_mobileweb_call_fcrf_count)
									try:
										leads_per_user = round(conversions/float(s.buy_service_data.unique_uids_count),2)
									except ZeroDivisionError:
										leads_per_user = 0

									data.append({
										'city' : c.polygon_name,
										'locality' : l.polygon_name,
										'sublocality' : s.polygon_name,
										'demand' : s.buy_service_data.unique_uids_count,
										'supply' : s.buy_service_data.polygon_current_live_listings_count,
										'ds_gap' : ds_gap,
										'conversions' : conversions,
										'leads_per_user' : leads_per_user
										})
							else:
								temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
								temp_pds_obj = temp_pds_obj[0]
								ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
								conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : c.polygon_name,
									'locality' : temp_pds_obj.polygon_name,
									'sublocality' : 'None',
									'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
									'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
						else:
							temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							temp_pds_obj = temp_pds_obj[0]
							ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
							conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : temp_pds_obj.polygon_name,
								'locality' : 'None',
								'sublocality' : 'None',
								'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
								'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass
			
				
				elif request.GET['city']!='0' and request.GET['locality']!='0' and request.GET['sublocality']!='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						locality = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid, polygon_uuid=request.GET['locality']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
						if locality:
							l_ticker=0
							l=locality[0]
							l_ticker+=1
							print 'locality ticker ', l_ticker
							# print l.to_json()
							sublocality = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid, polygon_uuid=request.GET['sublocality']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							if sublocality:
								s_ticker=0
								s=sublocality[0]
								s_ticker+=1
								print 'sublocality ticker ', s_ticker
								# print s.to_json()
								ds_gap = s.buy_service_data.unique_uids_count - s.buy_service_data.polygon_current_live_listings_count
								conversions = int(s.buy_service_data.unique_desktop_ocrf_count + 1.67*s.buy_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(s.buy_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : c.polygon_name,
									'locality' : l.polygon_name,
									'sublocality' : s.polygon_name,
									'demand' : s.buy_service_data.unique_uids_count,
									'supply' : s.buy_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
							else:
								temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=l.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
								temp_pds_obj = temp_pds_obj[0]
								ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
								conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : c.polygon_name,
									'locality' : temp_pds_obj.polygon_name,
									'sublocality' : 'None',
									'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
									'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
						else:
							temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							temp_pds_obj = temp_pds_obj[0]
							ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
							conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : temp_pds_obj.polygon_name,
								'locality' : 'None',
								'sublocality' : 'None',
								'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
								'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		elif request.GET['name']=='export_ds_data_granular_to_locality':
			print 'this is GET request for exporting ds data granular to localities ',request.GET
			
			data=[]
			if request.GET['service']=='rent':

				if request.GET['city']=='0' and request.GET['locality']=='0' :
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if cities:
						c_ticker=0
						for c in cities:
							c_ticker+=1
							print 'city ticker ', c_ticker
							# print c.to_json()
							localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
							if localities:
								l_ticker=0
								for l in localities:
									l_ticker+=1
									print 'locality ticker ', l_ticker
									# print l.to_json()
									ds_gap = l.rent_service_data.unique_uids_count - l.rent_service_data.polygon_current_live_listings_count
									conversions = int(l.rent_service_data.unique_desktop_ocrf_count + 1.67*l.rent_service_data.unique_mobileweb_call_fcrf_count)
									try:
										leads_per_user = round(conversions/float(l.rent_service_data.unique_uids_count),2)
									except ZeroDivisionError:
										leads_per_user = 0

									data.append({
										'city' : c.polygon_name,
										'locality' : l.polygon_name,
										'demand' : l.rent_service_data.unique_uids_count,
										'supply' : l.rent_service_data.polygon_current_live_listings_count,
										'ds_gap' : ds_gap,
										'conversions' : conversions,
										'leads_per_user' : leads_per_user
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
									'locality' : 'None',
									'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
									'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']=='0' :
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
						if localities:
							l_ticker=0
							for l in localities:
								l_ticker+=1
								print 'locality ticker ', l_ticker
								# print l.to_json()
								ds_gap = l.rent_service_data.unique_uids_count - l.rent_service_data.polygon_current_live_listings_count
								conversions = int(l.rent_service_data.unique_desktop_ocrf_count + 1.67*l.rent_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(l.rent_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : c.polygon_name,
									'locality' : l.polygon_name,
									'demand' : l.rent_service_data.unique_uids_count,
									'supply' : l.rent_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
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
								'locality' : 'None',
								'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
								'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']!='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						locality = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid,polygon_uuid=request.GET['locality']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","rent_service_data")
						if locality:
							l_ticker=0
							l=locality[0]
							l_ticker+=1
							print 'locality ticker ', l_ticker
							# print l.to_json()
							ds_gap = l.rent_service_data.unique_uids_count - l.rent_service_data.polygon_current_live_listings_count
							conversions = int(l.rent_service_data.unique_desktop_ocrf_count + 1.67*l.rent_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(l.rent_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : c.polygon_name,
								'locality' : l.polygon_name,
								'demand' : l.rent_service_data.unique_uids_count,
								'supply' : l.rent_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
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
								'locality' : 'None',
								'demand' : temp_pds_obj.rent_service_data.unique_uids_count,
								'supply' : temp_pds_obj.rent_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass
			
			elif request.GET['service']=='buy':

				if request.GET['city']=='0' and request.GET['locality']=='0' :
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if cities:
						c_ticker=0
						for c in cities:
							c_ticker+=1
							print 'city ticker ', c_ticker
							# print c.to_json()
							localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							if localities:
								l_ticker=0
								for l in localities:
									l_ticker+=1
									print 'locality ticker ', l_ticker
									# print l.to_json()
									ds_gap = l.buy_service_data.unique_uids_count - l.buy_service_data.polygon_current_live_listings_count
									conversions = int(l.buy_service_data.unique_desktop_ocrf_count + 1.67*l.buy_service_data.unique_mobileweb_call_fcrf_count)
									try:
										leads_per_user = round(conversions/float(l.buy_service_data.unique_uids_count),2)
									except ZeroDivisionError:
										leads_per_user = 0

									data.append({
										'city' : c.polygon_name,
										'locality' : l.polygon_name,
										'demand' : l.buy_service_data.unique_uids_count,
										'supply' : l.buy_service_data.polygon_current_live_listings_count,
										'ds_gap' : ds_gap,
										'conversions' : conversions,
										'leads_per_user' : leads_per_user
										})
							else:
								temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
								temp_pds_obj = temp_pds_obj[0]
								ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
								conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : temp_pds_obj.polygon_name,
									'locality' : 'None',
									'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
									'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']=='0' :
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
						if localities:
							l_ticker=0
							for l in localities:
								l_ticker+=1
								print 'locality ticker ', l_ticker
								# print l.to_json()
								ds_gap = l.buy_service_data.unique_uids_count - l.buy_service_data.polygon_current_live_listings_count
								conversions = int(l.buy_service_data.unique_desktop_ocrf_count + 1.67*l.buy_service_data.unique_mobileweb_call_fcrf_count)
								try:
									leads_per_user = round(conversions/float(l.buy_service_data.unique_uids_count),2)
								except ZeroDivisionError:
									leads_per_user = 0

								data.append({
									'city' : c.polygon_name,
									'locality' : l.polygon_name,
									'demand' : l.buy_service_data.unique_uids_count,
									'supply' : l.buy_service_data.polygon_current_live_listings_count,
									'ds_gap' : ds_gap,
									'conversions' : conversions,
									'leads_per_user' : leads_per_user
									})
						else:
							temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							temp_pds_obj = temp_pds_obj[0]
							ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
							conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : temp_pds_obj.polygon_name,
								'locality' : 'None',
								'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
								'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass


				elif request.GET['city']!='0' and request.GET['locality']!='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						locality = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid,polygon_uuid=request.GET['locality']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
						if locality:
							l_ticker=0
							l=locality[0]
							l_ticker+=1
							print 'locality ticker ', l_ticker
							# print l.to_json()
							ds_gap = l.buy_service_data.unique_uids_count - l.buy_service_data.polygon_current_live_listings_count
							conversions = int(l.buy_service_data.unique_desktop_ocrf_count + 1.67*l.buy_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(l.buy_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : c.polygon_name,
								'locality' : l.polygon_name,
								'demand' : l.buy_service_data.unique_uids_count,
								'supply' : l.buy_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
						else:
							temp_pds_obj = polygon_demand_supply_data.objects(polygon_uuid=c.polygon_uuid).only("polygon_uuid","polygon_feature_type","polygon_name","buy_service_data")
							temp_pds_obj = temp_pds_obj[0]
							ds_gap = temp_pds_obj.buy_service_data.unique_uids_count - temp_pds_obj.buy_service_data.polygon_current_live_listings_count
							conversions = int(temp_pds_obj.buy_service_data.unique_desktop_ocrf_count + 1.67*temp_pds_obj.buy_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(temp_pds_obj.buy_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : temp_pds_obj.polygon_name,
								'locality' : 'None',
								'demand' : temp_pds_obj.buy_service_data.unique_uids_count,
								'supply' : temp_pds_obj.buy_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass
			
			return HttpResponse(json.dumps(data), content_type="application/json")


		elif request.GET['name']=='export_ds_data_granular_to_city':
			print 'this is GET request for exporting ds data granular to cities ',request.GET
			
			data=[]
			if request.GET['service']=='rent':

				if request.GET['city']=='0':
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name", "rent_service_data")
					if cities:
						c_ticker=0
						for c in cities:
							c_ticker+=1
							print 'city ticker ', c_ticker
							# print c.to_json()
							ds_gap = c.rent_service_data.unique_uids_count - c.rent_service_data.polygon_current_live_listings_count
							conversions = int(c.rent_service_data.unique_desktop_ocrf_count + 1.67*c.rent_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(c.rent_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : c.polygon_name,
								'demand' : c.rent_service_data.unique_uids_count,
								'supply' : c.rent_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass


				elif request.GET['city']!='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-rent_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name", "rent_service_data")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						ds_gap = c.rent_service_data.unique_uids_count - c.rent_service_data.polygon_current_live_listings_count
						conversions = int(c.rent_service_data.unique_desktop_ocrf_count + 1.67*c.rent_service_data.unique_mobileweb_call_fcrf_count)
						try:
							leads_per_user = round(conversions/float(c.rent_service_data.unique_uids_count),2)
						except ZeroDivisionError:
							leads_per_user = 0

						data.append({
							'city' : c.polygon_name,
							'demand' : c.rent_service_data.unique_uids_count,
							'supply' : c.rent_service_data.polygon_current_live_listings_count,
							'ds_gap' : ds_gap,
							'conversions' : conversions,
							'leads_per_user' : leads_per_user
							})
					else:
						pass

			elif request.GET['service']=='buy':

				if request.GET['city']=='0':
					cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name", "buy_service_data")
					if cities:
						c_ticker=0
						for c in cities:
							c_ticker+=1
							print 'city ticker ', c_ticker
							# print c.to_json()
							ds_gap = c.buy_service_data.unique_uids_count - c.buy_service_data.polygon_current_live_listings_count
							conversions = int(c.buy_service_data.unique_desktop_ocrf_count + 1.67*c.buy_service_data.unique_mobileweb_call_fcrf_count)
							try:
								leads_per_user = round(conversions/float(c.buy_service_data.unique_uids_count),2)
							except ZeroDivisionError:
								leads_per_user = 0

							data.append({
								'city' : c.polygon_name,
								'demand' : c.buy_service_data.unique_uids_count,
								'supply' : c.buy_service_data.polygon_current_live_listings_count,
								'ds_gap' : ds_gap,
								'conversions' : conversions,
								'leads_per_user' : leads_per_user
								})
					else:
						pass


				elif request.GET['city']!='0':
					city = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-buy_service_data.polygon_current_live_listings_count").only("polygon_uuid","polygon_feature_type","polygon_name", "buy_service_data")
					if city:
						c_ticker=0
						c=city[0]
						c_ticker+=1
						print 'city ticker ', c_ticker
						# print c.to_json()
						ds_gap = c.buy_service_data.unique_uids_count - c.buy_service_data.polygon_current_live_listings_count
						conversions = int(c.buy_service_data.unique_desktop_ocrf_count + 1.67*c.buy_service_data.unique_mobileweb_call_fcrf_count)
						try:
							leads_per_user = round(conversions/float(c.buy_service_data.unique_uids_count),2)
						except ZeroDivisionError:
							leads_per_user = 0

						data.append({
							'city' : c.polygon_name,
							'demand' : c.buy_service_data.unique_uids_count,
							'supply' : c.buy_service_data.polygon_current_live_listings_count,
							'ds_gap' : ds_gap,
							'conversions' : conversions,
							'leads_per_user' : leads_per_user
							})
					else:
						pass
			
			return HttpResponse(json.dumps(data), content_type="application/json")
	

	return render_to_response('demand_supply_table/index.html', context_instance=RequestContext(request))