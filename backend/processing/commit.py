from datetime import datetime
from typing import Any, Dict, List

from external.github_api.graphql.template import (
    GraphQLErrorAuth,
    GraphQLErrorTimeout,
    GraphQLErrorMissingNode,
)

from external.github_api.rest.repo import get_repo_commits
from external.github_api.graphql.commit import get_commits
from constants import NODE_CHUNK_SIZE, CUTOFF, BLACKLIST


def get_all_commit_info(
    user_id: str,
    name_with_owner: str,
    start_date: datetime = datetime.now(),
    end_date: datetime = datetime.now(),
) -> List[datetime]:
    """Gets all user's commit times for a given repository"""
    owner, repo = name_with_owner.split("/")
    data: List[Any] = []
    index = 0
    while index in range(10) and len(data) == 100 * index:
        data.extend(
            get_repo_commits(
                owner=owner,
                repo=repo,
                user=user_id,
                since=start_date,
                until=end_date,
                page=index + 1,
            )
        )
        index += 1

    data = list(
        map(
            lambda x: [
                datetime.strptime(
                    x["commit"]["committer"]["date"], "%Y-%m-%dT%H:%M:%SZ"
                ),
                x["node_id"],
            ],
            data,
        )
    )

    # sort ascending
    data = sorted(data, key=lambda x: x[0])
    return data


def _get_commits_languages(
    node_ids: List[str], per_page: int = NODE_CHUNK_SIZE
) -> List[Dict[str, Any]]:
    all_data: List[Dict[str, Any]] = []
    for i in range(0, len(node_ids), per_page):
        # TODO: alert user/display if some nodes omitted
        # TODO: figure out why Auth error code appears
        cutoff = min(len(node_ids), i + per_page)
        try:
            raw_data = get_commits(node_ids[i:cutoff])
            data: List[Dict[str, Any]] = raw_data["data"]["nodes"]  # type: ignore
            all_data.extend(data)
        except GraphQLErrorMissingNode as e:
            curr = node_ids[i:cutoff]
            curr.pop(e.node)
            all_data.extend(_get_commits_languages(curr))
        except GraphQLErrorTimeout:
            length = cutoff - i
            if length == per_page:
                midpoint = i + int(per_page / 2)
                all_data.extend(_get_commits_languages(node_ids[i:midpoint]))
                all_data.extend(_get_commits_languages(node_ids[midpoint:cutoff]))
            else:
                print("Commit Timeout Exception:", length, " nodes lost")
                all_data.extend([{} for _ in range(length)])
        except GraphQLErrorAuth:
            length = cutoff - i
            print("Commit Auth Exception:", length, " nodes lost")
            all_data.extend([{} for _ in range(length)])

    return all_data


def get_commits_languages(node_ids: List[str], cutoff: int = CUTOFF):
    all_data = _get_commits_languages(node_ids, per_page=NODE_CHUNK_SIZE)

    out: List[Dict[str, Dict[str, int]]] = []
    for commit in all_data:
        out.append({})
        if (
            "additions" in commit
            and "deletions" in commit
            and "changedFiles" in commit
            and commit["additions"] + commit["deletions"] < cutoff
        ):
            languages = [
                x
                for x in commit["repository"]["languages"]["edges"]
                if x["node"]["name"] not in BLACKLIST
            ]
            num_langs = min(len(languages), commit["changedFiles"])
            total_repo_size = sum(
                [language["size"] for language in languages[:num_langs]]
            )
            for language in languages[:num_langs]:
                lang_name = language["node"]["name"]
                additions = round(
                    commit["additions"] * language["size"] / total_repo_size
                )
                deletions = round(
                    commit["deletions"] * language["size"] / total_repo_size
                )
                if additions > 0 or deletions > 0:
                    out[-1][lang_name] = {
                        "additions": additions,
                        "deletions": deletions,
                    }

    return out
