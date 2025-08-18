from pathlib import Path
from src.helper_lib import (
    find_ws_root,
    find_git_root,
    get_github_base_url,
    get_current_git_hash,
    parse_remote_git_output,
    get_github_repo_info,
)

# Import types that depend on score_source_code_linker
from src.extensions.score_source_code_linker.needlinks import DefaultNeedLink, NeedLink
from src.extensions.score_source_code_linker.testlink import (
    DataOfTestCase,
    DataForTestLink,
)

def get_github_link(
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    passed_git_root = find_git_root()
    if passed_git_root is None:
        passed_git_root = Path()
    base_url = get_github_base_url()
    current_hash = get_current_git_hash(passed_git_root)
    return f"{base_url}/blob/{current_hash}/{link.file}#L{link.line}"
