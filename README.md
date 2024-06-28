# Testing Conversational Assistants

## Overview

This repository contains the source code and resources used in the blog post titled "[Testing Conversational Assistants Using BDD](https://www.equalexperts.com/blog/ai/how-to-test-conversational-assistants-using-behaviour-driven-development/)". The aim of this project is to provide a practical example to accompany the concepts and solutions discussed in the blog post.

## Disclaimer

Please note that the code contained in this repository is not intended for production use. It has been developed for demonstration purposes to support the content of the associated blog post. As such, it may lack the robustness, error handling, and security features required for a production environment. Users are encouraged to use this code as a learning tool and to apply best practices when adapting or extending it for their own use cases.

## Installation

### Prerequisites

This project requires Python 3.8 or later. If you don't have Python installed, you can download it from the [official website](https://www.python.org/downloads/).

### Clone the Repository

To clone the repository, run the following command:

```bash
git clone git@github.com:EqualExperts/agents-behave.git
```

### Navigate to the project directory


```bash
cd agents-behave
```

### (Optional) Create a virtual environment

It's a good practice to use a virtual environment to avoid conflicts between project dependencies. To create a virtual environment, run:

```bash
python -m venv .venv
```

### Install the dependencies

This project uses [Poetry](https://python-poetry.org/) to manage dependencies. To install the dependencies, run:

```bash
poetry install
```

### Activate the virtual environment

If you created a virtual environment, activate it by running:

```bash
source .venv/bin/activate
```

### Set up the environment variables

```bash
source .env
```

### Run the BDD tests

To run the BDD tests, run:

```bash
cd hotel_reservations
behave
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
