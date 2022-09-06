from multiprocessing import Process
import defs

# defs.runServer spins a basic http server.
# This server will process a single request and exit.

# defs.authorise opens a web browser to login to fyers.
# Once authorised, fyers will redirect to our http server with the access token.
# Upon receiving a request, server updates the config.json with access token
# and other details.
#
# While defs.authorise waits for authorisation,
# we check for changes to config.json via its file modification date.
#
# if authorisation takes too long, we sent an empty request to the server
# which closes the server and exits.
#
# Here both defs.runServer and defs.authorise run on its own threads
# via multiprocessing.
# Both processes run in a single script making it user friendly.


p1 = Process(target=defs.runServer)

p2 = Process(target=defs.authorise)

p1.start()
p2.start()

p1.join()
p2.join()


