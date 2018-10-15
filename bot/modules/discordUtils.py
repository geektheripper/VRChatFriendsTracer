"""
Extra things to make the discord library nicer
"""

from discord import errors


async def safeSend(channel, text=None, embed=None):
    """
    Send a text / embed message (one or the other, not both) to a
    user, and if an error occurs, safely supress it
    On failure, returns:
        -1 : Nothing to send (text & embed are `None`)
        -2 : Forbidden
        -3 : HTTPException
        -4 : InvalidArgument
    On success returns what the channel.send method returns
    """
    try:
        if text:
            return await channel.send(text)
        elif embed:
            return await channel.send(embed=embed)
        else:
            return -1
    except errors.Forbidden:
        return -2  # API down, Message too big, etc.
    except errors.HTTPException:
        return -3  # No permission to message this channel
    except errors.InvalidArgument:
        return -4  # Invalid channel ID (channel deleted)
