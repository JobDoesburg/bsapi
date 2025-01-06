from dataclasses import dataclass
import os
import os.path
import json
from typing import Optional

import bsapi


@dataclass
class Identity:
    """An identity that is used to access the Brightspace API, providing the user part of the application and user pair
    needed to authenticate to the API backend."""

    name: str
    user_id: str
    user_key: str
    default_for: set[str]

    def to_json(self):
        return {
            "userId": self.user_id,
            "userKey": self.user_key,
            "defaultFor": list(self.default_for),
        }

    @staticmethod
    def from_json(name: str, json_obj: any):
        return Identity(
            name, json_obj["userId"], json_obj["userKey"], set(json_obj["defaultFor"])
        )


class IdentityStore:
    """Manipulate a list of Brightspace identities for each LMS host, backed by a JSON file."""

    STORE_ENV_VAR = "BS_IDENTITY_PATH"
    VERSION = 1

    def __init__(self):
        """Construct a new and empty identity store."""
        self.identities: dict[str, dict[str, Identity]] = dict()

    def add(self, host: str, identity: Identity):
        """Add a new identity to the store. If an identity with that name already exists for the LMS host, it will be
        overwritten instead.

        :param host: The LMS host to add the identity to.
        :param identity: The identity to add.
        """
        if host not in self.identities:
            self.identities[host] = dict()
        self.identities[host][identity.name] = identity

    def get(self, host: str, name: str) -> Optional[Identity]:
        """Get the identity with the given name from the store if one exists for the given LMS host.

        :param host: The LMS host to get the identity for.
        :param name: The name of the identity to get.
        :return: The identity if one exists, `None` otherwise.
        """
        return self.identities.get(host, dict()).get(name, None)

    def get_hosts(self) -> list[str]:
        """Get a list of all LMS hosts that have at least one associated identity.

        :return: A list of LMS hosts.
        """
        return list(self.identities.keys())

    def get_identities(self, host: str) -> list[Identity]:
        """Get a list of all identities associated with the given LMS host.

        :param host: The LMS host to get identities for.
        :return: A list of identities, which is empty if no identity is associated with the given LMS host.
        """
        return list(self.identities.get(host, dict()).values())

    def get_default(self, host: str, tag: str) -> Optional[Identity]:
        """Get the default identity for the given LMS host and tag.

        :param host: The LMS host to get the default identity for.
        :param tag: The tag to get the default identity for.
        :return: The default identity if one exists, or `None` otherwise.
        """
        for identity in self.get_identities(host):
            if tag in identity.default_for:
                return identity

        return None

    def set_default(self, host: str, tag: str, identity: Identity):
        """Set the default identity for the given LMS host and tag. This will clear the tag from all other identities
        associated with the given LMS host. If the identity does not exist for the given LMS host, nothing is done.

        :param host: The LMS host to set the default identity for.
        :param tag: The tag to set the default identity for.
        :param identity: The default identity to set.
        """
        if host in self.identities:
            if identity.name in self.identities[host]:
                for id_ in self.identities[host].values():
                    id_.default_for.discard(tag)
                self.identities[host][identity.name].default_for.add(tag)

    def reset_default(self, host: str, tag: str):
        """Clear the default identity for the given LMS host and tag. If the given LMS host has no associated identities
        then nothing is done.

        :param host: The LMS host to clear the default identity for.
        :param tag: The tag to clear the default identity for.
        """
        if host in self.identities:
            for id_ in self.identities[host].values():
                id_.default_for.discard(tag)

    def remove(self, host: str, identity: Identity) -> Identity:
        """Remove the given identity from the given LMS host in the store.

        :param host: The LMS host to remove the identity from.
        :param identity: The identity to remove, based on the identity name.
        :return: The removed identity, or the given identity if it did not exist.
        """
        return self.identities.get(host, dict()).pop(identity.name, identity)

    def store_path(self) -> str:
        """Determine the path used to save the identity store. The default path can be overwritten by setting the
        `self.STORE_ENV_VAR` environment variable, allowing easy customization for end users.

        :return: The path used to save the identity store.
        """
        default_path = os.path.join(
            os.path.expanduser("~"), ".config", "brightspace", "identities.json"
        )
        return os.environ.get(self.STORE_ENV_VAR, default_path)

    def load(self, path: str = None):
        """Attempt to load the identity store from the given path, or from the path determined by `self.store_path`.

        :param path: The path to load from, or `None` to determine the path using `self.store_path()`.
        :raises ValueError: If the identity store format has an unsupported version number.
        """
        path = path if path else self.store_path()
        self.identities.clear()

        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                json_obj = json.loads(f.read())
                if json_obj["version"] > self.VERSION:
                    raise ValueError(f'unsupported version {json_obj["version"]}')

                for host, identities in json_obj["identities"].items():
                    self.identities[host] = {
                        name: Identity.from_json(name, identity)
                        for name, identity in identities.items()
                    }

    def store(self, path: str = None):
        """Attempt to store the identity store to the given path, or to the path determined by `self.store_path`.

        :param path: The path to store to, or `None` to determine the path using `self.store_path()`.
        """
        path = path if path else self.store_path()
        parent_path = os.path.dirname(path)

        json_obj = {"version": self.VERSION, "identities": dict()}
        for host, identities in self.identities.items():
            json_obj["identities"][host] = {
                identity.name: identity.to_json() for identity in identities.values()
            }

        os.makedirs(parent_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(json_obj, indent=True))


