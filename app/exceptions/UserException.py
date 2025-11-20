from logging import logging

from fastapi import FastAPI, HTTPException, Request, status

logging = logging.getLogger(__name__)

class UserDoesNotExistsException(HTTPException):
  def __init__(self, detail: str, status_code: int):
    self.detail = detail
    self.status_code = status_code

def user_exception_handler(req: Request, ex: UserDoesNotException):
    logging.error(f"UserDoesNotExistsException: {ex.detail}")
    return JSONResponse(
        status_code=ex.status_code,
        content={"message": f'error: {ex.detail}'}
    )

class credentialsException(HTTPException):
  def __init__(self):
    pass

def credentials_exception_handler(req: Request, ex: CredentialsException):
    logging.error(f"CredentialsException")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

class UnAuthorizedException(HTTPException):
  def __init__(self, detail: str, status_code: int):
    self.detail = detail
    self.status_code = status_code

def unauthorized_exception_handler(req: Request, ex: UnAuthorizedException):
    logging.error(f"UnAuthorizedException: {ex.detail}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your don't have permission to access this resource",
    ):
