"""
Configuration files manager
"""
from typing import TextIO, Any, Mapping

import click
import jschon
import tomlkit

from paths import CONFIG_SCHEMA_PATH


def get_config_from_file(config_IO: TextIO) -> dict:
    """
    Parse the configuration
    :param config_IO: configuration reader
    :return the configuration in a dict
    """
    jschon.create_catalog('2020-12')
    schema = jschon.JSONSchema.loadf(CONFIG_SCHEMA_PATH)
    config_dict = tomlkit.load(config_IO)
    config_validity = schema.evaluate(jschon.JSON(config_dict))
    if not config_validity.valid:
        details: Mapping[str, Any] = config_validity.output('basic')
        error: Mapping[str, str]
        for error in details['errors']:
            click.echo(click.style(
                f'In instance `{error["instanceLocation"]}`, in schema `{error["keywordLocation"]}` : {error["error"]}',
                bg='red',
                fg='white'
            ))

        raise click.ClickException('Configuration is not valid')
    return config_dict


class MyString(click.types.StringParamType):
    """Like click.types.STRING, but with a way to check length"""
    NO_MAX_VALUE: int = -1

    def __init__(self, minlen: int = 0, maxlen: int = NO_MAX_VALUE):
        if minlen < 0:
            raise ValueError('minlen is negative')

        if maxlen < 0 and maxlen != self.NO_MAX_VALUE:
            raise ValueError('maxlen is negative')

        self.minlen = minlen
        self.maxlen = maxlen

    def convert(self, *args, **kwargs) -> Any:
        value = super(MyString, self).convert(*args, **kwargs)

        if len(value) < self.minlen:
            raise click.ClickException('Value too small')

        if self.maxlen != self.NO_MAX_VALUE and len(value) > self.maxlen:
            raise click.ClickException('Value too large')

        return value
