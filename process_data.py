import subprocess

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

