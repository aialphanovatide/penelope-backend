Migration with Docker:

### docker-compose run web alembic revision --autogenerate -m "Description of the change"
### docker-compose run web alembic upgrade head


Creating an auto migrations
  alembic revision --autogenerate -m "Auto migrations"
  alembic upgrade head


  downgrade to prev revisition
  alembic downgrade -1
   or 
  alembic current
  alembic downgrade <previous_revision>

