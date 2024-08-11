# Use an official Ubuntu as a parent image
FROM ubuntu:latest

# Set the maintainer label
LABEL maintainer="your_email@example.com"

# Update the package list and install necessary packages
RUN apt-get update && apt-get install -y \
    software-properties-common \
    apt-transport-https \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Java
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk

# Set JAVA_HOME environment variable
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64
ENV PATH $JAVA_HOME/bin:$PATH

# Install Maven
RUN apt-get update && \
    apt-get install -y maven

# Verify installations
RUN java -version
RUN mvn -version

# Set the working directory
WORKDIR /usr/src/app

RUN apt-get install -y vim
RUN apt-get install -y python3
RUN apt-get update
RUN apt install -y python3-pip
RUN apt install -y python3.12-venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install JPype1

# wget releases

# Copy the current directory contents into the container
COPY . .

# Run the application
CMD ["bash"]
