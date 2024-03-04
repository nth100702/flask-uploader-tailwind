# Flask file uploader web server with OneDrive integration

Only local server can call /auth and /upload endpoints => OneDrive upload using MSGraph API

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

## With Docker
  
  ```bash
  docker build -t flask-uploader .
  docker run -p 0:8080 -d flask-uploader
  ```

## Endpoints

### /auth

**GET**: Local server returns access_token obtained from MS Graph API via Auth Code Flow (OAuth2.0)

### /upload

**POST**: Users upload file to local server, all file trafers will be chunked before sending to local

### /

**GET**: Upload page (client-side), Flask form

## Configuration for flask app

Can be found in `config.py` file
