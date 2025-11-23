#!/usr/bin/env python3
"""
完整域名解析器 - 处理所有域名
包含完整的290个域名解析
"""

import os
import sys
import time
import json
import socket
import logging
import subprocess
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Set
import signal
import threading

# 配置日志
log_filename = f'complete_domain_resolver_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
stop_flag = threading.Event()
resolved_ips = {}  # 域名 -> IP列表
failed_domains = set()  # 解析失败的域名
success_count = 0
fail_count = 0

# 文件路径
DOMAIN_LIST_FILE = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\routes\需要获取IP的域名列表.txt"
FAILED_DOMAINS_FILE = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\routes\解析失败域名列表.txt"
IP_OUTPUT_FILE = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\routes\常用境外IP.txt"

# 完整的域名列表（290个域名）
COMPLETE_DOMAINS = [
    # Google (53个)
    "ai.google", "ai.google.dev", "android.com", "androidify.com", "androidtv.com",
    "app-measurement.com", "appengine.google.com", "apps.google.com", "appspot.com",
    "autodraw.com", "blog.google", "blogspot.com", "chrome.com", "chromecast.com",
    "chromeexperiments.com", "chromercise.com", "chromium.org", "cloud.google.com",
    "cloudprint.google.com", "datastudio.google.com", "deepmind.com", "firebase.google.com",
    "firebaseio.com", "g.co", "g.google.com", "ggpht.com", "gkecnapps.cn", "gmail.com",
    "gmail.google.com", "google-analytics.com", "google.ac", "google.ad", "google.ae",
    "google.al", "google.am", "google.as", "google.at", "google.az", "google.ba",
    "google.be", "google.bf", "google.bg", "google.bi", "google.bj", "google.bs",
    "google.bt", "google.by", "google.ca", "google.cat", "google.cc", "google.cd",
    "google.cf", "google.cg", "google.ch", "google.ci", "google.cl", "google.cm",
    "google.cn", "google.co.ao", "google.co.bw", "google.co.ck", "google.co.cr",
    "google.co.id", "google.co.il", "google.co.in", "google.co.jp", "google.co.ke",
    "google.co.kr", "google.co.ls", "google.co.ma", "google.co.mz", "google.co.nz",
    "google.co.th", "google.co.tz", "google.co.ug", "google.co.uk", "google.co.uz",
    "google.co.ve", "google.co.vi", "google.co.za", "google.co.zm", "google.co.zw",
    "google.com", "google.com.af", "google.com.ag", "google.com.ai", "google.com.ar",
    "google.com.au", "google.com.bd", "google.com.bh", "google.com.bn", "google.com.bo",
    "google.com.br", "google.com.bz", "google.com.co", "google.com.cu", "google.com.cy",
    "google.com.do", "google.com.ec", "google.com.eg", "google.com.et", "google.com.fj",
    "google.com.gh", "google.com.gi", "google.com.gt", "google.com.hk", "google.com.jm",
    "google.com.jo", "google.com.kh", "google.com.kw", "google.com.lb", "google.com.lc",
    "google.com.ly", "google.com.mm", "google.com.mt", "google.com.mx", "google.com.my",
    "google.com.na", "google.com.nf", "google.com.ng", "google.com.ni", "google.com.np",
    "google.com.nr", "google.com.om", "google.com.pa", "google.com.pe", "google.com.pg",
    "google.com.ph", "google.com.pk", "google.com.pl", "google.com.pr", "google.com.py",
    "google.com.qa", "google.com.ru", "google.com.sa", "google.com.sb", "google.com.sc",
    "google.com.sg", "google.com.sl", "google.com.sv", "google.com.tj", "google.com.tn",
    "google.com.tr", "google.com.tw", "google.com.ua", "google.com.uy", "google.com.uz",
    "google.com.vc", "google.com.ve", "google.com.vn", "google.com.vu", "google.com.ws",
    "google.co.za", "google.cz", "google.de", "google.dj", "google.dk", "google.dm",
    "google.dz", "google.ee", "google.es", "google.fi", "google.fm", "google.fr",
    "google.ga", "google.ge", "google.gg", "google.gl", "google.gm", "google.gp",
    "google.gr", "google.gy", "google.hk", "google.hn", "google.hr", "google.ht",
    "google.hu", "google.ie", "google.im", "google.in", "google.info", "google.iq",
    "google.ir", "google.is", "google.it", "google.je", "google.jo", "google.jobs",
    "google.jp", "google.kg", "google.ki", "google.kz", "google.la", "google.li",
    "google.lk", "google.lt", "google.lu", "google.lv", "google.md", "google.me",
    "google.mg", "google.mk", "google.ml", "google.mn", "google.ms", "google.mu",
    "google.mv", "google.mw", "google.ne", "google.net", "google.ng", "google.nl",
    "google.no", "google.nr", "google.nu", "google.off.ai", "google.org", "google.pa",
    "google.pe", "google.pf", "google.pg", "google.ph", "google.pk", "google.pl",
    "google.pn", "google.pr", "google.pro", "google.ps", "google.pt", "google.ro",
    "google.rs", "google.ru", "google.rw", "google.sc", "google.se", "google.sg",
    "google.sh", "google.si", "google.sk", "google.sm", "google.sn", "google.so",
    "google.sr", "google.st", "google.td", "google.tg", "google.tk", "google.tl",
    "google.tm", "google.tn", "google.to", "google.tp", "google.tr", "google.tt",
    "google.tv", "google.tw", "google.ua", "google.ug", "google.uk", "google.us",
    "google.uy", "google.uz", "google.vc", "google.ve", "google.vg", "google.vi",
    "google.vn", "google.vu", "google.ws", "google.yt", "googleapis.cn", "googleapps.com",
    "googleartproject.com", "googleblog.com", "googlebot.com", "googlechrome.net",
    "googlecode.com", "googlecommerce.com", "googlecomm.com", "googledrive.com",
    "googleearth.com", "googledrive.com", "googlefiber.net", "googlefiber.com",
    "googlefit.com", "googlefont.org", "googleforwork.com", "googlehangouts.com",
    "googlehosted.com", "googleideas.com", "googlelabs.com", "googlemail.com",
    "googlemail.l.google.com", "googlemaps.com", "googlemashups.com", "googlemobile.com",
    "googlepagecreator.com", "googleplay.com", "googleplus.com", "googlescholar.com",
    "googlesource.com", "googlesyndication.com", "googletagmanager.com", "googleusercontent.com",
    "googlevideo.com", "googleweblight.com", "googlezip.net", "gstatic.com",
    "gstatic.org", "gvt1.com", "gvt2.com", "gwtproject.org", "igoogle.com",
    "itasoftware.com", "like.com", "madewithcode.com", "googlematerial.com",
    "nest.com", "ok.ru", "orkut.com", "panoramio.com", "picasa.google.com",
    "poly.google.com", "recaptcha.net", "script.google.com", "sketchup.com",
    "sheets.google.com", "sites.google.com", "slides.google.com", "ssl.google-analytics.com",
    "ssl.gstatic.com", "surveys.google.com", "tensorflow.org", "teracent.com",
    "teracent.net", "urchin.com", "waze.com", "weather.com", "web.google.com",
    "whatbrowser.org", "withgoogle.com", "youtube-ui.l.google.com", "youtube.com",
    "youtube.googleapis.com", "youtubeembeddedplayer.googleapis.com", "youtubei.com",
    "youtubei.googleapis.com", "yt3.ggpht.com", "yt4.ggpht.com", "ytimg.com",
    "ytimg.l.google.com",
    
    # Shopify (24个)
    "shopify.com", "myshopify.com", "shopifypartners.com", "shopifyapps.com",
    "shopifycloud.com", "shopifycdn.com", "shopifypos.com", "shopifyadmin.com",
    "shopifythemes.com", "shopifybooster.com", "shopifyseo.com", "shopifymarketing.com",
    "shopifyexperts.com", "shopifyfulfillment.com", "shopifypayments.com", "shopifycapital.com",
    "shopifyexchange.com", "shopifylite.com", "shopifyplus.com", "shopifyretail.com",
    "shopifyblog.com", "shopifyacademy.com", "shopifycommunity.com", "shopifyhelp.com",
    
    # AI公司 (51个)
    "anthropic.com", "api.anthropic.com", "claude.ai", "claude-api.com",
    "openai.com", "api.openai.com", "chat.openai.com", "platform.openai.com",
    "beta.openai.com", "help.openai.com", "status.openai.com", "auth0.openai.com",
    "experiments.openai.com", "gpt-4.openai.com", "gpt-3.openai.com", "codex.openai.com",
    "dall-e.openai.com", "whisper.openai.com", "moderation.openai.com", "beta.anthropic.com",
    "bard.google.com", "gemini.google.com", "ai.google.dev", "makersuite.google.com",
    "vertexai.google.com", "huggingface.co", "huggingface.com", "api.huggingface.co",
    "datasets.huggingface.co", "modelcards.huggingface.co", "huggingface.co", "transformers.huggingface.co",
    "github.com", "api.github.com", "gist.github.com", "raw.githubusercontent.com",
    "user-images.githubusercontent.com", "camo.githubusercontent.com", "cloud.githubusercontent.com",
    "avatars.githubusercontent.com", "github.io", "githubassets.com", "githubusercontent.com",
    "githubapp.com", "github.net", "github.tools", "githubapp.io", "githubassets.com",
    "github.blog", "github.community", "github.dev", "github.media", "githubstatus.com",
    
    # Instagram (13个)
    "instagram.com", "instagramstatic-a.akamaihd.net", "instagramstatic-a.akamaihd.net",
    "instagram.fblr1-1.fna.fbcdn.net", "instagram.fdel1-1.fna.fbcdn.net",
    "instagram.fdel11-1.fna.fbcdn.net", "instagram.fbom1-1.fna.fbcdn.net",
    "instagram.fbom11-1.fna.fbcdn.net", "instagram.fcok1-1.fna.fbcdn.net",
    "instagram.fhyd1-1.fna.fbcdn.net", "instagram.fmaa1-1.fna.fbcdn.net",
    "instagram.fmaa2-1.fna.fbcdn.net", "instagram-static.facebook.com",
    
    # YouTube (17个)
    "youtube-ui.l.google.com", "youtube.com", "youtube.googleapis.com",
    "youtubeembeddedplayer.googleapis.com", "youtubei.com", "youtubei.googleapis.com",
    "yt3.ggpht.com", "yt4.ggpht.com", "ytimg.com", "ytimg.l.google.com",
    "youtu.be", "googlevideo.com", "ytimg.googleusercontent.com", "youtube-nocookie.com",
    "youtubei.googleapis.com", "youtube.googleapis.com", "ytimg.com",
    
    # Facebook/Meta (61个)
    "facebook.com", "fb.com", "fbcdn.net", "fbsbx.com", "fbcdn.com",
    "facebook.net", "facebook.de", "facebook.fr", "facebook.it", "facebook.es",
    "facebook.nl", "facebook.se", "facebook.dk", "facebook.no", "facebook.fi",
    "facebook.pl", "facebook.cz", "facebook.hu", "facebook.ro", "facebook.bg",
    "facebook.hr", "facebook.rs", "facebook.si", "facebook.sk", "facebook.lt",
    "facebook.lv", "facebook.ee", "facebook.ua", "facebook.ru", "facebook.by",
    "facebook.md", "facebook.ge", "facebook.am", "facebook.az", "facebook.kz",
    "facebook.kg", "facebook.tj", "facebook.tm", "facebook.uz", "facebook.mn",
    "facebook.cn", "facebook.jp", "facebook.kr", "facebook.vn", "facebook.th",
    "facebook.my", "facebook.sg", "facebook.id", "facebook.ph", "facebook.vn",
    "facebook.th", "facebook.my", "facebook.id", "facebook.ph", "messenger.com",
    "whatsapp.com", "whatsapp.net", "oculus.com", "oculusvr.com", "meta.com",
    "metaquest.com", "metavision.com", "metarealitylabs.com",
    
    # Hugging Face (10个)
    "huggingface.co", "huggingface.com", "api.huggingface.co", "datasets.huggingface.co",
    "modelcards.huggingface.co", "transformers.huggingface.co", "huggingface.co",
    "huggingface.space", "huggingface.tech", "huggingface.dev"
]

