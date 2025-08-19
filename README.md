Lima's - A simple web based to record local shop's orders and sales.
=============================

## Purpose

This project aims to be an efficient order manager for dine-in establishment, e.g., restaurants, icecream shops etc.

## How to run

After downloading the project files, go to database folder and run:
```console
sqlite3 limas.db
```
Then, in sqlite program, run:
```sqlite3
.read limas.sql
```
By default, new users can be registered. In order to change that, you can change the value of the variable allow_new_users in preferences.py.

After that, your application is ready to run. To do so, go to the project root folder and run:
```bash
flask run
```
That is going to, by default, deploy your application locally on adress 127.0.0.1:5000. You can access it on your local browser and start using.

You can also add the flag --host=0.0.0.0 to run it on all adresses, including your local network (don't worry, flask is going to tell you your local ip), so it can be acessed from anyone using the same router as you

## How to use

The project design's goal is to be the most intuitive as possible. Currently, all the app interface is 

## Dependencies

The project depends on some python packages, including cs50, flask, flask_session, werkzeug.security etc.