class TablePrinter:
    """Minimal pretty printer for ASCII tables"""

    ALIGN_LEFT = "<"
    ALIGN_RIGHT = ">"
    ALIGN_CENTER = "^"

    @dataclass
    class Column:
        name: str
        width: int
        column_align: str
        row_align: str

    def __init__(self):
        """Construct a new table printer without any columns or rows."""
        self.columns: list[TablePrinter.Column] = []
        self.rows: list[list[str]] = []

    def add_column(
        self, name: str, column_align: str = ALIGN_CENTER, row_align: str = ALIGN_LEFT
    ):
        """Add a new column to the table printer.

        :param name: The name of the column.
        :param column_align: The alignment of the column header.
        :param row_align: The alignment of the row cells.
        :raises AssertionError: If the rows are not empty.
        """
        assert len(self.rows) == 0, "rows must be empty"
        self.columns.append(
            TablePrinter.Column(name, len(name), column_align, row_align)
        )

    def add_row(self, data: list[str]):
        """Add a new row to the table printer.

        :param data: The list of row cell data.
        :raises AssertionError: If the number of columns does not match the number of cells in the given row.
        """
        assert len(data) == len(self.columns), "incorrect number of data columns"
        self.rows.append(data)
        for i, cell in enumerate(data):
            self.columns[i].width = max(self.columns[i].width, len(cell))

    def add_rows(self, rows: list[list[str]]):
        """Add new rows to the table printer using `self.add_row` on each given row.

        :param rows: The rows to add.
        """
        for row in rows:
            self.add_row(row)

    def print(self):
        """Print the table using the specified alignment rules. The width of each column is determined by taking the
        maximum of the column name length and longest cell length of that column.
        """
        print(
            " | ".join(
                [
                    f"{column.name:{column.column_align}{column.width}}"
                    for column in self.columns
                ]
            )
        )
        print("-+-".join(["-" * column.width for column in self.columns]))
        for row in self.rows:
            print(
                " | ".join(
                    [
                        f"{cell:{self.columns[i].row_align}{self.columns[i].width}}"
                        for i, cell in enumerate(row)
                    ]
                )
            )


