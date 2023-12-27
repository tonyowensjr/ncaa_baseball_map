# May need to install baseballr package via devtools
# install.packages("devtools", repos = "http://cran.us.r-project.org")
# devtools::install_github("BIllPetti/baseballr")

# Usage: Rscript game_data.R 2023 1.5
args <- commandArgs(trailingOnly = TRUE)
data_year <- as.integer(args[1])
sleep_interval <- as.numeric(args[2])

# Get the team IDs for the year
team_ids <- baseballr::ncaa_teams(data_year, division = 1)$team_id

# Get the game results for each team using their team ID
game_df <- baseballr::ncaa_schedule_info(team_id = team_ids[1], year = data_year)
for (i in team_ids[(-1)]) {
    game_df <- rbind(game_df, baseballr::ncaa_schedule_info(team_id = i, year = data_year))

    # Sleep for a brief period to avoid violating the NCAA website rate limit
    Sys.sleep(sleep_interval)
}

# Write the game data to a CSV file
csv_path <- paste0("game_data/df_", data_year, ".csv")
write.csv(game_df, csv_path, row.names = TRUE)
