from collections.abc import Callable
from dataclasses import dataclass
import errno
import logging
import mimetypes
import numbers
import os
import pathlib
from typing import Optional
import requests
import urllib.parse

import bsapi.types

ENTITY_TYPE_GROUP = "group"
ENTITY_TYPE_USER = "user"

logger = logging.getLogger(__name__)


class APIError(RuntimeError):
    """Error while calling the Brightspace API."""

    def __init__(self, cause: str, response: requests.Response = None):
        """Construct a new API error instance.

        :param cause: The cause of the API error.
        :param response: The response that generated the API error, if available.
        """
        self.cause = cause
        self.response = response

    @staticmethod
    def from_response(response: requests.Response):
        """Create an API error instance from a response, using the status code of the response.

        :param response: The API response.
        :return: The API error instance.
        """
        return APIError(f"{response.status_code}: {response.text}", response=response)


@dataclass
class APIConfig:
    """Holds configuration information needed to set up the API access from an application perspective."""

    client_id: str
    client_secret: str
    lms_url: str
    redirect_uri: str
    le_version: str
    lp_version: str

    @staticmethod
    def from_json(obj: dict):
        """Construct a new API config instance from a JSON dictionary.

        :param obj: The JSON dictionary.
        :return: The `APIConfig` instance.
        """
        return APIConfig(
            client_id=obj["clientId"],
            client_secret=obj["clientSecret"],
            lms_url=obj["lmsUrl"],
            redirect_uri=obj["redirectUri"],
            le_version=obj["leVersion"],
            lp_version=obj["lpVersion"],
        )

    def to_json(self):
        """Construct a JSON serializable dictionary for this API config instance.

        :return: The JSON dictionary.
        """
        return {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "lmsUrl": self.lms_url,
            "redirectUri": self.redirect_uri,
            "leVersion": self.le_version,
            "lpVersion": self.lp_version,
        }


