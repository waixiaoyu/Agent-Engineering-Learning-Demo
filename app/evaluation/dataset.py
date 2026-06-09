DEMO_CASES = [
    {
        "input": "我们在新门店用华为坤灵 APP 开局，扫码添加 eKitEngine S380 后一直显示设备未上线，AP 也没有出现在拓扑里。现场说网线都插好了，帮我判断一下先查什么？",
        "expected": [
            "ask clarifying question",
            "identify S380 onboarding",
            "missing topology",
        ],
    },
    {
        "input": "S380 上联到门店路由器 LAN 口，电源灯常亮，上联口有灯闪。AP 接在 S380 下面。APP 里扫码能添加设备，但是一直显示未上线。现场电脑接到 S380 下面能上网，路由器开了 DHCP。",
        "expected": [
            "runbook_search",
            "case_search",
            "device_status_query",
            "开局动作核对",
        ],
    },
]
