function FindProxyForURL(url, host) {
    return "SOCKS5 127.0.0.1:1083; PROXY 127.0.0.1:8081; DIRECT";
}