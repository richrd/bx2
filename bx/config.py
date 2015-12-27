"""
Config handler
"""

import os
import json
import logging
import hashlib
import collections

from . import helpers


class Account:
    def __init__(self, config, data, filename=None):
        # Config instance
        self.config = config
        # Account information
        self.data = data
        # Account filename
        self.filename = filename

    #

    def set_data(self, data):
        self.data = data

    def set_username(self, username):
        self.data["username"] = username

    def set_filename(self, filename):
        self.filename = filename

    def set_servers(self, servers):
        self.data["servers"] = servers

    def set_server_channels(self, server, channels):
        self.data["servers"][server] = channels

    def set_permission_level(self, permission_level):
        self.data["level"] = permission_level

    def set_hostnames(self, hostnames):
        self.data["hostnames"] = hostnames

    def set_last_seen(self, last_seen):
        self.data["last_seen"] = last_seen

    #

    def get_data(self):
        return self.data

    def get_username(self):
        return self.data["username"]

    def get_filename(self):
        return self.filename

    def get_server(self, name):
        if name not in self.data["servers"].keys():
            return False
        return self.data["servers"][name]

    def get_servers(self):
        return self.data["servers"].keys()

    def get_server_channels(self, server):
        return self.data["servers"][server]

    def get_permission_level(self):
        return self.data["level"]

    def get_hostnames(self):
        return self.data["hostnames"]

    def get_last_seen(self):
        return self.data["last_seen"]

    #

    def has_server(self, server):
        return server in self.get_servers()

    def is_trusted_channel(self, server, channel):
        server = self.config.get_server(server)
        if not server:
            return False
        print(self)
        print(server)

    def add_hostname(self, hostname):
        self.get_hostnames().append(hostname)

    def valid_password(self, pw):
        # FIXME: deprecate md5
        in_hash = self.config._sha224_hash(pw)
        if in_hash == self.data["password"]:
            return True
        in_hash = self.config._md5_hash(pw)
        if in_hash == self.data["password"]:
            return True
        return False

    def store(self):
        self.config.store_account(self)


class Server:
    def __init__(self, config, data, filename=None):
        # Config instance
        self.config = config
        # Servers information
        self.data = data
        # Server filename
        self.filename = filename

    #

    def __getitem__(self, key):
        return self.data[key]

    def get_data(self):
        return self.data

    def get_name(self):
        return self.data["name"]

    def get_host(self):
        return self.data["host"]

    def get_port(self):
        return self.data["port"]

    def get_enabled(self):
        return self.data["enabled"]

    def get_stealth(self):
        return self.data["stealth"]

    def get_auto_send(self):
        return self.data["auto_send"]

    def get_channels(self):
        return self.data["channels"]

    #

    def __setitem__(self, key, value):
        self.data[key] = value

    def set_data(self, data):
        self.data = data

    def set_name(self, name):
        self.data["name"] = name

    def set_host(self, host):
        self.data["host"] = host

    def set_port(self, port):
        self.data["port"] = port

    def set_enabled(self, enabled):
        self.data["enabled"] = enabled

    def set_stealth(self, stealth):
        self.data["stealth"] = stealth

    def set_auto_send(self, auto_send):
        self.data["auto_send"] = auto_send

    def set_channels(self, channels):
        self.data["channels"] = channels

    #

    def store(self):
        self.config.store_server(self)


