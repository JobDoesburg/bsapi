from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def _parse_utc_date_time(value: str) -> Optional[datetime]:
    """Parse a UTCDateTime string as described by https://docs.valence.desire2learn.com/basic/conventions.html#term-UTCDateTime.

    :param value: The UTCDateTime string.
    :return: The parsed datetime, or `None` if `value` was `None` or empty.
    """
    if value:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    else:
        return None


@dataclass
class WhoAmIUser:
    """See https://docs.valence.desire2learn.com/res/user.html#User.WhoAmIUser"""

    identifier: int
    first_name: str
    last_name: str
    unique_name: str
    profile_identifier: str
    pronouns: Optional[str]

    @staticmethod
    def from_json(json_obj: dict):
        return WhoAmIUser(
            identifier=int(json_obj["Identifier"]),
            first_name=json_obj["FirstName"],
            last_name=json_obj["LastName"],
            unique_name=json_obj["UniqueName"],
            profile_identifier=json_obj["ProfileIdentifier"],
            pronouns=json_obj["Pronouns"],
        )


@dataclass
class Role:
    """See https://docs.valence.desire2learn.com/res/user.html#User.Role"""

    identifier: str
    display_name: str
    code: Optional[str]
    description: str
    role_alias: str
    is_cascading: bool
    access_future_courses: bool
    access_inactive_courses: bool
    access_past_courses: bool
    show_in_grades: bool
    show_in_user_progress: bool
    in_class_list: bool

    @staticmethod
    def from_json(json_obj: dict):
        return Role(
            identifier=json_obj["Identifier"],
            display_name=json_obj["DisplayName"],
            code=json_obj["Code"],
            description=json_obj.get("Description", ""),
            role_alias=json_obj.get("RoleAlias", ""),
            is_cascading=json_obj.get("IsCascading", False),
            access_future_courses=json_obj.get("AccessFutureCourses", False),
            access_inactive_courses=json_obj.get("AccessInactiveCourses", False),
            access_past_courses=json_obj.get("AccessPastCourses", False),
            show_in_grades=json_obj.get("ShowInGrades", False),
            show_in_user_progress=json_obj.get("ShowInGrades", False),
            in_class_list=json_obj.get("InClassList", False),
        )


@dataclass
class ProductVersions:
    """See https://docs.valence.desire2learn.com/res/apiprop.html#Version.ProductVersions"""

    product_code: str
    latest_version: str
    supported_versions: list[str]

    @staticmethod
    def from_json(json_obj: dict):
        return ProductVersions(
            product_code=json_obj["ProductCode"],
            latest_version=json_obj["LatestVersion"],
            supported_versions=json_obj["SupportedVersions"],
        )


@dataclass
class OrgUnitTypeInfo:
    """See https://docs.valence.desire2learn.com/res/orgunit.html#OrgUnit.OrgUnitTypeInfo"""

    id: int
    code: str
    name: str

    @staticmethod
    def from_json(json_obj: dict):
        return OrgUnitTypeInfo(
            id=json_obj["Id"], code=json_obj["Code"], name=json_obj["Name"]
        )


@dataclass
class OrgUnitInfo:
    """See https://docs.valence.desire2learn.com/res/enroll.html#Enrollment.OrgUnitInfo"""

    id: int
    type: OrgUnitTypeInfo
    name: str
    code: Optional[str]
    home_url: Optional[str]
    image_url: Optional[str]

    @staticmethod
    def from_json(json_obj: dict):
        return OrgUnitInfo(
            id=json_obj["Id"],
            type=OrgUnitTypeInfo.from_json(json_obj["Type"]),
            name=json_obj["Name"],
            code=json_obj["Code"],
            home_url=json_obj["HomeUrl"],
            image_url=json_obj["ImageUrl"],
        )


@dataclass
class MyOrgUnitInfo:
    """See https://docs.valence.desire2learn.com/res/enroll.html#Enrollment.MyOrgUnitInfo"""

    @dataclass
    class Access:
        is_active: bool
        start_date: Optional[datetime]
        end_date: Optional[datetime]
        can_access: bool
        classlist_role_name: Optional[str]
        lis_roles: list[str]
        last_accessed: Optional[datetime]

    org_unit: OrgUnitInfo
    access: Access
    pin_date: Optional[datetime]

    @staticmethod
    def from_json(json_obj: dict):
        return MyOrgUnitInfo(
            org_unit=OrgUnitInfo.from_json(json_obj["OrgUnit"]),
            access=MyOrgUnitInfo.Access(
                is_active=json_obj["Access"]["IsActive"],
                start_date=_parse_utc_date_time(
                    json_obj["Access"].get("StartDate", None)
                ),
                end_date=_parse_utc_date_time(json_obj["Access"].get("EndDate", None)),
                can_access=json_obj["Access"]["CanAccess"],
                classlist_role_name=json_obj["Access"].get("ClasslistRoleName", None),
                lis_roles=json_obj["Access"].get("LISRoles", []),
                last_accessed=_parse_utc_date_time(
                    json_obj["Access"].get("LastAccessed", None)
                ),
            ),
            pin_date=_parse_utc_date_time(json_obj["PinDate"]),
        )


