import pytest
from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)
from devkit.workspace.repolish.provider import WorkspaceProvider
from devkit.workspace.repolish.provider._shared import _SharedWorkspaceBehavior
from repolish import ProviderEntry
from repolish.testing import ProviderTestBed

CI_CHECKS = '.github/workflows/ci-checks.yaml'
DEPLOY_DOCS = '.github/workflows/deploy-docs.yaml'

# NOTE: create_file_mappings() points at the `_repolish.`-prefixed
# conditional templates (staging-only). ProviderTestBed.render_all()'s
# dest-mapped rendering does not resolve those, so these tests call
# bed.render() directly with the literal .jinja-suffixed path instead of
# relying on render_all()'s dest-keyed dict for these two templates
# specifically.
CI_CHECKS_TEMPLATE = '.github/workflows/_repolish.ci-checks.yaml.jinja'
DEPLOY_DOCS_TEMPLATE = '.github/workflows/_repolish.deploy-docs.yaml.jinja'

# ProviderTestBed is Generic[CtxT, InpT]; the alias pins it to the
# workspace provider's context/inputs pair so fixtures and test
# parameters share one concrete annotation (resolved_context, render_all,
# etc. then resolve against WorkspaceProviderContext instead of an
# unbound generic).
WorkspaceBed = ProviderTestBed[
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
]


@pytest.fixture
def bed_no_docs_no_python() -> WorkspaceBed:
    """A workspace provider test bed with docs and Python support both disabled."""
    return ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(
            has_python=False,
        ),
    )


@pytest.fixture
def bed_docs_and_python() -> WorkspaceBed:
    """A workspace provider test bed with docs and Python support both enabled."""
    return ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(
            enable_docs=True,
            has_python=True,
            devkit_ref='devkit-pin',
        ),
    )


def test_finalize_context_detects_python_provider() -> None:
    """Python checks are enabled by provider composition rather than file heuristics."""
    context = WorkspaceProviderContext()
    bed = ProviderTestBed(WorkspaceProvider, context)

    resolved = bed.finalize(
        [],
        all_providers=[ProviderEntry(provider_id='python', alias='python')],
    )

    assert resolved.has_python is True


def test_finalize_context_preserves_explicit_python_override() -> None:
    """A consumer can explicitly disable Python checks despite loading the provider."""
    context = WorkspaceProviderContext(has_python=False)
    bed = ProviderTestBed(WorkspaceProvider, context)

    resolved = bed.finalize(
        [],
        all_providers=[ProviderEntry(provider_id='python', alias='python')],
    )

    assert resolved.has_python is False


def test_file_mappings_omit_deploy_docs_when_disabled(
    bed_no_docs_no_python: WorkspaceBed,
) -> None:
    """enable_docs=False maps deploy-docs.yaml to None (not rendered)."""
    mappings = bed_no_docs_no_python.file_mappings()
    assert mappings[DEPLOY_DOCS] is None


def test_file_mappings_include_deploy_docs_when_enabled(
    bed_docs_and_python: WorkspaceBed,
) -> None:
    """enable_docs=True maps deploy-docs.yaml to its conditional template."""
    mappings = bed_docs_and_python.file_mappings()
    assert mappings[DEPLOY_DOCS] == '.github/workflows/_repolish.deploy-docs.yaml'


def test_render_all_succeeds_without_docs_or_python(
    bed_no_docs_no_python: WorkspaceBed,
) -> None:
    """Every mapped/auto-discovered template must render with no Jinja errors."""
    rendered = bed_no_docs_no_python.render_all()
    assert DEPLOY_DOCS not in rendered  # mapped to None, not rendered


