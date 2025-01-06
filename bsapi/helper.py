import bsapi.types


class APIHelper:
    """Helper class to perform common API operations."""

    def __init__(self, api: bsapi.BSAPI):
        """Construct a new API helper instance.

        :param api: The `BSAPI` instance to use when making API calls.
        """
        self.api = api

    def find_courses_by_code(self, course_code: str) -> list[bsapi.types.MyOrgUnitInfo]:
        """Find all courses with the provided course code.

        :param course_code: The course code to find.
        :return: List of all matching courses.
        """
        return [
            course
            for course in self.api.get_course_enrollments()
            if course.org_unit.code == course_code
        ]

    def find_course_by_code(self, course_code: str) -> bsapi.types.MyOrgUnitInfo:
        """Find course with the provided course code.

        :param course_code: The course code to find.
        :return: The matching course.
        :raises ValueError: If no, or more than one, course is found.
        """
        courses = self.find_courses_by_code(course_code)
        if not courses:
            raise ValueError(f'No course with code "{course_code}" found')
        if len(courses) > 1:
            raise ValueError(f'Found {len(courses)} courses with code "{course_code}"')

        return courses[0]

    def find_courses_by_name(self, course_name: str) -> list[bsapi.types.MyOrgUnitInfo]:
        """Find all courses with the provided course name.

        :param course_name: The course name to find.
        :return: List of all matching courses.
        """
        return [
            course
            for course in self.api.get_course_enrollments()
            if course.org_unit.name == course_name
        ]

    def find_course_by_name(self, course_name: str) -> bsapi.types.MyOrgUnitInfo:
        """Find course with the provided course code.

        :param course_name: The course name to find.
        :return: The matching course.
        :raises ValueError: If no, or more than one, course is found.
        """
        courses = self.find_courses_by_name(course_name)
        if not courses:
            raise ValueError(f'No course with name "{course_name}" found')
        if len(courses) > 1:
            raise ValueError(f'Found {len(courses)} courses with name "{course_name}"')

        return courses[0]

    def find_group_categories(
        self, org_unit_id: int, category_name: str
    ) -> list[bsapi.types.GroupCategoryData]:
        """Find all groups categories with the provided category name.

        :param org_unit_id: The orgUnitId of the course.
        :param category_name: The category name to find.
        :return: List of all matching group categories.
        """
        return [
            category
            for category in self.api.get_group_categories(org_unit_id)
            if category.name == category_name
        ]

    def find_group_category(
        self, org_unit_id: int, category_name: str
    ) -> bsapi.types.GroupCategoryData:
        """Find group category with the provided category name.

        :param org_unit_id: The orgUnitId of the course.
        :param category_name: The category name to find.
        :return: The matching group category.
        :raises ValueError: If no, or more than one, group category is found.
        """
        categories = self.find_group_categories(org_unit_id, category_name)
        if not categories:
            raise ValueError(f'No group category with name "{category_name}" found')
        if len(categories) > 1:
            raise ValueError(
                f'Found {len(categories)} group categories with name "{category_name}"'
            )

        return categories[0]

    def find_groups(
        self, org_unit_id: int, group_category_id: int, group_name: str
    ) -> list[bsapi.types.GroupData]:
        """Find all groups with the provided group name.

        :param org_unit_id: The orgUnitId of the course.
        :param group_category_id: The groupCategoryId of the group category.
        :param group_name: The group name to find.
        :return: List of all matching groups.
        """
        return [
            group
            for group in self.api.get_groups(org_unit_id, group_category_id)
            if group.name == group_name
        ]

    def find_group(
        self, org_unit_id: int, group_category_id: int, group_name: str
    ) -> bsapi.types.GroupData:
        """Find group with the provided group name.

        :param org_unit_id: The orgUnitId of the course.
        :param group_category_id: The groupCategoryId of the group category.
        :param group_name: The group name to find.
        :return: The matching group.
        :raises ValueError: If no, or more than one, group is found.
        """
        groups = self.find_groups(org_unit_id, group_category_id, group_name)
        if not groups:
            raise ValueError(f'No group with name "{group_name}" found')
        if len(groups) > 1:
            raise ValueError(f'Found {len(groups)} groups with name "{group_name}"')

        return groups[0]

    def find_assignments(
        self, org_unit_id: int, assignment_name: str
    ) -> list[bsapi.types.DropboxFolder]:
        """Find all assignment dropbox folders with the provided assignment name.

        :param org_unit_id: The orgUnitId of the course.
        :param assignment_name: The assignment name to find.
        :return: List of all matching assignment dropbox folders.
        """
        return [
            assignment
            for assignment in self.api.get_dropbox_folders(org_unit_id)
            if assignment.name == assignment_name
        ]

    def find_assignment(
        self, org_unit_id: int, assignment_name: str
    ) -> bsapi.types.DropboxFolder:
        """Find assignment dropbox folder with the provided assignment name.

        :param org_unit_id: The orgUnitId of the course.
        :param assignment_name: The assignment name to find.
        :return: The matching assignment dropbox folder.
        :raises ValueError: If no, or more than one, assignment dropbox is found.
        """
        assignments = self.find_assignments(org_unit_id, assignment_name)
        if not assignments:
            raise ValueError(f'No assignment with name "{assignment_name}" found')
        if len(assignments) > 1:
            raise ValueError(
                f'Found {len(assignments)} assignments with name "{assignment_name}"'
            )

        return assignments[0]

    def enroll_users_in_group(
        self,
        org_unit_id: int,
        group_category_id: int,
        group_id: int,
        user_ids: list[int],
    ):
        """Enroll all given users in the specified group.

        :param org_unit_id: The orgUnitId of the course.
        :param group_category_id: The groupCategoryId of the group category.
        :param group_id: The groupId of the group.
        :param user_ids: The list of users to enroll.
        """
        for user_id in user_ids:
            self.api.enroll_user_in_group(
                org_unit_id, group_category_id, group_id, user_id
            )

    def remove_users_from_group(
        self,
        org_unit_id: int,
        group_category_id: int,
        group_id: int,
        user_ids: list[int],
    ):
        """Remove all given users from the specified group.

        :param org_unit_id: The orgUnitId of the course.
        :param group_category_id: The groupCategoryId of the group category.
        :param group_id: THe groupId of the group.
        :param user_ids: The list of users to remove.
        """
        for user_id in user_ids:
            self.api.remove_user_from_group(
                org_unit_id, group_category_id, group_id, user_id
            )

    def set_group_members(
        self,
        org_unit_id: int,
        group_category_id: int,
        group_id: int,
        user_ids: list[int],
    ) -> list[int]:
        """Set the group members of the specified group to be exactly that of the given users. This is a multistep
        process. First a list of current members is obtained. Then all users not already enrolled are enrolled in the
        group. Finally, all existing members not part of the given users are removed.

        :param org_unit_id: The orgUnitId of the course.
        :param group_category_id: THe groupCategoryId of the group category.
        :param group_id: The groupId of the group.
        :param user_ids: The list of users to set.
        :return: List of userIds of all existing group members of the given group, before being updated.
        """
        group_data = self.api.get_group(org_unit_id, group_category_id, group_id)

        to_enroll = [
            user_id for user_id in user_ids if user_id not in group_data.enrollments
        ]
        to_remove = [
            user_id for user_id in group_data.enrollments if user_id not in user_ids
        ]

        self.enroll_users_in_group(org_unit_id, group_category_id, group_id, to_enroll)
        self.remove_users_from_group(
            org_unit_id, group_category_id, group_id, to_remove
        )

        return group_data.enrollments

    def clear_group_members(
        self, org_unit_id: int, group_category_id: int, group_id: int
    ) -> list[int]:
        """Clear all group members from the specified group. First a list of all members is obtained, which are then
        subsequently removed.

        :param org_unit_id: The orgUnitId of the course.
        :param group_category_id: The groupCategoryId of the group category.
        :param group_id: The groupId of the group.
        :return: List of userIds of all group members enrolled prior to their removal.
        """
        group_data = self.api.get_group(org_unit_id, group_category_id, group_id)

        self.remove_users_from_group(
            org_unit_id, group_category_id, group_id, group_data.enrollments
        )

        return group_data.enrollments