@dataclass
class ClasslistUser:
    """See https://docs.valence.desire2learn.com/res/enroll.html#Enrollment.ClasslistUser"""

    identifier: int
    profile_identifier: str
    display_name: str
    username: Optional[str]
    org_defined_id: Optional[str]
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    role_id: Optional[int]
    last_accessed: Optional[datetime]
    is_online: bool
    classlist_role_display_name: str

    @staticmethod
    def from_json(json_obj: dict):
        return ClasslistUser(
            identifier=int(json_obj["Identifier"]),
            profile_identifier=json_obj["ProfileIdentifier"],
            display_name=json_obj["DisplayName"],
            username=json_obj["Username"],
            org_defined_id=json_obj["OrgDefinedId"],
            email=json_obj["Email"],
            first_name=json_obj["FirstName"],
            last_name=json_obj["LastName"],
            role_id=json_obj["RoleId"],
            last_accessed=_parse_utc_date_time(json_obj["LastAccessed"]),
            is_online=json_obj["IsOnline"],
            classlist_role_display_name=json_obj.get("ClasslistRoleDisplayName", ""),
        )


@dataclass
class RoleInfo:
    """See https://docs.valence.desire2learn.com/res/enroll.html#Enrollment.RoleInfo"""

    id: int
    code: Optional[str]
    name: str

    @staticmethod
    def from_json(json_obj: dict):
        return RoleInfo(id=json_obj["Id"], code=json_obj["Code"], name=json_obj["Name"])


@dataclass
class User:
    """See https://docs.valence.desire2learn.com/res/user.html#User.User"""

    identifier: Optional[str]
    display_name: Optional[str]
    email_address: Optional[str]
    org_defined_id: Optional[str]
    profile_badge_url: Optional[str]
    profile_identifier: Optional[str]
    user_name: Optional[str]

    @staticmethod
    def from_json(json_obj: dict):
        return User(
            identifier=json_obj["Identifier"],
            display_name=json_obj["DisplayName"],
            email_address=json_obj["EmailAddress"],
            org_defined_id=json_obj["OrgDefinedId"],
            profile_badge_url=json_obj["ProfileBadgeUrl"],
            profile_identifier=json_obj["ProfileIdentifier"],
            user_name=json_obj.get("UserName", None),
        )


@dataclass
class OrgUnitUser:
    """See https://docs.valence.desire2learn.com/res/enroll.html#Enrollment.OrgUnitUser"""

    user: User
    role: RoleInfo

    @staticmethod
    def from_json(json_obj: dict):
        return OrgUnitUser(
            user=User.from_json(json_obj["User"]),
            role=RoleInfo.from_json(json_obj["Role"]),
        )


@dataclass
class RichText:
    """See https://docs.valence.desire2learn.com/basic/conventions.html#term-RichText"""

    text: str
    html: Optional[str]

    @staticmethod
    def from_json(json_obj: dict):
        return RichText(text=json_obj.get("Text", ""), html=json_obj.get("Html", None))


# https://docs.valence.desire2learn.com/res/assessment.html#term-RUBRIC_T
RUBRIC_HOLISTIC = 0
RUBRIC_ANALYTIC = 1

# https://docs.valence.desire2learn.com/res/assessment.html#term-SCORING_M
SCORING_TEXT_ONLY = 0
SCORING_POINTS = 1
SCORING_TEXT_AND_NUMERIC = 2
SCORING_CUSTOM_POINTS = 3


@dataclass
class Level:
    """See https://docs.valence.desire2learn.com/res/assessment.html#Rubric.Level"""

    id: int
    name: str
    points: Optional[float]

    @staticmethod
    def from_json(json_obj: dict):
        return Level(
            id=json_obj["Id"], name=json_obj["Name"], points=json_obj["Points"]
        )


@dataclass
class OverallLevel:
    """See https://docs.valence.desire2learn.com/res/assessment.html#Rubric.OverallLevel"""

    id: int
    name: str
    range_start: Optional[float]
    description: RichText
    feedback: RichText

    @staticmethod
    def from_json(json_obj: dict):
        return OverallLevel(
            id=json_obj["Id"],
            name=json_obj["Name"],
            range_start=json_obj["RangeStart"],
            description=RichText.from_json(json_obj["Description"]),
            feedback=RichText.from_json(json_obj["Feedback"]),
        )


