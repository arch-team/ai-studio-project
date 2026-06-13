"""SpaceBackend 值对象测试。"""

from src.modules.spaces.domain.value_objects import SpaceBackend


class TestSpaceBackend:
    def test_studio_value(self) -> None:
        assert SpaceBackend.STUDIO.value == "studio"

    def test_hyperpod_value(self) -> None:
        assert SpaceBackend.HYPERPOD.value == "hyperpod"

    def test_from_value(self) -> None:
        assert SpaceBackend("hyperpod") is SpaceBackend.HYPERPOD
