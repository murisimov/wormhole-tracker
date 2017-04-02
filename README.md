EVE Online star system tracker
---
_Draws your route in real time._
_Can be pretty useful in the Darkest Depths of Deadly W-space._

---

---

### How do I use this service?
- Use signin button to login via SSO.
- Press "Track" and you're good to go.

---

---

### Can I use it as standalone application?

---
Sure, just follow the instructions below.

---
#### Installation

---

- First of all you need to have a dedicated IP address that CCP can redirect your users to after authentication. [VPS](https://en.wikipedia.org/wiki/Virtual_private_server) usually have it, so it can be a nice idea to rent one (it's about 5$/mo).

- Install python3.6:
    - [CentOS 7](http://www.codeghar.com/blog/install-latest-python-on-centos-7.html)
    - [Ubuntu 14.04/16.04/16.10](http://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get)
    - [Building from source](https://docs.python.org/3/using/unix.html) (Please consider use `make altinstall` instead of usual `make install`!)

---
- Download or clone this repository, enter the repository directory and run `bash deploy.sh`. It will:
    - Create user for the application to run, with home directory at `/home/wormhole-tracker`. There you can find the application log.
    - Create directory `.envs/` inside new user's home directory
    - Install `virtualenv` if it is not installed
    - Create virtual environment for the application
    - Install application itself
    - Copy configuration template
    - Install application daemon to the `/etc/init.d/wormhole-tracker-daemon` and start it on behalf new user
- If you want to change any of those things just check out variables at the top of `deploy.sh`.
- In the end new user's home dir will look like this:
```
/home/
    wormhole-tracker/
        wormhole-tracker.conf    # Configuration file
        wormhole-tracker-daemon  # Daemon file
        wormhole-tracker.log     # Application log
        wormhole-tracker.pid     # Daemon's process file
```
- Feel free to re-run the deploy script to re-deploy the application, it won't touch the configuration.

---
#### Configuration

---
###### Third-party application setup

---
Before getting any further, you must have EVE online third-party app which you can create and setup [here](developers.eveonline.com/applications)
Give it any name and description you like, select _Authentication & API Access_ connection type and choose following permissions to use:

- `characterLocationRead`
- `characterBookmarksRead`

...and set the `Callback URL` to your dedicated IP(or domain, if you have it) in the following format:

- `http://your-ip-or-domain/auth/`

`http://` and `/auth/` parts **are** required.

In your application details you will see `Client ID` and `Secret Key`. You will need it for the next step.

---
###### Filling up the configuration file

---
There are 4 variables you'll have to define in the `wormhole-tracker.conf`:

- `client_id` is the `Client ID` from the previous step
- `client_key` is the `Secret Key` from the previous step
- `redirect_uri` is the `Callback URL` from the previous step
- `cookiet_secret` is the secret value you have to generate yourself



You can generate cookie secret as follows:

- Go to your python3.6 console and do `import base64` and `from os import urandom`
- Then do `b64encode(urandom(24)).strip()`, it's your secret value.

At the end, your configuration file should look like this:

```python
client_id     = "334jjnn32i23yv23592352352sa3n52b"
client_key    = "3534ui32b5223yu5u2v35v23v523v3fg"
redirect_uri  = "http://your-ip-or-domain/auth/"  # "http(s)://" and "/auth/" ARE required!
cookie_secret = "WYkRXG1RJhmpYlYCA2D99EFRz9lt709t"
```

And it seems like you're done. Enjoy your tracking! 07

---
