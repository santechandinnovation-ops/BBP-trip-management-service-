class TripNotFoundException(Exception):
    pass

class TripAlreadyCompletedException(Exception):
    pass

class InvalidCoordinatesException(Exception):
    pass

class UnauthorizedTripAccessException(Exception):
    pass

class WeatherServiceException(Exception):
    pass

class NoCoordinatesException(Exception):
    pass
