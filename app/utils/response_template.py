"""
# Response Templates
"""

def penelope_response_template(message: str, id: str = None, type: str = 'chunk') -> dict:
    """
    Create a standardized response template for method calls.

    Args:
        message (str): A descriptive message about the response.
        id (str): The id of the response.
        success (bool, optional): Indicates if the operation was successful. Defaults to False.
    """
    return {
        "message": message,
        "id": id,
        "type": type
    }


def response_template(message: str, data: dict = None, 
                      error: str = None, status_code: int = 200):
    """
    Create a standardized response template for API endpoints.

    Args:
        message (str): A descriptive message about the response.
        data (dict, optional): The data payload of the response. Defaults to None.
        error (str, optional): An error message if applicable. Defaults to None.
        status_code (int, optional): The HTTP status code for the response. Defaults to 200.

    Returns:
        tuple: A tuple containing the response data dictionary and the status code.
    """
    response_data = {
        "message": message,
        "data": data,
        "error": error
    }
    return response_data, status_code



def method_response_template(message: str, data: dict, success: bool = False) -> dict:
    """
    Create a standardized response template for method calls.

    Args:
        message (str): A descriptive message about the response.
        data (dict): The data payload of the response.
        success (bool, optional): Indicates if the operation was successful. Defaults to False.

    Returns:
        dict: A dictionary containing the structured response with message, data, and success status.
    """
    return {
        "message": message,
        "data": data,
        "success": success
    }