class IdentityManager:
    """Interactive manager to manage stored identities."""

    def __init__(
        self,
        host: str,
        app_id: str = None,
        app_key: str = None,
        client_callback_url: str = None,
        store_path: str = None,
    ):
        """Construct a new identity manager. After construction no attempt is made to load from the store. This is done
        separately using `self.load_store`.

        :param host: The LMS host to manage identities for.
        :param app_id: The application id to use for API access, or `None` to disable API access.
        :param app_key: The application key to use for API access, or `None` to disable API access.
        :param client_callback_url: The client callback URL to use when creating a new authentication process.
        :param store_path: The path to store the identity store, or `None` to use the default, unless overwritten by the
        user using the dedicated environment variable; see `IdentityStore.store_path`.
        """
        self.host = host
        self.app_id = app_id
        self.app_key = app_key
        self.client_callback_url = client_callback_url
        self.store_path = store_path
        self.store = IdentityStore()

    @staticmethod
    def from_config(config: bsapi.APIConfig):
        """Construct a new identity manager from the given Brightspace API configuration.

        :param config: The API configuration.
        :return: The IdentityManager instance.
        """
        return IdentityManager(
            config.lms_url, config.app_id, config.app_key, config.client_app_url
        )

    def load_store(self) -> bool:
        """Try to load the identity store. If this fails, an error message is printed to the standard output.

        :return: `True` if successful, `False` otherwise.
        """
        try:
            self.store.load(self.store_path)
            return True
        except Exception as e:
            store_path = self.store_path if self.store_path else self.store.store_path()
            print(
                f'[ERROR] failed to load identity store from path "{store_path}" due to exception: {e}'
            )
            return False

    def save_store(self) -> bool:
        """Try to save the identity store. If this fails, an error message is printed to the standard output.

        :return:`True` if successful, `False` otherwise.
        """
        try:
            self.store.store(self.store_path)
            return True
        except Exception as e:
            store_path = self.store_path if self.store_path else self.store.store_path()
            print(
                f'[ERROR] failed to save identity store to path "{store_path}" due to exception: {e}'
            )
            return False

    def _list_identities(self):
        identities = self.store.get_identities(self.host)
        id_str = "identity" if len(identities) == 1 else "identities"
        table = TablePrinter()
        table.add_column("name")
        table.add_column("user id")
        table.add_column("default for")
        table.add_rows(
            [
                [id_.name, id_.user_id, ", ".join(sorted(id_.default_for))]
                for id_ in identities
            ]
        )

        print(f'Storing {len(identities)} {id_str} for LMS host "{self.host}"')
        print()
        table.print()

    @staticmethod
    def _print_help_manager():
        print("Available commands:")
        print("* add                  - add a new identity")
        print("* remove <name>        - remove identity with <name>")
        print(
            "* test <name>          - test identity with <name> using Brightspace API"
        )
        print("* show <name>          - show details of identity with <name>")
        print("* default <name> <tag> - mark identity with <name> as default for <tag>")
        print("* reset <tag>          - clear default <tag> from identities")
        print("* exit                 - exit the manager")

    @staticmethod
    def _get_add_method() -> str:
        while True:
            print("Enter input method")
            print("* auth   - authenticate using API/browser")
            print("* manual - input user id and key manually")
            print("* cancel - cancel operation")
            method = input("method> ").strip().lower()

            if method in ["auth", "manual", "cancel"]:
                return method
            else:
                print("Invalid method\n")

    def _get_add_name(self, default: str = None) -> Optional[str]:
        while True:
            name = input("name> ")
            name = name.strip()
            if not name and default:
                return default
            elif not name:
                continue
            if self.store.get(self.host, name):
                print(f'[ERROR] identity with name "{name}" already exists')
            else:
                return name

    @staticmethod
    def _get_persist() -> bool:
        print("Do you want to save this identity to disk?")
        print("Doing so will allow you to reuse it in the future")
        print("Otherwise it is only temporarily stored in memory, and will not persist")
        print("Do not save to disk on untrusted/shared machines!")

        while True:
            choice = input("Save to disk? [y/n]: ").strip().lower()
            if choice in ["y", "yes"]:
                return True
            elif choice in ["n", "no"]:
                return False

    def _add_identity_manual(self) -> bool:
        print()
        print("Create a new identity by filling out the following fields")
        print("* name     - Name of your own choosing, must be unique")
        print("* user id  - User identifier token (PUBLIC)")
        print("* user key - User key token (PRIVATE)")
        print()

        name = self._get_add_name()
        user_id = input("user id> ")
        user_key = input("user key> ")

        identity = Identity(name, user_id, user_key, set())
        self.store.add(self.host, identity)

        return self._get_persist()

    def _complete_add_identity_auth(self, user_id: str, user_key: str) -> bool:
        context = bsapi.APIContext(
            self.app_id, self.app_key, user_id, user_key, self.host
        )
        api = bsapi.BSAPI(context, "", "")

        try:
            print()
            print(f'Found user identifier "{user_id}" and user key "{user_key}"')
            print()
            print("+ Checking latest API version")
            api.check_versions(use_latest=True)
            print("+ Obtaining user information via API")
            whoami = api.whoami()
            suggested_name = whoami.unique_name.lower().strip()
            description = (
                f"{whoami.first_name} {whoami.last_name} ({whoami.unique_name})"
            )

            print()
            print(f"Identified as: {description}")
            print(
                f'Enter a name for the new identity; leave blank to use suggested "{suggested_name}"'
            )

            name = self._get_add_name(default=suggested_name)
            identity = Identity(name, user_id, user_key, set())
            self.store.add(self.host, identity)

            return self._get_persist()
        except bsapi.APIError as e:
            print(f"[ERROR] API call failed: {e.cause}")
            return False

    def _add_identity_auth(self) -> bool:
        if not self.app_id or not self.app_key:
            print("[ERROR] app_id and/or app_key not specified; API not available")
            return False
        if not self.client_callback_url:
            print(
                "[ERROR] client_callback_url not specified; API authentication not available"
            )
            return False

        auth_url = bsapi.create_auth_url(
            self.host, self.client_callback_url, self.app_id, self.app_key
        )

        print()
        print(f"Open a browser and go to the following URL: {auth_url}")
        print("You will be asked to log in with your Brightspace account")
        print("If you have multiple accounts, use the one with access to the course")
        print(
            "Afterwards it will redirect you to a URL that looks similar to the following:"
        )
        print()
        print(f"{self.client_callback_url}&x_a=<user_id>&x_b=<user_key>&x_c=...")
        print()
        print(
            'Once you obtain this URL, paste it in the input below, or type "cancel" to cancel'
        )
        print(
            "Note that this page may not load correctly, or is immediately redirected"
        )
        print("Be sure to check your browser history in such cases")
        print()

        while True:
            url = input("url> ")
            url = url.strip()

            if url == "cancel":
                return False

            try:
                user_id, user_key = bsapi.parse_callback_url(url)

                return self._complete_add_identity_auth(user_id, user_key)
            except ValueError as e:
                print(f"[ERROR] Failed to parse url: {e}")

    def _add_identity(self) -> bool:
        method = self._get_add_method()

        if method == "auth":
            return self._add_identity_auth()
        elif method == "manual":
            return self._add_identity_manual()
        else:
            return False

    def _test_identity(self, identity: Identity):
        if not self.app_id or not self.app_key:
            print("[ERROR] app_id and/or app_key not specified; API not available")
            return

        context = bsapi.APIContext(
            self.app_id, self.app_key, identity.user_id, identity.user_key, self.host
        )
        api = bsapi.BSAPI(context, "", "")

        try:
            api.check_versions(use_latest=True)
            whoami = api.whoami()
            description = (
                f"{whoami.first_name} {whoami.last_name} ({whoami.unique_name})"
            )

            print(f"Test successful! Identified as: {description}")
        except bsapi.APIError as e:
            print(f"[ERROR] Test failed due to API error: {e.cause}")
        except Exception as e:
            print(f"[ERROR] Test failed due to unknown error: {e}")

    @staticmethod
    def _show_identity(identity: Identity):
        print(f"name:        {identity.name}")
        print(f"user id:     {identity.user_id}")
        print(f"user key:    {identity.user_key}")
        print(f'default for: {", ".join(sorted(list(identity.default_for)))}')

    def manage(self):
        """Start the interactive manager."""
        while True:
            print()
            self._list_identities()
            print()
            print("Manage stored identities")
            print()
            self._print_help_manager()
            print()
            user_input = input("manage> ").strip()
            print()

            command, _, params = user_input.partition(" ")
            params = params.strip()
            if command == "add":
                if self._add_identity():
                    self.save_store()
            elif command == "remove":
                identity = self.store.get(self.host, params)
                if identity:
                    self.store.remove(self.host, identity)
                    self.save_store()
                else:
                    print(f'[ERROR] Unknown identity "{params}"')
            elif command == "default":
                name, _, tag = params.rpartition(" ")
                name = name.strip()
                tag = tag.strip()
                if not name:
                    print("[ERROR] Missing tag")
                else:
                    identity = self.store.get(self.host, name)
                    if identity:
                        self.store.set_default(self.host, tag, identity)
                        self.save_store()
                        print(f'Marked identity "{name}" as default for tag "{tag}"')
                    else:
                        print(f'[ERROR] Unknown identity "{name}"')
            elif command == "reset":
                self.store.reset_default(self.host, params)
                self.save_store()
                print(f'Cleared default tag "{params}" from identities')
            elif command == "test":
                identity = self.store.get(self.host, params)
                if identity:
                    self._test_identity(identity)
                else:
                    print(f'[ERROR] Unknown identity "{params}"')
            elif command == "show":
                identity = self.store.get(self.host, params)
                if identity:
                    self._show_identity(identity)
                else:
                    print(f'[ERROR] Unknown identity "{params}"')
            elif command == "exit":
                break
            else:
                print(f'[ERROR] Unknown command "{command}"')

    @staticmethod
    def _print_help_identity():
        print("Available commands:")
        print("* select <name> - select identity with <name>")
        print("* manage        - start identity manager")
        print("* exit          - exit without selecting an identity")

    def get_identity(self, tag: str = None) -> Optional[Identity]:
        """Get an identity from the identity store by asking the user to select an identity. If a tag is provided, and a
        default identity exists for that tag, that identity is returned instead without user interaction.

        :param tag: The tag to get the default identity for, or `None` to always ask the user.
        :return: The selected identity, or `None` if no identity has been selected.
        """
        if tag:
            default_identity = self.store.get_default(self.host, tag)
            if default_identity:
                return default_identity

        while True:
            print()
            self._list_identities()
            print()
            print(
                "Select an identity to use, or start the manager to add/modify identities"
            )
            print()
            self._print_help_identity()
            print()
            user_input = input("select> ").strip()
            print()

            command, _, params = user_input.partition(" ")
            if command == "select":
                identity = self.store.get(self.host, params.strip())
                if identity:
                    if tag:
                        confirm = (
                            input(
                                f'Do you always want to use this identity for tag "{tag}"? [yes/no]: '
                            )
                            .strip()
                            .lower()
                        )
                        if confirm in ["y", "yes"]:
                            self.store.set_default(self.host, tag, identity)
                            self.save_store()
                    return identity
                else:
                    print(f'[ERROR] Unknown identity "{params}"')
            elif command == "manage":
                self.manage()
            elif command == "exit":
                return None
            else:
                print(f'[ERROR] Unknown command "{command}"')
