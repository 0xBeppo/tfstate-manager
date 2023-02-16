# Terraform State Manager

The Terraform State Manager is a Python tool for managing your Terraform infrastructure. It downloads a Terraform project from a Git repository and compares the state of the resources in your `tfstate` file with their actual state in the cloud. If there are any differences, it updates or removes a resource from the state of the resources in the `tfstate` file to match their actual state.

## Requirements for running locally

* Python 3.x
* Terraform
* Git
* AWS cli

## Installation

1. Clone this repository to your local machine.
2. Install the required Python packages with `pip install -r requirements.txt`.
3. Ensure Terraform and Git are installed on your machine.
4. Ensure that you have already AWS credentials on your machine

## Usage

### Running Locally

1. Run the script with `python main.py [<delete|update>] <url>`.

### Running in a Docker Container

1. Build the Docker container by running `docker build -t terraform-state-manager .` in the project directory.
2. Run the container with the appropriate environment variables by executing the following command:

```
docker run
-e AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
-e AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
-e AWS_DEFAULT_REGION=<your-aws-region>
terraform-state-manager python main.py [<delete|update>] <url>
```
