class TubePlanningError(Exception):
    """Project-specific exception raised for invalid tube-planning inputs.

    You can use this class in the same way as you would use any other Exception
    class:

    >>> raise TubePlanningError("error text")
    Traceback (most recent call last):
    File "/path/to/file/running.py", line XX, in <module>
        ...
    TubePlanningError: error_message
    """

    pass
