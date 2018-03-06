import argparse
import bjoern
import logging
import sys

logger = logging.getLogger(__name__)


def run_bjoern(args):
    from app import app
    logger.info('Starting bjoern web server')
    bjoern.run(app, args.host, args.port)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', dest='host', default='0.0.0.0')
    parser.add_argument('--port', dest='port', type=int, default=80)

    args = parser.parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run_bjoern(args)


if __name__ == '__main__':
    main()
