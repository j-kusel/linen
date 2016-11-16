class LinError(Exception):
    pass

class PassError(LinError):
    """Exception raised for improper use of the passwords.py file

    Attributes:
        message -- error explanation
    """

    def __init__(self, message):
        self.message = message
