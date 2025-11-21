import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logging = logging.getLogger(__name__)

class UserDoesNotExistsException(HTTPException):
  def __init__(self, detail: str, status_code: int):
    self.detail = detail
    self.status_code = status_code

def user_exception_handler(req: Request, ex: UserDoesNotExistsException):
    logging.error(f"UserDoesNotExistsException: {ex.detail}")
    return JSONResponse(
        status_code=ex.status_code,
        content={"message": f'error: {ex.detail}'}
    )

class CredentialsException(HTTPException):
  def __init__(self, msg: str = "Could not validate credentials", status_code: int = status.HTTP_403_FORBIDDEN):
    super().__init__(status_code=status_code)
    self.msg: str = msg

def credentials_exception_handler(req: Request, ex: CredentialsException):
    logging.error(f"CredentialsException: {ex.msg}")
    return JSONResponse(
        status_code=ex.status_code,
        content={"detail": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )

class UnAuthorizedException(HTTPException):
  def __init__(self, msg: str = "Unauthorized", status_code: int = status.HTTP_401_UNAUTHORIZED):
    self.msg = msg
    self.status_code = status_code

def unauthorized_exception_handler(req: Request, ex: UnAuthorizedException):
    logging.error(f"UnAuthorizedException: {ex.msg}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your don't have permission to access this resource",
    )

exceptions = [
    (UserDoesNotExistsException, user_exception_handler),
    (CredentialsException, credentials_exception_handler),
    (UnAuthorizedException, unauthorized_exception_handler),
]