@dataclass
class CriteriaGroup:
    """See https://docs.valence.desire2learn.com/res/assessment.html#Rubric.CriteriaGroup"""

    @dataclass
    class CriterionCell:
        feedback: RichText
        description: RichText
        points: Optional[float]

        @staticmethod
        def from_json(json_obj: dict):
            return CriteriaGroup.CriterionCell(
                feedback=RichText.from_json(json_obj["Feedback"]),
                description=RichText.from_json(json_obj["Description"]),
                points=json_obj["Points"],
            )

    @dataclass
    class Criterion:
        id: int
        name: str
        cells: list["CriteriaGroup.CriterionCell"]

        @staticmethod
        def from_json(json_obj: dict):
            return CriteriaGroup.Criterion(
                id=json_obj["Id"],
                name=json_obj["Name"],
                cells=[
                    CriteriaGroup.CriterionCell.from_json(cell)
                    for cell in json_obj["Cells"]
                ],
            )

    name: str
    levels: list[Level]
    criteria: list[Criterion]

    @staticmethod
    def from_json(json_obj: dict):
        return CriteriaGroup(
            name=json_obj["Name"],
            levels=[Level.from_json(level) for level in json_obj["Levels"]],
            criteria=[
                CriteriaGroup.Criterion.from_json(criterion)
                for criterion in json_obj["Criteria"]
            ],
        )


@dataclass
class Rubric:
    """See https://docs.valence.desire2learn.com/res/assessment.html#Rubric.Rubric"""

    rubric_id: int
    name: str
    description: RichText
    rubric_type: int  # RUBRIC_T
    scoring_method: int  # SCORING_M
    criteria_groups: list[CriteriaGroup]
    overall_levels: list[OverallLevel]

    @staticmethod
    def from_json(json_obj: dict):
        return Rubric(
            rubric_id=json_obj["RubricId"],
            name=json_obj["Name"],
            description=RichText.from_json(json_obj["Description"]),
            rubric_type=json_obj["RubricType"],
            scoring_method=json_obj["ScoringMethod"],
            criteria_groups=[
                CriteriaGroup.from_json(group) for group in json_obj["CriteriaGroups"]
            ],
            overall_levels=[
                OverallLevel.from_json(level) for level in json_obj["OverallLevels"]
            ],
        )


@dataclass
class RubricAssessment:
    """See https://docs.valence.desire2learn.com/res/assessment.html#Rubric.RubricAssessment"""

    @dataclass
    class OverallLevel:
        level_id: int
        feedback: RichText

        @staticmethod
        def from_json(json_obj: dict):
            return RubricAssessment.OverallLevel(
                level_id=json_obj["LevelId"],
                feedback=RichText.from_json(json_obj["Feedback"]),
            )

    @dataclass
    class CriteriaOutcome:
        criterion_id: int
        level_id: Optional[int]
        score: Optional[float]
        score_is_overridden: bool
        feedback: RichText
        feedback_is_overridden: bool

        @staticmethod
        def from_json(json_obj: dict):
            return RubricAssessment.CriteriaOutcome(
                criterion_id=json_obj["CriterionId"],
                level_id=json_obj["LevelId"],
                score=json_obj["Score"],
                score_is_overridden=json_obj["ScoreIsOverridden"],
                feedback=RichText.from_json(json_obj["Feedback"]),
                feedback_is_overridden=json_obj["FeedbackIsOverridden"],
            )

    rubric_id: int
    overall_score: Optional[float]
    overall_feedback: RichText
    overall_level: Optional[OverallLevel]
    overall_score_overridden: bool
    overall_feedback_overridden: bool
    criteria_outcome: list[CriteriaOutcome]

    @staticmethod
    def from_json(json_obj: dict):
        return RubricAssessment(
            rubric_id=json_obj["RubricId"],
            overall_score=json_obj["OverallScore"],
            overall_feedback=RichText.from_json(json_obj["OverallFeedback"]),
            overall_level=RubricAssessment.OverallLevel.from_json(
                json_obj["OverallLevel"]
            )
            if json_obj["OverallLevel"]
            else None,
            overall_score_overridden=json_obj["OverallScoreOverridden"],
            overall_feedback_overridden=json_obj["OverallFeedbackOverridden"],
            criteria_outcome=[
                RubricAssessment.CriteriaOutcome.from_json(outcome)
                for outcome in json_obj["CriteriaOutcome"]
            ],
        )


# https://docs.valence.desire2learn.com/res/dropbox.html#term-ENTITYDROPBOXSTATUS_T
ENTITY_DROPBOX_STATUS_UNSUBMITTED = 0
ENTITY_DROPBOX_STATUS_SUBMITTED = 1
ENTITY_DROPBOX_STATUS_DRAFT = 2
ENTITY_DROPBOX_STATUS_PUBLISHED = 3

# https://docs.valence.desire2learn.com/res/dropbox.html#term-DROPBOXTYPE_T
DROPBOX_TYPE_GROUP = 1
DROPBOX_TYPE_INDIVIDUAL = 2

