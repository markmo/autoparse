"""
Load settings from the `.env` file that can be accessed as environment variables
::

    os.getenv('<key>')

"""

from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
