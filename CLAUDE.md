This project contains a set of code files for a project an github. The goals in two fold.

## Goal 1: 

analyze the db.xml which is copied from the Curse of Strahd Fastasy Groups application, and parse out the players weekly notes.

To do this I manually copy the db.xml after each session, then run the "export_notes.py" program. 

## Goal 2: 

clean, sanitize, and convert to html DB to player emails from the emails folder mbox.

a new subfolder will keep track of all the cleaned emails.


## Goal 3:

Deployments. I deploy the html of github as a simple html file so the players can review the notes and email offline.

this serves as a historical account of our communications and progress through the sessions.

## Environment

I have a windows host machine, but I run my python from inside WSL. Using the `myenv` virtual env.


## Features:

Currently only Goal 1 is functional. I have a preliminary script to parse the MBOX emails, but I have not run it yet. the result will need to be html files will all the images correctly uploaded for access in the web. additionally I need an efficient way to manage the timeline of events, as the emails will have dates, but the player notes will not. that means I need a way to order them in the final html.