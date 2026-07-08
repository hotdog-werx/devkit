import subprocess

import pytest
from repolish.testing import ProviderTestBed

from devkit.workspace.repolish.models import WorkspaceContext
from devkit.workspace.repolish.provider import WorkspaceProvider

CI_CHECKS = '.github/workflows/ci-checks.yaml'
DEPLOY_DOCS = '.github/workflows/deploy-docs.yaml'

# NOTE: create_file_mappings() references these without the .jinja suffix
# (the real repolish CLI resolves that automatically), but
# ProviderTestBed.render_all()'s dest-mapped rendering does NOT do that
# fallback lookup — it only auto-discovers the literal on-disk name. So
# these tests call bed.render() directly with the literal .jinja-suffixed
# path instead of relying on render_all()'s dest-keyed dict for these two
# templates specifically.
CI_CHECKS_TEMPLATE = '.github/workflows/ci-checks.yaml.jinja'


@pytest.fixture
def bed_no_docs_no_python() -> ProviderTestBed:
    return ProviderTestBed(
        WorkspaceProvider,
        WorkspaceContext(owner='hotdog-werx', repo='example', year='2026'),
    )


@pytest.fixture
def bed_docs_and_python() -> ProviderTestBed:
    return ProviderTestBed(
        WorkspaceProvider,
        WorkspaceContext(
            owner='hotdog-werx',
            repo='example',
            year='2026',
            enable_docs=True,
            has_python=True,
            devkit_ref='topic/repolish',
        ),
    )


def test_create_context_detects_owner_repo_from_git_remote(mocker):
    mocker.patch(
        'devkit.workspace.repolish.provider.subprocess.check_output',
        return_value='git@github.com:hotdog-werx/devkit.git\n',
    )
    ctx = WorkspaceProvider().create_context()
    assert ctx.owner == 'hotdog-werx'
    assert ctx.repo == 'devkit'


def test_create_context_falls_back_when_no_git_remote(mocker):
    mocker.patch(
        'devkit.workspace.repolish.provider.subprocess.check_output',
        side_effect=subprocess.CalledProcessError(1, 'git'),
    )
    ctx = WorkspaceProvider().create_context()
    assert ctx.owner == ''
    assert ctx.repo == ''


def test_file_mappings_omit_deploy_docs_when_disabled(bed_no_docs_no_python):
    mappings = bed_no_docs_no_python.file_mappings()
    assert mappings[DEPLOY_DOCS] is None


def test_file_mappings_include_deploy_docs_when_enabled(bed_docs_and_python):
    mappings = bed_docs_and_python.file_mappings()
    assert mappings[DEPLOY_DOCS] == DEPLOY_DOCS


def test_render_all_succeeds_without_docs_or_python(bed_no_docs_no_python):
    """Every mapped/auto-discovered template must render with no Jinja errors."""
    rendered = bed_no_docs_no_python.render_all()
    assert '.editorconfig' in rendered
    assert 'dprint.json' in rendered
    assert DEPLOY_DOCS not in rendered  # mapped to None, not rendered


def test_ci_checks_omits_python_checks_job_when_has_python_false(bed_no_docs_no_python):
    content = bed_no_docs_no_python.render(CI_CHECKS_TEMPLATE)
    assert 'python-checks:' not in content
    assert 'repo-checks:' in content


def test_ci_checks_includes_python_checks_job_when_has_python_true(bed_docs_and_python):
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert 'python-checks:' in content


def test_ci_checks_references_devkit_ref_in_reusable_workflow_uses(bed_docs_and_python):
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert '__workspace_repo-checks.yaml@topic/repolish' in content
    assert '__python_python-checks.yaml@topic/repolish' in content


def test_enable_docs_passed_through_to_repo_checks_input(bed_docs_and_python):
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert 'enable-docs: true' in content


def test_enable_docs_false_passed_through(bed_no_docs_no_python):
    content = bed_no_docs_no_python.render(CI_CHECKS_TEMPLATE)
    assert 'enable-docs: false' in content


def test_deploy_docs_references_devkit_ref(bed_docs_and_python):
    content = bed_docs_and_python.render('.github/workflows/deploy-docs.yaml.jinja')
    assert '__workspace_deploy-docs.yaml@topic/repolish' in content
