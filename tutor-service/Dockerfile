# using my official python runtime as a parent image 

FROM python:3.14-slim

#prevents pythonfrom writing .pyc files and buffers output properly for logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#setting the working directory tutor-service
WORKDIR /app

#copy the the requirements file
COPY requirements.txt .


# installing the dependencies
RUN pip install --no-cahce-dir -r requirements.txt

#now copy the rest of the application
Copy . .

#command to run  the tutor service app 
CMD ["python" , "-m" , "pytest" , "tests/" , "-v" ]