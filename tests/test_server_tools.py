from gimp_mcp import server as srv


def test_tool_functions_exist():
    for name in (
        "gimp_doctor",
        "gimp_seed_demo",
        "gimp_resize",
        "gimp_batch_resize",
        "gimp_export",
        "gimp_sharpen",
        "gimp_brightness",
        "gimp_contrast",
        "gimp_saturation",
        "gimp_thumbnail",
        "gimp_pipeline",
        "gimp_close",
        "gimp_crop_bottom",
        "gimp_remove_background",
        "gimp_trim",
        "gimp_erase_rect",
        "gimp_pad",
        "gimp_border",
    ):
        assert hasattr(srv, name)


def test_seed_via_tool_json():
    from gimp_mcp.config import set_mode

    set_mode("mock")
    raw = srv.gimp_seed_demo()
    assert "img_" in raw or "image" in raw


def test_list_layers_tool_exists():
    assert hasattr(srv, "gimp_list_layers")


def test_new_layer_tool_exists():
    assert hasattr(srv, "gimp_new_layer")


def test_flatten_tool_exists():
    assert hasattr(srv, "gimp_flatten")


def test_list_layers():
    from gimp_mcp.config import set_mode
    from gimp_mcp.backend import get_backend

    set_mode("mock")
    b = get_backend()

    # Create an image first
    created = b.new_image(100, 100, "#ff0000")
    assert created["ok"]
    iid = created["image"]["id"]

    # List layers
    result = b.list_layers(iid)
    assert result["ok"]
    assert len(result["layers"]) >= 1
    assert result["layers"][0]["name"] == "Background"


def test_new_layer():
    from gimp_mcp.config import set_mode
    from gimp_mcp.backend import get_backend

    set_mode("mock")
    b = get_backend()

    created = b.new_image(100, 100, "#ff0000")
    assert created["ok"]
    iid = created["image"]["id"]

    result = b.new_layer(iid, "Test Layer")
    assert result["ok"]
    assert "Test Layer" in result.get("message", "")


def test_flatten():
    from gimp_mcp.config import set_mode
    from gimp_mcp.backend import get_backend

    set_mode("mock")
    b = get_backend()

    created = b.new_image(100, 100, "#ff0000")
    assert created["ok"]
    iid = created["image"]["id"]

    result = b.flatten(iid)
    assert result["ok"]
    assert result["image"]["id"] == iid
