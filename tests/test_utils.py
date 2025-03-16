from mkquartodocs.utils import convert_nav

NAV_EXAMPLE = [
    {"Home": "README.md"},
    {
        "Examples": [
            {"Simple python execution": "examples/example.qmd"},
            {"Simple dataframe execution": "examples/dataframe_example.qmd"},
            {"Simple matplotlib execution": "examples/matplotlib_example.qmd"},
        ]
    },
]

EXPECT_NAV_EXAMPLE = [
    {"Home": "README.md"},
    {
        "Examples": [
            {"Simple python execution": "examples/example.md"},
            {"Simple dataframe execution": "examples/dataframe_example.md"},
            {"Simple matplotlib execution": "examples/matplotlib_example.md"},
        ]
    },
]


def test_convert_nav():
    assert convert_nav(NAV_EXAMPLE) == EXPECT_NAV_EXAMPLE
