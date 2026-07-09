import subprocess

import pytest
from repolish.testing import ProviderTestBed

from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
from devkit.workspace.repolish.provider.root import WorkspaceRootHandler
from devkit.workspace.repolish.provider.standalone import WorkspaceStandaloneHandler

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
        WorkspaceProviderContext(owner='hotdog-werx', repo='example', year='2026'),
    )


@pytest.fixture
def bed_docs_and_python() -> ProviderTestBed:
    return ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(
            owner='hotdog-werx',
            repo='example',
            year='2026',
            enable_docs=True,
            has_python=True,
            workspace_ref='topic/repolish',
            python_ref='python-v2',
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
    assert DEPLOY_DOCS not in rendered  # mapped to None, not rendered


@pytest.mark.parametrize(
    'handler_cls',
    [WorkspaceRootHandler, WorkspaceStandaloneHandler],
)
def test_editorconfig_and_dprint_json_are_symlinked_not_rendered(handler_cls):
    """.editorconfig/dprint.json are static passthrough config — symlinked via
    create_default_symlinks(), not copied/rendered via create_file_mappings().

    Note: ProviderTestBed.symlinks() calls create_default_symlinks()
    directly on the base Provider instance, bypassing mode-handler dispatch
    (unlike create_file_mappings()/create_anchors(), which do dispatch via
    call_provider_method). The real repolish CLI *does* combine
    provider-level and handler-level symlinks (see
    repolish.linker.orchestrator._symlinks_from_module) — so this test
    instantiates the mode handler directly to verify what the real pipeline
    actually sees.
    """
    symlinks = handler_cls().create_default_symlinks()
    targets = {s.target for s in symlinks}
    sources = {s.source for s in symlinks}
    assert '.editorconfig' in targets
    assert 'dprint.json' in targets
    assert 'configs/.editorconfig' in sources
    assert 'configs/dprint.json' in sources


def test_ci_checks_omits_python_checks_job_when_has_python_false(bed_no_docs_no_python):
    content = bed_no_docs_no_python.render(CI_CHECKS_TEMPLATE)
    assert 'python-checks:' not in content
    assert 'repo-checks:' in content


def test_ci_checks_includes_python_checks_job_when_has_python_true(bed_docs_and_python):
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert 'python-checks:' in content


def test_ci_checks_references_independent_refs_per_namespace(bed_docs_and_python):
    """workspace_ref and python_ref are independently pinnable — ci-checks.yaml
    calls into both the __workspace_ and __python_ reusable-workflow
    namespaces, and each may need to move to a different devkit ref/tag
    on its own schedule (e.g. once each provider package gets its own
    release cycle).
    """
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert '__workspace_repo-checks.yaml@topic/repolish' in content
    assert '__python_python-checks.yaml@python-v2' in content


def test_enable_docs_passed_through_to_repo_checks_input(bed_docs_and_python):
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert 'enable-docs: true' in content


def test_enable_docs_false_passed_through(bed_no_docs_no_python):
    content = bed_no_docs_no_python.render(CI_CHECKS_TEMPLATE)
    assert 'enable-docs: false' in content


def test_deploy_docs_references_workspace_ref(bed_docs_and_python):
    content = bed_docs_and_python.render('.github/workflows/deploy-docs.yaml.jinja')
    assert '__workspace_deploy-docs.yaml@topic/repolish' in content
