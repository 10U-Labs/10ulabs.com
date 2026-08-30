from hcl2 import SerializationOptions


V7_COMPATIBLE = SerializationOptions(
    strip_string_quotes=True,
    explicit_blocks=False,
    with_comments=False,
    preserve_heredocs=False,
)
