import webapp2
import datetime
from datetime import datetime
from google.appengine.ext import ndb
from google.appengine.ext import db
import json


class Boat(ndb.Model):
    id = ndb.StringProperty()
    name = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True)
    length = ndb.IntegerProperty(required=True)
    at_sea = ndb.BooleanProperty(required=True)


class DepartureHistory(ndb.Model):
    departure_date = ndb.StringProperty()
    departed_boat = ndb.StringProperty()


class Slip(ndb.Model):
    id = ndb.StringProperty()
    number = ndb.IntegerProperty(required=True)
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()
    departure_history = ndb.StructuredProperty(DepartureHistory, repeated=True)


def set_slip_number():
    max_slip = Slip.query().order(-Slip.number).get()
    if max_slip is None:
        max_slip_number = 0
    else:
        max_slip_number = int(max_slip.number) + 1
    return max_slip_number


def depart(boat):
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


class BoatHandler(webapp2.RequestHandler):
    def post(self):
        boat_data = json.loads(self.request.body)
        new_boat = Boat()
        new_boat.name = boat_data['name']
        new_boat.type = boat_data['type']
        new_boat.length = int(boat_data['length'])
        new_boat.at_sea = True
        new_boat.put()
        new_boat.id = new_boat.key.urlsafe()
        new_boat.put()
        boat_dict = new_boat.to_dict()
        boat_dict['id'] = new_boat.key.urlsafe()
        boat_dict['self'] = '/boat/' + new_boat.key.urlsafe()
        self.create_boat_dictionary(new_boat)
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
                boat.name = boat_data['name']
                boat.type = boat_data['type']
                boat.length = int(boat_data['length'])
                if not boat.at_sea:
                    depart(boat)
                boat_dict = boat.to_dict()
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
                boat_dict = self.create_boat_dictionary(boat)
                self.response.write(json.dumps(boat_dict))
        else:
            boats = Boat.query()
            boat_list = list()
            for boat in boats:
                boat_dict = self.create_boat_dictionary(boat)
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
                    depart(boat)
                boat.key.delete()
        self.response.set_status(204)

    def patch(self, id=None):
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
                current_boat.put()
                current_boat_dict['self'] = '/boat/' + current_boat.key.urlsafe()
                self.response.write(json.dumps(current_boat_dict))
                self.response.headers.add('content-type', 'application/json')
                self.response.set_status(200)
        else:
            self.response.set_status(400)

    def create_boat_dictionary(self, boat):
        boat_dict = boat.to_dict()
        if not boat.at_sea:
            self.get_slip_url(boat, boat_dict)
        boat_dict['self'] = "/boat/" + boat.key.urlsafe()
        return boat_dict

    def get_slip_url(self, boat, boat_dict):
        slip = Slip.query(Slip.current_boat == boat.key.urlsafe()).get()
        boat_dict['slip_url'] = "/slip/" + slip.key.urlsafe()


