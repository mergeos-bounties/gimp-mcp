from gimp_mcp.backend import get_backend
from gimp_mcp.backend.mock import MockBackend
from gimp_mcp.config import set_mode


def test_seed_and_list():
    b = MockBackend()
    s = b.seed_demo()
    assert s["ok"] is True
    assert b.list_images()
    d = b.doctor()
    assert d["ok"] is True
    assert d["mode"] == "mock"


def test_resize_blur_export(tmp_path):
    b = MockBackend()
    s = b.seed_demo()
    iid = s["image"]["id"]
    r = b.resize(iid, 100, 80)
    assert r["ok"] is True
    assert r["image"]["width"] == 100
    assert b.blur(iid, 1.0)["ok"] is True
    out = tmp_path / "x.png"
    exp = b.export(iid, str(out))
    assert exp["ok"] is True
    assert out.is_file()


def test_batch_resize(tmp_path):
    b = MockBackend()
    s = b.seed_demo()
    src = tmp_path / "in"
    dst = tmp_path / "out"
    src.mkdir()
    # copy seeded image into input
    from shutil import copy2

    copy2(s["image"]["path"], src / "a.png")
    res = b.batch_resize(str(src), str(dst), 64, 64)
    assert res["ok"] is True
    assert res["count"] >= 1


def test_get_backend_mock():
    set_mode("mock")
    assert get_backend().name == "mock"
