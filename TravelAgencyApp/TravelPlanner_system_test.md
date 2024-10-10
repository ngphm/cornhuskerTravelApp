# Travel Planner System Test

## System Test: Validate Location

### Preconditions

- Have the Travel Planner App installed and ready to run.
- Have API key obtained from OpenWeather ready.
- Have linked Operator Tracker App and Airport Tracker App ready to use.

### Test

1. Run the `Airport Tracker App`. Select `Add City`.

    a. **Inputs**: Name = `Kearney`, Geographic Identity = `U.S.`, Longitude = `-92.4`, Latitude = `37.5`. **Expected
   output**: The app should now display message for succesfully creating city.

    b. Click `Back` when asked to select/create nearby service airport. 

    c. Select `Add Airport`. **Inputs**: Name = `Madang Airport`, ICAO code = `AYMD`, Longitude = `145.7`, Latitude = `-5.2`. Click `Back` when asked to create a new city.

    d.  Select `Add Airport`.  **Inputs**: Name = `Private Airport`, ICAO code = `MINE`, Longitude = `-1`, Latitude = `1`. Click `Back` when asked to create a new city. 

    e. Exit the App.

2. Run the `Travel Planner App`

   The app should now display, with an empty password and OpenWeather API Key field.

3. In the password and API Key field, type:

   a. **Input**: leave password and API Key field empty. Click submit. **Expected
   output**: `Please enter the password. Please enter the API key.`

   b. **Input**: password = `mdF:9Y` and leave API Key field empty. Click submit. **Expected
   output**: `Please enter the API key.`

   c. **Input**: password = `df`, API Key = `123`. Click submit. **Expected
   output**: `Database connection failed! Call OpenWeather API failed!`

   d. **Input**: password = `df`, use API Key obtained from OpenWeather. Click submit. **Expected output**: The app
   should now display menu screen because the initial connection is successful.

4. On menu screen, press `Validate Locations` button.

   The app should now display `Validate Locations` screen, with cities and/or airports needed to be validated.

5. On `Validate Locations` screen, select: 

    a. **Input**:`Lincoln`. Press `Validate`. **Expected output**: `City was successfully validated`.  Press `OK`.

    b. **Input**: `Kearney`. Press `Validate`. **Expected output**: `City could not be validated. A nearby city with the same name has longitude: -94.3621376 and latitude: 39.3731886. Do you want to use this data or keep your data?`

    c. Select `Use Official Data`. **Expected output**: `Kearney` will be removed from the list. `Cities/Airports to be validated` field in Main Menu Screen will be decreased by 1. City with name `Kearney`'s longitude and latitude will be updated in the database.

    d. **Input**: `Madang Airport` and press `Validate`. **Expected output**: `An airport with the same ICAO code {airport.ICAO_code} exists at longitude: 145.7890015 and latitude: -5.207079887. Do you want to use this data or keep your data?`

    e. Select `Use Official Data`. **Expected output**: `Madang Airport` will be removed from the list. `Cities/Airports to be validated` field in Main Menu Screen will be decreased by 1. Airport with name `Madang Airport`'s longitude and latitude will be updated in the database.

    f. **Input**: `Private Airport`. Press `Validate`. **Expected output**: `Airport with ICAO code MINE not found. Airport removed from the database.`

    g. Select `Back`. **Expected output**: `Private Airport` will be removed from the
   list. `Cities/Airports to be validated` field in Main Menu Screen will be decreased by 1. Airport with name `Private Airport`
   will be removed from the database.

6. Exit the app.