class SlipHandler(webapp2.RequestHandler):
    def post(self):
        body = json.loads(self.request.body)
        new_slip_number = body['number']
        slip_check = Slip.query(Slip.number == new_slip_number).get()
        new_slip = Slip()
        if slip_check is None:
            new_slip.number = number = new_slip_number
        else:
            self.response.set_status(403)
            self.response.headers.add('content-type', 'text/plain')
            self.response.write(
                "slip number is not available. " + str(set_slip_number()) + " may be an available slip.")
            return
        new_slip.put()
        new_slip.id = new_slip.key.urlsafe()
        new_slip.put()
        self.get(new_slip.key.urlsafe())
        self.response.headers.add('location', '/slip/' + new_slip.key.urlsafe())
        self.response.set_status(201)

    def delete(self, id=None):
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
                body = json.loads(self.request.body)
                new_slip_number = body['number']
                slip_check = Slip.query(Slip.number == new_slip_number).get()
                new_slip = Slip()
                if slip_check is None:
                    new_slip.number = number = new_slip_number
                else:
                    self.response.set_status(403)
                    self.response.headers.add('content-type', 'text/plain')
                    self.response.write(
                        "slip number is not available. " + str(set_slip_number()) + " may be an available slip.")
                    return
                # slip.number = self.set_slip_number()
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
                slip_patch_dict = dict()
                for key, data in slip_patch_data.items():
                    slip_patch_dict[key] = data
                if 'number' in slip_patch_dict:
                    slip_check = Slip.query(Slip.number == slip_patch_dict['number']).get()
                    if slip_check is None or slip_check.number == slip.number:
                        slip.number = int(slip_patch_dict['number'])
                    else:
                        self.response.set_status(400)
                        self.response.headers.add('content-type', 'text/plain')
                        self.response.write("slip number is not available")
                        return
                if 'current_boat' in slip_patch_dict:
                    if slip_patch_dict['current_boat'] != slip.current_boat:
                        boat_in_slip = ndb.Key(urlsafe=slip.current_boat).get()
                        depart(boat_in_slip)
                    slip.current_boat = slip_patch_dict['current_boat']
                if 'arrival_date' in slip_patch_dict and slip.current_boat is not None:
                    slip.arrival_date = slip_patch_data['arrival_date']
                slip.put()
                slip_dict = slip.to_dict()
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
                slip_dict['self'] = "/slip/" + id
                if slip.current_boat is not None:
                    slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
                self.response.write(json.dumps(slip_dict))
        else:
            slips = Slip.query()
            slip_list = list()
            for slip in slips:
                slip_dict = slip.to_dict()
                slip_dict['self'] = '/slip/' + slip.key.urlsafe()
                if slip.current_boat is not None:
                    slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
                slip_list.append(slip_dict)
            self.response.write(json.dumps(slip_list))
        self.response.headers.add('content-type', 'application/json')

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
        self.response.headers['content-type'] = 'text/plain'
        self.response.write('Hello, World!')
        self.response.write('\n')
        self.response.write(datetime.datetime.now().strftime("%x %X"))


allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods


