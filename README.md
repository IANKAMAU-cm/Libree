# Library Management System

## Description

The Library Management System is a web-based application designed to manage a library's catalog of books and users. The system allows for librarian registration and login, and facilitates the management of books, including adding, editing, and deleting entries. Users can interact with the system through a web interface that provides functionality for book inventory management and user authentication.

## Features

- Librarian registration and login
- Book management (add, edit, delete)
- SQLite database for storage
- Dockerized setup for easy deployment

## Getting Started

To get started with this project, follow the instructions below:

### Prerequisites

- Docker
- Docker Compose

### Cloning the Repository

1. **Clone the repository:**

   ```sh
   git clone https://github.com/IANKAMAU-cm/Libree.git

### Navigate to the project directory:
cd Libree

### Build and start the Docker containers:
docker-compose up --build

### Access the application:
The application will be available at http://localhost:5000. You can access the web interface from your browser.

### Stopping the Docker Container
To stop the containers gracefully, press Ctrl + C in the terminal where docker-compose up is running.
Alternatively, you can use the following command to stop and remove the containers:
docker-compose down

### Configuration

Database: The system uses an SQLite database stored in the instance directory. The database file is mounted as a Docker volume to persist data.

Configuration File: The configuration settings for the Flask application are located in config.py. You can adjust the settings as needed.

### Development

If you need to make changes or contribute to the development:

Make your changes in the source code.

Build the Docker image again using:

docker-compose up --build

Test your changes locally.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
