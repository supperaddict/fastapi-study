import httpx
import tools


def test_http_demo_success(client, monkeypatch):
    # 保存真正的客户端类
    real_async_client = httpx.AsyncClient

    # 模拟外部服务器
    def handler(request):
        assert request.url.params["keyword"] == "fastapi"

        return httpx.Response(
            200,
            json={"args": {"keyword": "fastapi"}},
        )

    # 创建使用模拟网络的客户端
    def mock_client(**kwargs):
        return real_async_client(
            transport=httpx.MockTransport(handler),
            **kwargs,
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)

    response = client.get(
        "/tools/http-demo",
        params={"keyword": "fastapi"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "message": "外部请求成功",
        "upstream_data": {
            "args": {"keyword": "fastapi"},
        },
    }


def test_http_demo_timeout(client, monkeypatch):
    real_async_client = httpx.AsyncClient

    def handler(request):
        raise httpx.ReadTimeout(
            "模拟读取超时",
            request=request,
        )

    def mock_client(**kwargs):
        return real_async_client(
            transport=httpx.MockTransport(handler),
            **kwargs,
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)

    response = client.get("/tools/http-demo")

    assert response.status_code == 504
    assert response.json() == {
        "detail": "外部服务响应超时",
    }