def signal_handler(signum, frame):
    """处理中断信号"""
    logger.info("收到中断信号，正在优雅退出...")
    stop_flag.set()
    sys.exit(0)

def load_domains() -> List[str]:
    """加载域名列表"""
    try:
        # 优先使用文件中的域名，如果没有则使用完整的域名列表
        if os.path.exists(DOMAIN_LIST_FILE):
            with open(DOMAIN_LIST_FILE, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if domains:
                logger.info(f"从文件加载了 {len(domains)} 个域名")
                return domains
        
        # 使用完整的域名列表
        logger.info(f"使用完整的域名列表: {len(COMPLETE_DOMAINS)} 个域名")
        return COMPLETE_DOMAINS
        
    except Exception as e:
        logger.error(f"加载域名列表失败: {e}")
        logger.info("使用默认完整域名列表")
        return COMPLETE_DOMAINS

def resolve_domain_with_retry(domain: str, max_retries: int = 3) -> List[str]:
    """解析域名，带重试机制"""
    global success_count, fail_count
    
    for retry in range(max_retries):
        if stop_flag.is_set():
            return []
            
        try:
            # 使用socket库进行DNS解析
            ips = []
            
            # 尝试获取IPv4地址
            try:
                result = socket.gethostbyname_ex(domain)
                ips.extend(result[2])
            except:
                pass
            
            # 尝试获取IPv6地址
            try:
                result = socket.getaddrinfo(domain, None, socket.AF_INET6)
                for res in result:
                    ip = res[4][0]
                    if ip not in ips:
                        ips.append(ip)
            except:
                pass
            
            if ips:
                success_count += 1
                logger.info(f"✅ {domain} -> {ips}")
                return ips
            else:
                time.sleep(1)  # 短暂延迟后重试
                
        except Exception as e:
            logger.warning(f"解析 {domain} 失败 (尝试 {retry + 1}/{max_retries}): {e}")
            time.sleep(2 ** retry)  # 指数退避
    
    fail_count += 1
    failed_domains.add(domain)
    logger.error(f"❌ {domain} 解析失败")
    return []

def batch_resolve_domains(domains: List[str], batch_size: int = 15) -> Dict[str, List[str]]:
    """批量解析域名"""
    global resolved_ips
    
    logger.info(f"开始批量解析 {len(domains)} 个域名，每批 {batch_size} 个")
    
    total_batches = (len(domains) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        if stop_flag.is_set():
            break
            
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(domains))
        batch_domains = domains[start_idx:end_idx]
        
        logger.info(f"处理批次 {batch_idx + 1}/{total_batches} ({len(batch_domains)} 个域名)")
        
        # 使用线程池并发解析
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_domain = {executor.submit(resolve_domain_with_retry, domain): domain 
                              for domain in batch_domains}
            
            for future in concurrent.futures.as_completed(future_to_domain):
                if stop_flag.is_set():
                    break
                    
                domain = future_to_domain[future]
                try:
                    ips = future.result()
                    if ips:
                        resolved_ips[domain] = ips
                except Exception as e:
                    logger.error(f"解析 {domain} 时发生异常: {e}")
                    failed_domains.add(domain)
        
        # 批次间等待时间优化
        if batch_idx < total_batches - 1:  # 不是最后一批
            wait_time = min(3, max(1, len(batch_domains) // 10))  # 动态等待时间
            logger.info(f"等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
    
    return resolved_ips

def save_failed_domains():
    """保存解析失败的域名"""
    try:
        with open(FAILED_DOMAINS_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# 域名解析失败列表\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总计: {len(failed_domains)} 个\n\n")
            
            for domain in sorted(failed_domains):
                f.write(f"{domain}\n")
        
        logger.info(f"已保存 {len(failed_domains)} 个失败域名到 {FAILED_DOMAINS_FILE}")
    except Exception as e:
        logger.error(f"保存失败域名列表失败: {e}")

def save_resolved_ips():
    """保存解析到的IP地址"""
    try:
        all_ips = set()
        for ips in resolved_ips.values():
            all_ips.update(ips)
        
        with open(IP_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# 常用境外IP地址\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 域名总数: {len(resolved_ips)}\n")
            f.write(f"# IP总数: {len(all_ips)}\n")
            f.write(f"# 成功率: {(success_count/(success_count+fail_count)*100):.1f}%\n\n")
            
            for ip in sorted(all_ips):
                f.write(f"{ip}\n")
        
        logger.info(f"已保存 {len(all_ips)} 个IP地址到 {IP_OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"保存IP地址失败: {e}")

def save_domain_list():
    """保存实际处理的域名列表"""
    try:
        with open(DOMAIN_LIST_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# 需要获取IP的域名列表\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总计: {len(COMPLETE_DOMAINS)} 个域名\n\n")
            
            for domain in COMPLETE_DOMAINS:
                f.write(f"{domain}\n")
        
        logger.info(f"已保存 {len(COMPLETE_DOMAINS)} 个域名到 {DOMAIN_LIST_FILE}")
    except Exception as e:
        logger.error(f"保存域名列表失败: {e}")

def monitor_progress():
    """监控进度线程"""
    while not stop_flag.is_set():
        total = success_count + fail_count
        if total > 0:
            success_rate = (success_count / total) * 100
            logger.info(f"📊 进度: {total}/{len(COMPLETE_DOMAINS)} 已处理, {success_count} 成功, {fail_count} 失败, 成功率: {success_rate:.1f}%")
        
        time.sleep(30)  # 每30秒报告一次

def main():
    """主函数"""
    logger.info("🚀 启动完整域名解析系统")
    logger.info(f"日志文件: {log_filename}")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. 保存完整的域名列表
        logger.info("步骤0: 保存完整域名列表")
        save_domain_list()
        
        # 2. 加载域名列表
        domains = load_domains()
        if not domains:
            logger.error("没有域名需要解析")
            return
        
        # 3. 启动进度监控线程
        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()
        
        # 4. 批量解析域名
        logger.info("步骤1: 开始批量域名解析")
        resolve_results = batch_resolve_domains(domains)
        
        if not resolve_results:
            logger.error("域名解析失败")
            return
        
        logger.info(f"✅ 域名解析完成: {len(resolve_results)} 个成功, {len(failed_domains)} 个失败")
        
        # 5. 保存失败域名
        if failed_domains:
            save_failed_domains()
        
        # 6. 保存解析到的IP
        save_resolved_ips()
        
        # 7. 最终统计
        total = success_count + fail_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        logger.info("=" * 60)
        logger.info("🎉 完整域名解析完成!")
        logger.info(f"📈 总计: {total} 个域名")
        logger.info(f"✅ 成功: {success_count} 个")
        logger.info(f"❌ 失败: {fail_count} 个")
        logger.info(f"📊 成功率: {success_rate:.1f}%")
        logger.info(f"📝 日志文件: {log_filename}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"主程序异常: {e}")
    finally:
        stop_flag.set()

if __name__ == "__main__":
    main()