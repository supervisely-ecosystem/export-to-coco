import pytest

from settings import Settings


def env(**state):
    return {f"modal.state.{k}": v for k, v in state.items()}


def test_defaults_export_whole_project_with_images():
    s = Settings.from_env({})
    assert s == Settings(export_images=True, only_annotated=False, dataset_ids=None, with_captions=False)


def test_values_as_the_platform_sends_them():
    s = Settings.from_env(
        env(
            selectedOutput="annotations",
            selectedFilter="annotated",
            allDatasets="False",
            datasets="[71754, 5]",
            captions="True",
        )
    )
    assert s == Settings(export_images=False, only_annotated=True, dataset_ids=(71754, 5), with_captions=True)


def test_selected_datasets_ignored_when_all_datasets():
    assert Settings.from_env(env(allDatasets="true", datasets="[1]")).dataset_ids is None


@pytest.mark.parametrize(
    "state",
    [
        {"selectedOutput": "zip"},
        {"selectedFilter": "labeled"},
        {"allDatasets": "maybe"},
        {"allDatasets": "false", "datasets": "[]"},
    ],
)
def test_invalid_input_fails_before_any_work(state):
    with pytest.raises(ValueError):
        Settings.from_env(env(**state))
