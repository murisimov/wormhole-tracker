EVE Online star system tracker
---
_Draws your route in real time._
_Can be pretty useful in Darkest Depths of Deadly W-space._

---

---

#### How do I use this service?
- Use signin button to login via SSO.
- Press "Track" and you're good to go.

---

---

#### Can I use it as standalone application?

---
- Sure, just follow the instructions below.

---
- First of all you need to have a dedicated IP address that CCP can redirect your users to after authentication. [VPS](https://en.wikipedia.org/wiki/Virtual_private_server) usually have it, so it can be a nice idea to rent one (it's about 5$/mo).

- Install python3.6:
    - [CentOS 7](http://www.codeghar.com/blog/install-latest-python-on-centos-7.html)
    - [Ubuntu 14.04/16.04/16.10](http://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get)
    - [Building from source](https://docs.python.org/3/using/unix.html) (Please consider use `make altinstall` instead of usual `make install`!)


---
- Download or clone this repository, enter the repository directory and run `bash deploy.sh`. It will:
    - Create user for the application to run, with home directory at `/home/wormhole-tracker`. There you can find application log.
    - Create directory `.envs/` inside new user's home directory
    - Install `virtualenv` if it is not installed
    - Create virtual environment for the application
    - Install application itself
    - Install application daemon to the `/etc/init.d/wormhole-tracker-daemon` and start it on behalf new user
- If you want to change any of those things just check out variables at the top of `deploy.sh`.

