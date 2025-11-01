#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YDS-Lab 统一检查命令行入口"""
import argparse
import json
from . import (
    run_all_checks,
    run_quality_checks,
    run_security_scan,
    run_performance_checks,
    run_compliance_checks,
)

def main():
    parser = argparse.ArgumentParser(description="YDS-Lab 检查聚合器")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="运行全部检查")
    group.add_argument("--quality", action="store_true", help="质量检查")
    group.add_argument("--security", action="store_true", help="安全检查")
    group.add_argument("--performance", action="store_true", help="性能检查")
    group.add_argument("--compliance", action="store_true", help="合规检查")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args()

    if args.all or not any([args.quality, args.security, args.performance, args.compliance]):
        res = run_all_checks()
    elif args.quality:
        res = run_quality_checks()
    elif args.security:
        res = run_security_scan()
    elif args.performance:
        res = run_performance_checks()
    elif args.compliance:
        res = run_compliance_checks()
    else:
        res = {"status": "no_action"}

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("检查完成：")
        print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()