from selenium import webdriver
from typing import Tuple

import pandas as pd
import random
import subprocess
import time

def run_R(year:str) -> None:
    """Run the R script to create a dataset of NCAA baseball game data for a given year

    Args:
        year (str): The year to create the dataset for
    """
    r_script_path = 'Rscript'

    # Define the path to R script
    r_file_path = 'game_data.R'

    # Define command line arguments as a list
    arguments = [year]

    # Build the command that will be executed
    command = [r_script_path, r_file_path] + arguments

    # Run command
    subprocess.run(command)


def prepare_locations(data:pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe containing all unique game locations.

    Args:
        data (pd.DataFrame): The game data use when finding unique locations

    Returns:
        pd.DataFrame: A dataframe containing all unique locations
    """

    columns = ['home_team','neutral_site','game_info_url']

    # Remove any duplicate locations
    game_info = data.drop_duplicates(subset=  ['home_team','neutral_site'])[columns]

    # Create a key column for eventually mapping the keys to locations
    game_info['key'] = game_info.home_team + game_info.neutral_site.astype(str)

    # Rename columns
    game_info.columns = ['home_team','neutral_site','url','key']

    return game_info

def add_locations(game_data:pd.DataFrame) -> Tuple[pd.DataFrame,dict]:
    """Add the location of each game to the game data.

    Args:
        game_data (pd.DataFrame): The game data to add locations to

    Returns:
        Tuple[pd.DataFrame,dict]: A tuple containing the game data with the locations added and a dictionary mapping the game keys to locations.
    """

    # Create a webdriver to scrape the NCAA website
    wd = webdriver.Chrome()

    locations = []

    # iterate through the game urls to find the location of each game
    for url in game_data.url:

        # Add a random delay to avoid being blocked by the NCAA website
        delay = random.random() + 1
        time.sleep(delay)

        # Try to find the location of the game
        try:
            wd.get(url)
            html = wd.page_source
            location = html.split('Location:</td>\n      <td>')[1].split("</td>\n")[0]
        except Exception:
            location = None
        locations.append(location)

    # Close the webdriver
    wd.quit()

    # Add the locations to the game data
    game_data['location'] = locations

    # handle two locations which are geo-located incorrectly
    game_data.location = game_data.location.replace({"San Mateo JC": "College of San Mateo",
                                                       "Young Memorial FIeld":"UAB"})

    # Create a dictionary mapping the game keys to locations
    location_dict = dict(zip(game_data['key'],game_data['location']))

    return game_data,location_dict
