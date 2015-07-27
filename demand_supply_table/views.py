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
		polys = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")[:200]	
		n = 200
	elif request_type == "getLocalities":
		polys = polygon_demand_supply_data.objects(parent_polygon_uuid=id).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")
		n = 100
	elif request_type == "getSublocalities":
		polys = polygon_demand_supply_data.objects(parent_polygon_uuid=id).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")
		n = 100
	if polys:
		for p in polys[:n]:
			data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			
	return HttpResponse(json.dumps(data), content_type="application/json")




def granular_to_city(request,export=False):
	print 'this is GET request for getting ds data granular to cities ',request.GET
			
	data=[]
	var_city = request.GET['city']
	service_type = request.GET['service']

	if var_city=='0':
		cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name", service_type+"_service_data")
	else:
		cities = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=var_city).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name", service_type+"_service_data")

	if cities:
		c_ = 100 if var_city == "0" else 1
		if export == True:
			c_ = len(cities)
		
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






def granular_to_locality(request,export=False):
	print 'this is GET request for getting ds data granular to localities ',request.GET
			
	data = []
	service_type = request.GET['service']
	var_city = request.GET['city']
	var_locality = request.GET['locality']

	if var_city == "0":
		cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")
	else:
		cities = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=var_city).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")

		
	if cities:

		c_ = 100 if var_city == "0" else 1
		if export == True:
			c_ = len(cities)

		for c in cities[:c_]:
			if var_locality == "0":
				localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
			else:
				localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid,polygon_uuid=var_locality).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")


			if localities:
				l_ = 100 if var_locality == "0" else 1
				if export == True:
					l_ = len(localities)

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






def granular_to_sublocality(request,export=False):
	print 'this is GET request for getting ds data granular to sublocalities ',request.GET
			
	data=[]

	service_type = request.GET['service']
	var_city = request.GET['city']
	var_locality = request.GET['locality']
	var_sublocality = request.GET['sublocality']


	if var_city == "0":
		cities = polygon_demand_supply_data.objects(polygon_feature_type=37).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")
	else:
		cities = polygon_demand_supply_data.objects(polygon_feature_type=37, polygon_uuid=request.GET['city']).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")
	
	if cities:
		c_= 100 if var_city == "0" else 1
		
		for c in cities[:c_]:

			if var_locality == "0":
				localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")
			else:
				localities = polygon_demand_supply_data.objects(parent_polygon_uuid=c.polygon_uuid, polygon_uuid=request.GET['locality']).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name")
			
			if localities:
				l_ = 100 if var_locality == "0" else 1

				for l in localities[:l_]:
					

					if var_sublocality == "0":
						sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
					else:
						sublocalities = polygon_demand_supply_data.objects(parent_polygon_uuid=l.polygon_uuid, polygon_uuid=request.GET['sublocality']).order_by("-"+service_type+"_service_data.unique_uids_count").only("polygon_uuid","polygon_feature_type","polygon_name",service_type+"_service_data")
					
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






##############################################################################################################################################################################
@csrf_exempt
def ds_table_app(request):

	if request.is_ajax() and request.GET:

		############################################################ NON GRANULAR OPTIONS ###############################################################################

		if request.GET['name']=='getCities':
			return non_granular(request.GET['name'],request.GET['service'],id=None)
		
		elif request.GET['name']=='getLocalities':
			return non_granular(request.GET['name'],request.GET['service'],id=request.GET['city_id'])

		elif request.GET['name']=='getSublocalities':
			return non_granular(request.GET['name'],request.GET['service'],id=request.GET['locality_id'])


		############################################################ GRANULAR OPTIONS ##################################################################################
		
		elif request.GET['name']=='ds_data_granular_to_sublocality':
			return granular_to_sublocality(request,export=False)


		
		elif request.GET['name']=='ds_data_granular_to_locality':
			return granular_to_locality(request,export=False)


		
		elif request.GET['name']=='ds_data_granular_to_city':
			return granular_to_city(request,export=False)
	

		############################################################# OPTIONS FOR EXPORTING ############################################################################
		

		elif request.GET['name']=='export_ds_data_granular_to_sublocality':
			
			return granular_to_sublocality(request,export=True)


		elif request.GET['name']=='export_ds_data_granular_to_locality':
			
			return granular_to_locality(request,export=True)


		elif request.GET['name']=='export_ds_data_granular_to_city':
			
			return granular_to_city(request,export=True)
	

	return render_to_response('demand_supply_table/index.html', context_instance=RequestContext(request))