@pytest.mark.parametrize(
    'handler_cls',
    [_SharedWorkspaceBehavior],
)
def test_editorconfig_and_dprint_json_are_symlinked_not_rendered(
    handler_cls: type[_SharedWorkspaceBehavior],
) -> None:
    """.editorconfig/dprint.json are symlinked, not rendered.

    They're static passthrough config, symlinked via
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


def test_ci_checks_omits_python_checks_job_when_has_python_false(
    bed_no_docs_no_python: WorkspaceBed,
) -> None:
    """has_python=False renders ci-checks.yaml with no python-checks job."""
    content = bed_no_docs_no_python.render(CI_CHECKS_TEMPLATE)
    assert 'python-checks:' not in content
    assert 'repo-checks:' in content


def test_ci_checks_includes_python_checks_job_when_has_python_true(
    bed_docs_and_python: WorkspaceBed,
) -> None:
    """has_python=True renders ci-checks.yaml with a python-checks job."""
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert 'python-checks:' in content


def test_ci_checks_passes_operating_systems_and_codecov_to_python_checks() -> None:
    """python_operating_systems/python_codecov reach the python-checks job's inputs.

    Lets a consumer opt into a Windows/macOS matrix and Codecov upload
    without needing its own custom tests job duplicating check-coverage.
    """
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(
            has_python=True,
            python_operating_systems=['ubuntu-latest', 'windows-latest'],
            python_codecov=True,
        ),
    )
    content = bed.render(CI_CHECKS_TEMPLATE)
    assert 'operating-systems: \'["ubuntu-latest", "windows-latest"]\'' in content
    assert 'codecov: true' in content
    assert 'CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}' in content
    assert 'secrets: inherit' not in content


def test_ci_checks_references_single_devkit_ref(
    bed_docs_and_python: WorkspaceBed,
) -> None:
    """All reusable workflows use the same tested Devkit snapshot."""
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert '__workspace_repo-checks.yaml@devkit-pin' in content
    assert '__python_python-checks.yaml@devkit-pin' in content


def test_enable_docs_passed_through_to_repo_checks_input(
    bed_docs_and_python: WorkspaceBed,
) -> None:
    """enable_docs=True passes enable-docs: true to the repo-checks job input."""
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert 'enable-docs: true' in content


def test_enable_docs_false_passed_through(
    bed_no_docs_no_python: WorkspaceBed,
) -> None:
    """enable_docs=False passes enable-docs: false to the repo-checks job input."""
    content = bed_no_docs_no_python.render(CI_CHECKS_TEMPLATE)
    assert 'enable-docs: false' in content


def test_deploy_docs_references_devkit_ref(
    bed_docs_and_python: WorkspaceBed,
) -> None:
    """deploy-docs.yaml pins the reusable workflow to devkit_ref."""
    content = bed_docs_and_python.render(DEPLOY_DOCS_TEMPLATE)
    assert '__workspace_deploy-docs.yaml@devkit-pin' in content


def test_ci_checks_adds_mustard_upload_and_report_job() -> None:
    """python_mustard uploads per OS in python-checks and reports in the caller.

    The report job needs checks/pull-requests/id-token/attestations write
    access, so it must live in the calling workflow rather than the shared
    reusable workflow, where requesting those permissions would break every
    caller that does not grant them.
    """
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(
            has_python=True,
            python_operating_systems=['ubuntu-latest', 'windows-latest'],
            python_mustard=True,
        ),
    )
    content = bed.render(CI_CHECKS_TEMPLATE)
    assert 'mustard: true' in content
    assert 'codecov: false' in content
    assert '  coverage:\n    needs: [python-checks]' in content
    assert 'checks: write' in content
    assert 'attestations: write' in content
    assert "fail-ci: 'true'" in content
    assert 'uses: hotdog-werx/mustard@' in content


def test_ci_checks_omits_mustard_report_job_by_default(
    bed_docs_and_python: WorkspaceBed,
) -> None:
    """Without python_mustard there is no input, report job, or extra permissions.

    Omitting the input entirely (rather than passing false) keeps a rendered
    workflow valid against an older python-checks ref that predates it.
    """
    content = bed_docs_and_python.render(CI_CHECKS_TEMPLATE)
    assert 'mustard:' not in content
    assert 'coverage:' not in content
    assert 'checks: write' not in content


def test_local_workflows_call_reusable_workflows_from_the_same_commit() -> None:
    """devkit_local_workflows renders same-commit `./` references with no ref.

    devkit's own CI uses this so a PR exercises its own reusable-workflow
    changes instead of whatever devkit_ref (master or v0) points at.
    """
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(
            has_python=True,
            devkit_ref='devkit-pin',
            devkit_local_workflows=True,
        ),
    )
    ci = bed.render(CI_CHECKS_TEMPLATE)
    docs = bed.render(DEPLOY_DOCS_TEMPLATE)
    assert 'uses: ./.github/workflows/__workspace_repo-checks.yaml\n' in ci
    assert 'uses: ./.github/workflows/__python_python-checks.yaml\n' in ci
    assert 'uses: ./.github/workflows/__workspace_deploy-docs.yaml\n' in docs
    assert 'hotdog-werx/devkit/' not in ci + docs
    assert 'devkit-pin' not in ci + docs
