from revcore.django.exceptions import APIError


class InvalidUser(APIError):
    status_code = 400
    code = 100
    detail = "Invalid request"


class UserExist(APIError):
    status = 400
    code = 101
    detail = 'User already exist'


class UserNotFoundError(APIError):
    status = 404
    code = 103
    detail = 'User Not Found'


class CantNotFound(APIError):
    status = 400
    code = 104
    detail = 'Login Failed'