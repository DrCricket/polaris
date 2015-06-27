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
			polys = polygon_interrelations.objects(polygon_feature_type=37).order_by('rent_service_data.polygon_current_live_listings_count')
			for p in polys[0:100]:
				data.append({'id':p.polygon_uuid,'name':p.polygon_name})
			# print json.dumps(data)
			return HttpResponse(json.dumps(data), content_type="application/json")
	
	return render_to_response('demand_supply_table/index.html', context_instance=RequestContext(request))