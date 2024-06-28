def transform_string(input_string: str) -> str:
    """
    Transforms the input string by:
    1. Removing forbidden characters for Windows and macOS filenames.
    2. Replacing consecutive spaces with a single space.
    3. Replacing remaining spaces with underscores.
    4. Removing consecutive underscores.
    5. Converting the string to lowercase.

    Args:
        input_string (str): The string to be transformed.

    Returns:
        str: The transformed string.

    Raises:
        TypeError: If the input is not a string.
    """
    try:
        if not isinstance(input_string, str):
            raise TypeError("Input must be a string")

        # List of forbidden characters for Windows and macOS filenames
        forbidden_chars = ['\\', ':', '*', '?', '"', '<', '>', '|', '\0', '-', ',']
        
        # Remove forbidden characters
        for char in forbidden_chars:
            input_string = input_string.replace(char, '')
        
        # Replace consecutive spaces with a single space
        input_string = ' '.join(input_string.split())
        
        # Replace spaces with underscores
        input_string = input_string.replace(' ', '_')
        
        # Remove consecutive underscores
        while '__' in input_string:
            input_string = input_string.replace('__', '_')
        
        # Convert to lowercase
        result = input_string.casefold()
        
        return result

    except TypeError as e:
        print(f"Error transforming string: {e}")
        return ""

# Test the function with different types of input
# print(transform_string('vet_|_done done')) 
# print(transform_string(123))  # Expected error message