# https://docs.valence.desire2learn.com/res/dropbox.html#term-SUBMISSIONTYPE_T
SUBMISSION_TYPE_FILE = 0
SUBMISSION_TYPE_TEXT = 1
SUBMISSION_TYPE_ON_PAPER = 2
SUBMISSION_TYPE_OBSERVED = 3

# https://docs.valence.desire2learn.com/res/dropbox.html#term-DROPBOX_COMPLETIONTYPE_T
DROPBOX_COMPLETION_TYPE_ON_SUBMISSION = 0
DROPBOX_COMPLETION_TYPE_DUE_DATE = 1
DROPBOX_COMPLETION_TYPE_MANUALLY_BY_LEARNER = 2
DROPBOX_COMPLETION_TYPE_ON_EVALUATION = 3

# https://docs.valence.desire2learn.com/res/dropbox.html#term-DROPBOX_LINK_ATTACHMENT_T
DROPBOX_LINK_ATTACHMENT_EXTERNAL = "External"
DROPBOX_LINK_ATTACHMENT_INTERNAL = "Internal"
DROPBOX_LINK_ATTACHMENT_MEDIA_CONTENT = "MediaContent"

# https://docs.valence.desire2learn.com/res/apiprop.html#term-AVAILABILITY_T
AVAILABILITY_ACCESS_RESTRICTED = 0
AVAILABILITY_SUBMISSION_RESTRICTED = 1
AVAILABILITY_HIDDEN = 2


@dataclass
class DropboxFolder:
    """See https://docs.valence.desire2learn.com/res/dropbox.html#Dropbox.DropboxFolder"""

    @dataclass
    class File:
        file_id: int
        file_name: str
        size: int

        @staticmethod
        def from_json(json_obj: dict):
            return DropboxFolder.File(
                file_id=json_obj["FileId"],
                file_name=json_obj["FileName"],
                size=json_obj["Size"],
            )

    @dataclass
    class Availability:
        start_date: Optional[datetime]
        end_date: Optional[datetime]
        start_date_availability_type: Optional[str]  # AVAILABILITY_T
        end_date_availability_type: Optional[str]  # AVAILABILITY_T

        @staticmethod
        def from_json(json_obj: dict):
            return DropboxFolder.Availability(
                start_date=_parse_utc_date_time(json_obj["StartDate"]),
                end_date=_parse_utc_date_time(json_obj["EndDate"]),
                start_date_availability_type=json_obj.get(
                    "StartDateAvailabilityType", None
                ),
                end_date_availability_type=json_obj.get(
                    "EndDateAvailabilityType", None
                ),
            )

    @dataclass
    class Assessment:
        score_denominator: Optional[float]
        rubrics: list[Rubric]

        @staticmethod
        def from_json(json_obj: dict):
            return DropboxFolder.Assessment(
                score_denominator=json_obj["ScoreDenominator"],
                rubrics=[Rubric.from_json(rubric) for rubric in json_obj["Rubrics"]],
            )

    @dataclass
    class Link:
        link_id: int
        link_name: str
        href: str

        @staticmethod
        def from_json(json_obj: dict):
            return DropboxFolder.Link(
                link_id=json_obj["LinkId"],
                link_name=json_obj["LinkName"],
                href=json_obj["Href"],
            )

    id: int
    category_id: Optional[int]
    name: str
    custom_instructions: RichText
    attachments: list[File]
    total_files: int
    unread_files: int
    flagged_files: int
    total_users: int
    total_users_with_submissions: int
    total_users_with_feedback: int
    availability: Optional[Availability]
    group_type_id: Optional[int]
    due_date: Optional[datetime]
    display_in_calendar: bool
    assessment: Assessment
    notification_email: Optional[str]
    is_hidden: bool
    link_attachments: list[Link]
    activity_id: Optional[str]
    is_anonymous: bool
    dropbox_type: str  # DROPBOXTYPE_T
    submission_type: str  # SUBMISSIONTYPE_T
    completion_type: str  # DROPBOX_COMPLETIONTYPE_T
    grade_item_id: Optional[int]
    allow_only_users_with_special_access: Optional[bool]

    @staticmethod
    def from_json(json_obj: dict):
        return DropboxFolder(
            id=json_obj["Id"],
            category_id=json_obj["CategoryId"],
            name=json_obj["Name"],
            custom_instructions=RichText.from_json(json_obj["CustomInstructions"]),
            attachments=[
                DropboxFolder.File.from_json(file) for file in json_obj["Attachments"]
            ],
            total_files=json_obj["TotalFiles"],
            unread_files=json_obj["UnreadFiles"],
            flagged_files=json_obj["FlaggedFiles"],
            total_users=json_obj["TotalUsers"],
            total_users_with_submissions=json_obj["TotalUsersWithSubmissions"],
            total_users_with_feedback=json_obj["TotalUsersWithFeedback"],
            availability=DropboxFolder.Availability.from_json(json_obj["Availability"])
            if json_obj["Availability"]
            else None,
            group_type_id=json_obj["GroupTypeId"],
            due_date=_parse_utc_date_time(json_obj["DueDate"]),
            display_in_calendar=json_obj["DisplayInCalendar"],
            assessment=DropboxFolder.Assessment.from_json(json_obj["Assessment"]),
            notification_email=json_obj["NotificationEmail"],
            is_hidden=json_obj["IsHidden"],
            link_attachments=[
                DropboxFolder.Link.from_json(link)
                for link in json_obj["LinkAttachments"]
            ],
            activity_id=json_obj["ActivityId"],
            is_anonymous=json_obj["IsAnonymous"],
            dropbox_type=json_obj["DropboxType"],
            submission_type=json_obj["SubmissionType"],
            completion_type=json_obj["CompletionType"],
            grade_item_id=json_obj["GradeItemId"],
            allow_only_users_with_special_access=json_obj[
                "AllowOnlyUsersWithSpecialAccess"
            ],
        )


