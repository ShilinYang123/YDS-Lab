
function FindProxyForURL(url, host) {
    // 本地地址直连
    if (isPlainHostName(host) ||
        isInNet(host, "10.0.0.0", "255.0.0.0") ||
        isInNet(host, "172.16.0.0", "255.240.0.0") ||
        isInNet(host, "192.168.0.0", "255.255.0.0") ||
        isInNet(host, "127.0.0.0", "255.0.0.0"))
        return "DIRECT";

    // 国内常见域名直连
    if (re.search(r'\.cn$', host) ||
        /^.*\.baidu\.com$/.test(host) ||
        /^.*\.qq\.com$/.test(host) ||
        /^.*\.163\.com$/.test(host) ||
        /^.*\.sina\.com\.cn$/.test(host) ||
        /^.*\.weibo\.com$/.test(host) ||
        /^.*\.taobao\.com$/.test(host) ||
        /^.*\.tmall\.com$/.test(host) ||
        /^.*\.jd\.com$/.test(host) ||
        /^.*\.alipay\.com$/.test(host))
        return "DIRECT";

    // 默认代理
    return "SOCKS5 127.0.0.1:1083; PROXY 127.0.0.1:8081; DIRECT";
}