class BSAPI:
    """Minimal Brightspace API wrapper."""

    _VALID_ENTITY_TYPES = [ENTITY_TYPE_USER, ENTITY_TYPE_GROUP]

    def __init__(
        self,
        access_token: str,
        host: str,
        le_version: str = "1.79",
        lp_version: str = "1.47",
    ):
        """Construct a new Brightspace API wrapper instance.

        :param access_token: The OAuth access token.
        :param host: The host URL for the API.
        :param le_version: The version to use for the LE product component.
        :param lp_version: The version to use for the LP product component.
        """
        self.access_token = access_token
        self.host = host
        self.le_version = le_version
        self.lp_version = lp_version

    @staticmethod
    def from_config(config: APIConfig, access_token: str):
        """Create BSAPI instance from config and access token."""
        return BSAPI(access_token, config.lms_url, config.le_version, config.lp_version)

    def _create_url(self, api_route: str) -> str:
        """Create URL for API requests."""
        return urllib.parse.urlunsplit(("https", self.host, api_route, "", ""))

    def _get_auth_headers(self) -> dict:
        """Get authorization headers for API requests."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _whoami(self):
        """Wrapper for https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-whoami"""
        return self._get_json(self._get_lp_route("users/whoami"))

    def whoami(self) -> bsapi.types.WhoAmIUser:
        """Wrapper for https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-users-whoami"""
        return bsapi.types.WhoAmIUser.from_json(self._whoami())

    def _get_roles(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-(orgUnitId)-roles-"""
        return self._get_json(self._get_lp_route(f"{org_unit_id}/roles/"))

    def get_roles(self, org_unit_id: int) -> list[bsapi.types.Role]:
        """Wrapper for https://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-(version)-(orgUnitId)-roles-"""
        return [
            bsapi.types.Role.from_json(role) for role in self._get_roles(org_unit_id)
        ]

    def _get_product_versions(self, product_code: str):
        """Wrapper for https://docs.valence.desire2learn.com/res/apiprop.html#get--d2l-api-(productCode)-versions-"""
        return self._get_json(f"/d2l/api/{product_code}/versions/")

    def get_product_versions(self, product_code: str) -> bsapi.types.ProductVersions:
        """Wrapper for https://docs.valence.desire2learn.com/res/apiprop.html#get--d2l-api-(productCode)-versions-"""
        return bsapi.types.ProductVersions.from_json(
            self._get_product_versions(product_code)
        )

    def _get_versions(self):
        """Wrapper for https://docs.valence.desire2learn.com/res/apiprop.html#get--d2l-api-versions-"""
        return self._get_json("/d2l/api/versions/")

    def get_versions(self) -> list[bsapi.types.ProductVersions]:
        """Wrapper for https://docs.valence.desire2learn.com/res/apiprop.html#get--d2l-api-versions-"""
        return [
            bsapi.types.ProductVersions.from_json(product)
            for product in self._get_versions()
        ]

    def check_versions(self, use_latest: bool = False):
        """Wrapper for https://docs.valence.desire2learn.com/res/apiprop.html#post--d2l-api-versions-check. The versions
        of the LP and LE products are checked.

        :param use_latest: If True, use the latest version rather than checking if the provided versions are supported.
        :raise APIError: If the API call fails, or an unsupported version is detected.
        """
        params = [
            {"ProductCode": "lp", "Version": self.lp_version},
            {"ProductCode": "le", "Version": self.le_version},
        ]

        response = self._post("/d2l/api/versions/check", json=params, check_status=True)

        version_response = response.json()
        version_info = dict()
        for item in version_response["Versions"]:
            version_info[item["ProductCode"]] = {
                "supported": item["Supported"],
                "version": item["Version"],
                "latest_version": item["LatestVersion"],
            }

        if use_latest:
            self.le_version = version_info["le"]["latest_version"]
            self.lp_version = version_info["lp"]["latest_version"]
        elif not version_response["Supported"]:
            cause = "unsupported products:"
            for product, info in version_info.items():
                if not info["supported"]:
                    cause += f' [{product}: req={info["version"]}, latest={info["latest_version"]}]'
            raise APIError(cause)

    def _get_course_enrollments(self):
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-myenrollments-.
        Enrollments are filtered to only include course enrollments (`orgUnitTypeId` 3).
        """
        return self._get_paged_set(
            self._get_lp_route("enrollments/myenrollments/"),
            query_params={"orgUnitTypeId": 3},
        )

    def get_course_enrollments(self) -> list[bsapi.types.MyOrgUnitInfo]:
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-myenrollments-.
        Enrollments are filtered to only include course enrollments (`orgUnitTypeId` 3).
        """
        return [
            bsapi.types.MyOrgUnitInfo.from_json(unit)
            for unit in self._get_course_enrollments()
        ]

    def _get_classlist(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-le-(version)-(orgUnitId)-classlist-"""
        return self._get_json(self._get_le_route(f"{org_unit_id}/classlist/"))

    def get_classlist(self, org_unit_id: int) -> list[bsapi.types.ClasslistUser]:
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-le-(version)-(orgUnitId)-classlist-"""
        return [
            bsapi.types.ClasslistUser.from_json(user)
            for user in self._get_classlist(org_unit_id)
        ]

    def _get_classlist_paged(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-le-(version)-(orgUnitId)-classlist-paged-"""
        return self._get_paged(self._get_le_route(f"{org_unit_id}/classlist/paged/"))

    def get_classlist_paged(self, org_unit_id: int) -> list[bsapi.types.ClasslistUser]:
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-le-(version)-(orgUnitId)-classlist-paged-"""
        return [
            bsapi.types.ClasslistUser.from_json(user)
            for user in self._get_classlist_paged(org_unit_id)
        ]

    def _get_users(self, org_unit_id: int, is_active: bool = None, role_id: str = None):
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-orgUnits-(orgUnitId)-users-"""
        params = dict()
        if is_active is not None:
            params["isActive"] = is_active
        if role_id is not None:
            params["roleId"] = role_id

        return self._get_paged_set(
            self._get_lp_route(f"enrollments/orgUnits/{org_unit_id}/users/"),
            query_params=params,
        )

    def get_users(
        self, org_unit_id: int, is_active: bool = None, role_id: str = None
    ) -> list[bsapi.types.OrgUnitUser]:
        """Wrapper for https://docs.valence.desire2learn.com/res/enroll.html#get--d2l-api-lp-(version)-enrollments-orgUnits-(orgUnitId)-users-"""
        return [
            bsapi.types.OrgUnitUser.from_json(user)
            for user in self._get_users(org_unit_id, is_active, role_id)
        ]

    def _get_dropbox_folders(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-"""
        return self._get_json(self._get_le_route(f"{org_unit_id}/dropbox/folders/"))

    def get_dropbox_folders(self, org_unit_id: int) -> list[bsapi.types.DropboxFolder]:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-"""
        return [
            bsapi.types.DropboxFolder.from_json(folder)
            for folder in self._get_dropbox_folders(org_unit_id)
        ]

    def _get_dropbox_folder(self, org_unit_id: int, folder_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/dropbox/folders/{folder_id}")
        )

    def get_dropbox_folder(
        self, org_unit_id: int, folder_id: int
    ) -> bsapi.types.DropboxFolder:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)"""
        return bsapi.types.DropboxFolder.from_json(
            self._get_dropbox_folder(org_unit_id, folder_id)
        )

    def get_dropbox_folder_attachment(
        self, org_unit_id: int, folder_id: int, file_id: int
    ) -> bytes:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-attachments-(fileId)"""
        return self._get_binary(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/attachments/{file_id}"
            )
        )

    def _get_dropbox_folder_submissions(
        self, org_unit_id: int, folder_id: int, active_only: bool = False
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-submissions-"""
        return self._get_json(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/submissions/"
            ),
            query_params={"activeOnly": active_only},
        )

    def get_dropbox_folder_submissions(
        self, org_unit_id: int, folder_id: int, active_only: bool = False
    ) -> list[bsapi.types.EntityDropBox]:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-submissions-"""
        return [
            bsapi.types.EntityDropBox.from_json(submission)
            for submission in self._get_dropbox_folder_submissions(
                org_unit_id, folder_id, active_only
            )
        ]

    def _get_my_dropbox_folder_submissions(self, org_unit_id: int, folder_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-submissions-mysubmissions-"""
        return self._get_json(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/submissions/mysubmissions/"
            )
        )

    def get_my_dropbox_folder_submissions(
        self, org_unit_id: int, folder_id: int
    ) -> list[bsapi.types.EntityDropBox]:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-submissions-mysubmissions-"""
        return [
            bsapi.types.EntityDropBox.from_json(submission)
            for submission in self._get_my_dropbox_folder_submissions(
                org_unit_id, folder_id
            )
        ]

    def get_dropbox_folder_submission_file(
        self, org_unit_id: int, folder_id: int, submission_id: int, file_id: int
    ) -> bytes:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-submissions-(submissionId)-files-(fileId)"""
        return self._get_binary(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/submissions/{submission_id}/files/{file_id}"
            )
        )

    def download_dropbox_folder_user_submission(
        self, org_unit_id: int, folder_id: int, user_id: int
    ) -> bytes:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-submissions-(userId)-download"""
        return self._get_binary(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/submissions/{user_id}/download"
            )
        )

    def download_dropbox_folder_group_submission(
        self, org_unit_id: int, folder_id: int, group_id: int
    ) -> bytes:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-group-submissions-(groupId)-download"""
        return self._get_binary(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/group-submissions/{group_id}/download"
            )
        )

    def _get_dropbox_folder_submission_feedback(
        self, org_unit_id: int, folder_id: int, entity_type: str, entity_id: int
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-feedback-(entityType)-(entityId).

        :return: The JSON object received from the API call, or `None` if the API call returned with a 404 status code.
        :raise AssertionError: If the given entity type is not valid, which must be either `group` or `user`.
        """
        # The API states it must be either 'group' or 'user', but in the JSON object returned by this API call it
        # actually returns 'Group' or 'User' for the 'EntityType' field. The case in general does not seem to matter as
        # even 'USEr' for example seems to work fine. As such be lenient with the check performed here.
        assert entity_type.lower() in self._VALID_ENTITY_TYPES, "Unknown entity type"

        return self._get_json(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/feedback/{entity_type}/{entity_id}"
            ),
            none_on_404=True,
        )

    def get_dropbox_folder_submission_feedback(
        self, org_unit_id: int, folder_id: int, entity_type: str, entity_id: int
    ) -> Optional[bsapi.types.DropboxFeedbackOut]:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-feedback-(entityType)-(entityId).

        :return: The `DropboxFeedbackOut` object received from the API call, or `None` if the API call returned with a 404 status code.
        :raise AssertionError: If the given entity type is not valid, which must be either `group` or `user`.
        """
        json_obj = self._get_dropbox_folder_submission_feedback(
            org_unit_id, folder_id, entity_type, entity_id
        )

        return bsapi.types.DropboxFeedbackOut.from_json(json_obj) if json_obj else None

    def get_dropbox_folder_submission_feedback_file(
        self,
        org_unit_id: int,
        folder_id: int,
        entity_type: str,
        entity_id: int,
        file_id: int,
    ) -> bytes:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-feedback-(entityType)-(entityId)-attachments-(fileId)"""
        # The API states it must be either 'group' or 'user', but in the JSON object returned by this API call it
        # actually returns 'Group' or 'User' for the 'EntityType' field. The case in general does not seem to matter as
        # even 'USEr' for example seems to work fine. As such be lenient with the check performed here.
        assert entity_type.lower() in self._VALID_ENTITY_TYPES, "Unknown entity type"

        return self._get_binary(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/feedback/{entity_type}/{entity_id}/attachments/{file_id}"
            )
        )

    def remove_dropbox_folder_submission_feedback_file(
        self,
        org_unit_id: int,
        folder_id: int,
        entity_type: str,
        entity_id: int,
        file_id: int,
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#delete--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-feedback-(entityType)-(entityId)-attachments-(fileId)"""
        # The API states it must be either 'group' or 'user', but in the JSON object returned by this API call it
        # actually returns 'Group' or 'User' for the 'EntityType' field. The case in general does not seem to matter as
        # even 'USEr' for example seems to work fine. As such be lenient with the check performed here.
        assert entity_type.lower() in self._VALID_ENTITY_TYPES, "Unknown entity type"

        self._delete(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/feedback/{entity_type}/{entity_id}/attachments/{file_id}"
            ),
            check_status=True,
        )

    def set_dropbox_folder_submission_feedback(
        self,
        org_unit_id: int,
        folder_id: int,
        entity_type: str,
        entity_id: int,
        score: float = None,
        symbol: str = None,
        feedback: str = "",
        html_feedback: str = None,
        draft: bool = False,
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#post--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-feedback-(entityType)-(entityId).

        If HTML feedback is given then the feedback is uploaded as HTML, Otherwise it is uploaded as plaintext.
        Both a numeric score and a string symbol can be given, but the symbol is only valid for SelectBox grades.
        A score and symbol cannot be given at the same time; one of the two must be provided.

        :raise AssertionError: If the given entity type is not valid, if both a score and symbol is set, or if neither score nor symbol is set.
        """
        # The API states it must be either 'group' or 'user', but in the JSON object returned by other API calls it
        # actually returns 'Group' or 'User' for the 'EntityType' field. The case in general does not seem to matter as
        # even 'USEr' for example seems to work fine. As such be lenient with the check performed here.
        assert entity_type.lower() in self._VALID_ENTITY_TYPES, "Unknown entity type"
        assert score is None or symbol is None, "score and symbol cannot both be set"
        assert (
            score is not None or symbol is not None
        ), "score and symbol cannot both be none"

        feedback_type = "Text" if html_feedback is None else "Html"
        feedback_value = feedback if html_feedback is None else html_feedback

        dropbox_feedback = {
            "Score": score,
            "Feedback": {feedback_type: feedback_value},
            "RubricAssessments": [],
            "IsGraded": not draft,
            "GradedSymbol": symbol,
        }

        self._post(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/feedback/{entity_type}/{entity_id}"
            ),
            json=dropbox_feedback,
            check_status=True,
        )

    def _upload_dropbox_folder_submission_feedback_file(
        self,
        org_unit_id: int,
        folder_id: int,
        entity_type: str,
        entity_id: int,
        content_type: str,
        content_length: int,
        file_name: str,
    ) -> str:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#post--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-feedback-(entityType)-(entityId)-upload"""
        headers = {
            "X-Upload-Content-Type": content_type,
            "X-Upload-Content-Length": str(content_length),
            "X-Upload-File-Name": file_name,
        }
        # Disable redirects for this POST as we expect a 308 status code, but do not want to be redirected.
        response = self._post(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/feedback/{entity_type}/{entity_id}/upload"
            ),
            headers=headers,
            allow_redirects=False,
        )

        if response.status_code != 308:
            raise APIError(
                f"Failed to initiate upload, expected 308 status code but got {response.status_code} instead",
                response,
            )

        return response.headers["Location"]

    def _attach_dropbox_folder_submission_feedback_file(
        self,
        org_unit_id: int,
        folder_id: int,
        entity_type: str,
        entity_id: int,
        file_key: str,
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#post--d2l-api-le-(version)-(orgUnitId)-dropbox-folders-(folderId)-feedback-(entityType)-(entityId)-attach"""
        # API documentation claims a 'fileName' form parameter can be used to alter the display name for the uploading
        # file, but this does not seem to have any effect.
        data = {"fileKey": file_key}

        self._post(
            self._get_le_route(
                f"{org_unit_id}/dropbox/folders/{folder_id}/feedback/{entity_type}/{entity_id}/attach"
            ),
            data=data,
            check_status=True,
        )

    def add_dropbox_folder_submission_feedback_file(
        self,
        org_unit_id: int,
        folder_id: int,
        entity_type: str,
        entity_id: int,
        file_path: pathlib.Path,
        file_name: str = None,
        content_type: str = None,
        chunk_size: int = 1024 * 1024 * 16,
        progress_callback: Callable[[int, int], None] = None,
    ):
        """Upload and attach a new file to the feedback of the provided entity. The entity must have been given feedback
        before this is possible, which may be in a draft state. The file is uploaded in fixed size chunks. Smaller chunk
        sizes give faster progress reports, but may reduce upload speed due to the additional overhead of making more
        requests.

        :param org_unit_id: The orgUnitId of the course.
        :param folder_id: The folderId of the dropbox folder.
        :param entity_type: The entityType of the submission, either 'group' or 'user'.
        :param entity_id: The entityId of the submission.
        :param file_path: The file path of the file to be attached.
        :param file_name: The display name of the file, or `None` to use the original name.
        :param content_type: The MIME type of the file, or `None` to automatically determine it.
        :param chunk_size: The upload chunk size.
        :param progress_callback: The progress callback function, which receives the number of bytes received and the
                                  total file size as parameters. Callbacks with `(0, N)` and `(N, N)` are guaranteed to
                                  be made where `N` is the size of the file. If the callback function is `None` then no
                                  progress callback are made.
        """
        # We must upload using a "resumable upload" as described in https://docs.valence.desire2learn.com/basic/fileupload.html#resumable-uploads.
        if not file_path.is_file():
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file_path.name
            )
        file_size = file_path.stat().st_size
        assert file_size > 0, "Uploading empty files is not possible"

        # Attempt to determine MIME type from file name if one was not provided.
        # This may fail, so fall back to octet stream if that happens.
        # I am honestly not sure why the content type even matters here.
        # The content type served when users/graders attempt to open them via Brightspace seems entirely based on the
        # file extension, rather than the content type we provide here.
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"

        logger.debug(
            f'Initiating file upload for "{file_path.name}" (len={file_size}) with content type "{content_type}"'
        )

        # Step 1: Initiate file upload and acquire file upload location/key.
        display_name = file_name if file_name else file_path.name
        location = self._upload_dropbox_folder_submission_feedback_file(
            org_unit_id,
            folder_id,
            entity_type,
            entity_id,
            content_type,
            file_size,
            display_name,
        )
        file_key = location[location.rfind("/") + 1 :]
        logger.debug(f'Acquired upload key "{file_key}"')

        # Step 2: Upload file data in chunks.
        acked = 0
        if progress_callback:
            progress_callback(acked, file_size)
        with open(file_path, "rb") as file:
            while acked < file_size:
                file.seek(acked, os.SEEK_SET)
                chunk = file.read(chunk_size)

                headers = {
                    "Content-Type": content_type,
                    "Content-Range": f"bytes {acked}-{acked + len(chunk) - 1}/{file_size}",
                }
                logger.debug(f'Uploading {headers["Content-Range"]}')
                # Disable redirects for this POST as we expect a 308 status code, but do not want to be redirected.
                response = self._post(
                    location, headers=headers, allow_redirects=False, data=chunk
                )

                if response.status_code == 308:
                    # Server indicated upload incomplete.
                    # Inspect 'Range' header to see what part of the file has been received successfully.
                    # This range always starts with 0, as file uploads must be incremental.
                    logger.debug(f'Server acked {response.headers["Range"]}')
                    last_received = int(response.headers["Range"].removeprefix("0-"))
                    acked = last_received + 1
                    if progress_callback:
                        progress_callback(acked, file_size)
                elif response.status_code == 200:
                    # Server indicated upload complete.
                    logger.debug(f'Completed file upload for "{file_path.name}"')
                    acked = file_size
                    if progress_callback:
                        progress_callback(acked, file_size)
                else:
                    raise APIError.from_response(response)

        # Step 3: Attach uploaded file to the LMS.
        self._attach_dropbox_folder_submission_feedback_file(
            org_unit_id, folder_id, entity_type, entity_id, file_key
        )

    def _get_dropbox_folder_categories(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-categories-"""
        return self._get_json(self._get_le_route(f"{org_unit_id}/dropbox/categories/"))

    def get_dropbox_folder_categories(
        self, org_unit_id: int
    ) -> list[bsapi.types.DropboxCategory]:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-categories-"""
        return [
            bsapi.types.DropboxCategory.from_json(category)
            for category in self._get_dropbox_folder_categories(org_unit_id)
        ]

    def _get_dropbox_folder_category(self, org_unit_id: int, category_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-categories-(categoryId)"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/dropbox/categories/{category_id}")
        )

    def get_dropbox_folder_category(
        self, org_unit_id: int, category_id: int
    ) -> bsapi.types.DropboxCategoryWithFolders:
        """Wrapper for https://docs.valence.desire2learn.com/res/dropbox.html#get--d2l-api-le-(version)-(orgUnitId)-dropbox-categories-(categoryId)"""
        return bsapi.types.DropboxCategoryWithFolders.from_json(
            self._get_dropbox_folder_category(org_unit_id, category_id)
        )

    def _get_group_categories(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-"""
        return self._get_json(self._get_lp_route(f"{org_unit_id}/groupcategories/"))

    def get_group_categories(
        self, org_unit_id: int
    ) -> list[bsapi.types.GroupCategoryData]:
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-"""
        return [
            bsapi.types.GroupCategoryData.from_json(category)
            for category in self._get_group_categories(org_unit_id)
        ]

    def _get_group_category(self, org_unit_id: int, group_category_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)"""
        return self._get_json(
            self._get_lp_route(f"{org_unit_id}/groupcategories/{group_category_id}")
        )

    def get_group_category(
        self, org_unit_id: int, group_category_id: int
    ) -> bsapi.types.GroupCategoryData:
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)"""
        return bsapi.types.GroupCategoryData.from_json(
            self._get_group_category(org_unit_id, group_category_id)
        )

    def _get_groups(self, org_unit_id: int, group_category_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-"""
        return self._get_json(
            self._get_lp_route(
                f"{org_unit_id}/groupcategories/{group_category_id}/groups/"
            )
        )

    def get_groups(
        self, org_unit_id: int, group_category_id: int
    ) -> list[bsapi.types.GroupData]:
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-"""
        return [
            bsapi.types.GroupData.from_json(group)
            for group in self._get_groups(org_unit_id, group_category_id)
        ]

    def _get_group(self, org_unit_id: int, group_category_id: int, group_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-(groupId)"""
        return self._get_json(
            self._get_lp_route(
                f"{org_unit_id}/groupcategories/{group_category_id}/groups/{group_id}"
            )
        )

    def get_group(
        self, org_unit_id: int, group_category_id: int, group_id: int
    ) -> bsapi.types.GroupData:
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-(groupId)"""
        return bsapi.types.GroupData.from_json(
            self._get_group(org_unit_id, group_category_id, group_id)
        )

    def remove_user_from_group(
        self, org_unit_id: int, group_category_id: int, group_id: int, user_id: int
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#delete--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-(groupId)-enrollments-(userId)"""
        self._delete(
            self._get_lp_route(
                f"{org_unit_id}/groupcategories/{group_category_id}/groups/{group_id}/enrollments/{user_id}"
            ),
            check_status=True,
        )

    def enroll_user_in_group(
        self, org_unit_id: int, group_category_id: int, group_id: int, user_id: int
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/groups.html#post--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-(groupId)-enrollments-"""
        group_enrollment = {"UserId": user_id}

        self._post(
            self._get_lp_route(
                f"{org_unit_id}/groupcategories/{group_category_id}/groups/{group_id}/enrollments/"
            ),
            json=group_enrollment,
            check_status=True,
        )

    def _get_grade_schemes(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-schemes-"""
        return self._get_json(self._get_le_route(f"{org_unit_id}/grades/schemes/"))

    def get_grade_schemes(self, org_unit_id: int) -> list[bsapi.types.GradeScheme]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-schemes-"""
        return [
            bsapi.types.GradeScheme.from_json(scheme)
            for scheme in self._get_grade_schemes(org_unit_id)
        ]

    def _get_grade_scheme(self, org_unit_id: int, grade_scheme_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-schemes-(gradeSchemeId)"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/grades/schemes/{grade_scheme_id}")
        )

    def get_grade_scheme(
        self, org_unit_id: int, grade_scheme_id: int
    ) -> bsapi.types.GradeScheme:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-schemes-(gradeSchemeId)"""
        return bsapi.types.GradeScheme.from_json(
            self._get_grade_scheme(org_unit_id, grade_scheme_id)
        )

    def _get_grade_objects(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-"""
        return self._get_json(self._get_le_route(f"{org_unit_id}/grades/"))

    def get_grade_objects(self, org_unit_id: int) -> list[bsapi.types.GradeObject]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-"""
        return [
            bsapi.types.GradeObject.from_json(grade)
            for grade in self._get_grade_objects(org_unit_id)
        ]

    def _get_grade_object(self, org_unit_id: int, grade_object_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/grades/{grade_object_id}")
        )

    def get_grade_object(
        self, org_unit_id: int, grade_object_id: int
    ) -> bsapi.types.GradeObject:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)"""
        return bsapi.types.GradeObject.from_json(
            self._get_grade_object(org_unit_id, grade_object_id)
        )

    def _get_grade_categories(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-categories-"""
        return self._get_json(self._get_le_route(f"{org_unit_id}/grades/categories/"))

    def get_grade_categories(
        self, org_unit_id: int
    ) -> list[bsapi.types.GradeObjectCategory]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-categories-"""
        return [
            bsapi.types.GradeObjectCategory.from_json(category)
            for category in self._get_grade_categories(org_unit_id)
        ]

    def _get_grade_category(self, org_unit_id: int, grade_category_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-categories-(categoryId)"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/grades/categories/{grade_category_id}")
        )

    def get_grade_category(
        self, org_unit_id: int, grade_category_id: int
    ) -> bsapi.types.GradeObjectCategory:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-categories-(categoryId)"""
        return bsapi.types.GradeObjectCategory.from_json(
            self._get_grade_category(org_unit_id, grade_category_id)
        )

    def _get_grade_values(
        self, org_unit_id: int, grade_object_id: int, is_graded: bool = None
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-"""
        params = dict()
        if is_graded is not None:
            params["isGraded"] = is_graded

        return self._get_paged(
            self._get_le_route(f"{org_unit_id}/grades/{grade_object_id}/values/"),
            query_params=params,
        )

    def get_grade_values(
        self, org_unit_id: int, grade_object_id: int, is_graded: bool = None
    ) -> list[bsapi.types.UserGradeValue]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-"""
        return [
            bsapi.types.UserGradeValue.from_json(grade)
            for grade in self._get_grade_values(org_unit_id, grade_object_id, is_graded)
        ]

    def _get_grade_value(self, org_unit_id: int, grade_object_id: int, user_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-(userId)"""
        return self._get_json(
            self._get_le_route(
                f"{org_unit_id}/grades/{grade_object_id}/values/{user_id}"
            ),
            none_on_404=True,
        )

    def get_grade_value(
        self, org_unit_id: int, grade_object_id: int, user_id: int
    ) -> Optional[bsapi.types.GradeValue]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-(userId)"""
        json_obj = self._get_grade_value(org_unit_id, grade_object_id, user_id)

        return bsapi.types.GradeValue.from_json(json_obj) if json_obj else None

    def _get_my_grade_value(self, org_unit_id: int, grade_object_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-myGradeValue"""
        return self._get_json(
            self._get_le_route(
                f"{org_unit_id}/grades/{grade_object_id}/values/myGradeValue"
            ),
            none_on_404=True,
        )

    def get_my_grade_value(
        self, org_unit_id: int, grade_object_id: int
    ) -> Optional[bsapi.types.GradeValue]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-myGradeValue"""
        json_obj = self._get_my_grade_value(org_unit_id, grade_object_id)

        return bsapi.types.GradeValue.from_json(json_obj) if json_obj else None

    def _get_my_grade_values(self, org_unit_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-values-myGradeValues-"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/grades/values/myGradeValues/")
        )

    def get_my_grade_values(self, org_unit_id: int) -> list[bsapi.types.GradeValue]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-values-myGradeValues-"""
        return [
            bsapi.types.GradeValue.from_json(grade)
            for grade in self._get_my_grade_values(org_unit_id)
        ]

    def _get_user_grade_values(self, org_unit_id: int, user_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-values-(userId)-"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/grades/values/{user_id}/")
        )

    def get_user_grade_values(
        self, org_unit_id: int, user_id: int
    ) -> list[bsapi.types.GradeValue]:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-values-(userId)-"""
        return [
            bsapi.types.GradeValue.from_json(grade)
            for grade in self._get_user_grade_values(org_unit_id, user_id)
        ]

    def _get_grade_statistics(self, org_unit_id: int, grade_object_id: int):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-statistics"""
        return self._get_json(
            self._get_le_route(f"{org_unit_id}/grades/{grade_object_id}/statistics")
        )

    def get_grade_statistics(
        self, org_unit_id: int, grade_object_id: int
    ) -> bsapi.types.GradeStatisticsInfo:
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#get--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-statistics"""
        return bsapi.types.GradeStatisticsInfo.from_json(
            self._get_grade_statistics(org_unit_id, grade_object_id)
        )

    def _set_grade_value(
        self,
        org_unit_id: int,
        grade_object_id: int,
        user_id: int,
        object_type: int,
        field_name: str,
        field_value: any,
        comment: str,
        private_comment: str = "",
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#put--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-(userId)"""
        incoming_grades_value = {
            "Comments": {"Content": comment, "Type": "Text"},
            "PrivateComments": {"Content": private_comment, "Type": "Text"},
            "GradeObjectType": object_type,
            field_name: field_value,
        }

        self._put(
            self._get_le_route(
                f"{org_unit_id}/grades/{grade_object_id}/values/{user_id}"
            ),
            json=incoming_grades_value,
            check_status=True,
        )

    def set_grade_value(
        self,
        org_unit_id: int,
        grade_object_id: int,
        user_id: int,
        object_type: int,
        grade_value: any,
        comment: str,
        private_comment: str = "",
    ):
        """Wrapper for https://docs.valence.desire2learn.com/res/grade.html#put--d2l-api-le-(version)-(orgUnitId)-grades-(gradeObjectId)-values-(userId)"""
        grade_mapping = {
            bsapi.types.GRADE_OBJECT_NUMERIC: ("PointsNumerator", numbers.Real),
            bsapi.types.GRADE_OBJECT_PASS_FAIL: ("Pass", bool),
            bsapi.types.GRADE_OBJECT_SELECT_BOX: ("Value", str),
            bsapi.types.GRADE_OBJECT_TEXT: ("Text", str),
        }
        assert object_type in grade_mapping, "Unknown object type"
        field_name, type_ = grade_mapping[object_type]
        assert isinstance(
            grade_value, type_
        ), f'Incorrect grade value type "{type(grade_value).__name__}", expected "{type_.__name__}"'

        # Since bool is a subclass of int we need to special case it. Otherwise, the json serialization will encode True
        # and False as true/false, rather than a numeric value 1/0, for numeric grades.
        if (
            object_type == bsapi.types.GRADE_OBJECT_NUMERIC
            and type(grade_value) == bool
        ):
            field_value = float(grade_value)
        else:
            field_value = grade_value

        self._set_grade_value(
            org_unit_id,
            grade_object_id,
            user_id,
            object_type,
            field_name,
            field_value,
            comment,
            private_comment,
        )

    def set_grade_value_numeric(
        self,
        org_unit_id: int,
        grade_object_id: int,
        user_id: int,
        grade: float,
        comment: str,
        private_comment: str = "",
    ):
        """Call `self.set_grade_value for Numeric grade types."""
        self.set_grade_value(
            org_unit_id,
            grade_object_id,
            user_id,
            bsapi.types.GRADE_OBJECT_NUMERIC,
            grade,
            comment,
            private_comment,
        )

    def set_grade_value_pass_fail(
        self,
        org_unit_id: int,
        grade_object_id: int,
        user_id: int,
        pass_fail: bool,
        comment: str,
        private_comment: str = "",
    ):
        """Call `self.set_grade_value for PassFail grade types."""
        self.set_grade_value(
            org_unit_id,
            grade_object_id,
            user_id,
            bsapi.types.GRADE_OBJECT_PASS_FAIL,
            pass_fail,
            comment,
            private_comment,
        )

    def set_grade_value_select_box(
        self,
        org_unit_id: int,
        grade_object_id: int,
        user_id: int,
        value: str,
        comment: str,
        private_comment: str = "",
    ):
        """Call `self.set_grade_value for SelectBox grade types."""
        self.set_grade_value(
            org_unit_id,
            grade_object_id,
            user_id,
            bsapi.types.GRADE_OBJECT_SELECT_BOX,
            value,
            comment,
            private_comment,
        )

    def set_grade_value_text(
        self,
        org_unit_id: int,
        grade_object_id: int,
        user_id: int,
        text: str,
        comment: str,
        private_comment: str = "",
    ):
        """Call `self.set_grade_value for Text grade types."""
        self.set_grade_value(
            org_unit_id,
            grade_object_id,
            user_id,
            bsapi.types.GRADE_OBJECT_TEXT,
            text,
            comment,
            private_comment,
        )

    def _get_lp_route(self, api_route: str) -> str:
        return f"/d2l/api/lp/{self.lp_version}/{api_route}"

    def _get_le_route(self, api_route: str) -> str:
        return f"/d2l/api/le/{self.le_version}/{api_route}"

    def _get_paged(self, api_route: str, query_params=None):
        objects = []
        page = self._get_json(api_route, query_params)

        objects.extend(page["Objects"])

        while page["Next"] is not None:
            logging.debug(f'Continuing with next page: {page["Next"]}')
            components = urllib.parse.urlsplit(page["Next"])
            new_query_params = urllib.parse.parse_qs(components.query)
            page = self._get_json(components.path, new_query_params)
            objects.extend(page["Objects"])

        return objects

    def _get_paged_set(self, api_route: str, query_params=None):
        items = []
        segment = self._get_json(api_route, query_params)

        items.extend(segment["Items"])

        while segment["PagingInfo"]["HasMoreItems"]:
            logging.debug(
                f'Continuing with next bookmark: {segment["PagingInfo"]["Bookmark"]}'
            )
            if query_params is None:
                query_params = dict()
            query_params["bookmark"] = segment["PagingInfo"]["Bookmark"]
            segment = self._get_json(api_route, query_params)
            items.extend(segment["Items"])

        return items

    def _get_json(self, api_route: str, query_params=None, none_on_404: bool = False):
        response = self._get(api_route, query_params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404 and none_on_404:
            return None
        else:
            raise APIError.from_response(response)

    def _get_binary(self, api_route: str, query_params=None) -> bytes:
        response = self._get(api_route, query_params)

        if response.status_code == 200:
            return response.content
        else:
            raise APIError.from_response(response)

    def _get(self, api_route: str, query_params=None) -> requests.Response:
        url = self._create_url(api_route)
        headers = self._get_auth_headers()
        try:
            response = requests.get(url, params=query_params, headers=headers)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to perform GET due to request exception: {e}")

        return response

    def _put(
        self, api_route: str, json=None, check_status: bool = False
    ) -> requests.Response:
        url = self._create_url(api_route)
        headers = self._get_auth_headers()
        try:
            response = requests.put(url, json=json, headers=headers)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to perform PUT due to request exception: {e}")

        if check_status and response.status_code != 200:
            raise APIError.from_response(response)

        return response

    def _post(
        self,
        api_route: str,
        json=None,
        check_status: bool = False,
        data=None,
        headers=None,
        allow_redirects: bool = True,
    ) -> requests.Response:
        url = self._create_url(api_route)
        auth_headers = self._get_auth_headers()
        if headers:
            auth_headers.update(headers)
        try:
            response = requests.post(
                url,
                json=json,
                data=data,
                headers=auth_headers,
                allow_redirects=allow_redirects,
            )
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to perform POST due to request exception: {e}")

        if check_status and response.status_code != 200:
            raise APIError.from_response(response)

        return response

    def _delete(
        self, api_route: str, json=None, check_status: bool = False
    ) -> requests.Response:
        url = self._create_url(api_route)
        headers = self._get_auth_headers()
        try:
            response = requests.delete(url, json=json, headers=headers)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to perform DELETE due to request exception: {e}")

        if check_status and response.status_code != 200:
            raise APIError.from_response(response)

        return response
