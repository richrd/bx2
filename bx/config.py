"""
Config handler
"""

import os
import json
import logging
import collections

from . import helpers


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

    def get_accounts(self):
        return self.accounts

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
        self.config = config
        self.update(self.config, self.defaults)
        return True

    def load_servers(self):
        files = self.get_config_files(self.server_dir)
        server_configs = self.load_config_files(self.server_dir, files)
        if not server_configs:
            self.logger.warning("No servers configured!")
            return False
        self.logger.debug("self.config: {}".format(self.config))
        for server in server_configs:
            defaults = dict(self.config["server"])
            self.logger.debug("defaults: {}".format(defaults))
            self.logger.debug("server: {}".format(server))
            self.servers[server["name"]] = self.update(defaults, server)
        return True

    def load_accounts(self):
        files = self.get_config_files(self.account_dir)
        account_configs = self.load_config_files(self.account_dir, files)
        if not account_configs:
            self.logger.warning("No accounts configured!")
            return False
        for account in account_configs:
            self.accounts[account["username"]] = account
        return True

    def load_config_files(self, path, files):
        configs = []
        for name in files:
            file_path = os.path.join(path, name)
            conf = self.load_config_file(file_path)
            if not conf:
                self.logger.warning("Failed to load config file '{}'.".format(file_path))
                continue
            configs.append(conf)
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
        # for k, v in u.iteritems():
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                r = self.update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d
