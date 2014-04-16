class ServerInfo:

    # I have used the defaults specified by RFC1459 here
    UserModes = 'iosw'
    ChannelListModes = 'b'
    ChannelSetArgsModes = 'l'
    ChannelSetUnsetArgsModes = 'k'
    ChannelNormalModes = 'imnpst'

    Statuses = {'o': '@', 'v': '+'}
    StatusesReverse = {'@': 'o', '+': 'v'}

    ChannelTypes = '#'
