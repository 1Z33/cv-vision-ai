import time

from app.core.cache import TTLCache


def test_cache_basic_set_get():
    cache = TTLCache(default_ttl=10)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_cache_expiration():
    cache = TTLCache(default_ttl=1)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_cache_stats():
    cache = TTLCache(default_ttl=10)
    cache.set("a", 1)
    assert cache.get("a") == 1  # hit
    assert cache.get("b") is None  # miss

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate_percent"] == 50.0


def test_cache_invalidate_pattern():
    cache = TTLCache(default_ttl=10)
    cache.set("cv:123:analysis", "data1")
    cache.set("cv:123:match", "data2")
    cache.set("cv:456:analysis", "data3")

    deleted = cache.invalidate_pattern("cv:123")
    assert deleted == 2
    assert cache.get("cv:123:analysis") is None
    assert cache.get("cv:456:analysis") == "data3"


def test_cache_thread_safety():
    """Test basique de thread-safety (pas de crash)."""
    import threading

    cache = TTLCache(default_ttl=60)

    def writer():
        for i in range(100):
            cache.set(f"key_{i}", i)

    def reader():
        for i in range(100):
            _ = cache.get(f"key_{i}")

    threads = [threading.Thread(target=writer) for _ in range(5)] + [
        threading.Thread(target=reader) for _ in range(5)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert True

