from os import urandom
from pkg_resources import resource_filename


settings = {
    'static_path': resource_filename('wormhole_tracker', 'static'),
    'template_path': resource_filename('wormhole_tracker', 'templates'),
    'cookie_secret': urandom(24),
    'db_path': '/home/wormhole-tracker/data.db',
}
