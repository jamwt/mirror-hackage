A script for mirroring Haskell's "Hackage" package repository.

Mirroring Hackage is useful for both leveraging local bandwidth
as well as being robust against the public Hackage going down while
you're doing critical builds/deployments.

It's written in Python 2 and uses the requests library found at
http://python-requests.org .

It is crash-safe and it resumes long synchronizations.  It treads
lightly on the upstream server and uses checksums to make sure it
has processed all packages in the upstream log.

Modify the `remote-repo:` entry in `~/.cabal/config` to point machines
to your local mirror.

*Note: expect to devote 10-15GB to your Hackage mirror as of 2012-08*
