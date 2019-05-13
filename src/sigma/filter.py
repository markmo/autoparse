"""
Filters records from a backend log aggregator such as Elasticsearch that contain
a signature indicative of potential malicious behaviour.

Dependency on rules within the Neo23x0/sigma source code repository. By default,
the sigma source location is expected under the `src` folder within the user's
home directory.
::

    cd ~
    git clone https://github.com/Neo23x0/sigma.git

"""

import itertools
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

import yaml
from sigma.backends.exceptions import BackendError, FullMatchError, NotSupportedError, PartialMatchError
from sigma.parser.collection import SigmaCollectionParser
from sigma.parser.exceptions import SigmaCollectionParseError, SigmaParseError

DEFAULT_RULES_DIR = Path.home() / 'src/sigma/rules'
DEFAULT_OUTPUT_DIR = Path('/tmp/autoparse')
DEFAULT_BACKEND = 'es-qs'  # Elasticsearch Query Strings

logger = logging.getLogger(__name__)


def all_iter(path):
    for sub in path.iterdir():
        if sub.name.startswith('.'):
            continue

        if sub.is_dir():
            yield from all_iter(sub)
        else:
            yield sub


def get_inputs(paths):
    # noinspection PyUnresolvedReferences
    return list(itertools.chain_from_iterable([list(all_iter(Path(p))) for p in paths]))


def run(constants):
    output_dir = constants.get('output_dir', DEFAULT_OUTPUT_DIR)
    rules_dir = constants.get('rules_dir', DEFAULT_RULES_DIR)
    backend = constants.get('backend', DEFAULT_BACKEND)
    filename = output_dir / 'query'
    try:
        out = open(filename, 'w', encoding='utf-8')
    except (IOError, OSError) as e:
        print('Failed to open output file "%s": %s' % (str(filename), str(e)), file=sys.stderr)
        sys.exit(1)

    error = 0
    inputs = get_inputs(rules_dir)
    for path in inputs:
        logger.debug('Processing Sigma rule "%s"' % path)
        f = None
        # noinspection PyUnresolvedReferences
        try:
            f = path.open(encoding='utf-8')
            sigma_parser = SigmaCollectionParser(f)
            results = sigma_parser.generate(backend)
            for result in results:
                print(result, file=out)
        except OSError as e:
            print('Failed to open Sigma rule file "%s": %s' % (path, str(e)), file=sys.stderr)
            error = 5
        except (yaml.parser.ParseError, yaml.scanner.ScannerError) as e:
            print('Sigma rule file "%s" is invalid YAML: %s' % (path, str(e)), file=sys.stderr)
            error = 3
            sys.exit(error)
        except (SigmaParseError, SigmaCollectionParseError) as e:
            print('Sigma parse error in "%s": %s' % (path, str(e)), file=sys.stderr)
            error = 4
            sys.exit(error)
        except NotSupportedError as e:
            print('The Sigma rule requires a feature that is not supported by the target system:',
                  str(e), file=sys.stderr)
            error = 9
            sys.exit(error)
        except BackendError as e:
            print('Backend error in "%s": %s' % (path, str(e)), file=sys.stderr)
            error = 8
            sys.exit(error)
        except NotImplementedError as e:
            print('An unsupported feature is required for this Sigma rule "%s": %s' % (path, str(e)), file=sys.stderr)
            error = 42
            sys.exit(error)
        except PartialMatchError as e:
            print('Partial field match error:', str(e), file=sys.stderr)
            error = 80
            sys.exit(error)
        except FullMatchError as e:
            print('Full field match error:', str(e), file=sys.stderr)
            error = 90
            sys.exit(error)
        finally:
            # noinspection PyBroadException
            try:
                f.close()
            except Exception:
                pass

    result = backend.finalize()
    if result:
        print(result, file=out)

    out.close()
    sys.exit(error)


if __name__ == '__main__':
    # read args
    parser = ArgumentParser(description='Filter logs from Elasticsearch')
    parser.add_argument('--out-dir', dest='output_dir', type=str, help='output directory')
    parser.add_argument('--rules-dir', dest='rules_dir', type=str, help='Sigma rules directory')
    parser.add_argument('--backend', dest='backend', type=str, help='backend log storage system')
    args = parser.parse_args()

    run(vars(args))
