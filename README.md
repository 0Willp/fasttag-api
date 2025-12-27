# 🛰️ FastTag API.
The **FastTag API** is a microservice developed in FastAPI to centralize communication with different tag tracking providers. The project allows authentication and retrieval of geographic data from multiple providers, standardizing the response and generating direct visualizations in Google Maps.

-----

## 🚀 Features
- Abstraction: A single interface to query different providers (Findtag, BrGPS, etc.).
- Surity: Authentication based on MD5 signature and API Keys managed via environment variables.
- Geolocation: Automatic conversion of coordinate strings to numerical latitude/longitude.
- Google Maps Integration: Dynamic generation of view links based on the last reported position.
-----
## 🛠️ Requirements

  * Python 3.11+
  * Pipenv
----
## 📥  Installation and Configuration
1. Clone the Repository.
```properties
git clone https://github.com/seu-usuario/fasttag-api.git
cd fasttag-api
```

2. Install Dependencies:
We use Pipenv to ensure that all libraries (FastAPI, Pydantic, Requests) are in the correct version.
```properties
pipenv install
pipenv shell
```

3. Configure Environment Variables:The project uses a .env file to protect sensitive credentials.
- Locate the .env.dist file in the project root.
- Create a copy called .env.

```properties
cp .env.dist .env
```

- Edit the .env file and add your API Keys.
-----
## 📦 Project Architecture
 - settings.py: Uses pydantic-settings to validate and load the .env file. It's the "heart" of the configuration.
 - client.py: Contains the FindtagClientMT01 class (with MD5 signature logic) and the FindtagClientMT02 class (with header and pagination logic).
 - models.py: Defines the Pydantic schemas (TagData, ApiResponse) to ensure that output data is always standardized, regardless of the originating API.
 - main.py: Defines the FastAPI routes and the Factory logic to instantiate the correct client.
----
## ▶️ Executing the project                         

```properties
uvicorn main:app --reload
```
Access http://127.0.0.1:8000/docs to view the interactive documentation (Swagger).


-----