@dataclass
class DropboxFeedbackOut:
    """See https://docs.valence.desire2learn.com/res/dropbox.html#Dropbox.DropboxFeedbackOut"""

    @dataclass
    class File:
        file_id: int
        file_name: str
        size: int

        @staticmethod
        def from_json(json_obj: dict):
            return DropboxFeedbackOut.File(
                file_id=json_obj["FileId"],
                file_name=json_obj["FileName"],
                size=json_obj["Size"],
            )

    @dataclass
    class Link:
        type: str  # DROPBOX_LINK_ATTACHMENT_T
        link_id: int
        link_name: str
        href: Optional[str]

        @staticmethod
        def from_json(json_obj: dict):
            return DropboxFeedbackOut.Link(
                type=json_obj["Type"],
                link_id=json_obj["LinkId"],
                link_name=json_obj["LinkName"],
                href=json_obj["Href"],
            )

    score: Optional[float]
    feedback: Optional[RichText]
    rubric_assessments: list[RubricAssessment]
    is_graded: bool
    files: list[File]
    links: list[Link]
    graded_symbol: Optional[str]

    @staticmethod
    def from_json(json_obj: dict):
        return DropboxFeedbackOut(
            score=json_obj["Score"],
            feedback=RichText.from_json(json_obj["Feedback"])
            if json_obj["Feedback"]
            else None,
            rubric_assessments=[
                RubricAssessment.from_json(assessment)
                for assessment in json_obj["RubricAssessments"]
            ],
            is_graded=json_obj["IsGraded"],
            files=[
                DropboxFeedbackOut.File.from_json(file) for file in json_obj["Files"]
            ],
            links=[
                DropboxFeedbackOut.Link.from_json(link) for link in json_obj["Links"]
            ],
            graded_symbol=json_obj["GradedSymbol"],
        )


@dataclass
class Entity:
    """See https://docs.valence.desire2learn.com/res/dropbox.html#Dropbox.Entity"""

    entity_id: int
    entity_type: str
    display_name: Optional[str]
    name: Optional[str]

    @staticmethod
    def from_json(json_obj: dict):
        return Entity(
            entity_id=json_obj["EntityId"],
            entity_type=json_obj["EntityType"],
            display_name=json_obj.get("DisplayName", None),
            name=json_obj.get("Name", None),
        )

    def get_name(self) -> str:
        if self.entity_type == "Group":
            return self.name
        elif self.entity_type == "User":
            return self.display_name
        else:
            return ""


@dataclass
class EntityDropBox:
    """See https://docs.valence.desire2learn.com/res/dropbox.html#Dropbox.EntityDropbox"""

    @dataclass
    class Submission:
        @dataclass
        class SubmittedBy:
            identifier: str
            display_name: str

            @staticmethod
            def from_json(json_obj: dict):
                return EntityDropBox.Submission.SubmittedBy(
                    identifier=json_obj["Identifier"],
                    display_name=json_obj["DisplayName"],
                )

        @dataclass
        class File:
            file_id: int
            file_name: str
            size: int
            is_read: bool
            is_flagged: bool

            @staticmethod
            def from_json(json_obj: dict):
                return EntityDropBox.Submission.File(
                    file_id=json_obj["FileId"],
                    file_name=json_obj["FileName"],
                    size=json_obj["Size"],
                    is_read=json_obj["IsRead"],
                    is_flagged=json_obj["IsFlagged"],
                )

        id: int
        submitted_by: SubmittedBy
        submission_date: Optional[datetime]
        comment: RichText
        files: list[File]

        @staticmethod
        def from_json(json_obj: dict):
            return EntityDropBox.Submission(
                id=json_obj["Id"],
                submitted_by=EntityDropBox.Submission.SubmittedBy.from_json(
                    json_obj["SubmittedBy"]
                ),
                submission_date=_parse_utc_date_time(json_obj["SubmissionDate"]),
                comment=RichText.from_json(json_obj["Comment"]),
                files=[
                    EntityDropBox.Submission.File.from_json(file)
                    for file in json_obj["Files"]
                ],
            )

    entity: Entity
    status: str  # ENTITYDROPBOXSTATUS_T
    feedback: Optional[DropboxFeedbackOut]
    submissions: list[Submission]
    completion_date: Optional[datetime]

    @staticmethod
    def from_json(json_obj: dict):
        return EntityDropBox(
            entity=Entity.from_json(json_obj["Entity"]),
            status=json_obj["Status"],
            feedback=DropboxFeedbackOut.from_json(json_obj["Feedback"])
            if json_obj["Feedback"]
            else None,
            submissions=[
                EntityDropBox.Submission.from_json(submission)
                for submission in json_obj["Submissions"]
            ],
            completion_date=_parse_utc_date_time(json_obj["CompletionDate"]),
        )


