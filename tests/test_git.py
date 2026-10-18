#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.utils import _git


class FakeGraphqlClient:

    queries = []

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def exec(self, query, headers, proxy):
        self.queries.append(query)
        return {
            "data": {
                "repositoryOwner": {
                    "repositories": {
                        "nodes": [{
                            "isFork": False,
                            "owner": {"login": "example-org"},
                            "name": "custom-default-branch",
                            "url": "https://github.com/example-org/custom-default-branch",
                            "description": "Uses develop instead of main",
                            "visibility": "PUBLIC",
                            "pushedAt": "2026-07-02T08:00:00Z",
                            "repositoryTopics": {"nodes": []},
                            "defaultBranchRef": {
                                "target": {"history": {"totalCount": 12}}
                            },
                        }],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
        }


class QueryReposTest(unittest.TestCase):

    @patch.object(_git, "_GraphqlClient", FakeGraphqlClient)
    def test_includes_org_repo_with_custom_default_branch(self):
        FakeGraphqlClient.queries = []

        repos = _git.query_repos("token")

        self.assertEqual(1, len(repos))
        self.assertEqual("example-org", repos[0].owner)
        self.assertEqual("PUBLIC", repos[0].visibility)
        self.assertEqual(12, repos[0].commit_cnt)
        query = FakeGraphqlClient.queries[0]
        self.assertIn("defaultBranchRef", query)
        self.assertIn('repositoryOwner(login: "CasualRO")', query)
        self.assertIn("repositories(first:", query)
        self.assertNotIn("viewer", query)
        self.assertIn("visibility", query)
        self.assertNotIn('object(expression:', query)

    def test_missing_token(self):
        with self.assertRaisesRegex(ValueError, '缺少 GitHub Token'):
            _git.query_repos('')

    @patch.object(_git, '_GraphqlClient')
    def test_graphql_error(self, client):
        client.return_value.exec.return_value = {'errors': [{'message': 'Access denied'}]}
        with self.assertRaisesRegex(RuntimeError, 'Access denied'):
            _git.query_repos('token')

    @patch.object(_git, '_GraphqlClient')
    def test_owner_not_accessible(self, client):
        client.return_value.exec.return_value = {'data': {'repositoryOwner': None}}
        with self.assertRaisesRegex(RuntimeError, 'CasualRO'):
            _git.query_repos('token')

    @patch.object(_git, '_GraphqlClient')
    def test_pagination(self, client):
        first = FakeGraphqlClient('endpoint').exec('', {}, '')
        second = FakeGraphqlClient('endpoint').exec('', {}, '')
        first['data']['repositoryOwner']['repositories']['pageInfo'] = {
            'hasNextPage': True, 'endCursor': 'next-page'
        }
        client.return_value.exec.side_effect = [first, second]

        self.assertEqual(2, len(_git.query_repos('token')))
        self.assertIn('after: "next-page"', client.return_value.exec.call_args.kwargs['query'])


if __name__ == "__main__":
    unittest.main()
