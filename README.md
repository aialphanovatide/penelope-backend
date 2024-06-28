# Penelope

This project is a Flask application with PostgreSQL database, containerized using Docker and Docker Compose. It uses Alembic for database migrations.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Database Migrations](#database-migrations)
- [Useful Commands](#useful-commands)

## Prerequisites

Ensure you have the following installed on your system:

- Docker
- Docker Compose

## Setup

1. Clone this repository:

```console
git clone <repository-url>
```

```console
cd <project-directory>
```

2. Create a `.env` file in the project root and add necessary environment variables:

- FLASK_APP=run.py

- FLASK_ENV=development

- DATABASE_URL=postgresql://user:password@db:5432/dbname

## Running the Application

To start the application, run:

```console
docker-compose up --build
```

The application should now be running at `http://localhost:5000`.

To stop the application, use:

```console
docker-compose down
```

## Database Migrations

This project uses Alembic for database migrations. Here are some useful commands:

### Creating a New Migration

To create a new migration:

```console
docker-compose run web alembic revision --autogenerate -m "Description of the change"
```

### Applying Migrations

To apply all pending migrations:

```console
docker-compose run web alembic upgrade head
```

### Creating Auto Migrations

To create and apply auto migrations:

```console
docker-compose run web alembic revision --autogenerate -m "Auto migrations"
```

```console
docker-compose run web alembic upgrade head
```

### Downgrading Migrations

To downgrade to the previous revision:

```console
docker-compose run web alembic downgrade -1
```

Or to downgrade to a specific revision:


```console
docker-compose run web alembic current
```

```console
docker-compose run web alembic downgrade <previous_revision>
```

## Useful Commands

Here are some additional useful commands:

- To view current migration version:

```console
docker-compose run web alembic current
```

- To view migration history:

```console
docker-compose run web alembic history
```

- To access the PostgreSQL database:

```console
docker-compose exec db psql -U <username> -d <dbname>
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

This README provides a comprehensive guide for setting up, running, and managing your Flask PostgreSQL Docker project. It includes sections on prerequisites, setup, running the application, database migrations, and useful commands. You may want to customize it further based on your specific project requirements and add any additional sections that might be relevant.