@dataclass
class DropboxCategory:
    """See https://docs.valence.desire2learn.com/res/dropbox.html#Dropbox.DropboxCategory"""

    id: int
    name: str
    last_modified_user_id: Optional[int]
    last_modified_date: Optional[datetime]

    @staticmethod
    def from_json(json_obj: dict):
        return DropboxCategory(
            id=json_obj["Id"],
            name=json_obj["Name"],
            last_modified_user_id=json_obj["LastModifiedUserId"],
            last_modified_date=_parse_utc_date_time(json_obj["LastModifiedDate"]),
        )


@dataclass
class DropboxCategoryWithFolders:
    """See https://docs.valence.desire2learn.com/res/dropbox.html#Dropbox.DropboxCategoryWithFolders"""

    id: int
    name: str
    folders: list[DropboxFolder]
    last_modified_user_id: Optional[int]
    last_modified_date: Optional[datetime]

    @staticmethod
    def from_json(json_obj: dict):
        return DropboxCategoryWithFolders(
            id=json_obj["Id"],
            name=json_obj["Name"],
            folders=[DropboxFolder.from_json(folder) for folder in json_obj["Folders"]],
            last_modified_user_id=json_obj["LastModifiedUserId"],
            last_modified_date=_parse_utc_date_time(json_obj["LastModifiedDate"]),
        )


# https://docs.valence.desire2learn.com/res/groups.html#term-GRPENROLL_T
GROUP_ENROLL_NUMBER_OF_GROUPS_NO_ENROLLMENT = "NumberOfGroupsNoEnrollment"
GROUP_ENROLL_PEOPLE_PER_GROUP_AUTO_ENROLLMENT = "PeoplePerGroupAutoEnrollment"
GROUP_ENROLL_NUMBER_OF_GROUPS_AUTO_ENROLLMENT = "NumberOfGroupsAutoEnrollment"
GROUP_ENROLL_PEOPLE_PER_GROUP_SELF_ENROLLMENT = "PeoplePerGroupSelfEnrollment"
GROUP_ENROLL_SELF_ENROLLMENT_NUMBER_OF_GROUPS = "SelfEnrollmentNumberOfGroups"
GROUP_ENROLL_PEOPLE_PER_NUMBER_OF_GROUPS_SELF_ENROLLMENT = (
    "PeoplePerNumberOfGroupsSelfEnrollment"
)
GROUP_ENROLL_SINGLE_USER_MEMBER_SPECIFIC_GROUP = "SingleUserMemberSpecificGroup"


@dataclass
class GroupData:
    """See https://docs.valence.desire2learn.com/res/groups.html#Group.GroupData"""

    group_id: int
    name: str
    code: str
    description: RichText
    enrollments: list[int]

    @staticmethod
    def from_json(json_obj: dict):
        return GroupData(
            group_id=json_obj["GroupId"],
            name=json_obj["Name"],
            code=json_obj["Code"],
            description=RichText.from_json(json_obj["Description"]),
            enrollments=json_obj["Enrollments"],
        )


