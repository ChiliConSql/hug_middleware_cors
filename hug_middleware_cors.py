from typing import Sequence
import re

class CORSMiddleware(object):
    """A middleware for allowing cross-origin request sharing (CORS)

    Adds appropriate Access-Control-* headers to the HTTP responses returned from the hug API,
    especially for HTTP OPTIONS responses used in CORS preflighting.
    """
    __slots__ = ('api', 'allow_origins', 'allow_credentials', 'max_age')

    def __init__(self, api, allow_origins: Sequence[str]=['*'], allow_credentials: bool=True, max_age: int=None):
        self.api = api
        self.allow_origins = allow_origins
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def match_route(self, reqpath):
        '''match a request with parameter to it's corresponding route'''
        route_dicts = [routes for _, routes in self.api.http.routes.items()][0]
        routes = [route for route, _ in route_dicts.items()]
        #no prameters in path
        if reqpath in routes:
            return reqpath
        for route in routes:
            #replace params in route with regex
            if re.match(re.sub(r'/{[^{}]+}', '/\w+', route) + '$', reqpath):
                return route
        return reqpath

    def process_response(self, request, response, resource):
        """Add CORS headers to the response"""

        # return list of allowed origins
        response.set_header('Access-Control-Allow-Origin', ', '.join(self.allow_origins))

        # return whether credentials are allowed
        response.set_header('Access-Control-Allow-Credentials', str(self.allow_credentials).lower())

        # check if we are handling a preflight request
        if request.method == 'OPTIONS':

            # find out what methods were registered for the requested path
            allowed_methods = set(
                method
                for _, routes in self.api.http.routes.items()
                for method, _ in routes[self.match_route(request.path)].items()
            )
            allowed_methods.add('OPTIONS')
            # return allowed methods
            response.set_header('Access-Control-Allow-Methods', ', '.join(allowed_methods))
            response.set_header('Allow', ', '.join(allowed_methods))

            # get all requested headers and echo them back
            requested_headers = request.get_header('Access-Control-Request-Headers')
            response.set_header('Access-Control-Allow-Headers', requested_headers or '')

            # return valid caching time
            if self.max_age:
                response.set_header('Access-Control-Max-Age', self.max_age)
