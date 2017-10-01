import webapp2
import datetime
from datetime import datetime
from google.appengine.ext import ndb
import json
import uuid

class Boat(ndb.Model):
    #boat_id = ndb.KeyProperty(required=True)
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()

class Departure_History(ndb.Model):
    departure_date = ndb.DateProperty()
    departed_boat = ndb.StringProperty()

class Slip(ndb.Model):
    id = ndb.StringProperty()
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date_str = ndb.StringProperty()
    #arrival_date = ndb.DateProperty()
    departure_history = ndb.StructuredProperty(Departure_History, repeated = True)

class BoatHandler(webapp2.RequestHandler):
    def post(self):
        boat_data = json.loads(self.request.body)
        new_boat = Boat(#id = str(uuid.uuid1()),
                        name = boat_data['name'],
                        type = boat_data['type'],
                        length = int(boat_data['length']),
                        at_sea = bool(boat_data['at_sea']))
        new_boat.put()
        new_boat.id = new_boat.key.urlsafe()
        new_boat.put()
        boat_dict=new_boat.to_dict()
        boat_dict['self'] = '/boat/' + new_boat.key.urlsafe()
        self.response.set_status(201)
        self.response.headers.add('content-type','application/json')
        self.response.headers.add('location',boat_dict['self'])
        self.response.write(json.dumps(boat_dict))
    def put(self, id = None):
        boat_data = json.loads(self.request.body)
        if id:
            boat = ndb.Key(urlsafe=id).get()
            if boat is None:
               self.response.set_status(404)
            else:
                boat.name = boat_data['name'],
                boat.type = boat_data['type'],
                boat.length = int(boat_data['length']),
                boat.at_sea = bool(boat_data['at_sea'])
                boat_dict = boat.to_dict()
                boat_dict['self'] = "/boat/" + id
                self.response.write(json.dumps(boat_dict))
            self.response.headers.add('content-type','application/json')
    def patch(self, id = None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            if boat is None:
               self.response.set_status(404)
            else:
                boat_patch_data_dict = json.loads(self.request.body)
                boat_dict = boat.to_dict()
                for key, data in boat_patch_data_dict.items():
                    boat_dict[key] = data
                if 'name' in boat_dict:
                    boat.name = boat_dict['name']
                if 'type' in boat_dict:
                    boat.type = boat_dict['type']
                if 'length' in boat_dict:
                    boat.length = boat_dict['length']
                if 'at_sea' in boat_dict:
                    boat.at_sea = boat_dict['at_sea']
                boat.put()
                boat_dict['self'] = '/boat/' + id
                self.response.write(json.dumps(boat_dict))
                self.response.headers.add('content-type','application/json')
                self.response.headers.add('location',boat_dict['self'])
                
    def get(self, id = None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            if boat is None:
               self.response.set_status(404)
            else:
                boat_dict = boat.to_dict()
                boat_dict['self'] = "/boat/" + id
                self.response.write(json.dumps(boat_dict))
        else:
            boat_list = Boat.query().fetch(10)
            self.response.write("[")
            for idx, boat in enumerate(boat_list):
                if idx != 0:
                    self.response.write(",")
                boat_dict = boat.to_dict()
                boat_dict['self'] = '/boat/' + boat.id
                self.response.write(json.dumps(boat_dict))
            self.response.write("]")
        self.response.headers.add('content-type','application/json')
    def delete(self, id = None):
        if id:
            b = ndb.Key(urlsafe=id)
            b.delete()
        self.response.set_status(204)

class SlipHandler(webapp2.RequestHandler):
    def get(self, id = None):
        if id:
            self.response.write('get a specific slip here')
        else:
            slips = Slip.query().fetch(1000)
            slip_list = list()
            for idx, slip in enumerate(slips):
                slip_list.append(slip.to_dict())
            self.response.write(json.dumps(slip_list))
        self.response.headers.add('content-type','application/json')
    def post(self, id = None):
        slip_data = json.loads(self.request.body)
        new_slip = Slip(
            #id = str(uuid.uuid1()),
            number = int(slip_data['number']),
            #current_boat = slip_data['current_boat'],
            #arrival_date_str = slip_data['arrival_date'],
            #arrival_date = datetime.strptime(slip_data['arrival_date'],"%m/%d/%Y"),
            departure_history = [])
        new_slip.put()
        new_slip.id = new_slip.key.urlsafe()
        new_slip.put()
        slip_dict = new_slip.to_dict()
        slip_dict['self']='/slip/' + new_slip.key.urlsafe()
        self.response.write(json.dumps(slip_dict))
        self.response.headers.add('content-type','application/json')
        self.response.headers.add('location',slip_dict['self'])
    
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')
        self.response.write('\n')
        self.response.write(datetime.datetime.now().strftime("%x %X"))

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boat', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/boats', BoatHandler), 
    ('/slip', SlipHandler),
    ('/slip/(.*)', SlipHandler)
], debug=True)
