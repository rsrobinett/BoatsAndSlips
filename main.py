import webapp2
import datetime
from datetime import datetime
from google.appengine.ext import ndb
from google.appengine.ext import db
import json


class Boat(ndb.Model):
    name = ndb.StringProperty()
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()


class DepartureHistory(ndb.Model):
    departure_date = ndb.StringProperty()
    departed_boat = ndb.StringProperty()


class Slip(ndb.Model):
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()
    departure_history = ndb.StructuredProperty(DepartureHistory, repeated=True)


class BoatHandler(webapp2.RequestHandler):
    def post(self):
        boat_data = json.loads(self.request.body)
        new_boat = Boat()
        if 'name' in boat_data:
            new_boat.name = boat_data['name']
        if 'type' in boat_data:
            new_boat.type = boat_data['type']
        if 'length' in boat_data:
            new_boat.length = int(boat_data['length'])
        new_boat.at_sea = True
        new_boat.put()
        boat_dict = new_boat.to_dict()
        boat_dict['id'] = new_boat.key.urlsafe()
        boat_dict['self'] = '/boat/' + new_boat.key.urlsafe()
        self.create_boat_dictionary(new_boat, new_boat.key.urlsafe())
        self.response.set_status(201)
        self.response.headers.add('content-type', 'application/json')
        self.response.headers.add('location', boat_dict['self'])
        self.response.write(json.dumps(boat_dict))

    def put(self, id=None):
        boat_data = json.loads(self.request.body)
        if id:
            try:
                boat = ndb.Key(urlsafe=id).get()
            except Exception:
                boat = None
            if boat is None:
                self.response.set_status(404)
                return
            else:
                if 'name' in boat_data:
                    boat.name = boat_data['name']
                else:
                    boat.name = None
                if 'type' in boat_data:
                    boat.type = boat_data['type']
                else:
                    boat.type = None
                if 'length' in boat_data:
                    boat.length = int(boat_data['length'])
                else:
                    boat.length = None
                if not boat.at_sea:
                    self.depart(boat)
                boat_dict = boat.to_dict()
                boat_dict['id'] = boat.key.urlsafe()
                boat_dict['self'] = "/boat/" + boat.key.urlsafe()
                boat.put()
                self.response.set_status(200)
                self.response.write(json.dumps(boat_dict))
                self.response.headers.add('location', boat_dict['self'])
                self.response.headers.add('content-type', 'application/json')
        else:
            self.response.set_status(400)

    def get(self, id=None):
        if id:
            try:
                boat = ndb.Key(urlsafe=id).get()
            except Exception:
                boat = None
            if boat is None:
                self.response.set_status(404)
                return
            else:
                boat_dict = self.create_boat_dictionary(boat, id)
                self.response.write(json.dumps(boat_dict))
        else:
            boats = Boat.query()
            boat_list = list()
            for boat in boats:
                boat_dict = self.create_boat_dictionary(boat, id)
                boat_list.append(boat_dict)
            self.response.write(json.dumps(boat_list))
        self.response.headers.add('content-type', 'application/json')

    def delete(self, id=None):
        if id:
            try:
                boat = ndb.Key(urlsafe=id).get()
            except Exception:
                boat = None
            if boat is None:
                self.response.set_status(404)
                return
            else:
                if not boat.at_sea:
                    self.depart(boat)
                boat.key.delete()
        self.response.set_status(204)

    def patch(self, id=None, slipnumber=None):
        if id:
            try:
                current_boat = ndb.Key(urlsafe=id).get()
            except Exception:
                current_boat = None
            if current_boat is None:
                self.response.set_status(404)
                return
            else:
                boat_patch_data_dict = json.loads(self.request.body)
                current_boat_dict = current_boat.to_dict()
                for key, patch_data in boat_patch_data_dict.items():
                    current_boat_dict[key] = patch_data
                if 'name' in current_boat_dict and 'name' in boat_patch_data_dict:
                    current_boat.name = boat_patch_data_dict['name']
                if 'type' in current_boat_dict and 'type' in boat_patch_data_dict:
                    current_boat.type = boat_patch_data_dict['type']
                if 'length' in current_boat_dict and 'length' in boat_patch_data_dict:
                    current_boat.length = boat_patch_data_dict['length']
                if 'at_sea' in current_boat_dict and 'at_sea' in boat_patch_data_dict:
                    # Boat in a slip and not going to sea
                    if not current_boat.at_sea and (('at_sea' in boat_patch_data_dict and not boat_patch_data_dict['at_sea']) or ('at_sea' not in boat_patch_data_dict)):
                        self.get_slip_url(current_boat, current_boat_dict)
                    # Departure Scenario
                    if (current_boat.at_sea != True and boat_patch_data_dict['at_sea']):
                        self.depart(current_boat)
                    # Arrival Scenario
                    if current_boat.at_sea and not boat_patch_data_dict['at_sea']:
                        slip = ndb.gql("SELECT * FROM Slip WHERE current_boat = NULL").get()
                        if slip is None:
                            self.response.set_status(403)
                            return
                        else:
                            if slip.current_boat is not None:
                                self.response.set_status(403)
                            else:
                                slip.current_boat = current_boat.key.urlsafe()
                                slip.arrival_date = datetime.strftime(datetime.today(), "%m/%d/%Y")
                                slip.put()
                                current_boat.at_sea = False
                                current_boat_dict['slip_url'] = '/slip/' + slip.key.urlsafe()
                    current_boat_dict['id'] = current_boat.key.urlsafe()
                current_boat.put()
                current_boat_dict['self'] = '/boat/' + current_boat.key.urlsafe()
                self.response.write(json.dumps(current_boat_dict))
                self.response.headers.add('content-type', 'application/json')
                self.response.set_status(200)
                self.response.headers.add('location', current_boat_dict['self'])
        else:
            self.response.set_status(400)

    def depart(self, boat):
        if not boat.at_sea:
            slip = Slip.query(Slip.current_boat == boat.key.urlsafe()).get()
            slip.current_boat = None
            slip.arrival_date = None
            departure = DepartureHistory()
            departure.departed_boat = boat.key.urlsafe()
            departure.departure_date = datetime.strftime(datetime.today(), "%m/%d/%Y")
            slip.departure_history.append(departure)
            slip.put()
            boat.at_sea = True
            boat.put()

    def create_boat_dictionary(self, boat, id):
        boat_dict = boat.to_dict()
        if not boat.at_sea:
            self.get_slip_url(boat, boat_dict)
        boat_dict['id'] = id
        boat_dict['self'] = "/boat/" + boat.key.urlsafe()
        return boat_dict

    def get_slip_url(self, boat, boat_dict):
        slip = Slip.query(Slip.current_boat == boat.key.urlsafe()).get()
        boat_dict['slip_url'] = "/slip/" + slip.key.urlsafe()


