from mongoengine import *

class polygon_interrelations(Document):
	polygon_uuid = StringField(required=True)
	polygon_feature_type = IntField(required=True)
	polygon_name = StringField(required=True)
	parent_polygon_uuid = StringField(required=True)
	parent_polygon_feature_type = IntField(required=True)
	parent_polygon_name = StringField(required=True)

class demand_supply_data(EmbeddedDocument):
	unique_uids = DictField(required=False)
	unique_uids_count = IntField(required=True, default=0)
	unique_desktop_ocrf_count = IntField(required=True, default=0)
	unique_mobileweb_call_fcrf_count = IntField(required=True, default=0)
	polygon_current_live_listings_count = IntField(required=True, default=0)

class polygon_demand_supply_data(Document):
	rent_service_data = EmbeddedDocumentField(demand_supply_data)
	buy_service_data = EmbeddedDocumentField(demand_supply_data)	
	polygon_uuid = StringField(required=True)
	polygon_feature_type = IntField(required=True)
	polygon_name = StringField(required=True)
	parent_polygon_uuid = StringField(required=True)
	parent_polygon_feature_type = IntField(required=True)
	parent_polygon_name = StringField(required=True)



