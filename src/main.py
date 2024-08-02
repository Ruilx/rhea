#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.framework.dry.assets.about import __slogan__

import asyncio
import os
import pathlib

import click
from src.framework.dry.assets.ani_helper import slow_print
from src.framework.dry.config import Config
from src.framework.dry.logger import Logger, setup_loggers, LogLevel
from src.framework.dry.server import Server


def welcome_msg():
    asyncio.run(slow_print(__slogan__))


@click.command()
@click.option('-c', '--config', type=click.Path(exists=True), required=True)
@click.option('-l', '--log', type=click.Path(file_okay=True), multiple=True, default=['_stderr'])
@click.option('--log-level', type=click.Choice(LogLevel.keys()), default="DEBUG")
def main(config, log, log_level):
    setup_loggers(Logger(), log, log_level)
    welcome_msg()
    Logger().get_logger(__name__).info(f"Working directory: {os.getcwd()}")
    config = Config(pathlib.Path(config))
    config.set_setting('log', {'log': log, 'log_level': log_level})
    Server(config).run()


if __name__ == '__main__':
    main()