class SlipHandler(webapp2.RequestHandler):

    def post(self):
        new_slip = Slip(number=self.set_slip_number())
        new_slip.put()
        self.get(new_slip.key.urlsafe())
        self.response.headers.add('location', '/slip/' + new_slip.key.urlsafe())
        self.response.set_status(201)

    def delete(self, id = None):
        if id:
            try:
                slip = ndb.Key(urlsafe=id).get()
            except Exception:
                self.response.set_status(404)
                return
            if slip is None:
                self.response.set_status(404)
                return
            else:
                self.depart_boat(slip)
                slip.key.delete()
            self.response.set_status(204)
        else:
            self.response.set_status(404)

    def put(self, id=None):
        if id:
            try:
                slip = ndb.Key(urlsafe=id).get()
            except Exception:
                self.response.set_status(404)
                return
            if slip is None:
                self.response.set_status(404)
            else:
                self.depart_boat(slip)
                slip.current_boat = None
                slip.arrival_date = None
                slip.departure_history = []
                slip.number = self.set_slip_number()
                slip.put()
                self.get(id)
        else:
            self.response.set_status(400)

    def patch(self, id=None):
        if id:
            try:
                slip = ndb.Key(urlsafe=id).get()
            except Exception:
                self.response.set_status(404)
                return
            if slip is None:
                self.response.set_status(404)
            else:
                slip_patch_data = json.loads(self.request.body)
                slip_dict = slip.to_dict()
                for key, data in slip_patch_data.items():
                    slip_dict[key] = data
                if 'number' in slip_dict:
                    slip_check = Slip.query(Slip.number == slip_dict['number']).get()
                    if slip_check is None:
                        slip.number = slip_dict['number']
                    else:
                        self.response.set_status(400)
                        self.response.headers.add('content-type', 'text/plain')
                        self.response.write("slip number is not available")
                        return
                #if 'current_boat' in slip_dict:
                #    if slip.current_boat is not None:
                #        self.depart_boat(slip)
                #    slip.current_boat = slip_dict['current_boat']
                if 'arrival_date' in slip_dict:
                    slip.arrival_date = slip_dict['arrival_date']
                slip.put()
                slip_dict['self'] = '/slip/' + id
                if slip.current_boat is not None:
                    slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
                self.response.write(json.dumps(slip_dict))
                self.response.headers.add('content-type', 'application/json')
                self.response.headers.add('location', slip_dict['self'])

    def get(self, id=None):
        if id:
            try:
                slip = ndb.Key(urlsafe=id).get()
            except Exception:
                self.response.set_status(404)
                return
            if slip is None:
                self.response.set_status(404)
            else:
                slip_dict = slip.to_dict()
                slip_dict["id"] = slip.key.urlsafe()
                slip_dict['self'] = "/slip/" + id
                if slip.current_boat is not None:
                    slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
                self.response.write(json.dumps(slip_dict))
        else:
            slips = Slip.query()
            slip_list = list()
            for slip in slips:
                slip_dict = slip.to_dict()
                slip_dict["id"] = slip.key.urlsafe()
                slip_dict['self'] = '/slip/' + slip.key.urlsafe()
                if slip.current_boat is not None:
                    slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
                slip_list.append(slip_dict)
            self.response.write(json.dumps(slip_list))
        self.response.headers.add('content-type', 'application/json')

    def set_slip_number(self):
        max_slip = Slip.query().order(-Slip.number).get()
        max_slip_number = int()
        if max_slip is None:
            max_slip_number = 0
        else:
            max_slip_number = int(max_slip.number) + 1
        return max_slip_number

    def depart_boat(self, slip):
        if slip.current_boat is not None:
            try:
                boat = ndb.Key(urlsafe=slip.current_boat).get()
            except Exception:
                boat = None
            if boat is not None:
                boat.at_sea = True
                boat.put()


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
 #   ('/boat/(.*)/slip/(\(?\+?[0-9]*\)?)?[0-9_\- \(\)]*$', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/boats', BoatHandler),
    ('/slip', SlipHandler),
    ('/slips', SlipHandler),
    ('/slip/(.*)', SlipHandler)
], debug=True)
