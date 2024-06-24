# FastAPI LINE Bot with Gemini AI and Firebase Integration

This project is a FastAPI application that integrates with LINE Messaging API, Gemini AI, and Firebase to handle various types of messages and provide intelligent responses.

## Features

- **Health Check Endpoint**: Simple endpoint to check if the service is running.
- **LINE Webhook Handler**: Handles incoming messages from LINE and responds accordingly.
- **Gemini AI Integration**: Uses Gemini AI to process and generate responses based on the content of the messages.
- **Firebase Integration**: Stores and retrieves chat history from Firebase.

## Prerequisites

- Python 3.7+
- LINE Messaging API account
- Gemini AI API key
- Firebase project
- .env file with the following environment variables:
  - `API_ENV`
  - `LINE_CHANNEL_SECRET`
  - `LINE_CHANNEL_ACCESS_TOKEN`
  - `LOG`
  - `FIREBASE_URL`
  - `GEMINI_API_KEY`
  - `OPEN_API_KEY`

## Installation

1. Clone the repository:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add the required environment variables.

## Usage

1. Run the FastAPI application:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8080 --reload
    ```

2. The application will start and listen for incoming requests on the specified port.

## Endpoints

- **GET /health**: Health check endpoint to verify if the service is running.
- **POST /webhooks/line**: Webhook endpoint to handle incoming messages from LINE.

## Environment Variables

- `API_ENV`: Set to `production` or `develop`.
- `LINE_CHANNEL_SECRET`: Your LINE channel secret.
- `LINE_CHANNEL_ACCESS_TOKEN`: Your LINE channel access token.
- `LOG`: Logging level (default is `WARNING`).
- `FIREBASE_URL`: Your Firebase database URL.
- `GEMINI_API_KEY`: Your Gemini AI API key.
- `OPEN_API_KEY`: Your Open Data API key.

## Logging

The application uses Python's built-in logging module. The log level can be set using the `LOG` environment variable.

## License

This project is licensed under the MIT License.