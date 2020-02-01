import math

# Define help message command
def help_message(role, p):
    to_send = ''
    if role in ['admin', 'head-moderator', 'moderator', 'security', 'recruit']:
        to_send += 'Commands:\n'
        to_send += '`-------Misc-------`\n'
        to_send += '`' + p + 'version` : prints current bot version\n'
        to_send += '`' + p + 'ping` : pong!\n'
        to_send += '`' + p + 'help` : you just used it!\n`-------Fun!-------`\n'
        to_send += '`' + p + 'owo` : what\'s this?\n'
        to_send += '`' + p + 'bignut` : █▀█ █▄█ ▀█▀\n'
        to_send += '`' + p + 'seal` : What the fuck did you just fucking say about me, you little bitch?\n'
        to_send += '`----Moderation----`\n'
        to_send += '`' + p + 'warn [type] [user] [reason (for custom type)]` : DMs user to notify of given type of warning\n'
        to_send += 'Valid `warn` types: `nsfw`, `hitler`, `status`, `name`, `custom`\n'
        if role != 'recruit':
            to_send += '`' + p + 'reminder [duration in seconds] [message]` : sends a reminder after the given number of seconds\n'
            to_send += '`' + p + 'kennel [user] [optional: reason]` : removes all roles, kennels user and DMs them to notify\n'
            to_send += '`' + p + 'mute [user] [optional: reason]` : removes all roles and mutes user\n'
        if role != 'recruit' and role != 'security':
            to_send += '`' + p + 'role [user] [list of roles]` : roles separated by commas, toggles unless + or - specified before a role\n'
        if role == 'admin' or role == 'head-moderator':
            to_send += '`------Admins------`\n'
            to_send += '`' + p + 'test` : toggles test mode (when running two instances, test mode will prevent one instance from logging joins/leaves)\n'
            to_send += '`' + p + 'log [channel] [optional: month] [optional: year]` : logs given channel for given month or last full month if no month is specified\n'
            to_send += '`' + p + 'updateprefix [new_prefix]` : changes prefix to given prefix (max 3 characters)\n'
            to_send += '`' + p + 'reminders` : outputs reminders.txt file for debugging\n'
            to_send += '`protobot reset prefix` : reset prefix to default'
    return to_send


# Load permissions from permissions.txt
role_dict = {}
role_list = []
with open('permissions.txt', 'r+') as roles:
    lines = roles.readlines()
for line in lines:
    to_dict = line.strip('\n').split(':')
    role_list.append(to_dict[0])
    role_dict[to_dict[0]] = {}
    role_dict[to_dict[0]]['allow'] = [c for c in to_dict[1].split(' ') if c[0] != '!']
    role_dict[to_dict[0]]['deny'] = [c[1:] for c in to_dict[1].split(' ') if c[0] == '!']

def duration_text(s):
    m = int(math.floor(s / 60)) % 60
    h = int(math.floor(s / 3600)) % 24
    d = int(math.floor(s / 86400))
    if d == 1:
        dtext = '1 day'
    elif d > 1:
        dtext = str(d) + ' days'
    else:
        dtext = ''
    if h == 1:
        htext = '1 hour'
    elif h > 1:
        htext = str(h) + ' hours'
    else:
        htext = ''
    if m == 1:
        mtext = '1 minute'
    elif m > 1:
        mtext = str(m) + ' minutes'
    else:
        mtext = ''
    textlist = []
    if dtext:
        textlist.append(dtext)
    if htext:
        textlist.append(htext)
    if mtext:
        textlist.append(mtext)
    if textlist:
        fulltext = ', '.join(textlist) + ' ago'
    else:
        fulltext = 'just now'
    return fulltext


# Define command to check permissions for a role
def check_permission(role, permissions, command):
    allow = permissions[role]['allow']
    deny = permissions[role]['deny']
    if command in deny:
        return False
    elif allow[0] == 'all':
        return True
    elif command in allow:
        return True
    else:
        return False

owo = '''Rawr x3 nuzzles how are you pounces on you you're so warm o3o notices you have a bulge o: someone's happy ;) nuzzles your necky wecky~ murr~ hehehe rubbies your bulgy wolgy you're so big :oooo rubbies more on your bulgy wolgy it doesn't stop growing ·///· kisses you and lickies your necky daddy likies (; nuzzles wuzzles I hope daddy really likes $: wiggles butt and squirms I want to see your big daddy meat~ wiggles butt I have a little itch o3o wags tail can you please get my itch~ puts paws on your chest nyea~ its a seven inch itch rubs your chest can you help me pwease squirms pwetty pwease sad face I need to be punished runs paws down your chest and bites lip like I need to be punished really good~ paws on your bulge as I lick my lips I'm getting thirsty. I can go for some milk unbuttons your pants as my eyes glow you smell so musky :v licks shaft mmmm~ so musky drools all over your cock your daddy meat I like fondles Mr. Fuzzy Balls hehe puts snout on balls and inhales deeply oh god im so hard~ licks balls punish me daddy~ nyea~ squirms more and wiggles butt I love your musky goodness bites lip please punish me licks lips nyea~ suckles on your tip so good licks pre of your cock salty goodness~ eyes role back and goes balls deep mmmm~ moans and suckles'''