class Config:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)

        self.default_filename = "defaults.json"
        self.main_filename = "config.json"

        self.home_dir = os.path.expanduser("~")
        self.config_dir = os.path.join(self.home_dir, ".config", "bx")
        self.server_dir = os.path.join(self.config_dir, "servers")
        self.account_dir = os.path.join(self.config_dir, "accounts")

        self.defaults = {}
        self.config = {}
        self.servers = {}
        self.accounts = {}

    def _sha224_hash(self, s):
        s = s.encode("utf-8")
        return hashlib.sha224(s).hexdigest()

    def _md5_hash(self, s):
        s = s.encode("utf-8")
        return hashlib.md5(s).hexdigest()

    def init(self):
        self.create_config_dirs()
        return self.load_defaults()

    def load(self):
        self.load_config()
        self.load_servers()
        self.load_accounts()

    def get_item(self, key):
        return self.config[key]

    def get_servers(self):
        return self.servers

    def get_account_names(self):
        return [account.get_username() for account in self.get_accounts()]

    def get_account(self, name):
        if name in self.accounts.keys():
            return self.accounts[name]
        return False

    def get_accounts(self):
        accounts = []
        for account in self.accounts.values():
            accounts.append(account)
        return accounts

    def get_account_by_hostname(self, user, hostname):
        for account in self.get_accounts():
            if not account.has_server(user.bot.get_name()):
                continue
            if hostname in account.get_hostnames():
                return account
        return False

    def authenticate_account(self, user, username, password):
        account = self.get_account(username)
        if not account:
            return False
        if not account.has_server(user.bot.get_name()):
            return False
        if account.valid_password(password):
            return account

    def set_config_dir(self, path):
        self.config_dir = path
        self.server_dir = os.path.join(self.config_dir, "servers")
        self.account_dir = os.path.join(self.config_dir, "accounts")

    def load_defaults(self):
        path = os.path.join(self.config_dir, self.default_filename)
        defaults = self.load_config_file(path)
        if not defaults:
            self.logger.error("Failed to load default config file! ('{0}')".format(path))
            return False
        self.defaults = defaults
        return True

    def load_config(self):
        path = os.path.join(self.config_dir, self.main_filename)
        config = self.load_config_file(path)
        if not config:
            self.logger.error("Failed to load default config file! ('{0}')".format(path))
            self.config = dict(self.defaults)
            return False
        self.config = helpers.merge(self.defaults.copy(), config)
        return True

    def load_servers(self):
        files = self.get_config_files(self.server_dir)
        server_configs = self.load_config_files(self.server_dir, files)
        if not server_configs:
            self.logger.warning("No servers configured!")
            return False
        for item in server_configs:
            defaults = dict(self.config["server"])
            conf = helpers.merge(defaults.copy(), item[1])
            server = Server(self, conf, item[0])
            self.servers[server["name"]] = server
        return True

    def load_accounts(self):
        files = self.get_config_files(self.account_dir)
        account_configs = self.load_config_files(self.account_dir, files)
        if not account_configs:
            self.logger.warning("No accounts configured!")
            return False
        for item in account_configs:
            account = Account(self, item[1], item[0])
            self.accounts[account.get_username()] = account
        return True

    def store_account(self, account):
        path = os.path.join(self.account_dir, account.get_filename())
        return self.store_config_file(path, account.get_data())

    def store_server(self, server):
        path = os.path.join(self.server_dir, server.get_filename())
        return self.store_config_file(path, server.get_data())

    def load_config_files(self, path, files):
        configs = []
        for name in files:
            file_path = os.path.join(path, name)
            conf = self.load_config_file(file_path)
            if not conf:
                self.logger.warning("Failed to load config file '{}'.".format(file_path))
                continue
            configs.append([name, conf])
            # configs.append(conf)
        return configs

    def get_config_files(self, path):
        """Return names of al config files in path."""
        files = os.listdir(path)
        config_files = []
        for file_name in files:
            # Skip hidden files
            if file_name[0] == ".":
                continue
            # Skip non json files
            if not helpers.ends(file_name, ".json"):
                continue
            config_files.append(file_name)
        return config_files

    def get_config_files_in_dir(self, path):
        all_files = os.listdir(path)
        config_files = []
        for file_name in all_files:
            if file_name[0] == ".":
                continue
            if not helpers.ends(file_name, ".json"):
                continue
            config_files.append(file_name)

    def load_config_file(self, path):
        # TODO: check existance
        try:
            f = open(path)
            data = f.read()
            f.close()
            data = self.remove_config_comments(data)
            config = json.loads(data)
            return config
        except:
            return False

    def store_config_file(self, path, data):
        """Store data as JSON at given path."""
        try:
            f = open(path, "w")
            f.write(json.dumps(data, indent=4))
            f.close()
            return True
        except:
            self.logger.exception("Storing config file '{}' failed!".format(path))

    def create_config_dirs(self):
        """Create all config directories."""
        dirs = [self.config_dir, self.server_dir, self.account_dir]
        for d in dirs:
            if not self.create_dirs(d):
                # TODO: Add logging
                return False
        return True

    def create_dirs(self, path):
        """Try to create a single directory path."""
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                return True
            except:
                # TODO: Add logging
                return False
        return True

    def remove_config_comments(self, data):
        """Remove comments from a 'pseudo' JSON config file.

        Removes all lines that begin with '#' or '//' ignoring whitespace.

        :param data: Commented JSON data to clean.
        :return: Cleaned pure JSON.
        """
        lines = data.split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            if helpers.starts(line, "//") or helpers.starts(line, "#"):
                continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def update(self, d, u):
        """Merge two dicts. Used for merging config to defaults."""
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                r = self.update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d
