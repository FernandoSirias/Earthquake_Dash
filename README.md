# Earthquake Dash App


This project used data from [USGS API](https://earthquake.usgs.gov/fdsnws/event/1/?ref=springboard) to create a dash app using plotly and deployed on Heroku.

The analysis include earthquake informations from 2010 to november 2021, the data describe the location, magnitud, tsunami alert, datetime, etc. I clean the data to work only with the columns that were important for the visualizations, some of the graphs are scatter, boxplot, histogram, maps.

Dataframe shape:
 - Observations: 6859
 - Columns: 30

I used an ***API*** to request all the data about earthquakes with an **alert** (green, yellow, orange, red).


**The purpose of this project is to analyze:**
- the increase in earthquakes worldwide.
- discover which are the countries that register the highest number of earthquakes.
- Where do the largest earthquakes occur?
- which earthquakes have a tsunami warning.
- The reason why the earthquakes occurred (Natural, vulcanic eruption, nuclar bomb).


All these objectives are completed by creating a dashboard where users can interact with the graphics through filters and maps.


You can see the live dash [here](https://earthquakedash.herokuapp.com/).

