# Specify Playground

This project is designed to experiment with the Specify methodology in a controlled environment. It includes various specifications and example tests to validate the methodologies being explored.

## Project Structure

- **src/**: Contains the source code for the playground.
  - **playground/**: Holds the main specification and example tests.
    - `demo.specify`: The main specification file defining the experiments.
    - **examples/**: Contains example tests for the specifications.
      - `example.spec.ts`: Example tests validating the methodologies.
  - **lib/**: Utility functions and types used throughout the playground.
    - `index.ts`: Exports helper functions for tests and specifications.
  - `index.ts`: Entry point for the playground, initializing the environment.

- **specs/**: Documentation specific to the specifications.
  - `README.md`: Explains the methodologies and usage of the .specify files.

- **tests/**: Contains unit tests for the playground functionality.
  - `playground.test.ts`: Unit tests ensuring specifications behave as expected.

- **scripts/**: Scripts for running the playground environment.
  - `run-playground.sh`: Script to set up and execute the playground.

- **.gitignore**: Specifies files and directories to be ignored by Git.

- **package.json**: Configuration file for npm, listing dependencies and scripts.

- **tsconfig.json**: TypeScript configuration file specifying compiler options.

## Getting Started

To get started with the Specify Playground, follow these steps:

1. Clone the repository.
2. Install the dependencies using `npm install`.
3. Run the playground using the provided script: `./scripts/run-playground.sh`.

## Usage

You can define your own specifications in the `src/playground/demo.specify` file and create corresponding tests in the `src/playground/examples/example.spec.ts` file. The playground is designed to be flexible and allow for easy experimentation with different methodologies.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or suggestions.