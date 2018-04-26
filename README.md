# Tracker
[Add Tracker to your server](https://discordapp.com/oauth2/authorize?client_id=439066525064757248&scope=bot&permissions=67234880)

Tracker is a discord bot infrastructure designed to track and post information.
Currently, there is 1 finished tracking module:
[osu! Tracker](#osu!)

## osu!
The osu! tracking module tracks information about user scores on the popular computer game, [osu!](https://osu.ppy.sh/). You can tell Tracker which players&apos; scores you&apos;d like to track, as well as how far into their top plays to check.

### Commands
`!track-osu <"user name" [limit]> ...`

Informs Tracker to track the specified osu! players&apos; scores in this channel.
- *user name* - specifies which player to track, the quotes are optional if the player&apos;s username has no spaces.
- *limit* - optional, specifies how many plays Tracker should look through before stopping. If empty, defaults to 100. Maximum is 100, minimum is 1.

`!untrack-osu <"user name"> ...`

Informs Tracker to stop tracking the specified osu! players&apos; scores in this channel.
- *user name* - specifies which player to stop tracking, the quotes are optional if the player&apos;s username has no spaces.

