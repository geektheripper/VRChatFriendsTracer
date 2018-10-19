#coding=utf-8
"""
Embeds and functions for dealing with errors
"""

from discord import Embed
import logging
import sys

from bot.modules.colours import hexColours

logger = logging.getLogger(__name__)

nextLaunchErrorEmbed = Embed(title="Error", description="An launchInfoEmbed error occurred, contact <@464362793009676288>", color=hexColours["errorRed"])
apiErrorEmbed = Embed(title="Error", description="An API error occurred, contact <@464362793009676288>", color=hexColours["errorRed"])
generalErrorEmbed = Embed(title="Error", description="An error occurred, contact <@464362793009676288>", color=hexColours["errorRed"])
dbErrorEmbed  = Embed(title="Error", description="A database error occurred, contact <@464362793009676288>", color=hexColours["errorRed"])

def fatalError(message):
    logger.critical(message)
    sys.exit(-1)
