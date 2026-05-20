def test_hello():
    from app import hello
    assert hello() == "Hello world!"
