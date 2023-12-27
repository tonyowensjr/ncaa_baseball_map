from geopy.geocoders import Nominatim
from selenium import webdriver
from typing import Tuple

import argparse
import os
import pandas as pd
import random
import subprocess
import time

def run_R(year:str,delay:str) -> None:
    """Run the R script to create a dataset of NCAA baseball game data for a given year

    Args:
        year (str): The year to create the dataset for
    """
    r_script_path = 'Rscript'

    # Define the path to R script
    r_file_path = 'game_data.R'

    # Define command line arguments as a list
    arguments = [year,delay]

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

def find_coords(game_data:pd.DataFrame) -> dict:
    """Create a dictionary which maps locations to coordinates.

    Args:
        game_data (pd.DataFrame): A dataframe with the unique locations

    Returns:
        dict: A dictionary mapping locations to coordinates
    """

    unique_locations = game_data.location.unique()
    geolocator = Nominatim(user_agent="ncaa_map")
    coords_dict = {}

    # iterate through the locations to find the coordinates of each location
    for unique_loc in unique_locations:
        # Add a random delay to avoid being blocked by the geolocator
        delay = random.random() + 1
        time.sleep(delay)

        # Try to find the coordinates of the location and add them to the dictionary
        loc_info = geolocator.geocode(unique_loc)
        try:
            lat,lon = loc_info.latitude,loc_info.longitude
            coords_dict[unique_loc] = (lat,lon)
        except Exception:
            continue
    return coords_dict

def main():
    # Parse the year from the command line
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--year", help="input csv file")
    argparser.add_argument("--delay", help="the delay (in seconds) between each request in the R file")
    args = argparser.parse_args()
    year = args.year
    delay = args.delay

    # If the data does not already exist, run the R script to create the dataset of NCAA data
    if not os.path.exists(f'game_data/df_{year}.csv'):
        run_R(year,delay)

    # Read in the data and add the locations
    data = pd.read_csv(f'game_data/df_{year}.csv')
    game_info,location_dict = add_locations(prepare_locations(data))

    # Find the coordinates of each location
    coords_dict = find_coords(game_info)
    data['location'] = (data.home_team + data.neutral_site.astype(str)).map(location_dict)
    data['coords'] = data.location.map(coords_dict)

    # Create a column with the information to be displayed on the map
    data['info'] = data.home_team + ' vs. ' + data.away_team + ' ' + '(' + data.home_team_score.astype(str) \
        + '-' + data.away_team_score.astype(str) + ') ' + data.date 
    
    # Create columns for the latitude and longitude
    data[['latitude', 'longitude']] = pd.DataFrame(data['coords'].tolist(), index=data.index)
    
    # Save the data
    data.sort_values(by = 'date')[['latitude','longitude','info']].drop_duplicates().to_csv(f'game_data/cleaned_df_{year}.csv')

if __name__ == "__main__":
    main()