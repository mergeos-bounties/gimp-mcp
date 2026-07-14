from gimp_mcp import server as srv


def test_tool_functions_exist():
    for name in (
        "gimp_doctor",
        "gimp_seed_demo",
        "gimp_resize",
        "gimp_batch_resize",
        "gimp_export",
    ):
        assert hasattr(srv, name)


def test_seed_via_tool_json():
    from gimp_mcp.config import set_mode

    set_mode("mock")
    raw = srv.gimp_seed_demo()
    assert "img_" in raw or "image" in raw
