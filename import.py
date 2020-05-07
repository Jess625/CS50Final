#script to import the imdb data into a SQLlite database (filtering by movies)

from cs50 import SQL
import csv

#db = SQL("sqlite:///movie.db")

#creates variable to open title.basics.tsv
with open("title.basics.tsv", "r") as titles:

    #variable to read titles into a Dict
    reader = csv.DictReader(titles, delimiter="\t")

    #sets variable to open and write to a csv
    with open("movies.csv", "w") as movies:

        writer = csv.writer(movies)

        #writes titles for each row
        writer.writerow(["id", "title", "year", "genres", "runtime"])

        for row in reader:

            if row["startYear"] != "\\N":

                year = int(row["startYear"])

                if year >= 1950:

                    if row["titleType"] == "movie" and row["isAdult"] == 0:

                        writer.writerow(row["tconst"], row["primaryTitle"], row["startYear"], row["genres"], row["runtimeMinutes"])