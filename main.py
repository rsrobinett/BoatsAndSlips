import webapp2
import datetime
from datetime import datetime
from google.appengine.ext import ndb
import json


class Boat(ndb.Model):
    # boat_id = ndb.KeyProperty(required=True)
    #id = ndb.StringProperty()
    name = ndb.StringProperty()
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()


class DepartureHistory(ndb.Model):
    departure_date = ndb.StringProperty()
    departed_boat = ndb.StringProperty()


class Slip(ndb.Model):
    #id = ndb.StringProperty()
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
        self.response.set_status(201)
        self.response.headers.add('content-type', 'application/json')
        self.response.headers.add('location', boat_dict['self'])
        self.response.write(json.dumps(boat_dict))

    def put(self, id=None):
        boat_data = json.loads(self.request.body)
        if id:
            boat = ndb.Key(urlsafe=id).get()
            if boat is None:
                self.response.set_status(404)
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
                boat.at_sea = True
                boat_dict = boat.to_dict()
                boat_dict['self'] = "/boat/" + boat.key.urlsafe()
                boat.put()
                self.response.write(json.dumps(boat_dict))
                self.response.headers.add('content-type', 'application/json')

    def get(self, id=None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            if boat is None:
                self.response.set_status(404)
            else:
                boat_dict = boat.to_dict()
                boat_dict['id'] = id
                boat_dict['self'] = "/boat/" + boat.key.urlsafe()
                self.response.write(json.dumps(boat_dict))
        else:
            boats = Boat.query()
            boat_list = list()
            for idx, boat in enumerate(boats):
                boat_dict = boat.to_dict()
                boat_dict['id'] = id
                boat_dict['self'] = '/boat/' + boat.key.urlsafe()
                boat_list.append(boat_dict)
            self.response.write(json.dumps(boat_list))
        self.response.headers.add('content-type', 'application/json')

    def delete(self, id=None):
        if id:
            b = ndb.Key(urlsafe=id)
            b.delete()
        self.response.set_status(204)

    def patch(self, id=None, slipnumber=None):
        if id:
            current_boat = ndb.Key(urlsafe=id).get()
            if current_boat is None:
                self.response.set_status(404)
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
                    # Departure Scenario
                    if (current_boat.at_sea != True and boat_patch_data_dict['at_sea']):
                        slip = Slip.query(Slip.current_boat == current_boat.key.urlsafe()).get()
                        slip.current_boat = None
                        slip.arrival_date = None
                        departure = DepartureHistory()
                        departure.departed_boat = current_boat.key.urlsafe()
                        departure.departure_date = datetime.strftime(datetime.today(), "%m/%d/%Y")
                        slip.departure_history.append(departure)
                        slip.put()
                        current_boat.at_sea = True
                    # Arrival Scenario
                    if (current_boat.at_sea and boat_patch_data_dict['at_sea'] != True):
                        slip = Slip.query(Slip.number == int(slipnumber)).get()
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
                                current_boat_dict['slip_url'] = '/slip/' + slip.key.urlsafe()
                                current_boat.at_sea = False
                current_boat.put()
                current_boat_dict['self'] = '/boat/' + current_boat_dict.key.urlsafe()
                self.response.write(json.dumps(current_boat_dict))
                self.response.headers.add('content-type', 'application/json')
                self.response.headers.add('location', current_boat_dict['self'])


class SlipHandler(webapp2.RequestHandler):
    def patch(self, id=None):
        if id:
            slip = ndb.Key(urlsafe=id).get()
            if slip is None:
                self.response.set_status(404)
            else:
                slip_patch_data = json.loads(self.request.body)
                slip_dict = slip.to_dict()
                for key, data in slip_patch_data.items():
                    slip_dict[key] = data
                if 'number' in slip_dict:
                    slip.number = slip_dict['number']
                if 'current_boat' in slip_dict:
                    slip.current_boat = slip_dict['current_boat']
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
        # type: (object) -> object
        if id:
            slip = ndb.Key(urlsafe=id).get()
            if slip is None:
                self.response.set_status(404)
            else:
                slip_dict = slip.to_dict()
                slip_dict['self'] = "/slip/" + id
                if slip.current_boat is not None:
                    slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
                self.response.write(json.dumps(slip_dict))
        else:
            slips = Slip.query().fetch(1000)
            slip_list = list()
            for idx, slip in enumerate(slips):
                slip_dict = slip.to_dict()
                slip_dict['self'] = '/slip/' + slip.id
                if slip.current_boat is not None:
                    slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
                slip_list.append(slip_dict)
            self.response.write(json.dumps(slip_list))
        self.response.headers.add('content-type', 'application/json')

    def post(self):
        slip_data = json.loads(self.request.body)
        new_slip = Slip(number=int(slip_data['number']))
        new_slip.put()
        slip_dict = new_slip.to_dict()
        slip_dict['self'] = '/slip/' + new_slip.key.urlsafe()
        self.response.write(json.dumps(slip_dict))
        self.response.headers.add('content-type', 'application/json')
        self.response.headers.add('location', slip_dict['self'])

    def delete(self, id = None):
        if id:
            slip = ndb.Key(urlsafe=id)
            slip.delete()
        self.response.set_status(204)


class DockHandler(webapp2.RequestHandler):
    def patch(self, id, slipNumber):
        self.response.write("id is " + id + " and slip number is " + slipNumber)
        self.response.headers.add('content-type', 'application/json')


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
    ('/boat/(.*)/slip/(\(?\+?[0-9]*\)?)?[0-9_\- \(\)]*$', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/boats', BoatHandler),
    ('/slip', SlipHandler),
    ('/slips', SlipHandler),
    ('/slip/(.*)', SlipHandler)
], debug=True)