@dataclass
class GroupCategoryData:
    """See https://docs.valence.desire2learn.com/res/groups.html#Group.GroupCategoryData"""

    group_category_id: int
    name: str
    description: RichText
    enrollment_style: str  # GRPENROLL_T
    enrollment_quantity: Optional[int]
    max_users_per_group: Optional[int]
    auto_enroll: bool
    randomize_enrollments: bool
    groups: list[int]
    allocate_after_expiry: bool
    self_enrollment_expiry_date: Optional[datetime]
    restricted_by_org_unit_id: Optional[int]
    descriptions_visible_to_enrolees: bool

    @staticmethod
    def from_json(json_obj: dict):
        return GroupCategoryData(
            group_category_id=json_obj["GroupCategoryId"],
            name=json_obj["Name"],
            description=RichText.from_json(json_obj["Description"]),
            enrollment_style=json_obj["EnrollmentStyle"],
            enrollment_quantity=json_obj["EnrollmentQuantity"],
            max_users_per_group=json_obj["MaxUsersPerGroup"],
            auto_enroll=json_obj["AutoEnroll"],
            randomize_enrollments=json_obj["RandomizeEnrollments"],
            groups=json_obj["Groups"],
            allocate_after_expiry=json_obj["AllocateAfterExpiry"],
            self_enrollment_expiry_date=_parse_utc_date_time(
                json_obj["SelfEnrollmentExpiryDate"]
            ),
            restricted_by_org_unit_id=json_obj["RestrictedByOrgUnitId"],
            descriptions_visible_to_enrolees=json_obj["DescriptionsVisibleToEnrolees"],
        )


# https://docs.valence.desire2learn.com/res/grade.html#term-GRADEOBJ_T
GRADE_OBJECT_NUMERIC = 1
GRADE_OBJECT_PASS_FAIL = 2
GRADE_OBJECT_SELECT_BOX = 3
GRADE_OBJECT_TEXT = 4
GRADE_OBJECT_CALCULATED = 5
GRADE_OBJECT_FORMULA = 6
GRADE_OBJECT_FINAL_CALCULATED = 7
GRADE_OBJECT_FINAL_ADJUSTED = 8
GRADE_OBJECT_CATEGORY = 9

# https://docs.valence.desire2learn.com/res/grade.html#term-GRADINGSYSTEM_T
GRADING_SYSTEM_POINTS = "Points"
GRADING_SYSTEM_WEIGHTED = "Weighted"
GRADING_SYSTEM_FORMULA = "Formula"


@dataclass
class GradeScheme:
    """See https://docs.valence.desire2learn.com/res/grade.html#Grade.GradeScheme"""

    @dataclass
    class GradeSchemeRange:
        percent_start: float
        symbol: str
        assigned_value: Optional[float]
        colour: str

        @staticmethod
        def from_json(json_obj: dict):
            return GradeScheme.GradeSchemeRange(
                percent_start=json_obj["PercentStart"],
                symbol=json_obj["Symbol"],
                assigned_value=json_obj["AssignedValue"],
                colour=json_obj["Colour"],
            )

    id: int
    name: str
    short_name: str
    ranges: list[GradeSchemeRange]

    @staticmethod
    def from_json(json_obj: dict):
        return GradeScheme(
            id=json_obj["Id"],
            name=json_obj["Name"],
            short_name=json_obj["ShortName"],
            ranges=[
                GradeScheme.GradeSchemeRange.from_json(range_)
                for range_ in json_obj["Ranges"]
            ],
        )


@dataclass
class AssociatedTool:
    """See https://docs.valence.desire2learn.com/res/grade.html#Grade.AssociatedTool"""

    tool_id: int
    tool_item_id: int

    @staticmethod
    def from_json(json_obj: dict):
        return AssociatedTool(
            tool_id=json_obj["ToolId"], tool_item_id=json_obj["ToolItemId"]
        )


@dataclass
class GradeObject:
    """See https://docs.valence.desire2learn.com/res/grade.html#Grade.GradeObject"""

    # Numeric/PassFail/SelectBox/Text
    id: int
    name: str
    short_name: str
    grade_type: str
    category_id: Optional[int]
    description: RichText
    weight: float
    associated_tool: Optional[AssociatedTool]
    is_hidden: bool

    # Numeric/PassFail/SelectBox only
    max_points: Optional[float]
    is_bonus: Optional[bool]
    exclude_from_final_grade_calculation: Optional[bool]
    grade_scheme_id: Optional[int]
    grade_scheme_url: Optional[str]

    # Numeric only
    can_exceed_max_points: Optional[bool]

    @staticmethod
    def from_json(json_obj: dict):
        return GradeObject(
            id=json_obj["Id"],
            name=json_obj["Name"],
            short_name=json_obj["ShortName"],
            grade_type=json_obj["GradeType"],
            category_id=json_obj["CategoryId"],
            description=RichText.from_json(json_obj["Description"]),
            weight=json_obj["Weight"],
            associated_tool=AssociatedTool.from_json(json_obj["AssociatedTool"])
            if json_obj["AssociatedTool"]
            else None,
            is_hidden=json_obj["IsHidden"],
            max_points=json_obj.get("MaxPoints", None),
            is_bonus=json_obj.get("IsBonus", None),
            exclude_from_final_grade_calculation=json_obj.get(
                "ExcludeFromFinalGradeCalculation", None
            ),
            grade_scheme_id=json_obj.get("GradeSchemeId", None),
            grade_scheme_url=json_obj.get("GradeSchemeUrl", None),
            can_exceed_max_points=json_obj.get("CanExceedMaxPoints", None),
        )


