from app.exceptions.UserException import (CredentialsException,
                                          UnAuthorizedException,
                                          UserDoesNotExistsException,
                                          credentials_exception_handler,
                                          unauthorized_exception_handler,
                                          user_exception_handler)

# export to main
exceptions = [
    [UserDoesNotExistsException, user_exception_handler],
    [CredentialsException, credentials_exception_handler],
    [UnAuthorizedException, unauthorized_exception_handler],
]
