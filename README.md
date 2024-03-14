# Workout Planner API

The Workout Planner API is a Flask-based RESTful web service designed to help users organize their workout routines, set fitness goals, and track their progress.

## Table of Contents

- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [API Endpoints](#api-endpoints)
  - [User Registration](#user-registration)
  - [User Login](#user-login)
  - [Workout Plans](#workout-plans)
  - [Fitness Goals](#fitness-goals)
  - [Workout Sessions](#workout-sessions)
- [Swagger Documentation](#swagger-documentation)
- [Issues](#issues)
- [Donation](#donation)

## Getting Started

### Prerequisites

Make sure you have the following installed:

- [Docker](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/Workout-Planner-API.git
   cd Workout-Planner-API

2. **Build the docker image:**

   ```bash
   docker build . -t flask:0.0.3

3. **Run the docker image:**
   ```bash
   docker run -p 5000:5000 flask:0.0.3

The API will be accessible at http://localhost:5000.

***Alternate Version:***

4. Install required modules (Flask, SQLAlchemy, etc.), pip install -r requirements.txt
5. Run app.py
6. In your web-browser access your localhost (127.0.0.1:8000).
7. If your localhost is taken by another project or service, you can modify last line of the project and add
   port = 9000. Ex : app.run(debug=True, port = 9000)


## API Endpoints

The Workout Planner API provides the following simple and intuitive endpoints:

- ### User Registration

  - **Endpoint:** `/register`
  - **Description:** Register a new user account.
  - **Example Request:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"name":"your_username","password":"your_password"}' http://localhost:8000/register
    ```

- ### User Login

  - **Endpoint:** `/login`
  - **Description:** Authenticate and obtain an access JWT token.
  - **Example Request:**
    ```bash
    curl -X GET -u "your_username:your_password" http://localhost:8000/login
    ```

- ### Workout Plans

  - **Create a Workout Plan**
    - **Endpoint:** `/workout-plans`
    - **Description:** Create a new workout plan.
    - **Example Request:**
      ```bash
      curl -X POST -H "Content-Type: application/json" -H "x-access-token: your_access_token" -d '{"workout_name":"Plan 1","frequency":"Weekly","goal":"Muscle Building","session_duration":60,"selected_exercises":[{"name":"Push-up","sets":3,"reps":10}]}' http://localhost:8000/workout-plans
      ```

  - **Get All Workout Plans**
    - **Endpoint:** `/workout-plans`
    - **Description:** Retrieve all workout plans for the authenticated user.
    - **Example Request:**
      ```bash
      curl -X GET -H "x-access-token: your_access_token" http://localhost:8000/workout-plans
      ```

  - **Get Single Workout Plan**
    - **Endpoint:** `/workout-plans/<int:workout_plan_id>`
    - **Description:** Retrieve details of a specific workout plan.
    - **Example Request:**
      ```bash
      curl -X GET -H "x-access-token: your_access_token" http://localhost:8000/workout-plans/1
      ```

  - **Delete Workout Plan**
    - **Endpoint:** `/workout-plans/<int:workout_plan_id>`
    - **Description:** Delete a specific workout plan.
    - **Example Request:**
      ```bash
      curl -X DELETE -H "x-access-token: your_access_token" http://localhost:8000/workout-plans/1
      ```

- ### Fitness Goals

  - **Create Fitness Goal**
    - **Endpoint:** `/fitness-goals`
    - **Description:** Set fitness goals, including exercise-specific details.
    - **Example Request:**
      ```bash
      curl -X POST -H "Content-Type: application/json" -H "x-access-token: your_access_token" -d '{"current_weight":70.5,"goal_weight":65.0,"exercises_goals":[{"name":"Squats","weight":100,"reps":12,"weight_goal":120,"reps_goal":15}]}' http://localhost:8000/fitness-goals
      ```

  - **Get All Fitness Goals**
    - **Endpoint:** `/fitness-goals`
    - **Description:** Retrieve all fitness goals for the authenticated user.
    - **Example Request:**
      ```bash
      curl -X GET -H "x-access-token: your_access_token" http://localhost:8000/fitness-goals
      ```

  - **Get Single Fitness Goal**
    - **Endpoint:** `/fitness-goals/<int:goal_id>`
    - **Description:** Retrieve details of a specific fitness goal.
    - **Example Request:**
      ```bash
      curl -X GET -H "x-access-token: your_access_token" http://localhost:8000/fitness-goals/1
      ```

  - **Delete Fitness Goal**
    - **Endpoint:** `/fitness-goals/<int:goal_id>`
    - **Description:** Delete a specific fitness goal.
    - **Example Request:**
      ```bash
      curl -X DELETE -H "x-access-token: your_access_token" http://localhost:8000/fitness-goals/1
      ```

- ### Workout Sessions

  - **Start Workout Mode**
    - **Endpoint:** `/workout-mode/start`
    - **Description:** Begin a workout mode for a specific workout plan.
    - **Example Request:**
      ```bash
      curl -X POST -H "Content-Type: application/json" -H "x-access-token: your_access_token" -d '{"workout_plan_id":1,"rest_time":30}' http://localhost:8000/workout-mode/start
      ```

  - **Complete Current Exercise**
    - **Endpoint:** `/workout-mode/start/complete`
    - **Description:** Mark the current exercise as completed and move to the next one.
    - **Example Request:**
      ```bash
      curl -X POST -H "Content-Type: application/json" -H "x-access-token: your_access_token" http://localhost:8000/workout-mode/start/complete
      ```

For more detailed information, refer to the ["Swagger Documentation"](#swagger-documentation)

## Swagger Documentation

To explore the detailed API documentation and interact with the Workout Planner API using Swagger UI, follow these steps:

### Prerequisites

Before accessing the Swagger Documentation, ensure you have the following:

1. **API Server Running:**
   - Make sure the Workout Planner API server is up and running.
   - If you haven't set up the server yet, refer to the ["Installation"](#installation) section in the README to get started.

2. **Access Token:**
   - Obtain an access token by registering and logging in as a user through the provided API endpoints.
   - Refer to the ["User Registration"](#user-registration) and ["User Login"](#user-login) sections for more details.

### Access Swagger Documentation

Once you have fulfilled the prerequisites, you can access the Swagger Documentation by navigating to:

[Swagger UI - Workout Planner API](http://localhost:8000/api/docs)

**For testing endpoints I highly suggest to use Postman** !


## Issues
If you encounter any issues, bugs, or have suggestions for improvement, I welcome your feedback. Here's how you can help:

1. **Check Existing Issues**: Before reporting a new issue, please check our [GitHub Issues](https://github.com/ggagua/workout-api/issues) to see if someone else has already reported the same problem or if there's an ongoing discussion about it.

2. **Create a New Issue**: If you can't find an existing issue that matches your problem or suggestion, feel free to [create a new issue](https://github.com/ggagua/workout-api/issues/new). Be as detailed as possible, including the steps to reproduce the issue, the expected behavior, and the actual behavior you observed.

3. **Include Screenshots**: If the issue is visual or related to the user interface, it's often helpful to include screenshots. You can upload them directly to the issue you create.

4. **Provide Context**: Describe the environment in which you encountered the issue, such as your operating system, browser, or any relevant software versions.

5. **Contribute to Solutions**: If you're technically inclined and want to contribute to resolving the issue, consider submitting a pull request. I am always open to collaboration from the community. 


## Donation

If you've found my Workout API useful and want to support its continued development and maintenance, you can make a donation. 

- [Support me on Buy Me a Coffee](https://www.buymeacoffee.com/ggagua)


---

Thank you for checking out the Workout Planner API. If you have any questions or need further details about the API endpoints, refer to the Swagger documentation available at `/api/docs`. For inquiries or issues, feel free to reach out at [ggagua.tech@gmail.com](mailto:ggagua.tech@gmail.com). This project was crafted for the choosing phase of Sweeft's Acceleration Program.



   
   
