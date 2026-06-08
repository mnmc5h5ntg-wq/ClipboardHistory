import contextlib
import io
import os
import unittest
from unittest import mock

from scripts import create_issues


class CreateIssuesTests(unittest.TestCase):
    def test_default_mode_is_dry_run(self):
        with mock.patch.object(create_issues, "post") as post, contextlib.redirect_stdout(io.StringIO()):
            result = create_issues.main([])

        self.assertEqual(result, 0)
        post.assert_not_called()

    def test_confirm_mode_requires_environment_token(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            create_issues,
            "post",
        ) as post, contextlib.redirect_stderr(io.StringIO()):
            result = create_issues.main(["--confirm-release-publish"])

        self.assertEqual(result, 1)
        post.assert_not_called()

    def test_confirm_mode_uses_token_without_shelling_out(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "secret"}, clear=True), mock.patch.object(
            create_issues,
            "post",
            return_value=1,
        ) as post, contextlib.redirect_stdout(io.StringIO()):
            result = create_issues.main(["--confirm-release-publish", "--repo", "owner/repo"])

        self.assertEqual(result, 0)
        self.assertEqual(post.call_count, len(create_issues.all_issues()))
        first_call = post.call_args_list[0]
        self.assertEqual(first_call.kwargs["token"], "secret")
        self.assertEqual(first_call.kwargs["repo"], "owner/repo")


if __name__ == "__main__":
    unittest.main()
