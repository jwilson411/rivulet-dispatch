import rivulet_dispatch
from rivulet_dispatch import dispatch_sync


def test_dispatch_sync_is_publicly_importable() -> None:
    assert callable(dispatch_sync)


def test_dispatch_sync_is_in_all() -> None:
    assert "dispatch_sync" in rivulet_dispatch.__all__
