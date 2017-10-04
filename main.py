import webapp2
import datetime
from datetime import datetime
from google.appengine.ext import ndb
import json
import uuid
import io


class Boat(ndb.Model):
    # boat_id = ndb.KeyProperty(required=True)
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()


class Departure_History(ndb.Model):
    departure_date = ndb.StringProperty()
    departed_boat = ndb.StringProperty()


class Slip(ndb.Model):
    id = ndb.StringProperty()
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()
    # arrival_date = ndb.DateProperty()
    departure_history = ndb.StructuredProperty(Departure_History, repeated=True)


class BoatHandler(webapp2.RequestHandler):
    def post(self):
        boat_data = json.loads(self.request.body)
        new_boat = Boat(  # id = str(uuid.uuid1()),
            name=boat_data['name'],
            type=boat_data['type'],
            length=int(boat_data['length']),
            at_sea=True)
        new_boat.put()
        new_boat.id = new_boat.key.urlsafe()
        new_boat.put()
        boat_dict = new_boat.to_dict()
        boat_dict['self'] = '/boat/' + new_boat.key.urlsafe()
        self.response.set_status(201)
        self.response.headers.add('content-type', 'application/json')
        self.response.headers.add('location', boat_dict['self'])
        self.response.write(json.dumps(boat_dict))

    def put(self, id=None):
        # type: (object) -> object
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
            self.response.headers.add('content-type', 'application/json')

    def get(self, id=None):
        # type: (object) -> object
        if id:
            boat = ndb.Key(urlsafe=id).get()
            if boat is None:
                self.response.set_status(404)
            else:
                boat_dict = boat.to_dict()
                boat_dict['self'] = "/boat/" + id
                self.response.write(json.dumps(boat_dict))
        else:
            boats = Boat.query().fetch(10)
            boat_list = list()
            for idx, boat in enumerate(boats):
                boat_dict = boat.to_dict()
                boat_dict['self'] = '/boat/' + boat.id
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
                    #Departure Scenario
                    if (current_boat.at_sea != True and boat_patch_data_dict['at_sea']):
                        slip = Slip.query(Slip.current_boat == current_boat.id).fetch()[0]
                        slip.current_boat = None
                        slip.arrival_date = None
                        departure = Departure_History()
                        departure.departed_boat = current_boat.id
                        departure.departure_date = datetime.strftime(datetime.today(), "%m/%d/%Y")
                        slip.departure_history.append(departure)
                        slip.put()
                        current_boat.at_sea = True
                    #Arrival Scenario
                    if (current_boat.at_sea and boat_patch_data_dict['at_sea'] != True):
                        #query to find empty slip
                        slip_list = Slip.query(Slip.number == int(slipnumber)).fetch()
                        #If slip is occupoed return 403?  (I guess i all slips occupied?)
                        if slip_list is None or slip_list.count == 0:
                            self.response.set_status(404)
                        else:
                            slip = slip_list[0]
                            if slip.current_boat is not None:
                                self.response.set_status(403)
                            else:
                                slip.current_boat = current_boat.id
                                slip.arrival_date = datetime.strftime(datetime.today(), "%m/%d/%Y")
                                slip.put()
                                current_boat_dict['slip_url'] = '/slip/' + slip.id
                                current_boat.at_sea = False
                current_boat.put()
                current_boat_dict['self'] = '/boat/' + id
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

    def post(self, id=None):
        slip_data = json.loads(self.request.body)
        new_slip = Slip(
            # id = str(uuid.uuid1()),
            number=int(slip_data['number']))  # ,
        # current_boat = slip_data['current_boat'],
        # arrival_date_str = slip_data['arrival_date'],
        # arrival_date = datetime.strptime(slip_data['arrival_date'],"%m/%d/%Y"),
        # departure_history = [])
        new_slip.put()
        new_slip.id = new_slip.key.urlsafe()
        new_slip.put()
        slip_dict = new_slip.to_dict()
        slip_dict['self'] = '/slip/' + new_slip.key.urlsafe()
        self.response.write(json.dumps(slip_dict))
        self.response.headers.add('content-type', 'application/json')
        self.response.headers.add('location', slip_dict['self'])

    def delete(self, id=None):
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
        # type: () -> object
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
