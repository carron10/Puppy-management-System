# Puppy Management System

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
  - [Backend](#backend)
- [Usage](#usage)
  - [Run](#run)
- [Project Structure](#project-structure)
- [Model Training](#model-training)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This application provides a user-friendly platform to manage your furry friends. It caters to dog owners with puppies under 21 days old, a crucial period for monitoring their health.The **Puppy Management System** is a web application developed using Flask that helps users manage the health of their puppies. Users can register and log in to the system, add their puppies and their parents, and record daily health metrics such as temperature and weight. The system uses a Machine Learning (ML) model to analyze these metrics and determine if a puppy requires veterinary attention, monitoring, or is in good health.

## Features

-User Login/Registration: Securely creates accounts for managing puppy data.
-Puppy and Parent Information: Add details about your adorable puppies and their parents for reference.
-Daily Records: Add and Track your puppy's weight and temperature, essential health indicators.
-ML-Powered Health Assessment: A trained AI model analyzes daily records to determine your puppy's well-being, suggesting veterinary attention, monitoring, or reassurance based on the analysis.

## Installation

### Backend

1. Go to the folder where you have saved this project.

2. Create a virtual environment:

    ```bash
    python -m venv venv
    ```

3. Activate the virtual environment:

    - On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```

    - On Windows:

        ```bash
        venv\Scripts\activate
        ```

4. Install dependencies from the requirements file:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Run

To run this project, follow these steps:

1. Run the application:

    ```bash
    python run.py
    ```

2. Open your web browser and go to:

    ```url
    http://127.0.0.1:5000
    ```

## Project Structure

Puppy-Management-System/
├── app/
│ ├── static/
│ ├── templates/
│ ├── init.py
│ ├── models.py
│ ├── routes.py
│ ├── forms.py
│ └── utils.py
├── ml/
│ ├── model.pkl
├── venv/
├── run.py
├── requirements.txt
└── README.md



## Model Training

The ML models used to determine the health status of the puppies is trained using historical data of puppy health metrics. These models are located in `ml/` directory.


## License

This project is licensed under the Apache License. See the [LICENSE](LICENSE) file for details.
