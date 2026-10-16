"""
网络与客户端 IP 解析工具
用于安全解析客户端真实 IP 地址，防御反向代理下的 X-Forwarded-For 伪造攻击
"""


def get_client_ip(request) -> str:
    """
    安全解析客户端真实 IP 地址，防御 HTTP 请求头伪造攻击。
    策略：
    1. 优先读取标准 REMOTE_ADDR 或受信反向代理设置的 HTTP_X_REAL_IP；
    2. 严禁盲信客户端单方面声明的 HTTP_X_FORWARDED_FOR 最左侧值；
    3. 若存在多级转发，取右侧最接近受信代理的 IP，防御伪造注入。
    """
    if not request or not hasattr(request, 'META'):
        return '127.0.0.1'

    # 1. 优先信任受管边缘反向代理传递的 X-Real-IP
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        ip = x_real_ip.strip()
        if ip:
            return ip

    # 2. 其次使用底层 TCP 连接层 IP (REMOTE_ADDR)
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr:
        ip = remote_addr.strip()
        if ip:
            return ip

    # 3. 兜底降级处理 X-Forwarded-For
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # 取右侧最接近反向代理的有效 IP（防止客户端在左侧伪造 IP 注入）
        parts = [p.strip() for p in x_forwarded_for.split(',') if p.strip()]
        if parts:
            return parts[-1]

    return '127.0.0.1'
