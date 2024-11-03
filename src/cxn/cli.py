import argparse
import logging
import sys
import time
from typing import Optional

from cxn.__about__ import __version__
from cxn.providers import Provider, registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cxn")


def main() -> None:
    providers = "\n".join(
        f"* {name} - {', '.join(provider.schemas)}"
        for name, provider in registry.providers.items()
    )
    parser = argparse.ArgumentParser(
        description="A CLI tool for verifying connectivity between services",
        epilog=f"Available providers:\n{providers}",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "provider",
        type=str,
        help="The third-party package that handles the connection",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        required=True,
        help="The connection URL for the provider",
    )
    parser.add_argument(
        "-t",
        "--terminate",
        action="store_true",
        help="Exit the program if no connection can be established",
    )
    parser.add_argument(
        "-b",
        "--backoff",
        action="store_true",
        help="Enable exponential backoff when retrying connections",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=0,
        help="Number of retries before giving up",
    )

    args: argparse.Namespace = parser.parse_args()
    retries: int = args.retries
    provider: Provider = registry.get(args.provider)(args.url)
    hostname: Optional[str] = provider.uri.hostname
    scheme: Optional[str] = provider.uri.scheme

    if args.backoff and not args.retries:
        retries = float("inf")

    code: int = 0
    attempt: int = 0
    delay: int = 0
    logfunc = logger.info

    if args.terminate:
        code = 1
        logfunc = logger.error

    while attempt <= retries:
        logger.info(f"Testing connection to {hostname} using {scheme} scheme")
        attempt += 1

        if provider.connection:
            logger.info("Ok")
            code = 0
            break

        logfunc("No connection")

        if args.backoff and attempt <= retries:
            wait: int = 2**delay
            logger.warning(f"Retrying in {wait} seconds...")
            time.sleep(wait)
            delay += 1
        else:
            break

    sys.exit(code)


if __name__ == "__main__":
    main()
