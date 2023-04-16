# FROM continuumio/miniconda3:4.10.3

# WORKDIR /code
# COPY ./backend /code/
# COPY ./backend/environment.yml /code/environment.yml

# # Create the Conda environment from environment.yml file
# RUN conda env create -f environment.yml

# # Activate the environment
# RUN echo "source activate mtdgame" > ~/.bashrc
# ENV PATH /opt/conda/envs/mtdgame/bin:$PATH

# COPY ./docker/django/django.sh /scripts/django.sh
# RUN chmod +x /scripts/django.sh
# # RUN python3 manage.py migrate
# RUN /opt/conda/envs/mtdgame/bin/python manage.py migrate

FROM python:3.9.6-slim-buster
WORKDIR /code
COPY ./backend /code/
COPY ./docker/django/django.sh /scripts/django.sh
RUN chmod +x /scripts/django.sh
COPY ./backend/requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python3 manage.py migrate