WEIGHT_DISTRIBUTION_MANUAL = 0  # Manually assign weight to items in the category
WEIGHT_DISTRIBUTION_EVEN = 1  # Distribute weight evenly across all items
WEIGHT_DISTRIBUTION_POINTS = (
    2  # Distribute weights by points across all items in the category
)


@dataclass
class GradeObjectCategory:
    """See https://docs.valence.desire2learn.com/res/grade.html#Grade.GradeObjectCategory"""

    id: int
    grades: list[GradeObject]
    name: str
    short_name: str
    can_exceed_max: bool
    exclude_from_final_grade: bool
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    weight: Optional[float]
    max_points: Optional[float]
    auto_points: Optional[bool]
    weight_distribution_type: Optional[int]
    number_of_highest_to_drop: Optional[int]
    number_of_lowest_to_drop: Optional[int]

    @staticmethod
    def from_json(json_obj: dict):
        return GradeObjectCategory(
            id=json_obj["Id"],
            grades=[GradeObject.from_json(grade) for grade in json_obj["Grades"]],
            name=json_obj["Name"],
            short_name=json_obj["ShortName"],
            can_exceed_max=json_obj["CanExceedMax"],
            exclude_from_final_grade=json_obj["ExcludeFromFinalGrade"],
            start_date=_parse_utc_date_time(json_obj["StartDate"]),
            end_date=_parse_utc_date_time(json_obj["EndDate"]),
            weight=json_obj["Weight"],
            max_points=json_obj["MaxPoints"],
            auto_points=json_obj["AutoPoints"],
            weight_distribution_type=json_obj["WeightDistributionType"],
            number_of_highest_to_drop=json_obj["NumberOfHighestToDrop"],
            number_of_lowest_to_drop=json_obj["NumberOfLowestToDrop"],
        )


@dataclass
class GradeValue:
    """See https://docs.valence.desire2learn.com/res/grade.html#Grade.GradeValue"""

    # All grades
    displayed_grade: str
    grade_object_identifier: int
    grade_object_name: str
    grade_object_type: int  # GRADEOBJ_T
    grade_object_type_name: Optional[str]
    comments: RichText
    private_comments: RichText
    last_modified: Optional[datetime]
    last_modified_by: Optional[int]
    released_date: Optional[datetime]

    # Only for computable grades
    points_numerator: Optional[float]
    points_denominator: Optional[float]
    weighted_denominator: Optional[float]
    weighted_numerator: Optional[float]

    @staticmethod
    def from_json(json_obj: dict):
        return GradeValue(
            displayed_grade=json_obj["DisplayedGrade"],
            grade_object_identifier=json_obj["GradeObjectIdentifier"],
            grade_object_name=json_obj["GradeObjectName"],
            grade_object_type=json_obj["GradeObjectType"],
            grade_object_type_name=json_obj["GradeObjectTypeName"],
            comments=RichText.from_json(json_obj["Comments"]),
            private_comments=RichText.from_json(json_obj["PrivateComments"]),
            last_modified=_parse_utc_date_time(json_obj["LastModified"]),
            last_modified_by=json_obj["LastModifiedBy"],
            released_date=_parse_utc_date_time(json_obj["ReleasedDate"]),
            points_numerator=json_obj.get("PointsNumerator", None),
            points_denominator=json_obj.get("PointsDenominator", None),
            weighted_denominator=json_obj.get("WeightedDenominator", None),
            weighted_numerator=json_obj.get("WeightedNumerator", None),
        )


@dataclass
class UserGradeValue:
    """See https://docs.valence.desire2learn.com/res/grade.html#Grade.UserGradeValue"""

    user: User
    grade_value: Optional[GradeValue]

    @staticmethod
    def from_json(json_obj: dict):
        return UserGradeValue(
            user=User.from_json(json_obj["User"]),
            grade_value=GradeValue.from_json(json_obj["GradeValue"])
            if json_obj["GradeValue"]
            else None,
        )


@dataclass
class GradeStatisticsInfo:
    """See https://docs.valence.desire2learn.com/res/grade.html#Grade.GradeStatisticsInfo"""

    org_unit_id: int
    grade_object_id: int
    minimum: Optional[float]
    maximum: Optional[float]
    average: Optional[float]
    mode: list[float]
    median: Optional[float]
    standard_deviation: Optional[float]

    @staticmethod
    def from_json(json_obj: dict):
        return GradeStatisticsInfo(
            org_unit_id=json_obj["OrgUnitId"],
            grade_object_id=json_obj["GradeObjectId"],
            minimum=json_obj["Minimum"],
            maximum=json_obj["Maximum"],
            average=json_obj["Average"],
            mode=json_obj["Mode"],
            median=json_obj["Median"],
            standard_deviation=json_obj["StandardDeviation"],
        )
