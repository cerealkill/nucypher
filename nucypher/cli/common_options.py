from collections import namedtuple
import functools

import click

from nucypher.cli.types import (
    EIP55_CHECKSUM_ADDRESS,
    EXISTING_READABLE_FILE,
    NETWORK_PORT,
    )


option_checksum_address = click.option(
    '--checksum-address', help="Run with a specified account", type=EIP55_CHECKSUM_ADDRESS)

option_config_file = click.option(
    '--config-file', help="Path to configuration file", type=EXISTING_READABLE_FILE)

option_config_root = click.option(
    '--config-root', help="Custom configuration directory", type=click.Path())

def option_controller_port(default=None):
    return click.option(
        '--controller-port',
        help="The host port to run Alice HTTP services on",
        type=NETWORK_PORT,
        default=default)

option_dev = click.option('--dev', '-d', help="Enable development mode", is_flag=True)

option_db_filepath = click.option(
    '--db-filepath', help="The database filepath to connect to", type=click.STRING)

def option_discovery_port(default=None):
    return click.option(
        '--discovery-port',
        help="The host port to run node discovery services on",
        type=NETWORK_PORT,
        default=default)

option_dry_run = click.option(
    '--dry-run', '-x', help="Execute normally without actually starting the node", is_flag=True)

option_etherscan = click.option(
    '--etherscan/--no-etherscan', help="Enable/disable viewing TX in Etherscan")

# Defaults to None since it can be overridden by the config file
option_federated_only = click.option(
    '--federated-only', '-F', help="Connect only to federated nodes", is_flag=True, default=None)

option_force = click.option('--force', help="Don't ask for confirmation", is_flag=True)

option_geth = click.option('--geth', '-G', help="Run using the built-in geth node", is_flag=True)

# TODO: Make True by default or deprecate - see #1439
option_hw_wallet = click.option('--hw-wallet/--no-hw-wallet')

def option_label(required:bool = False):
    return click.option(
        '--label',
        help="The label for a policy",
        type=click.STRING,
        required=required)

option_light = click.option('--light', help="Indicate that node is light", is_flag=True)

def option_message_kit(required:bool = False):
    return click.option(
        '--message-kit',
        help="The message kit unicode string encoded in base64",
        type=click.STRING,
        required=required)

option_m = click.option('--m', help="M-Threshold KFrags", type=click.INT)

option_min_stake = click.option(
    '--min-stake',
    help="The minimum stake the teacher must have to be a teacher",
    type=click.INT,
    default=0)

option_n = click.option('--n', help="N-Total KFrags", type=click.INT)

option_network = click.option('--network', help="Network Domain Name", type=click.STRING)

# Defaults to None since it can be overridden by the config file
option_poa = click.option('--poa', help="Inject POA middleware", is_flag=True, default=None)

def option_policy_encrypting_key(required:bool = False):
    return click.option(
        '--policy-encrypting-key',
        help="Encrypting Public Key for Policy as hexadecimal string",
        type=click.STRING,
        required=required)

def option_provider_uri(default=None, required:bool = False):
    return click.option(
        '--provider', 'provider_uri',
        help="Blockchain provider's URI i.e. 'file:///path/to/geth.ipc'",
        type=click.STRING,
        required=required,
        default=default)

option_registry_filepath = click.option(
    '--registry-filepath', help="Custom contract registry filepath", type=EXISTING_READABLE_FILE)

option_staking_address = click.option(
    '--staking-address', help="Address of a NuCypher staker", type=EIP55_CHECKSUM_ADDRESS)

option_teacher_uri = click.option(
    '--teacher', 'teacher_uri',
    help="An Ursula URI to start learning from (seednode)",
    type=click.STRING)


def group_options(option_class, **options):

    argnames = sorted(list(options.keys()))
    decorators = list(options.values())

    if isinstance(option_class, str):
        option_name = option_class
        option_class = namedtuple(option_class, argnames)
    else:
        option_name = option_class.__option_name__

    def _decorator(func):

        @functools.wraps(func)
        def wrapper(**kwargs):
            to_group = {}
            for name in argnames:
                if name not in kwargs:
                    raise ValueError(
                        f"When trying to group CLI options into {option_name}, "
                        f"{name} was not found among arguments")
                to_group[name] = kwargs[name]
                del kwargs[name]

            kwargs[option_name] = option_class(**to_group)
            return func(**kwargs)

        for dec in decorators:
            wrapper = dec(wrapper)

        return wrapper

    return _decorator
