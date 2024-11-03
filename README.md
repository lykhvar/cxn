# CXN - Connection

[![PyPI - Version](https://img.shields.io/pypi/v/cxn.svg)](https://pypi.org/project/cxn)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cxn.svg)](https://pypi.org/project/cxn)

-----

CXN (short for Connection) is a lightweight command-line tool created to verify connectivity between services. It aims to be as minimalistic as possible by reducing dependency conflicts and utilizing the existing Python environment on your system. The tool leverages pre-installed third-party Python packages to manage connection logic.

## Installation

```console
pip install cxn
```
### Arguments

- `provider`: The name of the third-party Python package that facilitates the connection.

_Note: CXN does not manage the installation of these third-party packages. Ensure that the required packages are installed in your Python environment._

### Options

- `-u`, `--url` (required): Specifies the connection URL for the provider.
- `-t`, `--terminate`: Exits with an error if the connection cannot be established.
- `-v`, `--version`: Displays the program's version number and exits.
- `-b`, `--backoff`: Enables exponential backoff for retrying connections indefinitely unless the `--retries` option is specified.
- `-r`, `--retries`: Specifies the number of retries before giving up. Works with both backoff and non-backoff modes. In backoff mode, defaults to indefinite retries if not specified; in non-backoff mode, defaults to a single attempt.

## Available Providers

You can list the available providers and their supported schemas by using the `-h` or `--help` option.

Currently, the supported providers are:

- **redis**: Supports `redis`
- **psycopg**: Supports `postgresql`
- **kombu**: Supports `amqp`

Stay tuned for more providers coming soon!

## Examples

Check connectivity to a service using a specific provider:

```bash
cxn --url redis://localhost:6379/0 kombu
```
```bash
cxn --url postgresql://user:password@localhost:5432/mydatabase?sslmode=disable psycopg
```
Check connectivity to a service using a specific provider with exponential backoff and unlimited retries:

```bash
cxn --url redis://localhost:6379/0 --backoff kombu
```
Check connectivity to a service with a specific number of retries in both backoff and non-backoff modes:

```bash
cxn --url postgresql://user:password@localhost:5432/mydatabase?sslmode=disable --retries 5 psycopg
```
```bash
cxn --url redis://localhost:6379/0 --backoff --retries 3 kombu
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or suggestions.

## License

`cxn` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