class ArrivalHandler(webapp2.RequestHandler):
    def put(self, slip_number):
        try:
            slip = Slip.query(Slip.number == int(slip_number)).get()
        except Exception:
            self.response.set_status(404)
            self.response.write("Searching for slip by number caused and exception")
            self.response.headers.add('content-type', 'text/plain')
            return
        if slip is None:
            self.response.set_status(404)
            self.response.write("Searching for slip by number resulted in no slip being found")
            self.response.headers.add('content-type', 'text/plain')
            return
        body = json.loads(self.request.body)
        incoming_boat_id = body['incoming_boat']
        if slip.current_boat != incoming_boat_id:
            if slip.current_boat is not None:
                self.response.set_status(403)
                self.response.write("Slip is occupied")
                self.response.headers.add('content-type', 'text/plain')
                return
            incoming_boat = ndb.Key(urlsafe=incoming_boat_id).get()
            if incoming_boat is None:
                self.response.set_status(404)
                self.response.write("unknown boat " + incoming_boat_id)
                self.response.headers.add('content-type', 'text/plain')
                return
            incoming_boat.at_sea = False
            incoming_boat.put()
            slip.current_boat = incoming_boat.id
            slip.arrival_date = datetime.strftime(datetime.utcnow().date(), "%m/%d/%Y")
            slip.put()
        slip_dict = slip.to_dict()
        slip_dict['self'] = "/slip/" + slip.id
        slip_dict['current_boat_url'] = '/boat/' + slip.current_boat
        self.response.write(json.dumps(slip_dict))
        self.response.headers.add('content-type', 'application/json')


    def delete(self, slip_number):
        try:
            slip = Slip.query(Slip.number == int(slip_number)).get()
        except Exception:
            self.response.set_status(404)
            self.response.write("Searching for slip by number caused and exception")
            self.response.headers.add('content-type', 'text/plain')
            return
        if slip is None:
            self.response.set_status(404)
            self.response.write("Searching for slip by number resulted in no slip being found")
            self.response.headers.add('content-type', 'text/plain')
            return
        if slip.current_boat is None:
            self.response.set_status(404)
            self.response.write("Slip is not occupied")
            self.response.headers.add('content-type', 'text/plain')
            return
        boat = ndb.Key(urlsafe=slip.current_boat).get()
        if boat is None:
            self.response.set_status(404)
            self.response.write("unknown boat " + slip.current_boat)
            self.response.headers.add('content-type', 'text/plain')
            return
        boat.at_sea = True
        boat.put()
        departure_history = DepartureHistory(departed_boat=boat.id, departure_date=datetime.strftime(datetime.utcnow().date(), "%m/%d/%Y"))
        slip.departure_history.append(departure_history)
        slip.current_boat = None
        slip.arrival_date = None
        slip.put()
        slip_dict = slip.to_dict()
        slip_dict['self'] = "/slip/" + slip.id
        self.response.write(json.dumps(slip_dict))
        self.response.headers.add('content-type', 'application/json')


        #try:
        #    current_boat = ndb.Key(urlsafe=boat_id).get()
        #ex#cept Exception:
        #    self.response.set_status(403)
        #    self.response.write("Searching for boat by id cause and exception")
        #    self.headers['content-type'] = 'text/plain'
        #    return
        #if current_boat is None:
        #    self.response.set_status(403)
        #    self.response.write("Searching for boat by id resulted in no boat being found")
        #    self.headers['content-type'] = 'text/plain'
        #    return
        #if not current_boat.at_sea:
        #    self.response.set_status(403)
        #    self.response.write("Searching boat has already arrived")
        #    self.headers['content-type'] = 'text/plain'
        #    return

    def patch(self, boat_id, slip_number_from_url):
        try:
            current_boat = ndb.Key(urlsafe=boat_id).get()
        except Exception:
            current_boat = None
        if current_boat is None:
            self.response.set_status(403)
            return
        else:
            if not current_boat.at_sea:
                self.response.set_status(403)
                return
            slip = Slip.query(Slip.number == int(slip_number_from_url)).get()
            if slip is None:
                self.response.set_status(403)
                return
            else:
                if slip.current_boat is not None:
                    self.response.set_status(403)
                else:
                    slip.current_boat = current_boat.key.urlsafe()
                    body = json.loads(self.request.body)
                    if 'arrival_date' in body:
                        slip.arrival_date = body['arrival_date']
                    else:
                        return self.response.set_status(403)
                    # slip.arrival_date = datetime.strftime(datetime.today(), "%m/%d/%Y")
                    slip.put()
                    current_boat.at_sea = False
                    current_boat.put()
            current_boat_dict = current_boat.to_dict()
            current_boat_dict['self'] = '/boat/' + current_boat.key.urlsafe()
            current_boat_dict['slip_url'] = '/slip/' + slip.key.urlsafe()
            self.response.write(json.dumps(current_boat_dict))
            self.response.headers.add('content-type', 'application/json')


class DepartureHandler(webapp2.RequestHandler):
    def patch(self, boat_id):
        try:
            current_boat = ndb.Key(urlsafe=boat_id).get()
        except Exception:
            current_boat = None
        if current_boat is None:
            self.response.set_status(403)
            self.response.write("current_boat is None")
            return
        if current_boat.at_sea:
            self.response.set_status(400)
            self.response.write("current_boat is already at sea")
        else:
            depart(current_boat)
            current_boat_dict = current_boat.to_dict()
            current_boat_dict['self'] = '/boat/' + current_boat.key.urlsafe()
            self.response.write(json.dumps(current_boat_dict))
            self.response.headers.add('content-type', 'application/json')
            self.response.headers.add('content-length', "0")


class SlipTestHelperHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(set_slip_number())
        self.response.headers['content-type'] = 'text/plain'


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boat', BoatHandler),
    ('/slip/available', SlipTestHelperHandler),
    ('/boat/(.*)/arrival', ArrivalHandler),
    ('/slip/(\(?\+?[0-9]*\)?)?[0-9_\- \(\)]*/arrival', ArrivalHandler),
    ('/boat/(.*)/at_sea', DepartureHandler),
    ('/boat/(.*)', BoatHandler),
    ('/boats', BoatHandler),
    ('/slip', SlipHandler),
    ('/slips', SlipHandler),
    ('/slip/(.*)', SlipHandler)
], debug=True)
