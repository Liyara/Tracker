# Tracker
Tracker is a discord bot infrustructure designed to track and post information.
Currently, there is 1 finished tracking module:
[osu! Tracker](#osu!)

## osu!
The osu! tracking module tracks information about user scores, you can tell Tracker which players&apos; scores you&apos;d like to track, as well as how far into their top plays to check.

### Commands
`!track-osu <"user name" [limit]> ...`

Informs Tracker to track the specified osu! players&apos; scores in this channel.
- *user name* - specifies which player to track, the quotes are optional if the player&apos;s username has no spaces.
- *limit* - optional, specifies how many plays Tracker should look through before stopping. If empty, defaults to 100. Maximum is 100, minimum is 1.

`!untrack-osu <"user name">`

Informs Tracker to stop tracking the specified osu! players&apos; scores in this channel.
- *user name* - specifies which player to stop tracking, the quotes are optional if the player&apos;s username has no spaces.

